import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class AICodingAgent(BaseAgent):
    """Assess which features can be delegated to AI-generated code."""

    def __init__(self):
        super().__init__("AICoding")

    def build_prompt(self, data):
        return """
You are an AI coding assistant evaluating a software project.
Project: {0}

List major features that could be delegated to AI code generation. For each feature provide an estimated percentage of the implementation that AI can handle.
Return JSON:
{
  "delegable_features": [
    {"feature": "Authentication", "ai_coverage_percent": 60, "notes": "Boilerplate and CRUD"}
  ]
}
""".format(data.get('description', ''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}
