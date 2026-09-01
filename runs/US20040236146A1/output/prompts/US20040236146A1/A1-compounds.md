# A1 - Compounds

**Artifact produced:** `output/compounds.json` (array of `CompoundRecord`)
**Input:** one section of `input/US20040236146A1-enriched-numbered.md` + its A0 entry
**Runs:** once per section where A0 set `contains_procedure = true`, plus once each
over `claims`, `background`, `summary_of_invention` and `abstract`.

This pass replaces LiteratureIQ's two-pass M1 (over-collect) + M2 (resolve) split
with a single pass, because the whole document fits in one context and a gold set is
optimised for accuracy rather than throughput. The **resolution rules from M2 are
kept in full** - they are the part that carries information.

---

You are a chemistry patent analyst building a **reference (gold) annotation**. This
output will be used to score an automated extractor, so a missed compound counts
against recall and an invented compound counts against precision. Both are equally
bad. Extract what is written; never what you happen to know.

## Input

PATENT_ID: `US20040236146A1`
SECTION_LABEL: `{SECTION_LABEL}`
SECTION_TYPE: `{SECTION_TYPE}`
LINES: `{START_LINE}`-`{END_LINE}`

SECTION TEXT (line-numbered enriched markdown - Chinese is authoritative, `EN:` lines are a convenience, `[IMAGE_EXTRACT: ...]` spans are machine-read structures):
---
{SECTION_TEXT}
---

## Rules

### What to extract
1. Extract **every** compound named in the section, whatever its role: products,
   reactants, reagents, solvents, catalysts, ligands, bases, acids, oxidants,
   reductants, by-products, additives and drying agents. A solvent is a compound.
   Water used as a wash is a compound. Do not filter by importance.
2. Extract the identifier **exactly as written**, in the form the text uses. Do not
   translate a Chinese chemical name into English for the `identifier` field -
   instead resolve it per rule 6 and keep the original as an alias.
3. Do not invent or infer compound names. If the text says "the title compound",
   extract that phrase (see rule 7).
4. A compound mentioned in more than one step of the same section is ONE record.
   Merge them: keep the most complete `quantity`, union the `aliases`, and note the
   merge. Do not emit one row per appearance.

### Structures read from the drawings
4a. A `[IMAGE_EXTRACT: {"molecules":[{"smiles": ...}]}]` span is a chemical structure
    that was **drawn** on the page and read into SMILES. In this document most
    experimental steps are preceded by a drawing of that step's product, so these
    spans are the structural identity of compounds the prose names only in words.
4b. When such a span sits immediately before or after a named compound and encodes
    the same structure, **add the SMILES to that compound's `aliases[]`**. Do not
    create a separate record for it. This is exactly how production handles
    MolScribe output, so following it keeps the artifacts comparable.
4c. Leave the `smiles` field itself **null**. Structure resolution against PubChem
    and OPSIN is a downstream enrichment stage, and populating `smiles` here would
    make the gold set score that stage rather than extraction.
4d. If a span's SMILES does not match the compound name it sits next to, keep the
    name as `identifier`, do **not** put the SMILES in `aliases`, and write
    `"SMILES_MISMATCH: drawn structure does not match the compound name - verify the
    vision read"` into `notes`.
4e. A `[IMAGE_EXTRACT: {"reactions":[...]}]` span is a reaction scheme, not a single
    compound. Its `reactants` and `products` are compounds and must be extracted;
    its `conditions[].text` entries are reagents and conditions, so extract any
    compound named there too. Pass A2 owns the connectivity; you own the compounds.
4f. Where a scheme names a compound the prose never mentions, still extract it. Set
    `resolved` honestly and note that it is drawing-only. A compound that exists
    solely as a drawing is the commonest thing a text-only extractor misses, and the
    gold set has to contain it for that miss to be measurable.

### Identifier resolution
5. `identifier_type` is one of: `iupac` | `smiles` | `local_label` |
   `functional_ref` | `abbreviation` | `formula` | `trivial_name` | `other`.
6. Resolve to a global identifier where the text supports it:
   - Chinese chemical name -> its standard English/IUPAC form, when the Chinese is
     unambiguous (`2-氯甲苯` -> `2-chlorotoluene`). Keep the Chinese as an alias and
     set `identifier_type` to `iupac` or `trivial_name`.
   - Local label (`化合物 3`, `intermediate 1`) -> the full name if the section
     states it. If it does not, keep the label, set `resolved: false` and
     `unresolved_reference: true`.
   - `functional_ref` ("the title compound", "标题化合物", "上述化合物") -> the
     product of the CURRENT section when the section names one. If the section names
     no product, leave unresolved.
7. `resolved` is true only when `identifier` is a name that identifies one specific
   compound. A Markush description, an R-group fragment, or a bare label is not
   resolved.
8. **Never emit an R-group substituent fragment as a compound.** In
   `formula_definitions` sections, extract only fully enumerated complete compound
   names, one record each.

### Role
9. `role` is one of: `product` | `reactant` | `reagent` | `solvent` | `catalyst` |
   `ligand` | `base` | `acid` | `oxidant` | `reductant` | `by_product` | `additive` |
   `drying_agent` | `other`.
   Assign the most specific role the text supports before falling back to `other`:
   - `product` - the isolated compound the step produces
   - `reactant` - a starting material transformed into the product
   - `reagent` - transforms the substrate but is not the carbon skeleton source
   - `solvent` - reaction or recrystallisation medium
   - `catalyst` - present sub-stoichiometrically and not consumed
   - `base` / `acid` - used to deprotonate, neutralise or acidify
   - `drying_agent` - MgSO4, Na2SO4 and similar in the workup
   - `by_product` - a co-formed compound the text names as such
10. `is_section_product` is true only for the compound the section as a whole is
    headed by or ends with. In a multi-step section there is one final product; the
    products of intermediate steps are `role: product` with
    `is_section_product: false`.
11. `commercially_available` is true only when the text says so, or when the
    compound is a bulk commodity reagent or solvent that no step of this patent
    prepares. If a preceding step in the document prepares it, it is false.

### Quantities
12. Populate `quantity` from the text only. Never convert, never compute a missing
    field from another. If the text gives `25.3g(0.2mol)`, set `mass_g: 25.3` and
    `mmol: 200.0` (mol -> mmol is a unit change, not a chemical inference, and is
    allowed). If it gives only grams, leave `mmol` null.
13. `yield_pct` goes on the **product** compound of the step, never on a reactant.
14. `equivalents` only when the text states it. Do not derive it from mmol ratios.
15. **Volumes:** `150ml` of a solvent is `volume_ml: 150.0`.

### Characterisation
16. Populate `nmr`, `melting_point`, `appearance`, `color`, `physical_form`,
    `analytics`, `purity_pct`, `purity_method` from the text, on the compound they
    describe - which is nearly always that step's product.
    - `nmr.raw_text` - the NMR block verbatim as printed.
    - `nmr.solvent` - `CDCl3`, `DMSO-d6` etc. as printed.
    - `melting_point` - `熔点110-112℃` gives `min_c: 110.0, max_c: 112.0,
      range_text: "熔点110-112℃"`.
    - `physical_form` - one of `solid` | `liquid` | `gas` | `gel` | `resin` | `oil` |
      `powder` | `crystals` | `other`. `淡黄的固体` / "light yellow solid" gives
      `physical_form: "solid"`, `color: "light yellow"`.
    - `analytics[].method` - `hplc` | `gc` | `ms` | `nmr` | `ir` | `uv` | `tlc` |
      `elemental` | `xrd` | `dsc` | `tga` | `boiling_point` | `optical_rotation` |
      `other`. Record in-process monitoring (`LC跟踪`, "followed by LC") here with
      `method: "hplc"` and the phrase in `raw_text`.
    - `purity_method` - `hplc` | `gc` | `nmr` | `uv` | `titration` | `other`.
17. Set every characterisation field you cannot support to `null`. An empty object
    is not the same as null; use null.

### Tags
18. Emit `tags` as `"category:value"` strings, lowercase snake_case ASCII, unique.
    Skip a category entirely rather than emit an uncertain value.
    - `compound_class:` exactly one of `active_ingredient` | `intermediate` |
      `starting_material` | `reagent` | `solvent` | `catalyst` | `ligand` | `base` |
      `acid` | `workup_agent` | `impurity` | `by_product` | `other`.
      Map from role and identity: solvent->solvent, K2CO3->base, Pd/C->catalyst,
      the final herbicide->active_ingredient, an isolated step product that feeds a
      later step->intermediate, the first purchased material->starting_material,
      MgSO4/brine->workup_agent.
    - `chemical_family:` broad scaffold, snake_case (`benzoic_acid`,
      `cyclohexanedione`, `aryl_sulfone`, `benzyl_halide`). Only when confident from
      the identifier.
    - `functional_group:` one tag per salient FG (`sulfone`, `ketone`, `ester`,
      `carboxylic_acid`, `halide_bromo`, `halide_chloro`, `ether`,
      `trifluoromethyl`, `nitrile`).
    - `hazard:` only when the patent warns about it, or the chemistry plainly
      requires it. Values: `cyanide_handling` | `flammable` | `pyrophoric` |
      `toxic` | `corrosive` | `explosive` | `peroxide_former`.
      Bromine -> `corrosive` and `toxic`. Peroxybenzoic acid -> `peroxide_former`.
      Thionyl chloride -> `corrosive`. Carbon tetrachloride -> `toxic`.
19. Do NOT emit tags for `physical_form`, `color`, `role_seen` or `commercial` -
    those are rule-derived downstream and emitting them here creates false diffs.

### Translation hazards
20. The `EN:` line is machine translation and it garbles chemistry. Where Chinese and
    English disagree, follow the Chinese and record the discrepancy in `notes`.

    The cases below were found in the reference run, the one worked example this
    repo ships. They are a checklist of the KINDS of hazard to look for in YOUR section. **None of them is
    an assertion about the patent you are reading.** Check each against your own
    text and use it only where your own text supports it. In particular, never carry
    a quantity from this list into your output: a number that is not in your section
    is not evidence, whatever it confirmed somewhere else.
    - A solvent name that differs from a valid one by a single character. The
      reference run prints `1,2-二氯乙烷` (1,2-dichloroethane) in one step and
      `1,2-二氯甲烷` a few lines later, which names no compound that can exist. That
      was an error in the patent, not in the translation: it was left unresolved,
      kept verbatim, and noted. Do the same with any such string, and do not silently
      read it as whichever neighbour looks likeliest.
    - An ambiguous ring locant. `环己二酮` alone does not say which dione. Resolve it
      only from evidence in your own section, such as a stated mass and mole pair
      that fixes the molecular weight, or a locant the text prints itself
      (`1,3-环己二酮` is unambiguous and needs no inference). Otherwise leave it
      unresolved.
    - A name whose literal reading and whose intended compound differ.
      `氰基丙酮` reads as cyanoacetone and `丙酮氰醇` as acetone cyanohydrin; they are
      different compounds and the two strings differ by transposition. Translate what
      is printed.
21. Never silently correct the source. Emit what the Chinese says and put the
    conflict in `notes`. A gold set that quietly fixes the patent cannot be used to
    measure an extractor that does not.

### Notes
22. Use `notes` for: merges, resolution reasoning, translation conflicts, and any
    place the text is internally inconsistent. Keep it factual and short. Do not put
    numbers in `notes` that are not in the text.

## Output

Return ONLY a valid JSON array. No preamble, no explanation, no markdown fences.
One element per distinct compound in this section.

Omit `id` and `compound_uuid` entirely - they are computed deterministically
downstream by `finalise.py` from `(patent_id, identifier)`, exactly as
`PersistentRecordBuilder` does, so that the gold set's join keys are byte-identical
to production's.

```json
[
  {
    "patent_id":              "US20040236146A1",
    "identifier":             "string",
    "identifier_type":        "iupac | smiles | local_label | functional_ref | abbreviation | formula | trivial_name | other",
    "aliases":                ["string"],
    "resolved":               true,
    "unresolved_reference":   false,
    "section_label":          "string",
    "section_type":           "string",
    "is_section_product":     false,
    "commercially_available": true,
    "role":                   "product | reactant | reagent | solvent | catalyst | ligand | base | acid | oxidant | reductant | by_product | additive | drying_agent | other",
    "quantity": {
      "mass_g":               0.0,
      "volume_ml":            0.0,
      "mmol":                 0.0,
      "equivalents":          0.0,
      "yield_pct":            0.0
    },
    "ms_mz":                  null,
    "nmr": {
      "h1":                   "string | null",
      "c13":                  "string | null",
      "raw_text":             "string | null",
      "solvent":              "string | null",
      "frequency_mhz":        null
    },
    "melting_point": {
      "min_c":                0.0,
      "max_c":                0.0,
      "range_text":           "string | null",
      "decomposition":        null
    },
    "appearance":             "string | null",
    "color":                  "string | null",
    "physical_form":          "solid | liquid | gas | gel | resin | oil | powder | crystals | other | null",
    "analytics": [
      {
        "method":             "hplc | gc | ms | nmr | ir | uv | tlc | elemental | xrd | dsc | tga | boiling_point | optical_rotation | other",
        "value":              null,
        "unit":               "string | null",
        "conditions":         "string | null",
        "raw_text":           "string"
      }
    ],
    "purity_pct":             null,
    "purity_method":          "hplc | gc | nmr | uv | titration | other | null",
    "tags":                   ["category:value"],
    "notes":                  "string | null"
  }
]
```

## Provenance sidecar

In addition, return a second JSON array under the marker line `---PROVENANCE---`,
one entry per compound record, in the same order:

```json
[
  { "identifier": "string", "source_lines": [163, 171], "quote_zh": "verbatim Chinese fragment the record came from" }
]
```

This is kept OUT of `compounds.json` so the artifact stays byte-comparable with
production output. It is written to `output/compounds-provenance.json` and is what
makes manual verification possible.
