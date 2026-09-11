"""Regression test using Omar's own completed Residential Distribution Pole
Design project as ground truth. These are the real, verified numbers from
that project (see README) -- the rule engine must reproduce a clean PASS.
"""

from nesc_verifier.rules import run_all_checks
from nesc_verifier.schema import PoleLoadingInputs


def test_reference_project_passes_all_checks():
      inputs = PoleLoadingInputs(
                pole_class="Class 5",
                pole_height_ft=35,
                nesc_grade="C",
                total_wind_load_lb=1091,
                groundline_moment_ft_lb=38588,
                pole_capacity_utilization_pct=85.8,
                guy_wire_tension_lb=1543,
                required_anchor_capacity_lb=3086,
                selected_anchor_capacity_lb=4000,
                final_ground_resistance_ohm=21,
      )
      results = run_all_checks(inputs)
      assert all(r.passed for r in results), [r for r in results if not r.passed]


def test_ground_resistance_failure_is_caught():
      """The project's own design history: the FIRST draft used a single
          ground rod and measured 42 ohm, which should fail. This is why the real
              design used two bonded rods to get to 21 ohm. The rule engine should
                  catch the failing first draft the same way the human review did.
                      """
      inputs = PoleLoadingInputs(
          pole_class="Class 5",
          pole_height_ft=35,
          nesc_grade="C",
          total_wind_load_lb=1091,
          groundline_moment_ft_lb=38588,
          pole_capacity_utilization_pct=85.8,
          final_ground_resistance_ohm=42,
      )
      results = run_all_checks(inputs)
      ground_check = next(r for r in results if r.rule_id == "NESC-092")
      assert ground_check.passed is False
  
