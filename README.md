# The Unofficial Guide

Shubhan Mital - Corpus: city_guides

**Stretch feature:** hybrid search (BM25 + semantic) in `store.py::search`, written up under "Second Improvement (Stretch)" below.

---

## What This Does

This system answers questions about a fictional English region's fourteen guides (town guides plus regional ones on transport, walking, and accessibility), covering things like town populations, historical dates, transport schedules, and restaurant closing times. It retrieves the most relevant section of the actual guide text for a question, then generates a short, grounded answer that names its source document. If a question falls outside what the guides cover, the relevance gate recognizes that the retrieved material isn't close enough to be useful and says "I don't have enough information about that" rather than guessing.

## Chunking Strategy

**Chunk size:** No fixed character target. Chunks are split on each document's own `## ` markdown headings, with a 900-character safety ceiling that never actually triggers in this corpus (longest real chunk is 758).

**Overlap:** 0 between sections (headings are natural boundaries, not arbitrary cuts). 100 characters, sentence-aware, reserved for the safety ceiling if a future section ever exceeds it.

When I first read the city_guides documents, every guide turned out to follow the same structure: an H1 title, then a run of `## ` sections (Getting there, Eat and drink, What to see, etc.), each one a self-contained topic. None of these sections come close to 800 characters; the largest across all 14 documents is 709. That made the default fixed-800-character chunker actively wrong for this corpus: on `python app.py index` it reported a 51-chunk run with a shortest chunk of 24 characters, which I traced to bare H1 titles with no lead-in paragraph (`# Walking in the region`, `# Eating across the region`) getting cut off as their own chunk before any real content followed.

My chunker splits on `## ` headings instead of a character count, folds any near-empty leading section into the one that follows it (eliminating the bare-title fragment), and prepends each document's title to every chunk. That last part matters because a section like "Eat and drink" never mentions its town's name inside the section text itself, so read in isolation it couldn't answer a question like "which town has X." The title makes each chunk self-contained.

Result: 94 chunks, averaging 319 characters, ranging from 183 to 758. That is smaller and more numerous than the default's 51, but each chunk maps to exactly one topic about exactly one place.

## Sample Chunks

**Chunk 1** - source: `guide_accessibility.md#0` - produced by: `chunker.py::split_documents`

```
Getting around the region with limited mobility - Overview

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** - source: `guide_corry_vale.md#5` - produced by: `chunker.py::split_documents`

```
Corry Vale - Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** - source: `guide_givens_mill.md#2` - produced by: `chunker.py::split_documents`

```
Givens Mill - Getting around

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

**Chunk 4** - source: `guide_kestrelford.md#4` - produced by: `chunker.py::split_documents`

```
Kestrelford - What to see

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

**Chunk 5** - source: `guide_pellew_sands.md#6` - produced by: `chunker.py::split_documents`

```
Pellew Sands - When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

## Sample Answer

**Question:** What year did the railway line north of Brightwater close?

**Answer:**

```
The railway line north of Brightwater closed in 1963.

Source: guide_regional_transport.md (also mentioned in guide_walking.md and guide_kestrelford.md).
```

**My relevance cutoff:** 0.66, set in `config.py`.

I ran my 5 in-corpus test questions and the 5 `OUT_OF_SCOPE` questions and recorded the best distance for each:

| Question | In corpus? | Best distance |
|---|---|---|
| How many residents does Kestrelford have? | Yes | 0.357 |
| What year did the mill in Brightwater close? | Yes | 0.353 |
| What year did the railway line north of Brightwater close? | Yes | 0.266 |
| Which town is built on three levels connected by stepped lanes? | Yes | 0.500 |
| What time do most kitchens in the region stop serving food in the evening? | Yes | 0.458 |
| What is the capital of Mongolia? | No | 0.810 |
| How do I change the oil in a diesel engine? | No | 0.881 |
| Who won the 1994 World Cup? | No | 0.969 |
| What is the recommended dosage of ibuprofen for a headache? | No | 0.835 |
| How do I write a for loop in Rust? | No | 0.861 |

The two groups separated cleanly: every in-corpus question landed at 0.500 or below, and every out-of-corpus question landed at 0.810 or above, a 0.31 gap with nothing in it. I set the cutoff at 0.66, just past the midpoint, giving roughly equal margin on both sides rather than hugging either group. Notably, my hardest question (the reverse-lookup "which town is built on three levels") was the one my criteria.md predicted would be the most likely miss. It still landed well inside the in-corpus group at 0.500, not near the boundary, which suggests my chunker's context-prefixing (adding each document's title to every chunk) is doing real work.

## Run Log - Before

Targets come from criteria.md. Criteria 3 and 4 are measured in one deterministic pass rather than three, so the same number appears in all three run columns. Gate distances and chunk lengths come from the embedder and chunker, not the generated answer, so one pass is the whole measurement.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, none under 150 chars | 4 of 5 sampled, no chunk < 150 chars | 5/5 | 5/5 | 5/5 | MET |
| 5. Cross-referenced facts cite a document that contains them | 4 of 5 | 1/1 | 1/1 | 1/1 | MET |

**Real output - criteria 1 and 2, "What year did the railway line north of Brightwater close?", run 1:**

```
The railway line north of Brightwater closed in 1963.

Source: guide_regional_transport.md (and also mentioned in guide_walking.md and guide_kestrelford.md).
```

**Real output - criterion 3, out-of-scope gate:**

```
What is the capital of Mongolia? - best distance 0.810 - refused
How do I change the oil in a diesel engine? - best distance 0.881 - refused
Who won the 1994 World Cup? - best distance 0.969 - refused
What is the recommended dosage of ibuprofen for a headache? - best distance 0.835 - refused
How do I write a for loop in Rust? - best distance 0.861 - refused
gate refused 5 of 5
```

**Real output - criterion 4, from `python app.py index`:**

```
chunked 94 chunks, 319 characters on average (shortest 183, longest 758), produced by chunker.py::split_documents
```

**Real output - criterion 5:** the one cross-referenced fact in my test set is the 1963 railway closure, which appears in three documents. All three runs cited `guide_regional_transport.md`, and I confirmed directly that this file's "The railway" section is the one containing the 1963 date, not a document that merely shares vocabulary with the question.

## Verdicts

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | All 5 questions passed all 3 runs (15/15), exceeding the 4-of-5 target with no misses at all. |
| 2 | Every answer names a source | MET | Every one of the 15 generated answers named at least one source filename, even across small wording variations between runs. |
| 3 | Gate stops out-of-corpus questions | MET | 5 of 5 refused, above the 4-of-5 target. |
| 4 | Chunks read as complete thoughts, none under 150 chars | MET | Shortest chunk across the whole corpus is 183 characters, above my 150 floor, and the 5 sampled chunks above all read as complete thoughts. |
| 5 | Cross-referenced facts cite a document that contains them | MET | The one repeated fact in my test set (1963 railway closure) was correctly attributed to a document that actually contains it, across all 3 runs. |

## Diagnoses

I missed nothing. Every criterion was met on every run, including the out-of-scope gate.

Being honest about what that means: I don't think this shows the system is excellent. I think it shows my targets were set with too much safety margin, for two concrete reasons.

**First, my questions turned out to be easier than I designed them to be.** I deliberately included one "hard" question, the reverse-lookup ("which town is built on three levels connected by stepped lanes?"), expecting it to be my most likely miss (I said so directly in criteria.md's reasoning for criterion 1). It never came close: 0.500 best distance, well inside my in-corpus group, and the model answered it correctly all three runs. My chunker's context-prefixing apparently solved this problem more completely than I expected when I wrote the criterion.

**Second, my corpus and my out-of-scope questions are too far apart.** My distance gap between in-corpus and out-of-corpus questions is 0.31 wide (0.500 to 0.810) with nothing in it. My `OUT_OF_SCOPE` questions (capital of Mongolia, diesel oil changes, Rust for-loops) are about as far outside a British town-guide corpus as a question can get. None of them is a near-miss the way a real user's off-topic-but-adjacent question might be (for example, asking about a *real* nearby city not in my fictional region, or a town-guide-shaped question about a town I don't have).

**What I'd tighten:** criterion 3. Right now it's tested against questions that are trivially far outside the corpus. A more honest test would include at least one adversarial out-of-scope question that is topically adjacent: something that uses vocabulary from my corpus (towns, transport, guides) but asks something the documents genuinely don't answer, such as "What's the population of a town not covered in this guide?" or "Which town has the cheapest hotel rooms?" (a comparison my guides don't actually make). I'd expect that kind of question to land much closer to my cutoff than 0.810, and it's the real test of whether 0.66 is doing meaningful work rather than just separating "on-topic" from "wildly off-topic."

## The Improvement

**What I changed:** Added one sentence to `GROUNDING_INSTRUCTION` in `generate.py`: "Being topically related to the question is not enough. Only answer if the specific fact the question asks for is explicitly stated in the documents. If the documents discuss the same general subject but never state the actual answer, say you don't have enough information - do not infer, estimate, or guess your way to an answer from related but incomplete information."

**Why I picked it:** My diagnosis found that my original out-of-scope test questions were too easy, since every one was wildly unrelated to the corpus (capital of Mongolia, Rust for-loops). When I tested 4 harder, topically-adjacent questions instead (population of a fictional nearby town, cheapest accommodation, Sunday shop hours, transport to London), only 1 of 4 was caught by the relevance gate itself. The other 3 slipped past my 0.66 cutoff and were only refused because of the model's own grounding instruction. This fix targets that gap directly.

I checked two other fixes before choosing this one and ruled both out with evidence:

- **Tightening the gate's cutoff can't work.** Two of my adversarial questions (0.398, 0.494) score a *lower* distance than my legitimate hardest question (0.500), so no single threshold keeps one passing while blocking the other.
- **Hybrid/keyword search wouldn't help.** I checked my actual documents: words like "cheapest" and "London" don't appear anywhere in the corpus, while "Sunday" appears in 9 documents in contexts that are topically adjacent but never state the specific regional fact asked. The failure isn't a retrieval-method problem. Generation-time reasoning is the only place that can distinguish "related content" from "the actual answer," so that's where I made the change. (I later built and measured hybrid search anyway; see Second Improvement.)

Full before/after output for these four questions is committed at `results/adversarial_before_after.md`.

## Run Log - After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, none under 150 chars | 4 of 5 sampled, no chunk < 150 chars | 5/5 | 5/5 | 5/5 | MET |
| 5. Cross-referenced facts cite a document that contains them | 4 of 5 | 1/1 | 1/1 | 1/1 | MET |

**Adversarial questions, before vs. after (same 4 questions, same distances, only the wording changed):**

| Question | Distance | Before | After |
|---|---|---|---|
| Population of Millbrook | 0.701 | Refused by gate | Refused by gate (unchanged) |
| Cheapest overnight stay | 0.551 | Generic refusal | Refusal names the specific gap: qualitative vs. comparative pricing data |
| Shops close on Sundays | 0.494 | Generic refusal | Refusal names the specific missing fact |
| Kestrelford to London | 0.398 | Generic refusal | Refused, still generic: no visible change on this one |

**Did the improvement help?** Partially, and I want to be precise about what changed. No criterion moved from MISS to MET or vice versa, since all 5 were already MET before this change. The gate-versus-generation split on the adversarial questions is also unchanged: still 1 of 4 caught by the gate, 3 of 4 caught only by generation-time refusal. What *did* change is the quality of two of those three model-generated refusals. They now name the specific reason the documents fall short (qualitative vs. comparative data; a specific unstated fact) instead of a generic "I don't have enough information." One adversarial question (Kestrelford to London) showed no visible difference in wording. I'd call this a real but modest improvement: it makes the system's refusals more legible and trustworthy to a user reading them, but it doesn't change the more fundamental limitation my diagnosis found, that the relevance gate itself, not just the prompt, is structurally unable to separate these categories by distance alone. I reviewed the before/after outputs myself rather than assuming the change had fixed the underlying classification.

## Second Improvement (Stretch)

**What I changed:** Added an opt-in hybrid search mode to `store.py::search` (`use_hybrid=True`), combining BM25 keyword scores with semantic cosine similarity via per-query min-max normalization and a 0.5/0.5 weighted blend, re-ranking all chunks in the collection rather than just the semantic top-k.

**Why I picked it:** It was on my list of options from the start, and my diagnosis had already reasoned (without empirically testing) that hybrid search likely wouldn't help my specific adversarial questions, since their key terms ("cheapest," "London") don't exist anywhere in my corpus. I wanted to measure that prediction rather than leave it as untested reasoning.

**What happened:** I ran the full test suite with `--hybrid`:

- All 5 original criteria still showed `pass`, but with drastically different (lower) distances than semantic-only search. For example, "railway line north of Brightwater" dropped from 0.266 to 0.000.
- The out-of-scope gate completely broke: **0 of 5 refused**, down from 5 of 5. "What is the capital of Mongolia?", a question with zero legitimate connection to a British town-guide corpus, scored a best distance of 0.163, comfortably inside my 0.66 cutoff.

**Diagnosis:** My hybrid implementation normalizes semantic and BM25 scores independently *per query*, using min-max normalization over that query's own candidate set. By construction, the single closest-matching chunk for *any* query, however irrelevant, gets normalized to the maximum value, 1.0. Every query therefore produces an artificially inflated "best score," regardless of whether the corpus contains anything relevant. My 0.66 cutoff was calibrated against absolute cosine distances from the original semantic-only search, so this normalization silently breaks that calibration for every query, not just adversarial ones.

**Did it help?** No, it made things significantly worse. It didn't fix my diagnosed problem (adversarial questions slipping past the gate). It broke the gate's core function entirely, turning "3 of 4 adversarial questions incorrectly pass the gate" into "0 of 5 out-of-scope questions of any kind get refused." I'm keeping this in the write-up rather than reverting silently, because the mechanism is real, understood, and instructive: hybrid search needs a normalization scheme calibrated against a fixed, global scale, not one computed independently per query, or it will always defeat a distance-based relevance gate. A corrected version would need either a pre-computed global normalization (fit once, at index time, across representative queries) or a fixed BM25 score range rather than a per-query min-max.

## What's Still Broken

Nothing failed outright: every criterion was MET before and after my changes. But my diagnosis surfaced a real structural gap that neither improvement closed. The relevance gate itself can only catch 1 of 4 topically-adjacent-but-unanswerable questions; the other 3 depend entirely on the model's own grounding discipline to refuse correctly. I ruled out two fixes for this: tightening the gate's cutoff (impossible without also blocking my legitimate hardest question, since the distances overlap: 0.398/0.494 vs. 0.500) and hybrid/keyword search (the missing words genuinely don't exist in my corpus, and my per-query implementation broke the gate besides).

What I'd do next, if I had more time: build a genuine second-stage check that is independent of the same embedding model that failed to separate these cases. For example, after retrieval, explicitly ask the model a yes/no question ("Does this specific chunk state [X]?") before letting it generate a full answer, rather than folding that judgment into one generation call that both checks relevance and writes the answer. Right now one call is doing two jobs, and I only have anecdotal confidence (3 of 3 adversarial cases, this run) that it consistently does both well. I stopped here because the scope of this project was one measured improvement, not a pipeline redesign, and the current two-layer defense (gate + prompt) never actually failed in my testing. It's a theoretical gap I found by stress-testing, not an observed failure.

## What I'd Do Differently

I'd rewrite criterion 3. As originally written ("the relevance gate stops it... in at least 4 of 5 tries"), it names the gate specifically, but my testing showed the gate isn't the layer doing most of the real work on hard cases; the grounding prompt is. A more honest criterion would test the *system's* end-to-end refusal behavior regardless of which layer catches it, for example: "For at least 4 of 5 out-of-scope questions, including at least one topically-adjacent question, the system's final answer indicates insufficient information rather than guessing." That version would have caught the real finding from day one, that my original 5 out-of-scope questions were too easy to meaningfully test the gate, instead of me discovering it later by hand.

I'd also write criterion 1 with an explicit adversarial case from the start, the way I already did with the reverse-lookup question. That one predicted correctly where my system would struggle; my out-of-scope set didn't get the same treatment, and that gap is exactly what the stress-testing surfaced.

## How I Used AI

**1. Acceptance criteria.** I developed the acceptance criteria based on my own analysis and observations, including the terminal output showing the 24-character chunk fragment and the 1963 railway closure appearing in three documents. Claude helped me refine the wording and check the "why this target" reasoning for the five criteria. I reviewed all of them myself against the assignment requirements and made the final decisions on what to keep.

**2. Chunker implementation.** I performed the analysis of the per-section character counts across all 14 documents and determined the chunking approach. Claude helped me implement my design through `_split_into_sections`, `_merge_short_leading_section`, and `_split_oversized` in `chunker.py`. I reviewed the implementation and caught the confusing `CHUNK_OVERLAP` naming conflict with `config.py`, then had it renamed to `OVERSIZE_OVERLAP` before using the code.

**3. Stress-testing the out-of-scope gate.** After my first evaluation run came back with zero misses, I used Claude to figure out how to stress-test criterion 3 rather than just accept the pass. It suggested a set of adversarial out-of-scope questions that were topically adjacent to my corpus (a fictional nearby town, comparative pricing, regional hours, and a real town name with an unanswerable route question) rather than the wildly unrelated questions in my original `OUT_OF_SCOPE` list. I ran those myself and got the real distances.

Based on those results, Claude proposed three possible fixes: lowering the gate's cutoff, adding keyword/hybrid search, or tightening the grounding prompt. I evaluated each against my system's actual behavior. The cutoff change was ruled out by the measured distances: the distributions for legitimate and adversarial questions overlap, so lowering the threshold would also block legitimate questions. I built the hybrid search mode and measured it, and it broke the gate rather than helping (see Second Improvement). The grounding-prompt change produced the most useful improvement, making the model's refusals more specific and better grounded in what the corpus actually contains. I reviewed the before/after outputs myself and concluded that the main gain was in the quality and specificity of the refusals, not a full change from wrong to right on every adversarial example, and I documented that distinction above.

Overall, I used Claude primarily as an assistant for drafting and translating my analysis and design into code. The corpus analysis, observations, implementation requirements, review, debugging, and final decisions were my own.
