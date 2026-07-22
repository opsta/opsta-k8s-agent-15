# AGENTS.md

This document defines your development constraints, environment expectations,
execution modes, security policies, and CI/CD rules for developing and
deploying LLM agents to the **Gemini Enterprise Agent Platform** using
`agents-cli`.

You must strictly align with and follow these specifications at all times.

---

## 1. Project Metadata & Variables

Before starting any development work, you must ensure the following variables
and configuration details are defined. If any required details are missing, you
must proactively ask the user to clarify them before writing or modifying code:

* **Agent Name** (which will also serve as your Application Name)
* **Working Directory** on the local developer machine
* **Repository URL** (e.g., `https://github.com/opsta/my-agent-repo` with SSH
  key configured and ready for push/pull)
* **Programming Language & Framework/Library Versions** (e.g., Python 3.12,
  FastAPI 0.110.0)
* **LLM Model Configuration**: Model name, version, and GCP region (e.g.,
  `gemini-1.5-pro` in `us-central1`)
* **GCP Region for Deployment** (e.g., `asia-southeast1`)
* **GCP Projects**: Dedicated projects for Staging and Production
* **Deployment Target & Services**: Agent Runtime target details (e.g., using
  `-stg` and `-prd` suffixes for Cloud Run/Agent Runtime services)
* **Terraform State Storage**: GCS Bucket Name for managing state
* **External Integration & Webhook Credentials** (e.g., Telegram Bot Token,
  ClickUp APIs, Slack, Jira, etc.)

---

## 2. Agent Skills & Capabilities

* Always consult [CLI_COMMANDS_GUIDE.md](file:///Users/winggundamth/git/opsta-k8s-agent-15/CLI_COMMANDS_GUIDE.md) for the exact, pre-verified commands, flags, parameters, and IAM policies (`agents-cli`, `gcloud`, `gh`, `terraform`, `uv`, `vertexai` SDK) required for this repository before running CLI commands.
* Always utilize your standard `agents-cli` toolset and commands for all
  initialization, packaging, local execution, and deployment tasks.
* Always pass `--min-instances 0` explicitly when deploying with `agents-cli deploy` to comply with cost-scaling guidelines.
* Consult local CLI help instructions if library syntax or parameters require
  clarification.

---

## 3. End-to-End Local Test Plan

* **Local-First Execution**: Run and verify all middleware, webhooks, and your
  core agent services locally first before syncing with remote repositories or
  cloud environments.
* **Database and Middleware Emulation**: Set up and run databases or storage
  engines locally (e.g., via Docker or emulators) for validation. You may
  access proprietary cloud databases (such as GCP Firestore) directly if local
  emulators are unavailable.
* **Direct Cloud LLM Connectivity**: You are authorized to connect directly
  to the target cloud LLM model and region during local runtime test executions.
* **No Early Commits**: Do not commit, push, or run deployments until all local
  functionality is validated via end-to-end tests.
* **Realistic Webhook/Event Simulation**: Validate webhook integrations by
  mocking realistic payload events from source platforms (e.g., GitHub, GitLab,
  Telegram, external monitoring systems).

### Real-World E2E Test Definition

When the instruction **"do real world e2e test"** is given, execute a true
integration flow rather than mocking triggers with `curl` or shell commands:

1. Manually or programmatically trigger a real event from the source platform
   (e.g., create a failing pipeline, send a test bot command, post a message, or
   trigger a webhook source).
2. Inspect runtime and webhook logs to verify that you receive and process the
   payload correctly.
3. Verify the downstream effects in respective environments (e.g., creation of
   Pull Requests, updates to task tracking systems, or notifications to chat
   interfaces).
4. If errors occur, resolve them locally first, commit and push the fix, and
   redeploy to staging before executing the real-world test again.

---

## 4. Developer Rules & Constraints

* **Branch Protection & Feature Branch Workflow**:
  * Treat the `main` (or default) branch as protected.
  * For any new feature or fix, branch from `main` using prefix conventions
    (e.g., `feat/`, `fix/`, `chore/`).
  * Clean up remote and local feature branches once they are successfully merged
    or no longer needed.
* **Authenticated CLIs**:
  * Utilize pre-authenticated CLIs present on the host environment without
    querying the user for credentials:
    * `gh` for GitHub operations.
    * `glab` for GitLab operations.
    * `gcloud` for Google Cloud platform resources.
* **Enforce Formatting & Linting**:
  * Always run formatters and linters (e.g., `terraform fmt` for Terraform,
    `black` or `ruff` for Python, `prettier` for JS) before committing code.
* **Evaluations (Evals)**:
  * Always run routing and tool-calling evaluations after code modifications to
    verify your reasoning accuracy.
* **Graceful Error Handling**:
  * Gracefully catch API rate limits, timeouts, or downtime from external
    platforms (e.g., Telegram, Jira, Google Workspace).
  * Return user-friendly, descriptive messages to clients/logs and fail
    gracefully instead of crashing the process.
* **Long-Term System Refinement**:
  * Avoid temporary workarounds for recurring errors. Propose and apply long-
    term automated fixes (e.g., modifying database schema indexes or upgrading
    libraries) after explaining the approach to the user.

---

## 5. Infrastructure Rules & Constraints (Terraform & GCP)

* **Infrastructure as Code (IaC)**:
  * Manage all GCP resources (service accounts, GCS buckets, runtimes, pub/sub
    topics) strictly using Terraform.
* **Strict Dependency Pinning**:
  * Pin exact versions for all project dependencies, Python packages
    (`requirements.txt`), Terraform providers, and libraries to ensure
    reproducible builds.
* **Core Tooling Upgrades**:
  * Use the latest stable major/minor versions for core developer tooling (e.g.,
    Terraform, `google-adk`, Action workflows) when they are not explicitly
    pinned.
  * If library or runtime mismatch issues occur, resolve them locally, deploy
    through pipelines, or recreate runtime resources as a last resort.
* **Local Package Installation**:
  * Prefer Homebrew (`brew`) for installing dependencies or CLI tools on the
    local machine. Use native package managers or SDKs (`gcloud`, `apt`, `npm`)
    only if the tool is not available in Homebrew.
* **Resource & Cost Optimization**:
  * Configure staging and production Agent Runtime targets to scale down to zero
    when idle (`min instance = 0`).

---

## 6. CI/CD Rules & Constraints

* **Automated Workflows**:
  * Implement robust pipelines (e.g., GitHub Actions, GitLab CI/CD) containing
    discrete steps for compilation, formatting, security scanning, deployment,
    and acceptance testing.
* **Warning-Free Pipelines**:
  * Monitor and proactively resolve deprecation warnings in CI/CD pipelines
    (e.g., action versions, runtime engines, node deprecations).
* **Tooling & Runtime Constraints**:
  * Ensure all actions and runner environments align with modern, supported
    platform runtimes (e.g., Node 20+ for GitHub workflows).
* **Pipeline Trigger Scopes & Loop Prevention**:
  * Configure CI/CD triggers carefully. Avoid automated runs on branches or PRs
    you created to prevent endless loop execution. Restrict automatic
    deployment triggers on push to target branches (e.g., `main`).
* **Environment Promotions**:
  * **Staging**: Deployments should automate on code pushes or merges to the
    default branch.
  * **Production**: Deployments must require a manual run or manual tag event
    (e.g., `workflow_dispatch`) that accepts a semantic tag input (e.g.,
    `v1.0.0`).
* **Conventional Commits**:
  * Write commit messages according to the Conventional Commits specification
    (e.g., `feat: add model integration`, `fix: check rate limits`).
* **Build Optimization & Caching**:
  * Implement caching strategies (e.g., package manager caches, vulnerability
    databases, docker layer caching) to keep build and test step durations under
    30 seconds.
* **Self-Hosted Runner Configurations**:
  * Configure runners safely using isolated Docker executors or virtual
    machines. Always submit a plan and obtain confirmation before modifying
    runner settings.

---

## 7. Security & Compliance

* **Zero Credential Hardcoding**:
  * Never store API keys, tokens, GCP credentials, or service account files in
    git repositories or Terraform configurations. Use Google Cloud Secret
    Manager, environment variables, or secure CI/CD secrets.
* **Incoming Request Verification**:
  * Authenticate and validate incoming webhook headers and payloads (e.g., via
    secret tokens or cryptographic signatures) to confirm they originate from
    trusted sources.
* **Static & Dependency Analysis**:
  * Run Static Application Security Testing (SAST) (e.g., `bandit` for Python)
    and Software Composition Analysis (SCA) (e.g., `trivy` for
    dependency/container/IaC scans) locally.
  * Block staging CI/CD builds if any vulnerability classified as `CRITICAL` or
    `HIGH` is detected.
* **Prompt Injection Protection**:
  * Apply system prompt hardening techniques to ensure that you do not leak your
    system prompts, API keys, database structures, or internal parameters to
    end-users.
* **Principle of Least Privilege**:
  * Ensure Terraform configurations declare dedicated service accounts for your
    staging and production runtime environments with minimal IAM permissions.

---

## 8. Execution Mode & Autonomy

* **Local-First Promotion**:
  * Build, run, and exhaustively test features locally. Once all local checks,
    security scans, and evaluations pass, automatically proceed to provisioning
    cloud infrastructure and running deployments without pausing for user
    confirmation.
* **Autonomous Steps**:
  * You have full authorization to execute successive CLI commands (git,
    terraform, gcloud, gh, glab) to fulfill tasks without waiting for prompt-by-
    prompt user approval.
* **Self-Correction**:
  * In the event of execution failures (compilation errors, deployment errors,
    Terraform blocks), read the logs, adjust the code, and rerun the step
    autonomously.
* **Progressive Checklists**:
  * Maintain a clear progress checklist (e.g., `task.md`), updating the status
    of tasks as you address them.
* **Continuous Synchronization**:
  * Commit and push progress to the repository after completing major logical
    milestones to keep your state synchronized.
* **Automated Production Tagging**:
  * Upon successful staging deployment and validation, push the semantic version
    tag (e.g., `v1.0.0`) and trigger the production workflow autonomously.
* **Definition of Done**:
  * A task is considered done only when local execution, tests, evaluations, and
    CI/CD pipelines run cleanly, culminating in successful staging and
    production deployments.
