#!/usr/bin/env python3
r"""Put a structure on every gold record that can honestly carry one.

WHY THIS EXISTS
---------------
`resolve_structures.py` resolves identifiers into a SIDECAR, `structures-resolved.json`,
and leaves `smiles` null on the records themselves. That was right while these files
were a scoring reference: a SMILES is a lookup, not an extraction, so a reference
carrying one would grade the enrichment service instead of the extractor.

These four patents are a GOLD DATASET now, not a scoring key. A gold record that
names a molecule and cannot say which molecule is an incomplete record. So this
writes the structure onto the record, and the departures table in README.md says so.

FOUR READERS, AND WHY IT IS FOUR
--------------------------------
Every structure in this repo used to trace back to a single reader. 76% of them came
from OPSIN alone, carrying `name_check: "is_the_source"`, which the verification
contract defines in as many words as "nothing independent has looked at it". That is
not a theoretical worry. It is why four patents here recorded `bromine` as [Br], one
atom, molecular weight 79.9 instead of 159.8, and nothing noticed for months.

    curated         a human typed it, having looked at the drawing        strongest
    patent_drawing  a vision pass read it off this patent's own scheme
    opsin           a grammar derived it from the systematic name
    pubchem         a database looked the name up                          weakest

The point is not the ranking. It is that these four fail in unrelated ways, so where
two agree, two unrelated routes reached the same molecule. A grammar cannot know
`mesotrione` and a database cannot parse a name nobody has indexed, so they cover
each other rather than competing.

    identifier
        |
        +-- ask every reader that can answer this KIND of string
        |
        +-- canonicalise every answer through RDKit
        |
        +-- one distinct answer   -> agreed, n sources on the record
        +-- more than one         -> adjudicate, and print the reason
        +-- none                  -> smiles null, and smiles_source says WHY

WHAT `smiles_source` HOLDS WHEN THERE IS NO STRUCTURE
-----------------------------------------------------
`none` on its own is the same failure as a guard that passes on absence: it cannot
tell "this is not a molecule" from "we did not manage to look it up". So the field
always carries the reason, and the reasons are different facts:

    none:class_name   `organic solvent`, `aromatic hydrocarbon`. Names a CLASS.
    none:markush      `compound of formula (I)`. A structure with variables in it.
    none:reference    `compound of Example No. 5`. Points at a molecule, is not one.
    none:material     `talc`, `kaolin`. Real, not molecular.
    none:polymer      `polyethylene glycol`. Real, not one molecule.
    none:ambiguous    `xylene`. Names three molecules and the patent does not say.
    none:unresolved   a specific molecule, and no reader here could find it.

Only the last is a gap somebody could close. The other six are the honest answer.

Usage:  python3 enrich_structures.py --patent-id WO2024109718A1
        python3 enrich_structures.py --patent-id WO2024109718A1 --check   # write nothing
        python3 enrich_structures.py --all                                 # every listed run
        python3 enrich_structures.py --patent-id X --offline               # caches only
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
VENDOR = HERE / "vendor"
JAR = VENDOR / "opsin-core-2.9.0.jar"
BATCH = VENDOR / "OpsinBatch.java"

PUBCHEM = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}"
           "/property/SMILES,MolecularFormula/JSON")


# ------------------------------------------------------------------ RDKit helpers

def canon(smiles: str | None) -> str | None:
    if not smiles:
        return None
    mol = Chem.MolFromSmiles(smiles)
    return Chem.MolToSmiles(mol) if mol is not None else None


def describe(smiles: str) -> dict:
    """The three fields a record carries, all derived from one string."""
    mol = Chem.MolFromSmiles(smiles)
    return {"smiles": Chem.MolToSmiles(mol),
            "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": round(Descriptors.MolWt(mol), 2)}


def connectivity(smiles: str) -> str | None:
    """InChIKey's first block: same skeleton, ignoring protonation and stereo.

    Used only to separate "these are different molecules" from "these are the same
    substance written ionic and covalent", which is most of what a database and a
    grammar disagree about on inorganics.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        return inchi.MolToInchiKey(mol).split("-")[0]
    except Exception:                                       # noqa: BLE001
        return None


def looks_like_smiles(s: str) -> bool:
    """True when the string is a STRUCTURE rather than a name that happens to parse.

    RDKit is happy to read plenty of abbreviations as molecules. `NBS` tokenises,
    because N, B and S are all organic-subset atoms, and it abbreviates
    N-bromosuccinimide. So parsing is necessary and not sufficient: a real SMILES
    from a drawn scheme also carries structure, a ring closure, a branch, a bond or
    a bracket atom. Deliberately conservative, and it rejects `CO`, which is both a
    valid SMILES and this patent's abbreviation for carbon monoxide.
    """
    if not s or " " in s:
        return False
    if not any(c in s for c in "()[]=#123456789"):
        return False
    return Chem.MolFromSmiles(s) is not None


def formula_of(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    return rdMolDescriptors.CalcMolFormula(mol) if mol is not None else None


# ------------------------------------------------------- what is not a molecule

# Ordered most specific first: `silica gel` must not be read as a class name because
# it ends in a word that also ends other class names.
MATERIALS = {
    "talc", "kaolin", "limestone", "lime", "chalk", "bole", "loess", "clay",
    "clays", "natural clays", "dolomite", "silica gel", "silica gels",
    "silicic acid", "silicic acids", "celite", "attapulgite", "montmorillonite",
    "bentonite", "pumice", "gypsum", "diatomaceous earth", "kieselguhr",
    "perlite", "vermiculite", "sand", "glass", "charcoal", "activated carbon",
    "molecular sieve", "molecular sieves", "zeolite", "zeolites", "silicate",
    "silicates", "ground synthetic minerals", "sawdust", "coconut shells",
    "corn cobs", "tobacco stalks", "cellulose powder", "granulated clay",
}

POLYMER = re.compile(
    r"^(poly|co-?poly)|"
    r"\b(polymers?|copolymers?|resins?|celluloses?|cellulose ether|alginates?|"
    r"lignin|lignosulfon\w*|ligninsulfon\w*|dextrins?|starch\w*|gums?|waxes|"
    r"gelatin\w*|condensation products?|polyvinyl\w*|polyethylene glycol\w*|"
    # An enzyme is a protein, which is a polymer, and no single SMILES describes
    # one. `4-hydroxyphenylpyruvate dioxygenase` is the target these herbicides
    # inhibit, and it is named alongside the molecules that inhibit it.
    # \w{5,} and not \w+ on purpose: `base` ends in `ase` and is a class name,
    # not an enzyme, and a five-character stem keeps it out.
    r"\w{5,}ases?|enzymes?|proteins?|antibod(y|ies))\b",
    re.I)

# Plural class nouns that make everything before them a family rather than a
# molecule. `benzoylcyclohexane-1,3-dione herbicides` carries locants and still
# names a class, so the no-digits test that catches `triketones` cannot see it.
# Patent prose names one molecule in the singular; the plural is the tell.
CLASS_TAIL = {
    "acids", "esters", "ethers", "alcohols", "ketones", "amines", "amides",
    "aldehydes", "nitriles", "halides", "salts", "oxides", "peroxides",
    "herbicides", "pesticides", "fungicides", "insecticides", "compounds",
    "derivatives", "analogues", "analogs", "homologues", "hydrocarbons",
    "solvents", "bases", "catalysts", "reagents", "sulfones", "sulfides",
    "phenols", "anilines", "quinones", "pyridines", "benzoates", "products",
    "intermediates", "impurities", "substances", "materials", "species",
}

MARKUSH = re.compile(
    r"\b(of\s+(the\s+)?(general\s+)?formulae?|of\s+formulae?|according to the invention|"
    r"of the invention|general formula)\b", re.I)

# A variable substituent anywhere in the name makes the name a family, not a
# molecule. `2-chloro-3-(alkoxymethyl)-4-(methanesulfonyl)benzoic acid` is the whole
# claim scope written as one string, and no structure is the honest answer for it.
#   ...-3-(alkoxymethyl)-4-...     no word boundary after `alkoxy`, so the group
#                    ^^^^^^        alternatives deliberately do not require one.
VARIABLE = re.compile(
    r"\balk(yl|oxy|enyl|ynyl|ylene)|\baralkyl|\baryloxy|\baryl\b|\bacyl\b|"
    r"\b(lower|higher)\s+alk", re.I)
# Case sensitive, and never before a hyphen: `m-`, `o-`, `p-`, `N-` and `S-` are
# position prefixes on real names, not variables standing in for a group.
VARIABLE_LETTER = re.compile(r"\b(R\d?|R'|X|Y|Z|M|Ar)\b(?!-)")
# `ROH`, `ROM`, `MOH`, `M2CO3`: a formula with a variable letter standing in for a
# group. Written as a formula, so the word-boundary test above cannot see them.
VARIABLE_FORMULA = re.compile(r"^[RMXYZ][A-Za-z0-9()\[\]]{0,9}$")

REFERENCE = re.compile(
    r"\b(of\s+Example|Example\s+No\.?|Tabelle|Table\s+\d|No\.\s*\d|"
    r"target\s+(compound|product|molecule)|starting\s+materials?|"
    r"the\s+(corresponding|above|foregoing|said)\b|"
    r"the\s+\w+\s+of\s+the\s+(target|title|desired))", re.I)

# A class noun in the head position with nothing in front of it but a qualifier.
# `organic solvent` is a class; `benzoic acid` is not, because `benzoic` is not a
# qualifier. That guard is what keeps a real molecule out of this bucket.
CLASS_HEAD = re.compile(
    r"\b(solvents?|bases?|acids?|catalysts?|reagents?|agents?|initiators?|oxidants?|"
    r"oxidi[sz]ing agents?|reducing agents?|additives?|carriers?|emulsifiers?|"
    r"surfactants?|dispersants?|wetting agents?|antifoams?|foam suppressants?|"
    r"stabili[sz]ers?|preservatives?|thickeners?|binders?|diluents?|fillers?|"
    r"adjuvants?|colorants?|dyes?|pigments?|inert gas(es)?|desiccants?|oxides?|"
    r"drying agents?|hydrocarbons?|derivatives?|compounds?|substances?|"
    r"materials?|species|impurit(y|ies)|salts?|halides?|mixtures?|metals?|"
    r"alcohols?|alkoxides?|ethers?|esters?|ketones?|amines?|amides?|nitriles?|"
    r"phenols?|aldehydes?|sulfones?|sulfides?|anhydrides?|peroxides?|"
    r"quinones?|products?|intermediates?)\b", re.I)

CLASS_QUALIFIER = re.compile(
    r"^(an?|the|any|some|other|suitable|customary|conventional|inert|organic|"
    r"inorganic|aqueous|aromatic|aliphatic|polar|apolar|protic|aprotic|strong|"
    r"weak|first|second|third|fourth|alkali|alkaline|earth|transition|noble|"
    r"cyclic|acyclic|halogenated|substituted|unsubstituted|corresponding|"
    r"primary|secondary|tertiary|quaternary|basic|acidic|neutral|"
    r"desired|target|type|crude|reaction|by|side|or|and|[a-z]+ing)\b", re.I)

# A role, not a substance. No single molecule is called `palladium catalyst` or
# `acid-binding agent`: the patent is naming what the thing DOES and leaving the
# choice open. Anything at all in front of these still leaves a class.
ROLE_TAIL = re.compile(
    r"\b(catalysts?|solvents?|agents?|ligands?|reagents?|initiators?|oxidants?|"
    r"reductants?|desiccants?|carriers?|diluents?|adjuvants?|additives?|"
    r"solutions?|mixtures?|liquors?|media|thereof)$", re.I)

# Singular class words this repo's patents use as families. A plural is the usual
# tell and these have none, so they are listed rather than inferred.
SINGULAR_CLASS = {"haloform", "triketone", "diketone", "trione", "quinone",
                  "sulfonamide", "carbamate", "phenoxy", "sulfonylurea"}

# `diazonium salt` names a charge type and the word salt, and nothing else. The
# gold's own note says so: "The text names only the compound class, not a specific
# salt". PubChem answers it with the bare diazonium ion, N#[NH+], mass 29, which is
# a fragment of every member of the class and none of them.
FUNCTIONAL_CATION = re.compile(
    r"\b(diazonium|ammonium|sulfonium|phosphonium|oxonium|iminium|carbenium|"
    r"pyridinium|imidazolium|azolium)\s+salts?$", re.I)

# A bare plural of a chemical class, with no locants to pin an isomer down.
# `triketones`, `pyrazolones`, `isoxazolones`. Patent prose names one molecule in
# the singular, so the plural is the tell, and the no-digits test keeps
# `3-methylbenzoic acids` out of here and in the Markush bucket where it belongs.
CLASS_PLURAL = re.compile(
    r"^[a-z][a-z\- ]*(ones|oles|ines|ates|ides|enes|anes|ols|ynes|azines|azoles|"
    r"pyridines|pyrimidines|benzenes|phenones|anilines)$", re.I)

# Names that pin no single molecule down even though they parse. OPSIN reports these
# as WARNING and this pipeline has never promoted a warning to a structure; the list
# also catches the ones OPSIN accepts silently.
AMBIGUOUS_NAMES = {
    "xylene", "xylenes", "dichloroethane", "dichlorobenzene", "cresol",
    "cyclohexanedione", "benzoylcyclohexanedione", "nonylphenol", "octylphenol",
    "isooctylphenol", "tributylphenol", "tetrahydronaphthalene", "cymene",
    "trimethylbenzene", "butanol", "propanol", "xylenol", "toluidine",
}

# Generic Chinese terms that name a role, not a molecule. The English classifier
# cannot see them and the run's own translation of 催化剂 is the abbreviation `cat`,
# which classifies as nothing. Eight words, and they are the eight this repo's CN
# patents actually use.
CHINESE_GENERIC = {
    "溶剂": "none:class_name", "催化剂": "none:class_name", "碱": "none:class_name",
    "酸": "none:class_name", "试剂": "none:class_name", "原料": "none:reference",
    "产物": "none:reference", "中间体": "none:reference",
    "卤仿": "none:class_name", "溴代试剂": "none:class_name",
}

_QUALIFIERS = ("anhydrous", "saturated", "aqueous", "concentrated", "dilute", "dry",
               "fuming", "glacial", "cold", "hot", "fresh", "solid", "liquid",
               "gaseous", "crude", "pure", "ice")
_ARTICLES = {"the", "a", "an", "said", "this", "that"}
_TRAILING = {"solution", "solutions", "solvent", "reagent", "salt", "liquor"}


def normalise(s: str) -> str:
    t = re.sub(r"[\s_]+", " ", s.lower().strip())
    for q in _QUALIFIERS:
        t = re.sub(rf"\b{q}\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def is_chinese(s: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in s)


def no_structure_reason(identifier: str, english_forms: list[str] | None = None) -> str | None:
    """Why this string can never carry one structure, or None if it might.

    Deliberately says nothing about whether a lookup will succeed. That is the
    readers' job, and conflating "not a molecule" with "not found" is the mistake
    this whole field exists to avoid.
    """
    s = identifier.strip()
    n = normalise(s)
    if not n:
        return "none:unresolved"
    # 式(I)化合物 is `compound of formula (I)`, and it is 55 of WO2024109718A1's
    # 173 pathway references. The English MARKUSH pattern cannot see it, and no
    # reader can resolve it, so without this it reads as chemistry we failed at.
    if re.search(r"(通)?式\s*[(（]?\s*[IVX0-9]+\s*[)）]?\s*(的)?化合物", s):
        return "none:markush"
    if is_chinese(s):
        # A grammar for English nomenclature has nothing to say about a Chinese
        # string, and neither has this classifier. Both read the English the run
        # already carries instead of reporting a language gap as a chemistry gap.
        stripped = re.sub(r"\d+$", "", s).strip()
        if stripped in CHINESE_GENERIC:
            return CHINESE_GENERIC[stripped]
        for form in english_forms or []:
            got = no_structure_reason(form)
            if got:
                return got
        return None
    if (MARKUSH.search(s) or VARIABLE.search(s) or VARIABLE_LETTER.search(s)
            or VARIABLE_FORMULA.match(s)):
        return "none:markush"
    if REFERENCE.search(s):
        return "none:reference"
    if n in MATERIALS:
        return "none:material"
    if POLYMER.search(s):
        return "none:polymer"
    if n in AMBIGUOUS_NAMES:
        return "none:ambiguous"
    head = n.split()
    if head and head[0] in ("compound", "compounds"):
        return "none:markush"
    if FUNCTIONAL_CATION.search(n):
        return "none:class_name"
    if re.match(r"^(a|an|any|some)\s", n) and CLASS_HEAD.search(n):
        return "none:class_name"
    if "(class)" in n or ROLE_TAIL.search(n):
        return "none:class_name"
    if n in SINGULAR_CLASS or n.split()[-1] in CLASS_TAIL:
        return "none:class_name"
    if CLASS_PLURAL.match(n) and not any(ch.isdigit() for ch in n):
        return "none:class_name"
    if re.search(r"\btype\s+compounds?\b", n):
        return "none:class_name"
    if CLASS_HEAD.search(n):
        without_head = CLASS_HEAD.sub("", re.sub(r"\s+\d+$", "", n)).strip(" -")
        words = without_head.replace("-", " ").split()
        if not words or all(CLASS_QUALIFIER.match(w) for w in words):
            return "none:class_name"
    return None


# ------------------------------------------------------------------- the readers

class Opsin:
    """The vendored jar, asked once for every name in the run.

    One JVM start for the whole patent rather than one per name: the grammar tables
    take longer to build than every parse in this repo takes to run.
    """

    def __init__(self, cache_file: Path, offline: bool = False):
        self.file = cache_file
        self.offline = offline
        doc = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
        self.answers: dict = doc.get("answers") or {}

    def warm(self, queries: list[str]) -> None:
        want = sorted({q for q in queries if q and q not in self.answers})
        if not want:
            return
        if self.offline:
            raise RuntimeError(f"{len(want)} names not cached and --offline was given")
        if not JAR.exists():
            raise RuntimeError(f"{JAR} is missing. See pipeline/vendor/README.md")
        proc = subprocess.run(
            ["java", "-cp", str(JAR), str(BATCH)],
            input="\n".join(want) + "\n", capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise RuntimeError(f"OPSIN exited {proc.returncode}: {proc.stderr[-400:]}")
        got = 0
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            ans = json.loads(line)
            self.answers[ans["query"]] = {"status": ans["status"], "smiles": ans["smiles"],
                                          "message": ans["message"]}
            got += 1
        # A silently short answer would look exactly like a run where every name
        # failed, and would then be cached as such.
        if got != len(want):
            raise RuntimeError(f"OPSIN answered {got} of {len(want)} names")

    def ask(self, query: str) -> tuple[str | None, str]:
        """(smiles, why-not). A WARNING is never a structure, and says so."""
        a = self.answers.get(query)
        if not a:
            return None, "not asked"
        if a["status"] == "SUCCESS":
            return a["smiles"], ""
        if a["status"] == "WARNING":
            return None, f"ambiguous: {a['message'][:120]}"
        return None, "unparseable"

    def save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps({
            "reader": "OPSIN 2.9.0, pipeline/vendor/opsin-core-2.9.0.jar",
            "what": "OPSIN's answer for one exact query string, so a re-run needs no jar.",
            "answers": self.answers}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


class PubChem:
    """A name dictionary, over HTTPS, cached per run.

    The reader that covers what a grammar structurally cannot: trade and common
    names. `mesotrione` is one molecule with one structure and OPSIN will never
    parse it, because it is not built out of nomenclature.

    NEVER ASKED ABOUT A FORMULA-SHAPED STRING. PubChem resolves `CO` to cobalt, and
    the patent means carbon monoxide. A lookup that answers confidently with the
    wrong molecule is worse than one that does not answer, so the shape test below
    keeps those strings away from it entirely.
    """

    #  Two capitals, or a capital and digits, and short. `CO`, `NBS`, `Br2`, `MOH`.
    FORMULA_SHAPED = re.compile(r"^[A-Z][A-Za-z0-9()\[\]/·.]{0,7}$")

    def __init__(self, cache_file: Path, offline: bool = False):
        self.file = cache_file
        self.offline = offline
        doc = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
        self.answers: dict = doc.get("answers") or {}

    def askable(self, query: str) -> bool:
        if not query or is_chinese(query) or len(query) > 180:
            return False
        if self.FORMULA_SHAPED.match(query) and " " not in query:
            return False
        return True

    def ask(self, query: str) -> tuple[str | None, str]:
        if not self.askable(query):
            return None, "not asked: formula-shaped or not English"
        if query in self.answers:
            a = self.answers[query]
            return a.get("smiles"), a.get("message", "")
        if self.offline:
            return None, "not cached and --offline"
        url = PUBCHEM.format(urllib.parse.quote(query, safe=""))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "patent-extraction/gold"})
            with urllib.request.urlopen(req, timeout=25) as r:
                doc = json.load(r)
            p = doc["PropertyTable"]["Properties"][0]
            ans = {"smiles": p.get("SMILES"), "cid": p.get("CID"),
                   "formula": p.get("MolecularFormula"), "message": ""}
        except urllib.error.HTTPError as e:
            if e.code == 404:
                ans = {"smiles": None, "message": "no entry"}
            else:
                # A 503 is the service throttling us. Caching it would turn a
                # transient into a permanent "this name has no structure".
                return None, f"HTTP {e.code}, not cached"
        except Exception as e:                              # noqa: BLE001
            return None, f"{type(e).__name__}, not cached"
        self.answers[query] = ans
        time.sleep(0.22)                # PubChem asks for no more than 5 per second
        return ans.get("smiles"), ans.get("message", "")

    def save(self) -> None:
        self.file.parent.mkdir(parents=True, exist_ok=True)
        self.file.write_text(json.dumps({
            "service": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/",
            "what": "PubChem's answer for one exact name, so a re-run needs no network.",
            "answers": self.answers}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def read_local_evidence(run: Path) -> tuple[dict, dict]:
    """(curated, drawn): what a human typed, and what the vision pass read.

    Both are readings of THIS document, which is what makes them stronger than any
    lookup. Keyed by normalised name, and drawn structures additionally by canonical
    SMILES, because the drawn scheme is read more than once and the reads name the
    same molecule differently. Joining drawings on names alone loses most of them.
    """
    curated: dict[str, str] = {}
    f = run / "input" / "structures-curated.json"
    if f.exists():
        doc = json.loads(f.read_text(encoding="utf-8"))
        for name, entry in (doc.get("entries") or {}).items():
            smi = entry.get("smiles") if isinstance(entry, dict) else entry
            if smi and canon(smi):
                curated[normalise(name)] = smi

    drawn: dict[str, str] = {}
    f = run / "output" / "structures.json"
    if f.exists():
        for block in json.loads(f.read_text(encoding="utf-8")):
            for s in block.get("structures") or []:
                smi, name = s.get("smiles"), s.get("name")
                if not smi or not canon(smi):
                    continue
                if name:
                    drawn.setdefault(normalise(name), smi)
    return curated, drawn


# -------------------------------------------------------------- the query ladder

def plausible_name(s: str) -> bool:
    """A chemical name, not a sentence and not a roman numeral.

    This gate exists because of one translation. `氯化钯` in WO2024109718A1 is
    rendered as a whole sentence listing every palladium catalyst the patent
    mentions, and pulling the parentheticals out of it handed `Pd/C`, `PdCO3` and
    `dibenzylideneacetone` to EVERY palladium record as if each were a synonym of
    that record. Three of them then resolved to the wrong metal complex.

    A name is short and has few words. Anything else is prose about the molecule.
    """
    if not s or len(s) > 120 or len(s.split()) > 10:
        return False
    if re.fullmatch(r"[IVXivx]+|\d+", s):
        return False
    # A comma with a space after it is prose. A comma without one is nomenclature:
    # `N,N-dimethylformamide`, `2-methyl-1,4-diazabicyclo[2.2.2]octane`. Rejecting
    # every comma cost two real solvents their only English name.
    return ", " not in s and "; " not in s


def query_forms(identifier: str, aliases: list[str], english: dict[str, str]) -> list[str]:
    """Every string worth asking about this identifier, most literal first."""
    out: list[str] = []

    def add(s: str) -> None:
        s = " ".join((s or "").split()).strip(" ,;:")
        if s and s not in out and plausible_name(s):
            out.append(s)

    # The identifier itself is always asked about, however long it is: it is the
    # thing being resolved, not a candidate synonym that has to earn its place.
    out.append(" ".join(identifier.split()))
    for a in aliases or []:
        add(a)
    # The pipeline's own English for anything that is not English. A grammar and a
    # database both have nothing to say about a Chinese name, and the run already
    # carries a translation for it.
    for name in [identifier, *(aliases or [])]:
        if name and is_chinese(name) and name in english:
            en = re.sub(r"\[[^\]]*\]", " ", english[name])
            cands = [re.sub(r"\([^)]*\)", " ", en)]
            # A parenthetical is a synonym only inside something already the size
            # of a name. Inside a sentence it is somebody else's molecule.
            if len(en) <= 80:
                cands += re.findall(r"\(([^)]*)\)", en)
            for cand in cands:
                add(cand)
    # Qualifiers and trailing nouns describe the bottle, not the molecule, and they
    # compose: `aqueous sodium hydroxide solution` needs both ends stripped.
    for name in list(out):
        cur, dropped = name, False
        for _ in range(4):
            w = cur.split()
            if len(w) > 1 and w[0].lower().strip(",") in _ARTICLES | set(_QUALIFIERS):
                cur, dropped = " ".join(w[1:]), True
                continue
            if len(w) > 1 and w[-1].lower().strip(",.") in _TRAILING:
                cur, dropped = " ".join(w[:-1]), True
                continue
            break
        if dropped:
            add(cur)
    return out


def load_english(run: Path) -> dict[str, str]:
    """Chinese string -> the English this run already carries for it.

    Both files, curated first. The curated table is the hand-checked one and wins;
    output/translations.json is the translations stage's own output and covers far
    more strings, including every generic term. Taking only the curated table would
    report five Chinese identifiers as chemistry we could not resolve, when what we
    actually could not do is read Chinese.
    """
    out: dict[str, str] = {}
    for f, is_curated in ((run / "output" / "translations.json", False),
                          (run / "input" / "translations-curated.json", True)):
        if not f.exists():
            continue
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        entries = doc.get("entries") if "entries" in doc else doc
        for zh, entry in (entries or {}).items():
            en = entry.get("en") if isinstance(entry, dict) else entry
            if isinstance(en, str) and en.strip() and (is_curated or zh not in out):
                out[zh] = en.strip()
    return out


# -------------------------------------------------------------- the adjudication

# Elements a patent charges as the diatomic molecule, whatever the prose calls them.
# OPSIN parses the bare element name to a single ATOM, which halves the molecular
# weight and therefore doubles every mole count computed from a mass.
DIATOMIC = {
    "hydrogen": "[H][H]", "nitrogen": "N#N", "oxygen": "O=O",
    "fluorine": "FF", "chlorine": "ClCl", "bromine": "BrBr", "iodine": "II",
}
DIATOMIC_ALIAS = {"h2": "hydrogen", "n2": "nitrogen", "o2": "oxygen", "f2": "fluorine",
                  "cl2": "chlorine", "br2": "bromine", "i2": "iodine"}

# Species every chemist knows, that a grammar cannot parse and a name lookup gets
# wrong. Hand-authored, so checked atom by atom against the name, as required.
# Nothing patent-specific belongs here: that goes in the run's
# input/structures-curated.json, where a reviewer looking at one patent will see it.
#
#   name                    SMILES              formula   checked
#   NBS                     O=C1CCC(=O)N1Br     C4H4BrNO2 succinimide ring, N bears Br
#   NCS                     O=C1CCC(=O)N1Cl     C4H4ClNO2 the same, chlorine
#   hydrogen chloride       Cl                  ClH       one implicit H on chlorine
#   hydrogen peroxide       OO                  H2O2      O-O single bond, one H each
#   thionyl chloride        O=S(Cl)Cl           Cl2OS     S=O, two S-Cl
#   phosphoryl chloride     O=P(Cl)(Cl)Cl       Cl3OP     P=O, three P-Cl
#   carbon monoxide         [C-]#[O+]           CO        the accepted Lewis form;
#                                                         OPSIN returns [C]=O, a
#                                                         carbene, same formula
#   brine                   [Na+].[Cl-]         ClNa      the SOLUTE. Water is the
#                                                         bottle, and `saturated`
#                                                         is already stripped as a
#                                                         qualifier everywhere else
#   palladium on carbon     [Pd]                Pd        the carbon is a support,
#                                                         not part of the species
KNOWN = {
    "nbs": "O=C1CCC(=O)N1Br", "n-bromosuccinimide": "O=C1CCC(=O)N1Br",
    "ncs": "O=C1CCC(=O)N1Cl", "n-chlorosuccinimide": "O=C1CCC(=O)N1Cl",
    "hcl": "Cl", "hydrogen chloride": "Cl", "hydrochloric acid": "Cl",
    "h2o2": "OO", "hydrogen peroxide": "OO",
    "socl2": "O=S(Cl)Cl", "thionyl chloride": "O=S(Cl)Cl",
    "pocl3": "O=P(Cl)(Cl)Cl", "phosphorus oxychloride": "O=P(Cl)(Cl)Cl",
    "phosphoryl chloride": "O=P(Cl)(Cl)Cl",
    "co": "[C-]#[O+]", "carbon monoxide": "[C-]#[O+]",
    "brine": "[Na+].[Cl-]",
    "palladium on carbon": "[Pd]", "pd/c": "[Pd]", "palladium/carbon": "[Pd]",
    "water": "O", "h2o": "O",
}


def known_species(query: str) -> str | None:
    """A diatomic element or a species from the hand-checked table above."""
    n = normalise(query)
    flat = n.replace(" ", "")
    base = DIATOMIC_ALIAS.get(flat, n)
    if base in DIATOMIC:
        return DIATOMIC[base]
    return KNOWN.get(n) or KNOWN.get(flat)


_ELEMENT = re.compile(r"([A-Z][a-z]?)(\d*)")


def as_formula(s: str) -> dict[str, int] | None:
    """`K3PO4` -> {K:3, P:1, O:4}, or None when the string is not a plain formula.

    Only used to let a record's OWN alias arbitrate between two readers. The gold
    carries `K3PO4` beside `potassium phosphate`, which says which of the three
    potassium phosphates the patent means, and no lookup of the bare name can.
    """
    t = s.replace("\u00b7", ".").strip()
    if not t or " " in t or not re.fullmatch(r"[A-Za-z0-9()\[\].]+", t):
        return None
    if not t[0].isupper():
        return None
    counts: dict[str, int] = {}
    pos = 0
    for m in _ELEMENT.finditer(t):
        if m.start() != pos:
            return None
        pos = m.end()
        counts[m.group(1)] = counts.get(m.group(1), 0) + int(m.group(2) or 1)
    return counts if pos == len(t) and counts else None


def element_counts(smiles: str) -> dict[str, int] | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    mol = Chem.AddHs(mol)
    out: dict[str, int] = {}
    for a in mol.GetAtoms():
        out[a.GetSymbol()] = out.get(a.GetSymbol(), 0) + 1
    return out

RANK = {"patent_scheme": 0, "curated": 1, "patent_drawing": 2,
        "known": 3, "opsin": 4, "pubchem": 5}

SALT_NAME = re.compile(r"(ate|ite|oxide|ide)$", re.I)

# A name built out of locants and nomenclature, which is what OPSIN is for.
SYSTEMATIC = re.compile(r"\d+[-,]|[-\[(]\d|\byl\b|oxy\w|\bN-|\bO-|\bS-")


def has_charge(smiles: str) -> bool:
    mol = Chem.MolFromSmiles(smiles)
    return bool(mol) and any(a.GetFormalCharge() for a in mol.GetAtoms())


def adjudicate(identifier: str, answers: dict[str, str],
               alias_formulas: list[str] | None = None) -> tuple[str, str, str]:
    """(smiles, source, reason) when the readers disagree.

    Every branch states a rule, and the rule goes on the report. An adjudication
    nobody can re-check later is just a preference.
    """
    by_canon: dict[str, list[str]] = {}
    for src, smi in answers.items():
        by_canon.setdefault(canon(smi), []).append(src)

    n = normalise(identifier)
    base = DIATOMIC_ALIAS.get(n.replace(" ", ""), n)
    if base in DIATOMIC:
        want = canon(DIATOMIC[base])
        src = sorted(by_canon.get(want, ["known"]), key=lambda s: RANK.get(s, 9))[0]
        return DIATOMIC[base], src, (
            f"diatomic element: a patent charges {base} as the molecule, not the "
            f"atom. The single-atom reading halves the molecular weight.")

    # The record's OWN alias settles it. `potassium phosphate` is three different
    # salts and the gold carries `K3PO4` beside it, which says which one. That is
    # evidence from this document, so it outranks anything either lookup returned.
    for al in alias_formulas or []:
        want = as_formula(al)
        if not want:
            continue
        for src in sorted(answers, key=lambda s: RANK[s]):
            if element_counts(answers[src]) == want:
                return answers[src], src, (
                    f"the record's own alias {al!r} is a formula, and only {src} "
                    f"returned a structure with those atoms.")

    # Two readers against one. Nothing about the ranking, just arithmetic: when
    # `known` and OPSIN both say brine is [Na+].[Cl-] and PubChem adds the water it
    # is dissolved in, the two that agree are the answer.
    best = max(by_canon.values(), key=len)
    if len(best) > 1 and sum(1 for v in by_canon.values() if len(v) == len(best)) == 1:
        src = sorted(best, key=lambda s: RANK[s])[0]
        losers = [s for s in answers if s not in best]
        return answers[src], src, (
            f"{len(best)} readers agree ({', '.join(sorted(best))}) against "
            f"{', '.join(losers)}. Majority, and the agreeing readers are unrelated.")

    # A reading of THIS document beats any lookup of a name, because the lookup does
    # not know which of several things sharing a name the patent drew.
    for strong in ("curated", "patent_drawing"):
        if strong in answers:
            others = [s for s in answers if s != strong]
            return answers[strong], strong, (
                f"{strong} is a reading of this patent; "
                f"{', '.join(others)} looked the name up without seeing it.")

    # Same formula, different convention. Ionic [O-2].[Mg+2] and covalent O=[Mg] are
    # one substance, and neither reader is wrong. Keep OPSIN's, which is explicit
    # about charge, and say that nothing was actually in dispute.
    formulas = {formula_of(s) for s in answers.values()}
    if len(formulas) == 1 and None not in formulas:
        src = sorted(answers, key=lambda s: RANK[s])[0]
        return answers[src], src, (
            f"same molecular formula {formulas.pop()}, written ionic by one reader and "
            f"covalent by the other. One substance, not a disagreement. Kept {src}.")

    # An -ate, -ite or -oxide name IS the anion. PubChem routinely indexes the free
    # acid or the neutral metal under the salt's name (`sodium tert-butoxide` comes
    # back as tert-butanol plus sodium metal), which is a different substance with a
    # different formula, one proton heavier.
    if SALT_NAME.search(n):
        charged = {s: v for s, v in answers.items() if has_charge(v)}
        if len(charged) == 1:
            src = next(iter(charged))
            return answers[src], src, (
                f"the name ends in an anion suffix, so the substance is the salt. "
                f"Kept {src}, the only reader that returned the charged form; the "
                f"others returned the neutral acid or metal.")

    # PubChem matches a NAME loosely. Asked for `3-oxo-1-cyclohexen-1-yl
    # 2-chloro-3-(2,2,2-trifluoroethoxy)methyl-4-methylsulfonylbenzoate` it returns
    # trifluoroethanol, a fragment of one substituent. On a name built out of
    # locants, a grammar that derived the whole structure beats a lookup that
    # matched part of the string.
    if SYSTEMATIC.search(identifier) and "opsin" in answers and "pubchem" in answers:
        return answers["opsin"], "opsin", (
            "the name is systematic and OPSIN derived the whole structure from it. "
            "PubChem's name match is loose and returned a different molecule.")

    src = sorted(answers, key=lambda s: RANK[s])[0]
    return answers[src], src, (
        f"readers disagree and no rule settles it. Kept {src} by precedence. "
        f"NEEDS A HUMAN.")


# ---------------------------------------------------------------- the resolution

def resolve_all(identifiers: list[str], aliases: dict[str, list[str]],
                run: Path, offline: bool) -> tuple[dict, list, list]:
    english = load_english(run)
    curated, drawn = read_local_evidence(run)
    opsin = Opsin(run / "input" / "opsin-cache-local.json", offline)
    pubchem = PubChem(run / "input" / "pubchem-cache.json", offline)

    plan = {i: query_forms(i, aliases.get(i, []), english) for i in identifiers}
    # A STRUCTURE ON THE RECORD BEATS ANY READING OF ITS NAME. WO2024109718A1
    # carries `compound of formula (I)` with the alias `CSc1ccc(Br)c(Cl)c1C`: the
    # name is Markush and the record is not, because the annotation wrote down
    # which member of the family this row is. Eight records, and classifying them
    # from the name alone threw away the answer the gold had already given.
    why_not = {i: (None if any(looks_like_smiles(q) for q in plan[i])
                   else no_structure_reason(i, plan[i]))
               for i in identifiers}
    askable = [q for i, qs in plan.items() if not why_not[i] for q in qs]
    opsin.warm(askable)

    resolved: dict[str, dict] = {}
    disputes: list[dict] = []
    unresolved: list[dict] = []

    for ident in identifiers:
        why = why_not[ident]
        if why:
            resolved[ident] = {"smiles": None, "smiles_source": why,
                               "molecular_formula": None, "molecular_weight": None}
            continue

        answers: dict[str, str] = {}
        used: dict[str, str] = {}
        notes: list[str] = []
        # The identifier IS a SMILES. 10 of WO2024109718A1's rows are the drawn
        # scheme's structures used as their own name, and asking a name parser
        # about one is meaningless. Nothing outranks it: the string is the answer.
        for q in plan[ident]:
            if looks_like_smiles(q):
                answers["patent_scheme"], used["patent_scheme"] = q, q
                break
        # An element in its standard state, or a species from the hand-checked
        # table. OPSIN parses `bromine` to a single ATOM and PubChem is never asked
        # about `Br2`, so without this the commonest reagents have no reader at all.
        for q in plan[ident]:
            hit = known_species(q)
            if hit:
                answers["known"], used["known"] = hit, q
                break
        for q in plan[ident]:
            nq = normalise(q)
            for src, smi in (("curated", curated.get(nq)), ("patent_drawing", drawn.get(nq))):
                if smi and src not in answers:
                    answers[src], used[src] = smi, q
            if "opsin" not in answers:
                smi, opsin_says = opsin.ask(q)
                if smi:
                    answers["opsin"], used["opsin"] = smi, q
                elif opsin_says.startswith("ambiguous"):
                    notes.append(opsin_says)
            if "pubchem" not in answers:
                smi, _ = pubchem.ask(q)
                if smi:
                    answers["pubchem"], used["pubchem"] = smi, q
            if len(answers) >= 2 and len({canon(s) for s in answers.values()}) == 1:
                break                       # two unrelated readers already agree

        # OPSIN's own parse of a name may also match a structure DRAWN in the patent
        # even when the two are spelled differently. That is a real second witness
        # and a name join would never find it.
        if "opsin" in answers and "patent_drawing" not in answers:
            target = canon(answers["opsin"])
            for name, smi in drawn.items():
                if canon(smi) == target:
                    answers["patent_drawing"], used["patent_drawing"] = smi, name
                    break

        answers = {k: v for k, v in answers.items() if canon(v)}
        if not answers:
            reason = "none:ambiguous" if any(n.startswith("ambiguous") for n in notes) \
                else "none:unresolved"
            resolved[ident] = {"smiles": None, "smiles_source": reason,
                               "molecular_formula": None, "molecular_weight": None}
            if reason == "none:unresolved":
                unresolved.append({"identifier": ident, "tried": plan[ident][:4]})
            continue

        distinct = {canon(s) for s in answers.values()}
        if len(distinct) == 1:
            src = sorted(answers, key=lambda s: RANK[s])[0]
            smiles, source = answers[src], "+".join(sorted(answers, key=lambda s: RANK[s]))
            reason = ""
        else:
            smiles, src, reason = adjudicate(
                ident, answers, [ident, *aliases.get(ident, [])])
            source = src
            disputes.append({
                "identifier": ident,
                "answers": {k: canon(v) for k, v in answers.items()},
                "chosen": canon(smiles), "chosen_source": src, "reason": reason,
                "needs_human": "NEEDS A HUMAN" in reason,
            })

        entry = describe(smiles)
        entry["smiles_source"] = source
        entry["_witnesses"] = len(answers)
        entry["_queried"] = used
        entry["_reason"] = reason
        resolved[ident] = entry

    opsin.save()
    pubchem.save()
    return resolved, disputes, unresolved


# ------------------------------------------------------------------- the writing

FIELDS = ("smiles", "smiles_source", "molecular_formula", "molecular_weight")


def public(entry: dict) -> dict:
    return {k: entry.get(k) for k in FIELDS}


def collect(run: Path) -> tuple[list[str], dict[str, list[str]]]:
    """Every identifier the three artifacts name, and the aliases each carries."""
    idents: list[str] = []
    aliases: dict[str, list[str]] = {}

    def note(ident, al=None):
        if not ident:
            return
        if ident not in aliases:
            idents.append(ident)
            aliases[ident] = []
        for a in al or []:
            if a and a not in aliases[ident]:
                aliases[ident].append(a)

    out = run / "output"
    for c in json.loads((out / "compounds.json").read_text(encoding="utf-8")):
        note(c.get("identifier"), c.get("aliases"))
    for r in json.loads((out / "reactions.json").read_text(encoding="utf-8")):
        note(r.get("product_name"))
        for name in r.get("reactant_names") or []:
            note(name)
        for c in r.get("compounds") or []:
            note(c.get("identifier"))
    p = out / "pathways.json"
    if p.exists():
        for pw in json.loads(p.read_text(encoding="utf-8")):
            for ref in [pw.get("ksm"), pw.get("product"), *(pw.get("intermediates") or [])]:
                if ref:
                    note(ref.get("identifier"))
    return idents, aliases


def write_artifacts(run: Path, resolved: dict, check: bool) -> tuple[dict, list]:
    out = run / "output"
    counts = {"compounds": [0, 0], "reaction_participants": [0, 0],
              "reaction_products": [0, 0], "pathway_refs": [0, 0]}

    def fill(record: dict, ident: str, bucket: str) -> None:
        counts[bucket][1] += 1
        entry = resolved.get(ident) or {}
        owner = by_alias.get(ident) if bucket != "compounds" else None
        if owner and canon(owner.get("smiles")) != canon(entry.get("smiles")):
            inherited.append({"identifier": ident, "from": owner["identifier"],
                              "was": entry.get("smiles"), "now": owner["smiles"]})
            entry = {k: owner.get(k) for k in FIELDS}
        record.update(public(entry))
        if entry.get("smiles"):
            counts[bucket][0] += 1

    compounds = json.loads((out / "compounds.json").read_text(encoding="utf-8"))
    for c in compounds:
        fill(c, c.get("identifier"), "compounds")

    # compounds.json is the naming authority. pathways.json was built against an
    # older read and spells 117 of WO2024109718A1's 173 references differently, for
    # the same molecules: `methyl 2-chloro-3-bromomethyl-4-methylsulfonylbenzoate`
    # against `methyl 2-chloro-3-(bromomethyl)-4-(methanesulfonyl)benzoate`. Both
    # parse to one structure, so the join is on CANONICAL SMILES and never on the
    # string, and the compound_uuid moves with the name so the record does not end
    # up naming one compound and pointing at another.
    authority: dict[str, dict] = {}
    for c in compounds:
        keys = [canon((resolved.get(c.get("identifier")) or {}).get("smiles"))]
        # and every alias that is itself a structure, which is how this gold
        # records the concrete member behind a formula label
        keys += [canon(a) for a in (c.get("aliases") or []) if looks_like_smiles(a)]
        for key in keys:
            if key and key not in authority:
                authority[key] = c
    known = {c.get("identifier") for c in compounds}

    # compounds.json is the authority, so a row elsewhere that uses one of its
    # ALIASES is that compound and takes its structure. PubChem answers
    # `bis(dibenzylideneacetone)palladium` with Pd2(dba)3 at 915.73 and
    # `bis(dibenzylideneacetone)palladium(0)` with Pd(dba)2 at 575.02, and this
    # patent prints Pd(dba)2. Both spellings appear in reactions.json, so without
    # this one reagent carried two masses 341 g/mol apart.
    by_alias: dict[str, dict] = {}
    for c in compounds:
        for a in c.get("aliases") or []:
            if a and a not in known and a not in by_alias and c.get("smiles"):
                by_alias[a] = c
    inherited: list[dict] = []

    # A Markush reference has no structure, so the SMILES join above cannot reach
    # it, and 58 of WO2024109718A1's pathway references are the Chinese for one:
    # 式(I)化合物 is `compound of formula (I)`, which compounds.json carries under
    # exactly that English name. Joined on the formula LABEL, and on whether the
    # reference says 酯 (ester), because the gold distinguishes
    # `compound of formula (VIII)` from `ester compound of formula (VIII)`.
    by_label: dict[tuple[str, bool], dict] = {}
    for c in compounds:
        m = re.search(r"formula\s*\(?([A-Za-z0-9]+)\)?\s*$", c.get("identifier", ""))
        if m:
            by_label.setdefault((m.group(1).upper(),
                                 "ester" in c["identifier"].lower()), c)

    reactions = json.loads((out / "reactions.json").read_text(encoding="utf-8"))
    for r in reactions:
        for c in r.get("compounds") or []:
            fill(c, c.get("identifier"), "reaction_participants")
        prod = (resolved.get(r.get("product_name")) or {}).get("smiles")
        counts["reaction_products"][1] += 1
        if prod:
            counts["reaction_products"][0] += 1
        r["product_smiles"] = prod
        r["product_smiles_source"] = (resolved.get(r.get("product_name")) or {}).get("smiles_source")
        # Reactants only, joined the way a reaction SMILES joins them. Reagents,
        # catalysts and solvents are deliberately out: they are not on the left of
        # the arrow in any reaction SMILES convention.
        parts = [(resolved.get(c.get("identifier")) or {}).get("smiles")
                 for c in (r.get("compounds") or []) if c.get("role") == "reactant"]
        parts = [p for p in parts if p]
        r["reactant_smiles"] = ".".join(parts) or None
        r["smiles_source"] = "joined_from_participants" if parts else None
        r["canonical_rxn"] = f"{'.'.join(parts)}>>{prod}" if parts and prod else None

    pathways, renames = None, []
    p = out / "pathways.json"
    if p.exists():
        pathways = json.loads(p.read_text(encoding="utf-8"))
        for pw in pathways:
            for ref in [pw.get("ksm"), pw.get("product"), *(pw.get("intermediates") or [])]:
                if not ref:
                    continue
                ident = ref.get("identifier")
                key = canon((resolved.get(ident) or {}).get("smiles"))
                target = None
                if ident not in known and key in authority:
                    target = authority[key]
                elif ident not in known:
                    m = re.search(r"[(（]?([IVXivx]+|[A-Z])[)）]?\s*(酯)?化合物", ident)
                    if m:
                        label = m.group(1).upper()
                        target = by_label.get((label, bool(m.group(2))))
                        # 式(VIII)化合物 omits the 酯 that `ester compound of formula
                        # (VIII)` carries, and that label has only the one record.
                        # Falling back is safe exactly while that stays true.
                        if target is None:
                            same = [c for (lab, _), c in by_label.items() if lab == label]
                            target = same[0] if len(same) == 1 else None
                # compounds.json is the authority for the name, so it is the
                # authority for the uuid that goes with it. Two of this patent's
                # references named one compound and pointed at another's uuid,
                # which no consumer joining on uuid could survive. Pre-existing:
                # 11 references at 92bdc9a, before any of this ran.
                if target is None and ident in known:
                    c = next(x for x in compounds if x["identifier"] == ident)
                    if c.get("compound_uuid") and ref.get("compound_uuid") != c["compound_uuid"]:
                        renames.append({"was": ident, "now": ident,
                                        "molecule": "uuid corrected to the "
                                                    "compounds.json record for this name"})
                        ref["compound_uuid"] = c["compound_uuid"]
                if target:
                    renames.append({"was": ident, "now": target["identifier"],
                                    "molecule": key or "no structure, joined on the "
                                                       "formula label"})
                    ref["identifier"] = ident = target["identifier"]
                    ref["compound_uuid"] = target.get("compound_uuid")
                fill(ref, ident, "pathway_refs")

    if not check:
        dump = lambda obj: json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
        (out / "compounds.json").write_text(dump(compounds), encoding="utf-8")
        (out / "reactions.json").write_text(dump(reactions), encoding="utf-8")
        if pathways is not None:
            p.write_text(dump(pathways), encoding="utf-8")
    return counts, renames, inherited


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--patent-id")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--check", action="store_true", help="resolve and report, write nothing")
    ap.add_argument("--offline", action="store_true", help="caches only, never the network")
    a = ap.parse_args()

    if not a.patent_id and not a.all:
        return ap.error("give --patent-id or --all")
    ids = ([a.patent_id] if a.patent_id else
           sorted(d.name for d in (REPO / "runs").iterdir()
                  if (d / "output" / "compounds.json").exists()))

    for pid in ids:
        run = REPO / "runs" / pid
        print(f"\n{'=' * 72}\n{pid}\n{'=' * 72}")
        idents, aliases = collect(run)
        print(f"{len(idents)} distinct identifiers across compounds, reactions and pathways")

        resolved, disputes, unresolved = resolve_all(idents, aliases, run, a.offline)
        counts, renames, inherited = write_artifacts(run, resolved, a.check)

        got = sum(1 for e in resolved.values() if e.get("smiles"))
        wit = {}
        for e in resolved.values():
            if e.get("smiles"):
                wit[e.get("_witnesses", 1)] = wit.get(e.get("_witnesses", 1), 0) + 1
        reasons: dict[str, int] = {}
        for e in resolved.values():
            if not e.get("smiles"):
                reasons[e["smiles_source"]] = reasons.get(e["smiles_source"], 0) + 1

        print(f"  resolved {got}/{len(idents)} identifiers")
        for n in sorted(wit, reverse=True):
            label = "independent readers agreed" if n > 1 else "reader only, unconfirmed"
            print(f"      {wit[n]:4d}  {n} {label}")
        print("  no structure, by reason:")
        for k in sorted(reasons, key=lambda k: -reasons[k]):
            print(f"      {reasons[k]:4d}  {k}")
        print("  records filled:")
        for k, (g, t) in counts.items():
            print(f"      {k:24s} {g:5d}/{t:<5d} {100 * g / t if t else 0:5.1f}%")
        if unresolved:
            print("  a specific molecule that no reader here could find:")
            for u in unresolved:
                print(f"      {u['identifier'][:88]}")
        for d in disputes:
            print(f"  DISAGREE  {d['identifier']}")
            for src, smi in d["answers"].items():
                print(f"      {src:15s} {smi}")
            print(f"      -> kept {d['chosen_source']}: {d['reason']}")
        for i in inherited:
            print(f"  ALIAS  {i['identifier']!r} takes the structure of "
                  f"{i['from']!r}: {i['was']} -> {i['now']}")
        if renames:
            print(f"  {len(renames)} pathway reference(s) renamed to the compounds.json "
                  f"spelling, joined on canonical SMILES "
                  f"({len({r['now'] for r in renames})} distinct molecules)")
        if disputes:
            print(f"  {len(disputes)} disagreement(s) adjudicated, "
                  f"{sum(1 for d in disputes if d['needs_human'])} need a human")

        report = {"patent_id": pid, "identifiers": len(idents), "resolved": got,
                  "witnesses": wit, "no_structure": reasons, "records": counts,
                  "disagreements": disputes, "unresolved": unresolved,
                  "pathway_renames": renames,
                  "alias_inherited": inherited,
                  "readers": ["curated (human, this patent)",
                              "patent_drawing (vision pass, this patent)",
                              "opsin (OPSIN 2.9.0, pipeline/vendor/)",
                              "pubchem (PUG-REST)"]}
        if not a.check:
            (run / "output" / "structures-enrichment.json").write_text(
                json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
