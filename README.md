# Moonshot Alpha v0.1

Moonshot Alpha is a modular, multi‑agent framework for **planning and estimating complex software projects**.  It combines conversational Large Language Model (LLM) prompts with conventional machine‑learning techniques to produce actionable **architectural plans**, **project timelines**, **cost estimates**, **security recommendations**, and more.  Version 0.1 (Alpha) extends the original proof‑of‑concept with a **data‑driven estimator**, exploratory data analysis tools, a simple SaaS web interface, and optional **Supabase persistence with Google authentication**.  The goal of this release is to provide a ready‑to‑run reference implementation that can be run locally or in Docker for experimentation, prototyping and education.

## Features

* **Multi‑agent orchestration** – Runs nine LLM‑driven agents and one machine‑learning agent in parallel to produce a holistic project plan.  Each agent returns structured JSON for easy integration.
* **Data‑driven cost estimation** – `DatasetMLAgent` loads CSV or ARFF datasets containing an `effort` column and evaluates multiple regression algorithms (Random Forest, Extra Trees, Gradient Boosting, Linear Regression).  It reports RMSE/MAE metrics, highlights top features, computes prediction intervals from residuals and flags potential outliers.  If a `DOMAIN_COLUMN` is specified, the agent trains separate models for each distinct domain value and reports per‑domain metrics.
* **Exploratory data analysis (EDA)** – `cli_eda.py` prints dataset shape, column types, missing values, descriptive statistics, top numeric correlations, domain distributions and IsolationForest‑based outliers with colourised output.
* **Cross‑platform CLI** – Scripts for running all agents on a project description (`cli.py`), invoking the data‑driven estimator (`cli_dataset.py`) and running EDA (`cli_eda.py`).  These tools print colourised logs to the terminal.
* **REST API** – A FastAPI service exposes endpoints for health checks, listing agents, running the orchestrator, uploading datasets, running with a specific dataset and (optionally) exporting results to Google Sheets.
* **SaaS Web UI** – A simple front‑end served from the API at `/ui`.  Users can upload datasets, select a domain column, provide a project description and run the multi‑agent orchestrator directly from the browser.  The UI includes Google authentication via Supabase and displays the latest predictions for each user.
* **Supabase persistence (optional)** – When configured, results are **persisted per user** to a Supabase table after each run.  Users authenticate using Google OAuth via Supabase; the API verifies their JSON Web Token (JWT) and stores the description, dataset ID, user ID and JSON results in a `project_runs` table.  A new API endpoint (`/projects/latest`) returns the most recent prediction for each description/dataset combination for the authenticated user.
* **Dockerised deployment** – A `Dockerfile` and `docker-compose.yml` build reproducible images for the CLI/Jupyter (port 8888) and API services (port 8000).  No local Python installation is required.

## Repository Structure

```
moonshot-poc-main/
├── Dockerfile               # Build instructions for the Python environment
├── docker-compose.yml       # Defines the Jupyter (8888) and API (8000) services
├── .env.example             # Template for environment variables (including Supabase)
├── requirements.txt         # Python dependencies, including LLM libs, scikit‑learn, FastAPI and Supabase
├── config/
│   └── cost_config.json     # Input for CostEstimatorAgent (rates, constraints, cloud costs)
├── data/                    # Placeholder for user datasets (tmpdata is used at runtime)
├── frontend/
│   ├── index.html           # Simple SaaS UI served at /ui
│   └── main.js              # Client‑side logic (dataset upload, run, auth, history)
├── notebooks/               # Example notebooks (e.g. verbose_demo.ipynb)
├── src/
│   ├── api/
│   │   └── main.py          # FastAPI app exposing `/health`, `/agents`, `/run`, `/datasets`, `/projects/run`, `/projects/latest`
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
│   │   └── dataset_ml_agent.py  # Non‑LLM machine‑learning estimator
│   ├── cli.py               # Run all agents on a project description (PDF input)
│   ├── cli_dataset.py       # Invoke the DatasetMLAgent and display metrics
│   ├── cli_eda.py           # Exploratory data analysis tool for datasets
│   ├── export_to_sheets.py  # Utility to flatten and send results to Google Sheets
│   ├── orchestrator.py      # VerboseOrchestrator coordinating all agents
│   └── config.py            # Configures the LLM (ChatOpenAI) using the MOONSHOT_API_KEY
└── README.md               # You’re reading it
```

## Getting Started

### Prerequisites

1. **Docker** and **docker‑compose** installed (recommended for a reproducible environment).  Alternatively, ensure **Python 3.11+** is available if running locally.
2. A **Moonshot API key** (`MOONSHOT_API_KEY`) to enable the LLM‑based agents.  Without a valid key the LLM agents will raise errors.  The machine‑learning agent does not require a key.
3. (Optional) A **Google Sheets service‑account JSON** if you plan to export results.  Provide its path in `GCP_SERVICE_ACCOUNT_JSON`.
4. (Optional) A **Supabase project** with **Google sign‑in enabled** if you want to persist results per user.  You must create a table called `project_runs` with the following columns:

   | Column       | Type     | Notes                                               |
   |-------------:|----------|-----------------------------------------------------|
   | `id`         | `uuid`   | Primary key (generated in the API)                 |
   | `user_id`    | `uuid`   | Supabase user ID (from the JWT)                    |
   | `description`| `text`   | Project description provided by the user            |
   | `dataset_id` | `text`   | Dataset identifier (optional)                      |
   | `results`    | `jsonb`  | JSON results from all agents                       |
   | `created_at` | `timestamp` | Default `now()` (set via Supabase)                |

### Environment Configuration

Copy `.env.example` to `.env` in the repository root and fill out the variables:

| Variable                     | Description                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------|
| `MOONSHOT_API_KEY`          | Your Moonshot or Kimi K2 API key for the LLM agents.                                         |
| `DATASET_PATH`              | Absolute or container‑relative path to a cost‑estimation dataset (CSV or ARFF) for the ML agent.  The dataset **must** contain an `effort` column (case‑insensitive).                              |
| `DOMAIN_COLUMN`             | (Optional) Name of a categorical column in the dataset for which you want separate models.    |
| `SHEETS_EXPORT_ENABLED`     | `true` or `false`.  When `true`, results are automatically exported to a Google Sheet.         |
| `SHEETS_EXPORT_NAME`        | Name of the Google Sheet to write to.                                                       |
| `GCP_SERVICE_ACCOUNT_JSON`  | Path to a service account JSON file with permissions to Sheets.                              |
| `SHEETS_WORKSHEET_INDEX`    | Worksheet index (0‑based) within the sheet.                                                 |
| `SUPABASE_URL`              | Base URL of your Supabase project (e.g. `https://xyzcompany.supabase.co`).                   |
| `SUPABASE_ANON_KEY`         | Anonymous key for client‑side authentication in the web UI.                                 |
| `SUPABASE_SERVICE_KEY`      | Service key used by the API to insert/query records.                                        |

If you are not using Google Sheets or Supabase, leave the related variables blank or set `SHEETS_EXPORT_ENABLED=false`.

### Setting Up Supabase Persistence

1. Create a **Supabase project** at <https://app.supabase.com/>.
2. Enable **Google OAuth** under *Authentication → Providers*.
3. Create the `project_runs` table described above (via SQL editor or the table designer).  A typical DDL statement might look like:

```sql
create table project_runs (
    id uuid primary key,
    user_id uuid not null,
    description text not null,
    dataset_id text,
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
2. Build and start the services in detached mode:

```bash
docker compose up --build -d
```

3. The following endpoints will be available:

| Service        | URL                                      | Notes                                                |
|---------------:|-------------------------------------------|------------------------------------------------------|
| **JupyterLab** | <http://localhost:8888/?token=agent123>    | Token is set via `JUPYTER_TOKEN` in `docker-compose.yml`.  Use the provided notebook example to run the orchestrator and inspect results. |
| **API**        | <http://localhost:8000>                   | Swagger docs at `/docs`.  Exposes the endpoints listed below. |
| **Web UI**     | <http://localhost:8000/ui>                | Upload datasets, authenticate via Google and run agents from the browser. |

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

# Or run the CLI
python src/cli.py -  # enter description interactively
```

## Using the CLI Tools

### Main Orchestrator CLI

Run all agents on a description:

```bash
# Provide a PDF file with a high‑level project description
python src/cli.py path/to/description.pdf

# Or omit the PDF and type the description interactively
python src/cli.py -

# Add --export to override the Sheets export flag for this run
python src/cli.py my_project.pdf --export
```

### Dataset Estimator CLI

Invoke the data‑driven estimator and see metrics:

```bash
# Path overrides DATASET_PATH; if omitted, uses the env var
python src/cli_dataset.py --dataset data/isbsg_cosmic.csv

# You can also specify DOMAIN_COLUMN in .env for per‑domain models
```

### EDA CLI

Quick exploratory data analysis:

```bash
python src/cli_eda.py data/isbsg_cosmic.csv --domain-col Application_Group

# Reports dataset shape, types, missing values, summary statistics,
# top correlations, domain distribution and potential outliers.
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
# → ["architect","pm","cost","security","devops","performance","data","ux","datasci","dataset_ml"]
```

### Run All Agents (No Dataset)

Run the orchestrator on a plain description.  If Supabase persistence is enabled, include your access token in the `Authorization` header (Bearer token) to persist the results.  Without a token, the API still returns results but does not store them.

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>" \
  -d '{"description": "Global AI FinTech platform: micro‑payments, fraud AI, robo‑advisors, carbon trading, 24 months, $4.5M.", "export_enabled": false}'
```

### Upload a Dataset

```bash
curl -s -X POST http://localhost:8000/datasets \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>" \
  -F "file=@dataset.csv" \
  -F "domain_column=Industry_Sector"
# → {"dataset_id":"123e4567-e89b-12d3-a456-…_dataset.csv"}
```

### List Datasets

```bash
curl -s http://localhost:8000/datasets
# → ["123e4567-e89b-12d3-a456-…_dataset.csv", …]
```

### Run with a Specific Dataset

```bash
curl -s -X POST http://localhost:8000/projects/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>" \
  -d '{"description": "Global AI FinTech platform…", "dataset_id": "123e4567-e89b-12d3-a456-…_dataset.csv", "export_enabled": false}'
```

### Get Latest Predictions (Supabase)

Returns the most recent prediction for each description/dataset combination for the authenticated user.

```bash
curl -s http://localhost:8000/projects/latest \
  -H "Authorization: Bearer <YOUR_SUPABASE_ACCESS_TOKEN>"
# → {"runs":[{ "id": "…", "user_id": "…", "description": "…", "dataset_id": "…", "results": {...}, "created_at": "…" }, …]}
```

## SaaS Web Interface

Navigate to <http://localhost:8000/ui> to use the web interface:

1. **Sign in with Google** – Click the “Accedi con Google” button.  A Supabase popup will handle OAuth authentication.  Once logged in, your email will appear in the header and the dataset and run sections will become available.
2. **Upload a Dataset** – Choose a CSV or ARFF file containing an `effort` column.  Optionally specify a domain column (categorical) used for per‑domain models.
3. **Run a Project** – Select a dataset, enter a high‑level project description and optionally toggle “Export to Sheets.”  The results appear below as formatted JSON.
4. **View History** – The “Previsioni recenti” section lists your latest predictions per description/dataset.  These are pulled from Supabase and update automatically after each run.
5. **Export to Google Sheets** – If `SHEETS_EXPORT_ENABLED=true` in your `.env`, results will also be written to the configured Google Sheet.  You can override this per request via the UI checkbox or the API.

## Limitations and Future Work

* **Experimental quality** – This is an early alpha release intended for exploration and experimentation.  Error handling, security, scalability and stability need further work for production use.
* **LLM cost and latency** – Running many agents in parallel can be slow and expensive.  Consider batching or disabling agents as needed.
* **Data quality** – The machine‑learning estimator assumes clean numeric/categorical data and may produce poor results on noisy or sparse datasets.
* **Supabase policies** – You may need to customise row‑level security policies on the `project_runs` table depending on your use case.
* **UI** – The SaaS front‑end is intentionally simple and may require customisation for enterprise use (e.g. styling, field validation, progress feedback).

## License

This project is provided for educational purposes under the MIT License.  You are free to use, modify and distribute the code with proper attribution.  See `LICENSE` (if provided) for details.