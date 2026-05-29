#!/usr/bin/env python3
"""
Phase 2 helper: annotate every input_port and output_port in the 8 module JSONs
with dtype (referencing port_types.json type_id) and unit.
Preserves all existing fields; only ADDS dtype/unit where missing.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MODULES_DIR = REPO_ROOT / "data/modules"

# Map of (module_id, port_name) -> (dtype, unit)
# Derived from real port data and port_types vocabulary
PORT_DTYPE_MAP = {
    # ── EG3.MOD.BIOTRANS.FLUX.v1 ─────────────────────────────────────────────
    ("EG3.MOD.BIOTRANS.FLUX.v1", "substrate_conc_uM"):      ("concentration:uM", "uM"),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "enzyme_genotype"):        ("multiplier:genotype_activity", "dimensionless"),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "tissue"):                 ("category:tissue_name", None),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "carcinogen_class"):       ("category:carcinogen_class", None),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "activation_score"):       ("score:activation", "dimensionless"),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "detoxification_score"):   ("score:detoxification", "dimensionless"),
    ("EG3.MOD.BIOTRANS.FLUX.v1", "flux_ratio"):             ("score:flux_ratio", "dimensionless"),

    # ── EG3.MOD.EXPOSURE.WAVE2.v1 ────────────────────────────────────────────
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "carcinogen_class"):      ("category:carcinogen_class", None),
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "exposure_scenario"):     ("category:exposure_scenario", None),
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "genotype_context"):      ("map:genotype_context", None),
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "exposure_multiplier"):   ("multiplier:exposure", "dimensionless"),
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "tissue_conc_uM"):        ("concentration:uM", "uM"),
    ("EG3.MOD.EXPOSURE.WAVE2.v1", "daily_intake_ug_kg"):    ("concentration:daily_intake", "ug/kg/day"),

    # ── EG3.MOD.MECHANISM.INTERACTION.v1 ─────────────────────────────────────
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "substrate_concentrations"): ("map:substrate_concentrations", "uM"),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "enzyme_genotypes"):         ("map:enzyme_genotypes", None),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "inducer_context"):          ("category:inducer_context", None),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "adjusted_flux_ratios"):     ("map:flux_ratios", "dimensionless"),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "GSH_pool_fraction"):        ("fraction:GSH_pool", "dimensionless"),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "synergy_flag"):             ("flag:boolean", None),
    ("EG3.MOD.MECHANISM.INTERACTION.v1", "antagonism_flag"):          ("flag:boolean", None),

    # ── EG3.MOD.MECHANISM.OXSTRESS.v1 ────────────────────────────────────────
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "ROS_burden_score"):     ("score:ROS_burden", "dimensionless"),
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "metal_exposure"):       ("map:metal_exposure", "uM"),
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "GSH_pool_fraction"):    ("fraction:GSH_pool", "dimensionless"),
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "ROS_burden"):           ("score:ROS_burden", "dimensionless"),
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "oxidative_adduct_score"): ("score:oxidative_adduct", "dimensionless"),
    ("EG3.MOD.MECHANISM.OXSTRESS.v1", "repair_capacity_index"): ("score:repair_capacity", "dimensionless"),

    # ── EG3.MOD.MODIFIER.POPGEN.v1 ───────────────────────────────────────────
    ("EG3.MOD.MODIFIER.POPGEN.v1", "gene"):                ("category:gene_symbol", None),
    ("EG3.MOD.MODIFIER.POPGEN.v1", "genotype"):            ("multiplier:genotype_activity", "dimensionless"),
    ("EG3.MOD.MODIFIER.POPGEN.v1", "activity_multiplier"): ("multiplier:genotype_activity", "dimensionless"),

    # ── EG3.MOD.OUTCOME.MUTSIG.v1 ────────────────────────────────────────────
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "carcinogen_class"):        ("category:carcinogen_class", None),
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "flux_ratio"):              ("score:flux_ratio", "dimensionless"),
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "adduct_types"):            ("list:adduct_types", None),
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "predicted_SBS_signature"): ("signature:SBS", None),
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "dominant_mutation"):       ("category:dominant_mutation", None),
    ("EG3.MOD.OUTCOME.MUTSIG.v1", "confidence"):              ("category:confidence_level", None),

    # ── EG3.MOD.TISSUE.SUBGRAPH.v1 ───────────────────────────────────────────
    ("EG3.MOD.TISSUE.SUBGRAPH.v1", "gene"):                     ("category:gene_symbol", None),
    ("EG3.MOD.TISSUE.SUBGRAPH.v1", "tissue"):                   ("category:tissue_name", None),
    ("EG3.MOD.TISSUE.SUBGRAPH.v1", "tissue_expression_weight"): ("weight:tissue_expression", "dimensionless"),

    # ── EG3.MOD.EVIDENCE.PROVENANCE.v1 ───────────────────────────────────────
    ("EG3.MOD.EVIDENCE.PROVENANCE.v1", "enzyme"):            ("category:gene_symbol", None),
    ("EG3.MOD.EVIDENCE.PROVENANCE.v1", "substrate"):         ("category:substrate_id", None),
    ("EG3.MOD.EVIDENCE.PROVENANCE.v1", "provenance_record"): ("record:provenance", None),
}


def annotate_ports(ports, module_id):
    annotated = []
    for p in ports:
        port = dict(p)
        key = (module_id, port["name"])
        if key in PORT_DTYPE_MAP:
            dtype, unit = PORT_DTYPE_MAP[key]
            if "dtype" not in port:
                port["dtype"] = dtype
            if unit is not None and "unit" not in port:
                port["unit"] = unit
        annotated.append(port)
    return annotated


def main():
    for mf in sorted(MODULES_DIR.glob("*.json")):
        data = json.loads(mf.read_text(encoding="utf-8"))
        module_id = data.get("module_id", "")

        changed = False
        if "input_ports" in data:
            new_inputs = annotate_ports(data["input_ports"], module_id)
            if new_inputs != data["input_ports"]:
                data["input_ports"] = new_inputs
                changed = True

        if "output_ports" in data:
            new_outputs = annotate_ports(data["output_ports"], module_id)
            if new_outputs != data["output_ports"]:
                data["output_ports"] = new_outputs
                changed = True

        if changed:
            mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"  Annotated ports: {mf.name}")
        else:
            print(f"  No changes needed: {mf.name}")

    print("Done.")


if __name__ == "__main__":
    main()
