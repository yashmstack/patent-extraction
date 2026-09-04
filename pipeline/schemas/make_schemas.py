#!/usr/bin/env python3
"""Emit JSON Schema for each artifact, so the pass output can be validated
mechanically rather than by eye.

Field names, nesting and enum vocabularies are transcribed from the Java records
in literatureiq-engine (core/model/persistent/) and the closed lists in
prompts/experiment-2/. Enrichment fields are intentionally absent: the annotation
must not produce them, so a schema that permitted them would not catch it.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

S = lambda: {"type": ["string", "null"]}
N = lambda: {"type": ["number", "null"]}
I = lambda: {"type": ["integer", "null"]}
B = lambda: {"type": ["boolean", "null"]}
ARR = lambda items: {"type": ["array", "null"], "items": items}
ENUM = lambda *v: {"type": ["string", "null"], "enum": [*v, None]}
def OBJ(props, required=(), extra=False):
    return {"type": ["object", "null"], "properties": props,
            "required": list(required), "additionalProperties": extra}

QUANTITY = OBJ({"mass_g": N(), "volume_ml": N(), "mmol": N(),
                "equivalents": N(), "yield_pct": N()})

ROLE = ENUM("product", "reactant", "reagent", "solvent", "catalyst", "ligand",
            "base", "acid", "oxidant", "reductant", "by_product", "additive",
            "drying_agent", "other")

ID_TYPE = ENUM("iupac", "smiles", "local_label", "functional_ref", "abbreviation",
               "formula", "trivial_name", "other")

SECTION_TYPE = ENUM("bibliographic", "abstract", "technical_field", "background",
                    "summary_of_invention", "beneficial_effects", "formula_definitions",
                    "description_of_drawings", "experimental_intermediate",
                    "experimental_example", "comparative_example", "assay_data",
                    "pharmaceutical_compositions", "claims", "search_report", "other")

REACTION_CLASS = ENUM(
    "suzuki_coupling", "heck_reaction", "buchwald_hartwig", "negishi_coupling",
    "sonogashira_coupling", "other_cross_coupling", "amide_bond_formation",
    "acylation", "ester_formation", "n_alkylation", "nucleophilic_substitution",
    "electrophilic_substitution", "halogenation", "n_oxidation", "oxidation",
    "reduction", "hydrolysis", "protection", "deprotection", "cyclisation",
    "elimination", "addition", "salt_formation", "resolution", "recrystallisation",
    "catalyst_preparation", "heterogeneous_catalysis", "formulation",
    "biological_assay", "other")

TAG = {"type": "string", "pattern": "^[a-z_]+:[a-z0-9_/.+-]+$"}

# Where a structure came from, or why there is not one. Written by
# enrich_structures.py, and constrained rather than free text because the whole
# value of the field is that a consumer can filter on it: `curated+patent_drawing`
# is two readings of this document agreeing, `pubchem` alone is one database and
# nobody else. `none:class_name` says no molecule exists to find, which is a
# different fact from `none:unresolved`, and a bare `none` would erase it.
READER = "patent_scheme|curated|patent_drawing|opsin|pubchem"
NO_STRUCTURE = "markush|reference|class_name|material|polymer|ambiguous|unresolved"
SMILES_SOURCE = {"type": ["string", "null"],
                 "pattern": rf"^(({READER})(\+({READER}))*|none:({NO_STRUCTURE})"
                            rf"|joined_from_participants)$"}
SMILES = {"type": ["string", "null"]}
FORMULA = {"type": ["string", "null"], "pattern": r"^[A-Za-z0-9+\-()\[\]]+$"}

# --------------------------------------------------------------- compounds
compound = OBJ({
    "id": S(), "patent_id": {"type": "string"},
    "identifier": {"type": "string"}, "identifier_type": ID_TYPE,
    "aliases": ARR({"type": "string"}), "resolved": B(),
    "unresolved_reference": B(),
    "section_label": S(), "section_type": SECTION_TYPE,
    "is_section_product": B(), "commercially_available": B(),
    "role": ROLE, "quantity": QUANTITY, "ms_mz": N(),
    "nmr": OBJ({"h1": S(), "c13": S(), "raw_text": S(), "solvent": S(),
                "frequency_mhz": N()}),
    "melting_point": OBJ({"min_c": N(), "max_c": N(), "range_text": S(),
                          "decomposition": B()}),
    "appearance": S(), "color": S(),
    "physical_form": ENUM("solid", "liquid", "gas", "gel", "resin", "oil",
                          "powder", "crystals", "other"),
    "analytics": ARR(OBJ({
        "method": ENUM("hplc", "gc", "ms", "nmr", "ir", "uv", "tlc", "elemental",
                       "xrd", "dsc", "tga", "boiling_point", "optical_rotation", "other"),
        "value": N(), "unit": S(), "conditions": S(), "raw_text": {"type": "string"}},
        required=["method", "raw_text"])),
    "purity_pct": N(),
    "purity_method": ENUM("hplc", "gc", "nmr", "uv", "titration", "other"),
    "compound_uuid": S(), "tags": ARR(TAG), "notes": S(),
    # These were pinned null while the artifacts were a scoring key, because a
    # SMILES is a lookup and not an extraction, so a reference carrying one would
    # grade the enrichment service instead of the extractor. The four patents in
    # goldenPatents are a GOLD DATASET now: a record that names a molecule and
    # cannot say which molecule is an incomplete record. Written by
    # enrich_structures.py, which puts the strength of the evidence in
    # smiles_source rather than leaving a bare string nobody can weigh.
    "smiles": SMILES, "smiles_source": SMILES_SOURCE,
    "molecular_formula": FORMULA, "molecular_weight": N(),
    # Still null. Nothing here computes an InChIKey, and a schema that permitted
    # one would stop catching the day something starts guessing at them.
    "inchi_key": {"type": "null"},
}, required=["patent_id", "identifier", "identifier_type", "role", "section_label"])

# --------------------------------------------------------------- reactions
conditions = OBJ({
    "temperature": OBJ({"type": ENUM("exact", "range", "room_temperature", "not_specified"),
                        "value_c": N(), "min_c": N(), "max_c": N()}),
    "pressure": OBJ({"type": ENUM("atmospheric", "reduced", "elevated", "vacuum",
                                  "not_specified"),
                     "value_kpa": N(), "qualitative_text": S()}),
    "atmosphere": S(), "time_h": N(), "reactor_type": S(),
    "concentration": OBJ({"value": N(), "unit": ENUM("M", "N", "%", "mol/L", "mg/mL"),
                          "reagent": S(), "text": S()}),
    "heating_method": S(), "cooling_method": S(),
    "light_source": OBJ({"type": ENUM("LED", "UV", "mercury_lamp", "sunlight",
                                      "tungsten", "fluorescent", "other"),
                         "color": S(), "wavelength_nm": N(), "power_w": N()}),
    "stirring": OBJ({"type": ENUM("magnetic", "mechanical", "overhead", "vortex",
                                  "shaker", "none"), "rpm": I()}),
    "ph_value": N(), "ph_target_stage": S()})

workup = OBJ({"steps": ARR({"type": "string"}), "quenching_agent": S(),
              "extraction_solvent": S(), "extraction_count": I(),
              "extraction_volume_ml": N(), "washes": ARR({"type": "string"}),
              "drying_agent": S(), "filtration": S(),
              "concentration_method": S(), "ph_target": N()})

rxn_compound = OBJ({
    "identifier": {"type": "string"}, "role": ROLE, "is_product": B(),
    "quantity": QUANTITY, "addition_profile": S(), "ms_mz": N(), "ms_type": S(),
    "purity_pct": N(), "purity_method": S(),
    # The participants are where the chemistry is: 1075 rows across the four gold
    # patents against 264 compound records. A mass balance is weighed here, so the
    # formula and weight belong on the row that carries mass_g and mmol.
    "smiles": SMILES, "smiles_source": SMILES_SOURCE,
    "molecular_formula": FORMULA, "molecular_weight": N(),
}, required=["identifier", "role"])

VALIDATION_FLAG = ENUM(
    "missing_product", "missing_reactant", "no_conditions", "no_procedure_summary",
    "cross_reference_unresolved", "conditions_unresolved", "a1_missing_compound",
    "mass_balance_implausible", "scale_discontinuity", "translation_conflict",
    "drawing_text_conflict", "reagent_drawn_not_written", "reagent_written_not_drawn",
    "route_attribution_unclear", "molar_mass_inconsistent")

reaction = OBJ({
    "id": S(), "patent_id": {"type": "string"},
    "reaction_id": {"type": "string"}, "reaction_uuid": S(),
    "section_label": S(), "section_type": SECTION_TYPE,
    "step_index": I(), "step_label": S(),
    "reaction_class": REACTION_CLASS,
    "reaction_class_confidence": ENUM("high", "medium", "low"),
    "named_reaction": S(),
    "mechanism_type": ENUM("radical", "ionic", "pericyclic", "photochemical",
                           "catalytic", "concerted", "not_determinable"),
    "scale": ENUM("micro", "lab", "pilot", "production", "not_specified"),
    "is_one_pot": B(), "one_pot_steps": ARR({"type": "string"}),
    "conditions": conditions, "conditions_inherited": B(),
    "workup": workup, "purification": S(),
    "process_control": OBJ({"method": S(), "target_compound": S(),
                            "threshold_pct": N(), "criterion": S()}),
    "byproduct_recovery": ARR(OBJ({"compound": S(), "mass_g": N(),
                                   "concentration_pct": N(),
                                   "recovery_method": S(), "reuse": S()})),
    "safety_notes": ARR({"type": "string"}), "molar_ratio_text": S(),
    "selectivity": OBJ({"regio": S(),
                        "stereo": OBJ({"type": ENUM("ee", "de", "dr", "syn/anti"),
                                       "value_pct": N()}),
                        "chemo": S()}),
    "compounds": ARR(rxn_compound),
    "reactant_names": ARR({"type": "string"}),
    "product_name": S(), "product_yield_pct": N(), "product_ms_mz": N(),
    "product_ms_type": S(), "product_purity_pct": N(), "product_purity_method": S(),
    "procedure_text": S(), "procedure_summary": S(),
    "precursor_step": S(), "linkage_confirmed": B(),
    "cross_reference_unresolved": B(), "non_synthetic": B(),
    "is_complete": B(), "validation_flags": ARR(VALIDATION_FLAG),
    "tags": ARR(TAG), "notes": S(),
    # `reactant_smiles` is the reactants only, dot-joined, and `canonical_rxn` is
    # reactants>>product. Reagents, catalysts and solvents are deliberately out of
    # both: no reaction SMILES convention puts them left of the arrow, and a
    # consumer that atom-maps this would be handed a mass balance that cannot close.
    "reactant_smiles": SMILES, "smiles_source": SMILES_SOURCE,
    "product_smiles": SMILES, "product_smiles_source": SMILES_SOURCE,
    "canonical_rxn": S(),
}, required=["patent_id", "reaction_id", "section_label", "step_index",
             "reaction_class", "compounds", "validation_flags"])

# --------------------------------------------------------------- pathways
cref = OBJ({"identifier": {"type": "string"}, "smiles": SMILES,
            "smiles_source": SMILES_SOURCE, "molecular_formula": FORMULA,
            "molecular_weight": N(), "compound_uuid": S()},
           required=["identifier"])

pathway = OBJ({
    "pathway_uuid": S(), "patent_id": {"type": "string"},
    "scope": ENUM("section", "patent"), "section_label": S(),
    "ksm": cref, "intermediates": ARR(cref), "product": cref,
    "steps": ARR(OBJ({"reaction_uuid": S(), "reaction_id": {"type": "string"},
                      "yield_pct": N(), "purity_pct": N(),
                      "components": ARR({"type": "string"}), "tags": ARR(TAG)},
                     required=["reaction_id"], extra=True)),
    "overall_yield_pct": N(), "overall_purity_pct": N(),
    "tags": ARR(TAG),
    "honest_uncertainty_flags": ARR({"type": "string"}),
    # Enrichment aggregates. Present on the Java record, so permitted here, but they
    # MUST be null: they are produced by the enrichment service, not by extraction,
    # and a reference carrying values would score the wrong component.
    **{k: {"type": "null"} for k in (
        "safety_score", "green_score", "feasibility_score", "cost_score",
        "yield_score", "byproduct_score", "confidence_score",
        "min_transformation_reaction_count", "min_common_literature_patent_count",
        "min_common_literature_journal_count", "all_steps_atom_map_confident")},
}, required=["patent_id", "scope", "ksm", "product", "steps"])

# --------------------------------------------------------------- patent
patent = OBJ({
    "patent_id": {"type": "string"}, "patent_uuid": S(), "title": S(),
    "abstract": S(), "language": S(),
    "bibliographic": OBJ({"publication_date": S(), "priority_date": S(),
                          "filing_date": S(), "grant_date": S(), "jurisdiction": S(),
                          "patent_type": S(), "legal_status": S(), "family_id": S(),
                          "ipc_codes": ARR({"type": "string"}),
                          "cpc_codes": ARR({"type": "string"})}),
    "parties": OBJ({"assignees": ARR(OBJ({"name": S(), "country": S(),
                                          "type": ENUM("multinational_corp", "sme",
                                                       "university", "government",
                                                       "individual", "consortium")})),
                    "inventors": ARR(OBJ({"name": S(), "country": S()})),
                    "examiners": ARR(OBJ({"name": S()}))}),
    "patent_summary": S(), "novelty_claims": S(),
    "key_examples": ARR({"type": "string"}),
    "extraction_rollup": OBJ({"reaction_count": I(), "compound_count": I(),
                              "pathway_count": I(),
                              "section_summary": {"type": ["object", "null"]},
                              "target_compounds": ARR(cref),
                              "key_starting_materials": ARR(cref),
                              "chemistry_focus": ARR({"type": "string"}),
                              "best_overall_yield_pct": N(),
                              "best_overall_yield_pathway_uuid": S(),
                              "scale_distribution": {"type": ["object", "null"]}}),
    "tags": ARR(TAG),
    "source_refs": OBJ({"patent_summary_doc_id": S(), "blob_root": S(),
                        "extracted_at": S(), "extractor_commit_sha": S()}),
    "honest_uncertainty_flags": ARR({"type": "string"}),
}, required=["patent_id"])

section = OBJ({
    "section_index": {"type": "integer"}, "section_label": {"type": "string"},
    "section_type": SECTION_TYPE, "start_line": {"type": "integer"},
    "end_line": {"type": "integer"}, "heading_text_zh": S(), "heading_text_en": S(),
    "contains_procedure": {"type": "boolean"}, "estimated_steps": {"type": "integer"},
    "notes": S()}, required=["section_index", "section_label", "section_type",
                             "start_line", "end_line", "contains_procedure"])

DOCS = {
    "sections.schema.json": ("00-sections.json - A0 output", {"type": "array", "items": section}),
    "compounds.schema.json": ("compounds.json - A1 output after finalise.py",
                              {"type": "array", "items": compound}),
    "reactions.schema.json": ("reactions.json - A2 output after finalise.py",
                              {"type": "array", "items": reaction}),
    "pathways.schema.json": ("pathways.json - A3 output after finalise.py",
                             {"type": "array", "items": pathway}),
    "patent.schema.json": ("patent.json - A4 output merged with biblio", patent),
}

for name, (title, body) in DOCS.items():
    doc = {"$schema": "https://json-schema.org/draft/2020-12/schema",
           "title": title, **body}
    (HERE / name).write_text(json.dumps(doc, indent=2))
    print(f"  {name:28} {len(json.dumps(doc))//1024 + 1} KB")
