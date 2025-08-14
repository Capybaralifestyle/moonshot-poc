# Moonshot POC v5

Moonshot POC is a modular, multi‑agent framework for planning and estimating complex software projects.  It combines conversational large‑language‑model prompts with conventional machine‑learning techniques to produce actionable plans, schedules, cost estimates and more.  Version 5 extends the original proof‑of‑concept with a data‑driven estimator, exploratory data analysis tools, domain‑specific calibration, outlier detection and prediction intervals.

## Overview

Moonshot comprises a set of specialised “agents,” each responsible for a different aspect of project planning.  These agents run in parallel via the **VerboseOrchestrator**, which collects their JSON responses and optionally exports them to Google Sheets.  The core LLM‑based agents cover architecture, project management, cost estimation, security, DevOps, performance engineering, data pipelines, UX design and data science.  A separate **DatasetMLAgent** is entirely non‑LLM and trains regression models on historical datasets (e.g., ISBSG/COSMIC) to predict effort.  Auxiliary command‑line tools and an API make it easy to operate the system from scripts or the browser, while Docker ensures a reproducible environment.

## Features

- **Multi‑agent orchestration:** Runs nine LLM‑driven agents and one machine‑learning agent to produce a holistic project plan.  Each agent returns structured JSON for easy integration.
- **Dataset‑driven cost estimation:** `DatasetMLAgent` loads CSV or ARFF datasets containing an `effort` column and evaluates multiple regression algorithms (Random Forest, Extra Trees, Gradient Boosting, Linear Regression).  It reports RMSE/MAE metrics, highlights top features, computes prediction intervals from residuals and flags potential outliers.  If a `DOMAIN_COLUMN` is specified, the agent trains separate models for each distinct domain value and reports per‑domain metrics.
- **Exploratory data analysis (EDA):** `cli_eda.py` prints dataset shape, column types, missing values, descriptive statistics, top numeric correlations, domain distributions and IsolationForest‑based outliers with colourised output.
- **Cross‑platform CLI:**
  - `cli.py` reads a project description (PDF or manual input) and runs all agents, displaying colour‑coded logs for each agent.  The CLI works on Linux, macOS and Windows.
  - `cli_dataset.py` runs the data‑driven estimator, performing cross‑validated training and presenting metrics, prediction intervals, outliers and domain‑specific summaries.
- **REST API:** A FastAPI service exposes `/health`, `/agents` and `/run` endpoints so you can integrate the orchestrator into other systems.  The service shares code with the CLI and uses the same environment variables.
- **JupyterLab environment:** A preconfigured Jupyter container lets you interactively run the agents and inspect their responses.  An example notebook (see the documentation in the repo) demonstrates how to log results live and export them to Google Sheets.
- **Dockerised deployment:** The provided `Dockerfile` and `docker-compose.yml` build reproducible images for the CLI/Jupyter and API services.  No local Python installation is required.
- **Google Sheets export:** When `SHEETS_EXPORT_ENABLED=true` the orchestrator automatically writes results to a spreadsheet via the credentials specified in `.env`.  You can override this behaviour per request.
- **Colourful logging:** Outputs from each agent are printed in distinct colours, making it easy to follow the verbose process.

- **SaaS Frontend (v6):**  Version 6 adds a simple web front‑end served from the API at `/ui`.  Users can upload datasets, select a domain column, provide a project description and run the multi‑agent orchestrator directly from the browser.  Uploaded datasets are stored in memory and assigned unique IDs; runs can be exported to Google Sheets if desired.  The API now exposes `/datasets` for uploads and listing, and `/projects/run` for orchestrating with a chosen dataset.

## Repository Structure

```
moonshot-poc-v6/
├── Dockerfile               # Build instructions for the Python environment
├── docker-compose.yml       # Defines the Jupyter (8888) and API (8000) services
├── .env.example             # Template for environment variables
├── requirements.txt         # Python dependencies, including LLM libs, scikit‑learn and FastAPI
├── config/
│   └── cost_config.json     # Input for CostEstimatorAgent (rates, constraints, cloud costs)
├── src/
│   ├── __init__.py
│   ├── config.py            # Configures the LLM (ChatOpenAI) using the MOONSHOT_API_KEY
│   ├── export_to_sheets.py  # Utility to flatten and send results to Google Sheets
│   ├── orchestrator.py      # VerboseOrchestrator coordinating all agents
│   ├── cli.py               # Run all agents on a project description (PDF input)
│   ├── cli_dataset.py       # Invoke the DatasetMLAgent and display metrics
│   ├── cli_eda.py           # Exploratory data analysis tool for datasets
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI app exposing `/health`, `/agents`, `/run`
│   └── agents/
│       ├── __init__.py
│       ├── base_agent.py
│       ├── architect_agent.py
│       ├── project_manager_agent.py
│       ├── cost_estimator_agent.py
│       ├── security_agent.py
│       ├── devops_agent.py
│       ├── performance_agent.py
│       ├── data_agent.py
│       ├── ux_agent.py
│       ├── data_scientist_agent.py
│       └── dataset_ml_agent.py  # Non‑LLM machine‑learning estimator
│   ├── frontend/               # HTML/JS assets for the SaaS UI (v6 only)
│   │   ├── index.html
│   │   └── main.js
└── README.md               # You’re reading it
```

## Getting Started

### Prerequisites

1. **Docker** and **docker‑compose** installed (for the recommended containerised deployment).  Alternatively, ensure Python 3.11+ is available if running locally.
2. A **Moonshot API key** (`MOONSHOT_API_KEY`) to enable the LLM‑based agents.  Without a valid key the LLM agents will raise errors.  The machine‑learning agent does not require a key.
3. (Optional) A **Google Sheets service‑account JSON** if you plan to export results.  Provide its path in `GCP_SERVICE_ACCOUNT_JSON`.

### Environment Configuration

1. Copy `.env.example` to `.env` in the repository root and fill out the variables:
   - `MOONSHOT_API_KEY`: your Moonshot or Kimi K2 API key.
   - `DATASET_PATH`: absolute or container‑relative path to a cost‑estimation dataset (CSV or ARFF).  The dataset **must** contain an `effort` column (case‑insensitive).
   - `DOMAIN_COLUMN` (optional): name of a categorical column in the dataset for which you want separate models (e.g. `Application_Group`, `Industry_Sector`).  Leave blank to disable per‑domain calibration.
   - `SHEETS_EXPORT_ENABLED`, `SHEETS_EXPORT_NAME`, `GCP_SERVICE_ACCOUNT_JSON`, `SHEETS_WORKSHEET_INDEX`: control Google Sheets export (see `.env.example` for guidance).
2. If you plan to run the CLI outside Docker, install dependencies with `pip install -r requirements.txt` in a Python 3.11 environment.

### Building and Running with Docker

1. Build and start the services in detached mode:

   ```bash
   cp .env.example .env  # customise this file first
   docker compose up --build -d
   ```

2. The following endpoints will be available:
   - **JupyterLab**: http://localhost:8888/?token=agent123 (token is set via `JUPYTER_TOKEN` in `docker-compose.yml`).  Use the provided notebook example to run the orchestrator and inspect results.
   - **FastAPI service**: http://localhost:8000 (Swagger docs at `/docs`).  Try `GET /health`, `GET /agents` and `POST /run`.

3. To view container logs: `docker logs moonshot-jupyter` or `docker logs moonshot-api`.

### Running the CLI Tools (Local or in Docker)

- **Main orchestrator CLI** – run all agents on a description:

  ```bash
  # Provide a PDF file with a high‑level project description
  python src/cli.py path/to/description.pdf

  # Or omit the PDF and type the description interactively
  python src/cli.py -
  ```

  The CLI prints verbose logs in colour for each agent.  Add `--export` to override the Sheets export flag for this run.

- **Dataset estimator CLI** – evaluate a dataset and see metrics:

  ```bash
  # Path overrides DATASET_PATH; if omitted, uses the env var
  python src/cli_dataset.py --dataset data/isbsg_cosmic.csv
  ```

  Output includes best model name, RMSE/MAE, top feature importances, prediction interval, the five most anomalous rows and per‑domain summaries (if `DOMAIN_COLUMN` is set).

- **EDA CLI** – quick exploratory data analysis:

  ```bash
  python src/cli_eda.py data/isbsg_cosmic.csv --domain-col Application_Group
  ```

  This tool reports dataset shape, types, missing values, summary statistics, top correlations, domain distribution and potential outliers.

### Using the REST API

After running `docker compose up`, the API is available at `http://localhost:8000`.

**Health Check:**

```bash
curl -s http://localhost:8000/health
```

**List Agents:**

```bash
curl -s http://localhost:8000/agents
```

**Run Orchestrator:**

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"description": "Global AI FinTech platform: micro‑payments, fraud AI, robo‑advisors, carbon trading, 24 months, $4.5M.", "export_enabled": false}'
```

The POST body accepts a `description` (string) and an optional `export_enabled` boolean to override the `SHEETS_EXPORT_ENABLED` environment variable for that request.
\
**Upload a dataset:**\
\
```bash\
# Replace dataset.csv with your local CSV or ARFF file.  Optionally pass a domain column.\
curl -s -X POST http://localhost:8000/datasets \\\n+  -F "file=@dataset.csv" \\\n+  -F "domain_column=Industry_Sector"\
# → {"dataset_id":"123e4567-e89b-12d3-a456-…_dataset.csv"}\
```\
\
**List datasets:**\
\
```bash\
curl -s http://localhost:8000/datasets\
```\
\
**Run with a specific dataset:**\
\
```bash\
curl -s -X POST http://localhost:8000/projects/run \\\n+  -H "Content-Type: application/json" \\\n+  -d '{"description": "Global AI FinTech platform…", "dataset_id": "<dataset_id>", "export_enabled": false}'\
```\
\
The SaaS UI is served at `http://localhost:8000/ui`.  Navigate there in your browser to upload a dataset and run the agents without using the command line.\

### Jupyter Notebook Demo

In the `src` folder you’ll find a notebook outline in the documentation.  Open JupyterLab, create a new notebook and execute the provided cells:

1. **Imports and logger:** sets up a log viewer widget and imports the orchestrator.
2. **Run all agents:** instantiates `VerboseOrchestrator`, runs it on a description and shows results.  If `SHEETS_EXPORT_ENABLED=true`, results are exported automatically.
3. **PDF helper cell:** demonstrates how to convert generated PDFs to text using PyMuPDF (already installed).

Refer to the comments in the notebook for details.

## Agents in Detail

Each agent inherits from `BaseAgent` and implements two methods: `build_prompt(data: Dict[str, Any])` to construct the LLM prompt and `analyze(data: Dict[str, Any])` to post‑process the LLM’s JSON response.  Here is an overview of their roles:

| Agent | Purpose | Output |
| --- | --- | --- |
| **ArchitectAgent** | Designs the high‑level cloud architecture, including language stack, messaging/streaming platforms, cloud provider services, infrastructure as code, CI/CD and observability tools. | JSON with nested sections for backend, messaging, cloud choices, security controls and estimated cost per day. |
| **ProjectManagerAgent** | Produces a project timeline with a fixed duration (e.g. 112 days) and a Gantt‑style list of tasks, owners and start days. | JSON with `duration_days` and `gantt` array entries. |
| **CostEstimatorAgent** | Builds a daily cost breakdown using `cost_config.json` as the single source of truth.  It respects budget constraints and returns a summary. | JSON with currency, constraints, assumptions, daily breakdown and summary totals. |
| **SecurityAgent** | Recommends threat models, security controls, compliance frameworks and a penetration‑test plan tailored to the project. | JSON listing threat model frameworks (e.g. OWASP, STRIDE), controls (OAuth, Vault, KMS) and compliance standards. |
| **DevOpsAgent** | Specifies container base images, Kubernetes manifests, scaling, ingress, GitOps tools, CI/CD pipelines and observability stacks. | JSON with sections for containerization, Kubernetes, GitOps, CI/CD and observability. |
| **PerformanceAgent** | Defines service‑level objectives (latency, availability), identifies bottleneck risks, proposes tuning knobs, outlines performance test plans and estimates capacity. | JSON with SLO values, lists of bottlenecks, tuning options, test scenarios and a capacity model. |
| **DataAgent** | Describes storage choices for OLTP, streaming and object data, schema governance strategies, ingest/processing/batch pipelines and data quality checks. | JSON with storage, schema governance, pipelines and data quality sections. |
| **UXAgent** | Crafts user personas, customer journeys, UI patterns and non‑functional requirements for a FinTech‑grade product. | JSON with arrays of personas, journeys, UI patterns and non‑functional traits. |
| **DataScientistAgent** | Develops a production‑ready data‑science plan: problem framing, data design, evaluation protocol, baselines and candidate models, MLOps pipeline, experiment backlog and data contracts. | JSON following a strict schema with nested dictionaries for each plan section. |
| **DatasetMLAgent** | Loads a dataset from `DATASET_PATH`, detects the `effort` target column, label‑encodes categoricals, imputes missing values, trains several regressors and reports metrics.  Computes 95 % prediction intervals from residuals, detects outliers via IsolationForest and optionally trains per‑domain models. | JSON containing the best model, its RMSE/MAE, top features, all model metrics, prediction interval, list of outliers and domain‑specific model summaries (if configured). |

## Usage Tips

- **Dataset Format:** The dataset must include an `effort` column.  Additional numeric and categorical columns are used as features.  Use ARFF or CSV.  Missing numeric values are imputed with the column mean; categorical variables are label‑encoded.  To avoid misleading models, clean your data first.
- **Domain Calibration:** If you set `DOMAIN_COLUMN` to a column name, the dataset agent will train separate models for each unique value.  Ensure each group has at least five rows; small groups are skipped to avoid unstable metrics.
- **Outlier Interpretation:** IsolationForest identifies unusual combinations of feature values.  Review these rows manually to decide whether they represent true anomalies or rare but valid projects.
- **Prediction Interval:** The interval uses the 2.5 % and 97.5 % quantiles of residuals from cross‑validation.  Wider intervals indicate more uncertainty in the model.
- **Performance Considerations:** The ML agent uses 5‑fold cross‑validation.  Large datasets may slow down evaluation; adjust the `n_estimators` parameters or reduce folds in the code if needed.

## Contributing

Contributions are welcome.  To add a new agent, create a subclass of `BaseAgent`, implement `build_prompt()` and `analyze()`, and register it in `orchestrator.py`.  When modifying prompts, ensure they return only valid JSON and do not invent keys.  For enhancements to the ML agent, follow the patterns in `dataset_ml_agent.py`, adding new algorithms or preprocessing steps as needed.  Pull requests should include updated documentation and tests.

## License

This project is provided as a learning example without warranty.  It is licensed under the MIT License.  See `LICENSE` for details.