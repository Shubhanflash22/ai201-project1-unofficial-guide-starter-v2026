# Acceptance criteria - The Unofficial Guide

Five criteria that say what "working" means for this system, written in week 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next week costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:**
<!-- e.g. "One of my questions is about a topic only two documents mention, so
     I expect that one to be hard." -->
One of my five questions (which town is built on three levels connected by
stepped lanes?) doesn't name its subject - the system has to match a
description to an entity rather than matching a proper noun, which is a
harder retrieval case than the other four. I expect that one to be the most
likely to miss, so 4 of 5 rather than 5 of 5 reflects a real difference in
difficulty across my questions, not a target I picked to be safe.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:**
<!-- Why all five and not four? What about your setup makes that achievable -
     or what would have to go wrong for it not to be? -->
This is 5 of 5 rather than 4 of 5 because source-naming isn't a retrieval
outcome - it's a formatting rule built into the generation prompt. Unlike
whether the *right* chunk gets retrieved, whether *a* source gets printed
should be deterministic and shouldn't degrade just because a question is
hard.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" -
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather -
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:**
<!-- What did your distances look like when you set the cutoff in Milestone 4?
     Was there a clean gap, or did the two groups overlap? -->
I haven't set my final cutoff yet - that happens in Milestone 4 - but my
corpus is narrow (one fictional region's town guides), so I expect
genuinely out-of-scope questions to land far outside it, with a clear gap
between in-corpus and out-of-corpus distances. 4 of 5 leaves room for one
out-of-scope question that happens to share vocabulary with something in
the corpus (e.g. asking about "trains" in a way that brushes against
`guide_regional_transport.md`) without demanding the cutoff be perfectly
tuned on the first try

---

## 4. Chunks read as complete thoughts, not fragments

At least 4 of 5 sampled chunks contain no sentence that is cut off at the
start or end. No chunk is shorter than 150 characters.

**Why this target:**
When I ran `python app.py index` with the default chunker, the shortest
chunk it produced was 24 characters - clearly a fragment left over from an
800-character cut landing mid-section, not a usable piece of information.
150 characters is short enough to allow a genuinely brief fact through but
long enough to rule out that kind of leftover fragment.

---

## 5. Cross-referenced facts cite a document that actually contains them

For questions whose answer appears in more than one document (for example,
the 1963 railway closure, mentioned in `guide_kestrelford.md`,
`guide_regional_transport.md`, and `guide_walking.md`), the source the
system names is checked against the actual chunk text and does contain the
fact, in at least 4 of 5 tries.

**Why this target:**
My corpus repeats several facts across a town-specific guide and a
cross-cutting guide (transport, walking, eating). It would be easy for the
system to retrieve a chunk that just shares vocabulary with the question
and cite it as if it supported the answer. I care about attribution being
*correct*, not just present, since criterion 2 only checks that a source
exists.
---

<!-- ─────────────────────────────────────────────────────────────────────────
     WEEK 2 - read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in week 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice - I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
