# Visual evidence for CN106008290A

What a reviewer who does not know chemistry can check with their own eyes.
A SMILES string is unreadable to them. Two drawings side by side are not.

## What is exact and what is a guess, asset by asset

| asset | what is exact | what is a guess |
|---|---|---|
| `page-index.json` marker to page | EXACT. Read off the per-page paragraph lists of the vision pass. | nothing |
| `page-index.json` marker to position down the page | CORROBORATED on 4 of 7 pages, covering 43 of 56 markers: the paragraph openings measured in the ink were counted against the printed markers the vision pass recorded, and only pages where the two agreed are placed. | the measurement itself. Where the counts disagreed the whole page is left unplaced, because a y that points at the wrong paragraph is worse than no y. |
| `page-index.json` line to page | EXACT. Read off the page comments the numbered source writes ahead of each page's lines. | nothing |
| `page-index.json` drawing regions | the page, and that a drawing is on it | APPROXIMATE. Found by measuring ink. Deliberately loose. |
| `comparisons/*.png` left half | EXACT. Rendered by RDKit from the SMILES text in the gold, with the same settings as `resolve_structures.py`. | nothing |
| `comparisons/*.png` right half | that it is a piece of the real scanned page | APPROXIMATE. Which piece was chosen by image analysis. |
| `comparisons/*.png` pairing of the two halves | see `pairing` per comparison | `name` is independent and strong; `structure` is weak and cannot catch a misread drawing. |
| `drawing-claims.json` conflicts | EXACT. Copied from the vision pass, which read each page. | the English wording of quoted Chinese, see below |

## How the right half of each comparison was found

The PDF is a scan. `pymupdf` returns zero characters on all nine pages and no
OCR engine is installed, so there are no text coordinates and the position of a
drawing has to come from the ink.

A line of Chinese body text is about 30 pixels tall and its ink fills about 15%
of its own bounding box. A drawn structure is 140 to 900 pixels tall and fills
about 1.5%. That is an order of magnitude, so splitting them is not delicate.
Runs of neighbouring not-text bands are joined into one drawing, which is what
keeps the four-row scheme on page 6 in one piece.

The check on that method: it was run over all nine pages and its count compared
against the number of drawings the vision pass reported per page.

| page | drawings reported | regions found | agree |
|---|---|---|---|
| p01 | 0 | 1 | NO |
| p02 | 2 | 2 | yes |
| p03 | 0 | 0 | yes |
| p04 | 2 | 2 | yes |
| p05 | 0 | 0 | yes |
| p06 | 0 | 0 | yes |
| p07 | 0 | 0 | yes |

Where a page disagrees, no region is trusted for it and the comparison shows the
WHOLE PAGE with a note saying so. A loose crop wastes a reviewer's time. A wrong
crop shows them a different molecule and invites them to reject a correct
extraction, so the fallback is always to show more rather than less.

The one disagreement, on p01, is benign and is left in
the table rather than tuned away. It is the front page, whose masthead logo
and QR code are ink that is not text and not a chemical structure either. No
chemical drawing appears on that page, so no comparison is built from it and
nothing downstream depends on the region. It is reported because a method
check that quietly drops its own failures is not a check.

## How the two halves of a comparison were paired

This is the part that decides whether a comparison proves anything.

- `name` (0 of 4): our structure was chosen by the compound name printed in the patent's TEXT near the drawing, and nothing about it came from the drawing. The two halves are independent and can genuinely disagree. This is the pairing that can catch a misread drawing.
- `structure` (4 of 4): the patent's words near the drawing name no compound we hold, so our record was found by matching structures. The halves then agree by construction. Such a comparison shows only that we hold the molecule at all, and it is labelled WEAK on the image itself.

## The mirror problem, and what was done about it

RDKit picks its own rotation and reflection for a depiction, and for these
molecules it picked the MIRROR IMAGE of the way the patent draws them. Same
molecule, flipped picture. A chemist reads straight past that. The reader this
asset is built for cannot: they are matching shapes, and the honest answer from
someone matching shapes to a mirrored pair is "no, these are different". That
would have turned the best asset in the pack into a generator of false defects
against correct extractions.

Our side is now laid out onto a template whose 2D coordinates reproduce the
patent's own geometry, read off the drawings themselves: a hexagon with an apex
top and bottom and vertical left and right edges, the acyl group at the
upper-left vertex, the chlorine at the top, the C3 group at the upper-right and
the sulfonyl at the lower-right. Two templates cover the document, one for the
four-substituent benzoate series and one for the three-substituent toluene.

8 of 17 panels are laid out the patent's way, and each panel records which template it used under
`oriented_to_patent_layout`. The only one left is 2,6-dichlorotoluene, which
carries too few substituents for either template to grip; it is near-symmetric
and reads the same either way.

Every comparison also carries a line ABOVE the question telling the reviewer to
judge by which groups are attached to the ring rather than by where they sit on
the page, and saying whether that particular picture was oriented or not. The
orientation fix reduces the problem; the sentence is what makes the question
answerable when it cannot be fixed.

**Matching the patent's notation was tried and rejected.** RDKit's abbreviation
set condenses the acetyl group to `Ac` and the carboxylic acid to `CO2H`, where
the patent draws both out in full, and it does not touch `SO2CH3` at all, which
was the group worth condensing. It would have added notation mismatches rather
than removing them, so our side stays as drawn-out skeletal structures.

## What the machine already found

Where the pairing is by name, the drawing's SMILES and the gold's SMILES are both reduced to one canonical form and compared. That check ran on 0 structures and found 0 disagreements. The denominator is the point: zero out of zero would mean the check never ran.

It found 0 molecules that the patent draws and the gold holds no record of.

The 11 conflicts in `drawing-claims.json` are defects in the PATENT, not in the annotation. What each one asks the reviewer is whether we recorded what the patent really prints, contradiction and all, rather than quietly correcting it. Only 5 of them involve a drawing at all; the rest are two pieces of the patent's prose disagreeing, and those carry the page scan as their evidence rather than a picture that could not answer them.

One thing worth a human eye, and visible on the page-6 scheme comparison: three of the molecules in that route are held in the gold with a SMILES string where their name should be. Their panels say so, rather than printing the SMILES as if it were a name.

## Running it on a different patent

`contracts/GENERALISATION-AUDIT.md` found that 108 of the pack's 119 declared
paths carry no patent id, and `input/vision/` and `input/pages/` are two of them.
This stage reads both, so on a second patent it would otherwise crop and compare
the FIRST patent's pages and put the second one's name on the result. Nothing
about the output would look wrong.

So before reading anything, the stage checks that its inputs are the patent it
was asked for, and refuses with exit 2 and an itemised reason if they are not. It
writes nothing in that case. The check is cheap because the scans identify
themselves: the publication number is printed in the running head of every page
and the vision pass captured it, on 7 of 7 pages here. The
result of that check is recorded in `page-index.json` under
`inputs_belong_to_this_patent`, so the artefact carries its own proof of which
document it was built from.

## Language

Every human-facing string is English and ends in `_en`. Compound names use
`output/translations.json`, the verified index, so the wording matches the gold.
The vision pass also quotes the patent's Chinese prose inside its findings, and
substituting names into that prose produces half-translated sentences, so each
such field is hand-written as whole English in `quote-translations.json`, keyed
by its exact source position and marked as authored at this stage rather than
verified. A gate at the end of the build fails the run if any Chinese character
reaches any file here.

## Files

- `page-index.json` - marker to page, page to image, plus detected drawing regions.
- `comparisons/<record_id>.png` - the full comparison, captioned and self-describing.
- `crops/<record_id>.png` - the patent's half on its own, trimmed to the
  drawing. This is what `comparison.theirs.src` points at, because the uncut
  band below runs the full width of the text column and on page 8 that sweeps
  up a line of Chinese heading printed level with the structure. Baked into
  pixels, no gate over strings can see it, so the trimmed file is the one a
  reviewer is shown.
- `comparisons/<record_id>-patent.png` - the UNCUT band from the page, running
  the full width of the text column, reachable as `comparison.theirs.uncut_src`.
  Nothing that was trimmed off the sides is lost; open this if the trim looks
  like it cut into the molecule.
- `drawing-claims.json` - review queue, conforming to `claims[]` in the
  verification contract, all `tier: 1`.
- `quote-translations.json` - hand-written English for the quoted Chinese.

## Two things this cannot tell you

1. Nothing here says the chemistry is right. A comparison answers only whether we
   wrote down the molecule the patent drew.
2. A `structure`-paired comparison cannot catch a misread drawing, because the
   drawing is what chose the record it is being compared against.

## Rebuild

```
python3 make_visual_evidence.py --patent-id CN106008290A
```

Deterministic and offline. No timestamps are written, so a diff between two runs
shows a real change and nothing else.
