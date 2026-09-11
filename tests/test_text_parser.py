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
