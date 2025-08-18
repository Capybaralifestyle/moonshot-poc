import os
import json
from typing import Callable, Dict, Any

from src.agents import (
    ArchitectAgent, ProjectManagerAgent, CostEstimatorAgent,
    SecurityAgent, DevOpsAgent, PerformanceAgent, DataAgent, UXAgent,
    DataScientistAgent,
)
from src.export_to_excel import export_results_to_xls


class VerboseOrchestrator:
    """Run planning and estimation agents and return a dictionary of results.

    Agents are executed via the language model.  If
    ``XLS_EXPORT_ENABLED=true``, results are automatically exported to an
    Excel ``.xls`` file after each run.
    """

    def __init__(
        self,
        llm,
        on_log: Callable[[str, str, str], None] | None = None,
    ) -> None:
        """Create a new orchestrator.

        :param llm: LLM client to use for all agents.
        :param on_log: Optional callback to receive (agent_name, prompt, response) events.
        """
        self.llm = llm
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

        self._xls_enabled = os.getenv("XLS_EXPORT_ENABLED", "false").lower() == "true"
        self._xls_path = os.getenv("XLS_EXPORT_PATH", "/workspace/results.xls")
        self.max_retries = int(os.getenv("AGENT_MAX_RETRIES", "100"))
        self._intervention_threshold = int(self.max_retries * 0.75)

    def run(self, description: str) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        for key, agent in self.agents.items():
            prompt = agent.build_prompt({"description": description})
            attempt = 0
            while attempt < self.max_retries:
                attempt += 1
                if self.on_log:
                    self.on_log(agent.name, prompt, f"🔄 calling LLM (attempt {attempt}/{self.max_retries}) …")
                try:
                    resp = self.llm.invoke(prompt).content
                except Exception as e:
                    resp = ""
                    if self.on_log:
                        self.on_log(agent.name, prompt, f"❌ LLM call failed: {e}")
                    if attempt >= self._intervention_threshold and self.on_log:
                        self.on_log(agent.name, prompt, "⚠️ Human intervention recommended.")
                    continue

                if self.on_log:
                    self.on_log(agent.name, prompt, resp)

                try:
                    results[key] = json.loads(resp or "{}")
                    break
                except json.JSONDecodeError:
                    results[key] = {"_error": f"Invalid JSON from {agent.name}", "raw": resp}
                    if attempt >= self._intervention_threshold and self.on_log:
                        self.on_log(agent.name, prompt, "⚠️ Human intervention recommended.")
            else:
                if self.on_log:
                    self.on_log(agent.name, prompt, f"❌ Failed after {self.max_retries} attempts")

        if self._xls_enabled:
            try:
                export_results_to_xls(results=results, file_path=self._xls_path)
                if self.on_log:
                    self.on_log("Exporter", f"File={self._xls_path}", "✅ Exported to XLS")
            except Exception as e:
                if self.on_log:
                    self.on_log("Exporter", f"File={self._xls_path}", f"❌ Export failed: {e}")

        return results
