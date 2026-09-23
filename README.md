[![Tests](https://github.com/omar-alsamman/nesc-compliance-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/omar-alsamman/nesc-compliance-agent/actions/workflows/tests.yml)

# NESC Compliance & Calculation Verification Agent

An AI agent that reviews electric distribution engineering calculations — pole
loading, guying, grounding, sag-and-tension — against NESC (National
Electrical Safety Code) requirements and flags discrepancies, the way a
senior utility engineer reviews a junior engineer's design package before
it's released for construction.

## Why this project

This sits at the intersection of two real, non-generic skill sets: hands-on
electric distribution design experience (pole loading, guying/grounding
analysis, NESC Grade C construction — see
[Residential Distribution Pole Design](https://drive.google.com/file/d/1UbCusSvVxF3nWbjKZy5suWxR1xAtEST5/view))
and AI response evaluation (rubric-based rating, calculation reconciliation,
spec verification — current work on the Handshake AI Fellowship / Project
Hedgehog). Instead of a generic LLM-wrapper demo, this is a domain expert
building the tool they'd actually want on the job.

## Architecture

```
nesc_verifier/
  rules.py      # Deterministic NESC rule checks (hard limits: ground
                 # resistance ≤ 25 Ω, pole capacity ≤ 100%, clearance
                 # minimums, etc.) — no LLM involved, these are pass/fail
                 # engineering facts.
  schema.py      # Pydantic models for calculation inputs and the
                 # structured verification report the agent returns.
  agent.py       # LLM layer: takes a free-text or structured calculation
                 # summary, extracts the relevant values, runs them through
                 # rules.py, and produces a structured pass/fail report with
                 # cited reasoning — mirrors how a human reviewer explains a
                 # rejection.
data/
  nesc_reference.md   # Condensed NESC rule text used for retrieval/citation.
tests/
  test_pole_design.py # Ground-truth regression test using Omar's own
                       # Residential Distribution Pole Design numbers
                       # (1,091 lb wind load, 38,588 ft-lb groundline moment,
                       # 85.8% pole capacity, 21 Ω final ground resistance —
                       # all PASS) as a known-correct fixture.
```

## Status

`rules.py` and `schema.py`: implemented, deterministic, no API key required.
`agent.py`: skeleton in place — needs an `ANTHROPIC_API_KEY` to run the LLM
extraction/reasoning layer. **Free alternative available now:** `nesc_verifier/text_parser.py` uses regex (no API key, no cost) to pull structured inputs out of a plain-text calc summary -- covers common labeled formats out of the box.

## Roadmap

- [x] Deterministic rule engine (grounding, structural capacity)
- [x] Ground-truth regression test against a real completed project
- [x] Free-text extraction layer (regex-based, no API key) -- `text_parser.py`
- [ ] LLM extraction layer (free-text calc summary → structured values, handles messier input than regex)
- [ ] Retrieval over full NESC rule text (currently a condensed excerpt)
- [ ] CLI / simple web front-end for pasting in a calculation package
- [ ] Eval harness: run against a small set of intentionally-flawed
      calculation packages to measure catch rate

## Setup

```bash
pip install -r requirements.txt
pytest                      # runs the deterministic rule tests — no API key needed
export ANTHROPIC_API_KEY=... # required only for agent.py's LLM layer
```


## Conversational agent mode (`agent.py`)

The browser demo and `text_parser.py`/`rules.py` run fixed, deterministic checks with no LLM and no API key. `agent.py` adds a second, separate mode: a conversational agent that wraps those same checks as tools an LLM can call, so you can ask about a design in plain language instead of pasting a full summary.

The LLM never states a pass/fail or a numeric limit on its own. It calls `check_grounding`, `check_pole_capacity`, or `check_guy_anchor` and answers only from what the tool returns, citing the rule ID.

### Run it

```
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
python agent.py
```

### Example

```
> My final ground resistance came out to 32 ohms and pole capacity is at 91%, am I compliant?
Grounding fails NESC-092: 32 ohm exceeds the 25 ohm limit.
Pole capacity passes STRUCT-CAP: 91% is within rated capacity.
```

This requires your own Anthropic API key and runs locally, unlike the no-key browser demo above.
