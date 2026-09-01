#!/usr/bin/env python3
r"""Resolve every Chinese string the gold can put on a screen to English.

CN104292137A is a Chinese patent and the gold annotation keeps its Chinese, because
the Chinese is the authoritative text: the acetone-cyanohydrin-versus-cyanoacetone
finding in FINDINGS.md was only catchable by reading the original. So the Chinese
stays. It simply must never be the only thing a reader gets, and today it often is.
The compound records carry 5 Chinese identifiers and 63 distinct Chinese aliases,
167 of the 176 provenance rows quote the patent in Chinese, and 51 of the 71 audit
findings quote it in their `quote` field. A consumer who cannot read Chinese sees a
blank where the evidence should be.

This stage builds the index that closes that gap. It is additive: no gold file and
no provenance file is touched, nothing is deleted, and the Chinese stays the key.

Resolution tiers, in order. The first one that fires wins.

    Chinese string
       |
       +-- 1. a source line this string sits on already carries
       |      a "> EN:" machine translation ..................... source_mt
       |
       +-- 2. the gold already carries an English name for this
       |      molecule, on the record itself or across
       |      provenance/compounds-equivalence.json ............. gold_alias
       |
       +-- 3. input/translations-curated.json has an entry ....... curated
       |
       +-- 4. nothing ........................................... none

TIER 1 IS OFFERED ONLY TO STRINGS THE GOLD PINS TO A SOURCE LINE, which means the
provenance `quote_zh` rows and the audit `quote` fields, never a compound identifier
or alias. The enriched source translates a PARAGRAPH, so the English it can offer a
bare compound name is a whole sentence of procedure. 27 of the 68 Chinese compound
strings do sit inside some source line, and taking that line's English for them
would answer "what does 冰水 mean" with a 60-word account of a workup. Tier 2 answers
it with "ice water". A name is resolved as a name; only a quotation is resolved as a
quotation.

TIER 1 MATCHES BY COVERING THE STRING WITH SOURCE-LINE SPANS, not by looking the
quote up on its declared lines. The quotes are not clean substrings. They elide with
" ... ", " | " and " / ", they normalise the patent's full-width punctuation to
ASCII, some are annotator prose in English with a Chinese citation embedded, and 18
of them quote text that is not on the source_lines the row itself declares. A
containment test fails on all four shapes. Covering the string greedily with the
longest span each source line can supply handles them uniformly, and reports how
much Chinese it could not place instead of quietly returning a partial answer.

TIER 2 IS DATA, NOT TRANSLATION. Most Chinese aliases are the Chinese spelling of a
molecule the gold already names in English on the very same record, so the English
is recoverable from the annotation rather than from a translator:

    identifier  hydrochloric acid
    aliases     ['盐酸', '稀盐酸', '36％HCl', '36％的盐酸', 'HCl']
                  \___ three Chinese spellings, one English name already present ___/

The join runs both ways, because 2 of the 5 Chinese identifiers carry their English
in `aliases` instead (N-溴琥珀酸亚胺 -> N-bromosuccinimide).

THE COVERAGE GATE is the point of the whole stage. It exits non-zero when a Chinese
string that CAN REACH A SCREEN has no English: any compound identifier, any alias on
a compound, any provenance `quote_zh`, any `quote` in a verification report, any run
of Chinese left inside the source's own English, and any run on a source line the
source never translated.

IT GATES ON WHAT SURVIVES SUBSTITUTION, not on whether a line has a "> EN:" partner.
Those are different questions and the second one gets line 76 wrong: line 76 is the
second line of the translation of paragraph 8, so it has no partner and needs none,
and the only Chinese in it is 环磺草酮, which the index resolves to "tembotrione". A
consumer substitutes and the reader sees English. The failure worth catching is a run
the index CANNOT replace, wherever it sits, and that is what the gate asks.

On failure the report prints the exact missing strings grouped by where they surface
and a JSON stub ready to paste into input/translations-curated.json, the way
resolve_structures.py does for SMILES.

Reads the gold, the provenance, the audits, the enriched source and the curated
table. Writes one new file. Re-running is byte-identical.

Usage:  python3 resolve_translations.py                  # defaults to CN104292137A
        python3 resolve_translations.py CN104292137A     # any patent id
        python3 resolve_translations.py --check          # resolve and report, write nothing
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# looks_like_smiles is the pipeline's one definition of "this string is a structure,
# not a name". Tier 2 needs it because compounds.json carries SMILES-identified
# records, and offering a reader "Cc1c(Cl)cccc1S(C)(=O)=O" as the English for
# 2-氯-6-甲磺酰基甲苯 is worse than offering nothing. Imported rather than re-written
# so the two stages cannot drift apart about what counts as a name.
from resolve_structures import looks_like_smiles

from pipeline_context import RUN_ROOT, shown
HERE = Path(__file__).resolve().parent
OUT = RUN_ROOT / "output"
REL = OUT / "relevant_output"
VISION = RUN_ROOT / "input" / "vision"
CURATED = RUN_ROOT / "input" / "translations-curated.json"
BIBLIO = lambda pid: RUN_ROOT / "input" / f"{pid}-biblio.json"

DEFAULT_PATENT_ID = "CN104292137A"

# The elision the provenance rows already use when a quote is stitched from parts.
# Tier 1 joins the per-line translations the same way, so a stitched quote and its
# English read with the same seams in the same places.
ELISION = " ... "

# Shortest run of source text that counts as a real match, in normalised characters.
# Below about this length a span is punctuation and a locant ("2-氯-3-") that occurs
# on twenty lines, and the cover would attribute a quote to whichever line sorted
# first rather than to the line it came from.
MIN_SPAN = 6


# ---------------------------------------------------------------- Chinese text

# Han ideographs only. Deliberately excludes the CJK punctuation block: a string of
# full-width brackets and commas carries no Chinese for a reader to be stuck on, and
# counting it as Chinese would put every ASCII-with-full-width-comma quote into a
# gate that cannot translate it into anything.
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# The patent prints full-width punctuation; the annotation quotes it back with ASCII
# punctuation about half the time, and some rows mix both inside one quote. Folding
# them together is what lets a quote be found in the line it was copied from. Applied
# to the MATCH form only, never to the key: the artifact is keyed by the exact string
# as the gold spells it, so a consumer can look up what it holds.
FULLWIDTH = str.maketrans("，。；：（）、％！？“”‘’　", ",.;:(),%!?\"\"'' ")


def has_chinese(s: str) -> bool:
    return bool(CJK.search(s))


def normalise(s: str) -> str:
    """Match form: full-width punctuation folded to ASCII, all whitespace removed."""
    return re.sub(r"\s+", "", s.translate(FULLWIDTH))


def is_english_name(s: str) -> bool:
    """True when `s` is something a reader who has no Chinese can actually read."""
    return bool(s) and not has_chinese(s) and not looks_like_smiles(s)


# ---------------------------------------------------------------- inputs

def die(msg: str) -> None:
    print(f"\nFAIL  {msg}", file=sys.stderr)
    raise SystemExit(2)


def load(name: str, *dirs: Path) -> object:
    """First existing copy of `name`, searching `dirs` in order.

    Same policy as resolve_structures.py: finalise.py writes the working copy into
    output/ and make_relevant_output.py copies it into output/relevant_output/, so
    either is a correct input and the stage runs whether or not relevant_output has
    been assembled yet.
    """
    for d in dirs:
        p = d / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    die(f"{name} not found in {', '.join(str(d) for d in dirs)}")


def load_verification() -> list[tuple[str, dict]]:
    """The A5 audit reports, newest location first. Returns (name, report) pairs."""
    for d in (REL / "verification", OUT / "stages" / "A5-verify"):
        files = sorted(d.glob("*.json")) if d.exists() else []
        if files:
            return [(f.stem, json.loads(f.read_text(encoding="utf-8"))) for f in files]
    die("no verification reports found in "
        f"{REL / 'verification'} or {OUT / 'stages' / 'A5-verify'}")


def load_inputs(patent_id: str):
    gold = REL / "gold"
    prov = REL / "provenance"
    compounds = load("compounds.json", gold, OUT)
    equivalence = load("compounds-equivalence.json", prov, OUT)
    prov_rows = (load("compounds-provenance.json", prov, OUT)
                 + load("reactions-provenance.json", prov, OUT))
    verification = load_verification()
    # For the name-fidelity gate. biblio.json is an INPUT and carries title_zh
    # beside title_en, which is the one place in this pipeline where the same
    # sentence exists in both languages and was written by different hands.
    # patent.json is DERIVED from it and may not exist yet on a cold pack, so it is
    # optional: without it the gate checks the source pair and says so.
    biblio = json.loads(BIBLIO(patent_id).read_text(encoding="utf-8")) \
        if BIBLIO(patent_id).exists() else {}
    patent_path = next((d / "patent.json" for d in (gold, OUT)
                        if (d / "patent.json").exists()), None)
    patent = (json.loads(patent_path.read_text(encoding="utf-8"))
              if patent_path is not None else None)

    if not CURATED.exists():
        die(f"{CURATED} not found. Create it with an empty 'entries' object to start.")
    curated = json.loads(CURATED.read_text(encoding="utf-8"))

    # Same reason resolve_structures.py checks it: pointing this stage at one
    # patent's gold and another patent's curated table would attach one document's
    # translations to another document's quotes, and nothing downstream would notice.
    if curated.get("patent_id") != patent_id:
        die(f"{CURATED.name} is for patent {curated.get('patent_id')!r}, "
            f"this run is {patent_id!r}")
    wrong = {c.get("patent_id") for c in compounds} - {patent_id}
    if wrong:
        die(f"gold compounds.json carries patent_id {sorted(wrong)}, "
            f"this run is {patent_id!r}")
    return compounds, equivalence, prov_rows, verification, curated, biblio, patent


# ---------------------------------------------------------------- the source text

NUMBERED = re.compile(r"^\s*(\d+) \| (.*)$")
EN_MARK = "    > EN: "


def read_numbered(patent_id: str) -> dict[int, str]:
    """line number -> line text, from input/<patent>-enriched-numbered.md.

    The numbered file is what every `source_line` and `source_lines` in the gold
    counts against, so it is the only correct place to look a line number up.
    """
    path = RUN_ROOT / "input" / f"{patent_id}-enriched-numbered.md"
    if not path.exists():
        die(f"{path} not found")
    lines = {}
    for raw in path.read_text(encoding="utf-8").split("\n"):
        m = NUMBERED.match(raw)
        if m:
            lines[int(m.group(1))] = m.group(2)
    if not lines:
        die(f"{path.name} has no numbered lines")
    return lines


def english_by_line(patent_id: str, lines: dict[int, str]):
    """The English pairing of every line, and which lines ARE that English.

    Returns (english, en_lines, walk). `english` maps a Chinese line number to the
    English the enriched source pairs with it. `en_lines` is the line numbers that
    are themselves English output, which is not a thing a regex can decide: the
    FIRST line of a translation carries "    > EN: " and every continuation line
    after it carries nothing at all, so line 76 looks exactly like a line of the
    patent. Only this walk knows the difference, and the gate needs it to tell a
    Chinese term left inside a translation apart from a line of source that was
    never translated. Those are different defects with different fixes.

    Rebuilt by walking the vision paragraphs against the file rather than by pattern
    matching the file alone, because the two cannot be told apart by eye. A paragraph
    is emitted by build_enriched.py as its Chinese lines followed by its English
    lines, and an English continuation line is just a line of text: nothing marks it.
    Guessing wrong attaches one paragraph's English to another paragraph's Chinese,
    which is a silent, plausible-looking, completely wrong translation. So the walk
    is exact and asserts itself against the file at every step, and a desync aborts.

    Where a paragraph's Chinese and English have the same number of lines the vision
    pass kept them line for line, and each line gets its own translation. Where the
    counts differ there is no line correspondence to be had, so every Chinese line of
    that paragraph gets the whole paragraph's English. Lossy upward, never wrong.
    """
    files = sorted(VISION.glob("p*.json"))
    if not files:
        die(f"no vision reads in {VISION}")
    paragraphs = [p for f in files
                  for p in (json.loads(f.read_text(encoding="utf-8")).get("paragraphs") or [])]

    # Everything build_enriched.py emits that is not a paragraph line, in the exact
    # forms it emits them, so the walk sees only paragraph content.
    body = [(n, t) for n, t in sorted(lines.items())
            if t.strip()
            and not t.startswith("# ")
            and not t.startswith("<!-- page")
            and not t.startswith("[IMAGE_EXTRACT")]

    english: dict[int, str] = {}
    en_lines: set[int] = set()
    i = 0
    no_english: list[int] = []
    aligned = unaligned = 0
    for par in paragraphs:
        # Reproduces build_enriched.py's own emit expression, `None` marker included:
        # a paragraph whose marker is JSON null really is written out as "None ...".
        zh_lines = f"{par.get('marker', '')} {par.get('zh', '')}".strip().split("\n")
        zh_numbers = []
        for text in zh_lines:
            if i >= len(body) or body[i][1] != text:
                die(f"enriched source and {VISION.name}/ have diverged at "
                    f"line {body[i][0] if i < len(body) else '?'}: expected {text[:60]!r}")
            zh_numbers.append(body[i][0])
            i += 1

        en = par.get("en")
        if not en:
            no_english.extend(zh_numbers)
            continue

        en_written = (EN_MARK + en).split("\n")
        en_text = []
        for text in en_written:
            if i >= len(body) or body[i][1] != text:
                die(f"enriched source and {VISION.name}/ have diverged at the English "
                    f"for line {zh_numbers[0]}")
            en_text.append(body[i][1][len(EN_MARK):] if body[i][1].startswith(EN_MARK)
                           else body[i][1].strip())
            en_lines.add(body[i][0])
            i += 1

        if len(en_written) == len(zh_lines):
            aligned += 1
            for n, t in zip(zh_numbers, en_text):
                english[n] = t
        else:
            unaligned += 1
            whole = " ".join(en_text)
            for n in zh_numbers:
                english[n] = whole

    if i != len(body):
        die(f"{len(body) - i} paragraph lines in the enriched source were not "
            f"accounted for by {VISION.name}/")
    return english, en_lines, {"paragraphs": len(paragraphs), "aligned": aligned,
                               "unaligned": unaligned, "no_english": sorted(no_english)}


# Lines build_enriched.py emits that no reader is ever shown as prose. The page
# markers are HTML comments and the UI prints only the page id out of them; the
# IMAGE_EXTRACT lines are the vision pass's JSON and render as drawn structures.
# Both are skipped here for that reason and for no other: skipping a line because
# its Chinese looked unimportant is how Chinese gets on a screen.
SKIP_PREFIXES = ("# ", "<!-- page", "[IMAGE_EXTRACT")


def source_runs(lines: dict[int, str], english: dict[int, str], en_lines: set[int]):
    """Every run of Chinese a reader can still meet in the source pane, by shape.

        a Chinese line the source translates ....... the reader gets the English
        a Chinese run inside that English .......... en_runs      <- must resolve
        a line with no English at all .............. bare_runs    <- must resolve

    The first needs nothing from this stage. The other two are the only two ways
    Chinese survives to a screen from the source, and both are gated the same way:
    the index must be able to replace the run. That is what makes the gate a
    statement about residual Chinese rather than about whether a "> EN:" line
    happens to exist, which is the wrong question. Line 76 is a translation whose
    only Chinese is a term the index resolves, so it is fine; a line of untranslated
    patent prose is not, and neither is a translation that kept a term the index
    has never heard of.
    """
    en_runs: dict[str, list[int]] = {}
    bare_runs: dict[str, list[int]] = {}
    for n, text in sorted(lines.items()):
        if n in english or not has_chinese(text) or text.startswith(SKIP_PREFIXES):
            continue
        bucket = en_runs if n in en_lines else bare_runs
        for run in re.findall(CJK.pattern + "+", text):
            bucket.setdefault(run, []).append(n)
    return en_runs, bare_runs


# ---------------------------------------------------------------- the universe

# Where a Chinese string surfaces. Every one of these renders, so every one gates;
# the split exists so the failure report can say WHICH screen loses its text, which
# is the difference between "fix the compound table" and "fix the evidence panel".
POPULATIONS = ["compound_identifier", "compound_alias",
               "provenance_quote", "verification_quote",
               "source_en_run", "source_bare_run", "annotator_prose"]

POPULATION_MEANING = {
    "compound_identifier": "the identifier of a gold compound record",
    "compound_alias": "an alias on a gold compound record",
    "provenance_quote": "quote_zh on a provenance row, the evidence for a record",
    "verification_quote": "quote on an A5 audit finding, the evidence for a defect",
    "source_en_run": "a Chinese term left inside the English of a translated "
                     "source line",
    "source_bare_run": "a Chinese term on a source line that carries no English",
    "annotator_prose": "a Chinese term quoted inside the annotator's English "
                       "commentary on a provenance row",
}

# The two provenance fields that are the annotator's OWN prose, written in English
# with the patent's Chinese quoted inside it:
#
#     "the prose names 浓硫酸 or 对甲苯磺酸"
#     "matches the heading name 2-氯-3-甲基-4-甲磺酰基苯甲酸"
#
# A consumer cannot look a sentence like that up as one string, so it substitutes
# instead, and this is the population that makes substitution safe. DELIBERATELY
# ONLY THESE TWO. `notes`, `procedure_text` and `molar_ratio_text` also mix the two
# languages, but what they mix in is whole verbatim sentences of the patent, whose
# English is the enriched source's job and is already on the screen beside them;
# pulling those in would turn this table into a second translation of the document.
# The gate covers what it covers, and this comment is the statement of where it stops.
PROSE_FIELDS = ("arithmetic_check", "drawing_evidence")


def substitute(text: str, keys: list[str]):
    """Replace the longest key that fits at each position; return what is left over.

    THE ORDER IS THE WHOLE POINT. 2-氯-6-甲磺酰基甲苯 is an alias the gold already
    names in English, and 氯 and 甲磺酰基甲苯 are the fragments it falls into when a
    shorter key wins. Taking the fragments and joining their English gives Chinese
    word order in Latin script: 甲磺酰基苯甲酸甲酯 comes out as "methylsulfonylbenzoic
    acid methyl ester" with the "methyl" at the wrong end of the name. Longest first
    keeps whole names whole, which is what "translate chemistry as chemistry" means
    here. `keys` must be sorted the same way the consumer sorts them, longest first,
    so the artifact and the screen agree about which name was looked up.

    Returns (matched keys in order, leftover Chinese runs).
    """
    matched: list[str] = []
    rest: list[str] = []
    i = 0
    while i < len(text):
        for k in keys:
            if text.startswith(k, i):
                matched.append(k)
                i += len(k)
                break
        else:
            rest.append(text[i])
            i += 1
    return matched, re.findall(CJK.pattern + "+", "".join(rest))


def sorted_keys(strings) -> list[str]:
    """Longest first, then lexicographic, so the cover is a function of the input."""
    return sorted(strings, key=lambda s: (-len(s), s))


def string_universe(compounds, prov_rows, verification, en_runs, bare_runs,
                    curated_keys):
    """Every distinct Chinese string the gold can render, in first-appearance order.

    Union over the four populations, never intersection: a quote that names no
    compound and a compound that is quoted nowhere are both strings a reader hits.

    `lines` is the source lines the gold ITSELF attaches to the string. Compound
    identifiers and aliases get none, because no artifact says which line a name was
    read off, and that absence is what keeps tier 1 away from them.
    """
    order: list[str] = []
    sites: dict[str, dict] = {}

    def add(text, population, lines=(), record=None):
        if not text or not has_chinese(text):
            return
        s = sites.get(text)
        if s is None:
            order.append(text)
            s = sites[text] = {"counts": {}, "lines": set(), "records": []}
        s["counts"][population] = s["counts"].get(population, 0) + 1
        s["lines"].update(n for n in lines if isinstance(n, int) and n > 0)
        if record is not None:
            s["records"].append(record)

    for idx, c in enumerate(compounds):
        add(c.get("identifier"), "compound_identifier", record=(idx, "identifier"))
        for a in c.get("aliases") or []:
            add(a, "compound_alias", record=(idx, "alias"))
    for row in prov_rows:
        add(row.get("quote_zh"), "provenance_quote", lines=row.get("source_lines") or [])
    for _, report in verification:
        for finding in report.get("findings") or []:
            line = finding.get("source_line")
            add(finding.get("quote"), "verification_quote",
                lines=[line] if isinstance(line, int) else [])

    # DELIBERATELY WITHOUT `lines`, even though the line each run sits on is known.
    # These are bare terms, and giving them a line would let tier 1 answer 环磺草酮
    # with the paragraph of procedure it appears in. A name is resolved as a name:
    # the gold's own English if it has one, otherwise the curated table. Same rule
    # as compound identifiers, for the same reason.
    for run in en_runs:
        add(run, "source_en_run")
    for run in bare_runs:
        add(run, "source_bare_run")

    # LAST, and after everything else is in, because it covers the annotator's prose
    # with the strings already in the universe and only the leftovers are new. The
    # curated keys join the cover set so that an entry hand-authored for a leftover
    # is found on the next run instead of being reported as an entry for a string
    # nothing looks up. Both the keys that matched and the runs that did not are
    # added: the matched ones because a consumer substituting them is relying on this
    # gate having checked them, the leftovers because they are the gaps.
    keys = sorted_keys(set(order) | set(curated_keys))
    for row in prov_rows:
        for field in PROSE_FIELDS:
            text = row.get(field)
            if not isinstance(text, str) or not has_chinese(text):
                continue
            matched, leftover = substitute(text, keys)
            for s in matched + leftover:
                add(s, "annotator_prose")

    for s in sites.values():
        s["lines"] = sorted(s["lines"])
    return order, sites


# ---------------------------------------------------------------- tier 1

def longest_span(text: str, start: int, line: str) -> int:
    """Length of the longest prefix of text[start:] that occurs in `line`.

    Binary search is valid because containment is monotone in length: if a substring
    is in the line then so is every prefix of it.
    """
    lo, hi = 0, len(text) - start
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if text[start:start + mid] in line:
            lo = mid
        else:
            hi = mid - 1
    return lo


def cover(text: str, declared, source_norm: dict[int, str], tighter=None):
    """Explain `text` as an ordered run of spans, each lying on one source line.

    Greedy longest match, left to right, over the lines that HAVE an English
    translation, since a line whose English we cannot borrow cannot help. Declared
    lines win ties so a quote is credited to the row's own citation wherever that
    citation is right; when it is not, the span is still found elsewhere in the
    document and the report says so rather than dropping the quote.

    `tighter` is an optional line -> rank function consulted BEFORE the declared-line
    preference, higher winning. It exists because two callers want different things
    from a tie. verify.py is asking WHERE a quote sits and must credit the row's own
    citation, so it passes nothing. source_translation is asking WHICH ENGLISH to
    borrow, and there the declared line is not automatically the right answer: see
    the note there for the eight-step heading that the Abstract also contains.
    """
    s = normalise(text)
    declared = set(declared)
    pool = sorted(source_norm)
    spans: list[tuple[int, int, int]] = []
    i = 0
    while i < len(s):
        best = None
        for n in pool:
            length = longest_span(s, i, source_norm[n])
            if length < MIN_SPAN or not CJK.search(s[i:i + length]):
                continue
            # Longest wins; then `tighter` if the caller supplied one; then a declared
            # line; then the lowest line number, so the cover is a function of the
            # inputs and nothing else.
            key = (length, tighter(n) if tighter else 0,
                   1 if n in declared else 0, -n)
            if best is None or key > best[0]:
                best = (key, n, length)
        if best is None:
            i += 1
            continue
        _, line, length = best
        spans.append((i, i + length, line))
        i += length

    covered = set()
    for a, b, _ in spans:
        covered.update(range(a, b))
    chinese = [k for k, ch in enumerate(s) if CJK.match(ch)]
    return spans, len(chinese), sum(1 for k in chinese if k not in covered)


def source_translation(text, declared, source_norm, english):
    """Tier 1: the enriched source's own English for the lines this string sits on.

    THE TIGHTEST COVERING, NOT MERELY A COVERING. A string that occurs on several
    source lines can be answered with any of their translations, and they are not
    interchangeable: 2-氯-6-甲磺酰基甲苯的合成 is printed on line 38, which is the
    Abstract and lists all eight steps, and again on lines 45, 117 and 182, which are
    the step heading on its own. The Abstract's English runs 934 characters and the
    heading's runs 58, and only one of the two is a translation of the heading. Taking
    the first covering found took the Abstract for 28 entries, at ratios up to 54x.

    So among the lines that supply the same span, the one whose English is SHORTEST
    wins. A short string answered with a long paragraph is the paragraph's translation
    and not the string's, and length is the signal that separates them. This is a rule
    rather than a threshold, so it needs no tuning and cannot be half-applied.

    It outranks the declared-line preference deliberately. The gold citing line 38 for
    a heading is not wrong, the heading really is printed there; it is simply not the
    line whose English answers the question. Attribution and translation are different
    questions and this function is only asking the second one, which is why the
    off-declared note below is computed against what the declared lines COULD have
    covered rather than against what this cover chose.
    """
    spans, total, uncovered = cover(text, declared, source_norm,
                                    tighter=lambda n: -len(english[n]))
    if not spans or uncovered == total:
        return None

    used, seen = [], set()
    for _, _, n in spans:
        if n not in seen:
            seen.add(n)
            used.append(n)
    parts, seen_text = [], set()
    for n in used:
        t = english[n]
        if t not in seen_text:
            seen_text.add(t)
            parts.append(t)

    where = ", ".join(str(n) for n in used)
    note = [f"Machine translation carried by the enriched source at line "
            f"{'s ' + where if len(used) > 1 else where}."]
    # Only spans no declared line could have supplied are a provenance defect. A span
    # a declared line covers just as well was borrowed elsewhere for its tighter
    # English, which says nothing about the gold's citation and must not be reported
    # as if it did.
    s = normalise(text)
    stranded = {n for a, b, n in spans
                if n not in set(declared)
                and not any(longest_span(s, a, source_norm[m]) >= b - a
                            for m in declared if m in source_norm)}
    off = [n for n in used if n in stranded]
    if declared and off:
        # Worth saying out loud: the string was found, but not where the gold said
        # it was. That is a provenance defect this stage can see and must not hide.
        note.append(f"Line {', '.join(str(n) for n in off)} is not among the "
                    f"source_lines the gold declares for it "
                    f"({', '.join(str(n) for n in declared)}).")
    if uncovered:
        note.append(f"{uncovered} of {total} Chinese characters in this string sit on "
                    f"no source line and are not covered by the English above.")
    return ELISION.join(parts), " ".join(note), uncovered


# ---------------------------------------------------------------- tier 2

def gold_english(records, compounds, equivalence):
    """Tier 2: the English name the gold already carries for this molecule.

    Runs both ways round the record, because the gold puts the English on whichever
    side the Chinese is not on:

        identifier English, alias Chinese   ->  the identifier is the answer
        identifier Chinese, alias English   ->  the alias is the answer

    Where several records offer several spellings, the tightest binding wins: the
    record carrying the fewest aliases is the one most specifically about this
    string, not the one that lumped four spellings together. That is what keeps 冰水
    on the record whose only alias is 冰水 ("ice water") instead of on the record that
    also answers for 水 ("water").
    """
    candidates: dict[str, tuple[int, int, str]] = {}
    for idx, role in records:
        rec = compounds[idx]
        aliases = rec.get("aliases") or []
        names = [rec.get("identifier")] if role == "alias" else list(aliases)
        for name in names:
            if not is_english_name(name or ""):
                continue
            # (aliases on the donor, length, name) is a total order, so the pick is
            # stable no matter what order compounds.json happens to be in.
            key = (len(aliases), len(name), name)
            if name not in candidates or key < candidates[name]:
                candidates[name] = key
    if not candidates:
        return None

    best = min(candidates, key=lambda n: candidates[n])

    # The equivalence index is the gold's own statement that several English
    # spellings are one substance. It cannot resolve a string on its own, but it is
    # what turns "the gold spells this three ways" from an ambiguity into a fact.
    group_of = {member: name for name, members in equivalence.items() for member in members}
    siblings: set[str] = set()
    group = group_of.get(best)
    if group:
        siblings.update(equivalence[group])
    other = sorted((set(candidates) | siblings) - {best})

    note = ["The gold already carries this molecule in English."]
    if other:
        note.append("It is spelled " + ", ".join(f"{n!r}" for n in [best] + other)
                    + " across the records.")
    if group:
        note.append(f"provenance/compounds-equivalence.json groups those spellings as "
                    f"one substance under {group!r}.")
    elif other:
        note.append("They are not in one equivalence group, so the spread is a "
                    "spelling split the gold has not indexed.")
    return best, " ".join(note)


# ---------------------------------------------------------------- tier 3

def index_curated(curated, universe: list[str]):
    """The hand-authored table, validated hard.

    This is the one hand-typed file in the stage, and every failure mode of it is
    silent: a key that matches no string resolves nothing, an English form that still
    contains Chinese has not translated anything, and a wrong chemical name reads
    exactly as convincingly as a right one. So each is an abort rather than a warning.
    """
    entries = curated.get("entries") or {}
    known = set(universe)
    table: dict[str, dict] = {}
    for key, entry in entries.items():
        if key not in known:
            die(f"curated {key!r} is not a Chinese string anywhere in the gold. "
                "Nothing would ever look it up.")
        if not isinstance(entry, dict):
            die(f"curated {key!r}: expected an object with 'en' and 'note'")
        en = entry.get("en")
        note = entry.get("note")
        if en is None and not note:
            die(f"curated {key!r}: neither an 'en' nor a 'note'. Give it a "
                "translation, or a note saying why it deliberately has none.")
        if en is not None:
            if not isinstance(en, str) or not en.strip():
                die(f"curated {key!r}: 'en' is empty. Use null plus a note to record "
                    "a gap deliberately left open.")
            if has_chinese(en):
                die(f"curated {key!r}: 'en' still contains Chinese ({en!r}). This "
                    "table is the last resort for a reader who has none; put the "
                    "Chinese in 'note' instead.")
        # OVERRIDE IS A CLAIM ABOUT THE OTHER TIERS, not a preference, so it is
        # allowed only where it can be true. The source and the gold are both
        # better provenance than we are. Two shapes so far where they are not:
        #
        #   tier 1 answers a PHRASE with the PARAGRAPH it was quoted out of,
        #     because covering a quotation with its source line is right for a
        #     quotation and wrong for a phrase spliced into somebody's sentence
        #   tier 2 answers a NAMED SOLUTION with the SUBSTANCE, because the gold
        #     record is named for the substance and the alias carries a strength,
        #     so 36％的盐酸 comes back as "hydrochloric acid" and the 36% is gone
        #
        # Both are the right rule reaching for the wrong granularity. Requiring an
        # 'en' and a 'note' keeps the reasoning attached to the decision in the
        # artifact rather than in a commit message.
        override = bool(entry.get("override"))
        if override and (en is None or not note):
            die(f"curated {key!r}: 'override' needs both an 'en' and a 'note' "
                "saying why the stronger tier is wrong for this string.")
        table[key] = {"en": en, "note": note, "override": override}
    return table


# ---------------------------------------------------------------- resolution

ORIGINS = ["source_mt", "gold_alias", "curated", "none"]

ORIGIN_MEANING = {
    "source_mt": "the enriched source already translates the line it sits on",
    "gold_alias": "the gold already names this molecule in English",
    "curated": "hand-authored in input/translations-curated.json",
    "none": "no English",
}


def resolve(universe, sites, compounds, equivalence, source_norm, english, table):
    """Run the four tiers over every string. Returns string -> the artifact entry."""
    out: dict[str, dict] = {}
    partial: list[tuple[str, int]] = []

    for text in universe:
        site = sites[text]
        curated_note = (table.get(text) or {}).get("note")
        en = origin = None
        note_bits: list[str] = []

        # Tier 3, first, but only when the entry asks for it in so many words.
        # See index_curated for the one shape that earns this: a short phrase
        # whose only other English is the translation of the whole paragraph it
        # was quoted out of. A paragraph is not a translation of a phrase, and
        # substituting one into a sentence is how "says the invention 革除了硫醚
        # 的过氧化氢氧化步骤" becomes "says the invention The beneficial effects of
        # the present invention are: ..." for 695 characters.
        if (table.get(text) or {}).get("override") and table[text].get("en"):
            en, origin = table[text]["en"], "curated"
            note_bits = ["Hand-authored, and deliberately preferred over the "
                         "source's own translation of the line: the source "
                         "translates the whole paragraph this phrase was quoted "
                         "out of, which is not a translation of the phrase."]

        # Tier 1. Only for strings the gold pins to a source line: see the module
        # docstring for why a compound name must not be answered with a sentence.
        if en is None and site["lines"]:
            got = source_translation(text, site["lines"], source_norm, english)
            if got:
                en, note, uncovered = got
                origin, note_bits = "source_mt", [note]
                if uncovered:
                    partial.append((text, uncovered))

        # Tier 2.
        if en is None and site["records"]:
            got = gold_english(site["records"], compounds, equivalence)
            if got:
                en, note = got
                origin, note_bits = "gold_alias", [note]

        # Tier 3.
        if en is None and (table.get(text) or {}).get("en"):
            en, origin = table[text]["en"], "curated"
            note_bits = ["Hand-authored: this string is named in the patent and the "
                         "gold carries no English for it."]

        if en is None:
            origin = "none"
            note_bits = ["No English. Not translated by the enriched source, not "
                         "named in English anywhere in the gold, and no entry in "
                         "input/translations-curated.json."]

        # Where it surfaces travels with the entry, because a consumer deciding
        # whether a gap matters needs to know whether it is one cell of a compound
        # table or the evidence quote under a critical audit finding.
        where = [POPULATION_MEANING[p] + (f" (x{n})" if n > 1 else "")
                 for p, n in sorted(site["counts"].items(),
                                    key=lambda kv: POPULATIONS.index(kv[0]))]
        note_bits.append("Surfaces as: " + "; ".join(where) + ".")
        out[text] = {
            "en": en,
            "origin": origin,
            "note": " ".join(x for x in note_bits + [curated_note] if x),
        }
    return out, partial


# ---------------------------------------------------------------- the gate

def gate(universe, sites, entries):
    """Which strings can reach a screen with no English, grouped by where."""
    missing: dict[str, list[str]] = {p: [] for p in POPULATIONS}
    for text in universe:
        if entries[text]["en"] is not None:
            continue
        for p in POPULATIONS:
            if p in sites[text]["counts"]:
                missing[p].append(text)
    return {p: v for p, v in missing.items() if v}


# How much longer than its Chinese an English form may be before it stops being a
# translation of that string and starts being a translation of its surroundings.
#
# MEASURED, not chosen. Over the 37 keys that are actually substituted into the
# annotator's prose the highest ratio is 10.5, 适量 against "an appropriate amount",
# and the entry this gate was written for sat at 49.6: 14 characters of Chinese
# answered with the 695-character translation of the whole paragraph it was quoted
# out of. 20 sits in the middle of that gap with room on both sides.
#
# DELIBERATELY ONLY FOR annotator_prose. 70 of the 274 entries exceed 20 and none of
# them is used in prose: they are quotations shown AS quotations, where covering the
# quote with its source line's translation is the designed and correct answer. The
# defect is not a long English form, it is a long English form spliced into the
# middle of somebody's sentence.
MAX_PROSE_RATIO = 20


def prose_ratio_gate(universe, sites, entries):
    """Entries that a consumer substitutes into prose but that answer a paragraph.

    Tier 1 covers a quotation with the translation of the source line it sits on,
    which is right for a quotation and wrong for a phrase quoted inside somebody
    else's English sentence. Both surfaces share one entry, so the artifact cannot
    be right for both, and the ratio is what tells them apart. On failure the fix is
    a curated entry with "override": true, which beats tier 1 and carries its own
    reasoning.

    Nothing here is about Chinese. Every string this catches produces output with no
    Chinese character in it at all, which is why the coverage gate above passes it
    and why a consumer's own CJK check passes it too.
    """
    bad = []
    for text in universe:
        if "annotator_prose" not in sites[text]["counts"]:
            continue
        en = entries[text]["en"]
        if not en:
            continue
        ratio = len(en) / len(text)
        if ratio > MAX_PROSE_RATIO:
            bad.append((text, ratio, en))
    return bad


# A percent sign, in both widths. The patent writes 36％ and 36%.
PERCENT = ("％", "%")

# Chinese modifiers that change WHAT WAS CHARGED rather than describing it, with the
# English that has to survive. Every one of these is a fact a chemist would act on:
# wet aluminium trichloride hydrolyses and will not catalyse a Friedel-Crafts,
# saturated sodium bicarbonate is a workup and solid sodium bicarbonate is not, and
# dilute hydrochloric acid is not concentrated hydrochloric acid.
#
# APPLIED ONLY TO gold_alias ENTRIES, which are NAMES. 浓 also opens 浓缩, "to
# concentrate", the verb that starts a dozen procedure quotations, and those resolve
# through source_mt to a whole paragraph where a prefix test means nothing. Scoping
# to names is what keeps this rule at four hits instead of twenty.
# The VALUE is every English rendering that counts as carrying the qualifier, because
# one Chinese modifier does not always come out as one English word. 冰 is the case
# that forced this: 冰水 is ice water, but 冰醋酸 is glacial acetic acid, and demanding
# the literal "ice" called a correct name a defect. Measured over every run in this
# repo, 冰 occurs twice, and this turns one false positive into a pass while leaving
# the true one failing.
QUALIFIERS = {
    "无水": ("anhydrous",),
    "饱和": ("saturated",),
    "稀": ("dilute",),
    "浓": ("concentrated",),
    "冰": ("ice", "glacial"),
}


def name_fidelity_gate(entries, biblio, patent, keys):
    """Where the gold's own English disagrees with this index about a molecule.

    THE GAP THIS CLOSES. Everything above asks whether a Chinese string HAS an
    English form. Nothing asked whether the English the gold already carries AGREES
    with it. That is how gold/patent.json shipped the title "Process for
    synthesizing triketone herbicide cyclic sulcotrione" through nine agents, a
    verification engine, a completeness report and a self-contained export, while
    the same file's own patent_summary says the structure the route builds is
    tembotrione, and while this index resolves 环磺草酮 to tembotrione from the
    gold's own alias data. Sulcotrione is a real and different herbicide. The first
    line of the deliverable named a molecule the route does not make.

    DELIBERATELY NARROW, AND IT REPORTS RATHER THAN REWRITES. Forcing every English
    string to be what substitution would produce is wrong: human-written prose
    legitimately paraphrases, and the gold's English is often better than a
    substitution would be. So this asks only two questions, each on a pairing where
    the two languages are genuinely saying the same thing, and each measured to
    produce no false positives on this patent.

    1. A NAME THAT LOSES A CONCENTRATION. `36％的盐酸` resolves through gold_alias to
       "hydrochloric acid", which is the right substance and the wrong strength, and
       `15％的次氯酸钠溶液` to "sodium hypochlorite" the same way. A concentration is a
       fact, and a translation that drops it has changed what was charged.

       The same shape without a number: 无水三氯化铝 is ANHYDROUS aluminium
       trichloride and resolves to "aluminium trichloride", 饱和碳酸氢钠 is SATURATED
       sodium bicarbonate and resolves to "sodium bicarbonate", 稀盐酸 is DILUTE
       hydrochloric acid and resolves to "hydrochloric acid". Wet aluminium
       trichloride will not catalyse a Friedel-Crafts. In three of those four the
       gold's own record already carries the fuller English, so the fact was never
       missing from the annotation, only from the index.

       Scoped to PERCENT SIGNS and not to digits generally, because a systematic
       name is full of digits that a common name correctly discards:
       2-(2-氯4-甲磺酰基-3-[(2,2,2-三氟乙氧基)甲基]苯甲酰基)环己烷-1,3-二酮 resolves to
       "tembotrione" and drops nine locants, and that is not a defect. A locant is
       not a quantity. Measured over this gold: the percent rule catches 2 and the
       digit rule would catch 3, the third being that name.

    2. A TITLE THAT NAMES NO MOLECULE ITS OWN CHINESE NAMES. biblio.json holds
       title_zh beside title_en, so substituting the index into the Chinese says
       which molecules the title is about and the English can be checked against
       that list. gold/patent.json's copy is checked against the same Chinese, so a
       title that drifted in derivation fails too.

       IT ASKS FOR AGREEMENT, NOT FOR EQUALITY. "A process for making tembotrione,
       a triketone herbicide, in eight steps" passes: an English title may be
       phrased any way at all as long as it does not name a molecule the Chinese
       does not. Only naming NONE of them fails, which is what
       "Process for synthesizing triketone herbicide cyclic sulcotrione" did.
    """
    dropped = []
    for text, entry in entries.items():
        if entry["origin"] != "gold_alias" or not entry["en"]:
            continue
        english = entry["en"].lower()
        if any(p in text for p in PERCENT) and not any(p in entry["en"] for p in PERCENT):
            dropped.append((text, entry["en"], "a strength"))
            continue
        for zh, words in QUALIFIERS.items():
            if text.startswith(zh) and not any(w in english for w in words):
                dropped.append((text, entry["en"], f"{zh!r}, {' or '.join(words)}"))
                break

    # THE PAIRS, DECLARED RATHER THAN DISCOVERED. Each is a place where the same
    # sentence exists in both languages, written by different hands, so the two can
    # be compared without assuming either is a translation of the other word for
    # word. input/<pid>-biblio.json is the source of the title and holds title_zh
    # beside title_en; gold/patent.json holds the copy derived from it. Checking
    # both catches a wrong title AND a title that drifted in derivation.
    title_zh = (biblio or {}).get("title_zh") or ""
    pairs = [("biblio title_en", (biblio or {}).get("title_en") or "")]
    if patent is not None:
        pairs.append(("gold patent.json title", patent.get("title") or ""))

    molecules = set()
    i = 0
    while i < len(title_zh):
        hit = next((k for k in keys if title_zh.startswith(k, i)), None)
        if hit is None:
            i += 1
            continue
        # gold_alias only: those are the entries where the gold itself is naming a
        # molecule, which is what a title can be expected to agree with.
        if entries[hit]["origin"] == "gold_alias":
            molecules.add(entries[hit]["en"])
        i += len(hit)

    disagreements = []
    if molecules:
        for label, english in pairs:
            if english and not any(m.lower() in english.lower() for m in molecules):
                disagreements.append((label, english, sorted(molecules)))
    return dropped, disagreements


def unresolved_lines(en_runs, bare_runs, entries):
    """Source lines the index cannot clear of Chinese, line -> the runs it leaves.

    THE GATE IS ABOUT RESIDUAL CHINESE, NOT ABOUT PAIRING. An earlier version asked
    whether a line carried a "> EN:" partner and failed line 76 for having none.
    Line 76 IS English; it is the second line of the translation of paragraph 8,
    and its only Chinese is 环磺草酮, which the index resolves to "tembotrione". A
    consumer substitutes and the reader sees English, so there is nothing wrong with
    it. What is wrong is a run the index cannot replace, wherever it sits, because
    that is the case where substitution leaves Chinese on the screen. This asks that
    question and only that question, so nothing is excused and nothing is invented.
    """
    bad: dict[int, set[str]] = {}
    for runs in (en_runs, bare_runs):
        for run, numbers in runs.items():
            if (entries.get(run) or {}).get("en"):
                continue
            for n in numbers:
                bad.setdefault(n, set()).add(run)
    return {n: sorted(bad[n]) for n in sorted(bad)}


def untranslated_no_loss(lines: dict[int, str], english: dict[int, str],
                         en_lines: set[int]):
    """Lines with no English that carry no Chinese either, so nothing is lost.

    Reported and deliberately not gated. These are the bare paragraph markers a
    drawing hangs under, and lines of NMR shifts that read the same in both
    languages. Counted out loud so that "no failures" is visibly a statement about
    every line rather than about the lines this stage chose to look at.
    """
    return [n for n, text in sorted(lines.items())
            if n not in english and n not in en_lines and text.strip()
            and not text.startswith(SKIP_PREFIXES) and not has_chinese(text)]


def stub(missing) -> str:
    """A ready-to-paste block for input/translations-curated.json."""
    flat = []
    for p in POPULATIONS:
        for text in missing.get(p, []):
            if text not in [t for t, _ in flat]:
                flat.append((text, p))
    lines = ['  "entries": {']
    for i, (text, population) in enumerate(flat):
        tail = "" if i == len(flat) - 1 else ","
        lines.append(f"    {json.dumps(text, ensure_ascii=False)}: {{")
        lines.append('      "en": "",')
        lines.append(f'      "note": "{POPULATION_MEANING[population]}. Translated as '
                     'chemistry against the structure or the context in the patent, '
                     'not word by word."')
        lines.append(f"    }}{tail}")
    lines.append("  }")
    return "\n".join(lines)


# ---------------------------------------------------------------- report

def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    patent_id = args[0] if args else DEFAULT_PATENT_ID

    (compounds, equivalence, prov_rows, verification, curated,
     biblio, patent) = load_inputs(patent_id)
    lines = read_numbered(patent_id)
    english, en_lines, walk = english_by_line(patent_id, lines)
    source_norm = {n: normalise(lines[n]) for n in english if normalise(lines[n])}
    en_runs, bare_runs = source_runs(lines, english, en_lines)

    universe, sites = string_universe(compounds, prov_rows, verification,
                                      en_runs, bare_runs,
                                      (curated.get("entries") or {}).keys())
    table = index_curated(curated, universe)
    entries, partial = resolve(universe, sites, compounds, equivalence,
                               source_norm, english, table)

    artifact = OUT / "translations.json"
    if not check:
        artifact.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    missing = gate(universe, sites, entries)
    stranded = unresolved_lines(en_runs, bare_runs, entries)
    harmless = untranslated_no_loss(lines, english, en_lines)

    # ---- report -------------------------------------------------------------
    print(f"patent    : {patent_id}")
    print(f"source    : {len(lines)} lines, {walk['paragraphs']} paragraphs, "
          f"{len(english)} lines carry an English pairing")
    print(f"            {walk['aligned']} paragraphs translate line for line, "
          f"{walk['unaligned']} translate as a block")
    print(f"curated   : {len(table)} entries")
    print()

    counts = {p: sum(1 for t in universe if p in sites[t]['counts']) for p in POPULATIONS}
    print(f"{len(universe)} distinct Chinese strings that can reach a screen:")
    for p in POPULATIONS:
        print(f"  {p:20} {counts[p]:4}   {POPULATION_MEANING[p]}")
    print()

    by_origin = {o: [t for t in universe if entries[t]["origin"] == o] for o in ORIGINS}
    print("resolved by tier:")
    for o in ORIGINS:
        print(f"  {o:12} {len(by_origin[o]):4}   {ORIGIN_MEANING[o]}")

    # Tier 2 is the interesting number: it is how much of this was already in the
    # data and needed no translator at all.
    gold_strings = [t for t in universe if sites[t]["records"]]
    from_gold = [t for t in gold_strings if entries[t]["origin"] == "gold_alias"]
    print(f"\n  {len(from_gold)}/{len(gold_strings)} Chinese compound identifiers and "
          f"aliases resolve from the gold's own data")
    if partial:
        print(f"  {len(partial)} quotations are only partly covered by their source "
              f"lines; each says so in its note")

    # A hand-authored translation that a stronger tier overrode is fine, and its note
    # still travels. A hand-authored translation that DISAGREES with the gold's own
    # English for the same molecule is not fine: one of the two is wrong and neither
    # is visible from the artifact, so it is called out here.
    forced = [k for k, v in table.items() if v.get("override")]
    if forced:
        print(f"\n  {len(forced)} curated entries were preferred OVER a stronger "
              f"tier, which is\n  allowed only where that tier answers the wrong "
              f"question. Each note says which:")
        for key in forced:
            print(f"    {key}  ->  {entries[key]['en'][:60]!r}")

    overridden = [(k, v["en"], entries[k]["en"]) for k, v in table.items()
                  if v.get("en") and not v.get("override")
                  and entries[k]["origin"] != "curated"]
    if overridden:
        print(f"\n  {len(overridden)} curated entries were overridden by a stronger "
              f"tier; their notes still travel:")
        for key, hand, won in overridden:
            verdict = "agrees" if hand == won else f"DISAGREES, {hand!r} was not used"
            print(f"    {key}  ->  {won!r} via {entries[key]['origin']}  ({verdict})")
    if not check:
        print(f"\nwrote {shown(artifact)} "
              f"({len(entries)} entries, keyed by the exact Chinese string)")
    else:
        print("\n--check: nothing written")

    print(f"\nsource pane: {len(en_runs)} distinct Chinese runs sit inside the "
          f"English of a translated line, {len(bare_runs)} on lines with no English")
    for label, runs in (("in the English", en_runs), ("no English", bare_runs)):
        for r, ns in sorted(runs.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            mark = (entries.get(r) or {}).get("en") or "NOT IN THE INDEX"
            print(f"  {r}  x{len(ns)}  {label}, line {ns[0]}  -> {mark}")
    if harmless:
        print(f"  {len(harmless)} lines have no English and no Chinese either, so "
              f"nothing is lost: {', '.join(str(n) for n in harmless)}")

    dropped, title_gaps = name_fidelity_gate(entries, biblio, patent,
                                             sorted_keys(entries))
    print(f"\nname fidelity gate: where the gold's own English disagrees with this "
          f"index\n  about a molecule. Reports, never rewrites.")
    if not dropped and not title_gaps:
        print("  the gold's names and this index agree. PASS")
    else:
        for text, en, what in dropped:
            print(f"  a name loses {what}: {text}  ->  {en!r}")
            print(f"      The substance is right and the qualifier is gone, and the "
                  f"qualifier is a fact\n      about what was charged.")
        for label, english, molecules in title_gaps:
            print(f"  {label} names no molecule its own Chinese names.")
            print(f"      english  : {english}")
            print(f"      chinese  : names {', '.join(molecules)}")
            print(f"      The English contradicts the Chinese it is a title for. Fix "
                  f"it where the\n      title is written, not here: this stage "
                  f"reports the disagreement and never\n      edits the gold.")
        print("  FAIL")

    oversized = prose_ratio_gate(universe, sites, entries)
    print(f"\nprose ratio gate: an entry a consumer splices into the annotator's own "
          f"English\n  must translate its own string, not the paragraph around it. "
          f"Limit {MAX_PROSE_RATIO}x its length.")
    if not oversized:
        print(f"  all {sum(1 for t in universe if 'annotator_prose' in sites[t]['counts'])} "
              f"entries used in prose are within it. PASS")
    else:
        print(f"  {len(oversized)} entries answer a phrase with a paragraph. FAIL")
        for text, ratio, en in oversized:
            print(f"    {text}  {len(text)}zh -> {len(en)}en, {ratio:.1f}x")
            print(f"      currently: {en[:90]}...")
        print("\n  Give each one a curated entry with \"override\": true, translating "
              "the phrase\n  as a phrase. See the note on 革除了硫醚的过氧化氢氧化步骤 for "
              "the worked example.")

    print(f"\ncoverage gate: every one of the {len(universe)} strings above must have "
          f"an English form, so that substituting the index leaves no Chinese anywhere")
    if not missing and not stranded:
        print(f"  all {len(universe)} strings resolve, and all {len(lines)} source "
              f"lines come out of the substitution in English. PASS")
        return 1 if (oversized or dropped or title_gaps) else 0

    total = len({t for v in missing.values() for t in v})
    print(f"\n  {total} strings have NO English, leaving Chinese on "
          f"{len(stranded)} source lines. FAIL")
    for p in POPULATIONS:
        if p in missing:
            print(f"\n    {p} ({len(missing[p])}) - {POPULATION_MEANING[p]}")
            for text in missing[p]:
                print(f"      {text}")
    for n, runs in stranded.items():
        print(f"\n    source line {n} still reads as Chinese after substitution "
              f"({', '.join(runs)}):")
        print(f"      {lines[n][:120]}")
    if missing:
        print("\n  Translate them as chemistry, checking each name against the "
              "structure or")
        print("  the context in the patent rather than word by word, and merge this "
              f"into\n  {shown(CURATED)}:\n")
        print(stub(missing))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
