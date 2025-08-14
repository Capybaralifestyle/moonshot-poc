import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


CONFIG_PATH = "/workspace/config/cost_config.json"


class CostEstimatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("DailyCostEstimator")

    def build_prompt(self, data):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cost_cfg = json.load(f)
        except Exception as e:
            cost_cfg = {"_error": f"Failed to load {CONFIG_PATH}: {e}"}
        cfg_inline = json.dumps(cost_cfg, separators=(",", ":"))
        description = data.get('description','')

        return f"""
You are a FinOps expert working at **daily 8-hour granularity**.
Project: {description}

Use the following JSON as the single source of truth for currency, constraints, daily rates, cloud costs, and other costs. Do not invent new keys. Keep numbers numeric.
COST_CONFIG_JSON:
{cfg_inline}

Return **only** JSON with this structure:
{{
  "currency": "<from cost_config>",
  "constraints": <from cost_config.constraints>,
  "assumptions": ["brief bullet assumptions you made (3-5 items)"],
  "daily_breakdown": [
    {{
      "day": 1,
      "task": "Sprint 0 – Infra",
      "roles": {{ "devops": 4, "senior_dev": 4 }},
      "cloud": {{ "aws_ec2_small": 4 }},
      "other": {{ "ci_cd": 1 }},
      "total_daily": 0
    }}
  ],
  "summary": {{
    "total_days": 0,
    "labor_cost": 0,
    "cloud_cost": 0,
    "other_cost": 0,
    "total_cost": 0,
    "within_budget": true,
    "within_deadline": true
  }}
}}
"""

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}