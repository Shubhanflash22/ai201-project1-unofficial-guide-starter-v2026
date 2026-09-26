# The Unofficial Guide

<!-- Replace this line with your name and which corpus you picked. -->
Shubhan Mital - Corpus: city_guides

---

# Week 1

## What This Does

<!-- Three or four sentences. Which corpus you picked, and the kinds of
     questions your system answers. Write it for someone who has never seen
     this repo.

     Milestone 5. -->
     This system answers questions about a fictional English region's fourteen town guides - things like town populations, historical dates, transport schedules, and restaurant closing times. It retrieves the most relevant section of the actual guide text for a question, then generates a short, grounded answer that names its source document. If a question falls outside what the guides cover, the relevance gate recognizes that the retrieved material isn't close enough to be useful and says "I don't have enough information about that" rather than guessing.


## Chunking Strategy

<!-- What about YOUR documents made you pick these numbers? Short posts and
     long sectioned guides don't want the same chunking, and "800 seemed
     reasonable" earns nothing. Point at something you noticed when you read
     the documents in Milestone 1.

     If you changed your mind partway through, say so and say why. That's worth
     more than pretending you got it right first time.

     Milestone 3. -->
**Chunk size:** No fixed character target - chunks are split on each document's own `## ` markdown headings, with a 900-character safety ceiling that never actually triggers in this corpus (longest real chunk is 758).

**Overlap:** 0 between sections (headings are natural boundaries, not arbitrary cuts). 100 characters, sentence-aware, reserved for the safety ceiling if a future section ever exceeds it.

When I read the city_guides documents in Milestone 1, every town guide turned out to follow the same structure: an H1 title, then a run of `## ` sections (Getting there, Eat and drink, What to see, etc.), each one a self-contained topic. None of these sections come close to 800 characters - the largest across all 14 documents is 709. That made the default fixed-800-character chunker actively wrong for this corpus: on `python app.py index` it reported a 51-chunk run with a shortest chunk of 24 characters, which I traced to bare H1 titles with no lead-in paragraph (`# Walking in the region`, `# Eating across the region`) getting cut off as their own chunk before any real content followed.

My chunker splits on `## ` headings instead of a character count, folds any near-empty leading section into the one that follows it (eliminating the bare-title fragment), and prepends each document's title to every chunk. That last part matters because a section like "Eat and drink" never mentions its town's name inside the section text itself - read in isolation it couldn't answer a question like "which town has X," so the title makes each chunk self-contained.

Result: 94 chunks, averaging 319 characters, ranging from 183 to 758 - smaller and more numerous than the default's 51, but each one maps to exactly one topic about exactly one place.

## Sample Chunks

<!-- Five chunks, pasted as text. Label each one and name the file it came from
     AND the function that produced it - the grader checks your code against
     what you claim here.

     `python app.py chunks -n 5` prints all three for you. Copy them straight
     across.

     Milestone 3. -->
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

<!-- One complete question and answer, pasted as text, with the source line
     visible. Milestone 4. -->

**Question:** What year did the railway line north of Brightwater close?

**Answer:**

```
The railway line north of Brightwater closed in 1963.

Source: guide_regional_transport.md (also mentioned in guide_walking.md and guide_kestrelford.md).
```

**My relevance cutoff:** 0.66, set in `config.py`.

<!-- The number you set in config.py, and how you got there.

     You ran five questions your corpus covers and the five in OUT_OF_SCOPE
     that it clearly doesn't, and wrote down the best distance for each. What
     did those two groups look like? Where was the gap? Put the actual numbers
     here - the table below wants all ten rows.

     Milestone 4. -->
     I ran my 5 test questions and the 5 `OUT_OF_SCOPE` questions and recorded the best distance for each:

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

The two groups separated cleanly: every in-corpus question landed at 0.500 or below, every out-of-corpus question landed at 0.810 or above - a 0.31 gap with nothing in it. I set the cutoff at 0.66, just past the midpoint, giving roughly equal margin on both sides rather than hugging either group. Notably, my hardest question (the reverse-lookup "which town is built on three levels" - the one my criteria.md predicted would be the most likely miss) still landed well inside the in-corpus group at 0.500, not near the boundary, which suggests my chunker's context-prefixing (adding each document's title to every chunk) is doing real work.

## How I Used AI

<!-- Two specific moments. For each: what you asked for, what came back, and
     what you changed about it.

     "I asked Claude to write the chunking function from my notes. It ignored
     the overlap, so I added that myself" is the level of detail we're after.
     "I used AI to help me code" is not.

     Milestone 5. -->

**1. Milestone 2:** I developed the acceptance criteria based on my own analysis and observations, including the terminal output showing the 24-character chunk fragment and the 1963 railway closure appearing in three documents. Claude assisted me in refining the wording and writing and the correctness of the “why this target” reasoning for the five criteria. I reviewed all of them myself against the assignment requirements and made the final decisions on what to keep.

**2. Milestone 3:** I performed the analysis of the per-section character counts across all 14 documents and determined the chunking approach. Claude assisted me in implementing my design through `_split_into_sections`, `_merge_short_leading_section`, and `_split_oversized` in `chunker.py`. I reviewed the implementation and caught the confusing `CHUNK_OVERLAP` naming conflict with `config.py`, then had it renamed to `OVERSIZE_OVERLAP` before using the code.

Overall, I used Claude primarily as an assistant for drafting and translating my analysis/design into code. The corpus analysis, observations, implementation requirements, review, debugging, and final decisions were my own.


<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Week 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     week 1 - the point is that someone can see what you said before you knew
     how it went. -->
## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->


| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, none under 150 chars | 4 of 5 sampled, no chunk < 150 chars | — | — | — | MET |
| 5. Cross-referenced facts cite a document that contains them | 4 of 5 | — | — | — | MET |

Criteria 4 and 5 don't vary between runs, for the same reason criterion 3 doesn't: chunk length and source citation are properties of the chunker and retrieval, not the generated answer, so one pass is the whole measurement — measured once rather than three times.

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs - the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

**Real output — criterion 1 and 2, "What year did the railway line north of Brightwater close?", run 1:**

The railway line north of Brightwater closed in 1963.

Source: guide_regional_transport.md (and also mentioned in guide_walking.md and guide_kestrelford.md).


**Real output — criterion 3, out-of-scope gate:**

What is the capital of Mongolia? — best distance 0.810 — refused
How do I change the oil in a diesel engine? — best distance 0.881 — refused
Who won the 1994 World Cup? — best distance 0.969 — refused
What is the recommended dosage of ibuprofen for a headache? — best distance 0.835 — refused
How do I write a for loop in Rust? — best distance 0.861 — refused
gate refused 5 of 5


**Real output — criterion 4, from `python app.py index`:**

chunked 94 chunks, 319 characters on average (shortest 183, longest 758), produced by chunker.py::split_documents


**Real output — criterion 5**, the one cross-referenced fact in my test set (the 1963 railway closure, which appears in three documents): all three runs cited `guide_regional_transport.md`, and I confirmed directly that this file's "The railway" section is the one containing the 1963 date — not a document that merely shares vocabulary with the question.

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     week - not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 | Retrieved chunk contains the answer | MET | All 5 questions passed all 3 runs (15/15), exceeding the 4-of-5 target with no misses at all. |
| 2 | Every answer names a source | MET | Every one of the 15 generated answers named at least one source filename — this held even across small wording variations between runs. |
| 3 | Gate stops out-of-corpus questions | MET | 5 of 5 refused, at the target. |
| 4 | Chunks read as complete thoughts, none under 150 chars | MET | Shortest chunk across the whole corpus is 183 characters — above my 150 floor — and the 5 chunks I sampled in Milestone 3 all read as complete thoughts. |
| 5 | Cross-referenced facts cite a document that contains them | MET | The one repeated fact in my test set (1963 railway closure) was correctly attributed to a document that actually contains it, across all 3 runs. |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough - you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

I missed nothing. Every criterion was met on every run, including the out-of-scope gate.

Being honest about what that means: I don't think this shows the system is excellent — I think it shows my targets were set with too much safety margin, for two concrete reasons.

**First, my questions turned out to be easier than I designed them to be.** I deliberately included one "hard" question — the reverse-lookup ("which town is built on three levels connected by stepped lanes?") — expecting it to be my most likely miss (I said so directly in criteria.md's reasoning for criterion 1). It never came close: 0.500 best distance, well inside my in-corpus group, and the model answered it correctly all three runs. My chunker's context-prefixing (adding each document's title to every chunk) apparently solved this problem more completely than I expected when I wrote the criterion.

**Second, my corpus and my out-of-scope questions are too far apart.** My distance gap between in-corpus and out-of-corpus questions is 0.31 wide (0.500 to 0.810) with nothing in it. My `OUT_OF_SCOPE` questions (capital of Mongolia, diesel oil changes, Rust for-loops) are about as far outside a British town-guide corpus as a question can get — none of them are a near-miss the way a real user's off-topic-but-adjacent question might be (e.g. asking about a *real* nearby city not in my fictional region, or a town-guide-shaped question about a town I don't have).

**What I'd tighten:** criterion 3. Right now it's tested against questions that are trivially far outside the corpus. A more honest test would include at least one adversarial out-of-scope question that's topically adjacent — something that uses vocabulary from my corpus (towns, transport, guides) but asks something the documents genuinely don't answer, e.g. "What's the population of a town not covered in this guide?" or "Which town has the cheapest hotel rooms?" (a comparison my guides don't actually make). I'd expect that kind of question to land much closer to my cutoff than 0.810, and it's the real test of whether 0.66 is doing meaningful work rather than just separating "on-topic" from "wildly off-topic."


## The Improvement

**What I changed:** Added one sentence to `GROUNDING_INSTRUCTION` in `generate.py`: "Being topically related to the question is not enough. Only answer if the specific fact the question asks for is explicitly stated in the documents. If the documents discuss the same general subject but never state the actual answer, say you don't have enough information — do not infer, estimate, or guess your way to an answer from related but incomplete information."

**Why I picked it:** My Milestone 3 diagnosis found that my original out-of-scope test questions were too easy — every one was wildly unrelated to the corpus (capital of Mongolia, Rust for-loops). When I tested 4 harder, topically-adjacent questions instead (population of a fictional nearby town, cheapest accommodation, Sunday shop hours, transport to London), only 1 of 4 was caught by the relevance gate itself; the other 3 slipped past my 0.66 cutoff and were only refused because of the model's own grounding instruction.

I checked two other fixes before choosing this one and ruled both out with evidence: tightening the gate's cutoff can't work, because two of my adversarial questions (0.398, 0.494) score a *lower* distance than my legitimate hardest question (0.500) — there's no single threshold that keeps one passing while blocking the other. Hybrid/keyword search also wouldn't help — I checked my actual documents, and words like "cheapest" and "London" don't appear anywhere in the corpus, while "Sunday" appears in 9 documents in contexts that are genuinely topically adjacent but never state the specific regional fact asked. The failure isn't a retrieval-method problem; it's that generation-time reasoning is the only place that can distinguish "related content" from "the actual answer," so that's where I made the change.

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log - After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 2. Every answer names a source | 5 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks read as complete thoughts, none under 150 chars | 4 of 5 sampled, no chunk < 150 chars | — | — | — | MET |
| 5. Cross-referenced facts cite a document that contains them | 4 of 5 | — | — | — | MET |

**Adversarial questions, before vs. after (same 4 questions, same distances — only the wording changed):**

| Question | Distance | Before | After |
|---|---|---|---|
| Population of Millbrook | 0.701 | Refused by gate | Refused by gate (unchanged) |
| Cheapest overnight stay | 0.551 | Generic refusal | Refusal names the specific gap: qualitative vs. comparative pricing data |
| Shops close on Sundays | 0.494 | Generic refusal | Refusal names the specific missing fact |
| Kestrelford to London | 0.398 | Generic refusal | Refused, still generic — no visible change on this one |

**Did it help?** Partially, and I want to be precise about what changed. No criterion moved from MISS to MET or vice versa — all 5 were already MET before this change, and the underlying gate-versus-generation split on the adversarial questions is unchanged: still 1 of 4 caught by the gate, 3 of 4 caught only by generation-time refusal. What *did* change is the quality of two of those three model-generated refusals — they now name the specific reason the documents fall short (qualitative vs. comparative data; a specific unstated fact) instead of a generic "I don't have enough information." One adversarial question (Kestrelford to London) showed no visible difference in wording. I'd call this a real but modest improvement: it makes the system's refusals more legible and trustworthy to a user reading them, but it doesn't change the more fundamental limitation my diagnosis found — that the relevance gate itself, not just the prompt, is structurally unable to separate these categories by distance alone.

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that - a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->
     

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now - which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
