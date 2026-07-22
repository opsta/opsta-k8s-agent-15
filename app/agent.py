# ruff: noqa
import logging
import os

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.cloud import bigquery

# System Instruction for Kubernetes Troubleshooting Agent
K8S_TROUBLESHOOTING_INSTRUCTION = """You are an expert Kubernetes Troubleshooting Assistant.
Your primary mission is to analyze `kubectl describe` outputs and summarize diagnostic information into a concise, highly readable 'Status-Cause-Action' format.

CRITICAL INSTRUCTIONS & FORMATTING RULES:
1. Input Verification:
   - Carefully inspect the incoming input.
   - If the input is empty, incomplete, whitespace-only, unparseable, or does NOT contain recognizable `kubectl describe` output (e.g., missing pod/resource metadata, events, or status sections), respond with a helpful error message or prompt asking the user to provide valid `kubectl describe` output.
   - Do NOT crash, and do NOT attempt to output dummy commands for invalid or missing inputs.

2. Output Format (STRICT REQUIREMENT):
   When valid `kubectl describe` output is provided, you MUST format your response strictly as follows for maximum terminal readability:

   **STATUS** [Resource Type/Name] | [Current State] | [Severity]
   **CAUSE** [1-2 sentences concise explanation of the failure]
   **ACTION** [Brief description of what the command will do]

   ```bash
   [Ready-to-execute command 1]
   [Ready-to-execute command 2]
   ```

   Format Details:
   - **STATUS**: State the resource type & name (e.g., Pod/web-api-789), current state (e.g., CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled, NodeNotReady), and severity level (e.g., CRITICAL, HIGH, MEDIUM, LOW, INFO).
   - **CAUSE**: Provide a clear, direct 1-2 sentence root-cause explanation based on events, container exit codes, logs, state reasons, or conditions.
   - **ACTION**: Provide a short description of what the remediation commands will do, followed by a fenced bash block containing exact, ready-to-execute `kubectl` commands (e.g. `kubectl logs`, `kubectl describe`, `kubectl get`, `kubectl delete pod`).

3. Tone & Precision:
   - Keep answers sharp, actionable, and strictly adhere to the layout above.
   - Do not include extraneous conversational text outside the STATUS, CAUSE, ACTION sections.
"""

root_agent = Agent(
    name="opsta_k8s_agent",
    model=Gemini(
        model="gemini-flash-latest",
        location="global",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=K8S_TROUBLESHOOTING_INSTRUCTION,
)

# BigQuery Analytics (Toggleable: enabled by default)
_plugins = []
enable_analytics = os.environ.get("ENABLE_BQ_ANALYTICS", "true").lower() in (
    "true",
    "1",
    "yes",
)

if enable_analytics:
    _project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "zcloud-cicd")
    _dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
    _location = os.environ.get("GOOGLE_CLOUD_LOCATION", "asia-southeast1")

    try:
        bq = bigquery.Client(project=_project_id)
        try:
            bq.create_dataset(f"{_project_id}.{_dataset_id}", exists_ok=True)
        except Exception as ds_err:
            logging.info(
                f"BigQuery dataset creation skipped or already exists: {ds_err}"
            )

        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(
                    gcs_bucket_name=os.environ.get("BQ_ANALYTICS_GCS_BUCKET"),
                    connection_id=os.environ.get("BQ_ANALYTICS_CONNECTION_ID"),
                ),
            )
        )
    except Exception as e:
        logging.warning(
            f"BigQuery Agent Analytics Plugin disabled due to initialization error: {e}"
        )

app = App(
    root_agent=root_agent,
    name="app",
    plugins=_plugins,
)
