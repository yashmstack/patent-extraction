# US20040236146A1 run notes

Method for producing 3-bromomethylbenzoic acids, Bayer CropScience, published
2004-11-25, abandoned. Annotated 2026-08-28. Row 10 of `TARGETS.md`, the
`Intermediate Molecule` tier, one representative of family 7698422; the WO member
`WO2003022800A1` is deliberately not annotated.

## Which model wrote what

**Every artifact in this run that a model produced was produced by the same model,
Claude Opus 5 (1M context).** The orchestrating session and all thirty-one subagent
invocations ran on it; no subagent was given a model override. That covers the 4
vision page reads, the section map, the 12 compound passes and their re-runs, the 7
reaction passes and their re-runs, the pathways pass, the patent record, the four
adversarial audits, and the independent completeness read.

`CLAUDE.md` asks for this because correlated blindness is invisible to the pipeline.
The sharper version, as the previous run put it:

- **A5's independence here is context-independence, not model independence.** Each
  audit ran in a fresh context, told explicitly not to open `output/stages/`,
  `input/PROMPT-CORRECTIONS.md`, any notes file, the other run directories, or
  `input/substances-observed.json`. That is what the pass is specified to be. It is
  not a second opinion from a different model, so a blind spot in this model's
  reading of a page is invisible to the audit by construction.
- **Step 6 is the same.** The independent read was delegated to a fresh context
  before any extraction existed on disk, so it cannot have been derived from one.
  Still the same model. Where it agrees with the extraction, that agreement is
  weaker evidence than two readers agreeing would be.
- **`mentions.py`, reading B, did not run.** ChemDataExtractor is unavailable here,
  the stage says so loudly, and the artifact publishes `readers: ["llm"]` with every
  finding saying "one reader only". That is the pack behaving correctly, not a gap
  that was closed.
- The one genuinely non-model check in the run is `resolve_names.py`, the
  grammar-based OPSIN pass. It carried more weight here than on a Chinese patent: it
  resolved 24 of the 25 structures in the gold from their names, leaving exactly one
  to be hand-authored.

### Where the single-model risk was visible

Four A1 sections were told to write an empty array where they found no substance,
and three of them cited `input/substances-observed.json` in their reasoning for
doing so. That file is the step 6 independent read, and A1 consulting it makes the
two no longer independent for those sections. The sections are `Bibliographic`,
`Technical Field`, `Formula Definitions` and `Examples Lead-in`. **The recall
measurement is unaffected**, because the sweep's universe is `specific` spans only
and all four of those sections carry nothing but `generic` ones, but the
contamination is real and is recorded rather than argued away.

## The chemistry, in one paragraph

One transformation, told seven times. A 2-halo-3-methyl-4-alkylsulfonylbenzoic acid
is brominated at the benzylic methyl to the 3-bromomethyl compound, by either
**variant A**, N-bromosuccinimide with a radical initiator, or **variant B**,
elemental bromine under a photolamp. The point of the invention is that it
brominates the free ACID directly: [0002] says the known route to that acid, EP-A
0 292 944, brominates the methyl ester and then hydrolyses it, and that WO 99/06339
needs an additional oxidizing agent. Example 1 makes the methylsulfonyl compound in
88.4% and runs both variants; Example 2 makes the ethylsulfonyl homologue in 95.6%.
Claim 19 also claims the compound genus, excluding the one member EP-A 0 292 944
already disclosed, which is precisely Example 1's product.

## What the run holds

| | |
|---|---|
| pages | 4, born digital with an OCR text layer, 11,953 characters |
| sections (A0) | 12, contiguous over all 198 lines |
| compound records | 75 raw over 12 sections, 44 after identifier merge |
| reaction records | 13 over 7 sections |
| pathways | 13, 12 section scope and 1 patent scope |
| drawings | 9, every one a Markush generic, so every one carries no SMILES |
| step-6 independent read | 180 lines keyed, 250 spans, 118 specific, 0 unverified |
| structures | 25 of 44 identifiers, 24 by OPSIN and 1 hand-authored |
| A5 findings | 52 over four artifacts: 1 critical, 17 major, 34 minor |
| hand-authored | 1 SMILES, 3 structure exemptions, 0 translations |
| selfcheck | 37 pass, 1 warn, 0 fail |

## Zero fragmentation, and how

`finalise.py` reports **0 molecules carried under more than one spelling**. The
reference run has twelve such families and `contracts/DUPLICATE-FAMILIES.md` argues,
correctly for that run, that not merging them is the right call because production
keys on the exact identifier string.

That was avoidable here only because this patent misprints names so badly that the
problem was obvious up front. It prints the Example 1 substrate three ways and the
Example 1 product four, including `2-chloro-3-methyl4-sulfonylmethylbenzoic acid`
with a hyphen missing AND the sulfone written backwards. Left alone that is one
molecule under seven join keys. So `input/PROMPT-CORRECTIONS.md` section 2 fixes one
identifier per substance before A1 runs, always **a spelling the document itself
prints somewhere**, and every printed variant is carried in `aliases` with its line
number in `notes`. Nothing is invented and nothing is silently corrected.

## The English-patent problems, which are new to this pack

This is the pack's first non-Chinese patent and three things assume Chinese.

1. **`resolve_translations.py` passes trivially.** It gates on runs of CJK
   codepoints, finds none, and reports "all 0 strings resolve". That is the
   `TARGETS.md` row 12 caveat about German, arriving early on a US patent. It is not
   lying, but it is not answering a question either, and no reader should take the
   green as evidence about this run.
2. **The `> EN:` line is a REPAIR, not a translation.** Each source line appears
   twice, as printed and as an `EN:` reading, and on an English patent the second
   silently corrects the first. Two shared-code checks read only the repair and so
   rejected as-printed spans that were the only thing literally on their line. Both
   are fixed and committed; see below.
3. **The A5 prompt's translation check has no subject**, and its drawings check found
   nine Markush generics rather than a scheme. The audits handled both correctly on
   their own reading.

## The most valuable finding: a correct biblio shipped a false fact

`patent.json` described Bayer CropScience AG as a small or medium enterprise.

`biblio.schema.json`'s assignee enum was moved to production's six words when
CN112645853A was annotated, so the biblio speaks the record's vocabulary directly.
`finalise.py`'s `ASSIGNEE_TYPE` still held only the OLD biblio words, so
`multinational_corp`, `sme` and `consortium` had no key at all, and
`assignee_type()` ends in `.get(kind, "sme")`. Three of the six legal values fell
through to `sme` without a word, and the tag `assignee_type:sme` went with it.

It held for two runs by coincidence: the reference's assignee is a university, which
both vocabularies share, and CN112645853A's is an `sme`, which is what the default
happens to be. This is the first multinational on the list and the first to be wrong.

Found by the A5 audit of `patent.json`, which checked the value against the biblio
rather than against the record it came from. Fixed with the operator's explicit
approval; the silent default on an unrecognised value survives and is still a
`GUARDS-THAT-PASS-ON-ABSENCE` case.

## Four shared-code fixes, all with explicit approval

Each is invisible on the reference run and each blocked or corrupted this one.

1. **`finalise.py` `ASSIGNEE_TYPE`**, above. Widened to identity for production's
   six, older biblio words kept as aliases. `biblio.schema.json`'s comment claiming
   finalise copies the field with no mapping was true once and is corrected.
2. **`make_svgs.py` m2-route width.** The previous run made the target box's HEIGHT
   a function of the name's line count; the WIDTH was still fixed, and the box hangs
   centred under the last step, so on a single-step route it overhung the left edge
   of the canvas. This target's first token is 45 characters with no space, 346px at
   size 14, centred at 146, so it started 27px off the page and the overflow check
   failed the stage. `wrap_lines` refuses to break such a token on purpose and is
   right to. The box and the left margin are now functions of the widest line. **The
   reference regenerates byte-identical, all five diagrams**, which is what the int
   coercion on `box_x` is for.
3. **`verify.py` `load_substance_readings`.** Checked a span only against the
   English rendering, so ten as-printed spans were rejected as "not on that line"
   when that line was the only place they appear. Either side is now enough; the
   span must still be on the line it claims.
4. **`make_visual_evidence.py` drawing caption.** `between_markers` is
   `[before, after]` and the code flattened it and counted, so a lone survivor was
   assumed to be the trailing marker. Both reference cases are missing the LEADING
   marker, so it had never been wrong. Two drawings here sit below [0034] with no
   marker after them, and the reviewer was told to look above a drawing that is
   below. It reads the slot now, and can say "just below".

Also fixed, in this run's own input rather than in code: the p03 vision read wrote
`["[0034]", null]` for two drawings, which is out of the V prompt's schema and
crashed the visual stage. Corrected to the documented prose convention. `[0034]`
must stay in the first slot: `build_enriched.py` anchors the drawing off it, and
prose in both slots makes the drawings orphans emitted at page top, which moves every
line number in the run and invalidates all 198 line keys in the step 6 read plus
every provenance citation. Verified the enriched markdown is byte-identical.

## Hand-authored, with the reasoning

**One SMILES.** `azoisobutyronitrile` = `CC(C)(C#N)N=NC(C)(C)C#N`. AIBN, the Example
1 variant A initiator, 6.6 g. Curated because the patent never draws it and OPSIN
cannot parse the non-systematic name, making it the one named, charged molecule in
the patent with no structure from any other route. Checked both ways before
committing and confirmed with the operator: the SMILES gives C8H12N4, MW 164.21, and
the name is 2,2'-azobis(2-methylpropanenitrile), two (CH3)2C(CN) halves joined by an
azo N=N, which is C4H6N twice plus N2, C8H12N4, MW 164.21. No mole count is printed
for the charge, so no mass balance depends on the formula.

**Three exemptions** via `no_structure_needed`, none of which denotes one molecule:
`3-bromomethylbenzoic acids of the formula II` and `compound of the formula II` are
the same Markush genus the whole patent is about, with R1 fluorine, chlorine or
bromine and R2 (C1-C4)alkyl, so at least twelve compounds; claim 19 claims the genus
and then excludes one member, which is only meaningful because the genus is not that
member. `substituted benzyl bromides` is the product class of the prior-art WO
99/06339 process and the patent names no member of it. The reference states the same
principle for `cyclohexanedione`.

**Zero translations.** There is no Chinese in this document.

## Disagreements recorded, not resolved

- **`components` carries reagents** on 8 of 14 pathway steps, and the A5 audit is
  right that A3 rule 12's prose says reactants only. The reference run's own
  `pathways.json` does the opposite on all 41 of its steps, so A3 was told to follow
  the reference: the artifacts have to be comparable field by field, and matching the
  prose would have made this run the only one shaped differently.
- **The merged Example 1 product carries `role: other`** while holding Example 1's
  mass and yield, with `is_section_product: true` under a `section_label` naming the
  section that excludes it. That is `finalise.py` merging by identifier and taking
  the role from the last-sorting section, which is production's behaviour mirrored on
  purpose and is documented in the A5 prompt's own side-channel note.
- **`compounds-equivalence.json` is empty** while three genus terms name one class
  under a longer and a shorter spelling. The index is structure-keyed and a Markush
  genus has no structure, so it cannot see them.
- **`identifier_type` differs across sections** on 3 identifiers of 44:
  `N-bromosuccinimide` and `bromine` are `trivial_name` in Example 1 and `iupac`
  elsewhere, and `compounds of the formula II` is `other` in the Abstract and
  `formula` in Novel Compounds. The merge takes one value, so `compounds.json` is
  self-consistent and only the stage files disagree.
- **`sodium bisulfate` against `sodium bisulfite`.** Line 98 prints the sulfate in
  the general workup; both worked examples print the sulfite. Bisulfite is what
  quenches bromine. Both are extracted as printed, unmerged, with the conflict and
  the line numbers in `notes`. Neither is corrected.
- **The patent misspells its own reagents.** `N-bromosuccimide` in [0007] and claim
  6 against `N-bromosuccinimide` in [0016] and both examples; `azoisobutyroniltrile`
  in [0027] against the correct spelling in claim 7. Recorded as printed, corrected
  only in the `EN:` reading and in `aliases`.
- **`II g of bromine`**, Example 1 variant B, line 130. Two capital-I letterforms at
  8x, not the digits 11, and restated nowhere. The bromine of that step carries
  `mass_g: null` and no number was substituted. Any mass balance over that step must
  treat the charge as unknown. The WO family member would probably settle it and was
  deliberately not consulted.
- **A5's four audits ran against the artifacts as they stood before the fixes above.**
  Their findings are what produced most of those fixes, so the reports and the gold
  no longer describe the same bytes. That is the normal audit-then-fix cycle and
  `input/PROMPT-CORRECTIONS.md` section 11 lists which findings were acted on and
  which were recorded and left.

## Both examples' arithmetic closes, and the yields are purity-corrected

Checked independently by the vision pass, by A2, and again by the A5 audit of
`reactions.json`, each without seeing the others' conclusion.

- Example 1: 100 g of C9H9ClO4S, MW 248.68, is 0.40213 mol; 121.3 g at 96% purity is
  116.45 g of C9H8BrClO4S, MW 327.58, which is 88.40% against the printed 88.4%.
- Example 2: 20 g of C10H11ClO4S, MW 262.70, is 0.07613 mol; 28.2 g at 88% is 24.82 g
  of C10H10BrClO4S, MW 341.60, which is 95.42% against the printed 95.6%.
  Uncorrected it would be 108.4%, which is impossible, so the printed yields are
  purity-corrected and the two examples are consistent with each other.

No `mass_balance_implausible` or `molar_mass_inconsistent` is raised anywhere, and
their absence is a result rather than an oversight. The only `validation_flag` in the
run is `no_conditions`, on the 5 records that state a transformation with no
conditions at all: the abstract, the three prior-art disclosures, and the summary's
variant A.

The working itself lives in the provenance `arithmetic_check` sidecars and NOT in the
records, because A5 check 2 lists molecular weights and formulae among the things
this annotation may not contain, and it had leaked into `notes` on five records.

## Where the run ends

All 18 stages run. `run_pipeline.py` reports `pipeline complete` with no gate
failure, the manifest is clean, and the deliverable matches `output/` on all 11
copied artifacts. Both coverage gates pass, the `visual` gate passes, and the
`verify` grounding gate passes: every checkable number and quote is on a line its own
record cites.

`selfcheck` reports **37 pass, 1 warn, 0 fail**. The warn is that
`no_conditions` is an annotation flag family with no counterpart engine check to
compare against, which is a property of the engine rather than of this annotation.

The review census is **47 claims, 6.8 minutes of the 15.0 the protocol pins**, so
this patent does not hit the wall that blocked row 9. It has two examples where
CN112645853A has twenty, which is the whole difference.

Two grounding failures were fixed rather than argued with, and both were real: a
`time_h` of 5.0 that was 1+1+1+2 summed and appears on no line, now the printed 2.0
with the interval structure in `notes`; and a line-broken title stem that no record
held, now an alias on the product it belongs to. The same hole existed silently in
Example 1, where no record cited the title line at all, and was closed too.
