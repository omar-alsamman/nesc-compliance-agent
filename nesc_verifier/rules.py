"""Deterministic NESC-derived rule checks.

These are hard engineering limits, not judgment calls -- no LLM involved.
Each function takes a PoleLoadingInputs and returns a RuleResult. Sources:
NESC Section 9 (grounding, Rule 092/096C) and standard pole
capacity/structural-loading practice as applied in the reference project
(see data/nesc_reference.md).
"""

from __future__ import annotations

from .schema import PoleLoadingInputs, RuleResult

MAX_GROUND_RESISTANCE_OHM = 25.0
MAX_POLE_CAPACITY_PCT = 100.0


def check_ground_resistance(inputs: PoleLoadingInputs) -> RuleResult:
      value = inputs.final_ground_resistance_ohm
      if value is None:
                return RuleResult(
                              rule_id="NESC-092",
                              description="Grounding system resistance must not exceed 25 ohm (NESC Rule 092).",
                              passed=False,
                              detail="No final_ground_resistance_ohm value provided -- cannot verify.",
                )
            passed = value <= MAX_GROUND_RESISTANCE_OHM
    return RuleResult(
              rule_id="NESC-092",
              description="Grounding system resistance must not exceed 25 ohm (NESC Rule 092).",
              passed=passed,
              detail=f"Final ground resistance = {value} ohm "
              f"({'within' if passed else 'exceeds'} the 25 ohm limit).",
    )


def check_pole_capacity(inputs: PoleLoadingInputs) -> RuleResult:
      value = inputs.pole_capacity_utilization_pct
    passed = value <= MAX_POLE_CAPACITY_PCT
    return RuleResult(
              rule_id="STRUCT-CAP",
              description="Groundline moment must not exceed rated pole capacity (100%).",
              passed=passed,
              detail=f"Pole capacity utilization = {value}% "
              f"({'within' if passed else 'exceeds'} rated capacity).",
    )


def check_anchor_capacity(inputs: PoleLoadingInputs) -> RuleResult:
      required = inputs.required_anchor_capacity_lb
    selected = inputs.selected_anchor_capacity_lb
    if required is None or selected is None:
              return RuleResult(
                            rule_id="GUY-ANCHOR",
                            description="Selected anchor capacity must meet or exceed the required anchor capacity (NESC Rule 261H).",
                            passed=False,
                            detail="Missing anchor capacity values -- cannot verify.",
              )
          passed = selected >= required
    return RuleResult(
              rule_id="GUY-ANCHOR",
              description="Selected anchor capacity must meet or exceed the required anchor capacity (NESC Rule 261H).",
              passed=passed,
              detail=f"Required = {required} lb, selected = {selected} lb "
              f"({'meets' if passed else 'does not meet'} requirement).",
    )


ALL_CHECKS = [check_ground_resistance, check_pole_capacity, check_anchor_capacity]


def run_all_checks(inputs: PoleLoadingInputs) -> list[RuleResult]:
      return [check(inputs) for check in ALL_CHECKS]
