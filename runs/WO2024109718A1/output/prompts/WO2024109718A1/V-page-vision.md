# V - Page vision read

**Artifact produced:** `input/vision/pNN.json`, one per page
**Input:** one rendered page image from `input/pages/`
**Runs:** once per page, in parallel, each in a fresh context.

This pass replaces OCR. It exists because WO2024109718A1 has **no text layer at all** - all 45 pages are scanned images, measured at 0 characters of extractable text - and because the information that matters most is
drawn, not written. On a synthesis patent one scheme page commonly carries the
whole route as structural formulae. A text OCR engine returns fragments like
`SO_2CH_3` and `Br_2` scraped off those drawings and silently loses the
connectivity, which is the actual content.

Apple's Vision framework was tried first and discarded: it read the Chinese prose
acceptably but returned only orphaned label fragments for every scheme, and it
corrupted chemistry in prose too (`环己烷-1,3-二酮` came back as `环己烷一1，3-二酮`,
with the hyphen replaced by the Chinese numeral one).

---

You are reading one page of a scanned Chinese patent. Transcribe everything on it,
text and drawings alike. This is the only pass that ever sees the page, so anything
you do not record is lost to every downstream pass.

## Rules

### Text
1. Transcribe every paragraph **verbatim in Chinese**, preserving its `[00NN]`
   paragraph marker. Do not translate in this field, do not normalise punctuation,
   do not fix what looks like a typo.
2. Give a faithful English translation in a separate field. Where the Chinese is
   chemically ambiguous, translate literally and say so in `notes` rather than
   picking the reading you think is intended.
3. Preserve every number exactly: `25.3g(0.2mol)`, `熔点110-112℃`, `收率84％`.
   Full-width characters (`％`, `，`, `．`) stay as printed.
4. Record the page header and footer separately from the body. They are artifacts,
   not content, and downstream passes must be able to drop them.

### Drawings - the part that matters
5. Find every drawing on the page. For each, say whether it is a **single
   structure** or a **reaction scheme**.
6. For a reaction scheme, walk it left to right and top to bottom, and record for
   each arrow: the structure before it, the reagents written **above** the arrow,
   the reagents written **below** the arrow, and the structure after it. Above and
   below are different positions and must not be merged.
7. For every structure, record:
   - `core` - the ring system as drawn (benzene, cyclohexane-1,3-dione, and so on)
   - `substituents` - each substituent as drawn, **with its position on the ring**
     read off the drawing, e.g. `"Cl at C2"`, `"SO2CH3 at C4"`, `"CH2OCH2CF3 at C3"`
   - `name` - the IUPAC or common name, **only when the drawing determines it
     unambiguously**. Null otherwise.
   - `smiles` - only when you are certain of every atom and bond. Null otherwise.
     A wrong SMILES is far worse than a null one; this is a reference dataset.
   - `confidence` - `high` | `medium` | `low`
8. If a substituent position is unclear in the scan, say `"unclear"` for that
   position and set `confidence: "low"`. Do not infer the position from what the
   molecule "should" be. Inferring from chemical knowledge rather than from the
   drawing is the single failure mode that would make this dataset useless.
9. Where a drawing sits between two numbered paragraphs, record which paragraph
   markers bracket it, so its place in the document is recoverable.

### Cross-checks you must run
10. Compare each drawn scheme against the prose on the same page. Report every
    disagreement in `discrepancies`: a reagent drawn but not written, a reagent
    written but not drawn, a structure that does not match the name in the text.
11. Say explicitly whether the drawn scheme is presented as the **invention's**
    route or as **prior art**. Chinese patents commonly draw the prior art route in
    the background section, and mistaking one for the other would corrupt the whole
    annotation.

### Honesty
12. Anything you cannot read, record as `"[illegible]"` with a description of where
    it is. Never fill a gap with a plausible guess.
13. `confidence` on the page as a whole reflects the worst part of it, not the
    average.

## Output

Write ONLY valid JSON to the given path. No preamble, no markdown fences.

```json
{
  "page": "pNN.png",
  "page_label": "the header as printed, e.g. 说明书 3/6页",
  "doc_part": "front_page | claims | description",
  "header": "string",
  "footer": "string",
  "paragraphs": [
    { "marker": "[0031]", "zh": "verbatim Chinese", "en": "faithful translation",
      "notes": "string | null" }
  ],
  "drawings": [
    {
      "kind": "structure | scheme",
      "between_markers": ["[0034]", "[0035]"],
      "presented_as": "invention_route | prior_art | intermediate_structure | unclear",
      "structures": [
        { "position_in_drawing": "1st, top-left",
          "core": "string",
          "substituents": ["Cl at C2", "SO2CH3 at C4"],
          "name": "string | null",
          "smiles": "string | null",
          "confidence": "high | medium | low" }
      ],
      "arrows": [
        { "from_structure": "1st", "to_structure": "2nd",
          "reagents_above": ["string"], "reagents_below": ["string"],
          "arrow_style": "solid | dashed",
          "confidence": "high | medium | low" }
      ],
      "notes": "string | null"
    }
  ],
  "discrepancies": [
    { "what": "one sentence", "drawing_says": "string", "text_says": "string" }
  ],
  "illegible": ["description of each unreadable region"],
  "page_confidence": "high | medium | low"
}
```
