"""
ExposoGraph 3.0 — Phase 5: Carcinogen-class alias map

The three modules (EXPOSURE, FLUX, MUTSIG) use different carcinogen-class
vocabulary keys.  This module provides a single canonical→(exposure, flux, mutsig)
mapping so the runner can resolve all three keys from one canonical class string.

Verified keys per module
─────────────────────────
EXPOSURE (EG3_MOD_EXPOSURE_WAVE2_v1.json):
    PAH, HCA, AromaticAmines, TobaccoNitrosamines, AflatoxinB1,
    EstrogenMetabolites, Benzene, VinylChloride, HeavyMetals, Aldehyde,
    Dioxins_AhR, DietaryNitroso, ChlorinatedSolvents, UV_Radiation

FLUX (EG3_MOD_BIOTRANS_FLUX_v1.json):
    PAH, HCA, Aflatoxin, Aldehyde, Benzene, ChlorinatedSolvent, Dioxin,
    HeavyMetal, NDMA, Nitrosamine

MUTSIG (EG3_MOD_OUTCOME_MUTSIG_v1.json — carcinogen_class params):
    PAH, Tobacco_PAH, Nitrosamine, NDMA, AlkylatingAgent, Aflatoxin,
    HCA, AromaticAmines, Aldehyde, Ethanol, Benzene, HeavyMetal, Dioxin,
    ChlorinatedSolvent, Estrogen, Colibactin
"""

from typing import NamedTuple


class ClassKeys(NamedTuple):
    exposure: str   # key for EG3_MOD_EXPOSURE_WAVE2_v1.json
    flux: str       # key for EG3_MOD_BIOTRANS_FLUX_v1.json
    mutsig: str     # key for EG3_MOD_OUTCOME_MUTSIG_v1.json


# Canonical class → (exposure_key, flux_key, mutsig_key)
CLASS_ALIASES: dict[str, ClassKeys] = {
    # ── Polycyclic Aromatic Hydrocarbons ─────────────────────────────────────
    "PAH":               ClassKeys("PAH",                 "PAH",               "PAH"),
    "Tobacco_PAH":       ClassKeys("PAH",                 "PAH",               "Tobacco_PAH"),

    # ── Aflatoxin B1 ─────────────────────────────────────────────────────────
    "Aflatoxin":         ClassKeys("AflatoxinB1",         "Aflatoxin",         "Aflatoxin"),
    "AflatoxinB1":       ClassKeys("AflatoxinB1",         "Aflatoxin",         "Aflatoxin"),

    # ── Heterocyclic Amines ───────────────────────────────────────────────────
    "HCA":               ClassKeys("HCA",                 "HCA",               "HCA"),

    # ── Aromatic Amines (4-ABP, benzidine etc.) ───────────────────────────────
    # Closest FLUX class is HCA (shared CYP1A2/NAT2 N-hydroxylation mechanism).
    # MUTSIG has an explicit AromaticAmines key.
    "AromaticAmines":    ClassKeys("AromaticAmines",      "HCA",               "AromaticAmines"),

    # ── Tobacco-Specific Nitrosamines (NNK, NNN) ─────────────────────────────
    "TobaccoNitrosamines": ClassKeys("TobaccoNitrosamines", "Nitrosamine",     "Nitrosamine"),
    "Nitrosamine":       ClassKeys("DietaryNitroso",      "Nitrosamine",       "Nitrosamine"),

    # ── NDMA (N-nitrosodimethylamine, alcohol/chronic exposure) ───────────────
    "NDMA":              ClassKeys("DietaryNitroso",      "NDMA",              "NDMA"),

    # ── Aldehydes / Acetaldehyde (alcohol metabolism) ─────────────────────────
    "Aldehyde":          ClassKeys("Aldehyde",            "Aldehyde",          "Aldehyde"),
    "Ethanol":           ClassKeys("Aldehyde",            "Aldehyde",          "Ethanol"),

    # ── Benzene ───────────────────────────────────────────────────────────────
    "Benzene":           ClassKeys("Benzene",             "Benzene",           "Benzene"),

    # ── Heavy Metals ──────────────────────────────────────────────────────────
    "HeavyMetal":        ClassKeys("HeavyMetals",         "HeavyMetal",        "HeavyMetal"),
    "HeavyMetals":       ClassKeys("HeavyMetals",         "HeavyMetal",        "HeavyMetal"),

    # ── Dioxins / AhR ligands ─────────────────────────────────────────────────
    "Dioxin":            ClassKeys("Dioxins_AhR",         "Dioxin",            "Dioxin"),
    "Dioxins_AhR":       ClassKeys("Dioxins_AhR",         "Dioxin",            "Dioxin"),

    # ── Chlorinated Solvents (TCE, PCE) ──────────────────────────────────────
    "ChlorinatedSolvent":  ClassKeys("ChlorinatedSolvents", "ChlorinatedSolvent", "ChlorinatedSolvent"),
    "ChlorinatedSolvents": ClassKeys("ChlorinatedSolvents", "ChlorinatedSolvent", "ChlorinatedSolvent"),

    # ── Dietary Nitroso (processed meat, contaminated water) ─────────────────
    "DietaryNitroso":    ClassKeys("DietaryNitroso",      "Nitrosamine",       "Nitrosamine"),

    # ── Estrogen metabolites ──────────────────────────────────────────────────
    "Estrogen":          ClassKeys("EstrogenMetabolites", "HeavyMetal",        "Estrogen"),
    # Note: FLUX has no Estrogen class; HeavyMetal used as structural proxy only.
    # In practice this scenario should surface FLUX params as None.

    # ── Vinyl chloride / haloalkanes ──────────────────────────────────────────
    "VinylChloride":     ClassKeys("VinylChloride",       "ChlorinatedSolvent","ChlorinatedSolvent"),

    # ── UV radiation ─────────────────────────────────────────────────────────
    # FLUX has no UV class — no MM kinetics available. Exposure only.
    "UV_Radiation":      ClassKeys("UV_Radiation",        "PAH",               "PAH"),
    # (PAH used as fallback for FLUX/MUTSIG; surfaced as missing in practice)
}


def resolve(canonical: str) -> ClassKeys:
    """
    Return (exposure_key, flux_key, mutsig_key) for a canonical class name.
    Falls back to (canonical, canonical, canonical) with a logged note if unknown.
    """
    if canonical in CLASS_ALIASES:
        return CLASS_ALIASES[canonical]
    # Unknown canonical: pass through as-is and let each module surface None
    import logging
    logging.getLogger(__name__).warning(
        "aliases.resolve: canonical class '%s' not in CLASS_ALIASES — "
        "using as-is for all three modules", canonical
    )
    return ClassKeys(canonical, canonical, canonical)
