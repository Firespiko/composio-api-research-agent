import json
from collections import Counter
from pathlib import Path


RESEARCH_PATH = Path(
    "results/research_results.json"
)

VERIFICATION_PATH = Path(
    "results/verification_results.json"
)


FIELDS = [
    "category",
    "description",
    "auth_methods",
    "access_type",
    "api_types",
    "sdk_available",
    "api_breadth",
    "mcp_status",
    "buildability",
    "blocker",
]


def load_json(path):

    if not path.exists():
        return []

    try:
        return json.loads(
            path.read_text()
        )
    except json.JSONDecodeError:
        return []


def count_values(results, field):

    counter = Counter()

    for result in results:

        values = result.get(field)

        if isinstance(values, list):

            for value in values:

                if value is not None:
                    counter[value] += 1

        elif values is not None:

            counter[values] += 1

    return counter


def percentage(part, total):

    if total == 0:
        return 0.0

    return (part / total) * 100


def values_equal(a, b):

    if isinstance(a, list):
        a = sorted(a)

    if isinstance(b, list):
        b = sorted(b)

    return a == b


def analyze_verification(
    research_results,
    verification_results
):

    research_by_id = {
        result["id"]: result
        for result in research_results
    }

    verified_apps = []
    corrected_apps = []
    field_corrections = Counter()

    for verification in verification_results:

        app_id = verification.get("id")

        original = research_by_id.get(
            app_id
        )

        if not original:
            continue

        verified_apps.append(
            original["name"]
        )

        corrections = verification.get(
            "corrections",
            {}
        )

        if not isinstance(
            corrections,
            dict
        ):
            continue

        app_changes = []

        for field, corrected_value in corrections.items():

            if field not in FIELDS:
                continue

            original_value = original.get(
                field
            )

            if not values_equal(
                original_value,
                corrected_value
            ):

                field_corrections[field] += 1

                app_changes.append({
                    "field": field,
                    "original": original_value,
                    "corrected": corrected_value,
                })

        if app_changes:

            corrected_apps.append({
                "id": app_id,
                "name": original["name"],
                "changes": app_changes,
            })

    return (
        verified_apps,
        corrected_apps,
        field_corrections,
    )


def print_distribution(
    title,
    counter,
    total
):

    print(f"\n{title}:")

    for value, count in counter.most_common():

        pct = percentage(
            count,
            total
        )

        print(
            f"  {value}: "
            f"{count} "
            f"({pct:.1f}%)"
        )


def main():

    research_results = load_json(
        RESEARCH_PATH
    )

    verification_results = load_json(
        VERIFICATION_PATH
    )

    research_count = len(
        research_results
    )

    verification_count = len(
        verification_results
    )

    # ================================================================
    # OVERVIEW
    # ================================================================

    print("=" * 70)
    print("COMPOSIO API RESEARCH ANALYSIS")
    print("=" * 70)

    print(
        f"\nApplications researched: "
        f"{research_count}"
    )

    print(
        f"Applications independently verified: "
        f"{verification_count}"
    )

    print(
        f"Research coverage: "
        f"{research_count}/100 "
        f"({percentage(research_count, 100):.1f}%)"
    )

    print(
        f"Verification coverage: "
        f"{verification_count}/{research_count} "
        f"({percentage(verification_count, research_count):.1f}%)"
    )

    # ================================================================
    # AUTHENTICATION
    # ================================================================

    print_distribution(
        "Authentication methods",
        count_values(
            research_results,
            "auth_methods"
        ),
        research_count
    )

    # ================================================================
    # ACCESS
    # ================================================================

    print_distribution(
        "Developer credential access",
        count_values(
            research_results,
            "access_type"
        ),
        research_count
    )

    # ================================================================
    # API TYPES
    # ================================================================

    print_distribution(
        "API types",
        count_values(
            research_results,
            "api_types"
        ),
        research_count
    )

    # ================================================================
    # SDK
    # ================================================================

    print_distribution(
        "SDK availability",
        count_values(
            research_results,
            "sdk_available"
        ),
        research_count
    )

    # ================================================================
    # MCP
    # ================================================================

    print_distribution(
        "MCP status",
        count_values(
            research_results,
            "mcp_status"
        ),
        research_count
    )

    # ================================================================
    # BUILDABILITY
    # ================================================================

    print_distribution(
        "Buildability",
        count_values(
            research_results,
            "buildability"
        ),
        research_count
    )

    # ================================================================
    # API BREADTH
    # ================================================================

    print_distribution(
        "API breadth",
        count_values(
            research_results,
            "api_breadth"
        ),
        research_count
    )

    # ================================================================
    # BLOCKERS
    # ================================================================

    print_distribution(
        "Blockers",
        count_values(
            research_results,
            "blocker"
        ),
        research_count
    )

    # ================================================================
    # CATEGORIES
    # ================================================================

    print_distribution(
        "Categories",
        count_values(
            research_results,
            "category"
        ),
        research_count
    )

    # ================================================================
    # VERIFICATION
    # ================================================================

    (
        verified_apps,
        corrected_apps,
        field_corrections,
    ) = analyze_verification(
        research_results,
        verification_results
    )

    print("\n" + "=" * 70)
    print("INDEPENDENT VERIFICATION")
    print("=" * 70)

    print(
        f"\nVerified applications: "
        f"{len(verified_apps)}"
    )

    print(
        f"Applications with actual field changes: "
        f"{len(corrected_apps)}"
    )

    print(
        f"Correction rate among verified: "
        f"{percentage(len(corrected_apps), verification_count):.1f}%"
    )

    # ================================================================
    # FIELD-LEVEL CORRECTIONS
    # ================================================================

    print("\nField-level corrections:")

    if field_corrections:

        for field, count in field_corrections.most_common():

            print(
                f"  {field}: "
                f"{count}"
            )

    else:

        print(
            "  None"
        )

    # ================================================================
    # ACTUAL CORRECTIONS
    # ================================================================

    print("\nActual corrections:")

    if corrected_apps:

        for app in corrected_apps:

            print(
                f"\n  {app['name']} "
                f"(ID {app['id']})"
            )

            for change in app["changes"]:

                print(
                    f"    {change['field']}:"
                )

                print(
                    f"      Research: "
                    f"{change['original']}"
                )

                print(
                    f"      Verified: "
                    f"{change['corrected']}"
                )

    else:

        print(
            "  None"
        )

    # ================================================================
    # CONFIDENCE
    # ================================================================

    confidence_values = [
        result.get(
            "confidence",
            0
        )
        for result in research_results
    ]

    if confidence_values:

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
        )

        print("\n" + "=" * 70)
        print("CONFIDENCE")
        print("=" * 70)

        print(
            f"\nAverage confidence: "
            f"{average_confidence:.2f}"
        )

        low_confidence = [
            result
            for result in research_results
            if result.get(
                "confidence",
                0
            ) < 0.75
        ]

        print(
            f"Low-confidence results (< 0.75): "
            f"{len(low_confidence)}"
        )

        for result in low_confidence:

            print(
                f"  {result['name']}: "
                f"{result.get('confidence', 0):.2f}"
            )

    # ================================================================
    # BUILDABILITY
    # ================================================================

    buildability = count_values(
        research_results,
        "buildability"
    )

    buildable = sum(
        count
        for value, count
        in buildability.items()
        if str(value).lower()
        in {
            "buildable",
            "easy",
        }
    )

    constrained = sum(
        count
        for value, count
        in buildability.items()
        if str(value).lower()
        == "buildable_with_constraints"
    )

    unknown = sum(
        count
        for value, count
        in buildability.items()
        if str(value).lower()
        == "unknown"
    )

    print("\n" + "=" * 70)
    print("BUILDABILITY SUMMARY")
    print("=" * 70)

    print(
        f"\nBuildable: "
        f"{buildable}"
    )

    print(
        f"Buildable with constraints: "
        f"{constrained}"
    )

    print(
        f"Unknown: "
        f"{unknown}"
    )

    # ================================================================
    # MACHINE-READABLE SUMMARY
    # ================================================================

    summary = {
        "research_count": research_count,
        "verification_count": verification_count,
        "research_coverage": percentage(
            research_count,
            100
        ),
        "verification_coverage": percentage(
            verification_count,
            research_count
        ),
        "correction_count": len(
            corrected_apps
        ),
        "correction_rate": percentage(
            len(corrected_apps),
            verification_count
        ),
        "authentication": dict(
            count_values(
                research_results,
                "auth_methods"
            )
        ),
        "access": dict(
            count_values(
                research_results,
                "access_type"
            )
        ),
        "api_types": dict(
            count_values(
                research_results,
                "api_types"
            )
        ),
        "sdk": dict(
            count_values(
                research_results,
                "sdk_available"
            )
        ),
        "mcp": dict(
            count_values(
                research_results,
                "mcp_status"
            )
        ),
        "buildability": dict(
            buildability
        ),
        "api_breadth": dict(
            count_values(
                research_results,
                "api_breadth"
            )
        ),
        "categories": dict(
            count_values(
                research_results,
                "category"
            )
        ),
        "field_corrections": dict(
            field_corrections
        ),
    }

    summary_path = Path(
        "results/analysis_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2
        )
    )

    print(
        f"\nSaved analysis summary to: "
        f"{summary_path}"
    )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()