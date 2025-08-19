# Moonshot Alpha v0.6.4

Moonshot Alpha is a modular, multi‑agent framework for **planning and estimating complex software projects**.  It combines conversational Large Language Model (LLM) prompts to produce actionable **architectural plans**, **project timelines**, **cost estimates**, **security recommendations**, and more.  The goal of this release is to provide a ready‑to‑run reference implementation that can be run locally or in Docker for experimentation, prototyping and education.

**What’s new in v0.6.4:** Added optional DocumentationAgent for end‑of‑project technical documentation, updated UI and bumped version.

## Features

* **Multi‑agent orchestration** – Runs up to twelve LLM‑driven agents in parallel, including an optional documentation agent, to produce a holistic project plan. Agents can be batched or disabled to control cost, and each returns structured JSON for easy integration.
* **Cross‑platform CLI** – Script for running agents on a project description (`cli.py`). Prompts for the desired LLM, prints colourised logs to the terminal, and supports selecting a subset of agents via `--agents`.
* **REST API** – A FastAPI service exposes endpoints for health checks, listing agents, running the orchestrator and (optionally) exporting results to an Excel `.xls` file.
* **SaaS Web UI** – A Tailwind-styled front‑end served from the API at `/ui`. Users can select which agents to run, watch per‑agent progress bars, authenticate via Google (Supabase), export to XLS and view their latest predictions.
* **Supabase persistence (optional)** – When configured, results are **persisted per user** to a Supabase table after each run.  Users authenticate using Google OAuth via Supabase; the API verifies their JSON Web Token (JWT) and stores the description, user ID and JSON results in a `project_runs` table.  The endpoint (`/projects/latest`) returns the most recent prediction for each description for the authenticated user.
* **Dockerised deployment** – A `Dockerfile` and `docker-compose.yml` build reproducible images for the CLI/Jupyter (port 8888), API (port 8000) and Ollama model server.  No local Python installation is required.
* **AI coding delegation analysis** – An AICoding agent identifies features that can be automated and estimates potential AI coverage.

Additional role descriptions and AI delegation guidelines are available in `docs/human_resources.md`.

## Repository Structure

```
moonshot-poc-main/
├── Dockerfile               # Build instructions for the Python environment
├── docker-compose.yml       # Defines the Jupyter (8888), API (8000), CLI and Ollama services
├── .env.example             # Template for environment variables (including Supabase)
├── requirements.txt         # Python dependencies, including LLM libs, FastAPI and Supabase
├── config/
│   └── cost_config.json     # Input for CostEstimatorAgent (rates, constraints, cloud costs)
├── frontend/
│   ├── index.html           # Simple SaaS UI served at /ui
│   └── main.js              # Client‑side logic (run, auth, history)
├── docs/
│   └── human_resources.md   # Roles and AI delegation guidelines
├── notebooks/               # Example notebooks (e.g. verbose_demo.ipynb)
├── src/
│   ├── api/
│   │   └── main.py          # FastAPI app exposing `/health`, `/agents`, `/run`, `/projects/latest`
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── architect_agent.py
│   │   ├── project_manager_agent.py
│   │   ├── cost_estimator_agent.py
│   │   ├── security_agent.py
│   │   ├── devops_agent.py
│   │   ├── performance_agent.py
│   │   ├── data_agent.py
│   │   ├── ux_agent.py
│   │   ├── data_scientist_agent.py
│   │   ├── ai_coding_agent.py
│   │   ├── technical_agent.py
│   │   └── documentation_agent.py
├── cli.py               # Run selected agents on a project description (PDF input)
├── export_to_excel.py  # Utility to flatten and export results as `.xls`
├── export_to_pdf.py    # Utility to save technical documentation as PDF
├── orchestrator.py      # VerboseOrchestrator coordinating all agents
└── config.py            # Factory to create LLM clients for Ollama or cloud providers
```

## Getting Started

### Prerequisites

1. **Docker** and **docker‑compose** installed (recommended for a reproducible environment).  Alternatively, ensure **Python 3.11+** is available if running locally.
2. API keys for whichever cloud providers you plan to use (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MOONSHOT_API_KEY`).
3. (Optional) A **Supabase project** with **Google sign‑in enabled** if you want to persist results per user.  You must create a table called `project_runs` with the following columns:

   | Column       | Type     | Notes                                               |
   |-------------:|----------|-----------------------------------------------------|
   | `id`         | `uuid`   | Primary key (generated in the API)                 |
   | `user_id`    | `uuid`   | Supabase user ID (from the JWT)                    |
    | `description`| `text`   | Project description provided by the user            |
    | `results`    | `jsonb`  | JSON results from all agents                       |
   | `created_at` | `timestamp` | Default `now()` (set via Supabase)                |

### Environment Configuration

Copy `.env.example` to `.env` in the repository root and fill out the variables:

| Variable                     | Description                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------|
| `MOONSHOT_API_KEY`          | Your Moonshot or Kimi K2 API key for the LLM agents.                                         |
| `OPENAI_API_KEY`            | API key for OpenAI models (if using the OpenAI provider).                                     |
| `ANTHROPIC_API_KEY`         | API key for Anthropic models (if using the Anthropic provider).                               |
| `OLLAMA_HOST`              | URL of the Ollama server (defaults to `http://ollama:11434`).                                 |
| `XLS_EXPORT_ENABLED`        | `true` or `false`.  When `true`, results are automatically exported to an XLS file.          |
| `XLS_EXPORT_PATH`           | Destination path for the XLS file (default `/workspace/results.xls`).                       |
| `AGENT_MAX_RETRIES`         | Maximum number of retries per agent (default `100`).                                         |
| `SUPABASE_URL`              | Base URL of your Supabase project (e.g. `https://xyzcompany.supabase.co`).                   |
| `SUPABASE_ANON_KEY`         | Anonymous key for client‑side authentication in the web UI.                                 |
| `SUPABASE_SERVICE_KEY`      | Service key used by the API to insert/query records.                                        |

If you are not using XLS export or Supabase, leave the related variables blank or set `XLS_EXPORT_ENABLED=false`.

### Setting Up Supabase Persistence

1. Create a **Supabase project** at <https://app.supabase.com/>.
2. Enable **Google OAuth** under *Authentication → Providers*.
3. Create the `project_runs` table described above (via SQL editor or the table designer).  A typical DDL statement might look like:

```sql
create table project_runs (
    id uuid primary key,
    user_id uuid not null,
    description text not null,
    results jsonb not null,
    created_at timestamp with time zone default now()
);

alter table project_runs enable row level security;

-- Optionally define policies to allow insert/select for authenticated users
create policy "Allow insert for authenticated users" on project_runs
    for insert using (auth.uid() = user_id);

create policy "Allow select own records" on project_runs
    for select using (auth.uid() = user_id);
```

4. Obtain your **API URL**, **anon key** and **service key** from the Supabase dashboard (Project → API → Settings).  Put these values in `.env` as `SUPABASE_URL`, `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_KEY` respectively.
5. The web UI uses `SUPABASE_ANON_KEY` to authenticate users via Google.  The API uses `SUPABASE_SERVICE_KEY` to insert and query runs.  If these are not set, persistence will be disabled and authentication will be ignored.

## Building and Running with Docker

1. Copy `.env.example` to `.env` and fill in the required variables.
2. Build and start the services (including the Ollama model server) in detached mode:

```bash
docker compose up --build -d
```

3. The following endpoints will be available:

| Service        | URL                                      | Notes                                                |
|---------------:|-------------------------------------------|------------------------------------------------------|
| **JupyterLab** | <http://localhost:8888/?token=agent123>    | Token is set via `JUPYTER_TOKEN` in `docker-compose.yml`.  Use the provided notebook example to run the orchestrator and inspect results. |
| **API**        | <http://localhost:8000>                   | Swagger docs at `/docs`.  Exposes the endpoints listed below. |
| **Web UI**     | <http://localhost:8000/ui>                | Authenticate via Google and run agents from the browser. |
| **Ollama**     | <http://localhost:11434>                  | Serves local models used by the CLI/API when selected. |

4. To view container logs use `docker logs moonshot-jupyter` or `docker logs moonshot-api`.

### Running Locally (Without Docker)

If you prefer running locally:

```bash
# Clone the repo and enter it (replace with your fork or local path)
git clone https://github.com/Capybaralifestyle/moonshot-poc.git
cd moonshot-poc

# Create a Python virtualenv and activate it
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in variables
cp .env.example .env

# Run the API
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Or run the CLI (inside Docker)
docker compose run --rm cli -  # enter description interactively
```

## Using the CLI Tools

### Main Orchestrator CLI

Run agents on a description (you will be prompted to choose a local or cloud model):

```bash
# Provide a PDF file with a high‑level project description
docker compose run --rm cli path/to/description.pdf

# Run only the architect and project manager agents to reduce cost
docker compose run --rm cli my_project.pdf --agents architect,pm

# Or omit the PDF and type the description interactively
docker compose run --rm cli -

# Add --export to override the XLS export flag for this run
docker compose run --rm cli my_project.pdf --export
```

## Using the REST API

### Health Check

```bash
curl -s http://localhost:8000/health
# → {"status":"ok"}
```

### List Available Agents

```bash
curl -s http://localhost:8000/agents
# → ["architect","pm","cost","security","devops","performance","data","ux","datasci","aicoding","technical"]
```

### Run All Agents

Run the orchestrator on your project description. If Supabase persistence is enabled, include your access token in the `Authorization` header (Bearer token) to persist the results. Without a token, the API still returns results but does not store them.

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>" \
  -d '{"description": "Global AI FinTech platform…", "export_enabled": false}'
```



### Get Latest Predictions (Supabase)

Returns the most recent prediction for each description for the authenticated user.

```bash
curl -s http://localhost:8000/projects/latest \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>"
# → {"runs":[{ "id": "…", "user_id": "…", "description": "…", "results": {...}, "created_at": "…" }, …]}
```

## SaaS Web Interface

Navigate to <http://localhost:8000/ui> to use the web interface:

1. **Sign in with Google** – Click the “Accedi con Google” button.  A Supabase popup will handle OAuth authentication.  Once logged in, your email will appear in the header and the run section will become available.
2. **Run a Project** – Enter a high‑level project description and optionally toggle “Export to XLS.”  The results appear below as formatted JSON.
3. **View History** – The “Recent Runs” section lists your latest predictions per description.  These are pulled from Supabase and update automatically after each run.
4. **Export to XLS** – If `XLS_EXPORT_ENABLED=true` in your `.env`, results will also be written to the configured XLS file.  You can override this per request via the UI checkbox or the API.

## Limitations and Future Work

* **Experimental quality** – This is an early alpha release intended for exploration and experimentation.  Error handling, security, scalability and stability need further work for production use.
* **LLM cost and latency** – Running many agents in parallel can be slow and expensive. Use the CLI `--agents` option or UI checkboxes to batch or disable agents as needed.
* **Supabase policies** – You may need to customise row‑level security policies on the `project_runs` table depending on your use case.
* **UI** – The SaaS front‑end is intentionally simple and may require customisation for enterprise use (e.g. styling, field validation, progress feedback).

## License

This project is provided for educational purposes under the MIT License.  You are free to use, modify and distribute the code with proper attribution.  See `LICENSE` (if provided) for details.
