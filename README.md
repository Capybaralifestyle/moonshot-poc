# Moonshot‑K2 POC

An end‑to‑end Jupyter + Docker POC that orchestrates multiple domain agents against the **Kimi K2 (Moonshot) API** and (optionally) auto‑exports results to **Google Sheets**.

## ✨ What you get
- **Jupyter Lab** workspace in Docker
- **Agents**: Architect, Project Manager, Cost Estimator (reads `config/cost_config.json`), Security, DevOps, Performance, Data, UX, **Data Scientist**
- **Verbose orchestrator** with live logging (prompts + responses)
- **Google Sheets export** (toggle via `.env`)
- Clean, file‑by‑file setup (no magic scripts)

## 🗂 Project structure
```
moonshot-poc/
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
├─ .env.example
├─ notebooks/
│  └─ verbose_demo.ipynb
├─ src/
│  ├─ __init__.py
│  ├─ config.py                 # Moonshot/Kimi LLM config
│  ├─ orchestrator.py           # Runs all agents, optional auto-export to Sheets
│  ├─ export_to_sheets.py       # Google Sheets exporter
│  └─ agents/
│     ├─ __init__.py
│     ├─ base_agent.py
│     ├─ architect_agent.py
│     ├─ project_manager_agent.py
│     ├─ cost_estimator_agent.py
│     ├─ security_agent.py
│     ├─ devops_agent.py
│     ├─ performance_agent.py
│     ├─ data_agent.py
│     ├─ ux_agent.py
│     └─ data_scientist_agent.py
├─ config/
│  ├─ cost_config.json
│  └─ gcp_service_account.json  # (gitignored)
└─ data/
   └─ uploads/
```

## ✅ Prerequisites
- Docker Desktop (or Docker Engine)
- A **Moonshot API key** (Kimi K2)
- (Optional) **Google Sheets** service account JSON and a target spreadsheet shared with that service account

## 🚀 Quick start
1. Copy `.env.example` to `.env` and set values:
   ```
   MOONSHOT_API_KEY=sk-xxxx

   # Google Sheets export (optional)
   SHEETS_EXPORT_ENABLED=true
   SHEETS_EXPORT_NAME=Moonshot POC Outputs
   GCP_SERVICE_ACCOUNT_JSON=/workspace/config/gcp_service_account.json
   SHEETS_WORKSHEET_INDEX=0
   ```
2. Place your service account key at `config/gcp_service_account.json` and share your Google Sheet with that service account email.
3. Build & run:
   ```
   docker compose up --build -d
   ```
4. Open Jupyter: `http://localhost:8888/?token=agent123`
5. Open `notebooks/verbose_demo.ipynb`, run cells. If `SHEETS_EXPORT_ENABLED=true`, results auto‑export to Sheets.

## 🔧 Environment variables
| Name | Required | Example | Notes |
|---|---|---|---|
| `MOONSHOT_API_KEY` | yes | `sk-xxxx` | Moonshot/Kimi API key |
| `SHEETS_EXPORT_ENABLED` | no | `true` | if `true`, auto-export after each run |
| `SHEETS_EXPORT_NAME` | if export | `Moonshot POC Outputs` | must exist in your Drive |
| `GCP_SERVICE_ACCOUNT_JSON` | if export | `/workspace/config/gcp_service_account.json` | service account key path (inside container) |
| `SHEETS_WORKSHEET_INDEX` | no | `0` | which tab (0 = first) |

## 🧪 Notebook usage
Minimal cell to run everything:
```python
import sys; sys.path.insert(0, '/workspace')
from src.orchestrator import VerboseOrchestrator
orc = VerboseOrchestrator()
results = orc.run("Your project description here")
results["datasci"]  # Data Scientist agent output
```

## 🛡 Secrets & safety
- Do **not** commit `.env` or `config/gcp_service_account.json`. They’re in `.gitignore`.
- Rotate credentials regularly.

## 🧭 Troubleshooting
- **401/403** → Check `MOONSHOT_API_KEY`
- **Sheets export fails** → Confirm `.env`, key path, spreadsheet sharing, and name matches exactly
- **Widgets not showing** → Refresh notebook tab; JupyterLab v4 + ipywidgets v8 are included

## 📝 Development notes
- Tested with Python 3.11 (Docker image `python:3.11-slim`).
- Works on Linux/macOS/Windows (Docker Desktop on macOS/Windows).
- You can extend agents by adding a new file under `src/agents/` and registering it in `src/agents/__init__.py` and `src/orchestrator.py`.

## 📜 License
MIT (suggested). Replace with your preferred license.
