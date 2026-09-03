# WO2022024094A1 run notes

"Process for preparation of mesotrione and its intermediates", a WO publication in
English. 23 rendered pages. Born digital, not a scan: the PDF carries a text layer,
so the prose in this annotation comes from the text layer and the vision pass was
run for the drawn structures, which no text layer contains.

## Model provenance, and why the agreement here is weaker than it looks

CLAUDE.md asks for this because correlated blindness is invisible to the pipeline.

Every judgement artifact in this run was produced by Claude Opus 5, across two
Claude Code sessions. The first session ran the seven passes and the step 6 read;
the second resumed the deterministic half from the structures gate onward. The
`what_this_is_en` field of `input/substances-observed.json` carries the same
attribution, written at the time that file was produced.

| pass | invocations | what it produced |
|---|---:|---|
| V | 23 | one page read each, `input/vision/pNN.json` |
| A0 | 1 | the 15 section map |
| A1 | 15 | 109 compound records across sections, 43 unique after merge |
| A2 | 11 | 24 reaction records |
| A3 | 1 | 16 pathways |
| A4 | 1 | the patent record |
| A5 | 4 | the adversarial audits, fresh context, one per artifact |
| step 6 | 1 | the independent substance read, 758 spans over 406 lines |

**The three readings in this pack are not independent in the way the word implies.**
The vision pass, the extraction passes and the step 6 read are the same model working
from the same pages. Where the extraction missed something and the step 6 read also
missed it, nothing here can see that, and it reports as clean. Only the
disagreements are strong evidence.

Reading B is the one genuinely non-model reader: ChemDataExtractor, a grammar and a
CRF tagger, over the same lines. Where it and the LLM read agree, that agreement is
worth more than any agreement between two of the passes above.

## Three input defects this run found and fixed

None of these were fixed in `output/`. Each was fixed in the input that produced it
and the pipeline re-run, per CLAUDE.md rule 3.

1. **`family_id` was an integer.** `biblio.schema.json` permits `["string","integer"]`
   but `patent.schema.json` requires `["string","null"]`, so a biblio that validates
   produced a `patent.json` that does not. Every other run in this repo happens to
   author the field as a string, so the integer branch had never been exercised.
   Fixed by quoting it in the biblio. **The schema disagreement is still there** and
   the next person to type an unquoted family id will hit it again.

2. **The step 6 read quoted reagent labels out of the `IMAGE_EXTRACT` JSON.**
   34 spans over 15 drawing lines. That JSON is machine-readable structure, not text:
   the English rendering of a drawing line is "Drawn on the page: N structures" plus
   each drawn structure's formula and SMILES, and it carries no condition labels at
   all. `verify.py` checks spans against that rendering and stopped the run,
   correctly. The 34 spans are removed and the removal is recorded in
   `drawn_only_reagents_not_carried_en` inside the file rather than done silently,
   because two of them are named nowhere else in the document.

3. **The vision pass wrote `null` in `between_markers`.** 8 drawings over 6 pages.
   The convention the reference run and the V prompt both use is a pair of strings,
   with parenthesised prose where no marker is visible. `null` crashed
   `make_visual_evidence.py` on `m.strip()`. Replaced with the prose form.

## What the removal in defect 2 costs

Two substances are now recorded nowhere:

- **Sodium acetate**, drawn at line 75. The prose at line 70 says "acetic acid and
  acetate ion", which is not the same claim.
- **O2**, drawn at line 83 as the condition "Nitric acid/O2". The prose at line 81
  recites sulphuric acid, nitric acid and vanadium pentoxide, and no oxygen.

Both are conditions on background-art schemes reciting US 5,591,890 and
CN 105669504 A, so neither touches the invention's own route. Recorded because a
loss that happens to be harmless is still a loss.

`(CH3CH2 )3N` and `V2O5` were also removed, but those substances survive under
their other spellings: triethylamine in the prose at lines 245, 246, 329 and 330,
and vanadium pentoxide at 77, 78, 81, 82, 88 and 89. Only the formula spellings
are gone.

## The gates

Both coverage gates passed with no curated entries.

- **structures**: 43 compounds resolved and 34 drawings produced with
  `input/structures-curated.json` empty. Nothing was hand-authored, so the warning
  in CLAUDE.md rule 5 about checking SMILES atom by atom did not arise on this run.
  Every structure here came from a resolver tier that can be re-derived.
- **translations**: `output/translations.json` is `{}`. The document is English
  throughout and nothing Chinese can reach a screen.

## The verify gate is red, and 13 of its 20 failures are a bug in verify.py

`verify.py` cannot see a volume written with the unit jammed on in capital-L form,
`120mL`. `UNIT_ALTERNATION` at verify.py:218 lists `ml` case-sensitively, and its
`[gLl]` branch matches a standalone `L` but never the `m` of `mL`. With no unit
matched, `BARE_BOUNDARY` then disqualifies the bare number too, because the next
character is a letter. The number becomes invisible.

Measured, not argued:

```
'hydrochloric acid(120mL, 1.23mol)'  -> [('1.23', 'mol')]      120 not seen
'water (160mL)'                      -> []                     nothing seen
'acid (5.4mL, 0.054mol)'             -> [('5', None), ...]     5.4 MISREAD as 5
'hypochlorite (500ml, 0.745mol)'     -> [('500', 'ml')]        lowercase, fine
'water (60 mL)'                      -> [('60', None)]         spaced, degrades to bare
```

This is why `volume_ml` scores 6/19 in the numeric field table while every other
numeric field scores N/N, and it is 13 of the 20 claims in the grounding gate. Each
of those 13 is reported as "the fabrication signal", and each of the values is
plainly printed on a line the record cites: `120mL` on line 264, `54mL` on line 285,
`160mL` on line 300, `5.4mL` on line 329.

**The annotation is right and the checker is wrong.** No number was invented and no
citation points at the wrong line. Per CLAUDE.md rule 4 that verdict was reached by
re-measuring rather than by preferring the annotation.

`verify_selfcheck.py` cannot catch this. Its check J, "does `not_found` mean what it
says", re-reads the cited lines with the same tokeniser, so it confirms the absence
its own scanner manufactured and reports `[PASS] every not_found value really is
absent from its cited lines: 13 checked`. A self-check that shares a scanner with
the thing it checks cannot see a scanner bug. That belongs in
`contracts/GUARDS-THAT-PASS-ON-ABSENCE.md` as the mirror case: a guard that fails on
presence.

**Not fixed here.** The fix is one token in a regex in the shared verification
engine, and it changes the verification output of every run that writes volumes that
way. Counted across the pack: CN112645853A 114 occurrences, WO2022024094A1 30,
CN109678767A 5, and every other run 0. **The reference run CN104292137A has none, so
its pinned numbers would not move.** That is the fact anyone deciding this should
have, and it is measured rather than assumed.

## The other 7 grounding failures are real

They are `__substance__` claims: the patent names a substance on a line a record
cites and no record holds it as an identifier. `acetate ion` at line 70, `NMSBA` and
`NMST` at 350 and 359, `ruthenium` at 185, `HPPD` at 55 and others. The A5 compounds
audit independently reached the same conclusion about `acetate ion`, calling it the
only compound-level recall gap it found. These are what the tier 1 and tier 2 census
is for and they are left in the queue for a reviewer.

## Reading B could not run

ChemDataExtractor installs but its current API is incompatible with `mentions.py`:
`legacy_pos_tag is not a supported tag type`. `mentions.py` refused to write an empty
`substances-cde.json`, which is correct, because an empty file reads on every screen
as "ChemDataExtractor found nothing" and that is a different claim from "it could not
run". The sweep therefore publishes `readers: ["llm"]` and every finding says so.

So the caveat above stands at full strength: there is no non-model reader in this
run, and every agreement in it is agreement between one model and itself.

## What I am least sure of

Recorded here rather than resolved, per CLAUDE.md rule 8.

- **The A5 compounds audit found a real merge defect and it is still open.** The
  merged `mesotrione` record carries Example 7's melting point, appearance and
  purity but an all-null `quantity`, and is labelled "Summary of the Invention".
  Example 7 prints "Yield: 17g (85%)" and the raw record holds `mass_g 17.0,
  yield_pct 85.0`. The cross-section merge kept the empty quantity of an
  alphabetically later section. This is the patent's target compound losing its
  mass and its yield. The fix belongs in `finalise.py`, not in the artifact, and it
  would change every run in this repo, so it is not made here.
- **The verify gate is red on 13 false positives.** See above. A reviewer opening
  this run will meet 12 claims marked `critical`, "a value on no line of the
  patent", and most of them are values plainly on the page. That is the single most
  misleading thing in this deliverable and it is not fixed.
- **45 A5 findings in total, 14 of them major**, across the four artifacts. They are
  published in the deliverable rather than acted on, which is what the audit is for.
- The step 6 read and the extraction are the same model. See above.

## Gold curation, prompt 2 reconciliation (2026-09-01)

Model: Claude Opus 5, run interactively by sathvik.k.

Prompt 1 was run first and independently: 19 transformations read from
`input/WO2022024094A1-enriched-numbered.md` alone, with `output/reactions.json`
unopened until prompt 1 was written down. Prompt 2 then reconciled the two.

    gold reactions read from the patent      19
    records originally in reactions.json     24
    matched by identity                      18 of 19
    missing                                  1
    invented / false records                 0
    duplicates by the per-section convention 6 records, 3 groups

**One record added by hand.** `Detailed Description of the Invention_Step 4`,
the in-situ preparation of the RuO2 catalyst from ruthenium trichloride in
aqueous caustic with a chlorine purge, paragraph [0034] at lines 187 and 192.
It was the only transformation in the patent with no record. `reaction_class`
`catalyst_preparation` already existed in the enum, so no schema change was
needed. A matching entry was added to `reactions-provenance.json`, keeping the
two files 1:1 at 25 entries each.

`id` and `reaction_uuid` were computed with the pipeline's own formulae from
`pipeline/finalise.py`, `uuid5(NAMESPACE_DNS, "WO2022024094A1::" + normalised
reaction_id)`, and that formula was verified against all 24 pre-existing records
before use. `product_smiles` is null because the reactions schema types that
field as null on every record by design.

`reactions.json` revalidates against `pipeline/schemas/reactions.schema.json`
at 25 records.

**This is a hand-edit of `output/`, which CLAUDE.md rule 3 forbids.** It was made
on the reviewer's explicit instruction, following the precedent set on
CN112645853A, and is recorded here so the edit is not indistinguishable from
generated output. Everything else was flagged, not fixed.

15 findings are in `output/GOLDEN-DATASET-FINDINGS.xlsx`, Reactions tab, in the
same shape as the CN112645853A workbook: 1 fixed, 3 fixable with fields that
already exist, 6 needing a schema change, 3 needing a reviewer decision.

Correlated-blindness note, per CLAUDE.md: the vision pass, the A2 extraction and
this reconciliation were all produced by language models. Where the extraction
missed something and this pass also missed it, nothing here can see it. One such
case is already known and recorded as F-015: the implied NMSBA to NMSBC step of
CN106565561A at line 88 is absent from both the extraction and my independent
list of 19.

### Merge of the per-section duplicates (2026-09-01)

Nine records for three transformations merged to three, on the reviewer's
instruction, applying the gold dedup rule: one entry for a reaction DESCRIBED in
several sections, separate entries only for reactions PERFORMED separately. The
Claims and Detailed Description route records were folded into the Summary ones,
`section_label` taking the first section in document order.

Nothing was discarded. Compounds, reactant_names, tags and validation_flags are
the union; conditions, workup, purification and byproduct_recovery take the first
non-empty value; procedure_text concatenates all three verbatim passages under
section headers; notes concatenates all three sidecars unedited; and the three
line spans are unioned in `reactions-provenance.json`. Compound unions were
12, 10 and 15 before and after, with nothing lost.

What it cost, recorded because no field can hold it: the records no longer say
which section contributed which value. That ladder was real. The Summary named
no oxidant, the Claims named sodium hypochlorite, and only the Detailed
Description offered alternatives; claim 9 printed "1,2-dichloroethane" where the
description printed "dichloroethane". It also makes the alternatives-recorded-as-
co-present defect file-wide rather than confined to one record. Both facts are
written into the notes of each merged record.

    reactions.json  25 -> 19 records, matching the 19 transformations of prompt 1
    validates against pipeline/schemas/reactions.schema.json

This diverges from the reference run CN104292137A, which keeps per-section
records. A later run comparing the two must not read the difference as a defect.

## Phase 2, prompt 5: per-record content verification (2026-09-01)

Model: Claude Opus 5, run interactively by sathvik.k.

All records checked twice, each against the whole 406-line `.md` rather than only
its cited span. 23 findings, F-003 to F-025, all in
`output/GOLDEN-DATASET-FINDINGS.xlsx`. 21 fixed, 5 open.

Verified rather than assumed: **68 of 68 quantity values** in the file were found
verbatim in their cited spans, so nothing numeric was invented anywhere. The 18
places where an `> EN:` line differs from its source are all front-page INID code
prefixes, with no semantic divergence.

### Nine new fields, and why each exists

    time_h_min / time_h_max          "6-8 hours" against a scalar time_h
    time_h_tiers                     three nested tiers at line 194
    ph_target_min / ph_target_max    "pH < 3" recorded as ph_target 3.0
    product_purity_pct_min / _max    ">95%" recorded as an assayed 95.0
    temperature_stages               one object cannot hold reflux, then 25-30, then 5-10
    stirring_stated                  every Example stirs; the enum has no "type unstated"
    solvent_recovery_pct_min / _max  ">85%" stated five times, held nowhere
    catalyst_recovery                filtration, reuse, and the ">50 conversion" bound
    catalyst_alternatives            RuO2 / RuO2 hydrate / RuCl3 are forms of supply
    catalytic_cycle_species          ruthenate, perruthenate, RuO4 are not charged

Naming follows `runs/CN112645853A/output/`, which already carries `time_h_min`,
`time_h_max`, `ph_target_min` and `ph_target_max`.

**`reactions.json` no longer validates against `pipeline/schemas/reactions.schema.json`.**
That is the accepted trade taken on CN112645853A, recorded so a later run does not
read it as corruption. `pipeline/schemas` was deliberately left untouched.

### The alternatives handling, and its revision

The three route records asserted that three oxidants, six ruthenium species and
seven bases were each present in one flask. Method used, on the reviewer's
instruction: read how each section states the alternatives. The patent varies the
OXIDANT with distinct conditions attached, claims 2 and 6 and [0035] narrowing it
to sodium hypochlorite which owns the reflux and the time tiers, and varies the
BASE with a stated preference at [0043], while solvents are always an
undifferentiated list with "Preferably... dichloromethane" and no distinct
condition. So step 1 split by oxidant into Step 1, 1a, 1b and step 3 split by base
into Step 3 and 3a to 3f. Solvent lists kept as lists, with the reason on each
record.

The hydrogen peroxide record does NOT carry `catalytic_cycle_species`: line 185
states that mechanism specifically for the hypochlorite.

### Three defects were mine, not the extraction's

`F-017` a false `no_conditions` flag and `F-018` a phantom sixth solvent, both
artifacts of the 9-to-3 merge, and `F-023` an identifier split on the record added
in the reconciliation pass. All three fixed and attributed in the workbook.

### Byproduct_recovery was investigated and rejected

Asked whether the solvent and catalyst recovery numbers should go in
`byproduct_recovery`. Measured: it is empty on every record of every run in this
repo, is not a column in the shipped export CSV, and no downstream stage reads it.
Putting the numbers there would have hidden them as effectively as prose. New
fields were used instead.

### Still open

    F-007  prose "acetate ion" against drawn "Sodium acetate", one reading lost
    F-008  the cobalt option of US5424481 dropped
    F-024  reaction_class has no "rearrangement" value, mitigated by a tag
    F-025  the implied NMSBA to NMSBC step of CN106565561A at line 88
    F-026  the schema divergence above, an accepted trade

Correlated blindness, per CLAUDE.md: the vision pass, the A2 extraction and this
verification were all produced by language models. F-025 is a known instance, missed
by the extraction and by my own independent count of 19 alike.

### Closing pass (2026-09-01)

`F-007` both readings kept: the compound identifier stays "Sodium acetate", the
prose term "acetate ion" is carried in an `aliases` array on the compound and on
the Sodium acetate record in `compounds.json`. Sodium acetate is a source of
acetate ion, so the scheme is more specific than the prose rather than
contradicting it.

`F-025` fixed. `Background of the Invention_Step 9` added: NMSBA to NMSBC per
CN106565561A, line 88, precursor Step 8. Implied by the stated target of that
cited process, with no reagent or condition given and no arrow drawn, so all
condition fields are null, `no_conditions` is raised and
`reaction_class_confidence` is "low". Recorded on the same standard as
Background Step 2, the equivalent step of US 7,820,863.

This step was missed by the extraction AND by my own independent count of 19 in
prompt 1. It is the one demonstrated instance of correlated blindness in this run,
both readings being language models, which is why agreement between the two is not
treated as confirmation anywhere in these notes.

`F-026` closed, not a defect. The reviewer's decision: the repo schema is not the
authority, the gold is. `pipeline/schemas` was deliberately left untouched and
`reactions.json` intentionally carries fields it does not define.

    reactions.json  28 records
    open findings   2 (F-008 cobalt option, F-024 no rearrangement enum value)

### Recall check on reactions.json (2026-09-01)

Asked whether the records are not merely CORRECT but COMPLETE: is anything the
patent states about a reaction absent from the gold. The earlier numeric check had
passed at 118 of 118, but it only asked whether a number appears somewhere in the
file, not whether it sits in a field a consumer can read. Two real gaps came out of
asking the harder question.

`F-027` every Example reports the melting point and the appearance of the batch it
made, and both existed only inside `procedure_text`. There is no melting-point or
appearance field anywhere in the reactions schema. Added `product_observed` to all
seven Examples. It belongs on the reaction and not only on the compound because the
three NMSBA runs measured 210-214, 207-210 and 210-214 and the three enol ester runs
measured 158-163, 152-158 and 157-163: one value on a compound cannot hold them and
silently keeps one batch while discarding the others.

`F-029` the patent states sub-atmospheric pressure seven times, for drying,
filtration and distillation, and none of it was in any field. Added
`workup.pressure_operations`. `conditions.pressure` is deliberately left
`not_specified`: every pressure phrase in this patent governs a work-up operation and
never the reaction, so setting the reaction pressure would assert what the patent
does not say. Examples 4 and 5 get nothing, because they say only "concentrated".

One finding raised during this pass is a compounds.json defect, not a reactions
one, so it was moved off the Reactions tab and renumbered `C-001` on the Compounds
tab. compounds.json holds one melting point per compound, so Example 2's 207-210
and Examples 4 and 5's 158-163 and 152-158 are absent, as are two of the three enol
ester appearances. Pick it up at prompt 6. The reactions side already carries every
one of those measurements in `product_observed`, so nothing is lost from the gold as
a whole; compounds.json on its own is what is incomplete.

    reactions.json     28 records
    Reactions findings 28: 27 fixed, 1 closed, NONE open
    Compounds findings 1 open (C-001), waiting for prompt 6

### Revision of the alternatives split (2026-09-01, same session)

The split of step 1 by oxidant and step 3 by base was REVERTED on the reviewer's
rule: a separate record is earned only where the patent gives different conditions,
yields or purities, not by a list of things that could be used. All seven bases come
from one sentence at line 245 and all three oxidants from one sentence at line 183,
with no condition, yield or purity attached to any alternative, and only triethylamine
and dichloromethane are ever actually charged, in Example 7. The eight split records
were near-empty clones differing by a single word.

The original defect is still fixed. Alternatives are kept OUT of `compounds[]`, which
is what wrongly asserted that seven bases were in one flask, and are recorded in
`reagent_alternatives` with the sentence they come from, plus a plain-language
`alternatives_note` on each record. This matches the treatment already given to the
cobalt option in F-008 and to the ruthenium forms and catalytic-cycle species.

Caught during the revert: the six alternative bases had been stripped from
`compounds[]` when the splits were created, so deleting those records briefly left
them nowhere. Restored into `reagent_alternatives`, and all 20 named reagents in the
patent verified present afterwards.

    reactions.json  28 -> 20 records; the invention route is 3 records again

### Null-field audit (2026-09-01)

Every field that was null or `not_specified` on all 20 records was tested against the
patent, rather than assuming null meant the patent was silent. 37 fields were null
across the board. 36 are correctly null: the patent states no molar ratio in words, no
named reaction, no in-process monitoring, no mass spectrometry, no drying agent, no
inert atmosphere, no photochemistry, no stereo or regio selectivity, no reaction pH and
no extraction, and `canonical_rxn`, `product_smiles`, `reactant_smiles` and
`smiles_source` are typed null by the schema on every record by design.

Three apparent hits were artifacts and are recorded so nobody re-chases them:
"EXTRACT" came from the `IMAGE_EXTRACT` markers, "uv" from image metadata, and "DE"
from the Designated States list, where it is the country code for Germany.

One real gap came out of it. `conditions.concentration` was null everywhere, but the
oxidant is charged as a solution with a printed volume and a printed mole figure, so
its strength is derivable: 1.49, 1.49 and 1.48 mol/L across the three Examples, about
11% w/v, agreeing on one commercial solution. Recorded as `F-030`, marked DERIVED in
the field's own text so it is never mistaken for a printed value.

That gap is worth the attention because `pipeline/contracts/HYPOCHLORITE-STRENGTH.md`
records a real defect of exactly this shape on CN104292137A: the patent printed "15%
sodium hypochlorite solution", the gold attached 500 g to the solute name, and the
oxidant came out at 28 equivalents against a true 4.2. This patent is not exposed to
that failure, because it prints moles directly and the equivalents are sane at 2.68,
6.48 and 2.52, but the strength is now explicit rather than left to be recomputed.

    reactions.json  20 records
    Reactions findings 29, all closed
