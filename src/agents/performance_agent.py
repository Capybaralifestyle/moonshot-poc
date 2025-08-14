import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class PerformanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("Performance")

    def build_prompt(self, data):
        return """
You are a performance engineer for Java 21 / Spring Boot 3.3 and Kafka 3.7.
Project: {0}
Return **only** JSON:
{
  "service_slo": {
    "p99_latency_ms": 250,
    "availability": "99.9%",
    "error_budget_monthly_minutes": 43
  },
  "bottleneck_risks": ["GC pauses", "DB connection pool saturation", "Kafka consumer lag"],
  "tuning": {
    "jvm": ["G1GC defaults then measure", "Xms=Xmx for critical services"],
    "spring_boot": ["virtual threads for IO-bound", "connection pooling sizing"],
    "kafka": ["max.in.flight.requests=1 for exactly-once", "linger.ms for batching"]
  },
  "test_plan": {
    "tools": ["k6", "JMeter"],
    "scenarios": ["soak 8h", "stress to failure", "spike"],
    "synthetic_data": ["masked prod schema", "edge cases"]
  },
  "capacity_model": {
    "traffic_drivers": ["DAU", "tx/sec", "burst ratio"],
    "baseline_nodes": {"api": 3, "kafka_consumer": 2}
  }
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}