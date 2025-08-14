import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class DataScientistAgent(BaseAgent):
    """
    Produces a production-minded DS plan: problem framing, data design,
    eval protocol, baselines, MLOps, and experiment backlog.
    """

    def __init__(self):
        super().__init__("DataScientist")

    def build_prompt(self, data):
        return """
You are a senior data scientist for a Java/Spring + Kafka + Postgres product at FinTech scale.
Your job: design a practical, production-minded DS plan with clear experiments and guardrails.

Project context:
{0}

Return **ONLY** JSON with this exact schema (no extra keys, no comments):
{
  "problem_framing": {
    "type": "classification|regression|ranking|forecasting|segmentation|anomaly_detection",
    "primary_objective": "...",
    "target_definition": "...",
    "unit_of_analysis": "...",
    "observational_bias_risks": ["..."]
  },
  "data_design": {
    "sources": ["Postgres OLTP tables","Kafka topics: events-*","object store"],
    "target_query_sketch": "pseudo-SQL without leakage",
    "feature_views": [
      {"name":"realtime_user_stats","freshness":"under 2m","features":["tx_count_5m","avg_amount_1h","country_mismatch_flag"]}
    ],
    "leakage_checks": ["time-based split","no post-outcome fields"],
    "privacy_constraints": ["PII hashing/salting","min row count for aggregates"]
  },
  "evaluation_protocol": {
    "split_strategy": "temporal_split|kfold|group_kfold|blocked_time_series",
    "metrics": ["AUROC","AUPRC","F1","MAE","MAPE","NDCG"],
    "business_thresholds": ["..."],
    "robustness_checks": ["drift analysis","worst-group performance","calibration curve"]
  },
  "baselines_and_models": {
    "baselines": ["majority_class","logistic_regression","prophet_or_naive_forecast"],
    "candidates": ["xgboost","lightgbm","random_forest","linear_models","simple_nn_if_justified"],
    "feature_importance_plan": ["permutation_importance","SHAP (off-line)"],
    "model_risks": ["overfitting","spurious correlations"]
  },
  "mlops_plan": {
    "feature_store": "Feast or curated tables",
    "training_pipeline": ["reproducible env","seed control","data versioning"],
    "batch_vs_stream": "which features/inference are batch vs streaming",
    "serving": "REST endpoint in Java or Python sidecar",
    "monitoring": ["input drift","target drift (delayed)","performance by segment"]
  },
  "experiments_backlog": [
    {"id":"E-001","hypothesis":"...","design":["..."],"effort_days":2,"dependencies":["..."]}
  ],
  "data_contracts": [
    {"entity":"transaction","required_fields":["tx_id","user_id","amount","currency","timestamp"],"quality_rules":["not null","valid currency","timestamp monotonicity"]}
  ]
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}