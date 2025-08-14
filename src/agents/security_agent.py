import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class SecurityAgent(BaseAgent):
    def __init__(self):
        super().__init__("Security")

    def build_prompt(self, data):
        return f"""
Security lead for Java/Spring cloud.
Project: {data.get('description','')}
Return JSON:
{{
  "threat_model": ["OWASP Top 10", "STRIDE"],
  "controls": ["Spring Security 6","Vault","KMS","Trivy"],
  "compliance": ["SOC 2","GDPR","PCI-DSS"],
  "pen_test_plan": ["SAST","DAST","Container scan"]
}}
"""

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}