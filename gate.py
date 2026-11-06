"""
The relevance gate.

This runs *before* the model does. It looks at how close the best retrieved
chunk actually is, and if nothing came back close enough it refuses the
question outright.

Why this is its own step, rather than just asking the model to admit when it
doesn't know: asking alone sometimes fails, and the model writes something
confident and wrong. Those answers are much harder to catch than obvious
errors. Deciding in code when there is nothing worth answering from is more
reliable.

The polite instruction is still in generate.py, as a second layer. The gate
catches the clear misses; the prompt catches the near ones.
"""

from dataclasses import dataclass

import config
from store import Result

REFUSAL = "I don't have enough information about that."


@dataclass
class GateDecision:
    passed: bool
    best_distance: float
    threshold: float

    @property
    def explanation(self) -> str:
        if self.passed:
            return (
                f"best distance {self.best_distance:.3f} "
                f"is under the {self.threshold} cutoff"
            )
        return (
            f"best distance {self.best_distance:.3f} "
            f"is over the {self.threshold} cutoff — refusing"
        )


def check(results: list[Result], threshold: float | None = None) -> GateDecision:
    """
    Decide whether the retrieved chunks are close enough to answer from.

        Lower distance is better. A question passes when its best chunk is
        *under* the threshold.
    """
    threshold = config.THRESHOLD if threshold is None else threshold

    if not results:
        return GateDecision(passed=False, best_distance=1.0, threshold=threshold)

    best = min(r.distance for r in results)
    return GateDecision(passed=best < threshold, best_distance=best, threshold=threshold)
