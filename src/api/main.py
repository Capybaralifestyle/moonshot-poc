import os
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.orchestrator import VerboseOrchestrator
from src.agents import (
    ArchitectAgent, ProjectManagerAgent, CostEstimatorAgent,
    SecurityAgent, DevOpsAgent, PerformanceAgent, DataAgent, UXAgent,
    DataScientistAgent
)

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


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/agents", response_model=List[str])
def list_agents():
    return [
        "architect", "pm", "cost", "security",
        "devops", "performance", "data", "ux", "datasci"
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