import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class ProjectManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__("PM")

    def build_prompt(self, data):
        return """
You are a PMP certified for **daily 8-hour planning**.
Project: {0}
Return JSON:
{
  "duration_days": 112,
  "gantt": [
    {"day":1,"task":"Sprint 0 – Infra","owner":"DevOps"},
    {"day":8,"task":"Auth Micro-service","owner":"Senior Dev"},
    {"day":30,"task":"Kafka Topics","owner":"Kafka Engineer"},
    {"day":60,"task":"AI Fraud Model","owner":"AI Lead"},
    {"day":90,"task":"Web MVP","owner":"Frontend Team"},
    {"day":112,"task":"Launch","owner":"PM"}
  ]
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}