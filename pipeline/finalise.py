#!/usr/bin/env python3
"""Turn the raw A0-A4 pass outputs into production-shaped artifacts.

The prompts deliberately do NOT ask the model for ids, UUIDs or the patent rollup.
Those are deterministic functions of the extracted content, and asking a language
model to compute them only introduces a way for the join keys to be wrong. This
script reproduces exactly what PersistentRecordBuilder / PatentRecordBuilder do in
literatureiq-engine, so the gold artifacts key-join with production output.

Java equivalence notes
----------------------
HashUtil.getUUID5 uses com.fasterxml.uuid Generators.nameBasedGenerator(
NAMESPACE_DNS), which is SHA-1 based (UUID v5) over the DNS namespace. Python's
uuid.uuid5(uuid.NAMESPACE_DNS, s) is the same construction. Verify against one
real production artifact before joining on uuid in anger - it has not been
checked against a live record, only against the source of both implementations.

Usage:  python3 finalise.py                       # reads output/raw-*, writes output/*.json
        python3 finalise.py --patent-id CN1234A   # any patent id
        python3 finalise.py --check               # validate only, write nothing

The patent id is load-bearing here in a way it is nowhere else: every id and every
UUID in every artifact is seeded with it. It used to be a module constant, so a run
on a second patent silently minted the first patent's join keys over the second
patent's chemistry, and nothing downstream could tell.
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

from pipeline_context import ContextError, RUN_ROOT, biblio_path, resolve_patent_id

HERE = Path(__file__).resolve().parent
OUT = RUN_ROOT / "output"

# Set by main() before any id is built. Kept as module state rather than threaded
# through twenty call sites, because every builder below is a pure function of it.
PATENT_ID: str = ""
BIBLIO: Path = Path()


# ---------------------------------------------------------------- id builders

def uuid5(s: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


def short_hash(s: str) -> str:
    """First 8 hex chars of the UUID5 - PersistentRecordBuilder.shortHash."""
    return uuid5(s).replace("-", "")[:8]


def sanitize_key(k: str) -> str:
    """Azure Search rejects '.', '/', '\\' in a document key, and rejects the whole
    batch when one document has a bad one. PersistentRecordBuilder.sanitizeKey."""
    return re.sub(r"[./\\]", "_", k)


def build_compound_id(identifier: str) -> str:
    needs_hash = len(identifier) > 80 or bool(re.search(r"[./\\]", identifier))
    base = identifier[:80]
    return sanitize_key(f"{PATENT_ID}_{base}" + (f"_{short_hash(identifier)}" if needs_hash else ""))


def normalize_reaction_id(rid: str | None) -> str | None:
    """Collapse whitespace/underscore runs so re-runs upsert instead of duplicating."""
    if rid is None:
        return None
    return re.sub(r"[\s_]+", "_", rid.strip()).strip("_")


def build_reaction_id(rid, section_label, step_label, step_index) -> str:
    norm = normalize_reaction_id(rid)
    if norm:
        return sanitize_key(f"{PATENT_ID}_{norm}")
    part = lambda s: re.sub(r"[\s_]+", "_", (s or "").strip()).strip("_") or "na"
    return sanitize_key(f"{PATENT_ID}_{part(section_label)}_{part(step_label)}_"
                        f"{'na' if step_index is None else step_index}")



# ============================================================
# Vocabulary normalisation
# ============================================================

# The A2 pass emitted three role values that are not in CompoundRecord's enum.
# They are recognisable and unambiguous, so they are mapped rather than dropped,
# but every substitution is logged: a gold set that silently rewrites its own
# extraction output is not a record of anything.
#
#   quench       water quenching a Lewis-acid reaction is not the reaction solvent
#                and not a reagent that transforms the substrate -> "other".
#                Hydrochloric acid quenching AND acidifying is an "acid".
#   wash         a wash liquid is functioning as a solvent -> "solvent".
#   intermediate not a role at all, it is a compound_class. Every occurrence has
#                is_product false and sits inside a step whose second
#                transformation consumes it, so it is that transformation's
#                reactant -> "reactant". The intermediate-ness is preserved as a
#                compound_class tag, which is where production puts it.
VALID_ROLES = {"product", "reactant", "reagent", "solvent", "catalyst", "ligand",
               "base", "acid", "oxidant", "reductant", "by_product", "additive",
               "drying_agent", "other"}

ROLE_FIXES: list[str] = []


def normalise_role(role, identifier, reaction_id):
    if role is None or role in VALID_ROLES:
        return role
    if role == "quench":
        new = "acid" if "acid" in (identifier or "").lower() else "other"
    elif role == "wash":
        new = "solvent"
    elif role == "intermediate":
        new = "reactant"
    else:
        new = "other"
    ROLE_FIXES.append(f"{reaction_id}: {identifier[:44]!r} role {role!r} -> {new!r}")
    return new



# ============================================================
# Cross-section identifier equivalence
# ============================================================

def equivalence_index(mols):
    """Group compound records that are the same molecule under different spellings.

    A1 runs per section with no shared vocabulary, so the same intermediate comes out
    as "2-chloro-6-(methanesulfonyl)toluene" in one section, "...(methylsulfonyl)..."
    in another and "...methylsulfonyl..." unparenthesised in a third. Eight molecules
    in this patent are carried under three spellings each.

    These are deliberately NOT merged. buildCompoundId is a pure function of the
    identifier string, so production would emit three separate CompoundRecords for
    these too; collapsing them here would make the gold set disagree with production
    for a reason that has nothing to do with extraction quality. Instead the
    equivalence is written out explicitly, so a benchmark can join on it and so the
    fragmentation is visible rather than latent.

    The key is structural-ish and deliberately crude: it exists to surface the
    problem, not to be a naming authority.
    """
    groups = {}
    for m in mols:
        ident = m["identifier"]
        t = ident.lower()
        for a, b in (("methanesulphonyl", "ms"), ("methanesulfonyl", "ms"),
                     ("methylsulfonyl", "ms"), ("bromomethyl", "brmet")):
            t = t.replace(a, b)
        t = re.sub(r"[\s()\[\],'-]", "", t)
        t = re.sub(r"(benzoate|benzoicacid)", "bz", t)
        groups.setdefault(t, []).append(ident)
    return {k: sorted(set(v)) for k, v in groups.items() if len(set(v)) > 1}


# ---------------------------------------------------------------- passes

def load_raw(name):
    p = OUT / f"raw-{name}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


# Fields where a later section's populated value wins over an earlier null, and
# fields that are unioned. Transcribed from PersistentRecordBuilder.mergeCompoundFields.
_UNION = ("aliases", "tags", "analytics")
_KEEP_FIRST = ("id", "patent_id", "identifier")


def populated(v) -> bool:
    """Whether a value carries information, looking INSIDE a nested object.

    THE BUG THIS FIXES. The scalar rule below used to read
    `v not in (None, "", [], {})`. `quantity` is a nested object, and one whose every
    member is null is not literally `{}`, so it passed that test and REPLACED a
    populated one. A1 runs per section, most sections print no numbers, and whichever
    section merges last wins, so a section with nothing in it overwrote the section
    that had everything.

    Measured on CN106008290A before the fix: `tembotrione` is read with a mass, a
    yield and a purity in all five examples, and reached the deliverable as
    mass_g null, yield_pct null, section_label "Technical Field". Five product masses
    and five yields, correctly extracted, were absent from the gold. `purity_pct`
    survived only because it is a top level scalar rather than a member of the dict.
    The reference run has the same hole: `tembotrione` there has seven raw section
    rows, one of them carrying a mass, and mass_g null in its finalised record.

    It is a silent loss of the kind CLAUDE.md is about. Nothing failed, every record
    validated, and the numbers were simply gone. It also inflated the review census
    past its pinned budget, because the sweep then asked a reviewer about every
    printed quantity "the annotation does not record anywhere" for quantities the
    annotation did record.

    WHY NOT MERGE THE MEMBERS FIELD BY FIELD. That would restore the numbers too, and
    it would let a mass from Example 1 sit beside a yield from Example 3, asserting a
    pair no example printed. A quantity block has to stay internally consistent, so
    the whole block still moves as one unit. All that changes is that a block with
    nothing in it no longer counts as something.
    """
    if isinstance(v, dict):
        return any(populated(x) for x in v.values())
    if isinstance(v, (list, tuple)):
        return any(populated(x) for x in v)
    return v not in (None, "", [], {})


def merge_compound(existing, incoming):
    """Merge two extractions of the same compound from different sections.

    A1 runs per section, so the same solvent is extracted independently in Claims,
    Summary and Example 1. Production has the same shape and resolves it in
    PersistentRecordBuilder.mergeCompoundFields, because buildCompoundId is a pure
    function of the identifier and duplicates would otherwise collide in the store.
    Semantics copied from there: incoming wins on a populated scalar, lists are
    unioned, is_section_product is a logical OR, and identity fields never change.

    "Populated" is decided by populated() above, which looks inside a nested object.
    Read its docstring before changing this: the naive test dropped five product
    masses on the floor.
    """
    out = dict(existing)
    for k, v in incoming.items():
        if k in _KEEP_FIRST:
            continue
        if k == "is_section_product":
            out[k] = bool(existing.get(k)) or bool(v)
        elif k in _UNION:
            a = existing.get(k) or []
            b = v or []
            seen, merged = set(), []
            for x in a + b:
                key = json.dumps(x, sort_keys=True, ensure_ascii=False) if isinstance(x, (dict, list)) else x
                if key not in seen:
                    seen.add(key)
                    merged.append(x)
            out[k] = merged
        elif k == "notes":
            notes = [n for n in (existing.get("notes"), v) if n]
            # keep both section's observations rather than letting one overwrite
            out[k] = " | ".join(dict.fromkeys(notes)) or None
        elif populated(v):
            out[k] = v
    # record every section the compound was seen in - production keeps only the last
    secs = list(dict.fromkeys(
        (existing.get("seen_in_sections") or [existing.get("section_label")])
        + [incoming.get("section_label")]))
    out["seen_in_sections"] = [x for x in secs if x]
    return out


def finalise_compounds(mols):
    by_ident = {}
    order = []
    for m in mols:
        ident = m["identifier"]
        m["patent_id"] = PATENT_ID
        m["id"] = build_compound_id(ident)
        m["compound_uuid"] = uuid5(f"{PATENT_ID}::{ident}")
        if ident in by_ident:
            by_ident[ident] = merge_compound(by_ident[ident], m)
        else:
            by_ident[ident] = m
            order.append(ident)
    merged = [by_ident[i] for i in order]
    print(f"compounds : {len(mols)} extracted across sections -> {len(merged)} unique "
          f"after merge ({len(mols) - len(merged)} duplicates resolved)")
    return merged


def finalise_reactions(rxns):
    for r in rxns:
        for c in r.get("compounds") or []:
            c["role"] = normalise_role(c.get("role"), c.get("identifier", ""),
                                       r.get("reaction_id", "?"))
        rid = r.get("reaction_id")
        r["id"] = build_reaction_id(rid, r.get("section_label"),
                                    r.get("step_label"), r.get("step_index"))
        norm = normalize_reaction_id(rid)
        r["reaction_uuid"] = uuid5(f"{PATENT_ID}::{norm}") if norm else uuid5(r["id"])
        r["patent_id"] = PATENT_ID
    return rxns


def finalise_pathways(pws, mols, rxns):
    by_ident = {m["identifier"]: m for m in mols}
    by_rid = {r["reaction_id"]: r for r in rxns}

    def fill_ref(ref):
        if not ref:
            return ref
        c = by_ident.get(ref.get("identifier"))
        if c:
            ref["compound_uuid"] = c["compound_uuid"]
            ref["smiles"] = c.get("smiles")
        return ref

    for p in pws:
        p["patent_id"] = PATENT_ID
        fill_ref(p.get("ksm"))
        fill_ref(p.get("product"))
        for i in p.get("intermediates") or []:
            fill_ref(i)
        for s in p.get("steps") or []:
            r = by_rid.get(s.get("reaction_id"))
            if r:
                s["reaction_uuid"] = r["reaction_uuid"]
        # PathwaysBuilder.buildPathway, not the PathwayRecord javadoc.
        #
        # The javadoc says the seed is (patent_id, scope, ksm_id, product_id). The
        # code says otherwise, and carries a comment explaining why: that seed
        # collapses every route sharing endpoints onto ONE uuid, and they then
        # overwrite each other on upload. Production measured the damage at 20
        # distinct routes lost across a ten-patent set. The fix was to fold the
        # ordered step signature into the seed unconditionally.
        #
        # The A5 audit caught us reproducing the javadoc version: three of our five
        # pathways came out with the same uuid, because Claims, Example 1 and the
        # Summary prose route all run 2-chlorotoluene to tembotrione.
        def safe_id(ref):
            ref = ref or {}
            return ref.get("compound_uuid") or ref.get("identifier") or "?"

        sig = "".join(f"{s.get('reaction_uuid') or s.get('reaction_id')}>"
                      for s in p.get("steps") or [])
        p["pathway_uuid"] = uuid5(f"{PATENT_ID}::{p.get('scope')}::"
                                  f"{safe_id(p.get('ksm'))}::{safe_id(p.get('product'))}::{sig}")
    return pws


def pathway_section_type(p: dict) -> str:
    """Which kind of section a pathway came from.

    The pathway record carries only `section_label`; the type it needs is on its
    steps, which are projections of reactions and do carry `section_type`.
    """
    for s in p.get("steps") or []:
        t = s.get("section_type")
        if t:
            return t
    return ""


# Sections that describe somebody ELSE'S chemistry. A route recited in the
# background is prior art by definition, and A0's own rule says so.
#
# A comparative example is deliberately NOT here. That is the applicant's own
# experiment, run at the conditions they are arguing against and reported as their
# own data, so it belongs to this patent in a way a cited competitor's route does
# not.
NOT_THIS_PATENTS_CHEMISTRY = {"background"}


# ONE VOCABULARY, NOT TWO. THERE IS NOTHING TO TRANSLATE HERE ANY MORE.
#
# The two schemas used to define different vocabularies for the same field, and
# only university, individual and government were in both:
#
#   biblio  : company university individual institute government hospital foundation
#   record  : multinational_corp sme university government individual consortium
#
# Two branches fixed that at once and both landed. One added a map here from the
# biblio's words to the record's. The other changed biblio.schema.json's enum to
# BE the record's words. Together they left a map standing between two sides that
# already agreed, and a map that no longer recognises the values it is handed:
# multinational_corp and consortium are not keys, so both fell through the default
# to sme. A biblio saying "this is a multinational" produced a record saying "this
# is a small company", silently, and only for the two values a person is most
# likely to reach for.
#
# The map is gone. biblio.schema.json's own comment already says the value is
# copied straight into the record with no mapping; that is now true. An unknown
# value fails validate.py loudly instead of becoming sme quietly, which is the
# behaviour this repo asks for: a guard that passes on absence is worse than none.


def tag_slug(name: str) -> str:
    """An assignee name as a tag value the schema will accept.

    The pattern is `^[a-z_]+:[a-z0-9_/.+-]+$`, so a comma is not allowed. This was
    `name.lower().replace(" ", "_")`, which is enough for "Wuhan Institute of
    Technology" and not for "Zhejiang Zhongshan Chemical Industry Group Co., Ltd.":
    the commas and the full stops survived and the record failed validation on the
    second patent this pack ever saw.

    Everything outside the allowed set becomes an underscore, runs collapse, and
    the ends are trimmed, so the tag stays readable rather than escaped.
    """
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return slug or "unknown"


def rollup(mols, rxns, pws):
    """PatentRecord.ExtractionRollup, computed not asked for.

    THE "BEST" AND "KEY" FIELDS ARE ABOUT THIS PATENT, SO PRIOR ART IS EXCLUDED.
    Both used to be computed over everything annotated. On a patent whose
    background recites competitors' routes, that made `best_overall_yield_pct`
    report 75.2 for CN109678767A: the yield of the Heilongjiang University NBS
    route, which the background quotes only in order to criticise it, against the
    invention's own best of 69.88. `key_starting_materials` likewise listed three
    feedstocks belonging to routes this patent argues against.

    It was invisible on the reference run for one reason: its A0 marked the
    background as carrying no procedures, so it produced no background pathways
    and no background starting materials, and the max happened to be right. The
    counts are 0 and 0 there, so this exclusion cannot change it.

    A wrong number here is the worst kind available: `best_overall_yield_pct` is
    exactly the field that gets read out of the artifact and put on a slide, and
    a competitor's yield reported as this patent's is not a defect anyone would
    catch downstream.
    """
    from collections import Counter
    sec = Counter(r.get("section_type") or "unknown" for r in rxns)
    scale = Counter(r.get("scale") or "not_specified" for r in rxns)
    # chemistry_focus must describe THIS patent's chemistry, so the same filter the
    # yield and the starting materials already get applies here too. Found by the A5
    # patent audit on WO2022024094A1: that run's rollup named `halogenation`, on the
    # strength of one background reaction, the NMSBA to acid-chloride step recited from
    # US 7,820,863 which is precisely the step the invention exists to avoid. The
    # reference run could not expose this because its A0 marked its background as
    # carrying no procedures, so it has zero background reactions and the counter had
    # nothing foreign to pick up.
    cls = Counter(r.get("reaction_class") or "other" for r in rxns
                  if (r.get("section_type") or "") not in NOT_THIS_PATENTS_CHEMISTRY)
    ours = [p for p in pws
            if pathway_section_type(p) not in NOT_THIS_PATENTS_CHEMISTRY]
    best = max((p for p in ours if p.get("overall_yield_pct") is not None),
               key=lambda p: p["overall_yield_pct"], default=None)
    ref = lambda c: {"identifier": c["identifier"], "smiles": c.get("smiles"),
                     "compound_uuid": c["compound_uuid"]}
    return {
        "reaction_count": len(rxns),
        "compound_count": len(mols),
        "pathway_count": len(pws),
        "section_summary": dict(sec),
        "target_compounds": [ref(m) for m in mols if m.get("is_section_product")],
        "key_starting_materials": [
            ref(m) for m in mols
            if "compound_class:starting_material" in (m.get("tags") or [])
            and (m.get("section_type") or "") not in NOT_THIS_PATENTS_CHEMISTRY],
        "chemistry_focus": [k for k, _ in cls.most_common(5)],
        "best_overall_yield_pct": best["overall_yield_pct"] if best else None,
        "best_overall_yield_pathway_uuid": best["pathway_uuid"] if best else None,
        "scale_distribution": dict(scale),
    }


def inventors(b: dict) -> list[dict]:
    """Inventor names and countries, from the biblio rather than from a constant.

    This was `{"name": n, "country": "CN"}`, a literal, for every inventor of every
    patent. It was right for the one patent in the pack and silently wrong for any
    other: a US patent's inventors came out labelled Chinese, in the deliverable,
    with no crash and nothing to notice.

    Two shapes are accepted, so a biblio that knows can say so:

        "inventors": ["A Person", "B Person"]                 country from the office
        "inventors": [{"name": "A Person", "country": "DE"}]  stated outright

    The bare-string form falls back to the issuing jurisdiction, which is a guess,
    but a defensible one and the same guess for every patent rather than one
    patent's answer applied to all of them. Where it matters, state it.
    """
    out = []
    fallback = (b.get("jurisdiction") or "").upper() or None
    for inv in b.get("inventors") or []:
        if isinstance(inv, dict):
            out.append({"name": inv.get("name"),
                        "country": inv.get("country") or fallback})
        else:
            out.append({"name": inv, "country": fallback})
    return out


def finalise_patent(llm, mols, rxns, pws):
    b = json.loads(BIBLIO.read_text())
    tags = list(llm.get("tags") or [])
    # metadata-derived categories the prompt is told NOT to emit
    tags += [f"jurisdiction:{b['jurisdiction']}",
             f"patent_family:{b['family_id']}",
             f"time_period:{b['publication_date'][:4]}"]
    for a in b.get("assignees") or []:
        tags += [f"assignee:{tag_slug(a['name'])}",
                 f"assignee_type:{a['type']}"]
    # full inheritance: union every reaction / compound / pathway tag
    for coll in (mols, rxns, pws):
        for rec in coll:
            tags += rec.get("tags") or []
    seen, uniq = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    return {
        "patent_id": PATENT_ID,
        "patent_uuid": uuid5(PATENT_ID),
        "title": b["title_en"],
        # A4 is given the abstract, it does not emit one. The A5 audit found this
        # null against a front page that prints it in full. Sourced from pass V.
        "abstract": b.get("abstract_zh"),
        "language": b["language"],
        "bibliographic": {
            "publication_date": b["publication_date"],
            "priority_date": b["priority_date"],
            "filing_date": b["filing_date"],
            "grant_date": b["grant_date"],
            "jurisdiction": b["jurisdiction"],
            "patent_type": None,
            "legal_status": b["legal_status"],
            "family_id": b["family_id"],
            "ipc_codes": b.get("ipc_codes") or None,
            "cpc_codes": None,
        },
        "parties": {"assignees": [{"name": a["name"], "country": a["country"],
                                   "type": a["type"]}
                                  for a in b["assignees"]],
                    "inventors": inventors(b),
                    "examiners": None},
        "patent_summary": llm.get("patent_summary"),
        "novelty_claims": llm.get("novelty_claims"),
        "key_examples": llm.get("key_examples"),
        "extraction_rollup": rollup(mols, rxns, pws),
        "tags": uniq,
        "source_refs": {"patent_summary_doc_id": None,
                        "blob_root": "manual_annotations/output",
                        "extracted_at": None,
                        "extractor_commit_sha": None},
        "honest_uncertainty_flags": llm.get("honest_uncertainty_flags") or [],
    }


def assert_patent_scope(raw: dict[str, object]) -> list[str]:
    """Every patent_id already on an incoming record must be the one we are running.

    This is the guard that was missing, and its absence produced the worst artifact
    this pipeline can produce. Point the runner at a second patent in a pack that
    still holds the first patent's A0 to A5 output and every stage agrees: the
    passes are present, so the prerequisite check is satisfied; the schema does not
    say a record's patent_id must match the run, so validation passes; and this
    function's absence meant `m.setdefault("patent_id", ...)` left the OLD id in
    place while `build_compound_id` stamped the NEW one into `id`.

    The result was 75 compound records each carrying id US9999999B2_<name> and
    patent_id CN104292137A, under a patent record for US9999999B2, published to the
    deliverable, internally consistent enough that nothing downstream objected. A
    crash is a message. That is a lie with a schema.

    So: refuse. Loudly, before a single id is built.
    """
    def walk(node, out):
        if isinstance(node, dict):
            v = node.get("patent_id")
            if isinstance(v, str) and v:
                out.add(v)
            for x in node.values():
                walk(x, out)
        elif isinstance(node, list):
            for x in node:
                walk(x, out)

    problems = []
    for name, obj in raw.items():
        found = set()
        walk(obj, found)
        wrong = sorted(found - {PATENT_ID})
        if wrong:
            problems.append(f"  raw-{name}.json carries patent_id {wrong}")
    return problems


def main() -> int:
    global PATENT_ID, BIBLIO
    check = "--check" in sys.argv
    try:
        PATENT_ID = resolve_patent_id()
    except ContextError as e:
        print(f"FAIL  {e}", file=sys.stderr)
        return 2
    BIBLIO = biblio_path(PATENT_ID)
    if not BIBLIO.exists():
        print(f"FAIL  {BIBLIO} not found", file=sys.stderr)
        return 2
    print(f"patent    : {PATENT_ID}")
    mols, rxns, pws, pat = (load_raw("compounds"), load_raw("reactions"),
                            load_raw("pathways"), load_raw("patent"))
    missing = [n for n, v in [("compounds", mols), ("reactions", rxns),
                              ("pathways", pws), ("patent", pat)] if v is None]
    if missing:
        print(f"missing raw pass output: {', '.join(missing)}")
        print(f"expected at {OUT}/raw-<name>.json")
        return 1

    wrong = assert_patent_scope({"compounds": mols, "reactions": rxns,
                                 "pathways": pws, "patent": pat})
    if wrong:
        print(f"\nFAIL  this run is {PATENT_ID!r}, but the pass output is not.\n",
              file=sys.stderr)
        for w in wrong:
            print(w, file=sys.stderr)
        print(f"\n  The A0 to A5 stage folders are not scoped by patent, so a pack that\n"
              f"  still holds another patent's pass output will satisfy every\n"
              f"  prerequisite check and then be finalised under {PATENT_ID!r}. The ids\n"
              f"  would be built from {PATENT_ID!r} while the records kept the other\n"
              f"  patent's, and nothing downstream would object.\n\n"
              f"  Clear output/stages/ and input/vision/ and run the passes for\n"
              f"  {PATENT_ID!r}, or run the pipeline on the patent this pack holds.",
              file=sys.stderr)
        return 2

    mols = finalise_compounds(mols)
    rxns = finalise_reactions(rxns)
    pws = finalise_pathways(pws, mols, rxns)
    patent = finalise_patent(pat, mols, rxns, pws)

    # seen_in_sections is our own bookkeeping, not a CompoundRecord field. Keeping
    # it on the record would make every compound diff against production output, so
    # it moves to a sidecar.
    sections_index = {m["identifier"]: m.pop("seen_in_sections")
                      for m in mols if "seen_in_sections" in m}
    equiv = equivalence_index(mols)

    if not check:
        (OUT / "compounds-sections.json").write_text(
            json.dumps(sections_index, indent=2, ensure_ascii=False))
        (OUT / "compounds-equivalence.json").write_text(
            json.dumps(equiv, indent=2, ensure_ascii=False))
        for name, obj in [("compounds", mols), ("reactions", rxns),
                          ("pathways", pws), ("patent", patent)]:
            (OUT / f"{name}.json").write_text(
                json.dumps(obj, indent=2, ensure_ascii=False))

    print(f"reactions : {len(rxns):4}  ids + uuids assigned")
    print(f"pathways  : {len(pws):4}  uuids assigned, refs resolved")
    print(f"patent    :    1  biblio merged, {len(patent['tags'])} tags after union")
    if ROLE_FIXES:
        print(f"\nrole values normalised to the CompoundRecord enum ({len(ROLE_FIXES)}):")
        for x in ROLE_FIXES:
            print(f"  {x}")
    n_frag = sum(len(v) for v in equiv.values())
    print(f"\nmolecules carried under more than one spelling: {len(equiv)} "
          f"({n_frag} records that are really {len(equiv)} molecules)")
    print("  not merged: production keys on the exact identifier string and would")
    print("  fragment identically. Equivalence written to compounds-equivalence.json.")
    print(f"\ncompounds seen in more than one section: "
          f"{sum(1 for v in sections_index.values() if len(v) > 1)} "
          f"(index written to compounds-sections.json)")
    flagged = [r["reaction_id"] for r in rxns if r.get("validation_flags")]
    print(f"\nreactions carrying validation_flags: {len(flagged)}")
    for r in flagged:
        rec = next(x for x in rxns if x["reaction_id"] == r)
        print(f"  {r:28} {', '.join(rec['validation_flags'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
