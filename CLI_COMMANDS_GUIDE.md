# CLI Commands & Operational Guide (`CLI_COMMANDS_GUIDE.md`)

This guide serves as an authoritative operational reference for LLM Agents developing, testing, provisioning, and deploying the **Kubernetes Troubleshooting Agent** (`opsta_k8s_agent`). It captures exact commands, required flags, tested parameters, and platform quirks learned during project execution to eliminate trial-and-error discovery.

---

## 1. `google-agents-cli` (`agents-cli`)

### Local Evaluation
Runs routing and tool-calling evaluations locally against test datasets.
```bash
uvx google-agents-cli@1.1.0 eval \
  --dataset tests/evals/eval_dataset.json \
  --agent app/agent.py:opsta_k8s_agent
```

### Agent Engine Deployment (Agent Runtime)
Deploys or updates an agent on GCP Agent Runtime / Vertex AI Reasoning Engine.

> [!IMPORTANT]
> **Zero Minimum Instance Flag**: `agents-cli deploy` defaults to `--min-instances 1` if omitted. You **MUST** explicitly pass `--min-instances 0` to scale down to zero when idle for cost optimization.
> **Required IAM Role**: The deployment service account / runner requires `roles/aiplatform.admin` on the target GCP project (`roles/aiplatform.user` alone results in `403 PERMISSION_DENIED`).

```bash
uvx google-agents-cli@1.1.0 deploy \
  --project <PROJECT_ID> \
  --region asia-southeast1 \
  --min-instances 0 \
  --max-instances 10 \
  --service-account=<APP_SERVICE_ACCOUNT_EMAIL> \
  --update-env-vars="COMMIT_SHA=${GITHUB_SHA},LOGS_BUCKET_NAME=${LOGS_BUCKET}"
```

### Deploy Command Options Reference
* `--project TEXT`: Target GCP project ID (e.g. `zcloud-cicd`).
* `--region TEXT`: Target GCP region (e.g. `asia-southeast1`).
* `--min-instances INTEGER`: Minimum instances (set to `0`).
* `--max-instances INTEGER`: Maximum scaling limit (default: `10`).
* `--service-account TEXT`: App Service Account email.
* `--update-env-vars TEXT`: Comma-separated `KEY=VALUE` environment variables.

---

## 2. Google Cloud SDK (`gcloud`) & Vertex AI Python SDK

### Print Auth Token for API / Load Tests
```bash
_AUTH_TOKEN=$(gcloud auth print-access-token -q)
```

### Vertex AI Reasoning Engine Inspection (Python SDK)
> [!NOTE]
> `gcloud ai` CLI does not contain a `reasoning-engines` subcommand. Query and verify live Reasoning Engines using the `vertexai.agent_engines` Python SDK.

```python
import vertexai
from vertexai.agent_engines import AgentEngine

vertexai.init(project="zcloud-cicd", location="asia-southeast1")

# List all deployed Reasoning Engines
engines = AgentEngine.list()
for e in engines:
    raw = getattr(e, "_gca_resource", None)
    display_name = getattr(e, "display_name", "")
    resource_name = getattr(e, "resource_name", "")
    min_inst = getattr(raw.spec.deployment_spec, "min_instances", 0) if raw and raw.spec else 0
    print(f"{display_name} ({resource_name}): min_instances = {min_inst}")
```

### Model Location Constraint
> [!WARNING]
> Gemini models (such as `gemini-1.5-flash` or `gemini-flash-latest`) require Vertex AI initialization with `location="global"` or environment variable `GOOGLE_CLOUD_LOCATION="global"`, even when the Agent Engine runtime is located in `asia-southeast1`.

---

## 3. GitHub CLI (`gh`) for CI/CD Pipeline Management

### Triggering CI/CD Workflows
```bash
# Trigger Staging Deployment Pipeline
gh workflow run staging.yaml

# Trigger Production Release Pipeline with Version Input
gh workflow run deploy-to-prod.yaml -f version_tag=v1.0.0
```

### Monitoring Workflow Execution
```bash
# List recent workflow runs
gh run list --limit 5

# View run details & job status
gh run view <RUN_ID>

# Watch live workflow progress until completion
gh run watch <RUN_ID>
```

---

## 4. Terraform Infrastructure as Code (IaC)

### Local Format, Validation & Apply
```bash
cd deployment/terraform/cicd
terraform init
terraform fmt -check
terraform validate
terraform plan
terraform apply -auto-approve
```

### Single-Project Setup Quirk
When `staging_project_id` and `prod_project_id` target the same GCP project (e.g., `zcloud-cicd`), ensure:
1. `locals.tf` deduplicates projects using `toset([var.staging_project_id, var.prod_project_id])` for `local.deploy_project_ids` to avoid duplicate Service Account and BigQuery dataset creation errors.
2. `github.tf` secret mapping uses `lookup(google_service_account.app_sa, "prod", google_service_account.app_sa["staging"]).email`.

---

## 5. Local Environment, Formatting & Load Testing (`uv` / `pytest` / `locust`)

### Code Formatting & Testing
```bash
# Code formatting check
uv run black --check app/ tests/

# Unit tests
uv run pytest tests/ -v

# Acceptance Load Testing with Locust
uvx locust==2.32.4 \
  -f tests/load_test/load_test.py \
  --headless \
  -t 30s -u 2 -r 0.5 \
  --csv=tests/load_test/.results/results \
  --html=tests/load_test/.results/report.html
```

---

## 6. GitHub Actions Workflow Configuration Policy

### Upgrade Actions to Supported Versions (Do NOT use `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`)
> [!IMPORTANT]
> **Action Version Upgrades over Force Flags**: Do **NOT** set `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"`. Setting `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` causes the GitHub Actions runner to emit deprecation warning annotations on every step because the actions' metadata still targets older runtimes.
>
> Always upgrade GitHub Actions to their latest supported major versions:
> * `google-github-actions/auth@v3` (v3 natively supports modern GitHub Actions runner runtimes)
> * `google-github-actions/setup-gcloud@v3`
> * `actions/setup-python@v5`
> * `astral-sh/setup-uv@v5`
> * `actions/checkout@v4`
