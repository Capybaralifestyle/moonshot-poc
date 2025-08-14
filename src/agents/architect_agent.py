import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__("Architect")

    def build_prompt(self, data):
        return """
You are a principal cloud architect fluent in Java 21, Spring Boot 3.3, Kafka 3.7, Scala 3, Terraform, AWS / Azure / GCP.
Project: {0}

Return **only** JSON:
{
  "architecture_pattern": "cloud-native micro-services with event sourcing",
  "language_stack": {
    "backend": {
      "primary": "Java 21 + Spring Boot 3.3 (virtual threads, native-image)",
      "secondary": "Scala 3 (Akka Streams for heavy compute)",
      "gateway": "Spring Cloud Gateway 4"
    },
    "messaging": "Kafka 3.7 (exactly-once, idempotent producers)",
    "streaming": "Kafka Streams (Java) + Akka Streams (Scala)"
  },
  "cloud": {
    "aws": {
      "compute": "EKS + Fargate Spot",
      "storage": "RDS Postgres (Multi-AZ), S3 + Glacier Deep Archive",
      "networking": "ALB, CloudMap, VPC Lattice",
      "observability": "CloudWatch, X-Ray, Grafana Cloud"
    },
    "azure": {
      "compute": "AKS + KEDA autoscaling",
      "storage": "Azure Database for PostgreSQL Flexible, Blob Storage",
      "networking": "Application Gateway, Front Door",
      "observability": "Azure Monitor, Log Analytics"
    },
    "gcp": {
      "compute": "GKE Autopilot + Cloud Run (for burst)",
      "storage": "Cloud SQL Postgres, Cloud Storage Nearline",
      "networking": "Cloud Load-Balancing, Cloud Armor",
      "observability": "Cloud Trace, Cloud Profiler"
    }
  },
  "infrastructure_as_code": "Terraform 1.7 (multi-provider workspace)",
  "ci_cd": "GitHub Actions → Argo CD → Flux CD (GitOps)",
  "observability": {
    "metrics": "Micrometer + Prometheus",
    "tracing": "OpenTelemetry + Jaeger",
    "logs": "Loki + Grafana"
  },
  "security": [
    "Spring Security 6 + OAuth 2.1",
    "HashiCorp Vault for secrets",
    "KMS keys per cloud",
    "Container scanning (Trivy, Snyk)"
  ],
  "cost_per_day": 1500
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}