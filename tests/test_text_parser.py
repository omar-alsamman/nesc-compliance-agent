"""Regression test for the free, regex-based text parser (no API key needed)."""

from nesc_verifier.text_parser import extract_inputs_from_text_free
from nesc_verifier.agent import verify

SAMPLE_CALC_TEXT = """
Residential Distribution Pole Design Summary

Pole Class: Class 5
Pole Height: 35 ft
NESC Grade: C

Total Wind Load: 1091 lb
Groundline Moment: 38588 ft-lb
Pole Capacity Utilization: 85.8%

Guy Wire Tension: 1543 lb
Required Anchor Capacity: 3086 lb
Selected Anchor Capacity: 4000 lb

Final Ground Resistance: 21 ohm
"""


def test_free_parser_extracts_reference_project_and_passes():
    inputs = extract_inputs_from_text_free(SAMPLE_CALC_TEXT)
    assert inputs.pole_height_ft == 35
    assert inputs.nesc_grade == "C"
    assert inputs.total_wind_load_lb == 1091
    assert inputs.final_ground_resistance_ohm == 21

    report = verify(inputs)
    assert report.overall_pass is True


def test_free_parser_raises_on_missing_required_fields():
    import pytest

    with pytest.raises(ValueError):
        extract_inputs_from_text_free("Just some random text with no labeled values.")


NARRATIVE_CALC_TEXT = (
    "Design summary for the residential distribution structure: this is a "
    "Class 5 wood pole, 35 feet tall, built to Grade C construction. The "
    "total lateral wind load came out to 1091 lbs. The bending moment at "
    "groundline is 38588 ft-lb, which loads the pole to 85.8% of rated "
    "capacity. Tension in the guy wire is 1543 lbs, requiring an anchor "
    "rated 3086 lbs -- we specified and installed a 4000 lb anchor. "
    "Measured resistance to ground was 21 ohms."
)


def test_free_parser_handles_narrative_phrasing_not_just_labels():
    """Proves the parser isn't tied to one rigid label format -- it should
    pull the same values out of a full-sentence description with filler
    words, different unit spellings, and no colon-separated labels at all."""
    inputs = extract_inputs_from_text_free(NARRATIVE_CALC_TEXT)
    assert inputs.pole_class == "Class 5"
    assert inputs.pole_height_ft == 35
    assert inputs.nesc_grade == "C"
    assert inputs.total_wind_load_lb == 1091
    assert inputs.groundline_moment_ft_lb == 38588
    assert inputs.pole_capacity_utilization_pct == 85.8
    assert inputs.guy_wire_tension_lb == 1543
    assert inputs.required_anchor_capacity_lb == 3086
    assert inputs.selected_anchor_capacity_lb == 4000
    assert inputs.final_ground_resistance_ohm == 21

    report = verify(inputs)
    assert report.overall_pass is True
