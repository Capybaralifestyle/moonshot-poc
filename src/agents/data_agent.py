import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("Data")

    def build_prompt(self, data):
        return """
You are a data/platform engineer for transactional Java/Spring + Kafka + Postgres.
Project: {0}
Return **only** JSON:
{
  "storage": {
    "oltp": "PostgreSQL (RDS/Azure PG/Cloud SQL)",
    "streaming": "Kafka topics (compacted for reference, EoS for tx)",
    "object": "S3/Blob/Cloud Storage for cold data"
  },
  "schema_governance": {
    "registry": "Confluent/Apicurio Schema Registry",
    "strategy": "backward-compatible Avro/JSON Schema",
    "validation": ["pre-commit", "CI check", "topic-level policy"]
  },
  "pipelines": {
    "ingest": ["Kafka Connect", "Debezium CDC where needed"],
    "processing": ["Kafka Streams (Java)", "Akka Streams (Scala)"],
    "batch": ["Spark/Dataproc optional", "DuckDB for ad-hoc"]
  },
  "dq": {
    "rules": ["null checks", "range checks", "referential integrity"],
    "monitoring": ["great_expectations optional"]
  }
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}