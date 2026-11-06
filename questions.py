"""
Test questions.

`QUESTIONS` holds questions the system should be able to answer from the
corpus, specific enough to have a right answer. `expects` is a word or short
phrase a correct answer should contain; `scorer.py` checks for it.

`OUT_OF_SCOPE` holds five questions the documents clearly don't cover. The
relevance gate should refuse all five. `run_eval.py` runs them through the gate
and records what happened, which is the evidence for criterion 3. There are
five because criterion 3 names a target of 4 of 5.
"""

QUESTIONS = [
    {"question": "How many residents does Kestrelford have?", "expects": "12,000"},
    {"question": "What year did the mill in Brightwater close?", "expects": "1974"},
    {"question": "What year did the railway line north of Brightwater close?", "expects": "1963"},
    {"question": "Which town is built on three levels connected by stepped lanes?", "expects": "Halden Bay"},
    {"question": "What time do most kitchens in the region stop serving food in the evening?", "expects": "9pm"},
]

# Questions from a different world entirely. The gate should refuse all five.
# They cost no model calls: a refusal never reaches the model.
OUT_OF_SCOPE = [
    "What is the capital of Mongolia?",
    "How do I change the oil in a diesel engine?",
    "Who won the 1994 World Cup?",
    "What is the recommended dosage of ibuprofen for a headache?",
    "How do I write a for loop in Rust?",
]


def answered() -> list[dict]:
    """The questions that have been filled in."""
    return [q for q in QUESTIONS if q.get("question", "").strip()]
