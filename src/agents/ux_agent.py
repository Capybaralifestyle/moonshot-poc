import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class UXAgent(BaseAgent):
    def __init__(self):
        super().__init__("UX")

    def build_prompt(self, data):
        return """
You are a UX lead for a FinTech-grade web/mobile product with secure flows.
Project: {0}
Return **only** JSON:
{
  "personas": [
    {"name": "Retail Investor", "goals": ["portfolio view", "micro-payments"], "risks": ["cognitive overload"]},
    {"name": "Ops Analyst", "goals": ["fraud triage", "alerts"], "risks": ["alert fatigue"]}
  ],
  "journeys": [
    {"name": "KYC onboarding", "steps": 6, "friction_points": ["document capture", "2FA handoff"]},
    {"name": "Payment flow", "steps": 5, "friction_points": ["fees clarity", "decline reasons"]}
  ],
  "ui_patterns": ["progressive disclosure", "skeletal loading", "accessible forms (WCAG 2.2 AA)"],
  "non_functional": ["responsive", "offline-tolerant", "perceived-latency < 200ms for primary actions"]
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}