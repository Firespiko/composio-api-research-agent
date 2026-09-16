import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
import re

from src.search import search_web
from src.schema import ResearchResult
from urllib.parse import urlparse


load_dotenv()

def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def source_quality(url: str, app_name: str) -> int:
    domain = get_domain(url)

    app = (
        app_name.lower()
        .replace(" ", "")
        .replace("-", "")
        .replace(".", "")
    )

    clean_domain = (
        domain
        .replace("www.", "")
        .replace(".", "")
        .replace("-", "")
    )

    # Strong signal for official domain
    if app in clean_domain:
        return 3

    # Official-looking developer/documentation sources
    if any(x in domain for x in [
        "docs.",
        "developer.",
        "developers.",
        "api.",
    ]):
        return 2

    return 1




# ---------------------------------------------------------
# Local LLM
# ---------------------------------------------------------

client = OpenAI(
    base_url=os.getenv("LM_STUDIO_BASE_URL"),
    api_key="lm-studio",
)

MODEL = os.getenv("LM_STUDIO_MODEL")


# ---------------------------------------------------------
# Research queries
# ---------------------------------------------------------


def build_queries(app):

    name = app["name"]
    hint = app["hint"]

    return [
        f'"{name}" official API developer documentation authentication',
        f'"{name}" official API reference credentials access',
    ]


# ---------------------------------------------------------
# Search
# ---------------------------------------------------------

def collect_evidence(app):
    evidence = []

    queries = build_queries(app)

    for query in queries:

        print(f"  Searching: {query}")

        results = search_web(
            query=query,
            max_results=5,
        )

        for result in results:

            url = result.get("url", "")

            evidence.append({
                "query": query,
                "title": result.get("title", ""),
                "url": url,
                "content": result.get("content", ""),
                "score": result.get("score", 0),

                # New field
                "source_quality": source_quality(
                    url,
                    app["name"]
                ),
            })

    # Put higher-quality sources first.
    #
    # Priority:
    # 3 = company's official domain
    # 2 = developer/docs/API domain
    # 1 = third-party source
    #
    # Within the same quality level, use Tavily's relevance score.
    evidence.sort(
        key=lambda x: (
            x["source_quality"],
            x["score"]
        ),
        reverse=True
    )

    return evidence

# ---------------------------------------------------------
# Remove duplicate URLs
# ---------------------------------------------------------

def deduplicate_evidence(evidence):

    seen = set()
    unique = []

    for item in evidence:

        url = item["url"]

        if url in seen:
            continue

        seen.add(url)
        unique.append(item)

    return unique


# ---------------------------------------------------------
# Build LLM prompt
# ---------------------------------------------------------

def build_prompt(app, evidence):

    evidence_text = ""

    for i, item in enumerate(evidence, start=1):

        evidence_text += f"""
SOURCE {i}

Title:
{item["title"]}

URL:
{item["url"]}

Source Quality:
{item.get("source_quality", "unknown")}

Content:
{item["content"]}

--------------------------------------------------
"""

    output_schema = """
{
  "id": 0,
  "name": "",
  "category": "",
  "description": "",
  "auth_methods": [],
  "access_type": "",
  "api_types": [],
  "sdk_available": false,
  "api_breadth": "",
  "mcp_status": "",
  "buildability": "",
  "blocker": null,
  "evidence": [],
  "confidence": 0.0
}
"""

    evidence_format = """
[
  {
    "claim": "The API uses API keys for authentication",
    "url": "https://docs.example.com/auth"
  }
]
"""

    return f"""
You are an API research agent.

Your task is to research an application for an AI-agent
integration platform.

==================================================
APPLICATION
==================================================

ID:
{app["id"]}

Name:
{app["name"]}

Category:
{app["category"]}

Initial documentation hint:
{app["hint"]}


==================================================
EVIDENCE
==================================================

{evidence_text}


==================================================
TASK
==================================================

Using ONLY the evidence above, determine the following.


1. DESCRIPTION

What does the application do?

Write one concise sentence.


2. AUTHENTICATION METHODS

Determine how developers authenticate with the API.

Allowed values:

- OAuth2
- API Key
- Basic
- Bearer Token
- API Token
- Other
- Unknown

Only include authentication methods supported by the evidence.

Do not assume an authentication method exists just because it is
common for similar applications.


3. DEVELOPER ACCESS

Determine how a developer can obtain API access or credentials.

Allowed values:

- self_serve
- free_trial
- paid_plan
- admin_approval
- partner_gated
- contact_sales
- unknown

IMPORTANT:

Public API documentation does NOT mean that API access is free.

Documentation availability and credential availability are different.

Look for evidence about:

- creating an account
- obtaining API keys
- developer registration
- requesting access
- approval requirements
- paid plans
- contacting sales
- partner programs

If the evidence does not establish the access requirement, use:

unknown


4. API SURFACE

Determine the actual API protocols/interfaces provided by the company.

Allowed values:

- REST
- GraphQL
- SOAP
- WebSocket
- gRPC
- Other
- Unknown

IMPORTANT:

SDK is NOT an API type.

Do NOT put "SDK" inside api_types.

Only classify GraphQL if the evidence explicitly demonstrates that
the company provides a GraphQL API.

A third-party:

- GraphQL connector
- Apollo connector
- SDK
- integration
- wrapper
- community library

does NOT prove that the company's API itself is GraphQL.

Similarly, a third-party library implementing an API does not prove
that the underlying company API uses that protocol.


5. SDK AVAILABILITY

Determine whether the company provides official client libraries
or SDKs.

Use JSON boolean/null values:

true
false
null

Do NOT return these as strings.

Correct:
"sdk_available": true

Incorrect:
"sdk_available": "true"

If there is insufficient evidence:
"sdk_available": null
Only mark true when official company documentation or an official
repository provides evidence of SDK/client-library support.

Third-party SDKs do not count.


6. API BREADTH

Estimate the breadth of the API based on the documented resources
and capabilities.

Use:

- narrow
- moderate
- broad
- unknown

Examples:

narrow:
Only a small number of resources or one specific capability.

moderate:
Several resources but limited overall coverage.

broad:
Many major resources, operations, and capabilities across the
application.

Do not infer breadth merely from the popularity of the application.


7. MCP AVAILABILITY

Determine whether an MCP implementation exists.

Allowed values:

- official
- third_party
- none_found
- unknown

IMPORTANT:

Only classify MCP as "official" when the evidence comes from:

- the company's official documentation
- the company's official GitHub
- another clearly official company source

A third-party MCP server must be classified as:

third_party

Do not confuse a third-party MCP server with an official MCP server.


8. BUILDABILITY

Determine whether an AI-agent integration could realistically be
built using the documented API access.

Allowed values:

- buildable
- buildable_with_constraints
- blocked
- unknown

Consider:

- credential availability
- authentication requirements
- API availability
- approval requirements
- paid requirements
- API limitations
- missing documentation

Use "buildable" when a developer can realistically obtain credentials
and use the API.

Use "buildable_with_constraints" when integration is possible but
there are meaningful restrictions.

Use "blocked" when the required access cannot reasonably be obtained
through normal developer access.

Use "unknown" when the evidence is insufficient.


9. MAIN BLOCKER

Identify the primary obstacle to integration.

Examples:

- API access requires contacting sales
- Partner approval required
- API access requires paid plan
- No public API
- Restricted API access
- Missing authentication documentation

If there is no meaningful blocker:

null


10. EVIDENCE

For every important conclusion, provide supporting evidence.

Each evidence item MUST contain exactly two fields:

- claim
- url

The format is:

{evidence_format}

Do not add:

- claim_2
- claim_3
- title
- source
- notes
- reasoning
- any other fields

Every important claim should be traceable to a URL from the supplied
evidence.


11. CONFIDENCE

Give an estimated confidence between:

0.0 and 1.0

IMPORTANT:

Do not give a high confidence score merely because the answer looks
plausible.

Confidence should decrease when:

- evidence is weak
- evidence is contradictory
- only third-party sources support a claim
- important information is missing
- search results are ambiguous

If important fields are "unknown", confidence should generally be
lower.


==================================================
SOURCE QUALITY RULES
==================================================

Official company documentation has the highest priority.

For:

- API protocols
- authentication
- MCP
- credential requirements
- API availability

prefer sources in this order:

1. Official developer documentation
2. Official API reference
3. Official GitHub/repository
4. Official company documentation
5. Reputable third-party technical documentation
6. Blogs/articles
7. Search snippets


IMPORTANT:

Never infer an API protocol from the existence of a third-party
integration.

For example:

Third-party GraphQL connector
does NOT prove GraphQL API.

Third-party MCP server
does NOT prove official MCP.

Third-party SDK
does NOT prove official SDK.

API documentation
does NOT automatically prove free/self-serve access.


==================================================
CONFLICTING EVIDENCE
==================================================

If sources disagree:

- Prefer official sources.
- Do not combine contradictory claims.
- Do not invent a resolution.
- Use the most authoritative source.
- If the conflict cannot be resolved, use "unknown" where appropriate
  and lower confidence.


==================================================
OUTPUT FORMAT
==================================================

Return EXACTLY ONE JSON object.

Use these EXACT field names:

{output_schema}

The evidence field MUST be an array.

The sdk_available field MUST be:

true

false

or

null


Return ONLY the JSON object.

DO NOT wrap the JSON in Markdown code fences.

DO NOT write:

```json

DO NOT provide explanations before or after the JSON.

DO NOT add additional fields.

DO NOT rename fields.

DO NOT omit required fields.
"""

# ---------------------------------------------------------
# Gemma extraction
# ---------------------------------------------------------

def extract_with_gemma(app, evidence):

    prompt = build_prompt(app, evidence)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise research extraction system. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()

    print("\nGemma raw response:")
    print(raw)


    def clean_json_response(raw: str) -> str:
        """
        Remove Markdown code fences if the model wraps JSON in them.
        """

        raw = raw.strip()

        # ```json
        # {...}
        # ```
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

        return raw.strip()


    cleaned = clean_json_response(raw)

    data = json.loads(cleaned)

    # Validate with Pydantic
    result = ResearchResult.model_validate(data)

    return result


# ---------------------------------------------------------
# Research one application
# ---------------------------------------------------------

def research_app(app):

    print(f"\n{'=' * 70}")
    print(f"Researching: {app['name']}")
    print(f"{'=' * 70}")

    evidence = collect_evidence(app)

    evidence = deduplicate_evidence(evidence)

    print(
        f"\nCollected {len(evidence)} unique sources."
    )

    result = extract_with_gemma(
        app,
        evidence,
    )

    return result


# ---------------------------------------------------------
# Save result
# ---------------------------------------------------------

def save_result(result):

    output_path = Path("results/research_results.json")

    existing = []

    if output_path.exists():

        with open(output_path, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    # Remove previous result for same app
    existing = [
        item
        for item in existing
        if item["id"] != result.id
    ]

    existing.append(
        result.model_dump()
    )

    existing.sort(
        key=lambda x: x["id"]
    )

    with open(output_path, "w") as f:

        json.dump(
            existing,
            f,
            indent=2,
        )

    print(
        f"\nSaved result to {output_path}"
    )


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------

if __name__ == "__main__":

    app = {
        "id": 81,
        "name": "Stripe",
        "category": "Finance and Fintech",
        "hint": "stripe.com/docs/api",
    }

    result = research_app(app)

    save_result(result)

    print("\nFINAL RESULT:")
    print(
        json.dumps(
            result.model_dump(),
            indent=2,
        )
    )