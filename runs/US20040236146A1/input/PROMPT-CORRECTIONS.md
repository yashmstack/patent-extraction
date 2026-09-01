# Prompt corrections for US20040236146A1

`render_prompts.py` substitutes the patent id but not the patent-specific prose, so
several rules in the rendered A1, A2 and A3 prompts assert things that are true of
the reference patent CN104292137A and false here. Where this file and a rendered
prompt disagree, **this file wins**. Everything not listed here stands unchanged.

Recorded as an input so the run is reproducible and so the next patent's owner can
see that the same treatment is owed.

## What this document actually is

A four page US patent application publication, **in English**, born digital with an
OCR text layer. `Method for producing 3-bromomethylbenzoic acids`, Bayer
CropScience, published 2004-11-25, abandoned.

One transformation: benzylic bromination of a 2-halo-3-methyl-4-alkylsulfonyl
benzoic acid to the 3-bromomethyl compound, by either

- **variant A**, N-bromosuccinimide plus a radical initiator, or
- **variant B**, elemental bromine plus photolamp irradiation.

Two worked examples. Example 1 makes the methylsulfonyl compound and runs both
variants; Example 2 makes the ethylsulfonyl homologue and runs variant A only.

## 1. There is no Chinese in this document

Every rule about Chinese being authoritative, about machine translation garbling
chemistry, and about following the Chinese where it disagrees with the English,
has no subject here. Specifically A1 rules 2, 6, 20 and 21, A2 rule 27's
`translation_conflict`, and every worked example in those rules
(`1,2-二氯乙烷` against `1,2-二氯甲烷`, `环己二酮`, `氰基丙酮` against `丙酮氰醇`)
describe the reference patent and not this one.

**The analogue that does apply.** Each source line appears twice in the enriched
markdown: the line **as printed**, and a `> EN:` line under it. Here the `> EN:`
line is not a translation. It is the vision pass's normalisation of the same
English, and it silently repairs printing errors. So:

- the as-printed line is the document and is authoritative
- the `> EN:` line is a reading of it, and where the two differ that difference is
  a **finding about the patent**, not about the annotation
- never let the `> EN:` line be the only thing a record rests on

## 2. Naming: one identifier per substance, and it is a form this patent prints

This patent misprints chemical names, repeatedly and inconsistently, and the same
substance is printed several ways within one paragraph. Left alone that produces
one molecule under four join keys, which is the failure
`contracts/DUPLICATE-FAMILIES.md` measures on the reference run.

**Rule for this run.** `identifier` is the corrected form, and the corrected form is
always **a spelling this document itself prints somewhere**. Nothing is invented.
Every as-printed variant goes in `aliases[]`, and `notes` names each variant and the
line it is printed on. This is A1 rule 6's resolve-and-keep-the-original applied to
a misprint instead of to a translation.

Use exactly these strings, in every section, so the artifacts join:

| identifier | as-printed variants to carry in aliases |
|---|---|
| `2-chloro-3-methyl-4-methylsulfonylbenzoic acid` | `2-chloro-3-methyl4-sulfonylmethylbenzoic acid` (L122), `2-chloro-3-methyl-4-sulfonylmethylbenzoic acid` (L130) |
| `3-bromomethyl-2-chloro-4-methylsulfonylbenzoic acid` | `3-bromomethyl-2-chloro4-methylsulfonylbenzoic acid` (L55, L100, L110), `3-bromomethyl-2-chloro4-methylsulfonyl-benzoic acid` (L124), `3-bromomethyl-2-chloro-4-methylsulfonyl-benzoic acid` (L191) |
| `2-chloro-3-methyl-4-ethylsulfonylbenzoic acid` | `2-chloro-3-methyl-4-sulfonylethylbenzoic acid` (L140) |
| `3-bromomethyl-2-chloro-4-ethylsulfonylbenzoic acid` | (printed correctly at L140) |
| `N-bromosuccinimide` | `N-bromosuccimide` (L69, L154) |
| `azoisobutyronitrile` | `azoisobutyroniltrile` (L122) |
| `methyl 2-chloro-3-methyl-4-methylsulfonylbenzoate` | (printed correctly, L55) |
| `methyl 3-bromomethyl-2-chloro-4-methylsulfonylbenzoate` | (printed correctly, L55) |

`sulfonylmethyl` and `sulfonylethyl` name a divalent linker and cannot be a terminal
ring substituent, so they are transpositions of `methylsulfonyl` and `ethylsulfonyl`.
The patent settles this itself, twice: the Example 1 and Example 2 titles print the
correct order, and the printed mass, purity and yield of each example close only for
the correctly ordered compound. Say so in `notes`; do not leave it implied.

Everything else keeps the name the patent prints: `chlorobenzene`, `acetonitrile`,
`methylene chloride`, `chloroform`, `carbon tetrachloride`, `1,2-dichloroethane`,
`bromine`, `dibenzoyl peroxide`, `water`, `sodium bisulfite`, `sodium bisulfate`,
`ethyl acetate`, `butyl acetate`, `diethyl ether`, `heptane`.

## 3. There is no drawn reaction scheme anywhere in this document

Every `[IMAGE_EXTRACT: ...]` span in this patent is a **single Markush structure**,
formula I or formula II, with variable R1 and R2, and every one carries
`{"molecules": []}` because the vision pass correctly refused a SMILES for a generic.

So these do not apply and **must not** be raised:

- A2 rules 5a, 5c, 5e, 5f and 5g about scheme arrows, reagents above against below
  an arrow, and overview schemes
- the `validation_flags` `drawing_text_conflict`, `reagent_drawn_not_written`,
  `reagent_written_not_drawn` and `route_attribution_unclear`
- A2 rule 5e's account of a scheme that contradicts its own prose. That is the
  reference patent. This document has no scheme to contradict anything.

A1 rules 4a to 4f likewise have no work to do: no span carries a SMILES, so nothing
goes into `aliases[]` from a drawing and no `SMILES_MISMATCH` is possible.

Do record, in `notes` on the affected records, that the drawings are Markush
generics and that this is why no structure reached the record.

## 4. Step markers

A0 rules 5 and 6 describe experimental steps marked `N、<compound name>`. This
patent has no such markers. Its structure is a centred `EXAMPLE N` heading, a
centred `Preparation of <name>` title, and `Process Variant A):` or
`Process Variant B):` subheadings. In Example 2 the variant subheading is printed
**before** the preparation title, the reverse of Example 1.

Variant A and variant B of Example 1 are **alternatives, not sequential steps**.
Neither is the other's precursor and `precursor_step` is null on both. The same
holds between Example 1 and Example 2: different substrates, no material flows
between them.

## 5. Arithmetic: check it, and expect it to close

A2 rules 27 and 29 cite the reference run, where printed mass and mole pairs
repeatedly implied the wrong molecular weight. **That is not the case here.** Both
examples state a purity and both yields reconcile once the purity is applied:

- Example 1: 121.3 g at 96% is 116.4 g of C9H8BrClO4S, MW 327.6, against 100 g of
  C9H9ClO4S, MW 248.7, giving 88.4% as printed
- Example 2: 28.2 g at 88% is 24.8 g of C10H10BrClO4S, MW 341.6, against 20 g of
  C10H11ClO4S, MW 262.7, giving 95.4% against the 95.6% printed

Do the arithmetic yourself and report what you find. A2 rule 29's second half is the
operative one here: **do not invent a defect.** If a step closes, raise nothing.

One quantity genuinely cannot be checked, and it is not a defect in this annotation:

- **Example 1 variant B prints `II g of bromine`**, two capital-I letterforms, not a
  number. The vision pass examined it at 8x and it is not the digits `11`. It is
  restated nowhere. Record the bromine of that step with `mass_g: null`, put the
  as-printed string in `notes`, and do **not** substitute 11. Any mass balance over
  that step must treat the charge as unknown.

Variant B of Example 1 also isolates nothing: it reports only an HPLC composition,
87% product and 10% reactant. So it has no product mass, no yield and no purity of
an isolated solid. That is the document, not a gap.

## 6. Null shapes, which have bitten this pack before

Where nothing is stated, emit `"quantity": null`, `"nmr": null`,
`"melting_point": null` - **not** an object whose members are all null.

`finalise.py`'s compound merge replaces a populated value wholesale and an
all-null object is not empty, so a null-filled `quantity` arriving from a
later-sorting section erases a real mass extracted from an earlier one. On the
previous run in this pack that silently emptied every mass in the merged gold.
A1 rule 17 states the rule for characterisation fields; it applies to `quantity`
too.

## 7. Two things about the claims

- Claims 1 to 5 are printed as `1-5 (Canceled)` and have no text. They are not
  records.
- Claim 20 restricts R2 to `(C2)alkyl`, read off the pixels at 10x. The OCR text
  layer renders it `(C.)alkyl`, which is damage. Claim 19 gives `(C1-C4)alkyl` and
  excludes the R2 = methyl compound, so `(C2)alkyl` in claim 20 is consistent with
  the document and with Example 2.

## 8. A radical initiator is `reagent`, not `catalyst`

Added after the first A1 sweep, which split three ways on this and produced one
substance with two roles. Recorded here rather than settled in a side conversation,
and the two sections that disagreed were re-run against it.

`azoisobutyronitrile` and `dibenzoyl peroxide` take `role: "reagent"` and
`compound_class:reagent` in every section of this patent.

The reason is the prompt's own definition. A1 rule 9 defines `catalyst` as "present
sub-stoichiometrically and not consumed". A radical initiator is consumed: it
fragments to give the chain-carrying radical, which is what initiating means. This
patent supplies the evidence itself, at [0033], where dibenzoyl peroxide is charged
0.7 g at the start and then **three further times, 0.7 g each, at one hour
intervals**. A species that has to be replenished four times through one reaction is
not a catalyst under any reading.

`reagent`, "transforms the substrate but is not the carbon skeleton source", is the
closest value the closed list holds. There is no `initiator` value; that absence is
a limitation of the vocabulary and is worth saying rather than papering over.

## 9. Class terms drop the article

Also added after the first sweep. `Background` recorded the class term as
`radical initiator` and `Summary of the Invention` as `a radical initiator`, which
is one class under two join keys and the same fragmentation
`contracts/DUPLICATE-FAMILIES.md` measures on the reference run.

**A class term's identifier is the bare noun phrase, with no leading article and no
attributive fragment carried in from the sentence.** So `radical initiator`, not
`a radical initiator` and not `radical initiator-induced`. The form with the article
goes in `aliases`. This matches how the same sweep already handled
`oxidizing agent`, whose line prints `an additional oxidizing agent`.

## 10. A2 rulings, after the first reaction sweep

Three things the seven A2 sections split on. Settled here and the affected sections
re-run, for the same reason as sections 8 and 9: a gold set in which one fact is
recorded two ways measures the annotator, not the patent.

### 10a. One `step_role` per record, and a one-step route is `final_step`

The first sweep put both `step_role:first_step` and `step_role:final_step` on the
Abstract and Claims records, `first_step` on Background, Process Conditions and
Summary, and `final_step` on the two Examples. All for the same one-step
transformation.

The category is single-valued: the reference run carries exactly one `step_role`
on each of its 33 reactions. So:

- a chain of ONE step takes `step_role:final_step`
- the first step of a longer chain takes `first_step`, the last `final_step`, and
  anything between `intermediate_step`

`final_step` for the one-step case because the category exists to locate a step
within a chain, and `first_step` on a route that is over implies something follows.
This is a convention, not a fact: the step really is both, and the field holds one
value. Every affected record says so in `notes`. It is another instance of
`contracts/SINGLE-VALUED-FIELDS.md`, and naming it is the point.

Under this rule only `Background_Step 2` takes `first_step`, being the ester
bromination that the hydrolysis at `Background_Step 3` consumes.

### 10b. No seventeenth tag category

The first Background pass emitted `route_attribution:prior_art`, which is not one of
A2 rule 26's sixteen categories and appears nowhere in the reference run. The
instruction that produced it was mine and it was wrong: the closed list has no slot
for attribution.

Prior-art attribution stays where the schema can hold it, in `notes` on every record,
and it is already carried structurally by `section_type: "background"`. Do not invent
a category to hold a fact the vocabulary cannot express; record the gap instead.

### 10c. `radical initiator` was a real A1 miss in Process Conditions

`Process Conditions_Step 1` raised `a1_missing_compound` and it was correct. [0016]
charges "a compound of the formula I with N-bromosuccinimide (NBS) and radical
initiator in solvent", and the bare class term is printed three times in that
section, but A1 emitted only its named members. Background and Summary both record
the class.

A1 `process-conditions` is re-run to hold it, and A2 `process-conditions` is re-run
after, so the flag clears because the miss is fixed rather than because it was
waved away. This is A2 rule 7 working exactly as designed and it is worth saying
that the flag found something.

### Not changed: `compounds[].quantity` shape on reaction records

Section 6's `quantity: null` rule is about A1 compound records, where
`finalise.py`'s merge replaces a populated value wholesale. Reaction records are not
merged by identifier, and every access site in `verify.py` reads
`c.get("quantity") or {}`, so a null and an all-null object are indistinguishable
downstream. Both shapes are schema-valid and both appear in this run. Recorded rather
than normalised, because normalising it would change bytes without changing meaning.

## 11. Acting on the A5 audits

The four adversarial audits ran against the finalised artifacts in fresh contexts
that were told not to open the stage folders, this file, or any notes. They returned
52 findings: 1 critical, 17 major, 34 minor. What was done with each class is here so
that a reviewer can see which findings changed the gold and which were recorded and
left, rather than having to infer it.

### Acted on

- **The critical one is a pipeline bug, not an annotation defect.**
  `finalise.py`'s `ASSIGNEE_TYPE` had no key for `multinational_corp`, `sme` or
  `consortium`, three of the six values `biblio.schema.json` now allows, and its
  lookup defaulted to `sme`. A correct biblio shipped Bayer CropScience AG as a small
  enterprise. Fixed with the operator's explicit approval by widening the map to
  identity for production's six, keeping the older biblio words as aliases. The stale
  comment in `biblio.schema.json` claiming finalise copies the field with no mapping
  was corrected in the same change.
- **Molecular formulae and molecular weights in `notes`.** Five records carried
  `C9H8BrClO4S`, `MW 327.6` and derived masses that the patent never prints. A5 check
  2 lists formulae and molecular weights among the things this annotation may not
  contain, and A1 rule 22 forbids numbers in notes that are not in the text. The
  working moved to the provenance `arithmetic_check` sidecar, which exists for it and
  never enters an artifact; the notes now say only that the printed yield reproduces
  once purity is applied.
- **`dibenzoyl peroxide` `mass_g: 2.8`** was 0.7 times four, a number on no line, and
  `verify.py` would have read it as the hallucination signal. A1 rule 12 forbids
  computing a quantity. Now 0.7, the charge the text states, with the four-portion
  structure in words in `addition_profile` and `notes`, and the schema limitation
  named. My own instruction to record the total is what produced it.
- **Process Conditions carried no solvent.** Both its records emitted
  `solvent_class` tags derived from solvents that appeared in no `compounds[]` entry,
  while the parallel Claims records carry their equally alternative claimed solvents.
  [0014] names six and says which are advantageous for each variant. Re-run to hold
  them.

### Recorded and not changed, with the reason

- **`components` carries reagents** (pathways, 8 of 14 steps). A3 rule 12's prose says
  reactants and not reagents. The reference run's `pathways.json` does the opposite on
  all 41 of its steps: `components` is `reactant_names` plus `product_name`, key
  reagent included. A3 was told to follow the reference, because the artifacts have to
  be comparable field by field and matching the prose would have made this run the
  only one shaped differently. The finding is correct about the prose and is kept.
- **The merged Example 1 product carries `role: other` with Example 1's mass and
  yield**, and `is_section_product: true` under a `section_label` naming the section
  that excludes it. This is `finalise.py`'s merge taking the role from the
  last-sorting section, which is production's behaviour mirrored on purpose and is
  documented in the A5 prompt's own side-channel note. Not repairable from a stage
  file without making one section lie about its own reading.
- **`compounds-equivalence.json` is empty** while three genus terms name one class
  under a longer and a shorter spelling. The equivalence index is structure-keyed and
  a Markush genus has no structure, so it cannot see them. A real limitation, and the
  three pairs are named in `RUN-NOTES.md`.
- **`identifier_type` differs across sections** on three identifiers of 44:
  `N-bromosuccinimide` and `bromine` are `trivial_name` in Example 1 and `iupac` in
  the four other sections that hold them, and `compounds of the formula II` is `other`
  in the Abstract and `formula` in Novel Compounds. The merge takes one value, so
  `compounds.json` is self-consistent and only the stage files disagree. Left, because
  re-running three sections to align one descriptive field buys less than the record
  of the disagreement does.
- **`light_source.type` is `other`, `photolamp` and `lamp`** across three records for
  the one photolamp. `other` is the only one of the three in the schema enum. Left and
  recorded; the two out-of-enum values are a real vocabulary defect the reviewer
  should see.
- **`time_h: 5.0` on Example 2 WAS left, and then the verify gate rejected it.**
  It summed the printed 1, 1, 1 and 2 hour intervals. The argument for leaving it was
  that a duration field is a total by nature where a charge field is not, and it was
  recorded here as arguable. The grounding check then said the number 5 is on none of
  the nine lines that record cites, which is the same objection the A5 audit had made
  and is decisive: a computed value in a numeric field is the hallucination signal
  whatever the field means. It is now **2.0**, the printed further 2 h after the last
  initiator portion, with the 1, 1, 1, 2 structure in `notes` and in the initiator's
  `addition_profile`, and the total moved to the provenance `arithmetic_check`. That
  also makes it agree with `Example 1_Step 2`, which the A5 pathways audit had flagged
  as keeping a different clock for the same kind of step.

## 12. `light_source.type` is `other`, and the printed word goes in `notes`

`schemas/validate.py` rejected three reaction records: `light_source.type` was
`lamp` on `Example 1_Step 2` and `photolamp` on `Process Conditions_Step 2` and
`Summary of the Invention_Step 2`. The reaction schema's enum is
`LED | UV | mercury_lamp | sunlight | tungsten | fluorescent | other | null`, which
has no value for a photolamp, and `Claims_Step 2` had already chosen `other`.

So: **`other` on all four**, with the word the patent actually prints kept in `notes`
on each. `power_w` still carries the 300 W that Example 1 variant B states; that is a
number the document prints and the schema holds it.

The A5 audit of `reactions.json` raised the three-way split as a minor vocabulary
finding before validate did, and validate then made it fatal. Worth noting which
found it first: the audit, on its own reading, one stage earlier.
