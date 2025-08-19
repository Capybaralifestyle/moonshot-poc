import os
import json
import uuid
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.orchestrator import VerboseOrchestrator
from src.config import get_llm

from pathlib import Path

# Supabase client setup.  When SUPABASE_URL and SUPABASE_SERVICE_KEY are provided,
# a client will be created for persisting and querying project runs.  The
# anonymous key (SUPABASE_ANON_KEY) is intended for client-side use only.
try:
    from supabase import create_client, Client  # type: ignore
except Exception:
    # supabase may not be installed if persistence is not required
    Client = None  # type: ignore
    def create_client(*args, **kwargs):  # type: ignore
        return None

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Initialise a Supabase client if credentials are provided.  We prefer the
# service key here because it has permission to insert and query tables.
_supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY and create_client:
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception:
        _supabase_client = None

def _get_user_from_token(auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Supabase user from a Bearer token, or None if invalid/unset.

    The front-end sends the access token in the Authorization header as
    `Bearer <token>`.  This helper extracts the token and uses the
    Supabase client to fetch the associated user.  If no Supabase client
    exists or the token cannot be verified, None is returned.
    """
    if not auth_header or not _supabase_client:
        return None
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        # The get_user method accepts the access token and returns a response
        # with a `user` attribute.  Depending on the supabase-py version,
        # this may be a dict or an object with `.user`.
        resp = _supabase_client.auth.get_user(token)  # type: ignore[attr-defined]
        user = None
        # Newer versions return an object with a `user` attribute
        if hasattr(resp, "user"):
            user = resp.user  # type: ignore[attr-defined]
        # Older versions may return a dict
        if user is None and isinstance(resp, dict) and "user" in resp:
            user = resp["user"]
        return user or None
    except Exception:
        return None

def _persist_run(user: Optional[Dict[str, Any]], description: str, results: Dict[str, Any]) -> None:
    """Insert a new project run into the Supabase table for the given user.

    Requires `_supabase_client` to be configured and `user` to have an `id` field.
    Any exceptions are swallowed to avoid breaking the API in case of
    connectivity issues or misconfiguration.
    """
    if not _supabase_client or not user or not isinstance(user, (dict, object)):
        return
    user_id = None
    # Attempt to fetch the user's ID from either dict or object
    if isinstance(user, dict):
        user_id = user.get("id") or user.get("sub")
    else:
        # pydantic user model may have id attribute
        user_id = getattr(user, "id", None)
        if not user_id:
            user_id = getattr(user, "sub", None)
    if not user_id:
        return
    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "description": description,
        "results": results,
    }
    try:
        # Insert the record into the `project_runs` table.  If the table does
        # not exist, the user must create it in their Supabase project.
        _supabase_client.table("project_runs").insert(data).execute()  # type: ignore[reportMissingTypeStubs]
    except Exception:
        # Fail silently so that a persistence error doesn't break the API
        pass

app = FastAPI(
    title="Moonshot-K2 POC API",
    version="1.0.0",
    description="Run the multi-agent orchestrator via REST and (optionally) export to an XLS file."
)

_default_provider = os.getenv("LLM_PROVIDER", "kimi")
_default_model = os.getenv("LLM_MODEL", "kimi-k2-instruct")

# Allow everything for simplicity; lock down if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


class RunRequest(BaseModel):
    description: str = Field(
        ...,
        description="High‑level project description for the agents."
    )
    export_enabled: Optional[bool] = Field(
        None,
        description="Override the XLS export flag for this run only."
    )


class RunResponse(BaseModel):
    results: Dict[str, Any]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/agents", response_model=List[str])
def list_agents():
    return [
        "architect", "pm", "cost", "security",
        "devops", "performance", "data", "ux", "datasci", "aicoding",
    ]


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest, authorization: Optional[str] = Header(None)) -> RunResponse:
    """Run the multi‑agent orchestrator on a project description.

    If a valid Supabase JWT is supplied in the ``Authorization`` header, the
    results will be persisted to the ``project_runs`` table along with the user ID.
    """

    user = _get_user_from_token(authorization)

    def noop_log(agent: str, prompt: str, resp: str) -> None:
        # keep logs server-side only for now; you can store or stream if needed
        pass

    llm = get_llm(_default_provider, _default_model)
    orch = VerboseOrchestrator(llm, on_log=noop_log)
    if req.export_enabled is not None:
        orch._xls_enabled = bool(req.export_enabled)

    try:
        results = orch.run(req.description)
        _persist_run(user, req.description, results)
        return RunResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ---- Persistence endpoints ----

@app.get("/projects/latest")
def get_latest_runs(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Return the most recent prediction for each project description for the authenticated user.

    This endpoint requires an Authorization header containing a valid Supabase access
    token.  The response is a dictionary with a single key ``runs`` containing
    a list of run records.  Each record is the most recent entry for its
    description.  If persistence is not configured or no runs exist, an empty list is returned.
    """
    # Determine the current user from the Supabase token
    user = _get_user_from_token(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not _supabase_client:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    # Extract user_id from dict or object
    user_id = None
    if isinstance(user, dict):
        user_id = user.get("id") or user.get("sub")
    else:
        user_id = getattr(user, "id", None) or getattr(user, "sub", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # Fetch all runs for this user ordered by creation timestamp descending
        resp = _supabase_client.table("project_runs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()  # type: ignore[reportMissingTypeStubs]
        records = None
        # Newer versions return an object with data attribute
        if hasattr(resp, "data"):
            records = resp.data
        if records is None and isinstance(resp, dict) and "data" in resp:
            records = resp["data"]
        if not records:
            return {"runs": []}
        # Group by description and pick first (latest) record per group
        latest_map: Dict[str, Dict[str, Any]] = {}
        for rec in records:
            desc = rec.get("description")
            if desc not in latest_map:
                latest_map[desc] = rec
        return {"runs": list(latest_map.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch runs: {e}")

# Mount the frontend under /ui.  The files reside in src/../frontend relative
# to this file, so we compute the path at runtime.  Setting html=True serves
# index.html for /ui requests.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount(
        "/ui",
        StaticFiles(directory=str(frontend_dir), html=True),
        name="frontend",
    )