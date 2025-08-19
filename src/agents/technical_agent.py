import json

from .base_agent import BaseAgent
from src.config import llm


class TechnicalAgent(BaseAgent):
    """Generate technical documentation for the project."""

    def __init__(self) -> None:
        super().__init__("TechnicalWriter")

    def build_prompt(self, data: dict) -> str:
        description = data.get("description", "")
        return (
            "You are a senior technical writer.\n"
            "Draft a technical documentation summarizing the project's goals, "
            "architecture, and key technology choices.\n"
            "Return JSON with a single key 'documentation' containing the "
            "documentation as markdown text.\n"
            f"PROJECT_DESCRIPTION: {description}"
        )

    def analyze(self, data: dict) -> dict:
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        try:
            return json.loads(resp or "{}")
        except json.JSONDecodeError:
            return {"documentation": resp}
