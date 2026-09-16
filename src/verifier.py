import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.search import search_web

load_dotenv()


LM_STUDIO_BASE_URL = os.getenv(
    "LM_STUDIO_BASE_URL",
    "http://localhost:1234/v1"
)

LM_STUDIO_MODEL = os.getenv(
    "LM_STUDIO_MODEL",
    "google/gemma-4-e4b"
)


client = OpenAI(
    base_url=LM_STUDIO_BASE_URL,
    api_key="lm-studio"
)


# ============================================================
# INDEPENDENT SEARCH
# ============================================================

def independent_search(result):

    queries = [
        f'"{result["name"]}" official API documentation authentication credentials',
        f'"{result["name"]}" official API reference SDK MCP',
    ]

    evidence = []

    for query in queries:

        print(f"  Verification search: {query}")

        try:
            results = search_web(
                query=query,
                max_results=5,
            )

            for item in results:

                evidence.append({
                    "query": query,
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0),
                })

        except Exception as e:

            print(
                f"  Search failed for query: {query}"
            )

            print(
                f"  Error: {e}"
            )

    return evidence

# ============================================================
# BUILD VERIFICATION PROMPT
# ============================================================

def build_verification_prompt(result):

    # --------------------------------------------------------
    # Original research evidence
    # --------------------------------------------------------

    evidence_text = ""

    for i, item in enumerate(
        result.get("evidence", []),
        start=1
    ):

        evidence_text += f"""
ORIGINAL SOURCE {i}

Claim:
{item.get("claim", "")}

URL:
{item.get("url", "")}

--------------------------------------------------
"""


    # --------------------------------------------------------
    # Independently retrieved evidence
    # --------------------------------------------------------

    independent_evidence_text = ""

    for i, item in enumerate(
        result.get("independent_evidence", []),
        start=1
    ):

        independent_evidence_text += f"""
INDEPENDENT SOURCE {i}

Title:
{item.get("title", "")}

URL:
{item.get("url", "")}

Content:
{item.get("content", "")}

--------------------------------------------------
"""


    # --------------------------------------------------------
    # Prompt
    # --------------------------------------------------------

    return f"""
You are an independent verification agent.

Your job is NOT to blindly accept the researcher's conclusions.

Your job is to determine whether each conclusion is actually
supported by the available evidence.

The researcher produced a structured result.

You must critically verify it using:

1. The researcher's original evidence.
2. Independently retrieved evidence.

==================================================
RESEARCH RESULT
==================================================

Application:
{result["name"]}

Category:
{result["category"]}

Description:
{result["description"]}

Authentication methods:
{result["auth_methods"]}

Access type:
{result["access_type"]}

API types:
{result["api_types"]}

SDK available:
{result["sdk_available"]}

API breadth:
{result["api_breadth"]}

MCP status:
{result["mcp_status"]}

Buildability:
{result["buildability"]}

Blocker:
{result["blocker"]}


==================================================
ORIGINAL RESEARCH EVIDENCE
==================================================

{evidence_text}


==================================================
INDEPENDENTLY RETRIEVED EVIDENCE
==================================================

{independent_evidence_text}


==================================================
FIELDS TO VERIFY
==================================================

Verify these fields:

1. auth_methods
2. access_type
3. api_types
4. sdk_available
5. api_breadth
6. mcp_status
7. buildability
8. blocker


==================================================
VERIFICATION RULES
==================================================

1. DO NOT TRUST THE RESEARCHER.

The researcher's output is a hypothesis that must be checked.


2. EVIDENCE MUST SUPPORT THE CLAIM.

A claim is "supported" only when the evidence actually establishes
the conclusion.


3. PREFER OFFICIAL SOURCES.

Use this priority:

1. Official developer documentation
2. Official API reference
3. Official GitHub/repository
4. Official company documentation
5. Reputable technical documentation
6. Blogs/articles
7. Search snippets


4. THIRD-PARTY SOURCES

A third-party source can provide useful supporting evidence.

However, it must not be treated as proof of an official company
feature when an official source is required.


5. GRAPHQL

Only accept GraphQL when evidence demonstrates that the company
actually provides a GraphQL API.

Examples that DO NOT prove GraphQL:

- third-party GraphQL connector
- Apollo connector
- third-party SDK
- wrapper
- integration
- community library

For example, if official documentation says the API is REST and
a third-party website mentions GraphQL, do NOT accept GraphQL
as an API type.


6. MCP

Only classify MCP as "official" if evidence comes from the
company itself or an official company repository/documentation.

A third-party MCP server must be:

"third_party"


7. SDK

SDK means an official client library provided by the company.

A third-party SDK does NOT count.

Only mark sdk_available=true when official evidence supports it.


8. ACCESS TYPE

Public documentation does NOT automatically mean self-serve access.

Look for evidence about:

- account creation
- obtaining API credentials
- API keys
- developer registration
- approval
- partner requirements
- paid plans
- contacting sales


9. BUILDABILITY

Buildability depends on whether a developer can realistically
obtain credentials and use the documented API.

Do not mark something buildable merely because documentation exists.


10. CONFLICTING SOURCES

If sources disagree:

- Prefer official sources.
- Prefer primary documentation over third-party sources.
- Do not combine contradictory claims.
- If the conflict cannot be resolved, mark the field unsupported
  and reduce confidence.


==================================================
STATUS VALUES
==================================================

For each field use exactly one of:

"supported"

"unsupported"

"contradicted"


SUPPORTED:

The evidence supports the researcher's conclusion.


UNSUPPORTED:

There is insufficient evidence to establish the researcher's
conclusion.


CONTRADICTED:

The evidence indicates that the researcher's conclusion is wrong.


==================================================
CORRECTIONS
==================================================

If a field is unsupported or contradicted, provide the corrected
value when the evidence allows a correction.

IMPORTANT:

The correction MUST use the same data type as the original field.


For api_types:

CORRECT:

"api_types": ["REST"]


INCORRECT:

"api_types": ["REST, GraphQL"]


INCORRECT:

"api_types": "REST"


For auth_methods:

CORRECT:

"auth_methods": ["API Key"]


For sdk_available:

CORRECT:

"sdk_available": true


or:

"sdk_available": false


If there is insufficient evidence:

"sdk_available": null


For access_type:

CORRECT:

"access_type": "self_serve"


If there is insufficient evidence:

"access_type": null


Only include fields in "corrections" that actually require
correction.

Do NOT invent a correction when evidence is insufficient.


==================================================
IMPORTANT API TYPE RULE
==================================================

Do not treat SDK as an API type.

Do not treat a third-party GraphQL integration as evidence that
the company's API is GraphQL.

Do not treat a third-party wrapper as evidence of the underlying
API protocol.


==================================================
OUTPUT
==================================================

Return EXACTLY ONE JSON object.

Use this structure:

{{
  "id": {result["id"]},
  "name": "{result["name"]}",
  "overall_status": "needs_correction",

  "field_checks": {{

    "auth_methods": {{
      "status": "supported",
      "reason": "..."
    }},

    "access_type": {{
      "status": "unsupported",
      "reason": "..."
    }},

    "api_types": {{
      "status": "contradicted",
      "reason": "..."
    }},

    "sdk_available": {{
      "status": "supported",
      "reason": "..."
    }},

    "api_breadth": {{
      "status": "supported",
      "reason": "..."
    }},

    "mcp_status": {{
      "status": "supported",
      "reason": "..."
    }},

    "buildability": {{
      "status": "supported",
      "reason": "..."
    }},

    "blocker": {{
      "status": "supported",
      "reason": "..."
    }}

  }},

  "corrections": {{}}
}}


If the researcher's api_types is:

["REST", "GraphQL"]

and the evidence only supports REST, return:

"corrections": {{
  "api_types": ["REST"]
}}


NOT:

"api_types": ["REST, GraphQL"]


If no fields require correction:

"overall_status": "pass"

and:

"corrections": {{}}


If ANY important field is contradicted or unsupported:

"overall_status": "needs_correction"


==================================================
STRICT JSON REQUIREMENTS
==================================================

Return ONLY the JSON object.

Do NOT use Markdown code fences.

Do NOT write:

```json

Do NOT provide explanations before or after the JSON.

Do NOT add fields.

Do NOT rename fields.

Do NOT omit fields.

All status values must be exactly:

supported
unsupported
contradicted
"""


# ============================================================
# CLEAN JSON
# ============================================================

def clean_json_response(raw):

    raw = raw.strip()

    # Remove Markdown code fences if Gemma adds them.
    if raw.startswith("```"):

        lines = raw.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        raw = "\n".join(lines)

    return raw.strip()


# ============================================================
# VERIFY RESULT
# ============================================================

def verify_result(result):

    print("\nRunning independent verification searches...")

    independent_evidence = independent_search(
        result
    )

    print(
        f"\nCollected "
        f"{len(independent_evidence)} "
        f"independent sources."
    )

    # Make a copy so we don't mutate the original result.
    result_for_verification = dict(result)

    result_for_verification[
        "independent_evidence"
    ] = independent_evidence

    prompt = build_verification_prompt(
        result_for_verification
    )

    response = client.chat.completions.create(
        model=LM_STUDIO_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are an independent fact-checking system. "
                    "Critically verify claims. "
                    "Return only valid JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.0,
    )

    raw = response.choices[0].message.content

    print("\nVerifier raw response:")
    print(raw)

    cleaned = clean_json_response(raw)

    try:

        verification = json.loads(
            cleaned
        )

    except json.JSONDecodeError as e:

        print("\nERROR: Verifier returned invalid JSON.")

        print("\nCleaned response:")
        print(cleaned)

        raise e

    return verification


# ============================================================
# SAVE VERIFICATION
# ============================================================

def save_verification(result):

    output_path = Path(
        "results/verification_results.json"
    )

    existing = []

    if output_path.exists():

        try:

            existing = json.loads(
                output_path.read_text()
            )

        except json.JSONDecodeError:

            existing = []


    # Replace previous result for this application.
    existing = [
        item
        for item in existing
        if item["id"] != result["id"]
    ]


    existing.append(result)

    existing.sort(
        key=lambda x: x["id"]
    )


    output_path.write_text(
        json.dumps(
            existing,
            indent=2
        )
    )


    print(
        f"\nSaved verification to "
        f"{output_path}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    research_path = Path(
        "results/research_results.json"
    )


    if not research_path.exists():

        raise RuntimeError(
            "research_results.json does not exist. "
            "Run researcher.py first."
        )


    results = json.loads(
        research_path.read_text()
    )


    if not results:

        raise RuntimeError(
            "research_results.json is empty."
        )


    # For now verify the most recently researched application.
    result = results[-1]


    print("=" * 70)

    print(
        f"Verifying: {result['name']}"
    )

    print("=" * 70)


    verification = verify_result(
        result
    )


    save_verification(
        verification
    )


    print(
        "\nFINAL VERIFICATION:"
    )

    print(
        json.dumps(
            verification,
            indent=2
        )
    )