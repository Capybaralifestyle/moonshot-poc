import os
import json
from typing import Callable, Dict, Any

from src.agents import (
    ArchitectAgent, ProjectManagerAgent, CostEstimatorAgent,
    SecurityAgent, DevOpsAgent, PerformanceAgent, DataAgent, UXAgent,
    DataScientistAgent
)
from src.config import llm
from src.export_to_sheets import export_results_to_sheets


class VerboseOrchestrator:
    """Run planning and estimation agents and return a dictionary of results.

    Agents are executed in parallel via the language model.  If
    ``SHEETS_EXPORT_ENABLED=true``, results are automatically exported to
    Google Sheets after each run.
    """

    def __init__(
        self,
        on_log: Callable[[str, str, str], None] | None = None,
    ) -> None:
        """Create a new orchestrator.

        :param on_log: Optional callback to receive (agent_name, prompt, response) events.
        """
        self.on_log = on_log
        # Base LLM-driven agents
        self.agents: Dict[str, Any] = {
            "architect":   ArchitectAgent(),
            "pm":          ProjectManagerAgent(),
            "cost":        CostEstimatorAgent(),
            "security":    SecurityAgent(),
            "devops":      DevOpsAgent(),
            "performance": PerformanceAgent(),
            "data":        DataAgent(),
            "ux":          UXAgent(),
            "datasci":     DataScientistAgent(),
        }

        self._sheets_enabled = (os.getenv("SHEETS_EXPORT_ENABLED", "false").lower() == "true")
        self._sheet_name = os.getenv("SHEETS_EXPORT_NAME", "Moonshot POC Outputs")
        self._sa_path = os.getenv("GCP_SERVICE_ACCOUNT_JSON", "/workspace/config/gcp_service_account.json")
        self._worksheet_index = int(os.getenv("SHEETS_WORKSHEET_INDEX", "0"))

    def run(self, description: str) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for key, agent in self.agents.items():
            prompt = agent.build_prompt({"description": description})
            if self.on_log:
                self.on_log(agent.name, prompt, "🔄 calling LLM …")
            resp = llm.invoke(prompt).content
            if self.on_log:
                self.on_log(agent.name, prompt, resp)
            try:
                results[key] = json.loads(resp or "{}")
            except json.JSONDecodeError:
                results[key] = {"_error": f"Invalid JSON from {agent.name}", "raw": resp}

        if self._sheets_enabled:
            try:
                export_results_to_sheets(
                    results=results,
                    sheet_name=self._sheet_name,
                    creds_path=self._sa_path,
                    worksheet_index=self._worksheet_index
                )
                if self.on_log:
                    self.on_log("Exporter", f"Sheet={self._sheet_name}", "✅ Exported to Google Sheets")
            except Exception as e:
                if self.on_log:
                    self.on_log("Exporter", f"Sheet={self._sheet_name}", f"❌ Export failed: {e}")

        return results