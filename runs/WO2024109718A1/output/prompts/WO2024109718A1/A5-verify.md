# A5 - Adversarial verification

**Artifact produced:** `output/verification-report.json`
**Input:** all four artifacts, their provenance sidecars, and the source text
**Runs:** once per artifact type, with a fresh context that has NOT seen the
annotation being checked produced.

This pass is what separates a gold set from another extraction. Without it, the
annotation is one model's opinion, and benchmarking against one model's opinion
measures agreement, not correctness.

---

You are auditing a reference annotation of a chemistry patent. **Assume it is wrong
until the source text proves otherwise.** Your job is to find defects, not to
confirm the work. An audit that finds nothing is a failed audit unless you can show
you checked each class of defect below and it genuinely held.

## Input

SOURCE TEXT (line-numbered enriched markdown - verbatim Chinese is authoritative, `EN:` lines are a convenience, `[IMAGE_EXTRACT: ...]` spans are the vision read of the drawings):
---
{NUMBERED_TEXT}
---

ARTIFACT UNDER AUDIT: `{ARTIFACT_NAME}`
---
{ARTIFACT_JSON}
---

PROVENANCE SIDECAR:
---
{PROVENANCE_JSON}
---

## What else is on disk before you call something lost

Three side-channel files hold what a `CompoundRecord` has no field for. Read them
before you raise a finding about information being missing or misattributed,
because a defect that is really a side channel you did not open is a false
critical, and a false critical costs a reviewer more than a missed one.

- `output/compounds-sections.json` - every section each compound was seen in.
  A1 runs per section and `finalise.py` merges by identifier the way production's
  `mergeCompoundFields` does, so the surviving `section_label` is the LAST section
  that mentioned the compound and can name a section that holds none of its
  numbers. That is production's behaviour, mirrored on purpose; this file is the
  index production does not keep. A merged record is not evidence of a lost one.
- `output/compounds-equivalence.json` - compounds that are one molecule under
  several spellings. These are deliberately NOT merged, because `buildCompoundId`
  is a pure function of the identifier string and production emits them separately
  too. Fragmentation that appears here is recorded, not undetected.
- `output/reactions.json` - the per-step record. Every charge, every yield and
  every purity the document prints survives here, per example. `compounds.json` is
  a per-compound summary and keeps one merged quantity, so a number absent there is
  usually present here. Check before calling it gone.

None of this makes a genuine defect less of one. It tells you which artifact to
file it against, and whether "missing" means missing or means somewhere else.

## Checks

### 1. Recall - what is in the text but missing from the artifact
Read the source independently. List every compound, step, condition, quantity and
characterisation datum you find that the artifact does not carry. Go section by
section. Solvents, washes and drying agents are the usual casualties; check them
explicitly rather than skimming.

### 2. Precision - what is in the artifact but not in the text
For each record, find the line that supports it. Anything you cannot anchor to a
line is a fabrication and must be reported, however plausible it looks. Pay
particular attention to:
- conditions that read like defaults (`atmosphere: "nitrogen"` where the text is
  silent)
- structures, SMILES, molecular weights or formulae, none of which this annotation
  is permitted to contain
- yields or masses attached to the wrong compound

### 3. Fidelity - values that are present but wrong
Compare each numeric field against its quote. Check unit handling: mol against
mmol, ml against l, celsius against anything else. Check that a temperature the
text gives as a range was not flattened to a point, and that reflux was not
recorded as a temperature.

### 4. Arithmetic - does the chemistry close
For each step, take the stated input moles, the stated product mass and the stated
yield, and check they are consistent with each other given the product's molecular
weight. Report every step that does not close, with the numbers.
Then check step-to-step continuity: does the mass a step produces cover the mass
the next step consumes?
**Report the discrepancy. Do not correct the artifact and do not correct the
patent.** The correct outcome is a `validation_flag` on the record, and if the flag
is absent that is itself a defect.

### 5. Translation
For every compound and every reagent, compare the Chinese against the English on
the same line. Report every case where they name different things, and state which
one the artifact followed. The artifact must follow the Chinese.

### 6. Linkage
Verify each `precursor_step`: does the named step's product identifier actually
appear among this step's reactants? Report every `linkage_confirmed: true` you
cannot substantiate, and every genuine link the artifact left null.

### 7. Vocabulary
Check every enum-valued field against its closed list in the A1/A2/A3/A4 prompts.
Report any value outside its list, any case mismatch, and any tag that is not
`category:value` with a lowercase snake_case ASCII value.

### 8. Schema
Report fields that are present but should have been omitted (`id`, `*_uuid`, any
enrichment or vector field), and required fields that are missing.

### 9. Drawings
Open the page images in `input/pages/` yourself and check the vision read that the
enriched markdown was built from. For every `[IMAGE_EXTRACT: ...]` span, confirm the
structure it encodes matches what is actually drawn: ring system, every substituent,
and every substituent's **position**. Report any structure whose substituent
positions were plausibly inferred from chemical knowledge rather than read off the
page - a structure that is chemically sensible but not what the page shows is the
worst defect available here, because it is invisible to every downstream check.

Also verify, for each drawn scheme, that reagents written **above** an arrow were not
merged with those written **below** it, and that a scheme in a background section was
not annotated as the invention's route.

## Rules for your own output

1. One finding per defect. Do not bundle.
2. Every finding cites the source line and quotes the text.
3. `severity`:
   - `critical` - a fabrication, or a wrong value that would corrupt a benchmark score
   - `major` - a missed record, or a missing validation flag on inconsistent data
   - `minor` - vocabulary, casing, or a null that could have been populated
4. Where you are not certain, say so in `confidence` and explain what would settle
   it. A hedged true finding is more useful than a confident wrong one.
5. Do not propose rewrites of the whole artifact. Propose the minimal correction.
6. If a check genuinely passes, record it in `checks_passed` with what you verified.
   Silence is not evidence of checking.

## Output

Return ONLY a valid JSON object. No preamble, no explanation, no markdown fences.

```json
{
  "artifact":       "{ARTIFACT_NAME}",
  "records_audited": 0,
  "findings": [
    {
      "check":        "recall | precision | fidelity | arithmetic | translation | linkage | vocabulary | schema | drawings",
      "severity":     "critical | major | minor",
      "record":       "identifier or reaction_id of the affected record, or null for a missing record",
      "field":        "string | null",
      "problem":      "one sentence",
      "source_line":  0,
      "quote":        "verbatim from the source",
      "artifact_says": "string | null",
      "should_be":    "the minimal correction",
      "confidence":   "high | medium | low"
    }
  ],
  "checks_passed": [
    { "check": "string", "what_was_verified": "string" }
  ],
  "recall_estimate": {
    "found_in_text":     0,
    "present_in_artifact": 0,
    "missing":           ["string"]
  }
}
```
