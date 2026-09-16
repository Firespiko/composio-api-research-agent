import json
import time
from pathlib import Path

from src.researcher import research_app, save_result
from src.verifier import verify_result, save_verification


APPS_PATH = Path("data/apps.json")
RESEARCH_PATH = Path("results/research_results.json")
VERIFICATION_PATH = Path("results/verification_results.json")

# Results below this confidence will be independently verified.
VERIFICATION_THRESHOLD = 0.75


def load_apps():
    return json.loads(
        APPS_PATH.read_text()
    )


def load_existing(path):
    if not path.exists():
        return []

    try:
        return json.loads(
            path.read_text()
        )
    except json.JSONDecodeError:
        return []


def main():

    apps = load_apps()

    # ------------------------------------------------
    # LOAD CHECKPOINTS
    # ------------------------------------------------

    research_results = load_existing(
        RESEARCH_PATH
    )

    verification_results = load_existing(
        VERIFICATION_PATH
    )

    completed_research = {
        item["id"]
        for item in research_results
    }

    completed_verification = {
        item["id"]
        for item in verification_results
    }

    print("\n" + "=" * 70)
    print("COMPOSIO API RESEARCH AGENT")
    print("=" * 70)

    print(
        f"Total applications: {len(apps)}"
    )

    print(
        f"Already researched: {len(completed_research)}"
    )

    print(
        f"Already verified: {len(completed_verification)}"
    )

    # ------------------------------------------------
    # COUNTERS
    # ------------------------------------------------

    research_success = 0
    research_failed = 0

    verification_attempted = 0
    verification_skipped = 0
    verification_success = 0
    verification_failed = 0

    # ------------------------------------------------
    # PROCESS APPS
    # ------------------------------------------------

    for index, app in enumerate(apps, start=1):

        app_id = app["id"]
        name = app["name"]

        print("\n" + "=" * 70)
        print(
            f"[{index}/{len(apps)}] {name}"
        )
        print("=" * 70)

        # ================================================================
        # RESEARCH
        # ================================================================

        if app_id in completed_research:

            print(
                f"Research already exists for {name}"
            )

        else:

            try:

                print(
                    f"Researching {name}..."
                )

                result = research_app(app)

                save_result(result)

                completed_research.add(
                    app_id
                )

                research_results.append(
                    result.model_dump()
                    if hasattr(result, "model_dump")
                    else result
                )

                research_success += 1

                print(
                    f"Research completed: {name}"
                )

            except Exception as e:

                research_failed += 1

                print(
                    f"RESEARCH FAILED: {name}"
                )

                print(
                    f"Error: {e}"
                )

                # Do not attempt verification if research failed.
                continue

        # ================================================================
        # GET SAVED RESEARCH RESULT
        # ================================================================

        try:

            result = next(
                x
                for x in research_results
                if x["id"] == app_id
            )

        except StopIteration:

            print(
                f"Could not find saved research for {name}"
            )

            continue

        # ================================================================
        # VERIFICATION
        # ================================================================

        if app_id in completed_verification:

            print(
                f"Verification already exists for {name}"
            )

        else:

            confidence = result.get(
                "confidence",
                0.0
            )

            print(
                f"Research confidence: {confidence:.2f}"
            )

            # ------------------------------------------------------------
            # HIGH CONFIDENCE
            # ------------------------------------------------------------

            if confidence >= VERIFICATION_THRESHOLD:

                verification_skipped += 1

                print(
                    f"Verification skipped "
                    f"(confidence >= {VERIFICATION_THRESHOLD})"
                )

            # ------------------------------------------------------------
            # LOW CONFIDENCE
            # ------------------------------------------------------------

            else:

                verification_attempted += 1

                print(
                    f"Verification required "
                    f"(confidence < {VERIFICATION_THRESHOLD})"
                )

                try:

                    verification = verify_result(
                        result
                    )

                    save_verification(
                        verification
                    )

                    completed_verification.add(
                        app_id
                    )

                    verification_results.append(
                        verification
                    )

                    verification_success += 1

                    print(
                        f"Verification completed: {name}"
                    )

                except Exception as e:

                    verification_failed += 1

                    print(
                        f"VERIFICATION FAILED: {name}"
                    )

                    print(
                        f"Error: {e}"
                    )

        # ------------------------------------------------
        # Small pause
        # ------------------------------------------------

        time.sleep(1)

    # ================================================================
    # FINAL SUMMARY
    # ================================================================

    print("\n" + "=" * 70)
    print("RUN COMPLETE")
    print("=" * 70)

    print(
        f"Total apps:              {len(apps)}"
    )

    print(
        f"Research completed:      {research_success}"
    )

    print(
        f"Research failed:         {research_failed}"
    )

    print(
        f"Research total saved:    {len(completed_research)}"
    )

    print(
        f"Verification attempted:  {verification_attempted}"
    )

    print(
        f"Verification skipped:    {verification_skipped}"
    )

    print(
        f"Verification successful: {verification_success}"
    )

    print(
        f"Verification failed:     {verification_failed}"
    )

    print(
        f"Total verified:          {len(completed_verification)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()