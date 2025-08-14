import os
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.orchestrator import VerboseOrchestrator
from src.agents import (
    ArchitectAgent, ProjectManagerAgent, CostEstimatorAgent,
    SecurityAgent, DevOpsAgent, PerformanceAgent, DataAgent, UXAgent,
    DataScientistAgent, DatasetMLAgent
)

import uuid
from pathlib import Path

app = FastAPI(
    title="Moonshot-K2 POC API",
    version="1.0.0",
    description="Run the multi-agent orchestrator via REST and (optionally) export to Google Sheets."
)

# Allow everything for simplicity; lock down if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


class RunRequest(BaseModel):
    description: str = Field(..., description="High-level project description for the agents.")
    export_enabled: Optional[bool] = Field(
        None,
        description="Override SHEETS_EXPORT_ENABLED for this request only."
    )


class RunResponse(BaseModel):
    results: Dict[str, Any]


# In-memory registry for uploaded datasets.  Keys are dataset IDs, values are
# dictionaries with 'path' and optional 'domain_column'.  In a production
# setting this would be persisted to a database or object storage.
DATASETS_DIR = os.getenv("DATASETS_DIR", "/workspace/tmpdata")
_datasets: Dict[str, Dict[str, Optional[str]]] = {}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/agents", response_model=List[str])
def list_agents():
    return [
        "architect", "pm", "cost", "security",
        "devops", "performance", "data", "ux", "datasci",
        "dataset_ml",
    ]


@app.post("/run", response_model=RunResponse)
def run(req: RunRequest):
    def noop_log(agent, prompt, resp):
        # keep logs server-side only for now; you can store or stream if needed
        pass

    orch = VerboseOrchestrator(on_log=noop_log)

    # Per-request export override, if provided
    if req.export_enabled is not None:
        orch._sheets_enabled = bool(req.export_enabled)

    try:
        results = orch.run(req.description)
        return RunResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- SaaS extensions -----

@app.post("/datasets")
async def upload_dataset(
    file: UploadFile = File(...),
    domain_column: Optional[str] = Form(None)
):
    """Upload a dataset file and optionally specify the domain column.

    Returns a unique dataset ID that can be used in subsequent run requests.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    # Ensure datasets directory exists
    Path(DATASETS_DIR).mkdir(parents=True, exist_ok=True)
    # Generate a unique ID and save file
    dataset_id = f"{uuid.uuid4()}_{file.filename}"
    dest_path = Path(DATASETS_DIR) / dataset_id
    try:
        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    # Record metadata
    _datasets[dataset_id] = {
        "path": str(dest_path),
        "domain_column": domain_column or None,
    }
    return {"dataset_id": dataset_id}


@app.get("/datasets")
def list_datasets() -> List[str]:
    """List all uploaded dataset IDs."""
    return list(_datasets.keys())


class ProjectRunRequest(BaseModel):
    description: str = Field(..., description="High-level project description for the agents.")
    dataset_id: str = Field(..., description="ID of a previously uploaded dataset.")
    export_enabled: Optional[bool] = Field(None, description="Override export flag for this run.")


@app.post("/projects/run")
def run_project(req: ProjectRunRequest) -> Dict[str, Any]:
    """Run the orchestrator on a description using a specific dataset.

    The dataset must be uploaded first via /datasets.  If the dataset was
    uploaded with a domain column, the environment variable DOMAIN_COLUMN is
    set accordingly for this run.
    """
    dataset_info = _datasets.get(req.dataset_id)
    if not dataset_info:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Set environment variables for this run
    os.environ["DATASET_PATH"] = dataset_info["path"]
    if dataset_info.get("domain_column"):
        os.environ["DOMAIN_COLUMN"] = dataset_info["domain_column"]
    else:
        # Remove any previous domain column
        if "DOMAIN_COLUMN" in os.environ:
            del os.environ["DOMAIN_COLUMN"]
    # Execute orchestrator
    def noop_log(agent, prompt, resp):
        pass
    orch = VerboseOrchestrator(on_log=noop_log)
    if req.export_enabled is not None:
        orch._sheets_enabled = bool(req.export_enabled)
    try:
        results = orch.run(req.description)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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