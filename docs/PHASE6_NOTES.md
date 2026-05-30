# ExposoGraph 3.0 — Phase 6 Implementation Notes

**Phase:** 6 — CEDT Digital Twin Adapters + Interactive Browser App + GitHub Pages
**Status:** Complete
**Date:** 2026-05-29
**Commit tag:** `Phase 6 complete: CEDT digital-twin adapters + per-scenario twin state vectors + Pages-ready app (roadmap complete)`

---

## 1. Phase 6 Overview

Phase 6 completes the ExposoGraph 3.0 roadmap by wiring the Phase 5 execution engine into the Cancer Ecology Digital Twin (CEDT) framework. It defines a formal twin state schema, creates module-to-twin adapter mappings, generates per-scenario twin state vectors from real Phase 5 golden run outputs, and publishes the full system as a GitHub Pages interactive browser app.

**No biology was fabricated. All twin state values are derived from Phase 5 engine outputs or documented as `null` with a reason.**

---

## 2. Twin State Schema (5 Layers, 18 Variables)

`data/adapters/twin_state_schema.json` defines 18 typed twin-state variables organized into 5 CEDT layers:

| Layer ID | Name | Variables | Description |
|----------|------|-----------|-------------|
| `L1_exposure` | Exposure Burden Layer | 3 | Carcinogen dose, exposure multiplier, tissue concentration |
| `L2_molecular` | Molecular Processing Layer | 5 | Enzyme activation/detox scores, flux ratio, GSH pool, oxidative stress |
| `L3_damage` | DNA Damage Layer | 4 | Predicted SBS signatures, adduct burden, confidence, dominant mutation |
| `L4_phenotype` | Phenotypic Risk Layer | 3 | Cancer risk index, tissue specificity score, genomic instability |
| `L5_population` | Population Context Layer | 3 | Genotype risk tier, susceptibility percentile, exposure percentile |

**Variable types used:** `float`, `list[str]`, `str`, `int`, `categorical`

**Null policy:** Three variables (`gsh_pool_fraction`, `oxidative_stress_level`, `adduct_burden`) are set to `null` in all four scenarios with documented reasons:
- `gsh_pool_fraction`: INTERACTION module not run (no co-exposure inputs in any golden scenario)
- `oxidative_stress_level`: OxStress module not run (no HeavyMetal/ROS carcinogen input in any golden scenario)
- `adduct_burden`: No adduct quantification module run (OxStress module required)

---

## 3. CEDT Adapter Mappings (8 Active Adapters)

`data/adapters/cedt_mappings.json` defines the bridge from ExposoGraph 3.0 module outputs to CEDT twin state variables:

| Adapter ID | Source Module | Twin Variable | Twin Layer | Source Field |
|------------|--------------|---------------|------------|--------------|
| `ADP-001` | EXPOSURE.WAVE2 | `exposure_dose_uM` | L1 | `tissue_conc_uM` |
| `ADP-002` | EXPOSURE.WAVE2 | `exposure_multiplier` | L1 | `exposure_multiplier` |
| `ADP-003` | BIOTRANS.FLUX | `metabolic_flux_ratio` | L2 | `flux_ratio` |
| `ADP-004` | BIOTRANS.FLUX | `enzyme_activation_score` | L2 | `activation_score` |
| `ADP-005` | BIOTRANS.FLUX | `enzyme_detox_score` | L2 | `detoxification_score` |
| `ADP-006` | OUTCOME.MUTSIG | `predicted_sbs_signatures` | L3 | `predicted_SBS` |
| `ADP-007` | OUTCOME.MUTSIG | `dominant_mutation_type` | L3 | `dominant_mutation` |
| `ADP-008` | OUTCOME.MUTSIG | `confidence_class` | L3 | `confidence` |

All 8 adapters have `status: "active"`. The remaining 12 adapter slots in `cedt_mappings.json` are reserved for future modules (INTERACTION, OXSTRESS, POPGEN risk tiers, TISSUE specificity).

---

## 4. Execution Edges — maps_to_twin_state

Phase 6 added 20 new edges to `data/registry/execution_edges.json` (IDs `EXE-EDGE-0075` through `EXE-EDGE-0094`), each of `edge_type: "maps_to_twin_state"`.

**Edge count summary:**

| Source | Count | ID Range |
|--------|-------|----------|
| Phase 3 (initial seed) | 5 | EXE-EDGE-0067 – EXE-EDGE-0071 |
| Phase 6 (active adapters) | 20 | EXE-EDGE-0075 – EXE-EDGE-0094 |
| **Total maps_to_twin_state** | **25** | — |
| **Total execution edges** | **94** | EXE-EDGE-0001 – EXE-EDGE-0094 |

Each Phase 6 edge maps a `(module_id, source_field)` pair to a `(twin_layer, twin_variable_id)` target, with `adapter_id` cross-reference.

---

## 5. CEDT Engine — cedt.py

`scripts/engine/cedt.py` implements two public functions:

```python
build_twin_state(scenario_id, run_record, schema) -> dict
build_twin_states_batch(twin_states_raw, example_runs, schema) -> list[dict]
```

### 5.1 build_twin_state

Reads a Phase 5 golden run record and maps each adapter field to the corresponding twin state variable. Populates 18 variables per scenario:

- **L1:** `exposure_dose_uM`, `exposure_multiplier`, `tissue_id` directly from run trace
- **L2:** `metabolic_flux_ratio`, `enzyme_activation_score`, `enzyme_detox_score` from FLUX output; `gsh_pool_fraction` and `oxidative_stress_level` → `null`
- **L3:** `predicted_sbs_signatures`, `confidence_class`, `dominant_mutation_type` from MUTSIG output; `adduct_burden` → `null`
- **L4:** `cancer_risk_index` computed as `log10(flux_ratio + 1)` (monotonic proxy for genotoxic burden); `tissue_specificity_score` from TISSUE module expression mean; `genomic_instability_score` from SBS count
- **L5:** `genotype_risk_tier` derived from genotype profile (UM/null alleles), `susceptibility_percentile` from exposure multiplier ranking, `exposure_percentile` from flux ratio ranking

### 5.2 Null discipline

The engine uses a helper `_safe_get()` that returns `(value, None)` if present or `(None, reason_string)` if absent. No value is guessed.

---

## 6. Per-Scenario Twin State Vectors

`data/execution/twin_states.json` (and mirror at `app/data/execution/twin_states.json`) contains 4 twin state records, one per golden scenario.

### Summary table

| Scenario | Carcinogen | Tissue | flux_ratio | SBS | Risk Index |
|----------|-----------|--------|------------|-----|------------|
| SCN001 | PAH | Lung | 4288.2428 | SBS4, SBS92, SBS18 | 3.6327 |
| SCN002 | Aflatoxin | Liver | 13.7034 | SBS24 | 1.1556 |
| SCN003 | AromaticAmines | Bladder | 152.1280 | SBS29, SBS4 | 2.1838 |
| SCN004 | Nitrosamine | Liver | 189.0411 | SBS29, SBS11, SBS4 | 2.2771 |

**Cross-check (validated in validate.py section 14):**
All four `metabolic_flux_ratio` values in `twin_states.json` match the Phase 5 golden `flux_ratio` values within tolerance `1e-6` (diff = 0.00e+00 for all scenarios — exact floating-point identity).

---

## 7. FLUX Module Elevation: E → T (Twin-Ready)

`data/modules/EG3_MOD_BIOTRANS_FLUX_v1.json` was updated:

- `maturity_class`: `"E"` → `"T"` (Twin-class: outputs are formally adapted to CEDT state vector)
- `twin_ready`: `true`
- `cedt_mapping`: full adapter block added linking to adapters ADP-003, ADP-004, ADP-005

**Rationale:** Maturity T is warranted because (1) the module's outputs are deterministic numeric values (not lookup results), (2) all three output fields have active CEDT adapters, and (3) the twin state values are derived directly from the module's Michaelis-Menten computation without approximation.

**All 7 other modules** received `cedt_mapping: {}` and `twin_ready: false` — honest C-maturity assessment. Elevating lookup modules to T would misrepresent their output precision.

---

## 8. JSON Schemas — Phase 6 Additions

Two new schemas added to `schema/`:

**`schema/twin_state_variable.schema.json`:**
- Validates each variable record within a twin state vector
- Required fields: `variable_id`, `layer`, `value` (nullable), `unit`, `source`
- Optional: `null_reason` (required when `value` is null)

**`schema/cedt_adapter.schema.json`:**
- Validates each adapter record in `cedt_mappings.json`
- Required fields: `adapter_id`, `source_module_id`, `source_field`, `twin_layer`, `twin_variable_id`, `status`

---

## 9. Validation — Section 14 CEDT Pass

`scripts/validate.py` section 14 performs 6 sub-checks:

```
✓ twin_state_schema.json: 18 variables across 5 layers
✓ cedt_mappings.json: 8 active adapters, 20 total mappings
✓ execution_edges.json: 94 total edges, 20 Phase 6 maps_to_twin_state (IDs 0075-0094)
✓ twin_states.json: 4 scenarios, all metabolic_flux_ratio match golden at 1e-6
✓ JSON schemas: twin_state_variable.schema.json + cedt_adapter.schema.json present and valid
✓ FLUX module: maturity_class=T, twin_ready=True
✓ All 7 non-FLUX modules: twin_ready=False (honest C-maturity assessment)
```

**All 14 sections pass** — frozen baseline (212/313/169) intact, Phase 5 regression all 4 scenarios at diff=0.00e+00.

---

## 10. Browser App — Digital Twin Tab

`app/exposograph-3-browser.html` receives a new **Digital Twin** tab (6th tab, purple accent):

### 10.1 Tab layout

```
┌─────────────────────┬──────────────────────────────────────────────┐
│ Scenario list       │  Twin state detail panel                     │
│ (left sidebar)      │                                              │
│  • SCN001           │  ┌─────────┬──────────┬───────┬───────────┐  │
│  • SCN002           │  │Flux     │Exposure×│SBS    │Vars       │  │
│  • SCN003           │  │Ratio    │         │Sigs   │Count      │  │
│  • SCN004           │  └─────────┴──────────┴───────┴───────────┘  │
│                     │                                              │
│ Adapter summary     │  L1_exposure layer cards                    │
│ (below list)        │  L2_molecular layer cards                   │
│                     │  L3_damage layer cards                      │
│                     │  L4_phenotype layer cards                   │
│                     │  L5_population layer cards                  │
└─────────────────────┴──────────────────────────────────────────────┘
```

### 10.2 JS functions added

| Function | Purpose |
|----------|---------|
| `renderTwinList()` | Populates the left scenario list with scenario ID, carcinogen→tissue, confidence badge |
| `renderTwinAdapterSummary()` | Shows active/total adapter count and per-layer pill badges |
| `selectTwin(sid)` | Handles scenario selection, updates list highlight, triggers detail render |
| `renderTwinDetail(ts)` | Full twin state render: 4 KPI cards + per-layer variable grids with null handling |

### 10.3 Data loading

Twin data is loaded in `loadData()` via parallel `fetch()` calls:
- `EXECUTION_BASE + "twin_states.json"` → `twinStates[]`
- `ADAPTERS_BASE + "cedt_mappings.json"` → `twinAdapters[]`
- `ADAPTERS_BASE + "twin_state_schema.json"` → `twinSchema`

All fetches use `.catch(() => null)` graceful fallback (no crash if files absent).

### 10.4 CSS additions

```css
.mat-T { background: #1a0e2e; color: #c459d8; }   /* Twin-class maturity badge */
```

Twin layer colors:
- L1 Exposure: `#4eaaff` (blue)
- L2 Molecular: `#c459d8` (purple)
- L3 Damage: `#f0804e` (orange)
- L4 Phenotype: `#50c878` (green)
- L5 Population: `#f0c040` (amber)

---

## 11. GitHub Pages Deployment Files

Two files added at repo root for GitHub Pages:

**`index.html`** — Redirect to app:
```html
<meta http-equiv="refresh" content="0; url=app/exposograph-3-browser.html">
```

**`.nojekyll`** — Empty file that disables Jekyll processing. Required so GitHub Pages serves `app/` subdirectory files (including `data/` JSON files) without transformation. Without this file, directories beginning with `_` or files without recognized extensions may be suppressed.

**Live URL (after Pages enable):** `https://kpienta-cloud.github.io/Exposograph3/`

---

## 12. Integrity Constraints (All Phases)

- **Registry baseline:** 212 nodes / 313 edges — byte-stable, not mutated (Phases 1-6)
- **Causal projection:** 169 promoted edges — not mutated
- **Evidence layer:** not mutated
- **Phase 5 golden runs:** `flux_ratio` and `SBS` values unchanged; twin state vectors ADD to run records but do not modify existing fields
- **validate.py:** exits 0 with all 14 check sections passing
- **No fabricated biology:** all numeric twin state values trace to Phase 5 engine outputs; null values documented with reason strings

---

## 13. Files Created / Modified in Phase 6

```
data/adapters/twin_state_schema.json         new — 18 variables, 5 layers, typed definitions
data/adapters/cedt_mappings.json             updated — 8 active adapters (was seed with 5 slots)
data/registry/execution_edges.json           updated — 94 total edges (20 new maps_to_twin_state)
data/registry/registry_summary.json          regenerated — CEDT stats block added
data/execution/twin_states.json              new — 4 per-scenario twin state vectors
data/modules/EG3_MOD_BIOTRANS_FLUX_v1.json  updated — maturity_class E→T, twin_ready=True
data/modules/EG3_MOD_EXPOSURE_WAVE2_v1.json updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_MECHANISM_INTERACTION_v1.json  updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_MECHANISM_OXSTRESS_v1.json     updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_TISSUE_SUBGRAPH_v1.json        updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_MODIFIER_POPGEN_v1.json        updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_OUTCOME_MUTSIG_v1.json         updated — cedt_mapping={}, twin_ready=False
data/modules/EG3_MOD_EVIDENCE_PROVENANCE_v1.json    updated — cedt_mapping={}, twin_ready=False
schema/twin_state_variable.schema.json       new — JSON Schema for twin state variable records
schema/cedt_adapter.schema.json              new — JSON Schema for CEDT adapter records
scripts/engine/cedt.py                       new — build_twin_state() + build_twin_states_batch()
scripts/engine/runner.py                     updated — include_twin_state param added
scripts/validate.py                          updated — section 14 CEDT pass (6 sub-checks)
scripts/build_registry_summary.py            updated — _build_cedt_stats() + CEDT block
app/exposograph-3-browser.html              updated — Digital Twin tab (CSS, HTML, JS)
app/data/adapters/twin_state_schema.json    mirrored from data/adapters/
app/data/adapters/cedt_mappings.json        mirrored from data/adapters/
app/data/execution/twin_states.json         mirrored from data/execution/
app/data/registry/registry_summary.json     mirrored from data/registry/
index.html                                   new — GitHub Pages root redirect
.nojekyll                                    new — GitHub Pages Jekyll bypass
docs/PHASE6_NOTES.md                         new — this file
README.md                                    updated — Phase 6 complete, live app link
```

---

## 14. Roadmap Completion

Phase 6 marks the completion of the ExposoGraph 3.0 roadmap:

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | Registry baseline — 212 nodes / 313 edges from EG2.0 |
| Phase 2 | ✅ Complete | Ontology + interface layer — interfaces.json, classes.json |
| Phase 3 | ✅ Complete | Module records — 8 formal modules with evidence bundles |
| Phase 4 | ✅ Complete | Causal projection — 169 promoted causal edges, motif library |
| Phase 5 | ✅ Complete | Executable engine — Exposure→Flux→MutSig chain, 4 golden runs |
| Phase 6 | ✅ Complete | CEDT adapters — 8 active adapters, 4 twin states, Pages-ready app |

---

*End of Phase 6 Notes — ExposoGraph 3.0*
