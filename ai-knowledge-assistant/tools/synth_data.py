"""
Task B: Synthetic Data Generator
Generates mock company knowledge documents across three themes:
  1. Company Overview & Team FAQs
  2. Technical Tutorials & API Snippets
  3. SOPs & Internal Best Practices

Output: data/raw/<filename>.md  +  data/raw/<filename>.meta.json
"""

import os
import json
from datetime import datetime, timedelta
import random

OUTPUT_DIR = os.path.join("data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end   = datetime(end_year, 12, 31)
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def save(filename: str, content: str, meta: dict):
    """Write document + sidecar metadata."""
    doc_path  = os.path.join(OUTPUT_DIR, filename)
    meta_path = os.path.join(OUTPUT_DIR, filename.replace(".md", ".meta.json"))

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"  ✅  {filename}")


# ══════════════════════════════════════════════════════════════════════════════
# THEME 1 — Company Overview & Team FAQs
# ══════════════════════════════════════════════════════════════════════════════

def gen_company_overview():
    content = """\
# Company Overview — Acme Corp

## Who We Are
Acme Corp is a mid-sized technology company specialising in data platforms and developer tooling.
Founded in 2015, we serve enterprise clients across finance, healthcare, and logistics.
Our headquarters are in Austin, TX, with remote teams distributed globally.

## Mission
"Empower teams to ship reliable software faster."

## Core Values
- **Transparency** — We default to open communication.
- **Ownership** — Every engineer owns their code end-to-end.
- **Curiosity** — We invest 10% of sprint time in learning.
- **Reliability** — We treat on-call as a first-class responsibility.

## Key Departments
| Department         | Head              | Slack Channel       |
|--------------------|-------------------|---------------------|
| Platform Eng       | Maria Santos      | #platform-eng       |
| Data Engineering   | James Okafor      | #data-eng           |
| Security & Compliance | Priya Nair     | #security           |
| Developer Experience | Leo Müller      | #devex              |
| People & Culture   | Tamara Liu        | #people             |

## Office Hours & Time Zones
Most synchronous meetings are scheduled 10:00–16:00 CT to accommodate EMEA colleagues.
The Austin office is open Monday–Thursday; Friday is optional in-office.
"""
    meta = {
        "title": "Company Overview — Acme Corp",
        "tags": ["company", "overview", "culture", "onboarding"],
        "type": "faq",
        "date": "2024-01-10"
    }
    save("company_overview.md", content, meta)


def gen_team_faq():
    content = """\
# New Engineer FAQ

## General

**Q: Where do I find the engineering wiki?**
A: Internal docs live in Confluence under the *Engineering* space. Start with the "Onboarding Trail"
   page — it links every resource in order.

**Q: How do I get access to AWS?**
A: Open a ticket in Jira under the `ACCESS` project. Approvals usually complete within one business day.
   Your manager should already have pre-approved standard roles for your team.

**Q: What's our branching strategy?**
A: We use trunk-based development. Feature branches are short-lived (< 2 days).
   Branch names follow: `<team>/<ticket-id>-<short-description>`, e.g. `data/DE-421-add-parquet-sink`.

## Tooling

**Q: Which IDE is recommended?**
A: VS Code is the default with our shared settings repo (`.vscode/settings.json` is committed).
   JetBrains IDEs are also supported; ask #devex for the license server URL.

**Q: How do I run the local dev environment?**
A: Clone the repo, copy `.env.example` → `.env`, then run:
   ```
   make setup   # installs dependencies and pre-commit hooks
   make dev     # starts all services via Docker Compose
   ```

**Q: Where do I report a security vulnerability?**
A: Email security@acmecorp.internal or use the private Slack channel #security-reports.
   Do NOT open a public Jira ticket for security issues.

## Processes

**Q: How are on-call rotations managed?**
A: PagerDuty owns the rotation schedule. Each team rotates weekly; shadow shifts are
   mandatory for the first two on-call cycles.

**Q: What's the incident severity matrix?**
A: SEV-1 = customer-impacting outage, SEV-2 = degraded service, SEV-3 = internal tooling.
   Full runbooks are in Confluence → *Incident Response Playbooks*.

**Q: How do I request a day off?**
A: Log it in Workday and give your manager at least 3 business days' notice for single days,
   2 weeks for extended leave.
"""
    meta = {
        "title": "New Engineer FAQ",
        "tags": ["faq", "onboarding", "tooling", "process", "access"],
        "type": "faq",
        "date": "2024-03-05"
    }
    save("team_faq.md", content, meta)


def gen_org_structure():
    content = """\
# Engineering Org Structure

## Reporting Lines

```
CTO — Aisha Brennan
├── VP Engineering — Carlos Reyes
│   ├── Platform Engineering (8 engineers)
│   │   ├── Infra Squad (Kubernetes, Terraform, CI/CD)
│   │   └── Observability Squad (Grafana, OpenTelemetry)
│   ├── Data Engineering (6 engineers)
│   │   ├── Ingestion Squad (Kafka, Airflow)
│   │   └── Analytics Squad (dbt, Spark)
│   └── Developer Experience (3 engineers)
│       └── Tooling & Docs
└── VP Product Engineering — Sophie Park
    ├── Core API Team (10 engineers)
    └── Frontend Team (5 engineers)
```

## Escalation Paths
- **Technical blockers** → Team lead → Engineering Manager
- **Cross-team dependencies** → Raise in #engineering-sync (Monday standup)
- **Urgent production issues** → Page via PagerDuty → Incident Commander
- **HR / People issues** → Direct to #people or confidential HR alias

## Weekly Rhythms
| Day       | Event                                  |
|-----------|----------------------------------------|
| Monday    | Engineering All-Hands (async update)   |
| Tuesday   | Sprint planning (per team)             |
| Wednesday | Architecture review (bi-weekly)        |
| Thursday  | 1:1s with managers                     |
| Friday    | Demo day + retro (end of sprint)       |
"""
    meta = {
        "title": "Engineering Org Structure",
        "tags": ["org", "structure", "reporting", "teams", "onboarding"],
        "type": "faq",
        "date": "2024-02-20"
    }
    save("org_structure.md", content, meta)


# ══════════════════════════════════════════════════════════════════════════════
# THEME 2 — Technical Tutorials & API Snippets
# ══════════════════════════════════════════════════════════════════════════════

def gen_api_tutorial():
    content = """\
# Internal Data API — Getting Started

## Overview
The Acme Data API (`data-api`) is a FastAPI service that exposes processed datasets
for consumption by downstream teams. Base URL (internal): `http://data-api.internal:8080`

## Authentication
All requests require a Bearer token. Obtain yours from the secrets vault:

```bash
# Retrieve token (requires Vault CLI configured)
export DATA_API_TOKEN=$(vault kv get -field=token secret/data-api/tokens/your-team)
```

Pass it as an HTTP header:
```
Authorization: Bearer <token>
```

## Key Endpoints

### GET /datasets
Returns a paginated list of available datasets.

```bash
curl -s http://data-api.internal:8080/datasets \\
  -H "Authorization: Bearer $DATA_API_TOKEN" | jq .
```

**Response:**
```json
{
  "items": [
    {"id": "sales_v2", "name": "Sales Transactions v2", "rows": 4200000, "updated": "2024-11-01"},
    {"id": "users_core", "name": "Core User Profiles", "rows": 850000, "updated": "2024-10-28"}
  ],
  "page": 1,
  "total_pages": 3
}
```

### GET /datasets/{id}/sample
Returns up to 100 rows as JSON for quick inspection.

```python
import httpx, os

token = os.environ["DATA_API_TOKEN"]
r = httpx.get(
    "http://data-api.internal:8080/datasets/sales_v2/sample",
    headers={"Authorization": f"Bearer {token}"},
    params={"limit": 20}
)
r.raise_for_status()
print(r.json())
```

### POST /datasets/{id}/export
Triggers an async export job. Returns a `job_id` you can poll.

```python
payload = {"format": "parquet", "destination": "s3://acme-exports/my-team/"}
r = httpx.post(
    "http://data-api.internal:8080/datasets/sales_v2/export",
    headers={"Authorization": f"Bearer {token}"},
    json=payload
)
job_id = r.json()["job_id"]
print(f"Export started: {job_id}")
```

## Error Codes
| Code | Meaning                              |
|------|--------------------------------------|
| 401  | Missing or invalid token             |
| 403  | Token lacks permission for resource  |
| 404  | Dataset not found                    |
| 429  | Rate limit exceeded (100 req/min)    |
| 500  | Internal server error — page #data-eng |

## Rate Limits
Default: 100 requests/minute per token. Bulk export jobs count as 10 requests each.
Contact #data-eng if you need a higher limit for batch workloads.
"""
    meta = {
        "title": "Internal Data API — Getting Started",
        "tags": ["api", "data", "tutorial", "authentication", "fastapi"],
        "type": "tutorial",
        "date": "2024-11-15"
    }
    save("data_api_tutorial.md", content, meta)


def gen_kafka_guide():
    content = """\
# Kafka Quickstart for Engineers

## What We Use Kafka For
- Real-time event streaming between microservices
- CDC (Change Data Capture) feeds from Postgres
- Audit log delivery to the data warehouse

## Our Cluster
Cluster alias: `acme-kafka` (Confluent-managed, on AWS MSK for prod)
Local dev uses `docker-compose` with a single-broker Kafka 3.6 image.

## Topic Naming Convention
```
<domain>.<entity>.<event_type>
```
Examples:
- `payments.transaction.created`
- `auth.session.expired`
- `inventory.product.updated`

## Producing a Message (Python)

```python
from confluent_kafka import Producer
import json, os

conf = {
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP"],
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "PLAIN",
    "sasl.username": os.environ["KAFKA_API_KEY"],
    "sasl.password": os.environ["KAFKA_API_SECRET"],
}

producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}]")

event = {"user_id": "u_8821", "action": "purchase", "amount": 49.99}
producer.produce(
    topic="payments.transaction.created",
    key="u_8821",
    value=json.dumps(event).encode("utf-8"),
    callback=delivery_report,
)
producer.flush()
```

## Consuming Messages (Python)

```python
from confluent_kafka import Consumer

conf = {
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP"],
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "PLAIN",
    "sasl.username": os.environ["KAFKA_API_KEY"],
    "sasl.password": os.environ["KAFKA_API_SECRET"],
    "group.id": "my-team-consumer-group",
    "auto.offset.reset": "earliest",
}

consumer = Consumer(conf)
consumer.subscribe(["payments.transaction.created"])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        print(f"Received: {msg.value().decode('utf-8')}")
finally:
    consumer.close()
```

## Dead Letter Queue Policy
Failed messages (after 3 retries) are routed to `<original-topic>.dlq`.
Monitor DLQ depth in Grafana → *Kafka DLQ Overview* dashboard.

## Local Dev Tips
```bash
# Start Kafka locally
docker compose up kafka zookeeper -d

# Create a test topic
docker exec -it kafka kafka-topics.sh \\
  --create --topic test.events --partitions 3 \\
  --bootstrap-server localhost:9092

# Consume from CLI
docker exec -it kafka kafka-console-consumer.sh \\
  --topic test.events --from-beginning \\
  --bootstrap-server localhost:9092
```
"""
    meta = {
        "title": "Kafka Quickstart for Engineers",
        "tags": ["kafka", "streaming", "events", "tutorial", "python"],
        "type": "tutorial",
        "date": "2024-09-03"
    }
    save("kafka_quickstart.md", content, meta)


def gen_ci_cd_guide():
    content = """\
# CI/CD Pipeline Guide

## Overview
We use GitHub Actions for all CI/CD. Pipelines live in `.github/workflows/`.
Every repository ships with three standard workflows:

| Workflow File       | Trigger                | Purpose                           |
|---------------------|------------------------|-----------------------------------|
| `ci.yml`            | PR opened / push       | Lint, test, build                 |
| `deploy-staging.yml`| Merge to `main`        | Deploy to staging environment     |
| `deploy-prod.yml`   | Manual dispatch / tag  | Deploy to production              |

## Standard CI Workflow (ci.yml)

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Lint
        run: ruff check .

      - name: Type check
        run: mypy src/

      - name: Run tests
        run: pytest tests/ -v --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

## Environment Secrets
Secrets are stored in GitHub → Settings → Secrets and never hard-coded.

| Secret Name          | Used By              |
|----------------------|----------------------|
| `AWS_ACCESS_KEY_ID`  | Deploy workflows     |
| `AWS_SECRET_ACCESS_KEY` | Deploy workflows  |
| `SLACK_WEBHOOK`      | Notification step    |
| `PYPI_TOKEN`         | Library publish jobs |

## Deployment Strategy
- **Staging** — auto-deployed on every merge to `main`, uses blue/green swap on ECS.
- **Production** — requires a semver git tag (`v1.2.3`) OR a manual workflow dispatch
  with `environment: production` approval from two senior engineers.

## Rollback Procedure
```bash
# Find the last stable image tag
aws ecr describe-images --repository-name acme/my-service \\
  --query 'sort_by(imageDetails,&imagePushedAt)[-2].imageTags[0]' \\
  --output text

# Force a new deployment with that tag
aws ecs update-service \\
  --cluster acme-prod \\
  --service my-service \\
  --force-new-deployment
```

Automated rollback fires if error rate > 5% for 3 consecutive minutes (CloudWatch alarm).
"""
    meta = {
        "title": "CI/CD Pipeline Guide",
        "tags": ["ci", "cd", "github-actions", "deployment", "devops"],
        "type": "tutorial",
        "date": "2024-07-22"
    }
    save("cicd_guide.md", content, meta)


# ══════════════════════════════════════════════════════════════════════════════
# THEME 3 — SOPs & Internal Best Practices
# ══════════════════════════════════════════════════════════════════════════════

def gen_incident_sop():
    content = """\
# SOP — Incident Response

**Document ID:** SOP-OPS-001  
**Owner:** Platform Engineering  
**Review Cycle:** Quarterly  
**Last Reviewed:** 2024-10-01  

---

## 1. Purpose
Define the standard process for detecting, responding to, and learning from production incidents.

## 2. Scope
Applies to all production services owned by Engineering. Does not cover pre-production environments.

## 3. Severity Definitions

| Severity | Customer Impact             | Response Time | Example                         |
|----------|-----------------------------|---------------|---------------------------------|
| SEV-1    | Complete outage             | Immediate     | API returning 500 for all users |
| SEV-2    | Partial or degraded service | < 15 min      | Checkout flow failing for 20%   |
| SEV-3    | Non-critical degradation    | < 2 hours     | Slow dashboard queries          |
| SEV-4    | Cosmetic / monitoring alert | Next business day | Minor UI glitch              |

## 4. Response Steps

### Step 1 — Acknowledge
- Page is acknowledged in PagerDuty within **5 minutes** for SEV-1/2.
- Responder posts in `#incidents`: `🚨 Investigating [SEV-X]: <brief description>`

### Step 2 — Assess
- Determine scope: which services, how many users, revenue impact estimate.
- Assign an **Incident Commander** (IC) — usually the on-call engineer.
- If SEV-1: notify Engineering Manager and VP Engineering immediately.

### Step 3 — Communicate
- Post status updates every **10 minutes** in `#incidents` during active SEV-1/2.
- Update the external status page (Statuspage.io) within 15 minutes of SEV-1 declaration.

### Step 4 — Mitigate
- Prefer **rollback over fix-forward** for production incidents.
- Runbooks are linked from PagerDuty alerts and Confluence → *Incident Runbooks*.

### Step 5 — Resolve
- Mark incident resolved in PagerDuty.
- Post resolution summary in `#incidents`.
- Update status page to "Resolved".

### Step 6 — Post-Incident Review (PIR)
- Required for all SEV-1 and SEV-2 incidents.
- PIR must be drafted within **48 hours** using the PIR template in Confluence.
- PIR meeting scheduled within **5 business days**.
- Action items tracked in Jira under `PIR-<date>`.

## 5. Escalation Matrix
| Situation                        | Escalate To                  |
|----------------------------------|------------------------------|
| Unable to mitigate within 30 min | Engineering Manager          |
| Customer data at risk            | Security + Legal immediately |
| Media / PR risk                  | VP Engineering + Comms       |

## 6. Communication Templates

**Initial alert (Slack):**
```
🚨 [SEV-1 INCIDENT] Payment service returning 503
IC: @james.okafor | Bridge: Zoom link in #incidents
Started: 14:32 UTC | Affected: All checkout flows
```

**Resolution message (Slack):**
```
✅ [RESOLVED] Payment service incident (SEV-1)
Duration: 47 minutes | Root cause: DB connection pool exhaustion
Fix: Increased pool size + restarted service | PIR: within 48h
```
"""
    meta = {
        "title": "SOP — Incident Response",
        "tags": ["sop", "incident", "on-call", "production", "pagerduty"],
        "type": "sop",
        "date": "2024-10-01"
    }
    save("sop_incident_response.md", content, meta)


def gen_code_review_sop():
    content = """\
# SOP — Code Review Standards

**Document ID:** SOP-ENG-003  
**Owner:** Developer Experience  
**Last Reviewed:** 2024-08-15  

---

## 1. Purpose
Establish consistent, respectful, and effective code review practices across all engineering teams.

## 2. Author Responsibilities

### Before Opening a PR
- [ ] Self-review your diff — catch obvious issues first.
- [ ] Tests pass locally (`make test`).
- [ ] No secrets or PII in the diff.
- [ ] PR description filled out using the PR template.
- [ ] PR is < 400 lines changed (excluding generated/lock files). Larger PRs must be split.

### PR Description Must Include
1. **What** — what does this change do?
2. **Why** — what problem does it solve? Link the Jira ticket.
3. **How to test** — steps a reviewer can follow to verify.
4. **Screenshots** — required for any UI change.

## 3. Reviewer Responsibilities

### SLA
| PR Size       | First review SLA |
|---------------|-----------------|
| < 100 lines   | Same business day |
| 100–400 lines | 1 business day    |
| > 400 lines   | Must be split     |

### Review Checklist
- [ ] Logic is correct and edge cases handled.
- [ ] Tests cover the new behaviour.
- [ ] No security vulnerabilities introduced.
- [ ] Code is readable without needing the author to explain it.
- [ ] Error handling is explicit (no silent failures).

### Comment Conventions
Use prefixes to signal intent:

| Prefix       | Meaning                                      |
|--------------|----------------------------------------------|
| `nit:`       | Minor style preference — author's call       |
| `question:`  | Seeking understanding, not requesting change |
| `suggest:`   | Idea for consideration, non-blocking         |
| `MUST:`      | Blocking — must be resolved before merge     |
| `DISCUSS:`   | Needs team discussion before proceeding      |

Example:
```
nit: variable name `d` could be `delta` for clarity.
MUST: This will fail if `user` is None — add a null check.
```

## 4. Merge Rules
- Minimum **1 approval** for standard PRs; **2 approvals** for infra/security changes.
- All CI checks must be green.
- No unresolved `MUST:` comments.
- Author merges their own PR (not reviewers).
- Use **Squash and Merge** to keep history clean.

## 5. What NOT to Review
- Auto-generated files (migrations, protobuf outputs, lock files).
- Whitespace-only changes.
- Mark these sections with `<!-- generated -->` in the PR description.

## 6. Handling Disagreements
1. Author and reviewer discuss in PR comments (time-boxed to 1 day).
2. If unresolved, escalate to team lead for a decision.
3. Decision is documented in the PR thread.
4. No PR should be blocked more than 2 business days on a disagreement.
"""
    meta = {
        "title": "SOP — Code Review Standards",
        "tags": ["sop", "code-review", "pull-request", "standards", "engineering"],
        "type": "sop",
        "date": "2024-08-15"
    }
    save("sop_code_review.md", content, meta)


def gen_data_handling_sop():
    content = """\
# SOP — Data Handling & Classification

**Document ID:** SOP-SEC-007  
**Owner:** Security & Compliance  
**Last Reviewed:** 2024-09-30  

---

## 1. Data Classification Tiers

| Tier | Label        | Examples                                       | Storage Rules                         |
|------|--------------|------------------------------------------------|---------------------------------------|
| T1   | Public       | Marketing copy, open-source code               | No restrictions                       |
| T2   | Internal     | Internal docs, aggregate metrics               | Company systems only                  |
| T3   | Confidential | Customer PII, financial data, credentials      | Encrypted at rest + in transit        |
| T4   | Restricted   | Health records, auth tokens, private keys      | Need-to-know + audit logging required |

## 2. PII Definition (Acme Standard)
The following are classified as PII and must be treated as T3 minimum:
- Full name + any contact identifier (email, phone, address)
- Government ID numbers
- Payment card data
- IP addresses combined with user identifiers
- Biometric data

## 3. Handling Rules by Tier

### T3 — Confidential
- Must be encrypted at rest (AES-256) and in transit (TLS 1.2+).
- Cannot be stored in code repositories, Slack messages, or Jira tickets.
- Access requires approval from the data owner.
- Retention: maximum 2 years unless legally required.

### T4 — Restricted
- All access must be logged with user ID, timestamp, and purpose.
- No export to personal devices.
- Must be reviewed by Security team before any third-party sharing.
- Retention: minimum 7 years for financial; 5 years for health data.

## 4. Developer Checklist — New Data Pipeline

Before deploying a pipeline that processes T3/T4 data:
- [ ] Data classification documented in the design doc.
- [ ] Encryption verified end-to-end.
- [ ] PII fields masked or tokenised in non-production environments.
- [ ] Retention policy configured.
- [ ] Access controls reviewed by Security.
- [ ] PIR process referenced if data breach occurs.

## 5. Breach Response
If you suspect a data breach:
1. **Do not attempt to fix it alone** — notify Security immediately.
2. Email: `security-incidents@acmecorp.internal` (24/7 monitored).
3. Do not delete logs — they are required for forensics.
4. Legal notification requirements: T3/T4 breaches may trigger regulatory notification
   within 72 hours (GDPR, CCPA). Security will assess.

## 6. Approved Data Storage Locations
| Environment | Approved Stores                         |
|-------------|----------------------------------------|
| Production  | AWS RDS (encrypted), S3 (SSE-KMS)      |
| Staging     | AWS RDS, S3 — PII must be anonymised   |
| Local dev   | Synthetic data only — never real PII   |
"""
    meta = {
        "title": "SOP — Data Handling & Classification",
        "tags": ["sop", "security", "data", "compliance", "pii", "gdpr"],
        "type": "sop",
        "date": "2024-09-30"
    }
    save("sop_data_handling.md", content, meta)


def gen_deployment_best_practices():
    content = """\
# Best Practices — Production Deployments

## 1. Pre-Deployment Checklist

### Code Readiness
- [ ] All tests pass (unit, integration, smoke).
- [ ] Code reviewed and approved per SOP-ENG-003.
- [ ] No outstanding SEV-1/2 incidents in progress.
- [ ] Changelog entry written.

### Infrastructure Readiness
- [ ] Terraform plan reviewed — no unexpected resource destruction.
- [ ] Database migrations tested on staging with production-scale data snapshot.
- [ ] Feature flags configured for gradual rollout if applicable.
- [ ] Rollback procedure documented and rehearsed.

## 2. Deployment Windows
| Environment | Allowed Window              | Notes                             |
|-------------|----------------------------|-----------------------------------|
| Staging     | Anytime                    | Automated on every merge to main  |
| Production  | Tue–Thu, 10:00–15:00 CT    | Avoid Mondays, Fridays, holidays  |
| Hotfix      | Anytime with IC approval   | Must have on-call engineer ready  |

## 3. Gradual Rollout Strategy
For significant changes, use feature flags to roll out incrementally:

```
0% → 1% → 5% → 25% → 50% → 100%
```

Monitor key metrics at each stage for at least 10 minutes before advancing:
- Error rate (target: < 0.1% increase)
- P99 latency (target: < 10% increase)
- Business metrics (conversion rate, API success rate)

## 4. Database Migration Rules
- **Never** run destructive migrations (DROP, column removal) without a multi-step process:
  1. Deploy code that works with both old and new schema.
  2. Run migration.
  3. Deploy code that removes old schema compatibility.
  4. Schedule cleanup migration separately.
- Always test migrations against a snapshot of production data in staging first.
- Large table migrations (> 10M rows) must use online migration tools (`pt-online-schema-change` or `pg_repack`).

## 5. Monitoring After Deployment
Set a **deployment watch period** based on traffic:
- Low traffic services: 30 minutes
- Medium traffic: 1 hour
- High traffic / critical path: 2 hours

Watch these dashboards (Grafana → *Post-Deploy Overview*):
- HTTP error rates by endpoint
- Database query latency
- Queue depth (if applicable)
- External dependency health

## 6. When to Rollback (vs. Fix-Forward)
Prefer rollback when:
- Error rate > 1% sustained for > 2 minutes
- Data corruption is suspected
- The fix-forward timeline exceeds 20 minutes

Prefer fix-forward when:
- Issue only affects < 0.1% of traffic
- A one-line config change resolves it
- Rollback would cause a worse data migration issue
"""
    meta = {
        "title": "Best Practices — Production Deployments",
        "tags": ["deployment", "best-practices", "production", "rollout", "devops"],
        "type": "sop",
        "date": "2024-06-18"
    }
    save("deployment_best_practices.md", content, meta)


# ══════════════════════════════════════════════════════════════════════════════
# RUNNER
# ══════════════════════════════════════════════════════════════════════════════

GENERATORS = [
    # Theme 1 — Company FAQs
    gen_company_overview,
    gen_team_faq,
    gen_org_structure,
    # Theme 2 — Technical Tutorials
    gen_api_tutorial,
    gen_kafka_guide,
    gen_ci_cd_guide,
    # Theme 3 — SOPs & Best Practices
    gen_incident_sop,
    gen_code_review_sop,
    gen_data_handling_sop,
    gen_deployment_best_practices,
]


def main():
    print(f"\n📝  Generating {len(GENERATORS)} synthetic documents → {OUTPUT_DIR}/\n")
    for gen in GENERATORS:
        gen()

    # Summary
    docs  = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")]
    metas = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".meta.json")]
    print(f"\n✨  Done — {len(docs)} documents, {len(metas)} metadata files\n")
    print("Files written:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f:<45} {size:>6} bytes")


if __name__ == "__main__":
    main()
