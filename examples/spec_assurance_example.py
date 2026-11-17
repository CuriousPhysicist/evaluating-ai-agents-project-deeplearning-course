"""Example: Using the generic compliance scoring engine with T1-T21 specification.

This script demonstrates how to:
1. Load the T1-T21 requirement specification
2. Gather test results from pytest markers
3. Calculate compliance score
4. Generate a compliance report
"""

from pathlib import Path

from agent_evals.spec_assurance import (
    calculate_compliance_score,
    load_spec_from_yaml,
)


def example_basic_scoring():
    """Basic example: Load spec and calculate score."""
    # Load the T1-T21 specification
    spec_path = Path(__file__).parent.parent / "requirements" / "t1-t21-spec.yaml"
    spec = load_spec_from_yaml(spec_path)

    # Simulate test results (in real use, these come from pytest)
    test_results = {
        "T1_setup": "pass",
        "T1_project_structure": "pass",
        "T2_upload": "pass",
        "T2_phoenix_integration": "pass",
        # ... etc for all T3-T21 markers
        "T10_call_limit": "pass",
        "T10_experiment_failure": "fail",  # T10 partially covered
        # Remaining markers can be skip or missing
    }

    # Calculate compliance
    result = calculate_compliance_score(spec, test_results)

    print("=== Compliance Score Report ===")
    print(f"Overall Score: {result['overall_score']:.2%}")
    print(f"Compliance: {result['compliance_percentage']:.1f}%")
    print(f"Tests Passed: {result['aggregate']['total_pass']}")
    print(f"Tests Failed: {result['aggregate']['total_fail']}")
    print(f"Tests Skipped: {result['aggregate']['total_skip']}")
    print()

    # Print per-requirement details
    print("=== Per-Requirement Scores ===")
    for req_id in sorted(result["per_requirement"].keys()):
        req = result["per_requirement"][req_id]
        print(
            f"{req_id}: {req['score']:.2%} "
            f"({req['test_counts']['pass']}P/"
            f"{req['test_counts']['fail']}F/"
            f"{req['test_counts']['skip']}S)"
        )


def example_regression_check():
    """Example: Check if score dropped from baseline."""
    spec_path = Path(__file__).parent.parent / "requirements" / "t1-t21-spec.yaml"
    spec = load_spec_from_yaml(spec_path)

    # Baseline results (previous run)
    baseline_results = {
        f"T{i}_{j}": "pass" for i in range(1, 22) for j in range(2)
    }

    # Current results (some regressions)
    current_results = baseline_results.copy()
    current_results["T10_call_limit"] = "fail"
    current_results["T18_subprocess_timeout"] = "fail"

    baseline_score = calculate_compliance_score(spec, baseline_results)
    current_score = calculate_compliance_score(spec, current_results)

    baseline_pct = baseline_score["compliance_percentage"]
    current_pct = current_score["compliance_percentage"]
    delta = current_pct - baseline_pct

    print("=== Regression Check ===")
    print(f"Baseline: {baseline_pct:.1f}%")
    print(f"Current:  {current_pct:.1f}%")
    print(f"Change:   {delta:+.1f}%")

    if delta < 0:
        print("⚠️ WARNING: Score decreased!")
        print("\nAffected requirements:")
        for req_id in sorted(baseline_score["per_requirement"].keys()):
            baseline_req = baseline_score["per_requirement"][req_id]
            current_req = current_score["per_requirement"][req_id]
            if current_req["score"] < baseline_req["score"]:
                print(
                    f"  {req_id}: {baseline_req['score']:.2%} -> "
                    f"{current_req['score']:.2%}"
                )


if __name__ == "__main__":
    print("Example 1: Basic Scoring\n")
    try:
        example_basic_scoring()
    except FileNotFoundError as e:
        print(f"Note: {e}")
        print(
            "This example requires the T1-T21 spec file. "
            "Run from the project root.\n"
        )

    print("\n" + "=" * 50)
    print("\nExample 2: Regression Detection\n")
    try:
        example_regression_check()
    except FileNotFoundError as e:
        print(f"Note: {e}")
