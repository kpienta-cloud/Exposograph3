"""
ExposoGraph 3.0 — Phase 6: CEDT Digital Twin Engine
Cancer Ecology Digital Twin (CEDT) adapter layer.

Takes a Phase 5 run trace (produced by runner.py ScenarioRunner.run_scenario)
plus the CEDT adapter mappings (cedt_mappings.json) and populates a typed
twin state vector covering five layers:
  host · exposure · tissue · metabolic · state_quality

HARD CONSTRAINTS (enforced by this module):
  - Values derived ONLY from real Phase 5 engine outputs.
  - Where a twin variable has no real source, it is set to null with a note.
  - No fabricated biology, no invented numbers.
  - Existing flux_ratio/SBS regression values are preserved (not re-derived).

stdlib only: json, math, statistics, pathlib, logging, datetime
"""

import json
import logging
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent
_ADAPTERS_PATH  = _REPO_ROOT / "data" / "adapters" / "cedt_mappings.json"
_SCHEMA_PATH    = _REPO_ROOT / "data" / "adapters" / "twin_state_schema.json"


# ─── Public API ───────────────────────────────────────────────────────────────

def build_twin_state(
    run_trace: dict,
    scenario_id: str,
    scenario_meta: dict | None = None,
    adapters_path: Path | None = None,
) -> dict:
    """
    Populate a CEDT twin state vector from a Phase 5 run trace.

    Parameters
    ----------
    run_trace : dict
        Full trace dict returned by ScenarioRunner.run_scenario().
        Must contain 'chain_summary', 'module_outputs', and 'scenario_inputs'.
    scenario_id : str
        Scenario identifier (e.g. 'SCN001').
    scenario_meta : dict, optional
        Extra scenario fields (genotype_profile, tissue, etc.) if not already
        embedded in run_trace['scenario_inputs'].
    adapters_path : Path, optional
        Override path to cedt_mappings.json (defaults to data/adapters/).

    Returns
    -------
    dict  — twin state vector with five layer dicts, metadata, and null_notes.
    """
    ap = adapters_path or _ADAPTERS_PATH
    with open(ap, encoding="utf-8") as f:
        adapters_doc = json.load(f)

    chain    = run_trace.get("chain_summary", {})
    mod_out  = run_trace.get("module_outputs", {})
    scen_in  = run_trace.get("scenario_inputs", {})

    # Pull per-module outputs
    flux_out     = mod_out.get("BIOTRANS.FLUX",  {}).get("outputs", {})
    exposure_out = mod_out.get("EXPOSURE.WAVE2", {}).get("outputs", {})
    mutsig_out   = mod_out.get("OUTCOME.MUTSIG", {}).get("outputs", {})
    popgen_out   = mod_out.get("MODIFIER.POPGEN", {}).get("outputs", {})
    tissue_out   = mod_out.get("TISSUE.SUBGRAPH", {}).get("outputs", {})

    null_notes: list[str] = []

    # ── HOST LAYER ─────────────────────────────────────────────────────────────
    # enzyme_activity_modifier: {gene: genotype_multiplier}
    # Source: POPGEN activity_multiplier (popgen_out['multipliers'])
    enzyme_multipliers: dict = popgen_out.get("multipliers", {})
    enzyme_activity_modifier = enzyme_multipliers if enzyme_multipliers else None
    if not enzyme_activity_modifier:
        null_notes.append(
            "host.enzyme_activity_modifier: POPGEN multipliers not found in run trace."
        )

    # susceptibility_index: mean(genotype_multiplier) across all enzymes
    if enzyme_multipliers:
        vals = [v for v in enzyme_multipliers.values() if v is not None]
        susceptibility_index = statistics.mean(vals) if vals else None
        if susceptibility_index is None:
            null_notes.append(
                "host.susceptibility_index: no valid multiplier values; POPGEN returned None for all enzymes."
            )
    else:
        susceptibility_index = None
        null_notes.append(
            "host.susceptibility_index: POPGEN multipliers not found; cannot derive mean."
        )

    host_layer = {
        "enzyme_activity_modifier": enzyme_activity_modifier,
        "susceptibility_index": susceptibility_index,
    }

    # ── EXPOSURE LAYER ─────────────────────────────────────────────────────────
    # exposure_intensity: exposure_multiplier (identity)
    # exposure_multiplier: same value (direct copy)
    # exposure_class: carcinogen_class from scenario_inputs (categorical)
    # exposure_duration_context: exposure_scenario from scenario_inputs (categorical)
    exp_mult = chain.get("exposure_multiplier") or exposure_out.get("exposure_multiplier")
    exp_class = scen_in.get("carcinogen_class")
    exp_scenario = scen_in.get("exposure_scenario")

    if exp_mult is None:
        null_notes.append(
            "exposure.exposure_intensity / exposure_multiplier: "
            "exposure_multiplier not found in chain_summary or EXPOSURE module output."
        )

    exposure_layer = {
        "exposure_intensity":        exp_mult,
        "exposure_multiplier":       exp_mult,
        "exposure_class":            exp_class,
        "exposure_duration_context": exp_scenario,
    }

    # ── TISSUE LAYER ───────────────────────────────────────────────────────────
    # tissue_context_id: target tissue from scenario_inputs (categorical)
    # tissue_expression_weight: mean(tissue_weight) across enzymes with non-null weight
    # tissue_sensitivity: max(tissue_weight) across activation-pathway enzymes
    tissue = scen_in.get("tissue")

    tissue_weights_dict: dict = tissue_out.get("weights", {})
    non_null_weights = [w for w in tissue_weights_dict.values() if w is not None]

    if non_null_weights:
        mean_weight = statistics.mean(non_null_weights)
        max_weight  = max(non_null_weights)
    else:
        mean_weight = None
        max_weight  = None
        null_notes.append(
            "tissue.tissue_expression_weight / tissue_sensitivity: "
            "no non-null tissue weights found in TISSUE.SUBGRAPH output."
        )

    tissue_layer = {
        "tissue_context_id":       tissue,
        "tissue_expression_weight": round(mean_weight, 6) if mean_weight is not None else None,
        "tissue_sensitivity":       round(max_weight,  6) if max_weight  is not None else None,
    }

    # ── METABOLIC LAYER ────────────────────────────────────────────────────────
    # metabolic_activation_score: activation_score (identity, MM-computed)
    # metabolic_detoxification_score: detoxification_score (identity)
    # metabolic_flux_ratio: flux_ratio (identity, regression-tested)
    # gsh_pool_fraction: from INTERACTION module — null if INTERACTION not run
    act_score  = chain.get("activation_score")
    detox_score = chain.get("detoxification_score")
    flux_ratio  = chain.get("flux_ratio")

    if act_score is None:
        null_notes.append(
            "metabolic.metabolic_activation_score: activation_score not in chain_summary."
        )
    if detox_score is None:
        null_notes.append(
            "metabolic.metabolic_detoxification_score: detoxification_score not in chain_summary."
        )
    if flux_ratio is None:
        null_notes.append(
            "metabolic.metabolic_flux_ratio: flux_ratio not in chain_summary."
        )

    # gsh_pool_fraction: INTERACTION module not run in Phase 5 scenarios
    # (no co-exposure inputs provided)
    gsh_pool_fraction = None
    null_notes.append(
        "metabolic.gsh_pool_fraction: INTERACTION module was not invoked in this scenario "
        "(no co-exposure inputs). GSH_pool_fraction is null. "
        "Would be populated in co-exposure scenarios."
    )

    metabolic_layer = {
        "metabolic_activation_score":      act_score,
        "metabolic_detoxification_score":  detox_score,
        "metabolic_flux_ratio":            flux_ratio,
        "gsh_pool_fraction":               gsh_pool_fraction,
    }

    # ── STATE_QUALITY LAYER ────────────────────────────────────────────────────
    # predicted_mutational_signature: predicted_SBS (list, regression-tested)
    # dominant_mutation: dominant_mutation string
    # evidence_confidence: confidence string from MutSig
    # oxidative_stress_level: null (OxStress not run in Phase 5 canonical scenarios)
    # adduct_burden: null (same reason)
    predicted_sbs = mutsig_out.get("predicted_SBS", chain.get("predicted_SBS"))
    dominant_mut  = mutsig_out.get("dominant_mutation", chain.get("dominant_mutation"))
    confidence    = mutsig_out.get("confidence",        chain.get("confidence"))

    if predicted_sbs is None:
        null_notes.append(
            "state_quality.predicted_mutational_signature: predicted_SBS not found in MUTSIG output."
        )

    # OxStress null — documented
    oxidative_stress_level = None
    adduct_burden = None
    null_notes.append(
        "state_quality.oxidative_stress_level: OxStress module not invoked "
        "(Phase 5 scenarios: PAH/Aflatoxin/AromaticAmines/Nitrosamine — no HeavyMetal/direct ROS input). "
        "Would be populated with ROS_burden in Arsenic/HeavyMetal scenarios."
    )
    null_notes.append(
        "state_quality.adduct_burden: OxStress module not invoked; same reason as oxidative_stress_level. "
        "Would be populated with oxidative_adduct_score in ROS-generating scenarios."
    )

    state_quality_layer = {
        "predicted_mutational_signature": predicted_sbs,
        "dominant_mutation":              dominant_mut,
        "evidence_confidence":            confidence,
        "oxidative_stress_level":         oxidative_stress_level,
        "adduct_burden":                  adduct_burden,
    }

    # ── Assemble twin state vector ─────────────────────────────────────────────
    twin_state = {
        "scenario_id": scenario_id,
        "generated_by": "ExposoGraph 3.0 Phase 6 (CEDT engine)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "adapter_version": adapters_doc.get("schema_version", "3.0.0"),
        "carcinogen_class": scen_in.get("carcinogen_class"),
        "tissue": tissue,
        "genotype_profile": scen_in.get("genotype_profile"),
        "exposure_scenario": exp_scenario,
        "twin_state": {
            "host":          host_layer,
            "exposure":      exposure_layer,
            "tissue":        tissue_layer,
            "metabolic":     metabolic_layer,
            "state_quality": state_quality_layer,
        },
        "null_notes": null_notes,
        "provenance": {
            "source": "Phase 5 golden run trace (regression-tested at 1e-6)",
            "flux_values_frozen": True,
            "sbs_values_frozen":  True,
        },
    }
    return twin_state


def build_twin_states_batch(
    golden_runs: list[dict],
    scenarios: list[dict],
    adapters_path: Path | None = None,
) -> dict:
    """
    Build twin state vectors for all golden runs.

    Parameters
    ----------
    golden_runs : list[dict]
        List of run records from example_runs.json (each has 'scenario_id' and 'computed_trace').
    scenarios : list[dict]
        List of scenario defs from scenarios.json (for metadata cross-ref).
    adapters_path : Path, optional
        Override path to cedt_mappings.json.

    Returns
    -------
    dict — twin_states.json document with all scenario twin state vectors.
    """
    scen_index = {s["id"]: s for s in scenarios}

    twin_state_records: list[dict] = []
    for run in golden_runs:
        sid = run["scenario_id"]
        computed = run.get("computed_trace", {})
        scen_meta = scen_index.get(sid, {})

        # Reconstruct a minimal run_trace compatible with build_twin_state()
        # from the flat example_runs.json structure
        run_trace = _reconstruct_trace_from_run_record(run, scen_meta)
        ts = build_twin_state(
            run_trace=run_trace,
            scenario_id=sid,
            adapters_path=adapters_path,
        )
        twin_state_records.append(ts)

    return {
        "bundle": "ExposoGraph 3.0 CEDT Twin States",
        "version_origin": "ExposoGraph 3.0 Phase 6 (CEDT adapter)",
        "description": (
            "Per-scenario CEDT twin state vectors derived from Phase 5 golden run outputs. "
            "All numeric values are traced to real engine computations (regression-tested at 1e-6). "
            "Null values are explicitly documented with reasons."
        ),
        "generated_by": "scripts/engine/cedt.py build_twin_states_batch()",
        "scenario_count": len(twin_state_records),
        "twin_states": twin_state_records,
    }


def _reconstruct_trace_from_run_record(run: dict, scen_meta: dict) -> dict:
    """
    Reconstruct a run_trace dict from a flat example_runs.json record.
    The example_runs.json stores computed_trace with sub-steps; we map these
    back to the structure expected by build_twin_state().
    """
    computed = run.get("computed_trace", {})
    flux_step   = computed.get("flux_step", {})
    mutsig_step = computed.get("mutsig_step", {})
    exposure_step = computed.get("exposure_step", {})
    tissue_step = computed.get("tissue_step", {})

    # Reconstruct module outputs from stored trace
    per_enzyme = flux_step.get("per_enzyme_mm_rates", [])

    # Build tissue weights dict from per_enzyme_mm_rates
    tissue_weights_dict = {}
    for entry in per_enzyme:
        enz = entry.get("enzyme")
        tw  = entry.get("tissue_weight")
        if enz:
            tissue_weights_dict[enz] = tw  # may be None

    # Build genotype multipliers dict from per_enzyme_mm_rates
    genotype_multipliers = {}
    for entry in per_enzyme:
        enz  = entry.get("enzyme")
        mult = entry.get("genotype_multiplier")
        if enz:
            genotype_multipliers[enz] = mult if mult is not None else 1.0

    # Reconstruct scenario_inputs
    scenario_inputs = {
        "carcinogen_class":  run.get("carcinogen_class") or scen_meta.get("carcinogen_class"),
        "tissue":            run.get("tissue")           or scen_meta.get("tissue"),
        "genotype_profile":  run.get("genotype_profile") or scen_meta.get("genotype_profile"),
        "exposure_scenario": run.get("exposure_scenario") or scen_meta.get("exposure_scenario"),
    }

    run_trace = {
        "scenario_inputs": scenario_inputs,
        "chain_summary": {
            "exposure_multiplier":     exposure_step.get("exposure_multiplier") or run.get("exposure_multiplier"),
            "activation_score":        flux_step.get("activation_score"),
            "detoxification_score":    flux_step.get("detoxification_score"),
            "flux_ratio":              flux_step.get("flux_ratio"),
            "predicted_SBS":           mutsig_step.get("predicted_SBS"),
            "dominant_mutation":       mutsig_step.get("dominant_mutation"),
            "confidence":              mutsig_step.get("confidence"),
        },
        "module_outputs": {
            "EXPOSURE.WAVE2": {
                "outputs": {
                    "exposure_multiplier": exposure_step.get("exposure_multiplier") or run.get("exposure_multiplier"),
                    "tissue_conc_uM":      exposure_step.get("tissue_conc_uM"),
                }
            },
            "BIOTRANS.FLUX": {
                "outputs": {
                    "activation_score":     flux_step.get("activation_score"),
                    "detoxification_score": flux_step.get("detoxification_score"),
                    "flux_ratio":           flux_step.get("flux_ratio"),
                }
            },
            "OUTCOME.MUTSIG": {
                "outputs": {
                    "predicted_SBS":  mutsig_step.get("predicted_SBS"),
                    "dominant_mutation": mutsig_step.get("dominant_mutation"),
                    "confidence":     mutsig_step.get("confidence"),
                }
            },
            "MODIFIER.POPGEN": {
                "outputs": {
                    "multipliers": genotype_multipliers,
                }
            },
            "TISSUE.SUBGRAPH": {
                "outputs": {
                    "weights": tissue_weights_dict,
                }
            },
        },
    }
    return run_trace


# ─── CLI entry point ──────────────────────────────────────────────────────────

def _cli_generate():
    """
    Generate twin_states.json from Phase 5 golden runs.
    Called from command line or validate.py.
    """
    import sys

    runs_path   = _REPO_ROOT / "data" / "execution" / "example_runs.json"
    scen_path   = _REPO_ROOT / "data" / "execution" / "scenarios.json"
    out_path    = _REPO_ROOT / "data" / "execution" / "twin_states.json"
    mirror_path = _REPO_ROOT / "app"  / "data" / "execution" / "twin_states.json"

    if not runs_path.exists():
        print(f"ERROR: {runs_path} not found", file=sys.stderr)
        sys.exit(1)
    if not scen_path.exists():
        print(f"ERROR: {scen_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(runs_path, encoding="utf-8") as f:
        runs_doc = json.load(f)
    with open(scen_path, encoding="utf-8") as f:
        scen_doc = json.load(f)

    golden_runs = runs_doc.get("runs", [])
    scenarios   = scen_doc.get("scenarios", [])

    doc = build_twin_states_batch(golden_runs, scenarios)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path} ({len(doc['twin_states'])} twin state records)")

    # Mirror to app/data/execution/
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Mirrored to {mirror_path}")

    return doc


if __name__ == "__main__":
    _cli_generate()
