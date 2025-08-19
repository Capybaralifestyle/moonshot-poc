import json

from .base_agent import BaseAgent
from src.config import llm


class DocumentationAgent(BaseAgent):
    """Compile final technical documentation from previous agent outputs."""

    def __init__(self) -> None:
        super().__init__("Documentation")

    def build_prompt(self, data: dict) -> str:
        description = data.get("description", "")
        results = data.get("results", {})
        return (
            "You are a senior technical writer.\n"
            "Create final technical documentation based on the project description "
            "and the structured results from prior analysis.\n"
            "Return JSON with key 'documentation' containing markdown.\n"
            f"PROJECT_DESCRIPTION: {description}\n"
            f"AGENT_RESULTS: {json.dumps(results)}"
        )

    def analyze(self, data: dict) -> dict:
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        try:
            return json.loads(resp or "{}")
        except json.JSONDecodeError:
            return {"documentation": resp}

