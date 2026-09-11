"""LLM layer: turns a free-text calculation summary into structured
PoleLoadingInputs, runs the deterministic rule engine, and produces a
VerificationReport with human-readable reasoning.

Skeleton only -- needs ANTHROPIC_API_KEY to run. Next build step.
"""

from __future__ import annotations

import os

from .rules import run_all_checks
from .schema import PoleLoadingInputs, VerificationReport


def verify(inputs: PoleLoadingInputs) -> VerificationReport:
      """Run the deterministic checks and assemble a structured report.

          This part works today with no API key. The next step is adding an LLM
              extraction pass in front of this so a user can paste in a raw
                  calculation summary (PDF text, spreadsheet dump, etc.) instead of
                      constructing PoleLoadingInputs by hand.
                          """
      results = run_all_checks(inputs)
      overall_pass = all(r.passed for r in results)
      failed = [r for r in results if not r.passed]
      summary = (
          "All checks passed."
          if overall_pass
          else f"{len(failed)} check(s) failed: " + "; ".join(r.rule_id for r in failed)
      )
      return VerificationReport(
          inputs=inputs,
          rule_results=results,
          overall_pass=overall_pass,
          summary=summary,
      )


def extract_inputs_from_text(raw_text: str) -> PoleLoadingInputs:
      """Use an LLM to pull structured PoleLoadingInputs out of free text.

          Not yet implemented -- requires ANTHROPIC_API_KEY. Placeholder raises
              so it fails loudly instead of silently returning bad data.
                  """
      if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError(
                              "ANTHROPIC_API_KEY not set -- extract_inputs_from_text needs the "
                              "LLM layer, which isn't built yet. See README roadmap."
                )
            raise NotImplementedError("LLM extraction layer not yet built.")
