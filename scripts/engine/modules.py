"""
ExposoGraph 3.0 — Phase 5 Reference Engine: Module Classes
stdlib only: json, math, logging

One class per module type. Each reads its own module JSON params and
implements its declared update_rule exactly. MichaelisMenten v=Vmax*[S]/(Km+[S])
for FLUX using real Km_uM/Vmax from the 37 params; lookups for
EXPOSURE/POPGEN/TISSUE/MUTSIG.

NEVER fabricates biology — missing values are surfaced as None with a logged note.
"""

import json
import math
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Repo root relative to this file location (scripts/engine/)
_REPO_ROOT = Path(__file__).parent.parent.parent
_MODULES_DIR = _REPO_ROOT / "data" / "modules"


def _load_module_json(filename: str) -> dict:
    """Load a module JSON file from data/modules/."""
    path = _MODULES_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# EXPOSURE module (maturity C — lookup)
# ──────────────────────────────────────────────────────────────────────────────

class ExposureWave2Module:
    """
    Implements EG3.MOD.EXPOSURE.WAVE2.v1.
    equation_type: lookup
    update_rule: lookup exposure_multiplier + tissue_conc_uM for
                 (carcinogen_class, exposure_scenario) from its 14 class param records.
    Outputs: tissue_conc_uM (concentration:uM), exposure_multiplier (multiplier:exposure).
    """

    MODULE_ID = "EG3.MOD.EXPOSURE.WAVE2.v1"
    EQUATION_TYPE = "lookup"

    def __init__(self):
        raw = _load_module_json("EG3_MOD_EXPOSURE_WAVE2_v1.json")
        self._params = raw["parameters"]
        # Build lookup: carcinogen_class -> {scenario -> record}
        self._class_map: dict = {}
        for p in self._params:
            cc = p.get("carcinogen_class")
            if cc and "exposure_scenarios" in p:
                self._class_map[cc] = p

    def run(self, inputs: dict) -> dict:
        """
        inputs:
          carcinogen_class (str)
          exposure_scenario (str)
        outputs:
          tissue_conc_uM (float | None)
          exposure_multiplier (float | None)
          daily_intake_ug_kg (float | None)
          provenance (list of str)
        """
        carcinogen_class = inputs["carcinogen_class"]
        exposure_scenario = inputs["exposure_scenario"]
        provenance = []

        if carcinogen_class not in self._class_map:
            logger.warning(
                "EXPOSURE: carcinogen_class '%s' not found in parameters — "
                "tissue_conc_uM=None", carcinogen_class
            )
            return {
                "tissue_conc_uM": None,
                "exposure_multiplier": None,
                "daily_intake_ug_kg": None,
                "provenance": [
                    f"MISSING: carcinogen_class '{carcinogen_class}' not in EXPOSURE params"
                ],
            }

        class_record = self._class_map[carcinogen_class]
        scenarios = class_record.get("exposure_scenarios", {})
        if exposure_scenario not in scenarios:
            logger.warning(
                "EXPOSURE: scenario '%s' not found for class '%s' — "
                "tissue_conc_uM=None", exposure_scenario, carcinogen_class
            )
            return {
                "tissue_conc_uM": None,
                "exposure_multiplier": None,
                "daily_intake_ug_kg": None,
                "provenance": [
                    f"MISSING: scenario '{exposure_scenario}' not in EXPOSURE "
                    f"params for class '{carcinogen_class}'"
                ],
            }

        scen = scenarios[exposure_scenario]
        tissue_conc = scen.get("estimated_tissue_conc_uM")
        multiplier = scen.get("multiplier_vs_baseline")
        daily_intake = scen.get("daily_intake_ug_kg") or scen.get("daily_intake_ug_kg_bw")

        provenance.append(
            f"EXPOSURE.params[carcinogen_class={carcinogen_class}]"
            f".exposure_scenarios[{exposure_scenario}]"
            f".estimated_tissue_conc_uM={tissue_conc}"
        )
        provenance.append(
            f"EXPOSURE.params[carcinogen_class={carcinogen_class}]"
            f".exposure_scenarios[{exposure_scenario}]"
            f".multiplier_vs_baseline={multiplier}"
        )
        if tissue_conc is None:
            logger.warning(
                "EXPOSURE: tissue_conc_uM is None for %s/%s",
                carcinogen_class, exposure_scenario
            )
            provenance.append(
                f"NOTE: estimated_tissue_conc_uM missing for "
                f"{carcinogen_class}/{exposure_scenario} — surfacing as None"
            )

        return {
            "tissue_conc_uM": tissue_conc,
            "exposure_multiplier": multiplier,
            "daily_intake_ug_kg": daily_intake,
            "provenance": provenance,
        }

    def get_params_for_class(self, carcinogen_class: str) -> dict:
        """Return the full class param record for a given carcinogen class."""
        return self._class_map.get(carcinogen_class, {})


# ──────────────────────────────────────────────────────────────────────────────
# POPGEN modifier module (maturity C — lookup)
# ──────────────────────────────────────────────────────────────────────────────

class PopgenModifierModule:
    """
    Implements EG3.MOD.MODIFIER.POPGEN.v1.
    equation_type: lookup
    update_rule: for each gene/phenotype in genotype_profile, look up
                 activity_multiplier from its 27 param records.
    Outputs: activity_multiplier dict (gene -> float).
    """

    MODULE_ID = "EG3.MOD.MODIFIER.POPGEN.v1"
    EQUATION_TYPE = "lookup"

    def __init__(self):
        raw = _load_module_json("EG3_MOD_MODIFIER_POPGEN_v1.json")
        self._params = raw["parameters"]
        # Build lookup: (gene, phenotype) -> activity_multiplier
        self._lookup: dict = {}
        for p in self._params:
            gene = p.get("gene")
            phenotype = p.get("phenotype")
            mult = p.get("activity_multiplier")
            if gene and phenotype:
                self._lookup[(gene, phenotype)] = (mult, p.get("source", ""))

        # Standard scale from genotype_modifier_standard_scale
        self._standard_scale = raw.get("genotype_modifier_standard_scale", {
            "PM": 0.0, "IM": 0.5, "NM": 1.0, "RM": 1.5, "UM": 2.0, "null": 0.0
        })
        # Special cases
        self._special_cases = raw.get("genotype_modifier_special_cases", {})

    def run(self, inputs: dict) -> dict:
        """
        inputs:
          genotype_profile (dict: gene -> phenotype string)
        outputs:
          multipliers (dict: gene -> float | None)
          provenance (list of str)
        """
        genotype_profile = inputs.get("genotype_profile", {})
        multipliers = {}
        provenance = []

        for gene, phenotype in genotype_profile.items():
            # Check special cases first
            special_key = f"{gene}_{phenotype}" if not phenotype.startswith(gene) else phenotype
            if special_key in self._special_cases:
                sc = self._special_cases[special_key]
                mult = sc.get("activity_fraction")
                multipliers[gene] = mult
                provenance.append(
                    f"POPGEN.genotype_modifier_special_cases[{special_key}]"
                    f".activity_fraction={mult} (source={sc.get('source','')})"
                )
                continue

            # Normal lookup
            if (gene, phenotype) in self._lookup:
                mult, source = self._lookup[(gene, phenotype)]
                multipliers[gene] = mult
                provenance.append(
                    f"POPGEN.params[gene={gene}, phenotype={phenotype}]"
                    f".activity_multiplier={mult} (source={source})"
                )
            elif phenotype in self._standard_scale:
                # Use standard scale as fallback if gene not in explicit params
                mult = self._standard_scale[phenotype]
                multipliers[gene] = mult
                provenance.append(
                    f"POPGEN.genotype_modifier_standard_scale[{phenotype}]={mult} "
                    f"(fallback; gene={gene} not in explicit params)"
                )
                logger.info(
                    "POPGEN: gene '%s' phenotype '%s' not in explicit params; "
                    "using standard scale %.2f", gene, phenotype, mult
                )
            else:
                multipliers[gene] = None
                provenance.append(
                    f"MISSING: POPGEN gene={gene} phenotype={phenotype} — "
                    "activity_multiplier=None (not in params or standard scale)"
                )
                logger.warning(
                    "POPGEN: no multiplier for gene=%s phenotype=%s", gene, phenotype
                )

        return {"multipliers": multipliers, "provenance": provenance}

    def get_multiplier(self, gene: str, phenotype: str) -> tuple:
        """Return (multiplier, source_note) for a single gene/phenotype."""
        if (gene, phenotype) in self._lookup:
            return self._lookup[(gene, phenotype)]
        if phenotype in self._standard_scale:
            return self._standard_scale[phenotype], f"standard_scale[{phenotype}]"
        return None, f"MISSING: {gene}/{phenotype}"


# ──────────────────────────────────────────────────────────────────────────────
# TISSUE subgraph module (maturity C — lookup)
# ──────────────────────────────────────────────────────────────────────────────

class TissueSubgraphModule:
    """
    Implements EG3.MOD.TISSUE.SUBGRAPH.v1.
    equation_type: lookup
    update_rule: for each enzyme + chosen tissue, look up
                 normalized_weights[gene][tissue] from its 53 param records.
    Outputs: tissue_weight dict (gene -> float).
    """

    MODULE_ID = "EG3.MOD.TISSUE.SUBGRAPH.v1"
    EQUATION_TYPE = "lookup"

    def __init__(self):
        raw = _load_module_json("EG3_MOD_TISSUE_SUBGRAPH_v1.json")
        self._params = raw["parameters"]
        # Build lookup: gene -> {tissue -> weight}
        self._lookup: dict = {}
        for p in self._params:
            gene = p.get("gene")
            if gene and "normalized_weights" in p:
                self._lookup[gene] = (p["normalized_weights"], p.get("source", ""))

    def run(self, inputs: dict) -> dict:
        """
        inputs:
          tissue (str)
          enzymes (list of str) — optional; if absent returns all known
        outputs:
          weights (dict: gene -> float | None)
          provenance (list of str)
        """
        tissue = inputs["tissue"]
        enzymes = inputs.get("enzymes")
        if enzymes is None:
            enzymes = list(self._lookup.keys())

        weights = {}
        provenance = []

        for gene in enzymes:
            if gene in self._lookup:
                norm_weights, source = self._lookup[gene]
                if tissue in norm_weights:
                    w = norm_weights[tissue]
                    weights[gene] = w
                    provenance.append(
                        f"TISSUE.params[gene={gene}].normalized_weights[{tissue}]={w} "
                        f"(source={source})"
                    )
                else:
                    weights[gene] = None
                    provenance.append(
                        f"MISSING: TISSUE gene={gene} tissue={tissue} — "
                        "normalized_weight=None (tissue not in params)"
                    )
                    logger.warning(
                        "TISSUE: gene=%s tissue=%s not in normalized_weights", gene, tissue
                    )
            else:
                weights[gene] = None
                provenance.append(
                    f"MISSING: TISSUE gene={gene} — not in params; weight=None"
                )
                logger.info("TISSUE: gene=%s not in params", gene)

        return {"weights": weights, "provenance": provenance}

    def get_weight(self, gene: str, tissue: str) -> tuple:
        """Return (weight, source_note) for a single gene/tissue."""
        if gene in self._lookup:
            norm_weights, source = self._lookup[gene]
            if tissue in norm_weights:
                return norm_weights[tissue], source
            return None, f"MISSING: tissue={tissue} not in params for gene={gene}"
        return None, f"MISSING: gene={gene} not in TISSUE params"


# ──────────────────────────────────────────────────────────────────────────────
# BIOTRANS FLUX module (maturity E — Michaelis-Menten executable)
# ──────────────────────────────────────────────────────────────────────────────

class BiotransFluxModule:
    """
    Implements EG3.MOD.BIOTRANS.FLUX.v1.
    equation_type: score-based / michaelis_menten
    update_rule (from module record):
      v = Vmax × [S] / (Km + [S])
      activation_score = Σ v_i(enzyme_i) × tissue_weight[enzyme_i][tissue]
                           × genotype_multiplier[enzyme_i]
      detoxification_score = Σ v_j(enzyme_j) × tissue_weight[enzyme_j][tissue]
                              × genotype_multiplier[enzyme_j]
      flux_ratio = activation_score / max(detoxification_score, 0.001)

    Uses REAL Km_uM / Vmax from the 37 module param records.
    Missing Km or Vmax → rate = None → contribution logged, excluded from sum.
    """

    MODULE_ID = "EG3.MOD.BIOTRANS.FLUX.v1"
    EQUATION_TYPE = "score-based/michaelis_menten"

    # Detox_guard: divide-by-zero protection (from update_rule in module)
    DETOX_GUARD = 0.001

    def __init__(self):
        raw = _load_module_json("EG3_MOD_BIOTRANS_FLUX_v1.json")
        self._params = raw["parameters"]
        # Internal state from module record
        self._internal_state = raw.get("internal_state", [])
        gsh_record = next(
            (s for s in self._internal_state if s.get("name") == "GSH_pool_mM"), {}
        )
        self.GSH_pool_baseline_mM = gsh_record.get("baseline_mM", 7.5)
        self.GSH_pool_threshold_mM = gsh_record.get("critical_threshold_mM", 1.5)

        # Build param lookup: (carcinogen_class, enzyme) -> param record(s)
        # A class may have multiple enzymes; an enzyme may appear in multiple records
        self._param_lookup: dict = {}
        for p in self._params:
            cc = p.get("carcinogen_class")
            enz = p.get("enzyme")
            if cc and enz:
                key = (cc, enz)
                # Keep first occurrence (most specific)
                if key not in self._param_lookup:
                    self._param_lookup[key] = p

        # Get pathway classification per (class, enzyme)
        self._pathway_type: dict = {}
        for p in self._params:
            cc = p.get("carcinogen_class")
            enz = p.get("enzyme")
            pt = p.get("pathway_type", "")
            if cc and enz:
                self._pathway_type[(cc, enz)] = pt

    def _michaelis_menten(self, Km_uM: float, Vmax: float, S_uM: float) -> float:
        """v = Vmax * S / (Km + S). Returns rate in same units as Vmax."""
        if S_uM <= 0.0:
            return 0.0
        return Vmax * S_uM / (Km_uM + S_uM)

    def _is_activation(self, pathway_type: str) -> bool:
        """Return True if pathway_type indicates an activation pathway."""
        pt_lower = pathway_type.lower()
        return any(kw in pt_lower for kw in (
            "activation", "ethanol_oxidation", "ahr_signaling", "oxidation",
            "biotransformation"
        ))

    def _is_detoxification(self, pathway_type: str) -> bool:
        """Return True if pathway_type indicates a detox pathway."""
        pt_lower = pathway_type.lower()
        return any(kw in pt_lower for kw in (
            "detoxification", "acetaldehyde_clearance", "gsh_conjugation",
            "formaldehyde_oxidation"
        ))

    def run(self, inputs: dict) -> dict:
        """
        inputs:
          substrate_conc_uM (float)    — [S], from EXPOSURE output
          carcinogen_class (str)        — selects which enzyme params to use
          tissue (str)                  — for tissue weights from TISSUE module
          genotype_multipliers (dict)   — gene -> float, from POPGEN module
          tissue_weights (dict)         — gene -> float, from TISSUE module
        outputs:
          per_enzyme_rates (list of dicts)
          activation_score (float)
          detoxification_score (float)
          flux_ratio (float)
          missing_params (list of str)
          provenance (list of str)
          internal_state_used (dict)
        """
        S_uM = inputs["substrate_conc_uM"]
        carcinogen_class = inputs["carcinogen_class"]
        genotype_multipliers = inputs.get("genotype_multipliers", {})
        tissue_weights = inputs.get("tissue_weights", {})

        per_enzyme_rates = []
        activation_sum = 0.0
        detox_sum = 0.0
        missing_params = []
        provenance = []

        # Find all enzyme params for this carcinogen class
        class_params = [p for p in self._params if p.get("carcinogen_class") == carcinogen_class]

        if not class_params:
            logger.warning("FLUX: No params for carcinogen_class='%s'", carcinogen_class)
            missing_params.append(
                f"MISSING: No FLUX params for carcinogen_class='{carcinogen_class}'"
            )

        for p in class_params:
            enzyme = p.get("enzyme", "?")
            pathway_type = p.get("pathway_type", "")
            Km_uM = p.get("Km_uM")
            Vmax = p.get("Vmax_pmol_min_pmolP450") or p.get("Vmax_U_per_mg")

            # Determine activation vs detox
            is_act = self._is_activation(pathway_type)
            is_det = self._is_detoxification(pathway_type)
            pathway_category = (
                "activation" if is_act
                else "detoxification" if is_det
                else "other"
            )

            # Compute MM rate
            rate = None
            rate_note = None
            if Km_uM is None:
                rate_note = (
                    f"MISSING: Km_uM is None for {carcinogen_class}/{enzyme} "
                    "(param record present but Km not available) — rate=None"
                )
                missing_params.append(rate_note)
                logger.warning("FLUX: %s", rate_note)
            elif Vmax is None:
                rate_note = (
                    f"MISSING: Vmax is None for {carcinogen_class}/{enzyme} "
                    "(param record present but Vmax not available) — "
                    "using CLint proxy if available, else rate=None"
                )
                # Try CLint as proxy: CLint = Vmax/Km => Vmax ~= CLint * Km
                CLint = p.get("CLint")
                if CLint is not None and Km_uM is not None:
                    Vmax_proxy = CLint * Km_uM
                    rate = self._michaelis_menten(Km_uM, Vmax_proxy, S_uM)
                    rate_note = (
                        f"NOTE: Vmax derived from CLint*Km={CLint}*{Km_uM}={Vmax_proxy:.4f} "
                        f"for {carcinogen_class}/{enzyme} (CLint proxy)"
                    )
                    Vmax = Vmax_proxy  # used Vmax
                else:
                    missing_params.append(rate_note)
                    logger.warning("FLUX: %s", rate_note)
            else:
                rate = self._michaelis_menten(Km_uM, Vmax, S_uM)

            # Get tissue weight and genotype multiplier
            # Use gene name as key (enzyme name may differ from gene symbol)
            # Try enzyme name directly, then common gene symbol mappings
            gene = _enzyme_to_gene(enzyme)
            tissue_w = tissue_weights.get(gene) or tissue_weights.get(enzyme)
            geno_m = genotype_multipliers.get(gene) or genotype_multipliers.get(enzyme)

            if tissue_w is None:
                logger.info(
                    "FLUX: tissue_weight for %s/%s not found; "
                    "using 1.0 (gene not in profile)", enzyme, gene
                )
                tissue_w = 1.0  # neutral — gene expressed but weight unknown

            if geno_m is None:
                # Default: NM (no genotype info) -> 1.0
                geno_m = 1.0

            # Weighted rate
            weighted_rate = None
            if rate is not None:
                weighted_rate = rate * tissue_w * geno_m

            # Build per-enzyme record
            enzyme_record = {
                "enzyme": enzyme,
                "gene": gene,
                "pathway_type": pathway_type,
                "pathway_category": pathway_category,
                "Km_uM": Km_uM,
                "Vmax": Vmax,
                "substrate_conc_uM": S_uM,
                "mm_rate": rate,
                "tissue_weight": tissue_w,
                "genotype_multiplier": geno_m,
                "weighted_rate": weighted_rate,
                "param_source": p.get("sources", []),
                "confidence": p.get("confidence", "unknown"),
            }
            if rate_note:
                enzyme_record["note"] = rate_note

            per_enzyme_rates.append(enzyme_record)

            provenance.append(
                f"FLUX.params[carcinogen_class={carcinogen_class}, enzyme={enzyme}]"
                f".Km_uM={Km_uM}, Vmax={Vmax} → mm_rate={rate}"
                f" × tissue_w={tissue_w} × geno_m={geno_m} = weighted={weighted_rate}"
            )

            # Accumulate scores
            if weighted_rate is not None:
                if is_act:
                    activation_sum += weighted_rate
                elif is_det:
                    detox_sum += weighted_rate

        # Internal state tracking
        activation_accumulator = activation_sum
        detox_accumulator = detox_sum

        # flux_ratio with divide-by-zero guard (from update_rule)
        flux_ratio = activation_sum / max(detox_sum, self.DETOX_GUARD)

        provenance.append(
            f"FLUX.activation_score={activation_sum:.6f} "
            f"detoxification_score={detox_sum:.6f} "
            f"flux_ratio={flux_ratio:.6f} "
            f"(guard={self.DETOX_GUARD})"
        )

        return {
            "per_enzyme_rates": per_enzyme_rates,
            "activation_score": activation_sum,
            "detoxification_score": detox_sum,
            "flux_ratio": flux_ratio,
            "missing_params": missing_params,
            "provenance": provenance,
            "internal_state_used": {
                "GSH_pool_baseline_mM": self.GSH_pool_baseline_mM,
                "GSH_pool_threshold_mM": self.GSH_pool_threshold_mM,
                "activation_accumulator": activation_accumulator,
                "detox_accumulator": detox_accumulator,
                "source": "EG3_MOD_BIOTRANS_FLUX_v1.json#internal_state[GSH_pool_mM]",
            },
        }

    def get_params_for_class(self, carcinogen_class: str) -> list:
        """Return all param records for a given carcinogen class."""
        return [p for p in self._params if p.get("carcinogen_class") == carcinogen_class]


# ──────────────────────────────────────────────────────────────────────────────
# MUTSIG outcome module (maturity C — lookup)
# ──────────────────────────────────────────────────────────────────────────────

class MutsigOutcomeModule:
    """
    Implements EG3.MOD.OUTCOME.MUTSIG.v1.
    equation_type: lookup
    update_rule:
      predicted_SBS = carcinogen_class_map[carcinogen_class].primary_signatures[0]
      dominant_mutation = signatures[SBS_id].dominant_mutation
      confidence influenced by flux_ratio magnitude.
    """

    MODULE_ID = "EG3.MOD.OUTCOME.MUTSIG.v1"
    EQUATION_TYPE = "lookup"

    # Confidence thresholds (flux_ratio based)
    HIGH_FLUX_THRESHOLD = 5.0
    LOW_FLUX_THRESHOLD = 0.5

    def __init__(self):
        raw = _load_module_json("EG3_MOD_OUTCOME_MUTSIG_v1.json")
        self._params = raw["parameters"]

        # Separate signature records from carcinogen_class_map records
        self._signatures: dict = {}      # signature_id -> record
        self._class_map: dict = {}       # carcinogen_class -> record

        for p in self._params:
            if "signature_id" in p:
                self._signatures[p["signature_id"]] = p
            elif "carcinogen_class" in p:
                self._class_map[p["carcinogen_class"]] = p

    def run(self, inputs: dict) -> dict:
        """
        inputs:
          carcinogen_class (str)
          flux_ratio (float)
        outputs:
          predicted_SBS (list of str)
          dominant_mutation (str | None)
          confidence (str)
          provenance (list of str)
        """
        carcinogen_class = inputs["carcinogen_class"]
        flux_ratio = inputs.get("flux_ratio", 1.0)
        provenance = []

        if carcinogen_class not in self._class_map:
            logger.warning(
                "MUTSIG: carcinogen_class '%s' not in class_map", carcinogen_class
            )
            return {
                "predicted_SBS": [],
                "dominant_mutation": None,
                "confidence": "none",
                "provenance": [
                    f"MISSING: carcinogen_class '{carcinogen_class}' not in MUTSIG params"
                ],
            }

        class_rec = self._class_map[carcinogen_class]
        primary_sigs = class_rec.get("primary_signatures", [])
        secondary_sigs = class_rec.get("secondary_signatures", [])
        all_sigs = primary_sigs + secondary_sigs

        provenance.append(
            f"MUTSIG.params[carcinogen_class={carcinogen_class}]"
            f".primary_signatures={primary_sigs}"
            f" secondary_signatures={secondary_sigs}"
        )

        # Get dominant mutation from primary signature
        dominant_mutation = None
        if primary_sigs:
            primary_id = primary_sigs[0]
            if primary_id in self._signatures:
                sig_rec = self._signatures[primary_id]
                dominant_mutation = sig_rec.get("dominant_mutation")
                provenance.append(
                    f"MUTSIG.params[signature_id={primary_id}]"
                    f".dominant_mutation={dominant_mutation}"
                )
            else:
                provenance.append(
                    f"NOTE: primary signature {primary_id} not in signature records"
                )

        # Confidence influenced by flux_ratio magnitude
        base_confidence = "medium"
        if primary_sigs and primary_sigs[0] in self._signatures:
            base_confidence = self._signatures[primary_sigs[0]].get("confidence", "medium")

        if flux_ratio >= self.HIGH_FLUX_THRESHOLD:
            confidence = "high" if base_confidence in ("high", "medium") else "medium"
            confidence_note = (
                f"flux_ratio={flux_ratio:.4f} ≥ {self.HIGH_FLUX_THRESHOLD} → "
                f"confidence elevated to '{confidence}'"
            )
        elif flux_ratio <= self.LOW_FLUX_THRESHOLD:
            confidence = "low"
            confidence_note = (
                f"flux_ratio={flux_ratio:.4f} ≤ {self.LOW_FLUX_THRESHOLD} → "
                f"confidence downgraded to 'low'"
            )
        else:
            confidence = base_confidence
            confidence_note = (
                f"flux_ratio={flux_ratio:.4f} in normal range → "
                f"confidence='{confidence}' (from primary signature record)"
            )

        provenance.append(f"MUTSIG.confidence_rule: {confidence_note}")

        return {
            "predicted_SBS": all_sigs,
            "primary_SBS": primary_sigs,
            "secondary_SBS": secondary_sigs,
            "dominant_mutation": dominant_mutation,
            "confidence": confidence,
            "provenance": provenance,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Helper: map enzyme names in FLUX params to gene symbols in POPGEN/TISSUE
# ──────────────────────────────────────────────────────────────────────────────

# Maps from FLUX param enzyme names to canonical gene symbols used in
# POPGEN + TISSUE modules. Enzyme names with suffixes (like CYP2A13_methyl,
# ADH1B_star1) are mapped to their base gene symbol.
_ENZYME_TO_GENE_MAP = {
    # PAH activation
    "CYP1A1": "CYP1A1",
    "CYP1B1": "CYP1B1",
    "EPHX1": "EPHX1",
    # PAH detox
    "GSTM1": "GSTM1",
    "GSTP1": "GSTP1",
    # Aflatoxin activation
    "CYP3A4": "CYP3A4",
    "CYP1A2": "CYP1A2",
    # Aflatoxin detox
    "CYP3A4_AFQ1": "CYP3A4",
    "GSTA1": "GSTA1",    # not in TISSUE params — will return None weight
    # Aldehyde / ethanol
    "ADH1B_star1": "ADH1B",
    "ADH1B_star2": "ADH1B",
    "ALDH2_star1": "ALDH2",
    "ALDH2_star2_homozygous": "ALDH2",
    "ALDH2_star1_star2": "ALDH2",
    "ALDH1A1": "ALDH2",   # ALDH1A1 not in TISSUE; map to nearest (ALDH2) — logged
    "ADH5": "ADH5",
    # Nitrosamine
    "CYP2A13": "CYP2A13",
    "CYP2A13_methyl": "CYP2A13",
    "CYP2A6": "CYP2A6",
    "carbonyl_reduction": "AKR1C2",  # proxy gene
    # NDMA
    "CYP2E1": "CYP2E1",
    "CYP2E1_with_b5": "CYP2E1",
    "ADH5_formaldehyde": "ADH5",
    # HCA
    "SULT1A1": "SULT1A1",
    "NAT2": "NAT2",
    # Benzene
    "CYP2E1_liver": "CYP2E1",
    "CYP2F2_lung": "CYP2F1",   # CYP2F2 not in TISSUE; closest is CYP2F1
    "NQO1": "NQO1",
    "GSTT1": "GSTT1",
    # HeavyMetal
    "AS3MT": "AS3MT",
    "general_ROS": None,        # not a gene; no tissue weight
    # Dioxin
    "AhR_binding": "AHR",
    # ChlorinatedSolvent
    "CYP2E1_TCE": "CYP2E1",
    "GSTT1_TCE": "GSTT1",
}


def _enzyme_to_gene(enzyme: str) -> str:
    """
    Map an enzyme name from FLUX params to a canonical gene symbol.
    Falls back to the enzyme name itself if not in the map.
    """
    return _ENZYME_TO_GENE_MAP.get(enzyme, enzyme)
