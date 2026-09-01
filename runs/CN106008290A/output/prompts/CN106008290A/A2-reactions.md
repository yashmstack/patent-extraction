# A2 - Reactions

**Artifact produced:** `output/reactions.json` (array of `ReactionRecord`)
**Input:** one section of `input/CN106008290A-enriched-numbered.md` + its A0 entry
+ the A1 compounds for that section + the running registry of reactions already
annotated in earlier sections
**Runs:** once per section where A0 set `contains_procedure = true`.

This pass merges LiteratureIQ's R1 (step boundaries), R2 (per-step detail) and R3
(classification, linkage, tags) into one call. The rules from all three are kept.
Merging is safe here because the section fits in context whole; splitting exists in
production to bound token cost, not to improve accuracy.

---

You are a chemistry patent analyst building a **reference (gold) annotation** of the
reactions in one section. An automated extractor will be scored against this, so a
missed step is a recall failure and an invented step is a precision failure.

## Input

PATENT_ID: `CN106008290A`
SECTION_LABEL: `{SECTION_LABEL}`
SECTION_TYPE: `{SECTION_TYPE}`
LINES: `{START_LINE}`-`{END_LINE}`
A0 said this section contains `{ESTIMATED_STEPS}` steps.

SECTION TEXT (line-numbered enriched markdown - Chinese is authoritative, `EN:` lines are a convenience, `[IMAGE_EXTRACT: ...]` spans are machine-read structures):
---
{SECTION_TEXT}
---

COMPOUNDS ALREADY ANNOTATED FOR THIS SECTION (from A1) - use these identifiers
verbatim so the two artifacts join:
---
{A1_COMPOUNDS}
---

PRIOR-SECTIONS REACTION REGISTRY (product of every step annotated so far, for
cross-section linkage):
---
{PRIOR_REGISTRY}
---

## Rules

### Step boundaries
1. Split the section into steps. A new step begins at a new transformation with its
   own charge of starting material and its own workup. In this document, each
   `N、<compound name>` marker starts a step.
2. `step_index` is sequential from 1 within the section, in document order.
   `step_label` is the document's own marker, e.g. `"Step 1"` where the text reads
   `1、`. Keep the Chinese heading in `notes` if it carries information the label
   does not.
3. `reaction_id` is `"{section_label}_{step_label}"`, e.g. `"Example 1_Step 1"`.
   This is the human-readable handle. Do not emit `id` or `reaction_uuid` - they are
   computed downstream (see Output).
4. If your step count differs from `{ESTIMATED_STEPS}`, that is allowed, but say why
   in the step's `notes`. A silent disagreement between A0 and A2 is the single most
   likely place for a recall miss to hide.
5. **One-pot detection.** When a single numbered step describes two or more
   sequential transformations with no workup between them, keep it as ONE record,
   set `is_one_pot: true`, and list the transformations in document order in
   `one_pot_steps`. Assign `reaction_class` from the FINAL transformation.
   Find these by reading for the absence of a workup between transformations. Do
   not assume a count: a route that isolates every intermediate has none, and a
   route whose selling point is that it does not isolate them has several.

### Reading the drawings
5a. `[IMAGE_EXTRACT: {"reactions":[{step_id, reactants[], conditions[], products[]}]}]`
    is a **reaction scheme** read off the page. Each `step_id` is one arrow, and the
    arrow's reagents arrive as `conditions[].text`. Use it for three things:
    - to corroborate step boundaries you derived from the prose
    - to catch reagents drawn on an arrow but never written in the procedure
    - to establish product-to-reactant connectivity, which is often clearer in the
      drawing than in the text
5b. `[IMAGE_EXTRACT: {"molecules":[...]}]` is a single structure. In this document
    one usually precedes each experimental step and depicts that step's product.
    Treat it as evidence for `product_name`, and cross-check it against the name the
    text gives.
5c. **The scheme and the prose can disagree.** Check whether they do here before
    assuming either way. When a reagent appears in one and not the other, or a drawn
    structure contradicts a written name, keep what the **prose of that step** says
    in the structured fields, and raise `drawing_text_conflict` in
    `validation_flags` with both readings in `notes`. Never silently merge them, and
    never let the drawing overwrite a stated procedure. Where they agree, say so in
    `notes` and raise nothing: a flag on a scheme that matches its prose is a false
    finding, and a reviewer sent to look at one stops trusting the next.
5d. **A scheme outside an experimental section is an overview, not a procedure.**
    It carries connectivity and reagents but no charges, no conditions and no
    yields. Annotate its arrows as reactions - production's passes run over every
    section type and would too - but:
    - one record per arrow, `step_index` in drawing order
    - `scale: "not_specified"`, and expect `no_conditions` in `validation_flags`
    - never merge it with, or renumber it against, the experimental steps. An
      overview scheme and `Example 1` are different sections and their step
      numbering is independent.
    - state in `notes` which section the scheme belongs to and that it is an
      overview
5e. **Attribution: whose route is the scheme?** Record it, and do not resolve what
    the document leaves open.
    - A scheme under `背景技术` / `background` is prior art.
    - A scheme under `发明内容` / `summary_of_invention`, `beneficial_effects`, or
      standing at the head of the specific-embodiments region is normally the
      invention's own route.
    - **The vision pass may have marked a scheme `presented_as: "unclear"`. When it
      has, that is a finding, not a gap for you to close.** Do not pick a side.
      Write both readings into `notes`, raise `route_attribution_unclear` in
      `validation_flags` on every record from that scheme, and move on.
    The reference run met exactly that case: its scheme used a reagent the text said
    the invention replaced, contained a step the text said the invention eliminated,
    and also used a reagent the text claimed as the invention's improvement, so it
    was internally inconsistent with the prose around it. That is a description of
    that patent, not of yours. Decide from your own document and record what you
    find, either way. Mislabelling prior art as the invention's route, or quietly
    deciding which it "must" be, is the most damaging single error available here.
5f. **A section may contain both prose steps and an overview scheme.** A
    `Summary of the Invention` commonly does: it recites the route in words across
    its numbered paragraphs and then draws it. Do not assume they are the same route
    and do not collapse them into one set of records, even where they look identical.
    Emit **both**, kept apart by `step_label`:
    - prose steps get `step_label: "Step N"` and `reaction_id
      "<section_label>_Step N"`
    - scheme arrows get `step_label: "Scheme Step N"` and `reaction_id
      "<section_label>_Scheme Step N"`, numbered in drawing order
    Then, for every scheme record whose transformation has a prose counterpart that
    contradicts it, raise `drawing_text_conflict` and name the counterpart in
    `notes`. The step counts need not match, and where they do not that difference
    is itself a finding: say in `notes` which transformation the prose has and the
    drawing lacks, or the reverse.
5g. Where a drawn arrow has **no reagent at all**, or a chemical change occurs
    between two drawn structures with **no arrow between them**, that is still a
    transformation and still gets a record. Set `reaction_class` from the structural
    change, leave the reagent fields null, and raise `no_conditions`. Silently
    skipping an unlabelled arrow is a recall miss.
5h. `procedure_text` must have every `[IMAGE_EXTRACT: ...]` span **stripped out**.
    Production does this at persistence time via `ProcedureTextSanitizer`, and
    leaving the spans in would make every `procedure_text` diff against production.

### Compounds on the reaction
6. `compounds[]` carries the full per-compound detail for this step. Each entry:
   ```
   { "identifier": string, "role": string, "is_product": bool,
     "quantity": { "mass_g": float, "volume_ml": float, "mmol": float,
                   "equivalents": float, "yield_pct": float },
     "addition_profile": string|null, "ms_mz": float|null, "ms_type": string|null,
     "purity_pct": float|null, "purity_method": string|null }
   ```
   `addition_profile` records how the reagent was introduced: `"dropwise over
   50 min, below 10 C"`, `"added in one portion"`, `"added as a mixture with
   triethylamine"`. This document is full of `滴加` (dropwise) additions - capture
   them, they are process-relevant.
7. Identifiers must match A1 exactly. If this step uses a compound A1 did not
   record, that is an A1 recall miss - still emit it here and flag
   `"a1_missing_compound"` in `validation_flags`.
8. Flatten the same information into `reactant_names`, `product_name`,
   `product_yield_pct`, `product_purity_pct`, `product_ms_mz`, `product_ms_type`,
   `product_purity_method`. Leave `reactant_smiles`, `smiles_source`,
   `product_smiles`, `product_smiles_source` and `canonical_rxn` as null - structure
   resolution is a separate enrichment stage and inventing SMILES here would poison
   the gold set. This holds **even though the drawings give you SMILES**: the SMILES
   belongs on the compound record's `aliases[]`, which A1 owns, not on these fields.

### Conditions
9. Fill the structured `conditions` block. Never invent a condition. Never carry a
   condition from one step to another unless the text says to.
   - `temperature.type` is `exact` | `range` | `room_temperature` | `not_specified`.
     `冷却至5℃` -> `{"type":"exact","value_c":5.0}`.
     `15-20℃` -> `{"type":"range","min_c":15.0,"max_c":20.0}`.
     `室温` / "room temperature" -> `{"type":"room_temperature"}` with `value_c` null.
     `回流` / "reflux" is NOT a temperature - it is a heating method. Put
     `heating_method: "reflux"` and leave temperature `not_specified` unless a
     number is given.

     **An addition temperature is still the step's temperature when it is the only
     one printed.** `在75～80℃滴加双氧水` gives
     `{"type":"range","min_c":75.0,"max_c":80.0}` AND the phrase in that reagent's
     `addition_profile`. The two are not alternatives. Recording it only in
     `addition_profile` leaves `not_specified` on a step whose temperature the
     patent states, and where four worked examples repeat one procedure it makes
     them incomparable: three carry a range and the fourth reads as though the
     temperature were never given.

     **A one-pot step takes its temperature from the FINAL transformation**, the
     same one rule 5 takes `reaction_class` from, and names the others in `notes`.
     A step that etherifies at 0 to 5 C and then hydrolyses at 70 to 75 C records
     70 to 75. Choosing per step is how two examples of one procedure end up
     disagreeing about which number describes them.
   - `time_h` in hours. `10h` -> 10.0. `50min` -> 0.83 only when the 50 min is the
     reaction time; a dropwise addition time belongs in that compound's
     `addition_profile`, not in `time_h`.
   - `pressure.type` is `atmospheric` | `reduced` | `elevated` | `vacuum` |
     `not_specified`. `减压蒸出` / "distilled off under reduced pressure" is a workup
     operation, so it sets `workup.concentration_method`, not reaction pressure.
   - `atmosphere` - only when stated. A drying tube (`干燥管`) means moisture
     exclusion, so `atmosphere: "dry"` with the phrase in `notes`. Do not write
     `nitrogen` unless nitrogen is named.
   - `reactor_type` - `四口反应瓶` is `"four-necked flask"`. Record the volume in
     `notes` (`500 ml`), not in a numeric field, since no field holds it.
   - `stirring.type` is `magnetic` | `mechanical` | `overhead` | `vortex` |
     `shaker` | `none`. `装有搅拌器` names a stirrer without saying which - use
     `mechanical` only if the text says so, otherwise leave the object null and note
     that a stirrer is fitted.
   - `concentration` - `15％的次氯酸钠溶液` -> `{"value":15.0,"unit":"%",
     "reagent":"sodium hypochlorite","text":"15% sodium hypochlorite solution"}`.
   - `ph_value` / `ph_target_stage` - only when a pH number is given.
   - `light_source`, `cooling_method` - null unless stated.
10. `conditions_inherited` is true only where the step says its conditions follow
    another step. Default false.

### Workup and purification
11. `workup` is structured:
    ```
    { "steps": [string], "quenching_agent": string|null,
      "extraction_solvent": string|null, "extraction_count": int|null,
      "extraction_volume_ml": float|null, "washes": [string]|null,
      "drying_agent": string|null, "filtration": string|null,
      "concentration_method": string|null, "ph_target": float|null }
    ```
    `steps` is the ordered workup narrative in short phrases. `将反应物倾入冰水中`
    -> quenching_agent `"ice water"`. `硫酸镁干燥` -> drying_agent
    `"magnesium sulfate"`. `减压蒸出甲醇` -> concentration_method
    `"distillation under reduced pressure"`.
12. `purification` is free text for the isolation method: `"recrystallised from
    ethanol"`, `"washed with ethyl acetate"`. Null when the product is used crude.
13. `process_control` when the text names in-process monitoring:
    `LC跟踪(液相色谱)至反应完全` ->
    `{"method":"hplc","criterion":"complete conversion"}`.
14. `byproduct_recovery` only when the text describes recovering or reusing a
    by-product. Otherwise null.
15. `safety_notes` - a list of safety-relevant statements **present in the text**.
    Do not add your own hazard assessment; that is A5's job and it goes elsewhere.
16. `molar_ratio_text` - the stoichiometry as the text words it, when it words it.

### Classification
17. `reaction_class`, exactly one of:
    `suzuki_coupling` | `heck_reaction` | `buchwald_hartwig` | `negishi_coupling` |
    `sonogashira_coupling` | `other_cross_coupling` | `amide_bond_formation` |
    `acylation` | `ester_formation` | `n_alkylation` | `nucleophilic_substitution` |
    `electrophilic_substitution` | `halogenation` | `n_oxidation` | `oxidation` |
    `reduction` | `hydrolysis` | `protection` | `deprotection` | `cyclisation` |
    `elimination` | `addition` | `salt_formation` | `resolution` |
    `recrystallisation` | `catalyst_preparation` | `heterogeneous_catalysis` |
    `formulation` | `biological_assay` | `other`.
    If it cannot be determined with reasonable confidence, use `other` and explain
    in `notes`. Do not guess.
18. `reaction_class_confidence` is `high` | `medium` | `low`.
19. `named_reaction` - the canonical name when one plainly applies
    (`"Friedel-Crafts acylation"`, `"Fischer esterification"`, `"haloform
    reaction"`, `"Williamson ether synthesis"`, `"Wohl-Ziegler bromination"`).
    Null when no widely accepted name fits. Do not stretch for one.
20. `mechanism_type`, exactly one of: `radical` | `ionic` | `pericyclic` |
    `photochemical` | `catalytic` | `concerted` | `not_determinable`.
    A peroxide initiator with bromine at reflux is `radical`. A Lewis acid
    promoted arene substitution is `ionic`.
21. `scale` from the limiting reagent charge: `micro` (<1 g) | `lab` (1-100 g) |
    `pilot` (100 g - 10 kg) | `production` (>10 kg) | `not_specified`.
22. `selectivity` - populate only from what the text states. This document reports
    no ee/de/dr, so expect null. Regiochemistry that is implied by the product name
    is not a stated selectivity; leave `regio` null unless the text discusses it.

### Linkage
23. `precursor_step` - the step whose product is a reactant here.
    - Within this section: the bare `step_label`, e.g. `"Step 1"`.
    - From an earlier section: `"<section_label>::<step_label>"`.
    - Null for the first step of the synthesis, or when no precursor can be found.
24. `linkage_confirmed` is true only when the precursor's product identifier
    actually matches a reactant identifier here, or the text explicitly refers back
    ("上述化合物", "the product of step 3"). Name similarity alone is not
    confirmation.
25. `cross_reference_unresolved` is true when the step refers to material or
    conditions from elsewhere that you could not locate.

### Tags
26. Emit `tags` as unique lowercase snake_case `"category:value"` strings across
    these 16 categories. Skip a category rather than guess.
    `transformation` (e.g. `sulfonylation`, `acylation`, `bromination`,
    `esterification`, `etherification`, `hydrolysis`, `oxidation`,
    `rearrangement`) | `mechanism` | `named_rxn` | `analytics` | `selectivity` |
    `scale` | `atmosphere` | `solvent_class` (`aprotic_polar` | `aprotic_apolar` |
    `protic` | `aqueous` | `hydrocarbon` | `halogenated` | `ionic_liquid` | `neat` |
    `other`) | `catalyst_class` (`palladium` | `nickel` | `copper` | `rhodium` |
    `ruthenium` | `iron` | `platinum` | `iridium` | `gold` | `enzyme` | `base` |
    `acid` | `none`) | `workup_type` (`aqueous_extraction` | `filtration` |
    `distillation` | `chromatography` | `crystallisation` | `trituration` |
    `precipitation` | `none`) | `purification` (`column_chromatography` |
    `recrystallisation` | `distillation` | `trituration` | `sublimation` | `hplc` |
    `none`) | `green_chemistry` | `safety` (`cyanide_handling` | `hf_handling` |
    `pyrophoric_reagent` | `high_pressure` | `cryogenic` | `exothermic` |
    `gas_evolution`) | `step_role` (`first_step` | `intermediate_step` |
    `final_step`) | `linkage` (`standalone` | `precursor_linked` |
    `cross_section_linked`) | `is_one_pot` (`true` | `false`).

### Validation - flag, never fix
27. Run these checks on every record and record failures in `validation_flags`:
    - `missing_product` - no compound with `is_product: true`
    - `missing_reactant` - no compound with `role: reactant`
    - `no_conditions` - every condition field null and `conditions_inherited` false
    - `no_procedure_summary` - `procedure_summary` empty
    - `cross_reference_unresolved`
    - `conditions_unresolved` - claims inherited conditions but the referenced
      record was not found
    - `a1_missing_compound` - rule 7
    - `mass_balance_implausible` - the stated product mass exceeds what the stated
      input moles could give, or the stated mass and the stated yield disagree.
      Check this on every step, and check it by arithmetic rather than by
      expectation. Where it closes, raise nothing. Where it does not, raise the flag,
      record the numbers as printed, and change nothing. In the reference run the
      printed mass/mole pairs repeatedly implied a molecular weight lower than the
      compound named; that is a fact about that patent and tells you nothing about
      whether yours closes.
    - `scale_discontinuity` - this step's input charge does not match the previous
      step's output
    - `translation_conflict` - Chinese and English name different compounds
    - `drawing_text_conflict` - the drawn scheme and the written procedure disagree
    - `reagent_drawn_not_written` - a reagent appears on an arrow but in no procedure
    - `reagent_written_not_drawn` - a reagent is in the procedure but not on the arrow
    - `route_attribution_unclear` - the scheme cannot be assigned to prior art or to
      the invention from the evidence on the page (rule 5e)
    - `molar_mass_inconsistent` - a stated mass/mole pair implies a molecular weight
      that does not match the compound named or drawn
28. `is_complete` is true only when `validation_flags` is empty.
29. **Do not repair the patent.** Where the numbers are internally inconsistent,
    record them exactly as printed and raise the flag. The value of this gold set
    depends on it being a faithful record of the document, not a corrected one.
    Equally, do not invent a defect. Check every step's arithmetic and report what
    you find. A patent whose numbers all close is a real outcome, not a sign you
    looked badly.

### Text fields
30. `procedure_text` - the procedure verbatim from the Chinese, unabridged, with
    every `[IMAGE_EXTRACT: ...]` span removed (rule 5e).
31. `procedure_summary` - one or two sentences, **no numbers at all**. Numbers live
    in the structured fields; duplicating them into prose creates two sources of
    truth that drift.
32. `notes` - reasoning, ambiguities, translation conflicts, reactor volume.
    Introduce no number that is absent from the text.

## Output

Return ONLY a valid JSON array. No preamble, no explanation, no markdown fences.

Omit `id` and `reaction_uuid` - `finalise.py` computes them from
`(patent_id, reaction_id)` the same way `PersistentRecordBuilder` does.
Leave every enrichment field out entirely (`atom_mapped_rxn`, `template_r0/r1/r2`
and hashes, `feasibility_score`, `yield_score`, `cost_score`, `safety_score`,
`green_score`, `byproduct_score`, `confidence_score`,
`transformation_reaction_count`, `common_literature_*_count`, `reaction_vector`,
`procedure_vector`) - those are produced by a downstream enrichment service, not by
extraction, and a gold set must not contain fields extraction cannot produce.

```json
[
  {
    "patent_id":                 "CN106008290A",
    "reaction_id":               "Example 1_Step 1",
    "section_label":             "string",
    "section_type":              "string",
    "step_index":                1,
    "step_label":                "Step 1",

    "reaction_class":            "string",
    "reaction_class_confidence": "high | medium | low",
    "named_reaction":            "string | null",
    "mechanism_type":            "radical | ionic | pericyclic | photochemical | catalytic | concerted | not_determinable",
    "scale":                     "micro | lab | pilot | production | not_specified",
    "is_one_pot":                false,
    "one_pot_steps":             [],

    "conditions": {
      "temperature":  { "type": "exact | range | room_temperature | not_specified",
                        "value_c": null, "min_c": null, "max_c": null },
      "pressure":     { "type": "atmospheric | reduced | elevated | vacuum | not_specified",
                        "value_kpa": null, "qualitative_text": null },
      "atmosphere":   "string | null",
      "time_h":       null,
      "reactor_type": "string | null",
      "concentration": { "value": null, "unit": "M | N | % | mol/L | mg/mL",
                         "reagent": null, "text": null },
      "heating_method": "string | null",
      "cooling_method": "string | null",
      "light_source": { "type": null, "color": null, "wavelength_nm": null, "power_w": null },
      "stirring":     { "type": "magnetic | mechanical | overhead | vortex | shaker | none",
                        "rpm": null },
      "ph_value":     null,
      "ph_target_stage": "string | null"
    },
    "conditions_inherited":      false,

    "workup": {
      "steps": ["string"], "quenching_agent": null, "extraction_solvent": null,
      "extraction_count": null, "extraction_volume_ml": null, "washes": null,
      "drying_agent": null, "filtration": null, "concentration_method": null,
      "ph_target": null
    },
    "purification":              "string | null",
    "process_control": { "method": null, "target_compound": null,
                         "threshold_pct": null, "criterion": null },
    "byproduct_recovery": [
      { "compound": "string", "mass_g": null, "concentration_pct": null,
        "recovery_method": null, "reuse": null }
    ],
    "safety_notes":              ["string"],
    "molar_ratio_text":          "string | null",
    "selectivity": { "regio": null,
                     "stereo": { "type": "ee | de | dr | syn/anti", "value_pct": null },
                     "chemo": null },

    "compounds": [
      { "identifier": "string", "role": "string", "is_product": false,
        "quantity": { "mass_g": null, "volume_ml": null, "mmol": null,
                      "equivalents": null, "yield_pct": null },
        "addition_profile": null, "ms_mz": null, "ms_type": null,
        "purity_pct": null, "purity_method": null }
    ],
    "reactant_names":            ["string"],
    "reactant_smiles":           null,
    "smiles_source":             null,
    "product_name":              "string",
    "product_smiles":            null,
    "product_smiles_source":     null,
    "product_yield_pct":         null,
    "product_ms_mz":             null,
    "product_ms_type":           null,
    "product_purity_pct":        null,
    "product_purity_method":     null,
    "canonical_rxn":             null,

    "procedure_text":            "string",
    "procedure_summary":         "string, no numbers",
    "precursor_step":            "string | null",
    "linkage_confirmed":         false,
    "cross_reference_unresolved": false,
    "non_synthetic":             false,
    "is_complete":               true,
    "validation_flags":          [],
    "tags":                      ["category:value"],
    "notes":                     "string | null"
  }
]
```

## Provenance sidecar

After the array, emit `---PROVENANCE---` then:

```json
[
  { "reaction_id": "Example 1_Step 1", "source_lines": [167, 171],
    "quote_zh": "verbatim Chinese fragment",
    "arithmetic_check": "stated input mol, stated product mass, stated yield, and whether they close",
    "drawing_evidence": "which IMAGE_EXTRACT span supports this step, and whether it agrees with the prose" }
]
```

`arithmetic_check` is written to `output/reactions-provenance.json` and is the
input to the A5 verification pass. It never enters `reactions.json`.
