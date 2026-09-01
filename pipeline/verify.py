#!/usr/bin/env python3
r"""Check the gold annotation against the patent it says it came from.

An LLM wrote the annotation in `output/relevant_output/gold/`. An LLM can invent a
number, attach a real number to the wrong molecule, or quote a sentence that is not
in the document. Nothing downstream of the extraction passes has ever asked the one
question that catches all three:

    Is this value actually on the source lines this record itself cites?

This stage asks it, once per field, for every field that holds a number or a quote,
and writes the answers into `output/relevant_output/verification/checks-<PATENT>.json`
as a queue of atomic, human-answerable claims. `contracts/VERIFICATION-CONTRACT.md`
is the shape; this file is the machine that fills it.

THE READER IS NOT A CHEMIST AND HAS TWENTY MINUTES. There are 114 records and
several hundred field values, and they cannot read the patent, which is in Chinese.
Three consequences run through every line below:

  - every human-facing string is English and ends in `_en`. Chinese never reaches
    the artifact, not in a quote, not in a note, not in a label. The index built by
    resolve_translations.py is what makes that possible, and where it has no
    English this file emits an English sentence saying so rather than the Chinese.
  - every claim carries the evidence that would settle it, inline, already
    translated. The reviewer never goes and finds the source text.
  - the machine states its verdict first. The human agrees or overrules.

THE VERDICT THAT MATTERS IS `not_found`: a number or a quote in the annotation that
is NOT in the source lines the annotation cites. That is the hallucination signal
and it sorts to the top of the queue. `found` is what lets the reviewer bulk-accept
the other several hundred and spend the twenty minutes on the handful that need
them.

WHAT COUNTS AS "THE LINES THIS RECORD CITES"

    reactions-provenance.json   source_lines of length 2 read as [start, end] and
                                the whole inclusive range is cited. Example 1 step 1
                                declares [182, 188], and 183 to 187 carry the
                                drawing, the paragraph marker and the procedure
                                itself. Reading those two numbers as two lines would
                                throw the procedure away.
    reactions-provenance.json   source_lines of length 3 or more are exact. Claims
                                step 1 declares [45, 46, 77, 82]: two lines of claim
                                1 plus two scattered lines of claim 2. As a span
                                that is 45 to 82, thirty-eight lines, most of them
                                about other steps.
    compounds-provenance.json   exact lines, unioned over every row for that
                                identifier, since a compound is quoted in several
                                places and each row cites its own.
    every cited Chinese line    also pulls in its own "    > EN: " partner, which is
                                a translation of that line and not independent
                                content. Without this a number printed only in the
                                machine translation reads as absent.

NUMBERS ARE MATCHED AS QUANTITIES, NOT AS STRINGS. A substring search for "5" finds
it on ninety lines. So each source line is tokenised into (value, unit) pairs and
the claim is matched against those:

    record  mmol = 200.0        source  "2-氯甲苯25.3g(0.2mol)"
                                tokens  (25.3, g) (0.2, mol)
                                0.2 mol converts to 200 mmol            -> found

    record  mass_g = 71.4       source  "滴加氯化亚砜71.4(0.6mol)"
                                tokens  (71.4, None) (0.6, mol)
                                the value is there, the unit is not     -> partial

The second is not a matcher failure. The patent really does print a bare 71.4 with
no unit at that step, and `partial` is the correct thing to put in front of a human.

Ranges are tokenised as ranges, so "15-20℃" yields (15, C) and (20, C) rather than a
bare 15 and a 20 that happens to carry the degree sign. Full-width digits and
full-width punctuation are folded to ASCII first. Chinese numerals are deliberately
NOT folded: all 110 of them in this document sit inside chemical names (三氯化铝,
二氯甲烷, 四口反应瓶) and converting them would make "3" match sixty-one lines that
say aluminium trichloride.

QUOTES ARE MATCHED BY COVERING THEM, NOT BY CONTAINMENT. `cover()` in
resolve_translations.py already solved this and is imported rather than
reimplemented, so the two stages cannot drift apart about where a quote lives. The
quotes are not clean substrings: they elide with " ... ", " | " and " / ", they fold
the patent's full-width punctuation to ASCII, some are English annotator prose with
a Chinese citation embedded, and some quote text that is not on the lines the row
declares. Covering the quote greedily with the longest span each source line can
supply handles all four, and the line each span lands on is what decides the
verdict: covered entirely from the cited lines is `found`, covered from somewhere
else in the document is `not_found` and names where the text really is.

NUMBERS ARE ALSO CLASSIFIED QUOTED OR DERIVED, per patent, from the data. A field
where no value at all appears on any line any record cites was calculated by the
annotator rather than read off the page, and scoring it as ungrounded would fill the
review queue with the machine being wrong about a field the document never states.
Such a field is recomputed instead. On CN104292137A the inference comes out
all-quoted, `mmol` included, because the patent prints molar amounts in mol and the
matcher converts: 0.2 mol against a recorded 200 mmol is a match, and a literal
search for "200" is not.

TWO DIFFERENT QUESTIONS reach the reviewer and every claim says which it is asking.

    about: extraction   the annotation says X and the patent says Y. We are wrong.
    about: patent       the annotation says the patent contradicts itself. The
                        annotation is RIGHT and the document is defective.

FINDINGS.md is explicit that its items are defects in the patent and that the
annotation records them and changes nothing. Blurring the two would ask a reviewer to
mark a correct annotation of a defective document as wrong, so `question_en` is
worded from `about` and the two are counted separately.

THREE QUEUES, NOT ONE LIST, because the reviewer has fifteen minutes and there are
several hundred claims. `tier` is the queue and `risk` is the order within it: tier 1
is everything the machine could not confirm plus the rows a failing check names, a
census; tier 2 is the candidate misses, a census; tier 3 is what matched cleanly, to
be sampled. See REVIEW-PROTOCOL.md. The summary carries each tier's population and
tier 3's population per stratum, because a confidence bound needs the denominator and
it cannot be recovered from a filtered list.

WHAT DID WE MISS is the other half, and no per-record check can answer it. Every
numbered line is walked, marked cited or not, and the uncited ones are scanned for
chemistry: a quantity with a unit, a temperature, a duration, a yield, a ratio, a
drawn structure, or the name of a compound the gold already knows. An uncited line
carrying chemistry is a candidate miss and gets its own claim with
`field: "__coverage__"`, so it queues beside the hallucinations instead of sitting
in a report nobody opens.

Reads the gold, the provenance, the structures, the translation index and the
numbered source. Writes exactly one file, into verification/. Never touches gold/
or provenance/. No network. Re-running is byte-identical apart from `generated_at`,
and setting SOURCE_DATE_EPOCH pins that too.

Exits non-zero when any grounding check fails, so the pipeline stops on a
hallucination rather than shipping one.

Usage:  python3 verify.py                  # defaults to CN104292137A
        python3 verify.py CN104292137A     # any patent id
        python3 verify.py --check          # check and report, write nothing
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, rdMolDescriptors

# The pipeline's one definition of "this string is a structure, not a name".
from resolve_structures import looks_like_smiles, normalise_name
# The quote matcher, imported rather than rewritten. See the module docstring: a
# containment test fails on all four shapes the quotes actually take.
from resolve_translations import (
    CJK,
    EN_MARK,
    FULLWIDTH,
    cover,
    english_by_line,
    has_chinese,
    normalise,
    read_numbered,
    sorted_keys,
    PERCENT,
    QUALIFIERS,
)

_ROMAN_ONLY = re.compile(r"^[ivx]+$", re.I)
_TRAILING_PAREN = re.compile(r"^(.*\S)\s*[\(\[]([^()\[\]]{1,24})[\)\]]\s*$")


def name_and_abbrev(s: str):
    """A printed name that carries its own abbreviation, split into both halves.

    A patent writes "benzoyl peroxide (BPO)" once and "BPO" thereafter, and an
    extraction records whichever form it met. The substance sweep then compares the
    two as strings and reports a substance the gold IS holding as unrecorded.
    Measured on WO2024109718A1: of 62 unaccounted mentions, most were this rather
    than a missing record.

    THE GUARD IS THE POINT. A parenthesised ROMAN NUMERAL is a label index, not an
    abbreviation: "compound of formula (I)" must never collapse to "compound of
    formula", because that is equally the base of formula (II) and of every other,
    and merging them would silently make eight different molecules one. Anything
    ending in "formula" is refused for the same reason, and so is a parenthetical
    carrying no letter.

    Returns (base, abbreviation), or None. Never a partial answer.
    """
    m = _TRAILING_PAREN.match(s or "")
    if not m:
        return None
    base, inner = m.group(1).strip(), m.group(2).strip()
    if _ROMAN_ONLY.match(inner):
        return None
    if base.lower().rstrip().endswith(("formula", "式")):
        return None
    if not re.search(r"[A-Za-z]", inner):
        return None
    return base, inner



RDLogger.DisableLog("rdApp.*")

from pipeline_context import RUN_ROOT, shown
HERE = Path(__file__).resolve().parent
OUT = RUN_ROOT / "output"
INPUT = RUN_ROOT / "input"
REL = OUT / "relevant_output"
STAGES = OUT / "stages"

DEFAULT_PATENT_ID = "CN104292137A"
ENGINE_VERSION = 1

# Evidence is shown inline so the reviewer never leaves the row. A compound quoted
# in seven places cites twenty-five lines, which is a wall rather than evidence, so
# the panel is capped. Lines that actually carried the match are never dropped, and
# `cited_lines` still holds the complete citation, so nothing is hidden - only the
# rendering is bounded.
EVIDENCE_LINE_CAP = 24

# Above this many cited lines a `found` verdict is materially weaker evidence, and
# the tier 3 bound must not average the two together. Measured rather than guessed.
# `water` cites 34 lines because water is quoted in seventeen places, so "100 ml is
# on a line this record cites" becomes nearly unfalsifiable. Two real examples from
# this patent, both verdicts CORRECT and half their evidence coincidence:
#
#   dichloromethane 100 ml   genuine on 243 ("100 ml dichloromethane")
#                            coincidence on 236, where the 100 ml is THF
#   water           100 ml   genuine on 206 ("100 ml of water was added")
#                            coincidence on 236, the same THF
#
# One printed quantity, belonging to a third substance, counted as confirmation for
# two different compounds. Note what would NOT have caught it: line 236 does name
# dichloromethane, elsewhere in the same sentence, so a "the line names the
# compound" test passes it too. Attachment is the reviewer's job and this constant
# exists to tell them where to spend it, not to decide it for them.
WIDE_CITATION = 10


# ---------------------------------------------------------------- normalisation

# The patent prints full-width digits and punctuation in places and the annotation
# quotes them back as ASCII. Folded before any number is read, never in a key.
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９．－～", "0123456789.-~")

# Every spelling of "degrees Celsius" this corpus uses, on both sides: the Chinese
# lines print ℃, the machine translations print °C, "degrees C" and "degree C".
CELSIUS = re.compile(r"\s*(?:℃|°\s*C|deg(?:ree)?s?\.?\s+C)(?![A-Za-z])", re.IGNORECASE)
CELSIUS_MARK = "°"

# Longest first, so mmol is never read as "m" + "mol" and min is never read as "m".
# CN106008290A prints "1000mL", "5小时", "0.5-12h" and "5 hours": mL was read as a
# bare 1000 and the hours were read as bare numbers, so every solvent volume and
# reaction time on the patent reported partial. The Chinese unit words are
# units, not context.
UNIT_ALTERNATION = r"mmol|mol|min|hours|hour|hrs|hr|kg|mg|mL|ml|小时|分钟|[gLl]|h|%|°"

# A leading minus is part of the number only when nothing alphanumeric or
# hyphen-like precedes it: "-10-8℃" reads as -10 to 8, while the "-2" in
# "1,2-dichloro" and the "-10" in "5-10℃" stay what they are.
NUMBER = r"(?:(?<![0-9A-Za-z.,\-~])-)?\d+(?:\.\d+)?"

# Two different boundaries, and the difference is measured rather than tidy.
#
# After a UNIT, only a lowercase letter or a digit disqualifies the match, because
# the patent writes "100mlTHF" and "36%HCl" with the next reagent jammed straight
# onto the unit. Requiring any non-letter there loses the 100 ml of solvent in
# Example 1 step 6 outright, and the check then reports a real quantity as printed
# only in the translation.
#
# After a BARE number the boundary stays strict, because NMR lines are full of
# "3H" and "2H" and a bare 3 that swallows its H is a number this stage would go on
# to match against a claimed mass.
UNIT_BOUNDARY = r"(?![a-z0-9])"
BARE_BOUNDARY = r"(?![A-Za-z0-9])"

RANGE_TOKEN = re.compile(
    rf"(?P<lo>{NUMBER})\s*(?P<lounit>{UNIT_ALTERNATION})?\s*[-~]\s*"
    rf"(?P<hi>{NUMBER})\s*"
    rf"(?:(?P<hiunit>{UNIT_ALTERNATION}){UNIT_BOUNDARY}|{BARE_BOUNDARY})"
)
PLAIN_TOKEN = re.compile(
    rf"(?P<value>{NUMBER})\s*"
    rf"(?:(?P<unit>{UNIT_ALTERNATION}){UNIT_BOUNDARY}|{BARE_BOUNDARY})"
)
# A comma used as a decimal point. Read only as a fallback, because this document is
# full of "1,2-dichloroethane" and "N,N-dimethylformamide" and reading those commas
# as decimal points would invent a 1.2 on every solvent line.
COMMA_DECIMAL = re.compile(rf"(?<!\d)(\d+),(\d+)(?![\d,-])")

# value -> canonical unit, and the factor onto it. `None` unit means the number was
# printed bare, which is a real and reportable state rather than a failure.
UNIT_CANON = {
    "kg": ("g", 1000.0), "g": ("g", 1.0), "mg": ("g", 0.001),
    "l": ("ml", 1000.0), "L": ("ml", 1000.0), "ml": ("ml", 1.0),
    "mol": ("mmol", 1000.0), "mmol": ("mmol", 1.0),
    "h": ("h", 1.0), "hr": ("h", 1.0), "hrs": ("h", 1.0), "min": ("h", 1.0 / 60.0),
    "hour": ("h", 1.0), "hours": ("h", 1.0), "小时": ("h", 1.0), "分钟": ("h", 1.0 / 60.0),
    "mL": ("ml", 1.0),
    "%": ("%", 1.0),
    CELSIUS_MARK: ("C", 1.0),
}

# How near two quantities must sit to be the same quantity. Relative, because 0.2 mol
# converts to 200.00000000000003 mmol in binary floating point and an absolute
# epsilon that works there is meaningless at 500 g.
NUM_EPS = 1e-6


def fold(s: str) -> str:
    """Match form for reading numbers: full-width folded, Celsius unified."""
    t = s.translate(FULLWIDTH).translate(FULLWIDTH_DIGITS)
    return CELSIUS.sub(CELSIUS_MARK, t)


def canon_unit(raw: str | None) -> tuple[str | None, float]:
    if raw is None:
        return None, 1.0
    return UNIT_CANON.get(raw, UNIT_CANON.get(raw.lower(), (None, 1.0)))


class Token:
    """One quantity read off one line: a number, and the unit printed beside it."""

    __slots__ = ("value", "unit", "factor", "raw_unit", "start", "end", "in_range",
                 "folded")

    def __init__(self, value, raw_unit, start, end, in_range=False):
        self.folded = ""
        self.value = value
        self.raw_unit = raw_unit
        self.unit, self.factor = canon_unit(raw_unit)
        self.start = start
        self.end = end
        self.in_range = in_range

    def canonical(self) -> float:
        return self.value * self.factor


def tokenise(text: str) -> list[Token]:
    """Every (number, unit) pair on one line, ranges expanded to their endpoints.

    Ranges are read first and their character spans are then withheld from the plain
    pass, because "15-20℃" must yield 15 C and 20 C. Read plainly it yields a bare
    15 and a 20 C, and a claim of min_c = 15 would come back as a value with no unit
    when the line plainly says otherwise.
    """
    folded = fold(text)
    out: list[Token] = []
    taken: set[int] = set()

    for m in RANGE_TOKEN.finditer(folded):
        unit = m.group("hiunit") or m.group("lounit")
        out.append(Token(float(m.group("lo")), m.group("lounit") or unit,
                         m.start("lo"), m.end("lo"), in_range=True))
        out.append(Token(float(m.group("hi")), unit,
                         m.start("hi"), m.end("hi"), in_range=True))
        taken.update(range(m.start(), m.end()))

    for m in PLAIN_TOKEN.finditer(folded):
        if m.start("value") in taken:
            continue
        out.append(Token(float(m.group("value")), m.group("unit"),
                         m.start("value"), m.end("value")))
    out.sort(key=lambda t: (t.start, t.end))
    return out


def merge_ranges(missed):
    """A range is one fact. Queue it once, not once per endpoint.

    "reflux for 1-10 h" is a single statement the schema could not hold, and
    handing a reviewer a row for the 1 and another row for the 10 doubles the queue
    to say one thing twice. Endpoints of the same range, on the same block, in the
    same unit, merge into one entry carrying both ends.
    """
    out, ranges = [], {}
    for line, block, tok, folded in missed:
        tok.folded = folded
        if not tok.in_range:
            out.append((line, block, [tok]))
            continue
        ranges.setdefault((block, tok.unit), (line, block, []))[2].append(tok)
    for (block, _), (line, blk, toks) in sorted(
            ranges.items(), key=lambda kv: (kv[1][0], kv[0][1])):
        toks.sort(key=lambda t: t.value)
        out.append((line, blk, toks))
    return sorted(out, key=lambda e: (e[0], e[2][0].unit, e[2][0].value))


def comma_decimals(text: str) -> list[float]:
    """Values the line would carry if its commas were decimal points."""
    folded = fold(text)
    return [float(f"{a}.{b}") for a, b in COMMA_DECIMAL.findall(folded)]


def same_number(a: float, b: float) -> bool:
    return abs(a - b) <= max(NUM_EPS, NUM_EPS * abs(b))


# ---------------------------------------------------------------- inputs

def die(msg: str) -> None:
    print(f"\nFAIL  {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(name: str, *dirs: Path) -> object:
    """First existing copy of `name`, searching `dirs` in order.

    Same policy as resolve_structures.py and resolve_translations.py: the working
    copy in output/ and the assembled copy in output/relevant_output/ are both
    correct inputs, so the stage runs whether or not the deliverable has been
    assembled yet.
    """
    for d in dirs:
        p = d / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    die(f"{name} not found in {', '.join(str(d) for d in dirs)}")


def load_inputs(patent_id: str) -> dict:
    gold, prov = REL / "gold", REL / "provenance"
    data = {
        "compounds": load("compounds.json", gold, OUT),
        "reactions": load("reactions.json", gold, OUT),
        "pathways": load("pathways.json", gold, OUT),
        "patent": load("patent.json", gold, OUT),
        "structures": load("structures-resolved.json", gold, OUT),
        # The name parser's answer, for the substance sweep's join. Optional: a pack
        # that never reached the network resolves fewer spans and says so, rather
        # than reporting every unresolved span as a miss.
        "names_opsin": load("names-opsin.json", gold, OUT) or {},
        "drawings": load("structures.json", gold, OUT),
        "equivalence": load("compounds-equivalence.json", prov, OUT),
        "compound_prov": load("compounds-provenance.json", prov, OUT),
        "reaction_prov": load("reactions-provenance.json", prov, OUT),
        "sections": load("00-sections.json", OUT, STAGES / "A0-sections"),
        "translations": load("translations.json", OUT, gold),
    }

    # The patent id is load-bearing, not decorative. Checking the gold against the
    # requested id is what stops one patent's annotation being verified against
    # another patent's source, which would report every claim as a hallucination.
    wrong = {c.get("patent_id") for c in data["compounds"]} - {patent_id}
    if wrong:
        die(f"gold compounds.json carries patent_id {sorted(wrong)}, "
            f"this run is {patent_id!r}")
    if data["patent"].get("patent_id") != patent_id:
        die(f"gold patent.json is for {data['patent'].get('patent_id')!r}, "
            f"this run is {patent_id!r}")
    return data


# ---------------------------------------------------------------- English text

UNTRANSLATED = "[untranslated Chinese term]"
NO_ENGLISH = ("[This source line is Chinese and the pipeline carries no English "
              "pairing for it. Ask a Chinese reader.]")

PAGE_MARKER = re.compile(r"^<!-- page (?P<page>\S+) :: (?P<label>.*?) :: "
                         r"(?P<type>\S+) :: confidence=(?P<conf>\S+) -->$")

# What build_enriched.py puts at the head of a source paragraph: the patent's own
# [00NN] number, or the literal "None" where the page printed no marker. Only ever
# on the Chinese side, so it is proof that a line is source and not translation.
PARAGRAPH_MARKER = re.compile(r"^(?:\[\d{4}\]|None\s)")

# "tembotrione (tembotrione)", which is what folding 环磺草酮 into English leaves
# behind wherever the source already glossed it. Collapsed rather than shipped.
GLOSS = re.compile(r"(?P<before>[^\s()][^()]*?)\s*\((?P<inner>[^()]+)\)")
# An untranslated run left alone inside brackets, "Galinsoga (辣子草属)". The English
# beside it already carries the meaning, so the bracket is dropped whole.
CJK_PAREN = re.compile(r"\s*[(（]\s*[^()（）]*?"
                       + CJK.pattern + r"[^()（）]*?\s*[)）]")


def _collapse_gloss(s: str) -> str:
    def repl(m):
        before, inner = m.group("before"), m.group("inner").strip()
        if before.strip().lower().endswith(inner.lower()):
            return before
        return m.group(0)
    return GLOSS.sub(repl, s)


# The translation index, longest key first, bucketed by first character. Built once
# per index object and held against it so a recycled id cannot serve a stale bucket.
_KEY_BUCKETS: dict[int, tuple] = {}


def index_buckets(index: dict) -> dict:
    entry = _KEY_BUCKETS.get(id(index))
    if entry is None or entry[0] is not index:
        buckets: dict[str, list[str]] = {}
        for key in sorted_keys([k for k in index if k and has_chinese(k)]):
            buckets.setdefault(key[0], []).append(key)
        entry = (index, buckets)
        _KEY_BUCKETS[id(index)] = entry
    return entry[1]


def substitute_longest(text: str, index: dict) -> str:
    """Replace the LONGEST index key that fits at each position, not each run.

    Looking up run by run is the obvious implementation and it is wrong, because a
    chemical name is not one run. `2-氯-3-甲基-4-甲磺酰基苯甲酸甲酯` is in the index
    whole, with the English `methyl 2-chloro-3-methyl-4-(methylsulfonyl)benzoate`,
    but its ASCII locants split it into three runs, none of which is a key. Every
    lookup misses and the reviewer is handed

        2-[untranslated Chinese term]-3-[untranslated Chinese term]-4-[...]

    which passes the no-Chinese gate by destroying the name. Measured over every
    Chinese string that can reach here on this patent: 250 of 325 mangled, 1442
    markers emitted, and 200 of the index's 274 keys unreachable by construction.

    Nor is the fix to curate the fragments. They are sentence clauses - 加入 "add",
    水洗 "wash with water" - and joining their English gives Chinese word order in
    Latin script, with the "methyl" at the wrong end of the name.

    `sorted_keys` is imported rather than reimplemented so this and
    resolve_translations.substitute() can never disagree about which key wins, which
    is the one thing that would make the artifact and the screen name different
    molecules.
    """
    buckets = index_buckets(index)
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        for key in buckets.get(text[i], ()):
            if text.startswith(key, i):
                en = (index.get(key) or {}).get("en")
                out.append(en if en else key)
                i += len(key)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def scrub(text: str, index: dict) -> str:
    """Every run of Chinese in `text` replaced by English, or by a statement.

    Three passes in this order, because the order is what stops the output reading
    like a machine: look the run up in the translation index first, then collapse
    the "English (English)" the lookup leaves behind wherever the source had already
    glossed the term, then drop a still-untranslated run that sits inside brackets,
    since the English outside them is already carrying the meaning. Whatever
    survives all three becomes a marker: a reader who has no Chinese must never be
    handed Chinese, and must never be left unable to tell that something was
    dropped.
    """
    if not has_chinese(text):
        return text

    # Substituted to a fixpoint, because an index VALUE can itself carry Chinese.
    # The abstract's entry resolves whole and its English still says "higher than
    # that of 硝环磺酮 and 甲基磺草酮", both of which the index also answers. One pass
    # leaves those as markers and loses two herbicide names; a second resolves them.
    # Bounded and stopped on no-change, so an entry that quoted its own key could
    # not spin here.
    out = text
    for _ in range(4):
        nxt = substitute_longest(out, index)
        if nxt == out:
            break
        out = nxt
    out = _collapse_gloss(out)
    out = CJK_PAREN.sub("", out)
    out = re.sub(CJK.pattern + "+", UNTRANSLATED, out)
    return re.sub(r"\s{2,}", " ", out).strip()


def describe_drawing(raw: str) -> str:
    """An IMAGE_EXTRACT span, said in a sentence rather than shown as JSON.

    These lines are cited evidence: the drawn scheme on line 174 is the only source
    a Scheme Step record has. Putting the raw span in an evidence panel hands a
    reviewer 4 kB of JSON and asks them to find the chemistry in it. The molecular
    formula and the SMILES are what is actually being claimed, so those are what is
    said, and the reader is told plainly that this line is a drawing.
    """
    mols = image_extract_molecules(raw)
    if not mols:
        return "A drawn structure on the page, which could not be read as data."
    if any(m.get("broken") for m in mols):
        return "A drawn structure on the page whose data span is malformed."
    seen, parts = set(), []
    for m in mols:
        smiles = m.get("smiles")
        if not smiles or smiles in seen:
            continue
        seen.add(smiles)
        formula = m.get("molecular_formula")
        parts.append(f"{formula} ({smiles})" if formula else smiles)
    head = (f"Drawn on the page: {len(parts)} structure"
            f"{'s' if len(parts) != 1 else ''}. ")
    return head + "; ".join(parts) + "."


class Source:
    """The numbered source, with an English rendering and a kind for every line."""

    def __init__(self, patent_id: str, index: dict):
        self.path = RUN_ROOT / "input" / f"{patent_id}-enriched-numbered.md"
        self.lines = read_numbered(patent_id)
        # resolve_translations.py owns the paragraph walk and is still being
        # worked on; it has already grown a third return value once. Unpacked by
        # position at both ends so a fourth does not stop this stage dead. The
        # middle value, when there is one, is the set of lines that ARE English
        # output, which no regex can decide: only the first line of a translation
        # carries "    > EN: " and every continuation line after it looks exactly
        # like a line of the patent.
        walked = english_by_line(patent_id, self.lines)
        self.english, self.walk = walked[0], walked[-1]
        self.en_hint: set[int] = set(walked[1]) if len(walked) > 2 else set()
        self.index = index
        self.numbers = sorted(self.lines)
        self.sha256 = hashlib.sha256(
            self.path.read_bytes()).hexdigest() if self.path.exists() else ""

        self.kind: dict[int, str] = {}
        self.text_en: dict[int, str] = {}
        self.is_translation: dict[int, bool] = {}

        for n in self.numbers:
            raw = self.lines[n]
            self.kind[n] = self._kind(raw)
            text, translated = self._english(n, raw)
            self.text_en[n] = text
            self.is_translation[n] = translated

        self.en_for, self.zh_for, self.pairing = self._pair_blocks()

        # Match forms, computed once. Every line is offered to the quote cover, not
        # only the translated ones, so a quote sitting on an untranslated line is
        # still located and reported rather than silently called missing.
        self.norm = {n: normalise(self.lines[n]) for n in self.numbers
                     if normalise(self.lines[n])}

    # ------------------------------------------------------------ line kinds

    def _kind(self, raw: str) -> str:
        if not raw.strip():
            return "blank"
        if raw.startswith(EN_MARK):
            return "translation"
        if raw.startswith("# ") or PAGE_MARKER.match(raw.strip()):
            return "heading"
        if raw.startswith("[IMAGE_EXTRACT"):
            return "image_extract"
        return "prose"

    def is_zh(self, n: int) -> bool:
        return self.kind[n] == "prose" and has_chinese(self.lines[n])

    def is_en_output(self, n: int, run_open: bool) -> bool:
        """Is line `n` part of the English a Chinese block was translated into?

        The paragraph walk in resolve_translations.py is the authority and is used
        alone wherever it is available, INCLUDING as a negative. Line 199 is the
        NMR shifts of Example 1 step 2, printed in the patent, carrying no Han
        character at all; it looks exactly like an English continuation line and it
        is not one. Absorbing it into line 197's translation would make every one
        of its shift values part of 197's evidence, and a claim of 3.14 g would
        then match an NMR peak.

        The fallback, for a corpus that has no walk, is the same rule spelled out
        by shape: the "    > EN: " mark opens a run, and a line with no Chinese and
        no paragraph marker continues one.
        """
        if self.en_hint:
            return n in self.en_hint or self.kind[n] == "translation"
        if self.kind[n] == "translation":
            return True
        return (run_open and self.kind[n] == "prose"
                and not has_chinese(self.lines[n])
                and not PARAGRAPH_MARKER.match(self.lines[n]))

    # ------------------------------------------------------------ block pairing

    def _pair_blocks(self):
        """Which English line translates which Chinese line. See SOURCE-PAIRING.md.

        Not n + 1. The source alternates Chinese and English 53 times, which is why
        n + 1 looks right, but where the chemistry is it does this:

            45 | 1) ...的合成                        zh, a heading
            46 | 将2-氯甲苯...25.3g(0.2mol)...       zh, THE PROCEDURE
            47 |     > EN: 1) Synthesis of ...       en, the heading
            48 | 2-Chlorotoluene, 25.3 g (0.2 mol)   en, THE PROCEDURE

        Line 46 carries every mass, temperature and time in step 1, and n + 1 hands
        back line 47, a heading with no number in it. A reviewer shown that would
        correctly conclude the evidence does not support "25.3 g of 2-chlorotoluene"
        - and the extraction was right, the pairing was wrong. That is the worst
        failure this tool has, because it accuses a correct extraction and leaves
        the reviewer no way to see it was the tool's fault. Measured at 19% of the
        288 compound citations that point at a Chinese line.

        So: take each maximal run of Chinese lines and the run of English lines
        immediately after it. Equal lengths pair positionally, i-th to i-th, and
        that is exact. Unequal lengths pair what they can and clamp the remainder
        onto the last English line, marked `approximate` so a screen can say so. No
        English in the block at all means no translation, said in English.
        """
        en_for: dict[int, list[int]] = {}
        zh_for: dict[int, list[int]] = {}
        pairing: dict[int, str] = {}

        nums = self.numbers
        i = 0
        while i < len(nums):
            if not self.is_zh(nums[i]):
                i += 1
                continue
            zh_run = []
            while i < len(nums) and self.is_zh(nums[i]):
                zh_run.append(nums[i])
                i += 1
            en_run: list[int] = []
            j = i
            while j < len(nums) and self.is_en_output(nums[j], bool(en_run)):
                en_run.append(nums[j])
                j += 1

            if not en_run:
                for n in zh_run:
                    pairing[n] = "none"
                continue
            exact = len(en_run) == len(zh_run)
            for k, n in enumerate(zh_run):
                partner = en_run[k] if k < len(en_run) else en_run[-1]
                en_for[n] = [partner]
                zh_for.setdefault(partner, []).append(n)
                pairing[n] = "exact" if exact else "approximate"
            # An English run longer than its Chinese run is one paragraph broken
            # over more English lines than Chinese ones. Every leftover English
            # line still belongs to the block, so it hangs off the last Chinese
            # line rather than being orphaned into the uncited pile.
            if len(en_run) > len(zh_run):
                last = zh_run[-1]
                for extra in en_run[len(zh_run):]:
                    en_for[last].append(extra)
                    zh_for.setdefault(extra, []).append(last)
                pairing[last] = "approximate"
            i = j
        return en_for, zh_for, pairing

    # ------------------------------------------------------------ English text

    def _english(self, n: int, raw: str) -> tuple[str, bool]:
        """The English for one line, and whether that English is a translation.

        `is_translation` is true when what the panel shows came out of a translator
        rather than off the page: the machine translation of a Chinese line, and the
        "    > EN: " lines, which are that translation written into the file. It is
        false for a line whose own characters are already English - the NMR shifts,
        the drawn-structure spans, the page markers - because a reviewer weighing
        evidence needs to know which of the two they are looking at, and the Chinese
        is the authoritative text in this document.
        """
        if not raw.strip():
            return "", False
        if raw.startswith(EN_MARK):
            return scrub(raw[len(EN_MARK):], self.index), True
        m = PAGE_MARKER.match(raw.strip())
        if m:
            return (f"Page {m.group('page')}, section type {m.group('type')}, "
                    f"transcription confidence {m.group('conf')}."), False
        if raw.startswith("[IMAGE_EXTRACT"):
            return describe_drawing(raw), False
        if n in self.english:
            return scrub(self.english[n], self.index), True
        if not has_chinese(raw):
            return raw, False
        # An English line carrying one Chinese term is still an English line, and
        # surrendering it whole is not the same as protecting the reader from
        # Chinese. Line 76 is 307 characters of the step 8 procedure with a single
        # term in it that the index resolves; abandoning it hid the step that makes
        # the product from eleven claims, and told the reviewer to find a Chinese
        # reader for text they could have read themselves. NO_ENGLISH is now reached
        # only when scrub cannot resolve what it found, which is the state the
        # sentence actually describes.
        rendered = scrub(raw, self.index)
        if UNTRANSLATED not in rendered:
            return rendered, False
        return NO_ENGLISH, True

    def label_kind(self, n: int, claim_lines: set[int]) -> str:
        """The contract's line kind. `claim` is a prose line inside the claims."""
        k = self.kind[n]
        return "claim" if k == "prose" and n in claim_lines else k

    def with_partners(self, lines) -> list[int]:
        """A citation, plus the English of every Chinese line in it.

        A Chinese line and the English it was translated into are one unit of
        evidence. Citing the first without the second hides the English half from
        the only reader this file has.
        """
        out = set()
        for n in lines:
            if n not in self.lines:
                continue
            out.add(n)
            out.update(self.en_for.get(n, ()))
            out.update(self.zh_for.get(n, ()))
        return sorted(out)


# ---------------------------------------------------------------- sections

def section_index(sections, source: Source):
    """line -> section label, and the claims line set, both in English only."""
    by_line: dict[int, str] = {}
    claim_lines: set[int] = set()
    order: list[str] = []
    for s in sections:
        label = s.get("section_label") or f"Section {s.get('section_index')}"
        if label not in order:
            order.append(label)
        for n in range(int(s["start_line"]), int(s["end_line"]) + 1):
            by_line[n] = label
            if s.get("section_type") == "claims":
                claim_lines.add(n)
    return by_line, claim_lines, order


# ---------------------------------------------------------------- citation sets

def reaction_cited(row) -> list[int]:
    """The lines a reaction provenance row cites. Two numbers are a span.

    See the module docstring: [182, 188] is a block of seven lines and [45, 46, 77,
    82] is four scattered citations. Length is the only signal the artifact gives,
    and it is a reliable one here because every block citation is written as its two
    endpoints and every scattered citation enumerates.
    """
    lines = sorted({n for n in (row.get("source_lines") or []) if isinstance(n, int)})
    if len(lines) == 2:
        return list(range(lines[0], lines[1] + 1))
    return lines


def compound_cited(rows) -> list[int]:
    """The union over every provenance row for one identifier. Exact lines."""
    out: set[int] = set()
    for row in rows:
        out.update(n for n in (row.get("source_lines") or []) if isinstance(n, int))
    return sorted(out)


# ---------------------------------------------------------------- record model

class Record:
    """One gold record, with its identity, its citation and its check results."""

    __slots__ = ("record_id", "kind", "label_en", "section_en", "cited",
                 "claims", "checks", "svg", "uuid", "rec", "flags")

    def __init__(self, record_id, kind, label_en, section_en, cited, svg=None,
                 uuid=None, rec=None, flags=()):
        self.uuid = uuid
        self.record_id = record_id
        self.kind = kind
        self.label_en = label_en
        self.section_en = section_en
        self.cited = cited
        self.svg = svg
        # The verdict key verifier/lib/verdict.ts resolveRec() understands. Emitted
        # rather than left for the UI to reconstruct, because reactions key on
        # reaction_id and everything else keys on a uuid, and a consumer that
        # guesses one rule for all four writes verdicts that never load again.
        self.rec = rec
        # The annotation's own validation_flags. Carried on the record so a check
        # that rediscovers one can say "the annotation flagged this too" instead of
        # presenting it as a new finding.
        self.flags = list(flags)
        self.claims: list[dict] = []
        self.checks: list[dict] = []

    @property
    def stratum(self) -> str:
        return f"{self.kind}:{self.section_en}"

    def failing(self) -> bool:
        return any(c["status"] == "fail" for c in self.checks)



def ascii_key(text: str) -> str:
    """A stable ASCII key for a string that may be Chinese.

    Five of the 75 compound identifiers in this gold are Chinese, so five gold ids
    and every field name built from them are Chinese too. Keys are not human-facing
    strings and are not covered by the `_en` rule, but they still land in a file
    whose whole promise is that a reader who has no Chinese can open it, and they
    are still grepped for Han characters as the last gate before it ships.

    Translating them instead would be worse. `claim_id` is a hash of `(record_id,
    field)` and the contract promises it is stable across runs; a record_id derived
    from the translation table would move the moment somebody improved a name, and
    every verdict a reviewer had already recorded against it would orphan. Hashing
    the Chinese itself is ASCII, is stable forever, and the readable name travels
    beside it as `label_en`, with `uuid` as the join key back into the gold.
    """
    if not has_chinese(text):
        return text
    return "zh-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def safe_record_id(patent_id: str, gold_id: str, identifier: str) -> str:
    return gold_id if not has_chinese(gold_id) else f"{patent_id}_{ascii_key(identifier)}"


def claim_id(record_id: str, field: str) -> str:
    return hashlib.sha256(f"{record_id}\x1f{field}".encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------- claim building

FIELD_LABELS = {
    "quantity.mass_g": "Mass charged",
    "quantity.volume_ml": "Volume charged",
    "quantity.mmol": "Amount charged, in millimoles",
    "quantity.equivalents": "Equivalents",
    "quantity.yield_pct": "Yield",
    "melting_point.min_c": "Melting point, low end",
    "melting_point.max_c": "Melting point, high end",
    "purity_pct": "Purity",
    "analytics.value": "Analytical measurement",
    "conditions.temperature.value_c": "Reaction temperature",
    "conditions.temperature.min_c": "Reaction temperature, low end",
    "conditions.temperature.max_c": "Reaction temperature, high end",
    "conditions.time_h": "Reaction time",
    "conditions.concentration.value": "Reagent concentration",
    "product_yield_pct": "Yield of the product",
    "overall_yield_pct": "Overall yield of the route",
    "extraction_rollup.best_overall_yield_pct": "Best overall yield in the patent",
    "molar_ratio_text": "Molar ratio",
    "provenance.quote": "Quoted source text",
    "validation_flags": "A defect the annotation found in the patent",
    "resolved": "Whether this is a definite molecule",
    "judgement.reaction_class_confidence": "Reaction class, self-declared as "
                                           "uncertain",
    "judgement.linkage_confirmed": "Which step this one follows",
    "judgement.cross_reference_unresolved": "An unresolved cross-reference",
    "judgement.validation_flags": "The annotation's own validation flags",
    "judgement.is_complete": "Whether this step is fully recorded",
    "__coverage__": "Source line no record cites",
    "__quantity__": "A quantity the patent prints that nothing records",
    "quantity_verdict": "Why the quantity has nowhere to live",
}

# A field name carries the row it came from: `compounds[toluene].quantity.mass_g`.
# The label is about the KIND of field, so the row is stripped before the lookup and
# the compound prefix with it, or every row of every reaction would need its own
# label and none of them would have one.
FIELD_INDEX = re.compile(r"\[[^\]]*\]")


def field_label(field: str) -> str:
    bare = FIELD_INDEX.sub("", field)
    for candidate in (bare, bare[len("compounds."):] if
                      bare.startswith("compounds.") else bare):
        if candidate in FIELD_LABELS:
            return FIELD_LABELS[candidate]
    return bare

UNIT_WORDS = {"g": "grams", "ml": "millilitres", "mmol": "millimoles",
              "%": "per cent", "C": "degrees Celsius", "h": "hours", None: ""}

HIGHLIGHT_KIND = {
    "quantity.yield_pct": "yield", "product_yield_pct": "yield",
    "conditions.temperature": "condition", "conditions.time_h": "condition",
}

# What the reviewer actually DOES with a row, which is not what `about` says. 56 of
# this patent's tier-1 claims were labelled `about: patent` and only 8 of them were
# judgements; the rest were "does the patent say 34 g" comparisons that happened to
# sit on a record carrying a patent-defect flag. `about` describes the record, this
# describes the work, and the measured cost differs by a factor of 2.3:
#
#     judgement    8.3 s median    read the evidence and form an opinion
#     comparison   3.6 s median    look at the highlighted number and agree
#
# So the queue can order on it and a UI can warn the reviewer what they are in for.
# Timings measured over 20 claims by an agent reader; treat them as a floor for a
# fast human rather than an average one.
WORK_SECONDS_MEASURED = {"judgement": 8.3, "comparison": 3.6}

# Fields where there is nothing to compare against and an opinion is the answer.
JUDGEMENT_FIELDS = ("validation_flags", "resolved", "judgement.",
                    "__coverage__", "__quantity__", "__schema__")


def work_kind(field: str, auto: str) -> str:
    """`judgement` or `comparison`: has the machine got something to SHOW you?

    Not "is there a number". A quote the machine located and highlighted is a
    comparison - the reviewer looks at the marked span and agrees - even though it
    carries no `claimed_value`. Keying on the value classified all 176 quote claims
    as judgements and put 163 of them in tier 3, which would have told a UI that
    sampling tier 3 costs twice what it does.

    So the test is whether the machine has a located thing to put on screen. It
    does for anything it settled; it does not for a field where an opinion is the
    only possible answer, or for a verdict of `not_checkable`, which means exactly
    "no opinion available".
    """
    if field.startswith(JUDGEMENT_FIELDS):
        return "judgement"
    return "judgement" if auto == "not_checkable" else "comparison"


BASE_RISK = {"not_found": 0.90, "not_reconciled": 0.85, "partial": 0.55,
             "not_checkable": 0.30, "found": 0.05}

# The quantity fields a record can carry, and the unit each is stated in.
QUANTITY_FIELDS = (("mass_g", "g"), ("volume_ml", "ml"), ("mmol", "mmol"),
                   ("equivalents", None), ("yield_pct", "%"))

# What each of the annotation's own validation flags says, in English. These are
# statements about the PATENT, and the wording has to keep that straight: a reviewer
# asked to mark a mass_balance_implausible reaction "wrong" would be being asked to
# reject a correct annotation of a defective document.
FLAG_MEANING_EN = {
    "no_conditions": "the patent states no reaction conditions for this step",
    "route_attribution_unclear": "it is unclear whether this step belongs to the "
                                 "prior art or to the invention",
    "mass_balance_implausible": "the masses printed for this step do not balance",
    "molar_mass_inconsistent": "the mass and the molar amount printed for a "
                               "reagent imply the wrong molecular weight",
    "drawing_text_conflict": "the drawn scheme and the written procedure disagree",
    "reagent_written_not_drawn": "a reagent named in the text is missing from the "
                                 "drawing",
    "reagent_drawn_not_written": "a reagent in the drawing is missing from the text",
    "scale_discontinuity": "the amount carried into this step does not match the "
                           "amount the previous step produced",
}


# Units that make a number a QUANTITY rather than an index, a locant or an NMR
# shift. A bare number is deliberately excluded: the NMR lines are full of them and
# a sweep that counts them reports the whole of Example 1 as dropped.
QUANTITY_UNITS = ("g", "ml", "mmol", "%", "C", "h")

# Glassware. "500ml four-necked reaction flask" prints a volume that is the size of
# the vessel and not a charge of anything, and `reactor_type` records the flask
# without its capacity. Six of them in this patent. Counted and reported, never
# queued, because asking a reviewer whether we dropped the flask is a waste of the
# only thing they are short of.
VESSEL_WORDS = ("反应瓶", "反应容器", "反应釜", "四口", "三口", "烧瓶",
                "flask", "reactor", "vessel", "autoclave", "necked")
VESSEL_WINDOW = 12

# A percentage is a yield or a concentration and the schema has a different field
# for each. Decided from the words beside it, never from which field happens to be
# free: 36%HCl is the strength of the acid, and reading it as a yield because
# `product_yield_pct` was occupied would report a false second stage.
YIELD_WORDS = ("收率", "产率", "得率", "yield")
YIELD_WINDOW = 12

# How a quantity is SAID back to the reviewer: in the unit the page prints, not the
# unit this stage converts to. "50 min" printed as "50 h" is the matcher lying about
# the document, and 50 min is exactly what line 227 says.
RAW_UNIT_EN = {"g": "g", "kg": "kg", "mg": "mg", "ml": "ml", "l": "L", "L": "L",
               "mol": "mol", "mmol": "mmol", "h": "h", "hr": "h", "hrs": "h",
               "min": "min", "%": "%", CELSIUS_MARK: "degrees C",
               "mL": "ml", "hour": "h", "hours": "h", "小时": "h", "分钟": "min"}


def say_quantity(value: float, raw_unit: str | None, high: float | None = None) -> str:
    unit = RAW_UNIT_EN.get(raw_unit or "", raw_unit or "")
    head = fmt_value(value) if high is None else f"{fmt_value(value)}-{fmt_value(high)}"
    return f"{head}{unit}" if unit == "%" else f"{head} {unit}".strip()


def derivation(field: str, quantity: dict, mw: float | None,
               name_en: str) -> dict | None:
    """How a field's value could be recomputed, if it is not quoted at all.

    Only `mmol` has one in this schema, and it is the important one. A row printing
    both a mass and a molar amount is an implicit claim about molecular weight, and
    the arithmetic is the same arithmetic verifier/lib/checks.ts already runs from
    the other side, so the tolerance is taken from there rather than reinvented.
    """
    if field != "mmol":
        return None
    mass = quantity.get("mass_g")
    if mass is None:
        return None
    return {"kind": "mmol_from_mass", "mass_g": float(mass), "mw": mw,
            "name_en": name_en}


def fmt_value(value: float) -> str:
    """The shortest honest rendering. 34.0 prints as 34, 25.25 stays 25.25."""
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def fmt_quantity(value: float, unit: str | None) -> str:
    if unit == "%":
        return f"{fmt_value(value)}%"
    if unit == "C":
        return f"{fmt_value(value)} C"
    return f"{fmt_value(value)} {unit}".strip() if unit else fmt_value(value)


class Engine:
    """Everything the run needs, assembled once and then asked questions."""

    def __init__(self, patent_id: str, data: dict):
        self.patent_id = patent_id
        self.data = data
        self.index = data["translations"]
        self.source = Source(patent_id, self.index)
        self.section_of_line, self.claim_lines, self.section_order = section_index(
            data["sections"], self.source)

        self.structures = {e["identifier"]: e for e in data["structures"]}
        self.group_of: dict[str, str] = {}
        for key, members in data["equivalence"].items():
            for m in members:
                self.group_of[m] = key

        self.compound_by_id = {c["identifier"]: c for c in data["compounds"]}
        self.compound_prov: dict[str, list] = {}
        for row in data["compound_prov"]:
            self.compound_prov.setdefault(row["identifier"], []).append(row)
        self.reaction_prov = {row["reaction_id"]: row for row in data["reaction_prov"]}

        # name -> what to look for, built once. English needles are kept long
        # enough not to fire inside another name: "water" would otherwise match
        # every occurrence of "washed with water" and name a reagent on 40 lines.
        self._name_index: list[tuple[str, str, str]] = []
        self._names_cache: dict[int, list[str]] = {}
        self.records: list[Record] = []
        self.claims: list[dict] = []
        self.record_of: dict[int, Record] = {}
        # record_id -> the gold dict it was built from. The quantity sweep needs to
        # ask a record which of its fields would have held a number, and that is a
        # question about the gold shape rather than about anything this stage keeps.
        self.raw_of: dict[str, dict] = {}
        self.cited_lines: dict[int, set[str]] = {}
        self.bases: dict[str, dict] = {}
        self.agreement = {"both": [], "machine_only": [], "annotation_only": []}

    # -------------------------------------------------------------- helpers

    def english_name(self, name: str | None) -> str:
        if not name:
            return "(unnamed)"
        if has_chinese(name):
            entry = self.index.get(name) or {}
            return scrub(entry.get("en") or name, self.index)
        return name

    def canon_name(self, name: str) -> str:
        return self.group_of.get(name, name)

    def svg_for(self, identifier: str) -> str | None:
        entry = self.structures.get(identifier)
        if entry and entry.get("svg"):
            return f"output/relevant_output/{entry['svg']}"
        return None

    def cumulative_yield(self, pathway) -> float | None:
        """The product of every step yield along a route, as a percentage.

        None when any step has no yield, because a route with a hole in it has no
        overall yield and reporting the product of the steps that do have one would
        silently overstate it.
        """
        product = 1.0
        for st in pathway.get("steps") or []:
            y = st.get("product_yield_pct")
            if y is None:
                return None
            product *= float(y) / 100.0
        return round(product * 100.0, 1)

    # ------------------------------------------------- quoted versus derived

    def resolve_bases(self) -> None:
        """Which numeric fields this document QUOTES, and which it DERIVES.

        Measured, never declared. For every numeric field name, count how many of
        its values are literally printed on the lines the record itself cites. On
        this patent the split is total:

            mass_g      22 of 22 printed        volume_ml   8 of 8 printed
            yield_pct    7 of 7  printed        mmol        0 of 10 printed

        `mmol` is never written in this patent. Every molar amount in the gold was
        calculated by the annotator from a mass and a molecular weight. A grounding
        check that does not know this reports ten hallucinations that are not
        hallucinations, at the top of a queue with about forty real items in it, and
        a reviewer whose first five rows are all the machine being wrong stops
        trusting it. Nothing after that matters.

        So a field nothing ever quotes is not checked for grounding at all. It is
        checked by RECOMPUTING it, which is a stronger test than the string match
        would have been and catches things no string match could. Bromine is the
        one that fails here: 39.6 g against 220 mmol implies 180.0 g/mol and bromine
        is 159.81, so either the mass or the amount is wrong and they cannot both be
        right. That is what tier 1 should be full of.

        Inferred per patent rather than hardcoded, because the next document may
        state its molar amounts and omit its masses, and a constant list would then
        be wrong in the direction that hides defects.
        """
        tally: dict[str, dict] = {}
        for claim in self.claims:
            name = claim.get("_field_name")
            if name is None:
                continue
            t = tally.setdefault(name, {"total": 0, "matched": 0})
            t["total"] += 1
            t["matched"] += 1 if claim.get("_matched") else 0

        for name, t in tally.items():
            t["basis"] = ("derived" if t["matched"] == 0 and t["total"] >= 3
                          else "quoted")
        self.bases = tally

        for claim in self.claims:
            name = claim.get("_field_name")
            if name is None:
                continue
            basis = tally[name]["basis"]
            claim["basis"] = basis
            if basis == "quoted" or claim.get("_matched"):
                continue
            self.rescore_derived(claim, name, tally[name])

    def rescore_derived(self, claim: dict, name: str, tally: dict) -> None:
        """Re-ask a derived field the only question there is about it."""
        d = claim.get("_derive")
        value = claim["_value"]
        preface = (f"This patent never prints a value for {name}: none of the "
                   f"{tally['total']} in the annotation appears on any line any "
                   f"record cites. It is calculated, not quoted, so the question "
                   f"is whether the calculation holds. ")
        claim["question_en"] = (f"The annotation calculated {claim['claimed_en']} "
                                f"for {claim['_subject']}. Does that calculation "
                                f"hold?")
        if d is None:
            claim["auto"] = "not_checkable"
            claim["auto_reason_en"] = (
                preface + "This stage has no way to recompute it from the other "
                "fields on the record, so a human must check it against the "
                "patent.")
            claim["risk_reasons_en"] = ["A calculated number with nothing to check "
                                        "it against."]
            claim["risk"] = 0.35
            claim["load_bearing"] = True
            claim["needs_human"] = True
            return

        if d["mw"] is None:
            claim["auto"] = "not_checkable"
            claim["auto_reason_en"] = (
                preface + f"It should be the {d['mass_g']} g charged divided by the "
                f"molecular weight of {d['name_en']}, but no structure is resolved "
                f"for that molecule, so there is no molecular weight to divide by.")
            claim["risk_reasons_en"] = ["A calculated number whose molecule has no "
                                        "resolved structure."]
            claim["risk"] = 0.35
            claim["load_bearing"] = True
            claim["needs_human"] = True
            return

        implied = d["mass_g"] / (value / 1000.0)
        delta = implied - d["mw"]
        tol = max(ABS_TOL_FLOOR, REL_TOL * d["mw"])
        arithmetic = (f"{d['mass_g']} g of {d['name_en']} at "
                      f"{d['mw']:.2f} g/mol is "
                      f"{d['mass_g'] / d['mw'] * 1000:.1f} mmol")
        if abs(delta) <= tol:
            claim["auto"] = "not_checkable"
            claim["auto_reason_en"] = (
                preface + f"The calculation checks out: {arithmetic}, and the "
                f"annotation records {fmt_value(value)} mmol. Implied molecular "
                f"weight {implied:.2f} against {d['mw']:.2f}, within tolerance "
                f"{tol:.2f}.")
            claim["risk_reasons_en"] = []
            claim["risk"] = 0.10
            claim["load_bearing"] = False
            claim["needs_human"] = True
            return

        rec = self.record_of.get(id(claim))
        flagged = bool(rec and ({"molar_mass_inconsistent",
                                 "mass_balance_implausible"} & set(rec.flags)))
        cl_for_h = abs(delta + CL_FOR_H) < CL_WINDOW
        claim["auto"] = "not_reconciled"
        claim["risk"] = 0.95
        claim["load_bearing"] = True
        claim["needs_human"] = True
        tail = ""
        if cl_for_h:
            tail = (f" The shortfall of {delta:+.2f} is very close to the "
                    f"{-CL_FOR_H:+.2f} that swapping one chlorine for one hydrogen "
                    f"would cost, which is a lead for the reviewer and not a "
                    f"diagnosis.")
        if flagged:
            claim["about"] = "patent"
            claim["question_en"] = (
                f"The patent's own numbers for {claim['_subject']} do not agree "
                f"with each other. The annotation recorded them as printed and "
                f"flagged it. Was that the right call?")
            claim["auto_reason_en"] = (
                preface + f"It does not: {arithmetic}, but the annotation records "
                f"{fmt_value(value)} mmol, an implied molecular weight of "
                f"{implied:.2f} against {d['mw']:.2f}.{tail} The annotation flagged "
                f"this step itself, so this is very likely a defect in the patent "
                f"that was correctly recorded rather than an extraction error.")
            claim["risk_reasons_en"] = [
                "The mass and the molar amount printed for this reagent cannot "
                "both be right.",
                "The annotation already flagged this step, so confirming it is "
                "quick."]
        else:
            claim["auto_reason_en"] = (
                preface + f"It does not: {arithmetic}, but the annotation records "
                f"{fmt_value(value)} mmol, an implied molecular weight of "
                f"{implied:.2f} against {d['mw']:.2f}, outside the tolerance of "
                f"{tol:.2f}.{tail} The annotation did NOT flag this step, so either "
                f"it missed a defect in the patent or one of the two numbers was "
                f"read wrong.")
            claim["risk_reasons_en"] = [
                "The mass and the molar amount cannot both be right.",
                "The annotation did not flag this step, so nobody has looked at "
                "it yet."]

    # ------------------------------------------------- the agreement matrix

    def agreement_matrix(self) -> None:
        """This stage's arithmetic findings against the annotation's own flags.

        Three buckets, and the two disagreements are where the information is.
        Rediscovering `molar_mass_inconsistent` and presenting it as a new finding
        would be this stage taking credit for a defect the annotator had already
        found and written up. What is worth a reviewer's time is a step this stage
        fails that the annotation passed, and what is worth THIS STAGE's authors'
        time is a step the annotation flagged that this stage could not see.
        """
        machine = {r.record_id for r in self.records
                   if r.kind == "reaction"
                   and any(c["family"] == "quantity" and c["status"] == "fail"
                           for c in r.checks)}
        annotated = {r.record_id for r in self.records
                     if r.kind == "reaction"
                     and {"molar_mass_inconsistent", "mass_balance_implausible"}
                     & set(r.flags)}
        label = {r.record_id: r.label_en for r in self.records}
        self.agreement = {
            "both": sorted(label[i] for i in machine & annotated),
            "machine_only": sorted(label[i] for i in machine - annotated),
            "annotation_only": sorted(label[i] for i in annotated - machine),
        }

    # ------------------------------------------------- the three review queues

    def promoted_fields(self) -> dict[str, list[str]]:
        """Record -> the claim-field prefixes some failing check on it names.

        A check that names no field promotes nothing. This used to append "" for
        such a check, and "" is a prefix of every field name, so ONE fieldless
        failure pulled every claim on its record into the census. Two
        `completeness.unmapped` checks on US20100041557A1's tembotrione record
        promoted all 33 of its claims that way, and the two numbers behind them
        are "at least 95 wt. % consists of the crystalline form A": a limit on
        what the patent claims, which no field on a compound record can hold and
        which recording as purity_pct would misreport as an assay.

        Nothing is hidden by dropping the blanket. A failing check is already a
        tier 1 claim in its own right through the `_finding` branch of
        assign_tiers, and the completeness family also emits its own tier 2
        `__quantity__` claim per number, so the reviewer still meets every one.
        """
        out: dict[str, list[str]] = {}
        for rec in self.records:
            for c in rec.checks:
                if c["status"] != "fail":
                    continue
                out.setdefault(rec.record_id, [])
                out[rec.record_id].extend(f for f in (c["about_fields"] or []) if f)
        return out

    def assign_tiers(self) -> None:
        """Which queue in REVIEW-PROTOCOL.md each claim belongs to.

        Tier is the queue and risk is the order within it. They answer different
        questions: risk says how alarming one claim is, tier says which census a
        reviewer with 900 seconds is working through when they meet it.

            1  the machine LOOKED AND FAILED. A census, not a sample.
            2  the candidate misses, the recall side. Also a census.
            3  the machine matched it cleanly, sampled rather than read.
            4  the machine had NO OPINION. Sampled, and not part of tier 3's bound.

        Tier 4 exists because of a measurement. The census was tier 1 plus tier 2,
        93 claims, and the queue has now been timed at a 5.3 s median and an 8.7 s
        p90. At the pessimistic rate 93 claims eat the whole 15 minutes and tier 3
        is sampled ZERO times, which does not merely slow the reviewer down: it
        leaves the report with no confidence bound at all. Demoting the 29
        `not_checkable` claims brings the census to 64, which fits at every rate
        measured and leaves budget for the sample.

        The reason it is right and not merely convenient: "the machine had no
        opinion" is a different population with a different prior from "the machine
        looked and failed". They should never have shared a census. They must also
        not join tier 3, whose bound is specifically the residual defect rate among
        claims the machine MATCHED - a claim it never matched would silently widen
        the very estimate it has no evidence about.
        """
        promoted = self.promoted_fields()
        for claim in self.claims:
            prefixes = promoted.get(claim["record_id"], [])
            if (claim["field"] == "__coverage__"
                    or claim["field"].startswith("__quantity__")
                    or claim["field"].startswith("__schema__")):
                claim["tier"] = 2
            elif claim["auto"] in ("not_found", "not_reconciled", "partial"):
                claim["tier"] = 1
            elif claim.get("_finding"):
                # `not_checkable` means the machine had NO OPINION, and tier 4 is
                # sampled on that basis. A claim that REPORTS a failing check is
                # the opposite: the machine looked and found something specific,
                # and it cannot be settled by a string match only because the
                # judgement is a human one. Sampling those would be sampling the
                # findings, which is the one population that must be a census.
                claim["tier"] = 1
            elif claim["auto"] == "not_checkable":
                claim["tier"] = 4
            elif any(claim["field"].startswith(pre) for pre in prefixes):
                claim["tier"] = 1
                claim["needs_human"] = True
                claim["risk"] = max(claim["risk"], 0.70)
                claim["risk_reasons_en"] = claim["risk_reasons_en"] + [
                    "A check on this row failed, so the number is worth reading "
                    "even though it is printed where the record says it is."]
            else:
                claim["tier"] = 3

    def assign_severity(self) -> None:
        """How bad is this one, as distinct from which queue it is in.

        Tier says a human must look. Severity says what they will find when they
        do, and the whole point is that these five things must not share a badge:

            derived            none      should never have reached the reviewer
            pointer misplaced  low       fix the citation, the fact stands
            quote off the line low       fix the quote, the citation stands
            judgement          medium    only a reader can settle it
            patent disagrees   high      the document contradicts itself
            not in the patent  critical  nobody can source this number

        The hand triage of this patent's twelve `not_found` claims found three
        derived, five misplaced pointers, four loose quotes and ZERO fabrications.
        One label over all four teaches a reviewer that the label means nothing,
        and the label is the only thing standing between the team and a fabricated
        number in a future run. When a real one finally arrives it must not turn up
        wearing the same badge as a citation that is four paragraphs out.

        `critical` is reserved: it fires only when the claimed value is on no line
        of the document at all, which `_elsewhere` records at the point the search
        was actually made.
        """
        for claim in self.claims:
            auto, basis = claim["auto"], claim.get("basis")
            elsewhere = claim.get("_elsewhere")
            derived = basis == "derived"

            if auto == "not_reconciled":
                # The derivation was recomputed and disagreed. The numbers are the
                # patent's own, so this is the document contradicting itself.
                sev = "high"
                action = ("Two numbers the patent prints for this reagent cannot "
                          "both be right. Confirm which one the page says.")
            elif auto == "not_found" and elsewhere:
                sev = "low"
                action = ("The fact is right and the pointer is wrong. Move the "
                          "citation to " + compact_lines(elsewhere) + ".")
            elif auto == "not_found":
                sev = "critical"
                action = ("This value is on no line of the patent. Either it was "
                          "invented or it came from somewhere nobody recorded. "
                          "Read this one first.")
            elif auto == "partial" and elsewhere:
                sev = "low"
                action = ("The citation stands and the quoted text does not come "
                          "from it. Fix the quote rather than the pointer.")
            elif auto == "partial":
                sev = "medium"
                action = ("Part of the claim is on the cited lines and part is "
                          "not. Read the evidence and decide.")
            elif auto == "not_checkable" and claim.get("quantity_verdict"):
                # A quantity with nowhere to live. The two shapes need opposite
                # fixes, so they must not share an action: a schema loss is not a
                # data defect and a reviewer cannot adjudicate it, while an empty
                # field is a re-extraction they CAN settle by reading the page.
                if claim["quantity_verdict"].startswith("schema_loss"):
                    sev = "low"
                    action = ("Nothing here is wrong and nothing here can be "
                              "marked wrong. The patent prints this, the "
                              "annotation read it, and the field it had to go in "
                              "is too small to hold it. This is a schema ticket, "
                              "not a review decision.")
                else:
                    sev = "medium"
                    action = ("The patent prints this and the field that would "
                              "hold it is empty. Decide whether the extraction "
                              "missed it or left it out on purpose.")
            elif auto == "not_checkable" and claim["field"] == "__coverage__":
                sev = "medium"
                action = ("Nothing cites this line. Decide whether the extraction "
                          "missed it or a nearby record already has it.")
            elif auto == "not_checkable" and claim["load_bearing"]:
                sev = "medium"
                action = ("A judgement no string match can settle. Read the "
                          "evidence and agree or overrule.")
            elif derived:
                sev = "none"
                action = ("A calculated value whose calculation checks out. "
                          "Nothing to do.")
            else:
                sev = "none"
                action = ("The machine found this where the record says it is. "
                          "Bulk-acceptable.")

            # A claim the machine matched, sitting on a record whose arithmetic
            # failed, is not severity none however well the string matched. Where
            # the failing check is the mass-against-moles arithmetic, the two
            # numbers are the PATENT's own and cannot both be right, which is the
            # `high` case: nothing is wrong with the extraction and something is
            # wrong with the document. Without this branch `high` could never fire
            # on this patent, and a severity level that cannot fire is decoration.
            if sev == "none" and claim["tier"] == 1:
                rec = self.record_of.get(id(claim))
                arithmetic = [c for c in (rec.checks if rec else [])
                              if c["family"] == "quantity" and c["status"] == "fail"]
                if arithmetic:
                    sev = "high"
                    claim["about"] = "patent"
                    action = ("The value is printed exactly where the record says "
                              "it is. What disagrees is the patent with itself: "
                              + arithmetic[0]["detail_en"])
                else:
                    sev = "medium"
                    action = ("The value is printed where the record says it is, "
                              "but a check on this row failed, so it is worth "
                              "reading.")

            claim["severity"] = sev
            claim["severity_action_en"] = action

    def note_citation(self, record_id: str, lines) -> None:
        for n in lines:
            self.cited_lines.setdefault(n, set()).add(record_id)

    def names_on(self, n: int) -> list[str]:
        """The substances the annotation knows that this line names, in English.

        THE ONE FACT A MISATTACHMENT TURNS ON, and the only help available for it.
        A planted defect moved a real 40.5 g from aluminium trichloride onto
        2-chlorotoluene. Both are real, both are on line 187, so grounding passes
        and the verdict `found` is correct. No cheap machine test separates them:
        requiring the cited line to name the compound passes too, because line 187
        names both.

        What a reviewer is missing is not evidence, it is the fact that the line
        names three substances and the number belongs to one of them. This does not
        settle the question and is not meant to. It hands over the missing fact and
        leaves the judgement where it belongs.
        """
        cached = self._names_cache.get(n)
        if cached is not None:
            return cached
        norm = self.source.norm.get(n, "")
        english = (self.source.text_en.get(n, "") or "").lower()
        hits: list[tuple[str, str]] = []
        for label, zh_needle, en_needle in self._name_index:
            # Word boundaries, so "toluene" does not fire inside
            # "2-chlorotoluene". Chinese has no boundaries and needs none: the
            # names are long enough to be unambiguous.
            if (zh_needle and zh_needle in norm) or (
                    en_needle and re.search(r"\b" + re.escape(en_needle) + r"\b",
                                            english)):
                if not any(label == l for l, _, _ in hits):
                    hits.append((label, zh_needle, en_needle))
        # A needle contained in another needle that also matched is the same
        # mention read twice: "water" inside "ice water", "dichloromethane" inside
        # "1,2-dichloromethane", "aluminium trichloride" inside "anhydrous
        # aluminium trichloride". Naming both tells the reviewer the line mentions
        # two substances where it mentions one, which is a worse error here than
        # naming too few: the whole point is to say what the number might belong to.
        def swallowed(mine: str, index: int) -> bool:
            """Is this string a proper part of another hit's string at the same
            position? Compared on the LABEL too, because the two halves of a pair
            can match in different languages: `dichloromethane` matched the English
            and `1,2-dichloromethane` matched the Chinese, so neither needle could
            see the other and the line named a solvent it does not contain."""
            return any(mine and mine != other[index] and mine in other[index]
                       for other in hits)

        found = [label for label, zh, en in hits
                 if not swallowed(label, 0)
                 and not swallowed(zh, 1) and not swallowed(en, 2)]
        self._names_cache[n] = found
        return found

    def evidence(self, cited: list[int], hit_lines: set[int]) -> list[dict]:
        """The evidence panel: every line that mattered, then the rest, capped.

        `pairing` says how the English on a Chinese line was arrived at, so a screen
        can mark the four lines in this document whose translation had to be clamped
        rather than paired one for one. `is_translation` says whether what is shown
        is a translation at all or the literal characters on the line.
        """
        ordered = sorted(cited, key=lambda n: (n not in hit_lines, n))
        shown = sorted(ordered[:EVIDENCE_LINE_CAP])
        return [{"n": n,
                 "text_en": self.source.text_en.get(n, ""),
                 "is_translation": self.source.is_translation.get(n, False),
                 "kind": self.source.label_kind(n, self.claim_lines),
                 "pairing": self.source.pairing.get(n, "self"),
                 "names_en": self.names_on(n),
                 "matched": n in hit_lines}
                for n in shown]

    # -------------------------------------------------------------- numeric claim

    def locate(self, cited, value: float, unit: str | None):
        """Where on the cited lines this quantity is printed, if it is at all.

        Three strengths, and the difference between them is what a reviewer needs.
        `exact` is the number with its unit beside it. `loose` is the number with
        no unit, which is a real state in this document: the patent prints thionyl
        chloride as "71.4(0.6mol)" with no g anywhere. `comma` is the number only
        if a comma on the line is read as a decimal point, which is offered last
        and never silently, because this document is full of 1,2-dichloroethane.
        """
        exact, loose, comma = [], [], []
        for n in cited:
            text = self.source.lines.get(n, "")
            for tok in tokenise(text):
                if tok.unit == unit and same_number(tok.canonical(), value):
                    exact.append((n, tok))
                elif tok.unit is None and same_number(tok.value, value):
                    loose.append((n, tok))
                elif unit is None and same_number(tok.value, value):
                    loose.append((n, tok))
            if not exact and not loose:
                if any(same_number(v, value) for v in comma_decimals(text)):
                    comma.append(n)
        return exact, loose, comma

    def numeric_claim(self, rec: Record, field: str, value: float,
                      unit: str | None, subject_en: str,
                      highlight_kind: str = "value",
                      field_name: str | None = None,
                      derive: dict | None = None) -> dict:
        """One number, asked of the lines its own record cites.

        Four verdicts and what each means to a reviewer who cannot read the patent:

            found        the number and its unit are both printed on a cited line
            partial      the number is there without its unit, or only in one of the
                         two languages, or only as a comma-decimal reading
            not_found    the number is on none of the cited lines. Read this one
            not_checkable the record cites no line at all, so nothing can be asked

        The verdict is provisional until `resolve_bases()` has run. A field that no
        record ever quotes is DERIVED rather than absent, and scoring it here as
        ungrounded would fill the review queue with the machine being wrong about a
        field the patent never states. See resolve_bases().
        """
        cited = rec.cited
        claimed_en = fmt_quantity(value, unit)
        question = (f"Does the patent say {claimed_en} of {subject_en}?"
                    if unit in ("g", "ml", "mmol")
                    else f"Does the patent say {claimed_en} for {subject_en}?")
        extra = {"basis": "quoted", "_field_name": field_name or field.split(".")[-1],
                 "_derive": derive, "_value": value, "_unit": unit,
                 "_subject": subject_en}

        if not cited:
            return self._claim(rec, field, question, claimed_en, value, unit,
                               [], [], "not_checkable",
                               "This record cites no source line, so there is "
                               "nothing to check the number against.",
                               ["The record carries no provenance."],
                               highlight_kind, load_bearing=True, extra=extra)

        exact, loose, comma = self.locate(cited, value, unit)
        extra["_matched"] = bool(exact or loose or comma)
        hits = exact or loose
        hit_lines = {n for n, _ in hits} | set(comma)
        zh = sorted(n for n in hit_lines if self.source.kind[n] != "translation")
        en = sorted(n for n in hit_lines if self.source.kind[n] == "translation")

        where = []
        if zh:
            where.append("the Chinese line" + ("s " if len(zh) > 1 else " ")
                         + ", ".join(str(n) for n in zh))
        if en:
            where.append("the English translation on line"
                         + ("s " if len(en) > 1 else " ")
                         + ", ".join(str(n) for n in en))

        risk_reasons: list[str] = []
        if exact:
            auto = "found"
            reason = (f"The number {fmt_value(value)} appears with its unit "
                      f"{UNIT_WORDS.get(unit, unit or '')} on "
                      + " and on ".join(where) + ".")
            if not zh:
                auto = "partial"
                reason += (" It is printed only in the English machine translation, "
                           "not in the Chinese the patent actually says.")
                risk_reasons.append(
                    "The value is in the translation only, and the Chinese is the "
                    "authoritative text.")
        elif loose:
            auto = "partial"
            reason = (f"The number {fmt_value(value)} appears on "
                      + " and on ".join(where)
                      + f", but not with the unit "
                        f"{UNIT_WORDS.get(unit, unit or 'expected')}.")
            risk_reasons.append(
                "The unit was read from context rather than printed beside the "
                "number.")
        elif comma:
            auto = "partial"
            reason = (f"The number {fmt_value(value)} appears on "
                      + " and on ".join(where)
                      + " only if the comma there is read as a decimal point.")
            risk_reasons.append("The match depends on reading a comma as a decimal "
                                "point.")
        else:
            auto = "not_found"
            # "Not on the lines this record cites" and "not in this patent at all"
            # are the same verdict and completely different defects. The first is a
            # pointer four paragraphs out and the fact still stands; the second is a
            # number nobody can source, which is the only thing in this artifact
            # that deserves the word fabrication. Asked here, once, over the whole
            # document, so `severity` can tell them apart downstream.
            far_exact, far_loose, _ = self.locate(self.source.numbers, value, unit)
            elsewhere = sorted({n for n, _ in far_exact} or {n for n, _ in far_loose})
            extra["_elsewhere"] = elsewhere
            if elsewhere:
                reason = (f"The number {fmt_value(value)} is in the patent, on line"
                          f"{'s' if len(elsewhere) > 1 else ''} "
                          + compact_lines(elsewhere)
                          + f", but on none of the {len(cited)} lines this record "
                            f"cites ({compact_lines(cited)}). The value is real and "
                            f"the citation points somewhere else.")
                risk_reasons.append("The number is in the document but the record "
                                    "cites the wrong lines.")
            else:
                reason = (f"The number {fmt_value(value)} is on none of the "
                          f"{len(cited)} source lines this record cites "
                          f"({compact_lines(cited)}), and it is on no other line "
                          f"of the {len(self.source.lines)}-line document either.")
                risk_reasons.append("The claimed number is absent from the whole "
                                    "document, not merely from the lines cited.")

        highlights = []
        for n, tok in hits:
            for h in self.highlights_for(n, tok.value, unit, highlight_kind):
                highlights.append(h)
        return self._claim(rec, field, question, claimed_en, value, unit,
                           cited, highlights, auto, reason, risk_reasons,
                           highlight_kind, hit_lines, extra=extra)


    def highlights_for(self, line: int, value: float, unit: str | None,
                       kind: str) -> list[dict]:
        """Offsets of the value inside the English the panel will actually show."""
        text = self.source.text_en.get(line, "")
        out = []
        for tok in tokenise(text):
            if same_number(tok.value, value) or (
                    tok.unit == unit and same_number(tok.canonical(), value)):
                out.append({"line": line, "start": tok.start, "end": tok.end,
                            "kind": kind})
        return out

    # -------------------------------------------------------------- text claim

    def ratio_claim(self, rec: Record, field: str, ratio: str,
                    subject_en: str) -> dict:
        """A molar ratio such as 1:1-3:1-2, matched as printed.

        Ratios are the one numeric field that is not a quantity: there is no unit to
        convert and no single value to compare, so the printed form is the claim and
        a normalised substring search is the honest test of it.
        """
        needle = normalise(ratio)
        hit_lines = {n for n in rec.cited
                     if needle and needle in self.source.norm.get(n, "")}
        question = f"Does the patent state the molar ratio {ratio} for {subject_en}?"
        if not rec.cited:
            return self._claim(rec, field, question, ratio, None, None, [], [],
                               "not_checkable",
                               "This record cites no source line.",
                               ["The record carries no provenance."], "value")
        elsewhere: list[int] = []
        if hit_lines:
            reason = (f"The ratio {ratio} is printed on line"
                      f"{'s' if len(hit_lines) > 1 else ''} "
                      + ", ".join(str(n) for n in sorted(hit_lines)) + ".")
            auto, risk = "found", []
        else:
            elsewhere = sorted(n for n, t in self.source.norm.items()
                               if needle and needle in t)
            if elsewhere:
                reason = (f"The ratio {ratio} is in the patent, on line"
                          f"{'s' if len(elsewhere) > 1 else ''} "
                          + ", ".join(str(n) for n in elsewhere)
                          + f", but not on the lines this record cites "
                            f"({compact_lines(rec.cited)}).")
                risk = ["The ratio is real but the record cites the wrong lines."]
            else:
                reason = (f"The ratio {ratio} is nowhere in the source.")
                risk = ["The claimed ratio is absent from the whole document."]
            auto = "not_found"
        return self._claim(rec, field, question, ratio, None, None, rec.cited, [],
                           auto, reason, risk, "value", hit_lines,
                           extra={"_elsewhere": elsewhere})

    # -------------------------------------------------------------- quote claim

    def quote_claim(self, rec: Record, field: str, quote: str,
                    declared: list[int]) -> dict:
        """Is the quoted text on the lines the row that carries it declares?

        The quote itself never reaches the artifact: it is Chinese, and the reader
        has none. What reaches the artifact is the English of the lines the quote
        was found on, plus a sentence saying whether those are the lines the row
        claimed. That is the whole question a reviewer can answer here.
        """
        cited = rec.cited
        question = ("Is the text this record quotes actually on the source lines it "
                    "cites?")
        if not has_chinese(quote):
            # English annotator prose, not verbatim patent text. Tested as ASCII
            # against the cited lines and handed to a human either way, because a
            # sentence someone wrote about the patent is not a sentence in it.
            needle = normalise(quote)
            found = [n for n in cited if needle and needle in self.source.norm.get(n, "")]
            auto = "found" if found else "not_checkable"
            reason = ("This row quotes English annotator prose rather than the "
                      "patent's own words"
                      + (f", and that text is on line "
                         f"{', '.join(str(n) for n in found)}."
                         if found else
                         ", so no string match against the Chinese source can "
                         "settle it. A human must read it."))
            return self._claim(rec, field, question,
                               "an English note rather than a quotation",
                               None, None, cited, [], auto, reason,
                               [] if found else
                               ["The quote is a note, not patent text."],
                               "name", set(found))

        text = normalise(quote)
        spans, total, _ = cover(quote, cited, self.source.norm)
        cited_set = set(cited)
        covered: dict[int, int] = {}
        for a, b, n in spans:
            for k in range(a, b):
                covered[k] = n

        on, off, uncovered = 0, 0, 0
        off_lines: set[int] = set()
        on_lines: set[int] = set()
        for k, ch in enumerate(text):
            if not CJK.match(ch) or k not in covered:
                continue
            if covered[k] in cited_set:
                on += 1
                on_lines.add(covered[k])
            else:
                off += 1
                off_lines.add(covered[k])

        # The cover refuses any span shorter than MIN_SPAN, because a five-character
        # locant occurs on twenty lines and crediting a quote to whichever of them
        # sorted first would be worse than not crediting it. But a leftover shorter
        # than that is NOT evidence of absence, and reporting it as "found nowhere"
        # is the matcher crying wolf: the water record's quote leaves 有机层水洗 (five
        # characters, "the organic layer is washed with water") uncovered, and it is
        # plainly there on line 227. So every residue is looked up directly, and
        # only what survives that is called absent.
        short = 0
        for frag_start, frag_end in residue_runs(text, set(covered)):
            frag = trim_joiners(text[frag_start:frag_end])
            zh = sum(1 for ch in frag if CJK.match(ch))
            if not zh:
                continue
            here = next((n for n in cited if frag in self.source.norm.get(n, "")),
                        None)
            if here is not None:
                on += zh
                on_lines.add(here)
                short += 1
                continue
            there = next((n for n in sorted(self.source.norm)
                          if frag in self.source.norm[n]), None)
            if there is not None:
                off += zh
                off_lines.add(there)
                short += 1
            else:
                uncovered += zh

        risk_reasons: list[str] = []
        misplaced = False
        if total == 0:
            auto = "not_checkable"
            reason = ("The quotation carries no Chinese characters to locate.")
            risk_reasons.append("Nothing in the quotation can be matched.")
        elif on and not off and not uncovered:
            auto = "found"
            reason = (f"All {total} Chinese characters of the quotation are on line"
                      f"{'s' if len(on_lines) > 1 else ''} "
                      + ", ".join(str(n) for n in sorted(on_lines))
                      + ", which this record cites.")
        elif on:
            auto = "partial"
            bits = [f"{on} of the {total} Chinese characters of the quotation are on "
                    f"the cited line{'s' if len(on_lines) > 1 else ''} "
                    + ", ".join(str(n) for n in sorted(on_lines)) + "."]
            if off:
                bits.append(f"Another {off} were found on line"
                            f"{'s' if len(off_lines) > 1 else ''} "
                            + ", ".join(str(n) for n in sorted(off_lines))
                            + ", which this record does not cite.")
                risk_reasons.append("Part of the quotation is on lines the record "
                                    "does not cite.")
            if uncovered:
                bits.append(f"{uncovered} were found nowhere in the source.")
                risk_reasons.append("Part of the quotation is in no source line at "
                                    "all.")
            reason = " ".join(bits)
        elif off:
            auto = "not_found"
            # No verdict on WHICH of the two is wrong yet. When the cited line is a
            # drawing the citation is the right one and the quote is the loose half,
            # and saying "the record cites the wrong place" there is false. The
            # closing sentence is chosen below, once that is known.
            reason = (f"The quoted text is in the patent, on line"
                      f"{'s' if len(off_lines) > 1 else ''} "
                      + ", ".join(str(n) for n in sorted(off_lines))
                      + f", but on none of the {len(cited)} lines this record cites "
                        f"({compact_lines(cited)}).")
            misplaced = True
            risk_reasons.append("The quotation is real but the citation points "
                                "somewhere else.")
        else:
            auto = "not_found"
            reason = (f"None of the {total} Chinese characters of this quotation "
                      f"were found anywhere in the {len(self.source.lines)}-line "
                      f"source. The quotation may be invented.")
            risk_reasons.append("The quotation was not found anywhere in the "
                                "document.")

        # A record anchored only to the drawn scheme has no prose on its cited
        # line to match against. The text it quotes is narrative from nearby, which
        # is a citation pointing at the wrong line and worth reporting, but it is
        # not an invented quotation and must not sit at the top of a queue whose
        # top is reserved for those.
        if auto == "not_found" and cited and all(
                self.source.kind.get(n) in ("image_extract", "blank")
                for n in cited):
            auto = "partial"
            misplaced = False
            reason += (" The citation itself is right: this record is anchored to "
                       "the drawn scheme, which carries no prose at all, so it is "
                       "the QUOTE that does not come from the cited line. Fix the "
                       "quote, not the pointer.")
            risk_reasons = ["The record cites only the drawing, and quotes prose "
                            "that is somewhere else."]
        elif misplaced:
            reason += " The record cites the wrong place."

        panel = sorted(cited_set | off_lines)
        panel = self.source.with_partners(panel)
        claim = self._claim(rec, field, question,
                            self.quote_gist(quote, on_lines | off_lines),
                            None, None, cited, [], auto, reason, risk_reasons,
                            "name", on_lines | off_lines, panel_lines=panel,
                            extra={"_elsewhere": sorted(off_lines)})
        return claim

    def quote_gist(self, quote: str, lines: set[int]) -> str:
        """What the row quotes, said in English, without the Chinese.

        The index is keyed on the exact string, so a quote it holds is answered
        directly; otherwise the English of the lines the quote was found on is the
        closest true thing that can be said about it.
        """
        entry = self.index.get(quote) or {}
        if entry.get("en"):
            return scrub(entry["en"], self.index)
        if lines:
            parts = []
            for n in sorted(lines):
                t = self.source.text_en.get(n, "")
                if t and t not in parts:
                    parts.append(t)
            if parts:
                return " ... ".join(parts)
        return ("a passage of Chinese for which the pipeline carries no English")

    # -------------------------------------------------------------- assembly

    def _claim(self, rec: Record, field: str, question: str, claimed_en: str,
               claimed_value, claimed_unit, cited, highlights, auto, reason,
               risk_reasons, highlight_kind, hit_lines=frozenset(),
               panel_lines=None, about="extraction", load_bearing=False,
               rec_field=None, extra=None) -> dict:
        """Assemble one claim. Every field a reviewer or a sampler needs, inline.

        `about` is the question being asked, and it is not decoration. There are two
        completely different things a reviewer can be shown:

            extraction   the annotation says X and the patent says Y. We are wrong.
            patent       the annotation says the patent contradicts itself. We are
                         RIGHT and the document is defective.

        Blurring them asks a reviewer to mark a correct annotation as wrong, which
        is worse than not asking at all. FINDINGS.md is explicit that its items are
        defects in the patent and that the annotation changes nothing, and that
        posture has to survive into every question worded here.
        """
        panel = panel_lines if panel_lines is not None else cited
        risk = BASE_RISK[auto]
        if risk_reasons:
            risk = min(1.0, risk + 0.05 * (len(risk_reasons) - 1))
        claim = {
            "claim_id": claim_id(rec.record_id, field),
            "record_id": rec.record_id,
            "record_kind": rec.kind,
            "rec": rec.rec,
            "rec_field": rec_field if rec_field is not None else field,
            "record_label_en": rec.label_en,
            "section_en": rec.section_en,
            "stratum": rec.stratum,
            "about": about,
            "field": field,
            "field_label_en": field_label(field),
            "question_en": question,
            "claimed_en": claimed_en,
            "claimed_value": claimed_value,
            "claimed_unit": claimed_unit,
            "cited_lines": list(cited),
            "evidence_en": " ".join(
                self.source.text_en.get(n, "") for n in panel).strip(),
            "evidence_lines": self.evidence(panel, set(hit_lines)),
            "highlights": highlights,
            "auto": auto,
            "auto_reason_en": reason,
            "needs_human": auto != "found",
            "load_bearing": bool(load_bearing),
            "risk": round(risk, 2),
            "risk_reasons_en": risk_reasons,
            "structure_svg_path": rec.svg,
            "work_kind": work_kind(field, auto),
            "evidence_width": len(cited),
            "evidence_class": "wide" if len(cited) > WIDE_CITATION else "narrow",
            "basis": None,
            "tier": None,
            "severity": None,
            "severity_action_en": None,
        }
        if auto == "found" and claim["evidence_class"] == "wide":
            claim["risk_reasons_en"] = claim["risk_reasons_en"] + [
                f"The match is one of {len(cited)} cited lines. On a citation that "
                f"wide a two-digit number is likely to appear somewhere whether or "
                f"not it belongs to this record, so confirm it is attached to the "
                f"right substance."]
        claim.update(extra or {})
        rec.claims.append(claim)
        self.claims.append(claim)
        self.record_of[id(claim)] = rec
        return claim



# The elisions a stitched quote is joined with, folded to their normalised forms.
# Trimmed off a residue before it is looked up, or "...有机层水洗..." is searched for
# verbatim and of course not found.
_JOINER_CHARS = ".|/,;: "


def trim_joiners(fragment: str) -> str:
    return fragment.strip(_JOINER_CHARS)


def residue_runs(text: str, covered: set[int]):
    """Maximal runs of `text` that no span of the cover explained."""
    runs, start = [], None
    for k in range(len(text)):
        if k in covered:
            if start is not None:
                runs.append((start, k))
                start = None
        elif start is None:
            start = k
    if start is not None:
        runs.append((start, len(text)))
    return runs


def compact_lines(lines) -> str:
    """"45, 46, 77, 82" for a citation, "182-188" for a span."""
    ns = sorted(set(lines))
    if not ns:
        return "none"
    runs, start, prev = [], ns[0], ns[0]
    for n in ns[1:]:
        if n == prev + 1:
            prev = n
            continue
        runs.append((start, prev))
        start = prev = n
    runs.append((start, prev))
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in runs)


# ---------------------------------------------------------------- record checks

def quantity_holder(record: dict, kind: str, unit: str, percent_is: str = ""):
    """Which field of `record` would hold a quantity in `unit`, and what is in it.

    Returns (field path, current value or None, whether the field can hold a RANGE),
    or None where the record has no field of that kind at all. The third value is
    what separates the two failures the lead cares about: `conditions.temperature`
    carries `min_c` and `max_c` and can hold "15-20 degrees", so a range going
    missing there is an extraction gap. `conditions.time_h` is one float and cannot
    hold "1-10 h" at all, so the same shape of loss there is the schema's fault and
    needs a schema change rather than a re-extraction.
    """
    if kind == "reaction":
        cond = record.get("conditions") or {}
        kind = percent_is or kind
        if unit == "h":
            return "conditions.time_h", cond.get("time_h"), False
        if unit == "C":
            t = cond.get("temperature") or {}
            held = next((t[k] for k in ("value_c", "min_c", "max_c")
                         if t.get(k) is not None), None)
            return "conditions.temperature", held, True
        if unit == "%":
            if kind == "yield":
                return "product_yield_pct", record.get("product_yield_pct"), False
            conc = cond.get("concentration") or {}
            return "conditions.concentration.value", conc.get("value"), False
        return None
    if kind == "compound":
        if unit == "C":
            mp = record.get("melting_point") or {}
            held = next((mp[k] for k in ("min_c", "max_c")
                         if mp.get(k) is not None), None)
            return "melting_point", held, True
        q = record.get("quantity") or {}
        field = {"g": "mass_g", "ml": "volume_ml", "mmol": "mmol"}.get(unit)
        if field:
            return f"quantity.{field}", q.get(field), False
    return None


def is_vessel(line: str, end: int) -> bool:
    """Does a volume token sit immediately before the word for a flask?"""
    window = line[end:end + VESSEL_WINDOW]
    return any(w in window for w in VESSEL_WORDS)


def is_yield(line: str, start: int) -> bool:
    """Is a percentage introduced by the word for yield?"""
    window = line[max(0, start - YIELD_WINDOW):start]
    return any(w in window for w in YIELD_WORDS)


# `title_en` is the QUESTION THE CHECK ASKS, never the answer, and every title in
# this file is phrased "Whether ..." for that reason. Phrasing it as the assertion
# reads correctly on a pass and states a falsehood on a fail: the report page showed
# "The page drawing and the gold agree about this molecule" as the heading above a
# body explaining that they do not. That is the same failure as a banner reading
# "Machine could NOT find this" over a value printed plainly on the page. A reviewer
# skimming headings would have read the opposite of every finding.
def check(cid: str, family: str, status: str, title: str, detail: str,
          needs_human: bool = False, about_fields=()) -> dict:
    """One machine finding about one record.

    `about_fields` names the claim fields this check is about, and it is what keeps
    tier 1 small enough to be read. Promoting every claim on a record with one
    failing check puts about a hundred cleanly-matched numbers in front of a
    reviewer who has time for fifty items, purely because one row of the same
    reaction failed a mass balance. The failing check names the row; only that row's
    claims are promoted. Empty means the check is about the record as a whole.
    """
    return {"id": cid, "family": family, "status": status, "title_en": title,
            "detail_en": detail, "needs_human": needs_human,
            "about_fields": list(about_fields)}


# Cl (35.453) minus H (1.008), to the two decimals the annotator used. Every
# constant in this block is taken from verifier/lib/checks.ts and must stay equal to
# it: the UI shows the reviewer one explanation and the engine writes another, and
# the two disagreeing about whether a row passes is worse than neither checking.
CL_FOR_H = 34.45
CL_WINDOW = 1.5
REL_TOL = 0.015
ABS_TOL_FLOOR = 0.5


def mass_check(name_en: str, mass_g: float, mmol: float,
               true_mw: float | None) -> tuple[str, str, dict]:
    """Implied molecular weight against the weight of the resolved structure.

    Ported from `classify` in verifier/lib/checks.ts, tolerance for tolerance. The
    chlorine-for-hydrogen classification is preserved because it is the finding this
    patent turns on: three of the printed mass and mole pairs imply the des-chloro
    weights, and calling that an unexplained offset would throw away the one lead a
    reviewer can act on.
    """
    implied = mass_g / (mmol / 1000.0)
    facts = {"mass_g": mass_g, "mmol": mmol,
             "implied_mw": round(implied, 3),
             "true_mw": true_mw,
             "delta": None if true_mw is None else round(implied - true_mw, 3)}
    if true_mw is None:
        return ("skip",
                f"No structure is resolved for \"{name_en}\", so the implied "
                f"molecular weight of {implied:.3f} has nothing to be compared "
                f"against.", facts)

    delta = implied - true_mw
    tol = max(ABS_TOL_FLOOR, REL_TOL * true_mw)
    if abs(delta) <= tol:
        return ("pass",
                f"Implied {implied:.3f} against {true_mw:.3f}, offset "
                f"{delta:+.2f}, within tolerance {tol:.2f}.", facts)
    if abs(delta + CL_FOR_H) < CL_WINDOW:
        return ("fail",
                f"Offset {delta:+.2f} (implied {implied:.3f} against "
                f"{true_mw:.3f}) is consistent with a chlorine-for-hydrogen "
                f"substitution, which shifts molecular weight by {-CL_FOR_H:+.2f}. "
                f"That is a lead for the reviewer, not a diagnosis.", facts)
    if delta > 0:
        return ("fail",
                f"The implied mass is OVER by {delta:.2f}: implied {implied:.3f} "
                f"against {true_mw:.3f}.", facts)
    return ("fail",
            f"Unexplained offset of {delta:+.2f}: implied {implied:.3f} against "
            f"{true_mw:.3f}.", facts)


IMAGE_EXTRACT = re.compile(r"^\[IMAGE_EXTRACT:\s*(?P<json>.*)\]\s*$")


def image_extract_molecules(raw: str):
    """Every molecule an IMAGE_EXTRACT span declares, with what it says about it."""
    m = IMAGE_EXTRACT.match(raw.strip())
    if not m:
        return []
    try:
        payload = json.loads(m.group("json"))
    except json.JSONDecodeError:
        return [{"smiles": None, "broken": True}]
    out = []
    for mol in payload.get("molecules") or []:
        out.append(mol)
    for rxn in payload.get("reactions") or []:
        for side in ("reactants", "products"):
            out.extend(rxn.get(side) or [])
    return out


# ---------------------------------------------------------------- the run

class Run(Engine):
    """Builds every record, every claim and every check, then the artifact."""

    # ------------------------------------------------------------ records

    def build_name_index(self) -> None:
        """Every compound the gold knows, with what to search a line for."""
        for c in self.data["compounds"]:
            ident = c["identifier"]
            if not ident or looks_like_smiles(ident):
                continue
            label = self.english_name(ident)
            # From the IDENTIFIER only, never from the alias list. Two gold records
            # can share aliases - `water` and `ice water` both carry 冰水 and "ice
            # water" - and taking needles from aliases gave the `water` record
            # ice-water needles, so every mention of ice water named two substances.
            # The identifier is the one string that belongs to this record alone.
            zh = normalise(ident) if has_chinese(ident) else ""
            en = "" if has_chinese(ident) else (ident.lower()
                                                if len(ident) >= 4 else "")
            if zh or en:
                self._name_index.append((label, zh, en))
        # Longest English needle first so a containing name wins over a contained
        # one and the list reads as the page reads.
        self._name_index.sort(key=lambda t: (-len(t[2]), t[0]))

    def build(self) -> None:
        self.build_name_index()
        self.build_compounds()
        self.build_reactions()
        self.build_pathways()
        self.build_patent()
        self.referential_integrity()
        self.structure_checks()
        self.second_reader_checks()
        self.drawing_checks()
        self.consistency_checks()
        self.naming_checks()
        self.yield_identity()
        self.build_coverage()
        # The quantity sweep reads every claim built above, so it runs last of the
        # builders and before anything that scores them.
        self.quantity_coverage()
        # The same sweep, for names. Runs after the quantity one because both read
        # every claim built above, and before claims_for_findings so its own tickets
        # are already in the queue when that runs.
        self.substance_coverage()
        # Runs after every check family, so nothing that failed is left unspoken.
        self.claims_for_findings()
        # Order matters from here. Bases rewrite verdicts, the agreement matrix
        # reads the checks those verdicts sit beside, and tiering reads both.
        self.resolve_bases()
        self.agreement_matrix()
        self.assign_tiers()
        self.assign_severity()
        self.assert_claim_ids_unique()

    def assert_claim_ids_unique(self) -> None:
        """No two claims may share a claim_id. Nothing checked this until it broke.

        A claim_id is (record_id, field), and the verdicts file is an append-only log
        folded by claim_id, last write wins. Two claims sharing an id are therefore
        one row on disk: answer either and both go quiet, including the one nobody
        read. A new check family collided with the generic finding claim exactly this
        way and every other assertion in the pack passed, because each of them counts
        claims and both claims were there.
        """
        seen: dict[str, dict] = {}
        clashes = []
        for c in self.claims:
            first = seen.get(c["claim_id"])
            if first is None:
                seen[c["claim_id"]] = c
            else:
                clashes.append((c["claim_id"], first["question_en"],
                                c["question_en"]))
        if clashes:
            lines = [f"{len(clashes)} claim id(s) are used twice. A verdict on one "
                     f"would silently answer the other:"]
            for cid, a, b in clashes[:8]:
                lines += [f"  {cid}", f"      {a[:90]}", f"      {b[:90]}"]
            raise AssertionError("\n".join(lines))

    def section_en_of(self, label) -> str:
        return label or "Whole patent"

    def build_compounds(self) -> None:
        for c in self.data["compounds"]:
            rows = self.compound_prov.get(c["identifier"], [])
            cited = self.source.with_partners(compound_cited(rows))
            rec = Record(safe_record_id(self.patent_id, c["id"], c["identifier"]),
                         "compound", self.english_name(c["identifier"]),
                         self.section_en_of(c.get("section_label")), cited,
                         self.svg_for(c["identifier"]), c.get("compound_uuid"),
                         f"cmp:{c.get('compound_uuid')}")
            self.records.append(rec)
            self.note_citation(rec.record_id, cited)
            self.raw_of[rec.record_id] = c

            q = c.get("quantity") or {}
            mw = (self.structures.get(c["identifier"]) or {}).get("mw")
            for field, unit in QUANTITY_FIELDS:
                if q.get(field) is not None:
                    self.numeric_claim(rec, f"quantity.{field}", float(q[field]),
                                       unit, rec.label_en,
                                       HIGHLIGHT_KIND.get(f"quantity.{field}",
                                                          "value"),
                                       field_name=field,
                                       derive=derivation(field, q, mw,
                                                         rec.label_en))
            mp = c.get("melting_point") or {}
            for bound in ("min_c", "max_c"):
                if mp.get(bound) is not None:
                    self.numeric_claim(rec, f"melting_point.{bound}",
                                       float(mp[bound]), "C",
                                       f"the melting point of {rec.label_en}",
                                       "condition", field_name="melting_point_c")
            if c.get("purity_pct") is not None:
                self.numeric_claim(rec, "purity_pct", float(c["purity_pct"]), "%",
                                   f"the purity of {rec.label_en}", "yield",
                                   field_name="purity_pct")
            for i, a in enumerate(c.get("analytics") or []):
                if a.get("value") is not None:
                    self.numeric_claim(rec, f"analytics[{i}].value",
                                       float(a["value"]), None,
                                       f"the {a.get('method') or 'analysis'} of "
                                       f"{rec.label_en}", "value",
                                       field_name="analytics_value")

            # One quote claim per provenance row, each asked of the lines THAT ROW
            # declares rather than of the union. A compound quoted in seven places
            # has seven citations and seven chances to point at the wrong line, and
            # unioning them first would let a right citation cover for a wrong one.
            # The stand-in record carries the real record's identity so the claim
            # keys, labels and verdict key are the real record's, and shares its
            # claims list so the claim lands on it.
            for i, row in enumerate(rows):
                sub = Record(rec.record_id, "compound", rec.label_en,
                             rec.section_en,
                             self.source.with_partners(
                                 [n for n in (row.get("source_lines") or [])
                                  if isinstance(n, int)]),
                             rec.svg, rec.uuid, rec.rec, rec.flags)
                sub.claims = rec.claims
                self.quote_claim(sub, f"provenance[{i}].quote",
                                 row.get("quote_zh") or "", sub.cited)
                self.note_citation(rec.record_id, sub.cited)

            if not c.get("resolved", True) or c.get("unresolved_reference"):
                self.judgement_claim(
                    rec, "resolved",
                    f"Is \"{rec.label_en}\" really a compound the patent names?",
                    "The annotation records this identifier as a class term or an "
                    "unresolved reference rather than a definite molecule, which "
                    "only a reader can settle.")

    def build_reactions(self) -> None:
        for r in self.data["reactions"]:
            row = self.reaction_prov.get(r["reaction_id"]) or {}
            cited = self.source.with_partners(reaction_cited(row))
            label = (f"{r.get('section_label')} {r.get('step_label')}: "
                     f"{self.english_name(r.get('product_name'))}")
            rec = Record(r["id"], "reaction", label,
                         self.section_en_of(r.get("section_label")), cited,
                         self.svg_for(r.get("product_name") or ""),
                         r.get("reaction_uuid"), f"rx:{r['reaction_id']}",
                         r.get("validation_flags") or [])
            self.records.append(rec)
            self.note_citation(rec.record_id, cited)
            self.raw_of[rec.record_id] = r

            cond = r.get("conditions") or {}
            temp = cond.get("temperature") or {}
            for bound, tag in (("value_c", "the reaction temperature"),
                               ("min_c", "the low end of the temperature range"),
                               ("max_c", "the high end of the temperature range")):
                if temp.get(bound) is not None:
                    self.numeric_claim(rec, f"conditions.temperature.{bound}",
                                       float(temp[bound]), "C",
                                       f"{tag} of this step", "condition",
                                       field_name="temperature_c")
            if cond.get("time_h") is not None:
                self.numeric_claim(rec, "conditions.time_h", float(cond["time_h"]),
                                   "h", "the reaction time of this step",
                                   "condition", field_name="time_h")
            conc = cond.get("concentration") or {}
            if conc.get("value") is not None:
                unit = "%" if (conc.get("unit") or "").strip() in ("%", "％") else None
                self.numeric_claim(rec, "conditions.concentration.value",
                                   float(conc["value"]), unit,
                                   f"the concentration of "
                                   f"{self.english_name(conc.get('reagent'))}",
                                   "condition", field_name="concentration")
            if r.get("product_yield_pct") is not None:
                self.numeric_claim(rec, "product_yield_pct",
                                   float(r["product_yield_pct"]), "%",
                                   f"the yield of "
                                   f"{self.english_name(r.get('product_name'))}",
                                   "yield", field_name="product_yield_pct")
            if r.get("molar_ratio_text"):
                for i, ratio in enumerate(molar_ratios(r["molar_ratio_text"])):
                    self.ratio_claim(rec, f"molar_ratio_text[{i}]", ratio,
                                     "this step")

            seen: dict[str, int] = {}
            for c in r.get("compounds") or []:
                ident = c.get("identifier") or ""
                seen[ident] = seen.get(ident, 0) + 1
                key = ascii_key(ident)
                tag = key if seen[ident] == 1 else f"{key}#{seen[ident]}"
                q = c.get("quantity") or {}
                mw = (self.structures.get(ident) or {}).get("mw")
                for field, unit in QUANTITY_FIELDS:
                    if q.get(field) is not None:
                        self.numeric_claim(
                            rec, f"compounds[{tag}].quantity.{field}",
                            float(q[field]), unit, self.english_name(ident),
                            HIGHLIGHT_KIND.get(f"quantity.{field}", "value"),
                            field_name=field,
                            derive=derivation(field, q, mw,
                                              self.english_name(ident)))

            if row.get("quote_zh"):
                self.quote_claim(rec, "provenance.quote", row["quote_zh"], cited)

            # The annotation's own doubts. Only the validation flags become a
            # claim, because only they name a specific thing wrong with the
            # DOCUMENT. Confidence, linkage and completeness are recorded as
            # checks: they are true of most of this patent, they discriminate
            # nothing, and 58 judgement calls in a 15-minute queue would crowd out
            # the dozen findings that are actually worth the reviewer's time.
            for key, en, ok in (
                    ("reaction_class_confidence",
                     f"The annotation records its own confidence in the reaction "
                     f"class as {r.get('reaction_class_confidence')}, not high.",
                     (r.get("reaction_class_confidence") or "high") == "high"),
                    ("linkage_confirmed",
                     "The annotation could not confirm which step this one follows.",
                     bool(r.get("linkage_confirmed"))),
                    ("cross_reference_unresolved",
                     "The annotation records an unresolved cross-reference.",
                     not r.get("cross_reference_unresolved")),
                    ("is_complete",
                     "The annotation records this step as not fully captured, "
                     "usually because the patent states no conditions for it.",
                     bool(r.get("is_complete", True)))):
                rec.checks.append(check(
                    f"consistency.{key}", "consistency",
                    "pass" if ok else "warn",
                    "The annotation is confident about this step"
                    if key == "reaction_class_confidence" else
                    FIELD_LABELS.get(f"judgement.{key}", key),
                    "The annotation raises nothing here." if ok else en,
                    needs_human=False))

            if r.get("validation_flags"):
                flags_en = english_list([FLAG_MEANING_EN.get(f, f)
                                         for f in sorted(r["validation_flags"])])
                self._claim(
                    rec, "validation_flags",
                    "The annotation says the PATENT is defective here. Reading the "
                    "evidence, was it right to say so?",
                    flags_en, None, None, cited, [], "not_checkable",
                    "This is not a claim that the annotation got something wrong. "
                    "The annotation read this step and recorded that the document "
                    "itself does not hold together: " + flags_en + ". A reviewer "
                    "confirms that the document really does say what the flag "
                    "says, and marks the annotation correct if it does.",
                    ["The annotation flagged the patent here and a human should "
                     "confirm the flag."],
                    "name", about="patent", load_bearing=True)

    def build_pathways(self) -> None:
        for p in self.data["pathways"]:
            uuid = p.get("pathway_uuid") or ""
            label = (f"{p.get('scope')} route to "
                     f"{self.english_name((p.get('product') or {}).get('identifier'))}"
                     f" from "
                     f"{self.english_name((p.get('ksm') or {}).get('identifier'))}"
                     f" ({len(p.get('steps') or [])} steps)")
            cited: list[int] = []
            for st in p.get("steps") or []:
                prov = self.reaction_prov.get(st.get("reaction_id")) or {}
                cited.extend(reaction_cited(prov))
            cited = self.source.with_partners(sorted(set(cited)))
            rec = Record(f"{self.patent_id}_pathway_{uuid}", "pathway", label,
                         self.section_en_of(p.get("section_label")), cited,
                         None, uuid, f"pw:{uuid}")
            self.records.append(rec)
            self.note_citation(rec.record_id, cited)
            stated = p.get("overall_yield_pct")
            computed = self.cumulative_yield(p)
            if stated is not None or computed is not None:
                ok = (stated is not None and computed is not None
                      and abs(float(stated) - computed) <= 0.15)
                rec.checks.append(check(
                    "quantity.overall_yield", "quantity",
                    "pass" if ok else ("skip" if computed is None or stated is None
                                       else "fail"),
                    "Whether the route yield is the product of its step yields",
                    (f"The record states {stated}%. " if stated is not None
                     else "The record states no overall yield. ")
                    + ("At least one step has no yield, so there is nothing to "
                       "multiply." if computed is None else
                       f"Multiplying the {len(p.get('steps') or [])} step yields "
                       f"gives {computed}%."
                       + ("" if ok else " These disagree.")),
                    needs_human=not ok and computed is not None
                                and stated is not None))

    def build_patent(self) -> None:
        p = self.data["patent"]
        cited = self.source.with_partners(
            [n for n, k in self.source.kind.items()
             if self.section_of_line.get(n) in ("Bibliographic Data", "Abstract")
             and k in ("prose", "translation")])
        rec = Record(f"{self.patent_id}_patent", "patent",
                     p.get("title") or self.patent_id, "Whole patent", cited,
                     None, p.get("patent_uuid"), f"pt:{self.patent_id}")
        self.records.append(rec)
        self.note_citation(rec.record_id, cited)

        rollup = p.get("extraction_rollup") or {}
        for field, actual, name in (
                ("reaction_count", len(self.data["reactions"]), "reactions"),
                ("compound_count", len(self.data["compounds"]), "compounds"),
                ("pathway_count", len(self.data["pathways"]), "pathways")):
            stated = rollup.get(field)
            if stated is None:
                continue
            ok = int(stated) == actual
            rec.checks.append(check(
                f"completeness.{field}", "completeness",
                "pass" if ok else "fail",
                f"The patent record's count of {name}",
                f"The record states {stated}; the gold holds {actual}."
                + ("" if ok else " These disagree.")))
        # Not a grounding claim. 28.4 is the product of the eight step yields and
        # is printed nowhere in the patent, so asking whether it is on a cited line
        # would put a guaranteed false alarm at the top of the queue. Checked as
        # arithmetic instead, which is the only question there is about it.
        stated = rollup.get("best_overall_yield_pct")
        if stated is not None:
            best = max([y for y in (self.cumulative_yield(pw)
                                    for pw in self.data["pathways"])
                        if y is not None] or [None]) if self.data["pathways"] else None
            ok = best is not None and abs(best - float(stated)) <= 0.15
            rec.checks.append(check(
                "quantity.best_overall_yield", "quantity",
                "pass" if ok else ("skip" if best is None else "fail"),
                "Whether the best overall yield is the product of the step yields",
                f"The record states {stated}%."
                + (" No route in the gold has a yield on every step, so there is "
                   "nothing to multiply." if best is None else
                   f" Multiplying the step yields of the best route gives "
                   f"{best:.1f}%."
                   + ("" if ok else " These disagree.")),
                needs_human=not ok and best is not None))

    def judgement_claim(self, rec: Record, field: str, question: str,
                        why: str, about: str = "extraction") -> dict:
        return self._claim(
            rec, field, question, "a judgement, not a number", None, None,
            rec.cited, [], "not_checkable",
            why + " No string match can settle it, so a human must read the "
                  "evidence below and decide.",
            ["The annotation flagged its own uncertainty here."], "name",
            about=about, load_bearing=True)

    # ------------------------------------------------------------ reference

    def referential_integrity(self) -> None:
        """Every name a record uses must be a record, and every record used.

        Reported both ways round, because the two failures are different bugs. A
        reaction naming a compound that does not exist is a dangling pointer and the
        scheme cannot be drawn. A compound nothing references is either a
        hallucinated molecule or a step the extraction dropped, and only a reader
        can tell which.
        """
        by_record = {r.record_id: r for r in self.records}
        known = set()
        for c in self.data["compounds"]:
            known.add(self.canon_name(c["identifier"]))
            for a in c.get("aliases") or []:
                known.add(self.canon_name(a))

        referenced_compounds: set[str] = set()
        for r in self.data["reactions"]:
            rec = by_record.get(r["id"])
            names = [c.get("identifier") for c in (r.get("compounds") or [])]
            names += r.get("reactant_names") or []
            names.append(r.get("product_name"))
            missing = sorted({n for n in names if n and
                              self.canon_name(n) not in known})
            referenced_compounds.update(self.canon_name(n) for n in names if n)
            rec.checks.append(check(
                "reference.compounds", "reference",
                "pass" if not missing else "fail",
                "Whether every compound this step names has a record",
                (f"All {len({n for n in names if n})} named compounds resolve to a "
                 f"compound record.") if not missing else
                (f"{len(missing)} named compounds have no record: "
                 + ", ".join(self.english_name(n) for n in missing) + "."),
                needs_human=bool(missing)))

        reaction_ids = {r["reaction_id"] for r in self.data["reactions"]}
        referenced_reactions: set[str] = set()
        for p in self.data["pathways"]:
            uuid = p.get("pathway_uuid") or ""
            rec = by_record.get(f"{self.patent_id}_pathway_{uuid}")
            steps = [st.get("reaction_id") for st in (p.get("steps") or [])]
            referenced_reactions.update(s for s in steps if s)
            missing = sorted({s for s in steps if s not in reaction_ids})
            rec.checks.append(check(
                "reference.reactions", "reference",
                "pass" if not missing else "fail",
                "Whether every step of this route has a reaction record",
                f"All {len(steps)} steps resolve to a reaction record."
                if not missing else
                f"{len(missing)} steps name a reaction that does not exist: "
                + ", ".join(missing) + ".",
                needs_human=bool(missing)))
            names = [(p.get("ksm") or {}).get("identifier"),
                     (p.get("product") or {}).get("identifier")]
            names += [i.get("identifier") for i in (p.get("intermediates") or [])]
            referenced_compounds.update(self.canon_name(n) for n in names if n)
            gone = sorted({n for n in names if n and
                           self.canon_name(n) not in known})
            rec.checks.append(check(
                "reference.compounds", "reference",
                "pass" if not gone else "fail",
                "Whether every molecule this route names has a record",
                f"All {len([n for n in names if n])} named molecules resolve."
                if not gone else
                f"{len(gone)} named molecules have no record: "
                + ", ".join(self.english_name(n) for n in gone) + ".",
                needs_human=bool(gone)))

        for c in self.data["compounds"]:
            rec = by_record[safe_record_id(self.patent_id, c["id"], c["identifier"])]
            used = self.canon_name(c["identifier"]) in referenced_compounds
            rec.checks.append(check(
                "reference.orphan", "reference", "pass" if used else "warn",
                "Whether any reaction or route uses this compound",
                "At least one reaction or route names it." if used else
                "No reaction and no route names this compound. It is either a "
                "molecule the annotation invented, or a step the extraction did "
                "not connect up.",
                needs_human=not used))

        for r in self.data["reactions"]:
            rec = by_record[r["id"]]
            used = r["reaction_id"] in referenced_reactions
            rec.checks.append(check(
                "reference.orphan", "reference", "pass" if used else "warn",
                "Whether any route uses this reaction",
                "At least one route lists it as a step." if used else
                "No route lists this reaction as a step.",
                needs_human=not used))

    # ------------------------------------------------------------ structure

    def structure_checks(self) -> None:
        """Does the drawn chemistry hold together, and does it agree with itself?

        Four questions, and only the first is about RDKit. The second compares the
        formula the vision pass WROTE DOWN beside a structure against the formula
        RDKit computes from the SMILES it read off the same drawing, which is the
        only place in this pipeline where a structure read is checked against
        anything. The third and fourth are about identity: the gold deliberately
        carries one molecule under three names, so the names must agree about the
        molecule, and two molecules that turn out to be the same one must be
        noticed rather than counted twice.
        """
        by_record = {r.record_id: r for r in self.records}
        patent_rec = by_record[f"{self.patent_id}_patent"]

        for c in self.data["compounds"]:
            rec = by_record[safe_record_id(self.patent_id, c["id"], c["identifier"])]
            entry = self.structures.get(c["identifier"]) or {}
            smiles = entry.get("smiles")
            if not smiles:
                rec.checks.append(check(
                    "structure.smiles", "structure", "skip",
                    "Whether a 2D structure is resolved for this compound",
                    "No structure is resolved. " + (entry.get("note") or "")))
                continue
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                rec.checks.append(check(
                    "structure.smiles", "structure", "fail",
                    "Whether the resolved SMILES parses",
                    f"RDKit cannot parse {smiles!r}.", needs_human=True))
                continue
            formula = rdMolDescriptors.CalcMolFormula(mol)
            stated = entry.get("formula")
            ok = stated is None or stated == formula
            rec.checks.append(check(
                "structure.formula", "structure", "pass" if ok else "fail",
                "Whether the molecular formula agrees with the drawn structure",
                f"RDKit computes {formula} from the structure, molecular weight "
                f"{Descriptors.MolWt(mol):.2f}."
                + ("" if ok else f" The record states {stated}, which disagrees."),
                needs_human=not ok))

        # Formula and InChI key as the vision pass wrote them, against what RDKit
        # computes from the SMILES the same pass read off the same drawing.
        agree = disagree = unparseable = 0
        problems: list[str] = []
        for n in self.source.numbers:
            if self.source.kind[n] != "image_extract":
                continue
            for mol_entry in image_extract_molecules(self.source.lines[n]):
                smiles = mol_entry.get("smiles")
                if not smiles:
                    continue
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    unparseable += 1
                    problems.append(f"line {n}: RDKit cannot parse {smiles!r}")
                    continue
                stated = mol_entry.get("molecular_formula")
                computed = rdMolDescriptors.CalcMolFormula(mol)
                if stated and stated != computed:
                    disagree += 1
                    problems.append(f"line {n}: the span states {stated}, RDKit "
                                    f"computes {computed} from {smiles!r}")
                else:
                    agree += 1
        status = "pass" if not problems else "fail"
        patent_rec.checks.append(check(
            "structure.drawn_formula", "structure", status,
            "Whether every drawn structure's stated formula matches its SMILES",
            f"{agree} of {agree + disagree + unparseable} structures read off the "
            f"page drawings have a stated molecular formula that RDKit reproduces "
            f"from the SMILES read beside it."
            + ("" if not problems else " " + "; ".join(problems) + "."),
            needs_human=bool(problems)))

        # One molecule under three names: the names must agree about the molecule.
        for key, members in sorted(self.data["equivalence"].items()):
            canons = {}
            for m in members:
                e = self.structures.get(m) or {}
                if e.get("canonical"):
                    canons.setdefault(e["canonical"], []).append(m)
            for m in members:
                rec = by_record.get(f"{self.patent_id}_{ascii_key(m)}")
                if rec is None:
                    continue
                ok = len(canons) <= 1
                rec.checks.append(check(
                    "consistency.equivalence", "consistency",
                    "pass" if ok else "fail",
                    "Whether every spelling of this molecule resolves to one structure",
                    f"The gold spells this molecule {len(members)} ways and all "
                    f"resolved spellings give one structure."
                    if ok else
                    "The spellings of this molecule resolve to different "
                    "structures: " + "; ".join(
                        f"{', '.join(self.english_name(x) for x in v)} give "
                        f"{k}" for k, v in sorted(canons.items())) + ".",
                    needs_human=not ok))

        # Two records, one molecule, and no equivalence group saying so.
        by_canonical: dict[str, list[str]] = {}
        for c in self.data["compounds"]:
            e = self.structures.get(c["identifier"]) or {}
            if e.get("canonical"):
                by_canonical.setdefault(e["canonical"], []).append(c["identifier"])
        for canonical, idents in sorted(by_canonical.items()):
            groups = {self.canon_name(i) for i in idents}
            duplicate = len(idents) > 1 and len(groups) > 1
            for ident in idents:
                rec = by_record.get(f"{self.patent_id}_{ascii_key(ident)}")
                if rec is None:
                    continue
                others = [self.english_name(i) for i in idents if i != ident]
                rec.checks.append(check(
                    "consistency.duplicate", "consistency",
                    "warn" if duplicate else "pass",
                    "Whether any other compound record is this same molecule",
                    "No other record resolves to this structure."
                    if not others else
                    (f"{len(others)} other records resolve to the same structure: "
                     + ", ".join(others) + ". "
                     + ("They are grouped as one substance in "
                        "provenance/compounds-equivalence.json, so this is "
                        "expected." if not duplicate else
                        "They are NOT grouped as one substance, so this may be a "
                        "duplicate record.")),
                    needs_human=duplicate))

    # ------------------------------------------------------------ drawing

    def drawing_checks(self) -> None:
        """The gold's structure for a molecule against the one read off the page.

        gold/structures.json is an INDEPENDENT reading: a vision pass looked at the
        rendered page and wrote down the substituents and their ring positions,
        without seeing the compound records. Where that reading and the gold's
        resolved structure name the same molecule and give different structures,
        one of the two is wrong, and no amount of text matching would ever find it.

        The join is on the name here, and only here, which is the opposite of what
        resolve_structures.py does and for the opposite reason. That stage joins on
        canonical SMILES because it is asking "is this molecule drawn", and a name
        join would answer no for molecules that plainly are. This check is asking
        "do the two readings of THIS NAME agree", and a SMILES join would make the
        question vacuous: it would only ever compare structures that were already
        equal. So the names are normalised hard - case, brackets, hyphens, spaces
        and the sulfonyl/sulphonyl and methanesulfonyl/methylsulfonyl spellings all
        folded - and a pair that survives that is compared.
        """
        by_record = {r.record_id: r for r in self.records}
        drawn: dict[str, dict] = {}
        for page in self.data["drawings"]:
            for struct in page.get("structures") or []:
                name, smiles = struct.get("name"), struct.get("smiles")
                if not name or not smiles:
                    continue
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                drawn.setdefault(drawing_key(name), {
                    "canonical": Chem.MolToSmiles(mol), "name": name,
                    "page": page.get("page", "?")})

        agree = disagree = 0
        for c in self.data["compounds"]:
            rec = by_record[safe_record_id(self.patent_id, c["id"],
                                           c["identifier"])]
            entry = self.structures.get(c["identifier"]) or {}
            names = [c["identifier"], *(c.get("aliases") or [])]
            hit = next((drawn[k] for k in map(drawing_key, names) if k in drawn),
                       None)
            if hit is None or not entry.get("canonical"):
                rec.checks.append(check(
                    "drawing.smiles", "drawing", "skip",
                    "Whether the page drawing and the gold agree about this molecule",
                    "No structure drawn on any page carries this molecule's name, "
                    "so there is no second reading to compare against."
                    if hit is None else
                    "No structure is resolved for this record, so there is nothing "
                    "to compare the drawing against."))
                continue
            same = hit["canonical"] == entry["canonical"]
            agree += 1 if same else 0
            disagree += 0 if same else 1
            rec.checks.append(check(
                "drawing.smiles", "drawing", "pass" if same else "fail",
                "Whether the page drawing and the gold agree about this molecule",
                f"The vision pass read this molecule off page {hit['page']} as "
                f"{hit['canonical']}."
                + (" The gold resolves the same structure." if same else
                   f" The gold resolves {entry['canonical']}, which is a different "
                   f"molecule. One of the two readings is wrong."),
                needs_human=not same))
        self.drawing_tally = (agree, disagree)

    # ------------------------------------------------------------ quantity

    def consistency_checks(self) -> None:
        """Mass over molar amount against the weight of the molecule named.

        The single most valuable arithmetic in this document. A row that prints both
        a mass and a mole count is an implicit claim about molecular weight, and on
        this patent several of those claims come out at the des-chloro weights. The
        tolerance and the chlorine-for-hydrogen classification are copied exactly
        from verifier/lib/checks.ts so the engine and the UI can never disagree
        about whether a row passes.
        """
        by_record = {r.record_id: r for r in self.records}
        for r in self.data["reactions"]:
            rec = by_record[r["id"]]
            rows = []
            for c in r.get("compounds") or []:
                q = c.get("quantity") or {}
                mass, mmol = q.get("mass_g"), q.get("mmol")
                if mass is None or mmol is None or mmol <= 0:
                    continue
                ident = c.get("identifier") or ""
                mw = (self.structures.get(ident) or {}).get("mw")
                status, detail, facts = mass_check(self.english_name(ident),
                                                   float(mass), float(mmol), mw)
                rows.append((ident, status, detail, facts))
            for ident, status, detail, facts in rows:
                rec.checks.append(check(
                    f"quantity.mass_mmol[{ascii_key(ident)}]", "quantity", status,
                    f"Mass and moles agree for {self.english_name(ident)}",
                    detail, needs_human=status == "fail",
                    about_fields=[f"compounds[{ascii_key(ident)}].quantity."]))

    # ------------------------------------------------------------ findings

    # Checks that already speak through a claim of their own, so the sweep below
    # must not raise a second one about the same thing.
    # Check ids whose failure already has a claim written for it by name. A check
    # left off this tuple gets a SECOND, generic claim here - and because a claim_id
    # is (record_id, field), that second claim carries the SAME id as the first. The
    # verdicts file is folded by claim_id, so answering one silently answers both.
    # `structure.second_reader` did exactly that for one run before the uniqueness
    # assertion below caught it.
    SPOKEN_FOR = ("naming.qualifier", "structure.second_reader")

    def claims_for_findings(self) -> None:
        """Every failing check a reviewer would otherwise never be shown.

        Measured, not supposed. A structure was swapped for a different real
        molecule and the cross-check fired perfectly - "which is a different
        molecule" - and then NO claim mentioned it. The two claims the reviewer met
        on that record both asked "is the text this record quotes actually on the
        source lines it cites?", with the action "a check on this row failed, so it
        is worth reading". It never said which check, or what was wrong. The
        detection was real and undeliverable.

        `about_fields` is what normally carries a check into the queue, by promoting
        the claims it names. A check that names no field promotes nothing, which is
        correct for keeping tier 1 small and wrong when the check IS the finding. So
        those get a claim of their own, worded from the check, and land in the
        census like any other thing the machine looked at and did not like.
        """
        for rec in list(self.records):
            for c in rec.checks:
                if (c["status"] != "fail" or c["about_fields"]
                        or c["id"] in self.SPOKEN_FOR):
                    continue
                self._claim(
                    rec, c["id"],
                    f"The machine checked {c['title_en'][0].lower()}"
                    f"{c['title_en'][1:]}, and the answer is no. Is it right?",
                    "a machine finding, not a number", None, None,
                    rec.cited, [], "not_checkable", c["detail_en"],
                    ["A check on this record failed and no other claim reports it."],
                    "name", set(), about="extraction", load_bearing=True,
                    extra={"_finding": True})

    # ------------------------------------------------------------ substance recall

    def load_substance_readings(self) -> tuple[dict, list[str]]:
        """Every substance every reader saw printed, per line, plus who read.

        Two files, both optional, both INPUTS:

            input/substances-observed.json   reading A, an LLM pass asked only
                                             "which substances are named here"
            input/substances-cde.json        reading B, ChemDataExtractor

        WHO READ IS RECORDED, ALWAYS. If reading B is absent the answer is
        `["llm"]` and every finding says so, because a silently-single reader looks
        exactly like two readers agreeing. That is the failure this pack keeps
        finding in its own guards and it is not going to be introduced here.

        EVERY SPAN IS CHECKED AGAINST THE LINE IT CLAIMS. A reader that invents a
        substance is the one way this sweep can manufacture a defect out of nothing,
        and a span that is not literally on its line stops the run. The check is here
        rather than in whatever produced the file, because a check that lives with
        the producer only ever grades the producer that was there when it was
        written.
        """
        readings: dict[int, list] = {}
        readers: list[str] = []
        bad: list[str] = []

        for name, reader in (("substances-observed.json", "llm"),
                             ("substances-cde.json", "cde")):
            f = INPUT / name
            if not f.exists():
                continue
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                bad.append(f"{name}: not JSON ({e})")
                continue
            readers.append(reader)
            for k, mentions in (doc.get("lines") or {}).items():
                n = int(k)
                # The KEY is what records "a reader looked at this line", and it has
                # to appear even when the row is empty. Registering it only when a
                # mention exists is the same absence bug the file itself had one
                # commit ago: a line with nothing on it then reads as a line nobody
                # read, and on a screen where green means "nothing unaccounted for"
                # those must not colour the same.
                readings.setdefault(n, [])
                # The ENGLISH rendering, which is what was read and what a reviewer
                # sees. source.lines[n] is the raw line and is Chinese on half the
                # document, so checking spans against it would reject every English
                # reading of a Chinese line. The block dedup below still collapses
                # the Chinese line and its translation into one fact.
                # CHECKED AGAINST EITHER THE PRINTED LINE OR ITS ENGLISH RENDERING.
                #
                # text_en is the translation on a Chinese line, and the reader records
                # English, so on a Chinese patent that side is the one that can match
                # and the raw line would reject every reading. But the `or` fallback
                # never fires when text_en is non-empty, and on an ENGLISH patent the
                # EN line is not a translation at all: it is a REPAIR of the same
                # language. US20040236146A1 prints
                # "2-chloro-3-methyl4-sulfonylmethylbenzoic acid" on line 122 and its
                # EN line silently corrects the name, so an as-printed span was
                # rejected as "not on that line" when it is the only thing literally
                # on that line. Ten of them, and the only way to satisfy the check
                # would have been to delete true observations.
                #
                # Either side is enough. The span must still be somewhere on the line
                # it claims, which is the whole of what this check is for: a reader
                # that invents a substance is what it exists to stop.
                raw = self.source.lines.get(n, "")
                text = self.source.text_en.get(n, "") or raw
                for m in mentions:
                    span = m.get("span") or ""
                    if span not in text and span not in raw:
                        bad.append(f"{name} line {n}: {span!r} is not on that line")
                        continue
                    readings.setdefault(n, []).append({**m, "reader": reader,
                                                       "line": n})
        if bad:
            raise AssertionError(
                "a substance reading claims spans that are not on the lines they "
                "name, so it is describing a document this is not:\n  "
                + "\n  ".join(bad[:10]))
        return readings, readers

    def substance_key(self, mention: dict):
        """What two mentions have to share to be the same substance.

        THE STRUCTURE FIRST, THE STRING ONLY WHEN THERE IS NO STRUCTURE. gold's own
        structures.json holds 18 SMILES for 11 molecules because the drawn scheme is
        read more than once and the reads name things differently, and 12 of the 16
        drawn names match no record name. A string join would report molecules the
        patent DRAWS as missing. Where a canonical SMILES can be had on both sides,
        that is the key; where it cannot, the normalised name is, and the finding
        says which join was used so a reviewer can weigh it.
        """
        if mention.get("kind") != "specific":
            return ("generic", normalise_name(mention["span"]))
        canonical = self.substance_canonical(mention["span"])
        if canonical is not None:
            return ("mol", canonical)
        # A span printed "benzoyl peroxide (BPO)" is the same substance as one
        # printed "benzoyl peroxide". Key on the base so the two meet. The guard in
        # name_and_abbrev refuses to do this to a formula label.
        split = name_and_abbrev(mention["span"])
        if split:
            return ("name", normalise_name(split[0]))
        return ("name", normalise_name(mention["span"]))

    def substance_canonical(self, span: str):
        """A span -> canonical SMILES, by the cheapest route that can answer.

        Four routes, in order, and the order is the point: what the READER knows
        beats what a grammar can parse, and both beat nothing.

            1. the reading carried it     abbreviations: CDCl3, DMSO, THF, HCl, NBS
            2. the span IS a SMILES       the drawn-structure lines
            3. it is a known identifier   or an alias of one, from structures-resolved
            4. OPSIN parsed it            from names-opsin.json, already cached
        """
        if span in self._substance_canon:
            return self._substance_canon[span]
        out = None
        reader_smiles = self._reader_smiles.get(span)
        if reader_smiles:
            out = reader_smiles
        elif looks_like_smiles(span):
            mol = Chem.MolFromSmiles(span)
            out = Chem.MolToSmiles(mol) if mol is not None else None
        if out is None:
            out = self._canon_by_name.get(normalise_name(span))
        self._substance_canon[span] = out
        return out

    def substance_coverage(self) -> None:
        """Every substance printed on a cited line, against every substance recorded.

        The recall half for names, and the exact shape the quantity sweep already has
        for numbers. Line coverage cannot see any of it: 222 of 256 lines are covered
        and `uncited_with_chemistry` reads 0, while a 730-character line carrying
        eight facts reads as covered when three were captured.

        Before this existed the pack could say "every NUMBER the patent prints is in
        a record or reported as a gap" - 126 tokens, 96 accounted, 3 gaps, 12 schema
        losses - and could say nothing whatever about the SUBSTANCES it names, which
        are the most common thing in the document by a factor of four.

        `asserted` is built from what a record IS, never from what it quotes: the
        identifiers and aliases its own fields carry. Matching against quoted prose is
        the trap the quantity sweep documents, and it is worse here, because a
        procedure quotes the name of every substance it uses whether or not the record
        has a field holding it.

        THREE OUTCOMES, KEPT APART:

            accounted             some record citing this line names this molecule
            unaccounted           nothing does. Pooled by record into one ticket.
            named_not_identifiable  the span refers to a substance without naming one:
                                  "the mixture", "an inorganic base". 98 of these are
                                  printed on this patent's lines. Counted and shown,
                                  never queued: a reviewer sent at 98 rows that name
                                  no molecule stops reading the queue, and deleting
                                  them with a stoplist would delete "the catalyst",
                                  which is twelve times a real thing nobody recorded.
        """
        readings, readers = self.load_substance_readings()
        self.substance_readers = readers
        self.substance_tally = {"tokens": 0, "accounted": 0,
                                "named_not_identifiable": 0, "unaccounted": 0}
        self.substance_findings: list[dict] = []
        self.substance_tickets: dict[str, list] = {}
        if not readings:
            # Said out loud. "No reader ran" and "the readers found nothing wrong"
            # are different facts and only one of them is about this patent.
            self.substance_tally["skipped_en"] = (
                "No substance reading is present, so nothing was swept for names. "
                "This is not a clean result: it is the absence of a check.")
            return

        # What the reader knows a span denotes, and what the pack knows a name is.
        self._reader_smiles = {}
        for mentions in readings.values():
            for m in mentions:
                if m.get("canonical"):
                    self._reader_smiles[m["span"]] = m["canonical"]
        self._canon_by_name = {}
        for entry in self.data["structures"]:
            if not entry.get("canonical"):
                continue
            for name in [entry["identifier"], *(entry.get("aliases") or [])]:
                self._canon_by_name[normalise_name(name)] = entry["canonical"]
        opsin = (self.data.get("names_opsin") or {})
        for row in (opsin.get("names") if isinstance(opsin, dict) else None) or []:
            if row.get("outcome") == "parsed" and row.get("canonical"):
                self._canon_by_name.setdefault(normalise_name(row["identifier"]),
                                               row["canonical"])
        self._substance_canon: dict[str, str | None] = {}

        # Both keys for every identifier a record carries, so a span that resolves
        # matches on the molecule and a span that does not can still match on the
        # name. Which one fired is recorded on the finding.
        asserted: dict[int, set] = {}
        for rec in self.records:
            keys = set()
            for name in self.record_identifiers(rec):
                keys.add(("name", normalise_name(name)))
                # AND THE SAME NAME IN THE OTHER LANGUAGE. The substance reading is
                # English and half the identifiers in a Chinese patent are Chinese,
                # so a name join between them can never fire and every Chinese-only
                # record reads as holding nothing. On WO2024109718A1 that put 式(I)
                # 化合物 and the span "compound of formula (I)" on opposite sides of
                # a join that had no way to close, and the sweep reported the
                # substance as unrecorded when the record was sitting on the cited
                # line holding it.
                #
                # The index is not a guess. resolve_translations built it from the
                # gold's own data and its coverage gate has already passed on it, so
                # this asks the pipeline's existing answer rather than inventing an
                # equivalence. It ADDS a key and never replaces one, so nothing that
                # matched before stops matching.
                english = (self.index.get(name) or {}).get("en")
                if english:
                    keys.add(("name", normalise_name(english)))
                # And both halves of a name carrying its own abbreviation, so a
                # record holding "BPO" answers a line printing "benzoyl peroxide
                # (BPO)" and a record holding the full name answers the short one.
                for candidate in (name, english):
                    split = name_and_abbrev(candidate or "")
                    if split:
                        keys.add(("name", normalise_name(split[0])))
                        keys.add(("name", normalise_name(split[1])))
                canonical = self.substance_canonical(name)
                if canonical is not None:
                    keys.add(("mol", canonical))
            if not keys:
                continue
            for n in rec.cited:
                asserted.setdefault(n, set()).update(keys)

        missed = self.line_sweep(
            tokens=lambda n: readings.get(n, []),
            key=self.substance_key,
            asserted=asserted,
            tally=self.substance_tally,
            excuse=lambda m, folded: (
                "named_not_identifiable" if m.get("kind") != "specific" else None),
        )
        for n, block, mention, _folded in missed:
            self.record_substance_miss(n, block, mention)
        self.substance_tally["unaccounted"] = len(missed)
        self.emit_substance_tickets()
        self.attach_substance_status(readings)

    def attach_substance_status(self, readings: dict) -> None:
        """Per line, what the substance sweep found, for the section screen.

        Five states, and `unread` is the one worth having. A line nobody read and a
        line read with nothing on it are the same absence in any file that records
        only hits, and on a screen where green means "nothing here is unaccounted
        for" they would both be green. One of them has been checked and one has not.

            unaccounted   something printed here is in no record. THE FINDING.
            named_only    only generic references: "the mixture", "an inorganic base"
            accounted     substances printed here, all of them in some record
            none          read, and no substance is named here
            unread        no reader has looked at this line

        Written onto source_coverage.lines, which the page already loads, rather
        than into a second structure holding the same fact.
        """
        by_line: dict[int, list] = {}
        for f in self.substance_findings:
            for n in f.get("lines") or [f["line"]]:
                by_line.setdefault(n, []).append(f["span"])

        for row in self.coverage_lines:
            n = row["n"]
            mentions = readings.get(n)
            missing = sorted(set(by_line.get(n, ())))
            if missing:
                status = "unaccounted"
            elif mentions is None:
                status = "unread"
            elif not mentions:
                status = "none"
            elif any(m.get("kind") == "specific" for m in mentions):
                status = "accounted"
            else:
                status = "named_only"
            row["substance"] = status
            if missing:
                row["substance_unaccounted"] = missing

    def record_identifiers(self, rec) -> list[str]:
        """Every substance name a record's own FIELDS carry. Not its quotes."""
        raw = self.raw_of.get(rec.record_id) or {}
        out: list[str] = []
        if rec.kind == "compound":
            out += [raw.get("identifier") or "", *(raw.get("aliases") or [])]
        elif rec.kind == "reaction":
            out.append(raw.get("product_name") or "")
            for c in raw.get("compounds") or []:
                out += [c.get("identifier") or "", *(c.get("aliases") or [])]
        elif rec.kind == "pathway":
            for st in raw.get("steps") or []:
                out.append(st.get("product_name") or "")
                for c in st.get("compounds") or []:
                    out.append(c.get("identifier") or "")
        return [x for x in out if x]

    def record_substance_miss(self, line: int, block: tuple, mention: dict) -> None:
        """Attach one unaccounted substance to the record that should have held it."""
        citers = sorted({r for m in block for r in self.cited_lines.get(m, ())})
        by_record = {r.record_id: r for r in self.records}
        best = None
        for rid in citers:
            rec = by_record.get(rid)
            if rec is None or rec.kind == "patent":
                continue
            # A reaction owns what was charged into its own step; a compound record
            # citing the same line owns only its own row. Same rank rule the quantity
            # sweep uses, so the claim lands where a fix can be made and the choice is
            # a function of the inputs and nothing else.
            rank = (0 if rec.kind == "reaction" else 1, rid)
            if best is None or rank < best[0]:
                best = (rank, rec)
        if best is None:
            best = (None, next(r for r in self.records if r.kind == "patent"))
        rec = best[1]
        canonical = self.substance_canonical(mention["span"])
        finding = {
            "line": line,
            # Every line printing this same fact, not just the one the sweep visited
            # first. The screen colours lines, and a reader looking at L200 must not
            # see green because the miss was recorded against L199.
            "lines": list(block),
            "span": mention["span"],
            "reader": mention.get("reader"),
            "join": "structure" if canonical else "name",
            "canonical": canonical,
            "record_id": rec.record_id,
            "record_label_en": rec.label_en,
            "uncited_line": not self.cited_lines.get(line),
        }
        self.substance_findings.append(finding)
        self.substance_tickets.setdefault(rec.record_id, []).append(finding)

    def emit_substance_tickets(self) -> None:
        """One claim per record, carrying every substance that record does not hold.

        Pooled for the reason schema losses are pooled: four substances missing from
        one record is one question about one record with four things listed on it,
        not four questions. The census has 29 claims of headroom before it stops
        fitting a fifteen-minute budget, and a queue nobody finishes is
        indistinguishable on every screen from a clean one.

        Nothing is dropped. Every instance is on the card, with its line, its span,
        which reader saw it and which join was tried.
        """
        by_record = {r.record_id: r for r in self.records}
        for rid, hits in sorted(self.substance_tickets.items()):
            rec = by_record.get(rid)
            if rec is None:
                continue
            spans = sorted({h["span"] for h in hits})
            lines = sorted({h["line"] for h in hits})
            weak = [h for h in hits if h["join"] == "name"]
            one_reader = len(set(self.substance_readers)) < 2
            reason = (
                f"The patent names " + english_list([repr(s) for s in spans])
                + f" on line{'s' if len(lines) > 1 else ''} " + compact_lines(lines)
                + f", which this record cites. None of them is an identifier on this "
                f"record or on any other record citing those lines. Either the "
                f"substance was not recorded, or it belongs on a record that does not "
                f"cite the line.")
            risk = [f"{len(spans)} substance{'s' if len(spans) > 1 else ''} printed "
                    f"on a line this record cites, and not carried by any record."]
            if weak:
                risk.append(
                    f"{len(weak)} of them could not be resolved to a structure, so "
                    f"the comparison was made on the NAME. Two spellings of one "
                    f"molecule would read as a miss here.")
            if one_reader:
                risk.append(
                    "One reader only. Nothing independent corroborates that these "
                    "are substances at all.")
            self._claim(
                rec, "__substance__",
                f"The patent names " + english_list([repr(s) for s in spans])
                + " here. Should this record have recorded "
                + ("them" if len(spans) > 1 else "it") + "?",
                english_list(spans), None, None,
                self.source.with_partners(lines), [], "not_found", reason, risk,
                "name", set(lines), about="extraction", load_bearing=True,
                rec_field="__substance__",
                extra={"_finding": True, "substance_instances": hits,
                       "substance_readers": sorted(set(self.substance_readers))})

    # ------------------------------------------------------------ second reader

    def second_reader_checks(self) -> None:
        """What an independent name parser thought of each structure we assigned.

        `name_check` is written by resolve_structures.py from resolve_names.py's
        output: OPSIN reading the compound's NAME by grammar, with no sight of this
        patent and no shared failure mode with the vision pass that read the drawing.

        THE POINT OF THIS FAMILY IS THE PASSES, NOT THE FAILURES. On this patent it
        agrees with 36 of 37, and that number is the closest thing this pack has to
        a corroboration of its own chemistry: two unrelated routes to the same
        molecule. It is worth a check row on every record precisely so the reviewer
        can see it held, instead of only meeting the parser when it complains.

        Two outcomes become claims, and both are answerable by LOOKING:

          disagree   two readings, two molecules, one of them wrong. The reviewer
                     compares two drawings. No chemistry needed to see they differ,
                     and the record says which reading came from where.
          ambiguous  OPSIN parsed the name and warned it does not pin one molecule
                     down. This is the class nothing else here can catch: the
                     candidates share a formula and a mass, so every arithmetic
                     check in this file passes on all of them.

        `is_the_source` never counts as agreement. Where the parse IS the structure,
        nothing independent has looked at it, and saying so is the whole reason the
        parse is consulted last.
        """
        by_record = {r.record_id: r for r in self.records}
        TITLE = ("Whether an independent reading of the NAME lands on the same "
                 "molecule")

        for c in self.data["compounds"]:
            rec = by_record.get(safe_record_id(self.patent_id, c["id"],
                                               c["identifier"]))
            if rec is None:
                continue
            entry = self.structures.get(c["identifier"]) or {}
            chk = entry.get("name_check") or {}
            outcome = chk.get("outcome")
            note = chk.get("note_en") or ""
            parsed = chk.get("query")
            here = entry.get("canonical")
            theirs = chk.get("opsin_canonical")

            if outcome == "agree":
                rec.checks.append(check(
                    "structure.second_reader", "structure", "pass", TITLE,
                    f"OPSIN parsed {parsed!r} and reached {theirs}, the same "
                    f"molecule this pack assigned. Two readings that share no "
                    f"method agree.", about_fields=[]))
                continue

            if outcome == "disagree":
                detail = (f"This pack assigns {here} to {c['identifier']!r}. OPSIN "
                          f"parsed the name {parsed!r} and reached {theirs}. Those "
                          f"are different molecules, so one of the two readings is "
                          f"wrong. This pack's structure came from: "
                          f"{entry.get('note') or entry.get('origin')}")
                rec.checks.append(check(
                    "structure.second_reader", "structure", "fail", TITLE, detail,
                    needs_human=True, about_fields=[]))
                self._claim(
                    rec, "structure.second_reader",
                    f"Two readings of {c['identifier']!r} give two different "
                    f"molecules. Look at the two drawings: which one does the "
                    f"patent mean?",
                    f"here {here}, name parser {theirs}", None, None,
                    rec.cited, [], "not_reconciled", detail,
                    ["A structure and an independent parse of its own name "
                     "disagree.",
                     "Both drawings are on this card. They are not the same "
                     "molecule, so exactly one of them is what the patent used."],
                    "name", set(), about="extraction", load_bearing=True,
                    extra={"_finding": True,
                           "second_reader": {"here": here, "opsin": theirs,
                                             "query": parsed,
                                             "origin": entry.get("origin"),
                                             # Both readings drawn. The card asks
                                             # which molecule the patent means,
                                             # and BrBr against [Br] cannot be
                                             # answered as text by anybody who is
                                             # not already a chemist.
                                             "here_svg": entry.get("svg"),
                                             "opsin_svg": chk.get("opsin_svg")}})
                continue

            if outcome == "ambiguous":
                detail = (f"OPSIN parsed {parsed!r} and warned that the name does "
                          f"not pin one molecule down; its best guess is {theirs}. "
                          f"Nothing else in this file can catch this: the molecules "
                          f"the name could mean share a formula and a molecular "
                          f"weight, so every mass and formula check here passes on "
                          f"all of them. {note}")
                rec.checks.append(check(
                    "structure.second_reader", "structure", "fail", TITLE, detail,
                    needs_human=True, about_fields=[]))
                self._claim(
                    rec, "structure.second_reader",
                    f"{c['identifier']!r} names more than one molecule. Does the "
                    f"patent say which one?",
                    f"ambiguous; OPSIN guesses {theirs}", None, None,
                    rec.cited, [], "not_checkable", detail,
                    ["The recorded name does not identify one molecule.",
                     "The candidates share a formula and a mass, so no arithmetic "
                     "check anywhere in this file can separate them."],
                    "name", set(), about="extraction", load_bearing=True,
                    extra={"_finding": True,
                           "second_reader": {"here": here, "opsin": theirs,
                                             "query": parsed, "ambiguous": True}})
                continue

            if outcome == "is_the_source":
                rec.checks.append(check(
                    "structure.second_reader", "structure", "skip", TITLE,
                    "This structure IS the name parse, so nothing independent has "
                    "checked it. Nothing drawn in the patent and nothing curated "
                    "corroborates it.", about_fields=[]))
                continue

            rec.checks.append(check(
                "structure.second_reader", "structure", "skip", TITLE,
                note or "No second reading of this name is available.",
                about_fields=[]))

    # ------------------------------------------------------------ naming

    def naming_checks(self) -> None:
        """A fact the Chinese name carries that the record's English name drops.

        The gap this closes was measured by planting a defect and following it to a
        screen: removing "anhydrous" from a record produced NO check, NO claim and
        NO change in risk, and not one check in the whole file mentioned an alias.
        The engine had nothing to say about it and did not know that it did not.

        It is not a small class. Wet aluminium trichloride does not catalyse a
        Friedel-Crafts at all; saturated sodium bicarbonate is a workup and the
        solid is not; dilute hydrochloric acid is not concentrated hydrochloric
        acid. The qualifier IS the fact.

        The table and the percent rule are imported from resolve_translations rather
        than restated, because two tables that are meant to agree will not. That
        module applies them to the translation INDEX; this asks the same question of
        a record's own alias set, which is where a reviewer would have to notice it.

        Scoped to names and to percent signs, for the reasons that module records: a
        systematic name is full of locants and a locant is not a quantity.
        """
        by_record = {r.record_id: r for r in self.records}
        for c in self.data["compounds"]:
            rec = by_record.get(safe_record_id(self.patent_id, c["id"],
                                               c["identifier"]))
            if rec is None:
                continue
            names = [c["identifier"], *(c.get("aliases") or [])]
            chinese = [n for n in names if n and has_chinese(n)]
            english = [n for n in names if n and not has_chinese(n)]
            lost = None
            for zh in chinese:
                if (any(p in zh for p in PERCENT)
                        and not any(any(p in e for p in PERCENT) for e in english)):
                    lost = (zh, "a strength", "the percentage it is used at")
                    break
                # QUALIFIERS values are a TUPLE of acceptable English renderings,
                # because one Chinese modifier does not always come out as one
                # English word: 冰水 is ice water but 冰醋酸 is glacial acetic acid.
                hit = next((ws for pfx, ws in QUALIFIERS.items()
                            if zh.startswith(pfx)
                            and not any(w in e.lower() for w in ws
                                        for e in english)),
                           None)
                if hit:
                    shown = " or ".join(repr(w) for w in hit)
                    lost = (zh, f"the word {shown}", f"whether it is {hit[0]}")
                    break

            if lost is None:
                rec.checks.append(check(
                    "naming.qualifier", "naming", "pass",
                    "Whether the English name keeps every fact the Chinese name "
                    "carries",
                    "No name on this record drops a strength or a qualifier."
                    if chinese else
                    "This record carries no Chinese name to compare against.",
                    about_fields=[]))
                continue

            zh, what, plainly = lost
            zh_en = self.english_name(zh)
            detail = (f"The patent calls this {zh_en!r}. The record's English "
                      f"names are " + english_list([repr(e) for e in english])
                      + f", none of which says {what}. The qualifier is not "
                      f"decoration: it is what was charged.")
            rec.checks.append(check(
                "naming.qualifier", "naming", "fail",
                "Whether the English name keeps every fact the Chinese name "
                "carries", detail, needs_human=True, about_fields=[]))
            self._claim(
                rec, "naming.qualifier",
                f"The patent calls this {zh_en!r}. The record calls it "
                f"{english[0]!r}. Is {plainly} a fact that has been lost?",
                zh_en, None, None, rec.cited, [], "not_checkable", detail,
                [f"The record's English name drops {what} its Chinese name "
                 f"carries.",
                 "A qualifier on a reagent name changes what was charged."],
                "name", set(), about="extraction", load_bearing=True,
                extra={"_finding": True})

    # ------------------------------------------------------------ yield identity

    def yield_identity(self) -> None:
        """limiting reactant mmol x yield x MW(product) = the product mass printed.

        `mass_check` needs a mass AND a mole count on the SAME row, and every
        example step in this patent writes its product as a mass with no mole count.
        So the single most important arithmetic in the document is invisible to the
        check built to find it. Example 1 Step 1 prints 28.6 g of a compound whose
        weight is 204.68; 0.2 mol at 84% is 34.39 g. The annotation flagged that step
        and this stage passed it, which is the one disagreement in the agreement
        matrix and the reason this check exists.

        The identity needs no mole count on the product row, only the charge, the
        yield and a resolved structure, so it reaches the eight rows the other check
        cannot. It is arithmetic on the PATENT's own three numbers, so a
        disagreement is the document contradicting itself and never an extraction
        error: `about` is `patent` and the question is worded to say so.

        Three of the eight land within half a unit of the chlorine-for-hydrogen
        shift, by a path completely independent of mass-over-moles, which is
        corroboration of the des-chloro finding rather than the same measurement
        twice. The rest cluster near -44.7 and are deliberately left unexplained:
        naming a cause this stage cannot support would be the machine guessing in
        front of a reviewer who cannot check it.
        """
        by_record = {r.record_id: r for r in self.records}
        for r in self.data["reactions"]:
            rec = by_record.get(r["id"])
            if rec is None:
                continue
            product = mass = None
            charges: list[float] = []
            for c in (r.get("compounds") or []):
                q = c.get("quantity") or {}
                if c.get("role") == "product" and q.get("mass_g") is not None:
                    product, mass = c.get("identifier"), float(q["mass_g"])
                elif c.get("role") == "reactant" and q.get("mmol"):
                    charges.append(float(q["mmol"]))
            yield_pct = r.get("product_yield_pct")
            mw = (self.structures.get(product) or {}).get("mw") if product else None

            if not (product and mass and charges and yield_pct and mw):
                rec.checks.append(check(
                    "quantity.yield_identity", "quantity", "skip",
                    "Whether the product mass agrees with the charge and the yield",
                    "This step does not print all four of a product mass, a "
                    "reactant molar charge, a yield and a resolved product "
                    "structure, so the identity cannot be applied to it.",
                    about_fields=[]))
                continue

            limiting = min(charges)
            scale = limiting / 1000.0 * (yield_pct / 100.0)
            predicted, implied = mw * scale, mass / scale
            delta = implied - mw
            tol = max(ABS_TOL_FLOOR, REL_TOL * mw)
            name_en = self.english_name(product)
            arithmetic = (f"{fmt_value(limiting)} mmol charged at "
                          f"{fmt_value(yield_pct)}% of {name_en}, molecular weight "
                          f"{mw:.2f}, comes to {predicted:.2f} g")

            if abs(delta) <= tol:
                rec.checks.append(check(
                    "quantity.yield_identity", "quantity", "pass",
                    "Whether the product mass agrees with the charge and the yield",
                    f"{arithmetic}, and the patent prints {fmt_value(mass)} g. "
                    f"Implied molecular weight {implied:.2f} against {mw:.2f}, "
                    f"within tolerance {tol:.2f}.", about_fields=[]))
                continue

            cl_for_h = abs(delta + CL_FOR_H) < CL_WINDOW
            tail = (f" The shortfall of {delta:+.2f} is within half a unit of the "
                    f"{-CL_FOR_H:+.2f} that swapping one chlorine for one hydrogen "
                    f"costs. That is a lead for the reviewer and not a diagnosis."
                    if cl_for_h else
                    f" The offset of {delta:+.2f} has no explanation this stage can "
                    f"support, which is why it is being shown to a person.")
            detail = (f"{arithmetic}, but the patent prints {fmt_value(mass)} g. "
                      f"Implied molecular weight {implied:.2f} against {mw:.2f}, "
                      f"outside the tolerance of {tol:.2f}.{tail}")
            rec.checks.append(check(
                "quantity.yield_identity", "quantity", "fail",
                "Whether the product mass agrees with the charge and the yield",
                detail, needs_human=True, about_fields=["product_yield_pct"]))

            self._claim(
                rec, "yield_identity",
                f"The patent's own numbers for this step do not agree with each "
                f"other. Does the page really print {fmt_value(mass)} g of "
                f"{name_en} from {fmt_value(limiting)} mmol at "
                f"{fmt_value(yield_pct)}%?",
                f"{fmt_value(mass)} g", mass, "g", rec.cited, [], "not_reconciled",
                detail,
                ["The charge, the yield and the product mass printed for this step "
                 "cannot all three be right.",
                 "The numbers are the patent's own, so the annotation recording "
                 "them is not the defect."],
                "value", set(), about="patent", load_bearing=True,
                extra={"basis": "derived"})

    # ------------------------------------------------------------ coverage

    # What makes an uncited line worth a reviewer's attention. Each signal is a fact
    # about the line, never a guess about its meaning, so a line that trips one can
    # be shown to a non-chemist with an English sentence saying exactly why.
    SIGNAL_LABELS_EN = {
        "quantity": "a quantity with a unit",
        "temperature": "a temperature",
        "duration": "a duration",
        "yield": "a percentage",
        "ratio": "a ratio",
        "structure": "a drawn chemical structure",
        "reagent": "the name of a compound the annotation knows",
    }

    def signals(self, n: int, reagent_names: dict[str, str]) -> list[str]:
        raw = self.source.lines[n]
        found: list[str] = []
        if self.source.kind[n] == "image_extract":
            found.append("structure")
        for tok in tokenise(raw):
            if tok.unit in ("g", "ml", "mmol"):
                found.append("quantity")
            elif tok.unit == "C":
                found.append("temperature")
            elif tok.unit == "h":
                found.append("duration")
            elif tok.unit == "%":
                found.append("yield")
        if re.search(r"\d+\s*:\s*\d+", fold(raw)):
            found.append("ratio")
        norm = self.source.norm.get(n, "")
        low = raw.lower()
        for name, needle in reagent_names.items():
            if (needle and needle in norm) or (len(name) > 6 and name in low):
                found.append("reagent")
                break
        seen, ordered = set(), []
        for s in found:
            if s not in seen:
                seen.add(s)
                ordered.append(s)
        return ordered

    # ------------------------------------------------------------ quantity sweep

    QUANTITY_VERDICT_EN = {
        "schema_loss_range": (
            "The patent prints this as a RANGE and the field that would hold it is "
            "a single number, so only one end of it could ever be recorded. The "
            "annotation is not wrong; the schema cannot hold what the document "
            "says."),
        "schema_loss_second": (
            "This step has more than one stage and the field that would hold this "
            "number already holds {held} from another stage. The annotation wrote "
            "both stages out in its notes, where nothing downstream can read them. "
            "The annotation is not wrong; the schema has one slot and the step has "
            "two."),
        "gap": (
            "The field that would hold this is empty. The patent prints the number "
            "and the annotation records nothing, so either it was missed or it was "
            "left out on purpose."),
        "unmapped": (
            "No field on this record could hold a quantity of this kind, so if the "
            "number matters it has nowhere to go."),
    }

    def source_blocks(self) -> dict[int, tuple]:
        """Line number -> every line carrying the SAME printed text.

        A Chinese line and the English it was translated into are one fact printed
        once, not two facts. Any sweep that walks lines and asks "did we record
        this" must dedup across the pair or it reports every bilingual fact twice
        and its miss count is roughly doubled for no reason.
        """
        # Two sources of pairing, because one of them has a blind spot.
        #
        # en_for/zh_for pair a Chinese line with its translation, and the heuristic
        # that finds them keys on the line LOOKING Chinese. An NMR line does not:
        #
        #   L199  prose        NMR (CDCl3): d (ppm) 2.64 (s, 3H, ), 2.88 (s, 3H, ...
        #   L200  translation  NMR (CDCl3): d (ppm) 2.64 (s, 3H, ), 2.88 (s, 3H, ...
        #
        # Byte-identical, one printed fact, and blocks (199,) and (200,) - so the
        # solvent named there was counted twice. Five NMR lines on this patent, so
        # eleven substance findings were really six.
        #
        # Identical English is therefore a second, independent reason to group. It
        # can only ever MERGE blocks, so it can only ever reduce double counting.
        groups: dict[int, set] = {n: {n, *self.source.en_for.get(n, ()),
                                      *self.source.zh_for.get(n, ())}
                                  for n in self.source.numbers}
        by_text: dict[str, list[int]] = {}
        for n in self.source.numbers:
            text = (self.source.text_en.get(n) or "").strip()
            if text:
                by_text.setdefault(text, []).append(n)
        for same in by_text.values():
            if len(same) < 2:
                continue
            merged = set().union(*(groups[n] for n in same))
            for n in merged:
                groups.setdefault(n, set()).update(merged)
        return {n: tuple(sorted(g)) for n, g in groups.items()}

    def line_sweep(self, *, tokens, key, asserted, tally, excuse=None) -> list:
        """Walk every cited line, and of each thing printed on it ask: did we record it?

        THIS IS THE RECALL HALF, AND IT IS NOT SPECIFIC TO QUANTITIES. Line coverage
        cannot see any of it: a line can be cited by one record while carrying three
        facts with two of them dropped, and `uncited_with_chemistry` still reads zero.

            for each cited line n:
                block = {n} + the lines n was translated from or into
                for each TOKEN printed on n:
                    k = key(token)
                    |
                    +-- k is None            -> not this sweep's business, skip
                    +-- k already seen in    -> skip; one printed fact, not two
                    |   this block
                    +-- k in what any record -> accounted
                    |   citing the block
                    |   structurally asserts
                    +-- excuse(token) says   -> excused, counted under its own name
                    |   so
                    +-- otherwise            -> missed, returned to the caller

        `asserted` MUST be built from what a record STRUCTURALLY says, never from the
        prose of a quote. That is the trap this whole sweep turns on: a "16" occurring
        anywhere inside any quotation would otherwise count as coverage of a
        sixteen-hour reaction, and the sweep reports a clean zero that means nothing.
        The same applies to a substance name against a record's quoted text.

        Extracted from quantity_coverage so a second sweep plugs a tokeniser and a key
        into it rather than copying the loop. The copy is the failure worth designing
        against: two walks that are meant to agree will drift, and this project has a
        live example of exactly that in the grounded denominator the report and the
        engine each computed their own way until they disagreed by one row.
        """
        blocks = self.source_blocks()
        seen: dict[tuple, set] = {}
        missed: list[tuple] = []

        for n in sorted(self.cited_lines):
            block = blocks[n]
            folded = fold(self.source.lines[n])
            for tok in tokens(n):
                k = key(tok)
                if k is None:
                    continue
                if k in seen.setdefault(block, set()):
                    continue
                seen[block].add(k)
                tally["tokens"] += 1

                held = set()
                for m in block:
                    held |= asserted.get(m, set())
                if k in held:
                    tally["accounted"] += 1
                    continue
                why = excuse(tok, folded) if excuse is not None else None
                if why is not None:
                    tally[why] += 1
                    continue
                missed.append((n, block, tok, folded))
        return missed

    def quantity_coverage(self) -> None:
        """Every quantity printed on a cited line, against every quantity claimed.

        Line coverage cannot see this. A line can be cited by one record while
        carrying three facts with two of them dropped, and `uncited_with_chemistry`
        still reads zero. So each cited line is tokenised and every (value, unit) is
        matched against what a claim on a record citing that line STRUCTURALLY
        asserts - `claimed_value` and `claimed_unit`, never the prose of a quote.
        Matching against quoted text instead is the trap: a "16" occurring anywhere
        inside any quotation would then count as coverage of a sixteen-hour
        reaction, and the sweep reports a clean zero that means nothing.

        Matching is unit-aware, so 0.22 mol on the page answers 220 mmol in the
        record, and a Chinese line is matched together with the English it was
        translated into, so one printed quantity is not counted twice. A range is
        one fact, not two, so its endpoints are merged before anything is queued.

        What comes back is not one number but four, and the four need different
        fixes. The one that matters most is `schema_loss`: the annotator read the
        document correctly and the container could not hold the answer. Example 1
        step 6 is one numbered step with two transformations in one flask, 16 h of
        etherification then 4 h of hydrolysis; `conditions.time_h` is a single float
        and holds 4.0. A consumer reads a four-hour step where the truth is twenty
        hours over two stages, which is a factor of five on the most expensive input
        to any throughput model. Re-running the extraction would not fix it.
        """
        asserted: dict[int, set] = {}
        for c in self.claims:
            if c.get("claimed_value") is None or not c.get("claimed_unit"):
                continue
            key = (c["claimed_unit"], round(float(c["claimed_value"]), 6))
            for n in c["cited_lines"]:
                asserted.setdefault(n, set()).add(key)

        by_record = {r.record_id: r for r in self.records}

        self.quantity_tally = {"tokens": 0, "accounted": 0, "vessel": 0,
                               "schema_loss": 0, "gap": 0, "unmapped": 0}
        self.quantity_findings: list[dict] = []
        # (kind, field path) -> every instance of that one schema limitation.
        # Eight of this patent's twelve schema losses are the SAME ticket, range
        # against a single-float `time_h`, asked against eight different lines. A
        # reviewer answering one question eight times is the clearest waste in the
        # queue, and collapsing it at render time would be the UI guessing which
        # rows are the same question. Grouped here, where the answer is known.
        self.schema_tickets: dict[tuple, list] = {}

        # A unit this sweep does not weigh returns no key, which is how line_sweep
        # is told to walk past it without counting it or deduping on it.
        def quantity_key(tok):
            if tok.unit not in QUANTITY_UNITS:
                return None
            return (tok.unit, round(tok.canonical(), 6))

        missed = self.line_sweep(
            tokens=lambda n: tokenise(self.source.lines[n]),
            key=quantity_key,
            asserted=asserted,
            tally=self.quantity_tally,
            excuse=lambda tok, folded: (
                "vessel" if tok.unit == "ml" and is_vessel(folded, tok.end) else None),
        )

        for line, block, group in merge_ranges(missed):
            self.record_quantity_miss(line, block, group, by_record)
        self.emit_schema_tickets()

    def record_quantity_miss(self, line: int, block: tuple, group: list,
                             by_record: dict) -> None:
        """Attach one unaccounted quantity to the record that should have held it."""
        low, high = group[0], (group[-1] if len(group) > 1 else None)
        percent_is = "yield" if (low.unit == "%" and is_yield(low.folded, low.start)) \
            else "concentration"
        citers = sorted({r for m in block for r in self.cited_lines.get(m, ())})

        best = None
        for rid in citers:
            rec, raw = by_record.get(rid), self.raw_of.get(rid)
            if rec is None or raw is None:
                continue
            holder = quantity_holder(raw, rec.kind, low.unit, percent_is)
            if holder is None:
                continue
            # A reaction owns the conditions of its own step; a compound record
            # citing the same line owns only its own row. Prefer the reaction, then
            # the lowest id, so the claim lands where a fix can be made and the
            # choice is a function of the inputs and nothing else.
            rank = (0 if rec.kind == "reaction" else 1, rid)
            if best is None or rank < best[0]:
                best = (rank, rec, holder)

        if best is None:
            rec = next((by_record[r] for r in citers if r in by_record), None)
            if rec is None:
                return
            path, occupied, kind = "", None, "unmapped"
        else:
            _, rec, (path, occupied, supports_range) = best
            if high is not None and not supports_range:
                kind = "schema_loss_range"
            elif occupied is not None:
                kind = "schema_loss_second"
            else:
                kind = "gap"

        printed = say_quantity(low.value, low.raw_unit,
                               high.value if high is not None else None)
        why = self.QUANTITY_VERDICT_EN[kind].format(
            held=say_quantity(float(occupied), low.raw_unit)
            if occupied is not None else "")
        family = "schema_loss" if kind.startswith("schema_loss") else "completeness"
        self.quantity_tally["schema_loss" if family == "schema_loss"
                            else ("gap" if kind == "gap" else "unmapped")] += 1

        # The magnitude here has to be the canonical one, not the printed one.
        # low.unit is already canonical (kg folds to g), so pairing it with the
        # raw value gave "1 g" and "1 kg" on one line the same tag, and so the
        # same claim id: a reviewer answering one would have silently answered
        # the other. quantity_key above already dedupes on canonical(), so using
        # it here cannot group differently from the sweep that found these.
        tag = f"{line}:{fmt_value(low.canonical())}{low.unit}"
        if kind.startswith("schema_loss"):
            # The CHECK stays on the record, because the loss really did happen
            # there. Only the QUESTION is pooled, because it is one question.
            ticket = (kind, path)
            cid = claim_id(f"{self.patent_id}_patent",
                           f"__schema__[{kind}:{path}]")
            self.schema_tickets.setdefault(ticket, []).append(
                {"line": line, "printed_en": printed, "record_id": rec.record_id,
                 "record_label_en": rec.label_en})
            rec.checks.append(check(
                f"{family}.{path or 'unmapped'}[{tag}]", family, "warn",
                f"The quantity {printed} printed on line {line}",
                (f"It is not asserted by any claim on any record citing line "
                 f"{line}. The field that would hold it is {path}. " + why),
                needs_human=True, about_fields=[path] if path else []))
            self.quantity_findings.append(
                {"line": line, "printed_en": printed, "verdict": kind,
                 "record_id": rec.record_id, "record_label_en": rec.label_en,
                 "field": path or None, "claim_id": cid})
            return
        rec.checks.append(check(
            f"{family}.{path or 'unmapped'}[{tag}]", family,
            "warn" if family == "schema_loss" else "fail",
            f"The quantity {printed} printed on line {line}",
            (f"It is not asserted by any claim on any record citing line {line}. "
             + (f"The field that would hold it is {path}. " if path else "") + why),
            needs_human=True, about_fields=[path] if path else []))
        # The question has to follow from `about` or the axis is decoration. These
        # two claims look identical on screen and ask opposite things: one asks a
        # reviewer to judge an omission, the other tells them there is nothing to
        # judge because the field could not have held the answer. Asking "should it
        # have?" of a schema loss invites a reviewer to mark correct work wrong,
        # which is the exact failure `about` exists to prevent.
        question = (
            f"Line {line} prints {printed}, and the field that would hold it, "
            f"{path}, cannot. Nothing was misread. Is a schema change worth it?"
            if family == "schema_loss" else
            f"Line {line} prints {printed}. The annotation does not record it "
            f"anywhere. Should it have?")
        claim = self._claim(
            rec, f"__quantity__[{tag}]", question,
            printed, low.value, low.unit, self.source.with_partners([line]), [],
            "not_checkable",
            f"{printed} is printed on line {line} and no claim on any record citing "
            f"that line asserts it. " + why,
            ["A quantity the patent prints that nothing in the annotation holds."],
            "value", {line}, about="schema" if family == "schema_loss"
            else "extraction", load_bearing=True,
            rec_field=f"__quantity__.line_{line}.{fmt_value(low.canonical())}{low.unit}")
        claim["quantity_verdict"] = kind
        # Ordered within tier 2 by what a fix would take: an empty field is a
        # re-extraction, a schema loss is a schema change, and a number with nowhere
        # at all to go is a design question.
        claim["risk"] = {"gap": 0.70, "unmapped": 0.65,
                         "schema_loss_second": 0.60,
                         "schema_loss_range": 0.55}[kind]
        self.quantity_findings.append(
            {"line": line, "printed_en": printed, "verdict": kind,
             "record_id": rec.record_id, "record_label_en": rec.label_en,
             "field": path or None, "claim_id": claim["claim_id"]})


    def emit_schema_tickets(self) -> None:
        """One claim per schema limitation, not one per time it bit.

        The reviewer is answering "is a schema change worth it for this field?".
        That question has one answer however many lines provoked it, and the eight
        instances are evidence for it rather than eight separate decisions. Every
        instance is still listed inside the one claim, and every affected record
        still carries its own failing check, so nothing is hidden - only the
        question is asked once.
        """
        patent_rec = next((r for r in self.records if r.kind == "patent"), None)
        if patent_rec is None:
            return
        for (kind, path), hits in sorted(self.schema_tickets.items()):
            lines = sorted({h["line"] for h in hits})
            printed = sorted({h["printed_en"] for h in hits})
            records = sorted({h["record_label_en"] for h in hits})
            shape = ("states a range where the field holds a single number"
                     if kind == "schema_loss_range" else
                     "has more than one stage where the field holds one value")
            reason = (
                f"On {len(hits)} occasion{'s' if len(hits) > 1 else ''} the patent "
                f"{shape}, and `{path}` could not carry it. The quantities lost are "
                + english_list(printed) + f", on line{'s' if len(lines) > 1 else ''} "
                + compact_lines(lines)
                + f". {len(records)} record{'s are' if len(records) > 1 else ' is'} "
                f"affected. Nothing was misread and re-running the extraction "
                f"changes nothing: the field cannot hold the answer.")
            self._claim(
                patent_rec, f"__schema__[{kind}:{path}]",
                f"`{path}` cannot hold what the patent prints, {len(hits)} times "
                f"over. Is widening it worth it?",
                english_list(printed), None, None,
                self.source.with_partners(lines), [], "not_checkable", reason,
                [f"One schema limitation, hit {len(hits)} times."],
                "value", set(lines), about="schema", load_bearing=True,
                rec_field=f"__schema__.{kind}.{path}",
                extra={"quantity_verdict": kind,
                       "schema_instances": hits})

    def build_coverage(self) -> None:
        reagent_names: dict[str, str] = {}
        for c in self.data["compounds"]:
            for name in [c["identifier"], *(c.get("aliases") or [])]:
                if not name or looks_like_smiles(name):
                    continue
                reagent_names[name.lower()] = normalise(name) if has_chinese(name) else ""

        patent_rec = next(r for r in self.records
                          if r.record_id == f"{self.patent_id}_patent")

        self.coverage_lines: list[dict] = []
        self.uncited_chemistry: list[int] = []
        for n in self.source.numbers:
            kind = self.source.label_kind(n, self.claim_lines)
            citers = sorted(self.cited_lines.get(n, ()))
            if kind == "blank":
                status, sigs = "covered" if citers else "uncited_plain", []
            else:
                sigs = self.signals(n, reagent_names)
                if citers:
                    status = "covered"
                elif kind == "translation" or n in self.source.en_hint:
                    # A translation line is not source. build_enriched.py writes
                    # one under each paragraph, and a record cites the original,
                    # not its rendering. Counting it as uncited chemistry asks a
                    # reviewer the same question twice: once about the line the
                    # patent prints and once about the machine's English for it.
                    # On a German patent that is most of the census, because
                    # every paragraph has such a partner.
                    #
                    # `kind` alone is not enough, and this is measured, not
                    # supposed. Only the FIRST line of a translation carries the
                    # "    > EN: " mark; every continuation line after it looks
                    # exactly like a line of the patent, so `kind` sees one line
                    # of a block and calls the rest source. Every table in
                    # US20100041557A1 is repeated inside its own translation, and
                    # 40 of that run's 64 coverage claims were the English copy of
                    # a table row a record already cites in the original.
                    #
                    #   714  16 A crystalline form A of ...     <- source
                    #   717  | 1 | 5.6+-0.2 deg |               <- source, cited
                    #   726      > EN: A crystalline form A ...  <- kind=translation
                    #   727  | 1 | 5.6+-0.2 deg |               <- English, NOT source
                    #
                    # en_hint is resolve_translations.py's paragraph walk, which is
                    # the only thing that knows where a block ends. A regex cannot:
                    # tried here first, it read claim 16's own 2theta table as
                    # English because a claim number does not close a run the way a
                    # paragraph marker does.
                    status = "covered"
                elif sigs:
                    status = "uncited_with_chemistry"
                    self.uncited_chemistry.append(n)
                else:
                    status = "uncited_plain"
            self.coverage_lines.append({
                "n": n,
                "kind": kind,
                "has_english": n in self.source.english
                               or kind in ("translation", "heading")
                               or not has_chinese(self.source.lines[n]),
                "text_en": self.source.text_en[n],
                "section_en": self.section_of_line.get(n, "Unassigned"),
                "cited_by": citers,
                "signals": sigs,
                "status": status,
            })

        for n in self.uncited_chemistry:
            sigs = next(l["signals"] for l in self.coverage_lines if l["n"] == n)
            # A candidate miss belongs to the patent as a whole, so its verdict
            # keys on the patent with the line number in the field. The convention
            # in verifier/lib/verdict.ts has no slot for a source line, and
            # inventing one would write verdicts that resolveRec cannot load.
            rec = Record(f"{self.patent_id}_line_{n}", "source_line",
                         f"Source line {n}",
                         self.section_of_line.get(n, "Unassigned"),
                         self.source.with_partners([n]),
                         None, None, f"pt:{self.patent_id}")
            self.records.append(rec)
            reason = ("No record in the whole annotation cites this line, and it "
                      "carries " + english_list(
                          [self.SIGNAL_LABELS_EN[s] for s in sigs])
                      + ". Either the extraction missed something here, or the "
                        "line repeats what a nearby record already captured.")
            self._claim(rec, "__coverage__",
                        f"Line {n} carries chemistry that no record cites. Did the "
                        f"annotation miss it?",
                        f"line {n}: " + self.source.text_en[n][:200], None, None,
                        rec.cited, [], "not_checkable", reason,
                        ["An uncited line carrying chemistry is a candidate miss."],
                        "name", {n}, load_bearing=True,
                        rec_field=f"__coverage__.line_{n}")


# Folded before a drawn name is compared with a record name. Every fold here is a
# spelling of the same thing in this corpus, never a chemical claim: the drawing
# pass writes "methylsulfonyl" where the records write "methanesulfonyl", and
# treating those as different names would make the check pass by never running.
_DRAWING_FOLDS = (("methanesulfon", "methylsulfon"), ("methanesulfan", "methylsulfan"),
                  ("sulphon", "sulfon"), ("sulphan", "sulfan"))


def drawing_key(name: str) -> str:
    t = name.lower()
    for a, b in _DRAWING_FOLDS:
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "", t)


def english_list(items) -> str:
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


MOLAR_RATIO = re.compile(r"\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?"
                         r"(?::\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)+")


def molar_ratios(text: str) -> list[str]:
    """The ratio itself, lifted out of the Chinese sentence that states it.

    `molar_ratio_text` is a whole Chinese clause and none of it may reach the
    artifact. The ratio inside it is ASCII, is the entire claim the field makes, and
    is exactly what a reviewer can check against the printed page, so it is lifted
    out and the sentence is left behind.
    """
    seen, out = set(), []
    for m in MOLAR_RATIO.finditer(fold(text)):
        s = re.sub(r"\s+", "", m.group(0))
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


# ---------------------------------------------------------------- the artifact

RISK_BANDS = (("high", 0.60), ("medium", 0.30), ("low", 0.0))

# The severity ladder. `tier` says which census a claim belongs to and `severity`
# says what the reviewer will find when they get there. Ordered worst first, which
# is the order the queue is read in.
SEVERITIES = ["critical", "high", "medium", "low", "none"]

SEVERITY_MEANING = {
    "critical": "a value on no line of the patent. The fabrication signal",
    "high":     "the patent's own numbers contradict each other",
    "medium":   "a judgement, or a row whose checks failed",
    "low":      "the fact stands and the pointer or the quote is wrong",
    "none":     "nothing for a reviewer to act on",
}

# `not_found` and `not_reconciled` are deliberately separate and must stay that way.
# `not_found` means the claimed value is not on the lines this claim cites: it is the
# hallucination signal and the most load-bearing label in the artifact. A consumer
# counting it to answer "how many possible fabrications" must get that number and no
# other. `not_reconciled` means the value IS where the record says it is and the
# patent's own numbers do not multiply out, which is not about citation at all and is
# never the annotation's fault. Folding the second into the first would have made
# this patent report 13 possible fabrications when the answer is 5.
VERDICTS = ["not_found", "not_reconciled", "partial", "not_checkable", "found"]
CHECK_STATUSES = ["fail", "warn", "pass", "skip"]
FAMILIES = ["grounding", "reference", "structure", "drawing", "quantity",
            "naming", "consistency", "completeness", "schema_loss"]

TIERS = [1, 2, 3, 4]

TIER_MEANING = {
    1: "census: the machine looked and could not confirm it",
    2: "census: a candidate miss, chemistry nothing in the annotation holds",
    3: "the machine matched it cleanly, to be sampled rather than read",
    4: "the machine had no opinion. Sampled, and NOT in tier 3's bound",
}

# Keys the engine uses to carry a claim between passes. They are working state, not
# contract, and are stripped before the file is written so a consumer can never
# come to depend on one.
PRIVATE = ("_field_name", "_matched", "_derive", "_value", "_unit",
           "_subject", "_elsewhere", "_finding")

# Which family a claim belongs to, for the roll-up. Everything a claim can be is a
# grounding question except the coverage sweep, which asks the opposite question.
def claim_family(claim: dict) -> str:
    if claim["field"] == "__coverage__":
        return "completeness"
    if claim["field"].startswith("__quantity__"):
        return "schema_loss" if claim.get("about") == "schema" else "completeness"
    if claim["field"] in ("validation_flags", "resolved"):
        return "consistency"
    if claim["basis"] == "derived":
        return "quantity"
    return "grounding"


def band(risk: float) -> str:
    for name, floor in RISK_BANDS:
        if risk >= floor:
            return name
    return "low"


def generated_at() -> str:
    """Now, in UTC, or the pinned time SOURCE_DATE_EPOCH names.

    The contract asks for a real timestamp and also for two runs to diff to nothing.
    Those pull against each other, so the timestamp is honest by default and
    pinnable when a diff is what is wanted. Nothing else in the file moves.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    when = (datetime.fromtimestamp(int(epoch), tz=timezone.utc) if epoch
            else datetime.now(timezone.utc))
    return when.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def assemble(run: Run) -> dict:
    records = []
    for rec in run.records:
        risk = max([c["risk"] for c in rec.claims] or [0.0])
        if any(c["status"] == "fail" for c in rec.checks):
            risk = max(risk, 0.8)
        elif any(c["status"] == "warn" for c in rec.checks):
            risk = max(risk, 0.4)
        records.append({
            "record_id": rec.record_id,
            "record_kind": rec.kind,
            "uuid": rec.uuid,
            "rec": rec.rec,
            "stratum": rec.stratum,
            "annotation_flags_en": [FLAG_MEANING_EN.get(f, f)
                                    for f in sorted(rec.flags)],
            "label_en": rec.label_en,
            "section_en": rec.section_en,
            "cited_lines": rec.cited,
            "claim_ids": [c["claim_id"] for c in rec.claims],
            "checks": rec.checks,
            "risk": round(risk, 2),
            "risk_band": band(risk),
        })

    # Highest risk first, then by source position, then by id. Every key is a
    # function of the inputs, so the order is stable across runs and a diff between
    # two artifacts is a diff in the data.
    claims = sorted(run.claims,
                    key=lambda c: (c["tier"], -c["risk"],
                                   min(c["cited_lines"]) if c["cited_lines"] else 10**6,
                                   c["record_id"], c["field"]))
    # Read before the strip, because `_finding` is working state. See the tier-1 and
    # tier-4 feeders below for what it is for.
    findings_no_opinion = sum(1 for c in claims
                              if c.get("_finding") and c["auto"] == "not_checkable")
    finding_claims = sum(1 for c in claims if c.get("_finding"))

    # THE FAMILY, WRITTEN DOWN RATHER THAN LEFT TO BE REDERIVED.
    #
    # `claim_family` needs `field`, `about` and `basis`, all of which are on the
    # claim, so every consumer CAN work it out. The report did, in TypeScript, as an
    # enumeration of auto statuses that happened to give the same denominator as
    # this engine's grounded percentage - until one `not_reconciled` grounding claim
    # existed, at which point the report printed "the engine says 94.6% and this
    # report counts 94.9%" about a difference that was purely definitional.
    #
    # Two implementations of one rule will drift; this one had, silently, and its
    # only symptom was an integrity light that would now be red forever. The rule
    # lives here and the answer travels with the claim.
    for c in claims:
        c["family"] = claim_family(c)

    for c in claims:
        for k in PRIVATE:
            c.pop(k, None)

    verdicts = {v: sum(1 for c in claims if c["auto"] == v) for v in VERDICTS}
    severities = {v: sum(1 for c in claims if c["severity"] == v)
                  for v in SEVERITIES}
    work_kinds = {k: sum(1 for c in claims if c["work_kind"] == k)
                  for k in ("judgement", "comparison")}
    families = {f: sum(1 for c in claims if claim_family(c) == f) for f in FAMILIES}
    tiers = {str(t): sum(1 for c in claims if c["tier"] == t) for t in TIERS}

    # The same three numbers again, derived from WHERE THE WORK CAME FROM rather
    # than by counting the queue. A denominator recovered from the list it is meant
    # to measure cannot detect the one failure that matters: a claim that was never
    # emitted at all. Tier 2 held fifteen claims while both of its old denominators
    # read zero, and nothing in the file could say so. `agrees` is the assertion a
    # consumer can check instead of trusting either number on its own.
    cov_qty = run.quantity_tally
    unconfirmed = sum(1 for c in claims
                      if c["tier"] != 2 and c["auto"] in ("not_found",
                                                          "not_reconciled",
                                                          "partial"))
    promoted = sum(1 for c in claims
                   if c["tier"] == 1 and c["auto"] == "found")
    no_opinion = sum(1 for c in claims
                     if c["tier"] != 2 and c["auto"] == "not_checkable")
    # A failing check that names no claim field gets a claim of its own, and that
    # claim is a FINDING rather than an absence of opinion, so it is censused in
    # tier 1 and not sampled in tier 4. Counted off the checks, which is where the
    # claims came from, rather than off the queue they landed in.
    findings = sum(1 for r in records for c in r["checks"]
                   if c["status"] == "fail" and not c["about_fields"])
    # Every finding is censused in tier 1, but they do not all arrive the same way.
    # The GENERIC finding claim is always `not_checkable`, so tier 1 has to add it and
    # tier 4 has to subtract it. A finding claim worded from its own check may be
    # `not_reconciled` instead - the second reader's disagreements are, because the
    # machine did form an opinion - and such a claim is ALREADY inside `unconfirmed`.
    # Counting findings whole then adds it to tier 1 twice and subtracts it from
    # tier 4 where it never was, which is exactly how both numbers went wrong the
    # first time the second reader ran.
    #
    # The population still comes from the CHECKS, so a finding that produced no claim
    # at all is still caught; only the split between the two buckets is read off the
    # claims, and `findings_produced` asserts the two views agree.
    # Tier 2's two feeders, counted from the sweep rather than from the queue. The
    # schema losses are pooled into tickets by (limitation, field), so the ticket
    # count and not the instance count is what a reviewer will actually work.
    quantities = sum(cov_qty.get(k, 0) for k in ("gap", "unmapped"))
    tickets = len(run.schema_tickets)
    feeders = {
        "1": {"population": unconfirmed + promoted + findings_no_opinion,
              "findings_from_checks": findings,
              "findings_produced": finding_claims,
              "from_en": f"{unconfirmed} claims the machine looked at and could "
                         f"not confirm, plus {promoted} it matched cleanly on a "
                         f"record whose own checks failed, plus "
                         f"{findings_no_opinion} of {findings} failing checks that "
                         f"name no claim field and about which the machine could "
                         f"form no opinion; the other "
                         f"{findings - findings_no_opinion} are already inside the "
                         f"first number"},
        "2": {"population": len(run.uncited_chemistry) + quantities + tickets,
              "from_en": f"{len(run.uncited_chemistry)} source lines no record "
                         f"cites, plus {quantities} quantities on cited lines no "
                         f"claim asserts, plus {tickets} schema tickets pooled "
                         f"from {cov_qty.get('schema_loss', 0)} instances"},
        "3": {"population": len(claims) - tiers["1"] - tiers["2"] - tiers["4"],
              "from_en": "every claim the machine matched cleanly, which is the "
                         "only population the sampled bound may be drawn from"},
        "4": {"population": no_opinion - findings_no_opinion,
              "from_en": f"{no_opinion - findings_no_opinion} claims the machine had no "
                         f"opinion about, "
                         f"demoted out of the census because they are a different "
                         f"population from claims it looked at and failed"},
    }
    tier_population = {t: {**feeders[t], "claims": tiers[t],
                           "agrees": feeders[t]["population"] == tiers[t]}
                       for t in tiers}
    # The denominators ui-report needs. A stratified sample cannot be drawn, and a
    # confidence bound cannot be computed, from a filtered list: both need the
    # population size of every stratum, including the ones that end up with no
    # sampled claim at all.
    strata: dict[str, int] = {}
    for c in claims:
        if c["tier"] == 3:
            strata[c["stratum"]] = strata.get(c["stratum"], 0) + 1
    # The bound needs this split, not just the total. A `found` against 34 cited
    # lines and a `found` against one are not the same evidence, and averaging them
    # into a single residual-defect rate quietly borrows the credibility of the
    # narrow matches to cover the wide ones.
    widths = {"narrow": 0, "wide": 0}
    for c in claims:
        if c["tier"] == 3:
            widths[c["evidence_class"]] += 1
    about = {a: sum(1 for c in claims if c["about"] == a)
             for a in ("extraction", "patent", "schema")}
    all_checks = [c for r in records for c in r["checks"]]
    statuses = {s: sum(1 for c in all_checks if c["status"] == s)
                for s in CHECK_STATUSES}
    check_families = {f: sum(1 for c in all_checks if c["family"] == f)
                      for f in FAMILIES}

    cov = run.coverage_lines
    cov_summary = {
        "total": len(cov),
        "covered": sum(1 for l in cov if l["status"] == "covered"),
        "uncited_with_chemistry": sum(1 for l in cov
                                      if l["status"] == "uncited_with_chemistry"),
        "uncited_plain": sum(1 for l in cov if l["status"] == "uncited_plain"),
    }

    by_section = []
    for label in run.section_order:
        sec_claims = [c for c in claims if c["section_en"] == label]
        sec_records = [r for r in records if r["section_en"] == label]
        by_section.append({
            "section_en": label,
            "records": len(sec_records),
            "claims": len(sec_claims),
            "found": sum(1 for c in sec_claims if c["auto"] == "found"),
            "partial": sum(1 for c in sec_claims if c["auto"] == "partial"),
            "not_found": sum(1 for c in sec_claims if c["auto"] == "not_found"),
            "not_reconciled": sum(1 for c in sec_claims
                                  if c["auto"] == "not_reconciled"),
            "not_checkable": sum(1 for c in sec_claims
                                 if c["auto"] == "not_checkable"),
            "uncited_chemistry_lines": sum(
                1 for l in cov if l["section_en"] == label
                and l["status"] == "uncited_with_chemistry"),
            # THE RECALL HALF, PER SECTION. Rolled up from the per-line status the
            # substance sweep wrote, not counted a second way: two derivations of one
            # number is how this pack's report and engine ended up with two grounded
            # denominators. A section is only clean when `unaccounted` is 0 AND
            # `unread` is 0, and the two are published apart because "nothing is
            # missing here" and "nobody has looked here" are different facts.
            "lines_total": sum(1 for l in cov if l["section_en"] == label
                               and l["kind"] != "blank"),
            "substance_accounted": sum(1 for l in cov if l["section_en"] == label
                                       and l.get("substance") == "accounted"),
            "substance_unaccounted": sum(1 for l in cov if l["section_en"] == label
                                         and l.get("substance") == "unaccounted"),
            "substance_none": sum(1 for l in cov if l["section_en"] == label
                                  and l.get("substance") == "none"),
            "substance_unread": sum(1 for l in cov if l["section_en"] == label
                                    and l.get("substance") == "unread"
                                    and l["kind"] != "blank"),
        })

    grounding = [c for c in claims if claim_family(c) == "grounding"]
    checkable = [c for c in grounding if c["auto"] != "not_checkable"]
    grounded_pct = (round(100.0 * sum(1 for c in checkable
                                      if c["auto"] == "found") / len(checkable), 1)
                    if checkable else 0.0)
    lines_worth_citing = [l for l in cov if l["kind"] not in ("blank",)]
    covered_pct = (round(100.0 * sum(1 for l in lines_worth_citing
                                     if l["status"] == "covered")
                         / len(lines_worth_citing), 1)
                   if lines_worth_citing else 0.0)
    resolved = sum(1 for e in run.data["structures"] if e.get("formula"))
    structure_pct = (round(100.0 * resolved / len(run.data["structures"]), 1)
                     if run.data["structures"] else 0.0)

    not_found = [c for c in grounding if c["auto"] == "not_found"]
    failing = [c for c in all_checks if c["status"] == "fail"]

    blocking = []
    for c in not_found[:20]:
        blocking.append(f"{c['record_label_en']} - {c['field_label_en']}: "
                        f"{c['auto_reason_en']}")
    for c in failing[:20]:
        blocking.append(f"{c['title_en']}: {c['detail_en']}")

    verdict = (
        f"{len(claims)} claims were put to the source. "
        f"{verdicts['found']} were found on the lines the annotation itself cites, "
        f"{verdicts['partial']} were only partly found, "
        f"{verdicts['not_found']} were NOT found and are the ones to read first, "
        f"and {verdicts['not_checkable']} are judgements no string match can "
        f"settle. Of the {len(checkable)} grounding claims a machine can decide, "
        f"{grounded_pct}% are grounded. "
        f"{cov_summary['uncited_with_chemistry']} source lines carry chemistry that "
        f"no record cites, and each has its own entry in the queue. "
        f"{statuses['fail']} record checks fail and {statuses['warn']} warn. "
        f"{resolved} of {len(run.data['structures'])} compound identifiers resolve "
        f"to a drawable structure. "
        + ("Nothing here is a verdict: every line is a prompt for a human to agree "
           "or overrule."))

    return {
        "patent_id": run.patent_id,
        "engine_version": ENGINE_VERSION,
        "generated_at": generated_at(),
        "source": {
            "file": shown(run.source.path),
            "sha256": run.source.sha256,
            "line_count": len(run.source.lines),
        },
        "summary": {
            "records": {
                "total": len([r for r in records
                              if r["record_kind"] != "source_line"]),
                "compound": sum(1 for r in records
                                if r["record_kind"] == "compound"),
                "reaction": sum(1 for r in records
                                if r["record_kind"] == "reaction"),
                "pathway": sum(1 for r in records if r["record_kind"] == "pathway"),
                "patent": sum(1 for r in records if r["record_kind"] == "patent"),
                "source_line": sum(1 for r in records
                                   if r["record_kind"] == "source_line"),
            },
            "claims": {"total": len(claims),
                       "needs_human": sum(1 for c in claims if c["needs_human"]),
                       **verdicts},
            "claims_by_family": families,
            "claims_by_tier": tiers,
            "tier_population": tier_population,
            "claims_by_severity": severities,
            "claims_by_work_kind": work_kinds,
            "work_seconds_measured": WORK_SECONDS_MEASURED,
            "tier3_population_by_stratum": dict(sorted(strata.items())),
            "tier3_population_by_width": widths,
            "claims_by_subject": about,
            "field_basis": {k: dict(sorted(v.items()))
                            for k, v in sorted(run.bases.items())},
            "agreement_with_annotation": {
                k: len(v) for k, v in sorted(run.agreement.items())},
            "checks": {"total": len(all_checks), **statuses},
            "checks_by_family": check_families,
            "source_coverage": cov_summary,
            "quantity_coverage": {**run.quantity_tally,
                                  "findings": run.quantity_findings},
            # The same tally for names. `readers` is published beside it because
            # "two readers agreed" and "one reader ran" produce the same finding
            # count and mean completely different things.
            "substance_coverage": {**run.substance_tally,
                                   "readers": sorted(set(run.substance_readers)),
                                   "findings": run.substance_findings},
            "grounding_failed": bool(not_found),
        },
        "claims": claims,
        "records": records,
        "source_coverage": {"lines": cov, "summary": cov_summary},
        "completeness": {
            "score": {"grounded_pct": grounded_pct,
                      "covered_pct": covered_pct,
                      "structure_pct": structure_pct},
            "verdict_en": verdict,
            "blocking_en": blocking,
            "by_section": by_section,
        },
    }


# ---------------------------------------------------------------- the gate

def chinese_runs(text: str) -> list[str]:
    return re.findall(CJK.pattern + "+", text)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check" in sys.argv
    patent_id = args[0] if args else DEFAULT_PATENT_ID

    data = load_inputs(patent_id)
    run = Run(patent_id, data)
    run.build()
    artifact = assemble(run)

    body = json.dumps(artifact, indent=2, ensure_ascii=False, sort_keys=True) + "\n"

    # The one gate that is not about the patent at all. Every string in this file
    # reaches a screen belonging to a reader who has no Chinese, so a single Han
    # character surviving into it is a defect in this stage and not a finding about
    # the annotation. Checked on the bytes actually about to be written, never on
    # the intent.
    leaked = chinese_runs(body)
    if leaked:
        die(f"{len(leaked)} runs of Chinese survived into the artifact, which is "
            f"unreadable for the reviewer this file exists for: "
            + ", ".join(sorted(set(leaked))[:20]))

    out_dir = REL / "verification"
    out_path = out_dir / f"checks-{patent_id}.json"
    if not check_only:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")

    return report(run, artifact, out_path, check_only)


def report(run: Run, artifact: dict, out_path: Path, check_only: bool) -> int:
    s = artifact["summary"]
    cov = s["source_coverage"]
    claims = artifact["claims"]

    print(f"patent    : {run.patent_id}")
    print(f"source    : {artifact['source']['line_count']} lines, "
          f"{artifact['source']['file']}")
    print(f"            sha256 {artifact['source']['sha256'][:16]}")
    print(f"            {sum(1 for v in run.source.pairing.values() if v == 'exact')}"
          f" Chinese lines pair one-for-one with their English, "
          f"{sum(1 for v in run.source.pairing.values() if v == 'approximate')}"
          f" had to be clamped, "
          f"{sum(1 for v in run.source.pairing.values() if v == 'none')}"
          f" have no English at all")
    print(f"gold      : {s['records']['compound']} compounds, "
          f"{s['records']['reaction']} reactions, {s['records']['pathway']} "
          f"pathways, {s['records']['patent']} patent record "
          f"= {s['records']['total']} records")
    print()

    # Which numeric fields this patent QUOTES and which it DERIVES, inferred from
    # the data. Printed so a human can sanity-check the inference rather than
    # trusting it: getting this wrong in one direction fills the queue with false
    # alarms and in the other hides real ones.
    print("numeric fields, quoted or derived (measured, not declared):")
    for name, t in artifact["summary"]["field_basis"].items():
        print(f"  {name:20} {t['matched']:4}/{t['total']:<4} printed on a cited "
              f"line   {t['basis']}")
    print()

    print(f"{s['claims']['total']} claims put to the source:")
    for v in VERDICTS:
        print(f"  {v:14} {s['claims'][v]:5}   {VERDICT_MEANING[v]}")
    print(f"  {'needs_human':14} {s['claims']['needs_human']:5}   "
          f"the review queue")
    print()
    print("the three review queues (REVIEW-PROTOCOL.md):")
    for t in TIERS:
        print(f"  tier {t}        {s['claims_by_tier'][str(t)]:5}   {TIER_MEANING[t]}")
    print(f"\n  tier 3 population by stratum, which is what a proportional sample "
          f"needs:")
    for k, v in list(s["tier3_population_by_stratum"].items()):
        print(f"    {k:52} {v:4}")
    print()
    print("severity, which is what they will find when they get there:")
    for v in SEVERITIES:
        print(f"  {v:14} {s['claims_by_severity'][v]:5}   {SEVERITY_MEANING[v]}")
    if not s["claims_by_severity"]["critical"]:
        print("  no claim states a value that is on no line of the patent: "
              "nothing here is fabricated")
    print()
    print(f"what each claim is ABOUT: {s['claims_by_subject']['extraction']} ask "
          f"whether the annotation is right,")
    print(f"                          {s['claims_by_subject']['patent']} ask "
          f"whether the PATENT is defective and we recorded that correctly")
    print()

    print(f"{s['checks']['total']} record checks:")
    for st in CHECK_STATUSES:
        print(f"  {st:14} {s['checks'][st]:5}")
    for f in FAMILIES:
        if s["checks_by_family"].get(f):
            print(f"    {f:12} {s['checks_by_family'][f]:5}   {FAMILY_MEANING[f]}")
    print()

    # This stage grading itself against the annotator who went first.
    a = run.agreement
    print("mass-and-moles arithmetic against the annotation's own flags:")
    print(f"  both flag it              {len(a['both']):4}   high confidence, the "
          f"annotator was already awake here")
    print(f"  this stage only           {len(a['machine_only']):4}   either a real "
          f"defect the annotation missed, or this check is too aggressive")
    for label in a["machine_only"]:
        print(f"      {label}")
    print(f"  the annotation only       {len(a['annotation_only']):4}   this "
          f"stage's coverage ends here")
    for label in a["annotation_only"]:
        print(f"      {label}")
    print()

    agree, disagree = getattr(run, "drawing_tally", (0, 0))
    print(f"drawn structure against gold structure: {agree} agree, "
          f"{disagree} disagree, over the names that appear in both")
    print()

    # Line coverage answers "did any record look here". Quantity coverage answers
    # "did any record take what was here", which is the stronger question and the
    # only one that can see a line cited by one record with two of its three facts
    # dropped.
    q = s["quantity_coverage"]
    print(f"quantity coverage over {q['tokens']} distinct quantities on cited lines:")
    print(f"  asserted by a claim      {q['accounted']:5}   the annotation holds it")
    print(f"  glassware, not a charge  {q['vessel']:5}   the size of the flask, "
          f"never queued")
    print(f"  schema could not hold it {q['schema_loss']:5}   the annotation read it "
          f"right and the field is too small")
    print(f"  field empty              {q['gap']:5}   the patent prints it and "
          f"nothing records it")
    if q["unmapped"]:
        print(f"  nowhere to put it        {q['unmapped']:5}   no field of that kind "
              f"on any record citing the line")
    for f in q["findings"]:
        print(f"    line {f['line']:<4} {f['printed_en']:>14}  {f['verdict']:19} "
              f"{f['field'] or 'no field'}")
        print(f"      {f['record_label_en'][:88]}")
    print()

    print(f"source coverage over {cov['total']} numbered lines:")
    print(f"  covered                  {cov['covered']:5}   at least one record "
          f"cites the line")
    print(f"  uncited, chemistry       {cov['uncited_with_chemistry']:5}   "
          f"candidate misses, each one a claim in tier 2")
    print(f"  uncited, plain           {cov['uncited_plain']:5}   nothing on the "
          f"line for a record to hold")
    if run.uncited_chemistry:
        print("  " + compact_lines(run.uncited_chemistry))
    else:
        print("  Tier 2 is a complete and EMPTY census: every line of this patent "
              "carrying a\n  quantity, a temperature, a duration, a yield, a ratio "
              "or a drawn structure is\n  cited by some record. That is a result, "
              "not a check that did not run.")
    print()

    score = artifact["completeness"]["score"]
    print(f"grounded {score['grounded_pct']}%   covered {score['covered_pct']}%   "
          f"structures {score['structure_pct']}%")
    print()

    if not check_only:
        print(f"wrote {shown(out_path)} "
              f"({out_path.stat().st_size / 1024:.0f} kB)")
    else:
        print("--check: nothing written")

    failed = [c for c in claims
              if claim_family(c) == "grounding" and c["auto"] == "not_found"]
    if not failed:
        print(f"\ngrounding gate: every checkable number and quote is on a line "
              f"its own record cites. PASS")
        return 0

    print(f"\ngrounding gate: {len(failed)} claims are NOT on the lines their own "
          f"record cites. FAIL")
    print("\n  Read these first. Each is either a value the annotation invented, "
          "or a\n  citation pointing at the wrong line. Both are defects, and only "
          "a reader\n  of the patent can say which:\n")
    for c in failed[:40]:
        print(f"    {c['record_label_en']}")
        print(f"      {c['field']} = {c['claimed_en'][:90]}")
        print(f"      {c['auto_reason_en']}")
    if len(failed) > 40:
        print(f"    ... and {len(failed) - 40} more, all in "
              f"{out_path.name} under claims[] with auto = not_found")
    print(f"\n  The full queue is claims[] in {shown(out_path)}, "
          f"ordered by tier\n  then by risk. Work tier 1 first: it is a census and "
          f"it is meant to be finished.")
    return 1


VERDICT_MEANING = {
    "found": "the value is on a line the record cites. Bulk-acceptable",
    "partial": "some of it is there. Needs a human",
    "not_found": "it is NOT there. The hallucination signal",
    "not_reconciled": "it is there, and the patent's own numbers do not agree",
    "not_checkable": "a judgement no string match can settle",
}

FAMILY_MEANING = {
    "grounding": "a number or a quote against the lines it cites",
    "reference": "a name pointing at a record that does not exist",
    "structure": "a SMILES or a formula that does not hold",
    "drawing": "the page drawing against the gold's structure for one molecule",
    "naming": "a fact the Chinese name carries that the English name drops",
    "quantity": "mass and moles against the molecular weight",
    "consistency": "the annotation against itself",
    "completeness": "something the patent states that no record holds",
    "schema_loss": "the annotation read it right and the schema cannot hold it",
}


if __name__ == "__main__":
    raise SystemExit(main())
