"""Free, deterministic text parser: pulls PoleLoadingInputs out of a plain-text
calculation summary using regex, no LLM / API key required.

This intentionally covers a wide range of common phrasings (labeled fields,
different unit spellings, full sentences with filler words in between,
alternate synonyms for the same quantity) so it handles more than one rigid
template while staying free and instant. It's still pattern-matching, not
comprehension -- a genuinely novel phrasing or an unlabeled narrative
description can still slip past it. That gap is exactly what an optional
LLM extraction layer would close later; this is the free ceiling on how
far regex can go.
"""

from __future__ import annotations

import re

from .schema import PoleLoadingInputs

# Short run of connective words/punctuation allowed between a label phrase
# and its value, so "wind load came out to 1091 lb" matches as readily as
# "wind load: 1091 lb". Bounded to avoid jumping to an unrelated number.
_GAP = r"(?:[a-zA-Z,:=\s]{0,30})?"

LB = r"(?:lb|lbs|pounds)"
FT = r"(?:ft|feet|foot|')"
FTLB = r"(?:ft[\s-]?lb|foot[\s-]?pounds?)"
OHM = r"(?:ohm|ohms|Ω)"

# Each field maps to a list of regex patterns tried in order. First match wins.
# (?:...) groups are non-capturing; the value itself is always group 1.
_FIELD_PATTERNS: dict[str, list[str]] = {
    "pole_class": [
        r"pole\s*class\s*[:=]?\s*(class\s*\d+)",
        r"\b(class\s*\d+)\b\s*(?:wood\s*)?pole",
        r"(class\s*\d+)\s*(?:wood\s*)?pole",
        r"pole\s*is\s*(?:a\s*)?(class\s*\d+)",
        r"\b(class\s*\d+)\b",
    ],
    "pole_height_ft": [
        rf"pole\s*height{_GAP}(\d+(?:\.\d+)?)\s*{FT}",
        rf"height{_GAP}(\d+(?:\.\d+)?)\s*{FT}",
        rf"(\d+(?:\.\d+)?)\s*{FT}[\s-]*(?:tall|high)",
        rf"(\d+(?:\.\d+)?)[\s-]*{FT}[\s-]*(?:class\s*\d+\s*)?(?:wood\s*)?pole",
    ],
    "nesc_grade": [
        r"nesc\s*grade\s*[:=]?\s*(?:grade\s*)?([a-c])\b",
        r"grade\s*[:=]?\s*([a-c])\s*(?:construction)?",
        r"construction\s*grade\s*[:=]?\s*([a-c])\b",
        r"grade[- ]([a-c])\s*construction",
    ],
    "total_wind_load_lb": [
        rf"total\s*wind\s*load{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"(?:lateral\s*)?wind\s*(?:force|load){_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"([\d,]+(?:\.\d+)?)\s*{LB}\s*(?:of\s*)?(?:total\s*)?(?:lateral\s*)?wind\s*(?:load|force)",
    ],
    "groundline_moment_ft_lb": [
        rf"groundline\s*moment{_GAP}([\d,]+(?:\.\d+)?)\s*{FTLB}",
        rf"(?:bending|overturning)?\s*moment(?:\s*at\s*(?:the\s*)?groundline)?{_GAP}([\d,]+(?:\.\d+)?)\s*{FTLB}",
        rf"([\d,]+(?:\.\d+)?)\s*{FTLB}\s*(?:of\s*)?(?:groundline\s*|bending\s*|overturning\s*)?moment",
    ],
    "pole_capacity_utilization_pct": [
        r"(?:pole\s*)?capacity\s*util\w*\s*[:=]?\s*([\d.]+)\s*%",
        r"([\d.]+)\s*%\s*(?:of\s*)?(?:rated\s*)?(?:pole\s*)?capacity",
        rf"(?:loads?|loaded|utilized|stressed)(?:\s*the\s*pole)?{_GAP}([\d.]+)\s*%",
        r"([\d.]+)\s*%\s*(?:utiliz\w*|load\w*)",
    ],
    "guy_wire_tension_lb": [
        rf"guy\s*(?:wire\s*)?tension{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"tension\s*in\s*(?:the\s*)?guy\s*(?:wire)?{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"guy\s*(?:wire\s*)?(?:load|force){_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
    ],
    "required_anchor_capacity_lb": [
        rf"required\s*anchor\s*capacity{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"anchor(?:\s*capacity)?\s*required{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"(?:requir\w+|needs?)(?:\s*an?)?\s*anchor(?:\s*rated)?{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
    ],
    "selected_anchor_capacity_lb": [
        rf"selected\s*anchor\s*capacity{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"anchor(?:\s*capacity)?\s*(?:used|selected|installed|chosen|specified){_GAP}([\d,]+(?:\.\d+)?)\s*{LB}",
        rf"(?:used|install\w+|specifi\w+)(?:\s*and\s*install\w+)?\s*an?{_GAP}([\d,]+(?:\.\d+)?)\s*{LB}\s*anchor",
    ],
    "final_ground_resistance_ohm": [
        rf"(?:final\s*)?ground(?:ing)?\s*resistance{_GAP}([\d.]+)\s*{OHM}",
        rf"resistance\s*to\s*ground{_GAP}([\d.]+)\s*{OHM}",
        rf"measured(?:\s*ground(?:ing)?)?\s*resistance{_GAP}([\d.]+)\s*{OHM}",
        rf"([\d.]+)\s*{OHM}\s*(?:to\s*ground|ground(?:ing)?\s*resistance)?",
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

    No API key, no network call, no cost -- works entirely offline. Tries
    several phrasings per field (labeled lines, full sentences with filler
    words, alternate synonyms/units) before giving up on that field. Raises
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
            "'Total Wind Load: 1091 lb', or a plain sentence like "
            "'the wind load was 1091 lb'."
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
