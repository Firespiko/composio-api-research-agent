# Composio API Research Agent

An automated research pipeline for analyzing API integration readiness across 100 applications.

The system researches authentication methods, credential accessibility, API protocols, SDK availability, MCP support, API breadth, buildability, blockers, and supporting evidence. It uses web retrieval, a local LLM for structured extraction, and an independent verification stage for selected results.

## Case Study

**Live case study:**
`https://<YOUR_GITHUB_USERNAME>.github.io/<YOUR_REPOSITORY>/case-study/`

The case study presents the research methodology, pipeline architecture, findings, verification results, limitations, and integration-readiness patterns.

---

## Problem

Researching 100 APIs manually requires repeatedly:

1. Finding official developer documentation.
2. Identifying authentication mechanisms.
3. Determining how developers obtain credentials.
4. Identifying the available API protocols.
5. Checking SDK availability.
6. Checking MCP support.
7. Assessing API breadth.
8. Determining practical integration blockers.
9. Recording evidence consistently.

The goal of this project was to turn that workflow into a reproducible research pipeline rather than manually researching each application.

---

## Architecture

```text
                    apps.json
                       │
                       ▼
               ┌──────────────┐
               │   Retrieval  │
               │    Tavily    │
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │    Source    │
               │   Ranking    │
               └──────┬───────┘
                      │
                      ▼
               ┌──────────────┐
               │     Gemma    │
               │  Extraction  │
               └──────┬───────┘
                      │
                      ▼
             research_results.json
                      │
                      ▼
               confidence gate
                  /        \
                 /          \
          high confidence   verification
                 │              │
                 │              ▼
                 │       independent search
                 │              │
                 │              ▼
                 │          verifier
                 │              │
                 └──────┬───────┘
                        ▼
               analysis_summary.json
                        │
                        ▼
                  case-study/
```

---

## Research Schema

Each application is normalized into a structured record containing:

* Application name
* Category
* Description
* Authentication methods
* Credential access type
* API types
* SDK availability
* API breadth
* MCP status
* Buildability
* Blocker
* Evidence URLs
* Confidence

This makes heterogeneous developer documentation comparable across applications.

---

## Technology

### Retrieval

**Tavily** is used to retrieve web evidence for each application.

The research stage searches specifically for:

* Official API documentation
* Developer documentation
* Authentication and credentials
* API references

The pipeline prioritizes official documentation where possible.

### Local LLM

A locally hosted Gemma model through LM Studio performs structured extraction.

The model receives retrieved evidence and produces a validated JSON record rather than generating an unrestricted natural-language answer.

### Verification

Selected research records receive an independent verification pass.

The verifier performs a separate search and evaluates fields including:

* Authentication
* Credential access
* API types
* SDK availability
* API breadth
* MCP status
* Buildability
* Blockers

Corrections are stored separately from the original research result.

---

## Results

The current run produced:

| Metric                              | Result |
| ----------------------------------- | -----: |
| Applications                        |    100 |
| Successfully researched             |     98 |
| Research failures                   |      2 |
| Independently verified              |     33 |
| Verified records with field changes |     26 |
| Buildable                           |     64 |
| Buildable with constraints          |     33 |

### Authentication

OAuth2 appeared in 68 of 98 researched applications.

Bearer-token authentication appeared in 60.

API-key authentication appeared in 49.

### API protocols

REST was identified in 95 of 98 applications.

GraphQL appeared in 23.

### MCP

The research identified:

* 39 applications with official MCP support
* 20 with third-party MCP implementations
* 36 with no MCP implementation found
* 3 with unknown status

### Verification

26 of the 33 independently verified applications contained at least one field-level discrepancy.

The most frequently corrected fields were:

| Field             | Corrections |
| ----------------- | ----------: |
| API types         |          13 |
| Credential access |          13 |
| MCP status        |           5 |
| Blocker           |           5 |
| SDK availability  |           3 |

The 33-app verification set is not treated as a statistically random sample, so the observed correction rate is not extrapolated to the full 100-app population.

---

## Example Corrections

### Pipedrive

Initial research:

```text
Access: paid_plan
API: REST + GraphQL
```

Verification:

```text
Access: self_serve
API: REST
```

### Pylon

Initial research:

```text
Access: admin_approval
API: GraphQL + REST
MCP: third_party
```

Verification:

```text
Access: self_serve
API: REST
MCP: official
```

### Stripe

Initial research:

```text
API: REST + GraphQL
```

Verification:

```text
API: REST
```

### Copper

Initial research:

```text
Official SDK: false
```

Verification:

```text
Official SDK: true
```

---

## Checkpointing

The pipeline is designed to survive individual failures.

Research results are persisted incrementally:

```text
results/research_results.json
```

Verification results are persisted separately:

```text
results/verification_results.json
```

If the process stops midway, already-completed applications are skipped on the next run.

This was particularly useful during the 100-application run because external retrieval limits can interrupt long-running research jobs.

---

## Project Structure

```text
composio-api-research-agent/
│
├── case-study/
│   └── index.html
│
├── data/
│   └── apps.json
│
├── prompts/
│   ├── research_prompt.txt
│   └── verification_prompt.txt
│
├── results/
│   ├── research_results.json
│   ├── verification_results.json
│   └── analysis_summary.json
│
├── src/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── main.py
│   ├── researcher.py
│   ├── reporter.py
│   ├── schema.py
│   ├── search.py
│   └── verifier.py
│
├── .env
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Running Locally

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd composio-api-research-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env`:

```env
TAVILY_API_KEY=your_tavily_key
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=google/gemma-4-e4b
```

Never commit `.env`.

### 5. Start the local LLM

Run the configured Gemma model through LM Studio's local server.

The expected endpoint is:

```text
http://localhost:1234/v1
```

### 6. Run the research pipeline

```bash
python -m src.main
```

### 7. Analyze the results

```bash
python -m src.analyzer
```

This generates:

```text
results/analysis_summary.json
```

### 8. Preview the case study

From the project root:

```bash
python -m http.server 8000
```

Then open:

```text
http://localhost:8000/case-study/
```

---

## Design Decisions

### Why retrieval and extraction are separate

Search results are noisy and inconsistent. Separating retrieval from extraction allows the evidence collection strategy to evolve independently from the LLM extraction prompt.

### Why use structured output

A fixed schema makes it possible to aggregate 100 applications and compare fields consistently.

### Why independently verify

The first extraction pass can incorrectly infer API protocols, credential requirements, SDK availability or MCP support from ambiguous documentation.

Independent verification provides a second evidence path and exposes these disagreements.

### Why checkpoint results

A 100-application research run is long-running and dependent on external services. Incremental persistence prevents a single failure from invalidating previous work.

---

## Limitations

### Confidence calibration

The LLM frequently produced high confidence values. The confidence field is therefore used as a triage signal rather than interpreted as a calibrated probability of correctness.

### Verification selection

Only 33 applications were independently verified in the current run. The verification set should not be interpreted as a random statistical sample.

### Documentation volatility

API documentation, authentication requirements, pricing and access policies can change. Evidence URLs should therefore be rechecked before production integration decisions.

### Search dependence

The quality of the extraction stage depends partly on the quality and coverage of retrieved evidence.

---

## Future Improvements

* Integrate Composio directly into the research workflow.
* Add deterministic official-domain validation.
* Improve confidence calibration using verification outcomes.
* Increase verification coverage.
* Track evidence timestamps.
* Add automated evidence freshness checks.
* Compare API capabilities against Composio's available integration/tool coverage.
* Add a database for historical research snapshots.

---

## Summary

This project demonstrates a reproducible approach to API ecosystem research:

```text
100 applications
       ↓
automated retrieval
       ↓
structured extraction
       ↓
confidence-based verification
       ↓
field-level corrections
       ↓
cross-application analysis
```

The result is not just a list of APIs, but a structured dataset for understanding where integrations are technically straightforward, where credentials create friction, and where documentation requires additional verification.
