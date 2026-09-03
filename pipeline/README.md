# Manual annotations - CN104292137A

A hand-run, prompt-driven annotation of one patent, produced in the same JSON
shapes LiteratureIQ writes, so the two can be compared field by field.

**Status: prompts written, nothing run yet.** The workflow is held until the
prompts below are reviewed.

- Target patent: **CN104292137A** - *Synthesis process for the
  triketone-class herbicide tembotrione*, Wuhan Institute of Technology, filed 2014-10-15,
  published 2015-01-21, DOCDB family **52312131**. Google's English title reads
  *...cyclic sulcotrione*, a character-by-character gloss of 环磺草酮 that names a
  real and different herbicide; the title above follows the Chinese.
- Why this one: its Example 1 is a complete eight-step linear route to
  tembotrione, with quantities, conditions, yield, melting point and NMR on almost
  every step. It is the same molecule as the Day 2 golden test, so the two
  datasets sit on the same target.

---

## Why do this by hand at all

The Day 3 work established that LiteratureIQ's existing benchmark measures
**extraction** - patent in, reactions out. What it does not have is a reference
that a human has actually checked. Without one, a benchmark score is a measure of
agreement between two automated runs.

This pack produces that reference. Three properties make it worth the effort:

1. **Schema-identical.** Field names, nesting and vocabularies are taken from the
   Java records in `literatureiq-engine`, not paraphrased. A diff between gold and
   extracted is a real diff, not a shape mismatch.
2. **Independently derived.** The prompts here are written from scratch. They are
   not copies of `prompts/experiment-2/`. If they were, the benchmark would be
   scoring a model against itself.
3. **Adversarially checked.** Pass A5 audits the output against the source with a
   fresh context, assuming it is wrong until the text proves otherwise.

---

## The pass map

![Production extraction passes mapped onto the manual annotation passes](svg/m1-pass-map.svg)

> Production splits reaction extraction across R1, R2 and R3, and runs R2 once per
> step, because token cost has to be bounded at scale. This patent is 27 kB of
> text, so the whole thing fits one context and the split buys nothing. Every rule
> from the split passes is carried into the merged prompt. A5 is the one addition.

| Pass | File | Produces | Runs |
|---|---|---|---|
| V | `prompts/V-page-vision.md` | `input/vision/pNN.json` | once per page, 9 in parallel |
| A0 | `prompts/A0-section-map.md` | `00-sections.json` | once over the document |
| A1 | `prompts/A1-compounds.md` | `raw-compounds.json` | once per section |
| A2 | `prompts/A2-reactions.md` | `raw-reactions.json` | once per section with procedures |
| A3 | `prompts/A3-pathways.md` | `raw-pathways.json` | once |
| A4 | `prompts/A4-patent.md` | `raw-patent.json` | once |
| A5 | `prompts/A5-verify.md` | `verification-report.json` | once per artifact, fresh context |

`build_enriched.py` turns the V output into `input/CN104292137A-enriched.md`.
Every pass writes its raw result into `output/stages/<pass>/` and nothing later
rewrites it, so each stage can be checked on its own. See `output/stages/README.md`.
`finalise.py` then turns the `raw-*.json` files into `compounds.json`,
`reactions.json`, `pathways.json` and `patent.json`. `resolve_structures.py` is the
one deterministic stage that runs after those, and it is documented on its own
below.

### The OCR problem, and why V exists

The PDF was downloaded from Google Patents and inspected before anything else was
built. **All nine pages are scanned images with a zero-length text layer.** There is
no text in the file to extract. Everything readable had to be produced by reading
the pixels.

Three routes were tried:

| Route | Result |
|---|---|
| PDF text layer | 0 characters on every page. Nothing to extract. |
| Apple Vision framework OCR (`zh-Hans` + `en-US`) | Read the Chinese prose acceptably, but corrupted chemistry inside it - `环己烷-1,3-二酮` came back as `环己烷一1，3-二酮`, the hyphen replaced by the Chinese numeral one. On the scheme pages it returned only orphaned fragments: page 6 gave 60 "lines" of which 36 were low-confidence and 37 were six characters or fewer. The connectivity, which is the entire content of that page, was gone. Discarded. |
| Vision model reading the rendered page | Reads the prose, reads the structures, and reads the reagents on each arrow. This is pass V. |

![What each text-recovery route recovers from a scanned patent page](svg/m5-ocr-comparison.svg)

> A tick is not a quality claim. Pass V can still misread a structure, which is why
> A5 re-opens the page images to audit it, and why every SMILES is RDKit-validated
> before it reaches a prompt.

The Google Patents HTML text used for the first draft of this pack was Google's own
OCR plus machine translation. It is retained as
`input/CN104292137A-fulltext.md` for cross-reference only. **It is not the input to
any pass**, because it silently drops every drawing.

### Why the format matches production exactly

LiteratureIQ's Phase 1 is `PDF -> OCR -> Translation -> Image Extraction -> Enriched
Markdown`. Step 4 runs MolScribe and RxnScribe over the structure images, and step 5
splices the results back into the markdown as inline
`[IMAGE_EXTRACT: {...}]` spans, preserving line count so downstream passes can keep
citing absolute line numbers.

Pass V plus `build_enriched.py` produce exactly that, in exactly that format:

```
[IMAGE_EXTRACT: {"molecules":[{"smiles":"...","molecular_formula":"...","inchi_key":"..."}]}]
[IMAGE_EXTRACT: {"reactions":[{"step_id":1,"reactants":[...],"conditions":[{"text":"AlCl3"}],"products":[...]}]}]
```

SMILES are canonicalised with RDKit and given a molecular formula and InChI key, the
same three fields `buildMoleculeEntry` produces via chemstack-toolkit. A SMILES RDKit
cannot parse is dropped from the span and reported, rather than passed downstream
malformed. It survives in `output/structures.json` with the parse failure recorded.

Because the input shape matches, a diff between this gold set and a production run is
a diff in extraction, not a diff in how the document was presented.

---

## What the model is allowed to fill in

![Three kinds of field: model-emitted, computed, deliberately null](svg/m4-field-provenance.svg)

> Ids and UUIDs are deterministic functions of extracted content. Asking a language
> model for them only creates a way for the join keys to be wrong, so `finalise.py`
> computes them instead, reproducing `PersistentRecordBuilder` exactly.
> Enrichment fields are left null on purpose: a reference carrying atom-mapped
> reactions or template hashes would be scoring the enrichment service rather than
> the extractor.

---

## Structure resolution, and the coverage gate

`resolve_structures.py` is the stage that turns identifier strings into drawable
molecules. It runs after `finalise.py` and before `make_relevant_output.py`, reads
the gold and writes only new files.

It exists because the extraction passes emit no structures at all, by design, and
the artifacts are close to unusable that way: a reader cannot see what *methyl
2-chloro-3-(bromomethyl)-4-(methylsulfonyl)benzoate* is, and the mass-balance check
cannot weigh a row it has no molecular weight for. This used to be hand-authored in
a downstream consumer, which meant running the pipeline on a second patent produced
no structures whatsoever and nothing said so. Now the pipeline produces them, and
says loudly what it still cannot.

### The five tiers

```
identifier
   |
   +-- 1. the string itself parses as SMILES ............. patent_scheme
   |
   +-- 2. a SMILES we can attach to it canonicalises to
   |      one DRAWN in gold/structures.json .............. patent_drawing
   |
   +-- 3. a synonym in the same equivalence group has
   |      already resolved ............................... derived
   |
   +-- 4. input/structures-curated.json has an entry ..... curated
   |
   +-- 5. nothing ....................................... none
```

Tier 2 joins on **RDKit canonical SMILES, never on names**. `gold/structures.json`
holds 18 SMILES entries for only 11 unique molecules, because the drawn scheme is
read more than once and the reads name things differently:

```
drawn (p06)  methyl 3-(bromomethyl)-2-chloro-4-(methylsulfonyl)benzoate
drawn (p08)  methyl 3-(bromomethyl)-2-chloro-4-(methanesulfonyl)benzoate
record       methyl 2-chloro-3-(bromomethyl)-4-(methylsulfonyl)benzoate
              \______ three strings, one molecule, no string equality ______/
```

12 of the 16 distinct drawn names match no record name in `compounds.json` or in
the equivalence groups. A name join falls through and reports molecules that **are**
drawn in the patent as not drawn, inverting the single distinction the stage exists
to make.

Tier 3 is why the curated table stays small. `finalise.py` deliberately does not
merge the spelling variants, because `buildCompoundId` is a pure function of the
identifier string and production fragments them identically, so one molecule is
carried under up to three names. The structure travels along
`provenance/compounds-equivalence.json` instead: write one entry, for one spelling,
and it propagates.

### The coverage gate

The script exits non-zero when a molecule that **carries chemistry** has no
structure. Carrying chemistry means one of two things:

- it is the **product** of some reaction, because a route with an unknown product is
  not a route
- it appears in a reaction-compound row with both **`mass_g` and `mmol`**, because
  such a row is an implicit claim about molecular weight and checking that claim is
  the single most valuable thing to do with this patent (see `FINDINGS.md`, where
  the printed pairs turn out to imply the des-chloro weights)

Trivial workup species such as water, hydrochloric acid and magnesium sulfate are
reported as needing no structure and never gate. Hydroxides, hypochlorites and
carbonates deliberately are **not** on that list: they look equally boring, but they
are charged stoichiometrically and a mass balance does need their formula.

On this patent, 34 identifiers carry chemistry, 24 as a product and 17 with a
mass/mole pair, and all 34 resolve.

### Running it on a new patent

```bash
python3 resolve_structures.py                 # defaults to CN104292137A
python3 resolve_structures.py CN102351735A    # any patent id
python3 resolve_structures.py --check         # resolve and report, write nothing
```

Start with an `input/structures-curated.json` holding the new `patent_id` and an
empty `entries` object. Run the stage. Expect it to fail: every reagent that the
patent names but never draws is unknown to it, and it will print exactly which ones
and a JSON stub ready to paste:

```
  2 carry chemistry and have NO structure. FAIL
    thionyl chloride   (mass_g + mmol)
    triethylamine   (mass_g + mmol)

  Hand-author them, checking each SMILES atom by atom against the name,
  and merge this into input/structures-curated.json:

  "entries": {
    "thionyl chloride": {
      "smiles": "",
      ...
```

Fill in each `smiles` and re-run. **Check every SMILES atom by atom against the
name before committing it.** There is no OPSIN and no network here, so nothing
verifies a hand-authored structure against its name except a human doing it; and a
wrong structure does not fail loudly, it silently corrupts a mass balance
downstream. Comparing the RDKit formula the report prints against the formula the
name implies catches most slips.

Two other ways the stage stops rather than guessing:

- a curated key or alias that is not an exact identifier anywhere in the gold, which
  is the only check that catches a typo in a hand-copied name
- two sources giving one identifier two different molecules, which is recorded as a
  conflict and resolved to nothing rather than to whichever was read first

The stage never writes to `gold/` or `provenance/`. It only adds
`output/structures-resolved.json` and `output/structures/<slug>.svg`, which
`make_relevant_output.py` copies alongside the rest of the deliverable. Re-running
is safe: output is byte-identical, and a drawing no molecule claims any more is
removed rather than left behind for a reader to trust.

---

## How the artifacts join

![The four artifacts and the keys that join them](svg/m3-artifact-joins.svg)

> `compound_uuid` is `UUIDv5(patent_id + "::" + identifier)` over the DNS
> namespace. `reaction_uuid` is the same construction over the normalised
> `reaction_id`. `pathway_uuid` folds in scope, KSM and product.
>
> One caveat worth carrying: Python's `uuid.uuid5` and Java's
> `Generators.nameBasedGenerator(NAMESPACE_DNS)` are the same construction on
> paper, but that has been checked against the source of both implementations,
> not against a live production record. Confirm it against one real artifact
> before joining on UUID.

---

## The chemistry being annotated

![The eight-step route to tembotrione disclosed in CN104292137A](svg/m2-route.svg)

> The three flagged steps are the most valuable part of this patent as a test case.
> The gold annotation must record the inconsistent numbers exactly as printed and
> raise `mass_balance_implausible` / `scale_discontinuity`, never quietly repair
> them. An extractor that also misses them has to score as a miss, and it cannot
> if the reference has been silently corrected.

---

## Deliberate departures from production, and what they cost

| Departure | Why | What it costs |
|---|---|---|
| OCR is a vision model reading rendered pages, not Mistral OCR | The PDF has no text layer at all, and Mistral is not reachable here. Apple Vision was tried and lost every scheme. | The gold set does not exercise Mistral's specific noise signature (LaTeX fragments, page-header artifacts). It exercises a different one. Output format is identical, so the artifacts remain comparable. |
| Structures read by a vision model, not MolScribe / RxnScribe | Neither service is reachable here | Structure reading accuracy differs. Mitigated by requiring substituent **positions** to be read off the drawing rather than inferred, by RDKit-validating every SMILES, and by A5 re-opening the page images to audit the read. |
| Text is bilingual CN + EN translation, kept together | Chinese is authoritative and the translation demonstrably garbles chemistry in this document | Prompts state that Chinese wins. Production translates to English and runs the passes on the English, so this pack sees strictly more than production does. |
| Seven production passes merged into five | Document fits one context | The over-collect-then-resolve dynamic of M1/M2 is lost. Mitigated by keeping M2's resolution rules verbatim and by A5. |
| Pathways built by a prompt, not by `PathwaysBuilder` | No Java runtime here | A3's rules are that logic written out. Any divergence is a defect in A3, so A5 checks the chain arithmetic independently. |
| SMILES, InChI, molecular formula and weight left null **on the records**, except in the four goldenPatents runs | Structure resolution is PubChem/OPSIN lookup, not extraction | Those fields cannot be benchmarked from this reference. Structures are supplied in a sidecar instead, `gold/structures-resolved.json`, so the records still diff cleanly against production while the artifacts remain readable and checkable. **CN109678767A, CN112645853A, WO2022024094A1 and WO2024109718A1 are an exception**: they are a gold DATASET rather than a scoring key, so `enrich_structures.py` writes `smiles`, `smiles_source`, `molecular_formula` and `molecular_weight` onto their records. Those four no longer diff cleanly on those fields. `inchi_key` stays null everywhere. |
| Structures resolved by tiered lookup. OPSIN and PubChem are now both available and both used, but only by `enrich_structures.py` on the four goldenPatents runs | When this was written there was no Java runtime and no network. There is now OpenJDK 21 and the OPSIN jar is vendored at `pipeline/vendor/`, so the parse is offline and version-pinned rather than a call to opsin.ch.cam.ac.uk | Anything the patent neither draws nor lets us infer has to be hand-authored in `input/structures-curated.json`, which is a human judgement rather than a lookup. Mitigated by the coverage gate, which refuses to pass until every molecule carrying chemistry has one, and by tagging every structure with the strength of its provenance. |

---

## Layout

```
manual_annotations/
  README.md
  build_enriched.py          vision reads -> enriched markdown with IMAGE_EXTRACT
  finalise.py                deterministic ids, uuids, rollup, biblio merge
  resolve_structures.py      identifier -> structure, plus the coverage gate
  make_svgs.py               diagram generator, with a collision checker
  prompts/       V, A0 .. A5
  input/
    pdf/                     the downloaded PDF, 9 pages, no text layer
    pages/                   rendered PNGs at 200 dpi, one per page
    vision/                  pNN.json, one per page, written by pass V
    CN104292137A-enriched.md          the actual pass input
    CN104292137A-enriched-numbered.md
    CN104292137A-fulltext.md          Google's OCR, cross-reference only
    CN104292137A-biblio.json
    structures-curated.json           hand-authored structures, one per molecule
  schemas/       json-schema for each artifact + validate.py
  output/
    relevant_output/         THE DELIVERABLE - start here
      README.md  FINDINGS.md  AUDIT.md
      gold/  provenance/  verification/  structures/  svg/
    stages/                  per-pass output, kept unmerged for manual checking
      A0-sections/  A1-compounds/  A2-reactions/
      A3-pathways/  A4-patent/     A5-verify/
    structures.json          every drawn structure, from pass V
    structures-resolved.json one structure per identifier, with its origin
    structures/              one monochrome SVG per unique molecule
    compounds.json  reactions.json  pathways.json  patent.json
    raw-*.json               pre-finalise pass output, working state
  svg/           m1 .. m5
```

## Running it

**One command.** `python3 run_pipeline.py --patent-id <ID>` runs every deterministic
stage in the right order, skips what is already current, stops on a coverage gate
with the message that says what a human owes, and writes a manifest of every
artifact with the hashes it was built from. It does not run the LLM passes; it tells
you exactly which are missing and which prompt produces each. See **[PIPELINE.md](PIPELINE.md)**
and the stage graph in [`svg/p1-pipeline-stages.svg`](svg/p1-pipeline-stages.svg).

The steps below are what that script automates, kept as the record of the order.

```bash
# 1. download PDF, render pages                      done
# 2. run pass V, 9 agents in parallel                -> input/vision/pNN.json
# 3. python3 build_enriched.py                       -> input/CN104292137A-enriched.md
# 4. run A0-A4, each writing into output/stages/<pass>/
# 5. python3 finalise.py                             -> the four artifacts
# 6. python3 schemas/validate.py                     -> schema conformance
# 7. run A5 over each artifact                       -> output/verification-report.json
# 8. fix findings, re-run finalise.py
# 9. python3 resolve_structures.py                   -> structures + the coverage gate
#    fails until every molecule that carries chemistry has a structure;
#    it prints the missing identifiers and a stub for input/structures-curated.json
# 10. python3 make_relevant_output.py                -> output/relevant_output/
```

Everything worth reading is in **`output/relevant_output/`**. The rest of `output/`
is working state, kept so the run is auditable and re-runnable.

## Related

- `../day2-literatureiq-golden-test/` - discovery golden set for the same molecule,
  now carrying `Patent Family Id`
- `../day3-extraction-benchmark/01-schema-discovery/` - where these schemas came from
