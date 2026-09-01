# Questions for the LiteratureIQ pipeline: what counts as a compound?

## Context

We are building a hand-checked **gold annotation** of one patent, CN112645853A, in
the same JSON shapes the LiteratureIQ pipeline writes, so the two can be compared
field by field. The reactions half is finished. We are now doing the compounds half.

The method is deliberate: a human-directed reader goes through the patent's
translated markdown line by line and lists every chemical it mentions, **without
looking at the pipeline's output first**. Only then do we compare. That independence
is the whole value of the exercise, so we cannot resolve these questions by peeking
at what the pipeline produced and calling it correct.

Reading the patent that way produced **38 specific named compounds** - a starting
ester, two benzoate salts, two products, an impurity, eight bases, two alcohols,
four alkoxides, seven solvents, water, methanol, hydrochloric acid, three named
herbicides and three impurities discussed in prose.

The pipeline's `compounds.json` for the same patent holds **43 records**.

The gap is not necessarily an error on either side. It could be that the pipeline
counts things we deliberately excluded, or splits one chemical across several
records, or records a mention rather than a substance. **We cannot tell which
without knowing the pipeline's own rule**, and scoring it against our assumption
instead of its contract would produce a meaningless benchmark.

Hence the questions below. We want to score the pipeline against **its own
specification**, and to adopt its conventions in the gold wherever it has one.

## How to answer

Answer from the **actual pipeline**: the A1 compounds prompt, the compound JSON
schema, and the compound records of a completed run. Not from general cheminformatics
practice, and not from what seems sensible.

For each question give:
- **yes / no**
- **the rule** that says so - quote it, with the file and line
- **one real example** from a completed run

Where the pipeline has **no rule** and the behaviour is simply whatever the model
did that time, say so plainly. That is the most useful answer of all, because it
tells us the difference is a gap in the spec rather than a defect in either output.

## The questions

**1. Generic classes.** A patent often says only "a basic substance", "an alcohol",
"a tertiary alcohol", "an alkali metal alkoxide", naming no specific compound. Does
A1 emit a compound record for these? If yes, what identifier does it use, and is it
marked as generic in any way?

**2. Markush / undefined R.** A named structure whose R group is never resolved, e.g.
"2-chloro-3-(alkoxymethyl)-4-(methanesulfonyl)benzoic acid". Compound record or not?
What goes in `smiles`, `formula` and `mw`?

**3. Prior art only.** A compound appearing only in the background, in a route the
patent cites and criticises, never used in any example. Recorded? Marked or flagged?

**4. Named in passing.** A real commercial compound named once for comparison and
never used - "tembotrione has higher activity than mesotrione". Recorded?

**5. Functional groups.** The patent calls something an "active group" inside a
molecule (the benzyl bromide group), not a substance in its own right. Recorded as a
compound?

**6. Qualitative impurities.** An impurity named but given no structure and no number
- "the double-attachment impurity", "dibenzyl ether type compounds". Recorded? One
record each, or skipped?

**7. Non-chemical entities.** Enzymes and proteins, e.g. HPPD
(4-hydroxyphenylpyruvate dioxygenase). In scope for `compounds.json`?

**8. Unit of a record - the most important one.** Is a compound record one per
distinct chemical for the whole patent, or one per (compound, section)? If tert-butanol
appears in twelve examples, how many records exist, and what distinguishes them?
There is a `compounds-sections.json` in the output directory, which suggests the
answer may be per-section - please confirm what each file holds.

**9. Salt and free-acid forms.** Are "the benzoate salt" (generic), "the sodium
benzoate" and "the potassium benzoate" one record or three? What decides it?

**10. Solvents and water.** Are ordinary solvents and water ordinary compound records,
or handled separately?

## What we will do with the answers

Adopt the pipeline's convention in the gold wherever it has one, so that a mismatch
in the eventual comparison means a real extraction defect and not a difference of
definition. Where the pipeline has no convention, we will decide one, write it down,
and apply it consistently across all twenty patents.
