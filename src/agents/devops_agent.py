import json
import sys
sys.path.append('/workspace')
from .base_agent import BaseAgent
from src.config import llm


class DevOpsAgent(BaseAgent):
    def __init__(self):
        super().__init__("DevOps")

    def build_prompt(self, data):
        return """
You are a DevOps lead for Java 21 / Spring Boot 3.3 microservices on Kubernetes with GitOps.
Project: {0}
Return **only** JSON:
{
  "containerization": {
    "base_images": ["eclipse-temurin:21-jre", "ubi8-minimal"],
    "build": ["Jib for Java", "Docker Buildx cache"],
    "security": ["multi-stage builds", "non-root user", "distroless optional"]
  },
  "kubernetes": {
    "platforms": ["EKS", "AKS", "GKE"],
    "manifests": ["Deployment", "Service", "HPA", "PDB"],
    "scaling": {"hpa": {"cpu": 60, "memory": 70}, "keda": ["Kafka lag"]},
    "ingress": ["ALB/AGIC/GCLB", "TLS", "WAF optional"]
  },
  "gitops": {
    "tools": ["Argo CD"],
    "policy": ["app-of-apps", "PR-based promotion", "drift detection"]
  },
  "ci_cd": {
    "pipeline": ["GitHub Actions reusable workflows", "matrix builds", "SAST/DAST"],
    "artifacts": ["OCI images", "SBOMs", "signed images (cosign)"]
  },
  "observability": {
    "metrics": ["Micrometer -> Prometheus/Grafana"],
    "tracing": ["OpenTelemetry -> Jaeger/Tempo"],
    "logging": ["Loki/Grafana Cloud"]
  }
}
""".format(data.get('description',''))

    def analyze(self, data):
        prompt = self.build_prompt(data)
        resp = llm.invoke(prompt).content
        return {"agent": self.name, **json.loads(resp or "{}")}