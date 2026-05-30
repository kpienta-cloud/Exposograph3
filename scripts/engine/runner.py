"""
ExposoGraph 3.0 — Phase 5 Reference Engine: Runner
stdlib only: json, math, logging

Loads data/ontology/wiring.json, topologically orders the 5 chain modules,
propagates outputs→inputs along the typed wiring connections, and exposes
run_scenario(canonical_class, tissue, genotype_profile, exposure_scenario)
-> trace dict.

Chain: EXPOSURE.WAVE2 → BIOTRANS.FLUX → OUTCOME.MUTSIG
       with FLUX modified by MODIFIER.POPGEN (genotype_multiplier)
       and TISSUE.SUBGRAPH (tissue_weight)

The three modules use DIFFERENT carcinogen-class vocabulary keys.
scripts/engine/aliases.py provides the canonical→(exposure, flux, mutsig) map
so each scenario resolves correctly without hard-coded per-scenario overrides.
"""

import json
import logging
from pathlib import Path

from scripts.engine.aliases import resolve as _resolve_class
from scripts.engine.modules import (
    ExposureWave2Module,
    PopgenModifierModule,
    TissueSubgraphModule,
    BiotransFluxModule,
    MutsigOutcomeModule,
    _enzyme_to_gene,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.parent
_WIRING_PATH = _REPO_ROOT / "data" / "ontology" / "wiring.json"


class ScenarioRunner:
    """
    Topologically ordered execution of the 5-module chain.
    Wiring connections define how outputs flow to inputs.
    Class-name aliasing is handled automatically via aliases.py.
    """

    def __init__(self):
        self.exposure = ExposureWave2Module()
        self.popgen   = PopgenModifierModule()
        self.tissue   = TissueSubgraphModule()
        self.flux     = BiotransFluxModule()
        self.mutsig   = MutsigOutcomeModule()

        with open(_WIRING_PATH, encoding="utf-8") as f:
            wiring_doc = json.load(f)
        self._wiring_connections = wiring_doc.get("connections", [])
        self._wiring_doc = wiring_doc

        # (from_module, from_port) → connection details
        self._wiring_index = {
            (c["from_module"], c["from_port"]): {
                "to_module": c["to_module"],
                "to_port":   c["to_port"],
                "dtype":     c["dtype"],
            }
            for c in self._wiring_connections
        }
        self._used_connections: set = set()

    def _note_wiring(self, from_module: str, from_port: str) -> bool:
        key = (from_module, from_port)
        if key in self._wiring_index:
            self._used_connections.add(key)
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    def run_scenario(
        self,
        carcinogen_class: str,
        tissue: str,
        genotype_profile: dict,
        exposure_scenario: str,
        # Optional overrides (still accepted for backwards-compat / explicit use)
        exposure_class:  str = None,
        mutsig_class:    str = None,
    ) -> dict:
        """
        Execute the full EXPOSURE→FLUX→MUTSIG chain.

        Parameters
        ----------
        carcinogen_class : str
            Canonical carcinogen class (e.g. "PAH", "Aflatoxin", "AromaticAmines",
            "TobaccoNitrosamines", "NDMA").  The alias map resolves the correct
            vocabulary key for each module automatically.
        tissue : str
            e.g. "Lung", "Liver", "Bladder", "Esophagus"
        genotype_profile : dict
            gene → phenotype, e.g. {"CYP1A1": "UM", "GSTM1": "null"}
        exposure_scenario : str
            Scenario key that must exist under the resolved EXPOSURE class,
            e.g. "smoker", "high_meat_well_done", "high_processed_meat".
        exposure_class : str, optional
            Override the EXPOSURE vocabulary key (skips alias resolution for EXPOSURE).
        mutsig_class : str, optional
            Override the MUTSIG vocabulary key (skips alias resolution for MUTSIG).

        Returns
        -------
        dict  — full trace with per-module inputs/outputs, MM rates, provenance.
        """
        # ── Resolve class aliases ─────────────────────────────────────────────
        keys = _resolve_class(carcinogen_class)
        _exposure_class = exposure_class if exposure_class is not None else keys.exposure
        _flux_class     = carcinogen_class  # canonical == flux key (already resolved)
        # BUT: when canonical differs from flux key we need to remap
        # e.g. "AromaticAmines" → flux key "HCA"
        _flux_class     = keys.flux
        _mutsig_class   = mutsig_class if mutsig_class is not None else keys.mutsig

        self._used_connections = set()
        trace: dict = {
            "scenario_inputs": {
                "carcinogen_class":  carcinogen_class,
                "tissue":            tissue,
                "genotype_profile":  genotype_profile,
                "exposure_scenario": exposure_scenario,
                "resolved_exposure_class": _exposure_class,
                "resolved_flux_class":     _flux_class,
                "resolved_mutsig_class":   _mutsig_class,
            },
            "wiring_connections_declared": self._wiring_connections,
            "module_outputs":    {},
            "chain_summary":     {},
            "wiring_connections_used": [],
            "all_provenance":    [],
            "missing_params":    [],
        }
        all_prov:    list[str] = []
        all_missing: list[str] = []

        # ── Step 1: EXPOSURE.WAVE2 ────────────────────────────────────────────
        exposure_inputs = {
            "carcinogen_class":  _exposure_class,
            "exposure_scenario": exposure_scenario,
        }
        exposure_out = self.exposure.run(exposure_inputs)
        all_prov.extend(exposure_out.get("provenance", []))
        trace["module_outputs"]["EXPOSURE.WAVE2"] = {
            "inputs":    exposure_inputs,
            "outputs":   exposure_out,
            "module_id": ExposureWave2Module.MODULE_ID,
        }

        # Wiring: EXPOSURE.tissue_conc_uM → FLUX.substrate_conc_uM
        self._note_wiring("EG3.MOD.EXPOSURE.WAVE2.v1", "tissue_conc_uM")
        substrate_conc_uM = exposure_out.get("tissue_conc_uM")
        if substrate_conc_uM is None:
            all_missing.append(
                f"EXPOSURE.tissue_conc_uM=None for "
                f"class={_exposure_class} scenario={exposure_scenario} — "
                f"check that the exposure_scenario key exists under this EXPOSURE class"
            )
            substrate_conc_uM = 0.0
            logger.warning(
                "Runner: tissue_conc_uM=None for %s/%s; forcing 0.0",
                _exposure_class, exposure_scenario
            )

        # ── Step 2: MODIFIER.POPGEN ───────────────────────────────────────────
        # Wiring: POPGEN.activity_multiplier → FLUX.enzyme_genotype
        self._note_wiring("EG3.MOD.MODIFIER.POPGEN.v1", "activity_multiplier")
        popgen_inputs = {"genotype_profile": genotype_profile}
        popgen_out    = self.popgen.run(popgen_inputs)
        all_prov.extend(popgen_out.get("provenance", []))
        genotype_multipliers: dict = popgen_out.get("multipliers", {})
        trace["module_outputs"]["MODIFIER.POPGEN"] = {
            "inputs":    popgen_inputs,
            "outputs":   popgen_out,
            "module_id": PopgenModifierModule.MODULE_ID,
        }
        # Replace any None multipliers with default NM=1.0
        for gene, mult in genotype_multipliers.items():
            if mult is None:
                genotype_multipliers[gene] = 1.0
                all_missing.append(
                    f"POPGEN: multiplier for {gene} was None; defaulted to 1.0 (NM)"
                )

        # ── Step 3: TISSUE.SUBGRAPH ───────────────────────────────────────────
        flux_class_params = self.flux.get_params_for_class(_flux_class)
        enzyme_names = [p.get("enzyme") for p in flux_class_params if p.get("enzyme")]
        gene_names = list({
            _enzyme_to_gene(e) for e in enzyme_names
            if _enzyme_to_gene(e) is not None
        })
        tissue_inputs = {"tissue": tissue, "enzymes": gene_names}
        tissue_out    = self.tissue.run(tissue_inputs)
        all_prov.extend(tissue_out.get("provenance", []))
        tissue_weights: dict = tissue_out.get("weights", {})
        trace["module_outputs"]["TISSUE.SUBGRAPH"] = {
            "inputs":    tissue_inputs,
            "outputs":   tissue_out,
            "module_id": TissueSubgraphModule.MODULE_ID,
        }

        # ── Step 4: BIOTRANS.FLUX (Michaelis-Menten, maturity E) ──────────────
        flux_inputs = {
            "substrate_conc_uM":     substrate_conc_uM,
            "carcinogen_class":      _flux_class,
            "tissue":                tissue,
            "genotype_multipliers":  genotype_multipliers,
            "tissue_weights":        tissue_weights,
        }
        flux_out = self.flux.run(flux_inputs)
        all_prov.extend(flux_out.get("provenance", []))
        all_missing.extend(flux_out.get("missing_params", []))
        trace["module_outputs"]["BIOTRANS.FLUX"] = {
            "inputs":    flux_inputs,
            "outputs":   flux_out,
            "module_id": BiotransFluxModule.MODULE_ID,
        }
        flux_ratio = flux_out["flux_ratio"]

        # ── Step 5: OUTCOME.MUTSIG ────────────────────────────────────────────
        # Wiring: FLUX.flux_ratio → MUTSIG.flux_ratio
        self._note_wiring("EG3.MOD.BIOTRANS.FLUX.v1", "flux_ratio")
        mutsig_inputs = {
            "carcinogen_class": _mutsig_class,
            "flux_ratio":       flux_ratio,
        }
        mutsig_out = self.mutsig.run(mutsig_inputs)
        all_prov.extend(mutsig_out.get("provenance", []))
        trace["module_outputs"]["OUTCOME.MUTSIG"] = {
            "inputs":    mutsig_inputs,
            "outputs":   mutsig_out,
            "module_id": MutsigOutcomeModule.MODULE_ID,
        }

        # ── Chain summary ─────────────────────────────────────────────────────
        trace["chain_summary"] = {
            "substrate_conc_uM":       substrate_conc_uM,
            "exposure_multiplier":     exposure_out.get("exposure_multiplier"),
            "activation_score":        flux_out["activation_score"],
            "detoxification_score":    flux_out["detoxification_score"],
            "flux_ratio":              flux_ratio,
            "predicted_SBS":           mutsig_out.get("predicted_SBS", []),
            "primary_SBS":             mutsig_out.get("primary_SBS", []),
            "secondary_SBS":           mutsig_out.get("secondary_SBS", []),
            "dominant_mutation":       mutsig_out.get("dominant_mutation"),
            "confidence":              mutsig_out.get("confidence"),
        }
        trace["wiring_connections_used"] = [
            {
                "from_module": k[0],
                "from_port":   k[1],
                "to_module":   self._wiring_index[k]["to_module"],
                "to_port":     self._wiring_index[k]["to_port"],
                "dtype":       self._wiring_index[k]["dtype"],
            }
            for k in sorted(self._used_connections)
        ]
        trace["all_provenance"]  = all_prov
        trace["missing_params"]  = all_missing
        return trace


# ── Module-level singleton ────────────────────────────────────────────────────
_runner_instance: ScenarioRunner | None = None


def get_runner() -> ScenarioRunner:
    global _runner_instance
    if _runner_instance is None:
        _runner_instance = ScenarioRunner()
    return _runner_instance


def run_scenario(
    carcinogen_class: str,
    tissue: str,
    genotype_profile: dict,
    exposure_scenario: str,
    exposure_class: str = None,
    mutsig_class:   str = None,
    include_twin_state: bool = False,
    scenario_id: str = None,
) -> dict:
    """
    Convenience wrapper around ScenarioRunner.run_scenario.

    Parameters
    ----------
    include_twin_state : bool, optional
        If True, attach a 'twin_state' key to the returned trace dict
        with the CEDT twin state vector populated from the run outputs.
    scenario_id : str, optional
        Scenario identifier for twin state metadata (used when include_twin_state=True).
    """
    trace = get_runner().run_scenario(
        carcinogen_class=carcinogen_class,
        tissue=tissue,
        genotype_profile=genotype_profile,
        exposure_scenario=exposure_scenario,
        exposure_class=exposure_class,
        mutsig_class=mutsig_class,
    )
    if include_twin_state:
        try:
            from scripts.engine.cedt import build_twin_state
            trace["twin_state"] = build_twin_state(
                run_trace=trace,
                scenario_id=scenario_id or "ad_hoc",
            )
        except Exception as _e:
            logger.warning("CEDT twin state generation failed: %s", _e)
            trace["twin_state"] = None
    return trace
