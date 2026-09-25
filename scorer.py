"""
scorer.py — decides whether an answer counts as correct.

Used automatically by run_eval.py: judge(question, expects, answer, results) -> bool

This checks whether the `expects` phrase from questions.py shows up in the
answer text, case-insensitively, and tolerant of a couple of common
formatting differences (comma-separated numbers, stray whitespace).

What this catches correctly:
  - the model produced the right number/name somewhere in its answer
  - the model refused ("I don't have enough information...") when it
    should have answered — that correctly counts as a miss, since the
    refusal text won't contain the expects phrase

What this does NOT do:
  - any deeper fact-checking. If the model said "12,000" but attributed it
    to the wrong town, this would still mark it correct, because it's only
    checking whether the expected string appears somewhere in the answer.
    That's a real limitation worth naming in your diagnosis if it comes up,
    not something to silently patch here.
"""

import re


def _normalize(text: str) -> str:
    """Lowercase and collapse commas/whitespace so '12,000' == '12000'."""
    return re.sub(r"[,\s]+", " ", text or "").strip().lower()


def judge(question: str, expects: str, answer: str, results) -> bool:
    if not expects:
        # No expects phrase was written for this question — nothing to
        # check against, so don't claim to have judged it.
        return False

    normalized_expects = _normalize(expects)
    if not normalized_expects:
        return False

    return normalized_expects in _normalize(answer)