"""Gather evidence from test results for requirement scoring."""

from __future__ import annotations

from typing import Any, TypedDict


class EvidenceData(TypedDict, total=False):
    """Evidence gathered for a single requirement."""

    requirement_id: str
    test_markers: list[str]
    test_outcomes: dict[str, str]  # marker -> pass/fail/skip
    manual_scores: dict[str, float]  # marker -> score
    aggregated_score: float
    source: str  # test_outcome, manual_review, or mixed


def gather_evidence_from_markers(
    requirement_id: str,
    markers: list[str],
    test_results: dict[str, str],
) -> EvidenceData:
    """Gather evidence for a requirement from test marker results.

    Args:
        requirement_id: ID of the requirement (e.g., 'T1')
        markers: List of pytest markers associated with this requirement
        test_results: Dict mapping marker names to test outcomes
                     (e.g., {'T1_setup': 'pass', 'T1_upload': 'pass'})

    Returns:
        EvidenceData with test outcomes
    """
    outcomes = {}
    for marker in markers:
        if marker in test_results:
            outcomes[marker] = test_results[marker]

    return {
        "requirement_id": requirement_id,
        "test_markers": markers,
        "test_outcomes": outcomes,
        "source": "test_outcome",
    }


def gather_evidence_from_manual_review(
    requirement_id: str,
    manual_score: float,
) -> EvidenceData:
    """Create evidence from manual review judgement.

    Args:
        requirement_id: ID of the requirement
        manual_score: Reviewer-assigned score (0.0 - 1.0)

    Returns:
        EvidenceData with manual review data
    """
    return {
        "requirement_id": requirement_id,
        "manual_scores": {requirement_id: manual_score},
        "aggregated_score": manual_score,
        "source": "manual_review",
    }


def compute_score_from_test_outcomes(
    outcomes: dict[str, str],
) -> tuple[float, dict[str, int]]:
    """Compute evidence score from test outcomes.

    Rules:
    - All pass -> 1.0 (covered completely)
    - All pass except some skipped -> 1.0 (skipped doesn't reduce coverage)
    - Mix of pass and fail -> 0.5 (partially covered)
    - All fail -> 0.0 (not covered)
    - No outcomes -> 0.0 (not covered)

    Args:
        outcomes: Dict mapping markers to outcomes (pass/fail/skip)

    Returns:
        Tuple of (score, counts) where counts is {'pass': int, 'fail': int, 'skip': int}
    """
    if not outcomes:
        return 0.0, {"pass": 0, "fail": 0, "skip": 0}

    counts = {"pass": 0, "fail": 0, "skip": 0}
    for outcome in outcomes.values():
        if outcome.lower() == "pass":
            counts["pass"] += 1
        elif outcome.lower() == "fail":
            counts["fail"] += 1
        elif outcome.lower() == "skip":
            counts["skip"] += 1

    # Scoring logic
    if counts["fail"] == 0:
        # All pass or skipped
        return 1.0, counts
    elif counts["pass"] == 0:
        # All fail or skipped with no passes
        return 0.0, counts
    else:
        # Mix of pass and fail
        return 0.5, counts
