"""Structured data models for calculation inputs and verification reports."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PoleLoadingInputs(BaseModel):
    """Inputs describing a single overhead distribution pole design."""

    pole_class: str = Field(description="e.g. 'Class 5'")
    pole_height_ft: float
    nesc_grade: str = Field(description="NESC construction grade, e.g. 'C'")
    total_wind_load_lb: float
    groundline_moment_ft_lb: float
    pole_capacity_utilization_pct: float = Field(
        description="Groundline moment as a percentage of rated pole capacity."
    )
    guy_wire_tension_lb: float | None = None
    required_anchor_capacity_lb: float | None = None
    selected_anchor_capacity_lb: float | None = None
    final_ground_resistance_ohm: float | None = None


class RuleResult(BaseModel):
    rule_id: str
    description: str
    passed: bool
    detail: str


class VerificationReport(BaseModel):
    """Structured output returned by the agent for a single calc package."""

    inputs: PoleLoadingInputs
    rule_results: list[RuleResult]
    overall_pass: bool
    summary: str
