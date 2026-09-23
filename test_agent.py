"""
Tests for agent.py's tool functions. These test the deterministic logic
only (no network call, no API key needed) so they can run in CI on every
push. The conversational loop itself (run_conversation) calls the Anthropic
API and is exercised manually via `python agent.py`, not here.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import check_grounding, check_pole_capacity, check_guy_anchor, TOOLS, TOOL_FUNCTIONS


def test_check_grounding_passes_within_limit():
    result = check_grounding(21)
    assert result["passed"] is True
    assert result["rule_id"] == "NESC-092"


def test_check_grounding_fails_over_limit():
    result = check_grounding(32)
    assert result["passed"] is False


def test_check_pole_capacity_passes_within_limit():
    result = check_pole_capacity(85.8)
    assert result["passed"] is True
    assert result["rule_id"] == "STRUCT-CAP"


def test_check_pole_capacity_fails_over_limit():
    result = check_pole_capacity(105)
    assert result["passed"] is False


def test_check_guy_anchor_passes_when_selected_meets_required():
    result = check_guy_anchor(3086, 4000)
    assert result["passed"] is True
    assert result["rule_id"] == "GUY-ANCHOR"


def test_check_guy_anchor_fails_when_selected_below_required():
    result = check_guy_anchor(4000, 3000)
    assert result["passed"] is False


def test_tool_schema_matches_tool_functions():
    tool_names = {t["name"] for t in TOOLS}
    assert tool_names == set(TOOL_FUNCTIONS.keys())


def run_all():
    tests = [
        test_check_grounding_passes_within_limit,
        test_check_grounding_fails_over_limit,
        test_check_pole_capacity_passes_within_limit,
        test_check_pole_capacity_fails_over_limit,
        test_check_guy_anchor_passes_when_selected_meets_required,
        test_check_guy_anchor_fails_when_selected_below_required,
        test_tool_schema_matches_tool_functions,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passing")


if __name__ == "__main__":
    run_all()
