# Adversarial out-of-scope questions - manual verification

These four questions were designed to stress-test criterion 3 more rigorously
than the original `OUT_OF_SCOPE` set: topically adjacent to city_guides rather
than wildly unrelated. Run by hand via `python app.py ask "..."` (the same
`search` -> `gate.check` -> `answer_from_chunks` path `run_eval.py` uses), before
and after the Milestone 4 grounding-prompt change, with no other change in
between.

- Produced by: manual runs, `app.py::ask`, same functions `run_eval.py` calls
- Corpus: `city_guides` (index variant `default`)
- Relevance cutoff: 0.66 (unchanged across both runs)

## Before (original GROUNDING_INSTRUCTION)

### What's the population of Millbrook? - best distance 0.701 (refused by gate)

I don't have enough information about that.


### Which town has the cheapest overnight stay? - best distance 0.551 (passed gate)

- Sources retrieved: guide_brightwater.md, guide_givens_mill.md, guide_halden_bay.md, guide_marchwood.md

Based on the provided documents, I do not have enough information to determine which specific town has the cheapest overnight stay.


### What time do shops close on Sundays? - best distance 0.494 (passed gate)

- Sources retrieved: guide_brightwater.md, guide_eating.md, guide_givens_mill.md, guide_kestrelford.md

I do not have enough information to answer what time shops close on Sundays.


### How do I get from Kestrelford to London? - best distance 0.398 (passed gate)

- Sources retrieved: guide_kestrelford.md

I do not have enough information to answer how to get from Kestrelford to London (guide_kestrelford.md).


## After (tightened GROUNDING_INSTRUCTION)

### What's the population of Millbrook? - best distance 0.701 (refused by gate, unchanged)

I don't have enough information about that.


### Which town has the cheapest overnight stay? - best distance 0.551 (passed gate)

- Sources retrieved: guide_brightwater.md, guide_givens_mill.md, guide_halden_bay.md, guide_marchwood.md

I don't have enough information to answer which town has the cheapest overnight stay, as the documents provide qualitative descriptions of pricing ("cheap", "better value", "priced accordingly", "prices roughly halve") rather than comparative cost data.


### What time do shops close on Sundays? - best distance 0.494 (passed gate)

- Sources retrieved: guide_brightwater.md, guide_eating.md, guide_givens_mill.md, guide_kestrelford.md

I do not have enough information to answer your question, as the documents do not state what time shops close on Sundays.


### How do I get from Kestrelford to London? - best distance 0.398 (passed gate)

- Sources retrieved: guide_kestrelford.md

I do not have enough information to answer your question.