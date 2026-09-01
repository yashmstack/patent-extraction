# A3 - Pathways

**Artifact produced:** `output/pathways.json` (array of `PathwayRecord`)
**Input:** the complete `output/reactions.json` and `output/compounds.json`
**Runs:** once, over the whole patent.

In production this artifact is built by `PathwaysBuilder`, which is deterministic
Java, not an LLM pass. The rules below are that logic written out. Follow them
mechanically. Where a rule fully determines the answer, do not exercise judgement.

---

You are assembling synthetic pathways from an already-annotated reaction set.

## Input

PATENT_ID: `CN106008290A`

REACTIONS (full `reactions.json`):
---
{REACTIONS_JSON}
---

COMPOUNDS (full `compounds.json`):
---
{COMPOUNDS_JSON}
---

## Rules

### Chain construction
1. Follow `precursor_step` backwards from each terminal step to build an ordered
   chain. A terminal step is one that is not named as any other step's
   `precursor_step`.
2. `steps` is ordered earliest first, terminal last.
3. `ksm` is the key starting material: the reactant of the earliest step in the
   chain that contributes the carbon skeleton surviving into the product. The
   substrate whose ring or backbone you can still see in the final product is the
   KSM; the reagent that decorates it is not, however much of it is charged.

   **When no reactant on that step contributes the skeleton, `ksm` is null**, and
   the pathway carries `ksm_not_stated` in `honest_uncertainty_flags` so the null
   is a recorded finding rather than an empty field. `PathwayRecord` has no free
   text field, and the flag list is what it has for exactly this.

   This case is real and it is not rare. A background section that criticises a
   prior-art route commonly names only the reagent it objects to and the product,
   never the substrate: "when preparing X, NBS was used as the brominating agent,
   yield only 67 percent". A2 records that faithfully as a single reactant plus
   `missing_reactant`. Taking "the principal reactant of the earliest step" then
   returns the brominating agent, and the artifact states that a route to
   tembotrione starts from NBS.

   That is a guard passing on absence: "the source does not say" rendered as an
   answer. Null is the answer. Do not fall back to the only compound present, and
   do not infer the substrate from the product or from the rest of the document,
   however obvious it looks.
4. `intermediates` is the ordered list of the products of every step except the
   last.
5. `product` is the product of the terminal step.
6. `ksm`, each `intermediates[]` entry and `product` are `CompoundRef` objects:
   `{ "identifier": string, "smiles": null, "compound_uuid": null }`.
   Leave `smiles` and `compound_uuid` null; `finalise.py` fills `compound_uuid`
   from `compounds.json`.

### Scope
7. Emit one pathway with `scope: "section"` per section that has a terminal step,
   with `section_label` set.
8. Emit one pathway with `scope: "patent"` for the chain terminating in the
   compound the patent treats as its overall target, with `section_label: null`.
   When the section chain and the patent chain are the same steps, emit both
   records anyway - production does, and a missing one is a false diff.

### Aggregates
9. `overall_yield_pct` is the product of every step's `yield_pct`, expressed as a
   percentage. If ANY step lacks a yield, it is null. Do not substitute, do not
   assume 100%, do not average.
   Worked form: yields of 84, 86, 72 give `0.84 * 0.86 * 0.72 * 100 = 52.01`,
   rounded to 2 decimal places.
10. `overall_purity_pct` is the terminal step's `product_purity_pct`. Null when
    absent.

### Steps
11. Each `PathwayStep` is a projection of its `ReactionRecord`. Copy these fields
    verbatim from the reaction - do not re-derive, re-word or re-classify any of
    them:
    `reaction_id`, `yield_pct` (from `product_yield_pct`), `purity_pct` (from
    `product_purity_pct`), `reaction_class`, `named_reaction`, `temperature_c`,
    `time_h`, `atmosphere`, `room_temperature`, `reactor_type`, `pressure`,
    `concentration`, `conditions`, `workup`, `purification`, `selectivity`,
    `process_control`, `byproduct_recovery`, `safety_notes`, `molar_ratio_text`,
    `compounds`, `reactant_names`, `product_name`, `product_yield_pct`,
    `product_ms_mz`, `product_ms_type`, `product_purity_pct`,
    `product_purity_method`, `procedure_text`, `procedure_summary`, `notes`,
    `section_label`, `section_type`, `step_index`, `step_label`,
    `reaction_class_confidence`, `is_one_pot`, `one_pot_steps`, `mechanism_type`,
    `scale`, `conditions_inherited`, `precursor_step`, `linkage_confirmed`,
    `cross_reference_unresolved`, `non_synthetic`, `is_complete`,
    `validation_flags`, `tags`.
    Leave `reaction_uuid` null - `finalise.py` fills it.
    The flat `temperature_c`, `room_temperature`, `time_h`, `atmosphere`,
    `reactor_type`, `pressure` and `concentration` values are derived from the
    reaction's `conditions` object exactly as `ReactionRecord`'s computed getters
    do: `temperature_c` = `conditions.temperature.value_c`; `room_temperature` =
    `conditions.temperature.type == "room_temperature"`; `pressure` =
    `conditions.pressure.value_kpa`; `concentration` =
    `conditions.concentration.text`.
12. `components` is the identifiers of that step's reactants plus its product, and
    nothing else. Not its reagents, oxidants, bases, catalysts or solvents: those
    are already on `compounds[]` with their roles, and adding them here makes the
    field mean something different on every step. Where the step records no
    skeleton-contributing reactant at all, `components` is just the product.
13. Leave every enrichment field null (`feasibility_score`, `safety_score`,
    `green_score`, `cost_score`, `yield_score`, `byproduct_score`,
    `confidence_score`, `transformation_reaction_count`,
    `common_literature_patent_count`, `common_literature_journal_count`,
    `atom_mapped_rxn`, `atom_map_confident`, `template_r0/r1/r2` and their hashes,
    `canonical_rxn`, `reactant_smiles`, `smiles_source`, `product_smiles`,
    `product_smiles_source`). Likewise leave the pathway-level aggregates
    (`safety_score`, `green_score`, `feasibility_score`, `cost_score`,
    `yield_score`, `byproduct_score`, `confidence_score`, `min_*_count`,
    `all_steps_atom_map_confident`) null.

### Pathway tags
14. `tags` is the union of: every step's `tags`, plus the `tags` of the `ksm`, each
    intermediate and the `product` compound records, plus these four derived
    categories:
    - `chain_length:N` where N is the number of steps
    - `branching:linear` when every step has at most one precursor step and is the
      precursor of at most one step; otherwise `branching:branched`
    - `convergence:linear` when no step consumes the products of two different
      earlier steps; otherwise `convergence:convergent`
    - `lcl:short` for 1-3 steps, `lcl:medium` for 4-7, `lcl:long` for 8 or more
      (LCL = longest linear chain)
    Deduplicate. Preserve first-seen order.

### Honesty
15. `honest_uncertainty_flags` is a list of snake_case codes for assumptions the
    construction had to make. Use these where they apply, and add others as needed:
    - `truncated_chain` - the chain does not reach a purchasable starting material
    - `unresolved_precursor` - a `precursor_step` pointed at a step not found
    - `yield_missing_step` - `overall_yield_pct` is null because a step lacks yield
    - `ksm_not_stated` - `ksm` is null because no reactant of the earliest step
      contributes the carbon skeleton, per rule 3. Common on a prior-art route
      recited in a background, where the source names only the reagent it objects
      to and the product
    - `scale_discontinuity_in_chain` - a step's input charge does not match the
      previous step's output, so the chain is a paper chain rather than a
      material one
    - `inconsistent_step_arithmetic` - a step carries `mass_balance_implausible`
    Empty array when nothing applies.
16. A pathway whose steps carry `validation_flags` inherits the problem. Do not
    present a clean pathway assembled from flagged steps.

## Output

Return ONLY a valid JSON array. No preamble, no explanation, no markdown fences.
Omit `pathway_uuid` - `finalise.py` computes it.

Note for anyone reading `PathwayRecord`'s javadoc: it says the uuid is seeded on
`(patent_id, scope, ksm_id, product_id)`. That is **stale**. `PathwaysBuilder`
folds the ordered step signature into the seed as well, because the endpoint-only
seed collapsed distinct routes onto one uuid and they overwrote each other on
upload. Follow the code.

```json
[
  {
    "patent_id":     "CN106008290A",
    "scope":         "section | patent",
    "section_label": "string | null",
    "ksm":           { "identifier": "string", "smiles": null, "compound_uuid": null },
    "intermediates": [ { "identifier": "string", "smiles": null, "compound_uuid": null } ],
    "product":       { "identifier": "string", "smiles": null, "compound_uuid": null },
    "steps": [
      {
        "reaction_uuid": null,
        "reaction_id":   "string",
        "yield_pct":     null,
        "purity_pct":    null,
        "components":    ["string"],
        "tags":          ["category:value"],
        "...":           "every field listed in rule 11, copied verbatim"
      }
    ],
    "overall_yield_pct":  null,
    "overall_purity_pct": null,
    "tags":               ["category:value"],
    "honest_uncertainty_flags": []
  }
]
```
