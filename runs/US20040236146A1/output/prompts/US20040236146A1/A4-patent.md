# A4 - Patent record

**Artifact produced:** `output/patent.json` (one `PatentRecord`)
**Input:** `input/US20040236146A1-biblio.json`, the abstract and claims, and a rollup
computed from the other three artifacts
**Runs:** once.

Bibliographic fields are NOT produced by this prompt. They come from
`input/US20040236146A1-biblio.json`, which was scraped from Google Patents, and are
merged in by `finalise.py`. `extraction_rollup` is computed arithmetically by
`finalise.py` from `compounds.json` / `reactions.json` / `pathways.json`. This
prompt produces only the narrative and the 5 LLM-derived tag categories, matching
the split production uses.

---

You are a chemistry patent analyst. Emit the patent-level narrative and tags.

## Input

PATENT_ID: `US20040236146A1`

TITLE (zh): `{TITLE_ZH}`
TITLE (en): `Method for producing 3-bromomethylbenzoic acids`

ABSTRACT:
---
{ABSTRACT}
---

CLAIMS:
---
{CLAIMS_TEXT}
---

CHEMISTRY ROLLUP (computed from the annotated artifacts):
---
{CHEMISTRY_ROLLUP}
---

## Rules

1. `patent_summary` - 1 to 2 sentences, neutral, describing what the document
   discloses. Describe the chemistry and the process. Do not say it is useful or
   novel; that is what `novelty_claims` is for. No yields, masses or temperatures.
2. `novelty_claims` - 2 to 4 sentences on what the patent positions as new. Quote
   claim phrasing where it helps. Where the background states specific objections
   to the prior art, a faithful novelty statement addresses what the invention
   offers against them. Null if the claims surface no novelty.
3. `key_examples` - ordered list of example labels the claims cite, sorted
   numerically. Empty array when the claims cite none. Note that citing zero
   examples is common and correct in CN process claims; do not manufacture one.
4. `tags` - `"category:value"` strings over exactly these five categories. Emit no
   others; `jurisdiction`, `patent_family`, `assignee`, `time_period`,
   `patent_type` and `legal_status` are metadata-derived and `finalise.py` unions
   them in from the biblio file.
   - `domain` (one): `agrochemical` | `pharmaceutical` | `materials` | `polymer` |
     `fine_chemical` | `catalyst` | `dye` | `fragrance` | `nutraceutical` |
     `electronic_material` | `other`
   - `target_class` (one): `insecticide` | `herbicide` | `fungicide` |
     `antibiotic` | `antiviral` | `anticancer` | `analgesic` | `cns_active` |
     `cardiovascular` | `monomer` | `surfactant` | `electrolyte` | `intermediate` |
     `catalyst` | `other`
   - `claim_type` (many): `composition` | `process` | `use` | `formulation` |
     `intermediate` | `apparatus`
   - `novelty` (many): `new_compound` | `new_process` | `new_formulation` |
     `new_use` | `improved_yield` | `improved_purity` | `improved_selectivity` |
     `scale_up` | `green_chemistry`
   - `process_focus` (many): `continuous_flow` | `batch` | `solvent_recovery` |
     `byproduct_recovery` | `photochemistry` | `electrochemistry` | `biocatalysis` |
     `asymmetric_synthesis` | `green_chemistry` | `scalable` | `one_pot`
   Skip a category entirely when no confident value exists.
5. `assignee_type` - omit it. The assignee is known from the biblio file and
   `finalise.py` sets it.
6. `honest_uncertainty_flags` - snake_case codes for anything you could not
   populate confidently:
   `patent_summary_truncated_input` | `novelty_claims_not_inferable` |
   `key_examples_not_referenced` | `domain_low_confidence` |
   `target_class_low_confidence`. Empty array when nothing is flagged.
7. The source text is a machine translation of a Chinese original. If the claims
   are ambiguous because of translation rather than because of drafting, say so via
   `patent_summary_truncated_input` and explain in `novelty_claims`. Do not guess
   what the Chinese "probably" said.

## Output

Return ONLY a valid JSON object. No preamble, no explanation, no markdown fences.

```json
{
  "patent_summary":           "string",
  "novelty_claims":           "string | null",
  "key_examples":             ["string"],
  "tags":                     ["category:value"],
  "honest_uncertainty_flags": []
}
```
