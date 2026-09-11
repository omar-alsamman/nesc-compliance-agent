"""Free, deterministic text parser: pulls PoleLoadingInputs out of a plain-text
calculation summary using regex, no LLM / API key required.

Designed to be forgiving about label wording, spacing, and units, since real
calc summaries (pasted from a spreadsheet, a report, or typed by hand) vary a
lot. Not as flexible as an LLM extractor would be, but free and instant, and
covers the common ways someone would describe these values in plain text.
"""

from __future__ import annotations

import re

from .schema import PoleLoadingInputs

# Each field maps to a list of regex patterns tried in order. First match wins.
# (?:...) groups are non-capturing; the value itself is always group 1.
_FIELD_PATTERNS: dict[str, list[str]] = {
    "pole_class": [
        r"pole\s*class\s*[:=]?\s*(class\s*\d+)",
        r"\b(class\s*\d+)\b.*pole",
    ],
    "pole_height_ft": [
        r"pole\s*height\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:ft|feet|')",
        r"(\d+(?:\.\d+)?)\s*(?:ft|feet|')\s*(?:class\s*\d+\s*)?pole",
    ],
    "nesc_grade": [
        r"nesc\s*grade\s*[:=]?\s*(?:grade\s*)?([a-c])\b",
        r"grade\s*[:=]?\s*([a-c])\s*(?:construction)?",
    ],
    "total_wind_load_lb": [
        r"total\s*wind\s*load\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*lb",
        r"wind\s*load\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*lb",
    ],
    "groundline_moment_ft_lb": [
        r"groundline\s*moment\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*ft[\s-]?lb",
        r"moment\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*ft[\s-]?lb",
    ],
    "pole_capacity_utilization_pct": [
        r"(?:pole\s*)?capacity\s*util\w*\s*[:=]?\s*([\d.]+)\s*%",
        r"([\d.]+)\s*%\s*(?:of\s*)?(?:pole\s*)?capacity",
    ],
    "guy_wire_tension_lb": [
        r"guy\s*(?:wire\s*)?tension\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*lb",
    ],
    "required_anchor_capacity_lb": [
        r"required\s*anchor\s*capacity\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*lb",
    ],
    "selected_anchor_capacity_lb": [
        r"selected\s*anchor\s*capacity\s*[:=]?\s*([\d,]+(?:\.\d+)?)\s*lb",
    ],
    "final_ground_resistance_ohm": [
        r"(?:final\s*)?ground(?:ing)?\s*resistance\s*[:=]?\s*([\d.]+)\s*(?:ohm|Ω)",
    ],
}

_REQUIRED = {
    "pole_class",
    "pole_height_ft",
    "nesc_grade",
    "total_wind_load_lb",
    "groundline_moment_ft_lb",
    "pole_capacity_utilization_pct",
}


def extract_inputs_from_text_free(raw_text: str) -> PoleLoadingInputs:
    """Parse a plain-text calc summary into PoleLoadingInputs using regex only.

    No API key, no network call, no cost -- works entirely offline. Raises
    ValueError listing any required field it could not find, so a bad/partial
    paste fails loudly instead of silently guessing.
    """
    text = raw_text.strip()
    found: dict[str, str] = {}

    for field, patterns in _FIELD_PATTERNS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found[field] = match.group(1).strip()
                break

    missing_required = _REQUIRED - found.keys()
    if missing_required:
        raise ValueError(
            "Could not find these required fields in the pasted text: "
            + ", ".join(sorted(missing_required))
            + ". Try including them as explicit labeled lines, e.g. "
            "'Total Wind Load: 1091 lb'."
        )

    def _num(key: str) -> float | None:
        value = found.get(key)
        if value is None:
            return None
        return float(value.replace(",", ""))

    return PoleLoadingInputs(
        pole_class=found["pole_class"].title().replace("  ", " "),
        pole_height_ft=_num("pole_height_ft"),
        nesc_grade=found["nesc_grade"].upper(),
        total_wind_load_lb=_num("total_wind_load_lb"),
        groundline_moment_ft_lb=_num("groundline_moment_ft_lb"),
        pole_capacity_utilization_pct=_num("pole_capacity_utilization_pct"),
        guy_wire_tension_lb=_num("guy_wire_tension_lb"),
        required_anchor_capacity_lb=_num("required_anchor_capacity_lb"),
        selected_anchor_capacity_lb=_num("selected_anchor_capacity_lb"),
        final_ground_resistance_ohm=_num("final_ground_resistance_ohm"),
    )
