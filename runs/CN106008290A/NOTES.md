# CN106008290A run notes

A method for preparing tembotrione. Anhui Jiuyi Agriculture Co., Ltd., filed
2016-05-16, published 2016-10-12, still pending. Seven scanned pages, zero
characters of text layer on all seven, so every readable character in this run
came from the vision pass.

## Status as of 2026-08-28: blocked on the census budget (superseded, see the 2026-08-30 sections)

`selfcheck` reports **35 pass, 1 warn, 2 fail**. The two failures are the same
measurement counted twice: the reviewer census is 131 claims, 19.0 minutes at the
pinned P90 rate, against a pinned 15 minute budget that allows 103.

I did not change the budget. It is a pinned number and rule 4 forbids moving it to
make a check pass.

### What the overrun actually is

It is the last paragraph of `pipeline/contracts/ONE-ROUTE-TOLD-FOUR-TIMES.md`, which
asks

> whether the queue should present the four tellings of a step together, since a
> reviewer checking step 3 four times in four places spends four times the budget of
> a reviewer checking it once with three corroborations shown alongside. Not
> measured, and not filed as a defect.

This patent measures it. It tells one two-step route **five** times, as Examples 1 to
5, which differ only in base, condensing agent, solvent and temperature, and then
again in the claims and the summary. 108 of the 131 census claims are tier 1
`comparison` work of the form "Does the patent say 1000 ml of N,N-dimethylformamide?"
and "Does the patent say 5 C for the high end of the temperature range of this step?",
asked once per telling. The reference run has one worked example and 81 census claims
and passes at 11.7 minutes.

So the overrun is a property of the queue's design meeting a patent with five
tellings, not a defect in this annotation. Fixing it means pooling the repeated
tellings of one step into one card with its corroborations shown alongside. That is a
change to the review queue, it would change the census of every run including the
read only reference run, and the contract that raises it deliberately leaves it
unowned. I did not build it: CLAUDE.md is explicit that this repo is not software and
that designing a module here means having misread the task.

### What I did fix, which was a different thing

My first diagnosis was wrong and is recorded here because it was wrong for an
instructive reason. I attributed the overrun to `finalise.py` losing quantities,
on the strength of 17 census claims sitting on the collapsed `tembotrione` record and
16 tier 2 candidate misses about numbers the annotation had recorded, which summed to
exactly the 25 claims of the overrun. That arithmetic was a coincidence. Repairing
the loss took the census **up**, from 125 to 131, because a restored number generates
its own "does the patent say this" comparison claim.

The loss was real all the same, and it is fixed in `pipeline/finalise.py`:

    populated()   new, and it looks INSIDE a nested object
    merge_compound()   its scalar rule now asks populated(v)

The old rule was `v not in (None, "", [], {})`. `quantity` is a nested object, and one
whose every member is null is not literally `{}`, so it passed that test and replaced
a populated one. A1 runs per section, most sections print no numbers, and whichever
section merges last wins.

Measured, both runs, by collapsing `raw-compounds.json` under the old rule and the new
one:

    CN106008290A   records carrying a quantity   13 -> 26     13 regained
    CN104292137A   records carrying a quantity   30 -> 31      1 regained

The 13 include `tembotrione` itself at 355.5 g and 83.9 percent, and the charges of
sodium trifluoroethoxide, 1,3-cyclohexanedione, three of the bases and the pyridine.
In the reference run the one regained record is also `tembotrione`, at 188.0 g and
95.0 percent: the target compound of the worked example, its mass previously absent
from the gold.

The whole `quantity` block still moves as one unit, deliberately. Merging its members
field by field would also have restored the numbers, and would have let a mass from
Example 1 sit beside a yield from Example 3, asserting a pair no example printed.

`section_label` on the merged record still reads `Technical Field` while the numbers
are Example 5's. That is the separate, already documented flaw at
`pipeline/contracts/SINGLE-VALUED-FIELDS.md` item 3, and it is untouched here.

The reference run still reports **37 pass, 1 warn, 0 fail** with this change in place,
and no file under `runs/CN104292137A/` was written: rule 2 makes it read only, so its
artifacts on disk still hold the lossy values and now differ from what the current
code would produce. Regenerating it is the owner's call, not mine.

## A second guard that passes on absence

`resolve_translations.py` gates on runs of CJK codepoints. The vision pass rendered
环磺酮 into English as the pinyin `huanhuangtong` and as the phrase `cyclic sulfone
ketone`, which is a character by character gloss naming no real compound. Pinyin is
Latin script, so the gate found nothing and passed, and the wrong compound name
would have reached the reviewer with nothing flagging it.

This is the shape `TARGETS.md` warns about for row 12, `DE10113137A1`, with pinyin
in place of German. It belongs in
`pipeline/contracts/GUARDS-THAT-PASS-ON-ABSENCE.md` as a twelfth instance.

I corrected it at the vision input rather than downstream, with the reasoning on
each affected paragraph, and rebuilt from `enrich`. The Chinese is untouched.

## Two corrections made to the vision input, both from structure not from a name

1. **sulcotrione.** The vision read glossed 环磺酮 as sulcotrione on pages 5 to 7
   and as tembotrione on page 2. 环磺酮 is tembotrione. Established from the
   chemistry rather than from a name lookup: the product is 1,3-cyclohexanedione
   acylated by 2-chloro-4-(methylsulfonyl)-3-[(2,2,2-trifluoroethoxy)methyl]benzoic
   acid, C17H16ClF3O6S at 440.82. Sulcotrione is 磺草酮, C14H13ClO5S at 328.77, and
   lacks the trifluoroethoxymethyl group entirely. The printed 355.5 g of product on
   a 1 mol charge fits the first and is impossible for the second. Eleven paragraphs
   corrected; one A1 section that had followed the wrong gloss was dropped and
   re-run rather than edited.

2. **the pinyin and the "cyclic sulfone ketone" gloss**, above. Eight paragraphs.

Worth recording that the reference run hit the mirror image of finding 1: its own
title translated to "cyclic sulcotrione" for the same molecule. Two runs, two
patents, the same trap, caught by different means.

## What the patent's own numbers do

The arithmetic was run per step rather than assumed, and it does not close.

- **318 g for 1.0 mol** of methyl 2-chloro-3-bromomethyl-4-methylsulfonylbenzoate,
  in all five examples. The name implies C10H10BrClO4S at 341.60. Off by 6.9%.
- **1,3-cyclohexanedione charged at two different weights.** An implied 98 g/mol on
  lines 140, 159 and 167, and 97 on line 180, against the true 112.13. Line 151
  prints 145.6 g for 1.3 mol, which is 112.0 and correct. The patent uses two
  weights for one compound.
- **152 g for 1 mol of pyridine** on line 167. Pyridine is 79.10. The same 152 g is
  printed for the DBU on the same line, where it fits. It looks copied, and nothing
  was corrected.
- **Product mass and stated yield disagree in all five examples**, implying 415.6 to
  429.0 g/mol against tembotrione's 440.82. Purity correction widens the gap every
  time.
- **Step a isolates less than step b charges**, in all five: 0.898 to 0.928 mol
  isolated, 1 mol charged.

9 steps carry `molar_mass_inconsistent`, 5 `mass_balance_implausible`, 5
`scale_discontinuity`. Every number is recorded as printed. Nothing was repaired.

Step a's product mass and yield, by contrast, **do** close, on the free acid
C11H10ClF3O5S at 346.70 and on nothing else. That is the evidence 化合物II is the
acid rather than the methyl ester at 360.73, and it is why the hand-authored
structure for it is the acid.

## Provenance of everything a model wrote

Every artifact in this run was produced by **Claude Opus 5**, except the A1 compound
sections `detailed-description-lead-in` and `closing-statement`, which were produced
by **Claude Sonnet 5**; both returned the empty array, which is the correct answer
for boilerplate naming no substance.

That means the vision pass, the seven extraction passes, the four A5 audits and the
independent read in step 6 are all the same model family. **They are not independent
in the way the word usually implies.** Where the extraction missed something and the
step 6 read also missed it, nothing in this pipeline can see that, and it reports as
clean. Treat every place this run agrees with itself as weaker evidence than it
looks.

Two places where that structure did earn its keep, because the readers disagreed:

- The step 6 reader, which never saw `output/`, reached the pyridine 152 g finding
  and the two-weights-for-one-dione finding on its own.
- The A5 patent audit, in a fresh context, derived tembotrione from the drawn
  equation without being told, and separately caught
  `extraction_rollup.key_starting_materials` listing 2,2,2-trifluoroethanol, which
  this patent charges in no step and names only as the prior-art reagent it
  replaces.
- The A5 reactions audit caught a `scale_discontinuity` flag missing from Example 3
  and Example 5, and it was right; Example 3 was re-run and now carries it.
- The A2 read of the summary section caught an A1 note asserting that scheme (1)
  does not depict sodium trifluoroethoxide. The page prints `+ CF3CH2ONa` on the
  reactant side. The `[IMAGE_EXTRACT]` spans under-read both schemes, dropping that
  co-reactant and the drawn CH3OH, NaBr and H2O by-products.

## Disagreements left standing rather than resolved

- Example 1 step a is annotated `is_one_pot: true` with an ester cleavage; Examples
  2 to 5 step a record only the etherification. The A5 pathways audit calls that a
  major inconsistency and it is right that the same transformation carries two
  classifications. Both readings are in the artifacts. The evidence for the cleavage
  is line 95, the drawn CH3OH, and the arithmetic closing on the free acid; the
  evidence against is that the prose of those four sections describes one
  transformation.
- Claims carries `contains_procedure: false`, so no reactions were extracted from
  it, while the reference run does extract from its claims. The two drawn schemes in
  the claims are the same two drawings as in the summary, so no chemistry is lost,
  only per-section recall. Recorded by the A5 pathways audit as a finding.
- An A1 note calls Example 2's `1.2mol(146.4g)` of sodium trifluoroethoxide
  inconsistent. It is not: 146.4 over 1.2 is 122.0 and matches C2H2F3ONa exactly.
  The A2 pass said so and declined to raise the flag. The wrong note still stands in
  the compounds artifact.

## One more shared-code defect, restored not committed

`pipeline/make_svgs.py:22` writes its diagrams to `pipeline/svg/`, a shared
directory outside any run. Running this patent overwrote eight tracked files
belonging to the repo. I restored them with `git checkout` each time and they are
not in any commit here, but the next person to run any patent will dirty them
again.

## Hand-authored inputs

Four structures, each checked atom by atom against its name, each with the formula
the SMILES implies compared against the formula the name implies, and each
corroborated by a number the patent prints rather than by the name alone:

| identifier | SMILES | formula | corroboration |
|---|---|---|---|
| 化合物II | `OC(=O)c1ccc(S(C)(=O)=O)c(COCC(F)(F)F)c1Cl` | C11H10ClF3O5S, 346.71 | step a mass and yield imply 346 in all five examples |
| HBTU | `CN(C)C(=[N+](C)C)On1nnc2ccccc21.F[P-](F)(F)(F)(F)F` | C11H16F6N5OP, 379.24 | 758 g for 2 mol, line 151 |
| CDI | `O=C(n1ccnc1)n1ccnc1` | C7H6N4O, 162.15 | 194.6 g for 1.2 mol, line 140 |
| DBU | `C1CCC2=NCCCN2CC1` | C9H16N2, 152.24 | 152 g for 1 mol, line 167 |

Seven translations plus one override. The override is `35％的盐酸`, which the alias
tier resolved to "hydrochloric acid": the right substance and the wrong strength,
and the strength is a fact about what was charged.

Step 6 keyed all 183 lines with 584 spans, 432 specific and 152 generic, every span
verified as a literal substring of the English rendering `verify.py:3020` compares
it against.

## Session 2026-08-30: the visual gate, which the first session did not report

Re-running the pipeline on this branch showed a second gate failure the notes above
never mentioned: `visual` failed with Chinese characters in 20 lines of
`drawing-claims.json`. The status line at the top counted selfcheck's two failures
and missed that the runner had also printed `GATE FAILED: visual`. Recorded here
because a report that says "blocked on one thing" and is blocked on two is the
silent kind of wrong this repo is about.

Two sources, two fixes, neither touching the gold:

1. **Nine vision-pass discrepancy fields quote the patent in Chinese** (p02#0 to #4,
   p04#2, p04#3, p05#1). The stage's mechanism for this is the hand-authored
   `output/relevant_output/visual/quote-translations.json`, which the reference run
   has and this run did not. Written, one whole English sentence per field, using
   `output/translations.json`'s English for every compound name.

2. **Claim 1 on page 2 runs over three unnumbered sub-paragraphs**, which the vision
   pass keyed by their opening words, `步骤a`, `步骤b`, `其中`, and the two drawn
   schemes anchor between them. Those anchors are what `build_enriched.py` places the
   drawings by, so they cannot be rewritten without moving both schemes in the
   enriched text and invalidating every line key downstream. Instead they are given
   English handles in `marker_labels_en`, the map the stage already applies to
   Chinese INID labels on the front page. `make_visual_evidence.py` applied that map
   to `markers_out` but copied `between_markers` through unmapped, one line at
   `between_markers_en`; it now maps both. The reference run's `between_markers` are
   all `[00NN]` or prose and none of its `marker_labels_en` keys appear there, so its
   output is unchanged by inspection. Not re-run: rule 2.

After this: `visual` passes, `selfcheck` is 35 pass, 1 warn, 2 fail, and both
failures are the census budget described above. Still blocked on that, still
unowned, still not built here.

This session's edits were produced by Claude Fable 5.

## Session 2026-08-30, second pass: the census overrun was mostly not what it looked like

The first session read the 131-claim census as a property of the queue meeting a
patent with five tellings. Most of it was a `verify.py` matcher gap on this patent's
number formats, and the rest was four records citing the wrong lines. Pulled apart:

1. **`verify.py` did not know this patent's units.** `UNIT_ALTERNATION` had `ml`,
   `h`, `hr` and `hrs`; the patent prints `1000mL`, `5小时`, `0.5-12h` and its
   translation prints `5 hours`. `mL` read as a bare 1000 and every reaction time
   read as a bare number, so every solvent volume and time on the patent reported
   `partial`, and a partial promotes its whole record into the tier 1 census. `NUMBER`
   also had no sign, so `-10-8℃` on line 167 was `-10` on no line of the document.
   Added `mL`, `hours`, `hour`, `小时`, `分钟` and a guarded leading minus (only where
   nothing alphanumeric or hyphen-like precedes it, so the `-2` in `1,2-dichloro` and
   the `-10` in `5-10℃` stay what they are). The reference run, re-verified on a
   scratch copy under `ANNOTATION_RUNS_ROOT`, still reports 37 pass, 1 warn, 0 fail;
   its census moved 81 to 82 because the sign fix surfaced a real candidate miss,
   line 48 prints -15℃ and no record holds it. `runs/CN104292137A/` was not written.
2. **Four Summary records cited only their opening line.** Their own `quote_zh`
   named lines 105 to 127 as the source of the conditions and ratios, but
   `source_lines` said `[95, 96]`, and a two-element `source_lines` is read as a
   range. Set to the explicit line lists the quotes already named, in
   `output/stages/A2-reactions/summary-of-the-invention-provenance.json`.
3. **One substance, two identifiers, twice.** A1 named 三氟乙醇 `trifluoroethanol`
   in the abstract and `2,2,2-trifluoroethanol` in three other sections, and HBTU
   `O-benzotriazol-` in the claims and `O-benzotriazolyl-` in the summary, so the
   gold carried two records for each and the recall sweep found the printed English
   form on neither. Harmonised to one identifier each with the printed form as an
   alias, in the A1 section files and their provenance sidecars. Gold compounds
   53 to 51. A first attempt also put an alias on the A2 background reaction's
   compound; the reactions schema forbids that key and validate said so, reverted.

Items 2 and 3 are edits to LLM-pass outputs under `output/stages/`, made by the same
kind of agent that wrote them and recorded here field by field. The A5 audits were
run against the records before these edits and were not re-run; nothing they found
depended on the identifiers or line lists that changed.

Result: pipeline reaches the end, `selfcheck` **37 pass, 1 warn, 0 fail**, census 97
claims at 14.1 minutes, grounded 99.5 percent. The `verify` gate is red on exactly one
claim and is left red: line 105 says M is one of the Li, Na and K ions and the sweep
asks whether Summary step 1 should record them. It should not, they are the cations
of an unspecified base, not substances charged, and recording the disagreement is
worth more than making the gate green.

Two things about the runner, observed and not fixed. It plans every stage's
staleness before any stage runs, so an edit under `output/stages/` takes two or
three invocations to cascade through merge, finalise and validate; and
`make_svgs.py:22` still writes to the shared `pipeline/svg/`, restored with
`git checkout` after every run again.

This session's edits were produced by Claude Fable 5.
