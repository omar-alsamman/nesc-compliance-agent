"""
NESC Compliance Agent - conversational mode

Wraps the same deterministic rule checks used by the regex parser and
browser demo (text_parser.py / rules.py) as tools an LLM can call, so a
user can ask natural-language questions about a pole design and get
grounded answers that cite the exact rule and number that fired.

This is the agentic layer on top of the existing rule engine: the LLM
never invents a pass/fail on its own, it always calls check_grounding,
check_pole_capacity, or check_guy_anchor and reports what those return.

Usage:
    export ANTHROPIC_API_KEY=sk-...
    python agent.py

Requires: pip install anthropic
"""

import json
import os
import sys

import anthropic

MAX_GROUND_RESISTANCE_OHM = 25.0
MAX_POLE_CAPACITY_PCT = 100.0


# ---------------------------------------------------------------------------
# The same three deterministic checks used by rules.py / the browser demo.
# These are the "ground truth" the agent is not allowed to guess around.
# ---------------------------------------------------------------------------

def check_grounding(final_ground_resistance_ohm: float) -> dict:
    """NESC-092: grounding system resistance must not exceed 25 ohm."""
    passed = final_ground_resistance_ohm <= MAX_GROUND_RESISTANCE_OHM
    return {
        "rule_id": "NESC-092",
        "description": "Grounding system resistance must not exceed 25 ohm (NESC Rule 092).",
        "passed": passed,
        "value_ohm": final_ground_resistance_ohm,
        "limit_ohm": MAX_GROUND_RESISTANCE_OHM,
        "detail": (
            f"Final ground resistance = {final_ground_resistance_ohm} ohm "
            f"({'within' if passed else 'exceeds'} the 25 ohm limit)."
        ),
    }


def check_pole_capacity(pole_capacity_utilization_pct: float) -> dict:
    """STRUCT-CAP: groundline moment must not exceed rated pole capacity."""
    passed = pole_capacity_utilization_pct <= MAX_POLE_CAPACITY_PCT
    return {
        "rule_id": "STRUCT-CAP",
        "description": "Groundline moment must not exceed rated pole capacity (100%).",
        "passed": passed,
        "value_pct": pole_capacity_utilization_pct,
        "limit_pct": MAX_POLE_CAPACITY_PCT,
        "detail": (
            f"Pole capacity utilization = {pole_capacity_utilization_pct}% "
            f"({'within' if passed else 'exceeds'} rated capacity)."
        ),
    }


def check_guy_anchor(required_anchor_capacity_lb: float, selected_anchor_capacity_lb: float) -> dict:
    """GUY-ANCHOR: selected anchor capacity must meet or exceed required (NESC 261H)."""
    passed = selected_anchor_capacity_lb >= required_anchor_capacity_lb
    return {
        "rule_id": "GUY-ANCHOR",
        "description": "Selected anchor capacity must meet or exceed the required anchor capacity (NESC Rule 261H).",
        "passed": passed,
        "required_lb": required_anchor_capacity_lb,
        "selected_lb": selected_anchor_capacity_lb,
        "detail": (
            f"Required = {required_anchor_capacity_lb} lb, selected = {selected_anchor_capacity_lb} lb "
            f"({'meets' if passed else 'does not meet'} requirement)."
        ),
    }


TOOLS = [
    {
        "name": "check_grounding",
        "description": "Check the final ground resistance of a pole design against the NESC 25 ohm limit (Rule 092).",
        "input_schema": {
            "type": "object",
            "properties": {
                "final_ground_resistance_ohm": {"type": "number", "description": "Measured/calculated final ground resistance in ohms."},
            },
            "required": ["final_ground_resistance_ohm"],
        },
    },
    {
        "name": "check_pole_capacity",
        "description": "Check whether the pole's structural capacity utilization is within its rated 100% capacity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pole_capacity_utilization_pct": {"type": "number", "description": "Pole capacity utilization as a percent, e.g. 85.8."},
            },
            "required": ["pole_capacity_utilization_pct"],
        },
    },
    {
        "name": "check_guy_anchor",
        "description": "Check whether the selected guy anchor capacity meets the required anchor capacity (NESC Rule 261H).",
        "input_schema": {
            "type": "object",
            "properties": {
                "required_anchor_capacity_lb": {"type": "number", "description": "Required anchor holding capacity in pounds."},
                "selected_anchor_capacity_lb": {"type": "number", "description": "Selected/installed anchor capacity in pounds."},
            },
            "required": ["required_anchor_capacity_lb", "selected_anchor_capacity_lb"],
        },
    },
]

TOOL_FUNCTIONS = {
    "check_grounding": lambda i: check_grounding(i["final_ground_resistance_ohm"]),
    "check_pole_capacity": lambda i: check_pole_capacity(i["pole_capacity_utilization_pct"]),
    "check_guy_anchor": lambda i: check_guy_anchor(i["required_anchor_capacity_lb"], i["selected_anchor_capacity_lb"]),
}

SYSTEM_PROMPT = """You are the NESC Compliance Agent, a conversational layer over a deterministic
pole-design rule engine (github.com/omar-alsamman/nesc-compliance-agent).

Rules:
- Never state a pass/fail result, a limit, or a numeric threshold from memory.
  Always call the matching tool (check_grounding, check_pole_capacity,
  check_guy_anchor) and base your answer only on what it returns.
- If the user gives a design's numbers, run every check that applies to the
  numbers they gave.
- Always cite the rule_id (e.g. NESC-092) in your answer.
- If a required number is missing, ask for it instead of guessing.
- Keep answers short and direct.
"""


def run_conversation(client: "anthropic.Anthropic", user_message: str, history: list) -> str:
    history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            func = TOOL_FUNCTIONS.get(block.name)
            result = func(block.input) if func else {"error": f"unknown tool {block.name}"}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result),
            })

        history.append({"role": "user", "content": tool_results})


def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("Set ANTHROPIC_API_KEY first: export ANTHROPIC_API_KEY=sk-...")
        sys.exit(1)

    client = anthropic.Anthropic()
    history = []

    print("NESC Compliance Agent (conversational mode). Ctrl+C to exit.")
    print("Example: \"My final ground resistance came out to 32 ohms and pole capacity is at 91%, am I compliant?\"\n")

    while True:
        try:
            user_message = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not user_message.strip():
            continue
        answer = run_conversation(client, user_message, history)
        print(answer + "\n")


if __name__ == "__main__":
    main()
