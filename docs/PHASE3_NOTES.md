# ExposoGraph 3.0 — Phase 3 Notes

**Phase**: 3 — Module Recast & Execution Edge Layer  
**Date completed**: 2026-05-29  
**Commit message**: `Phase 3 complete: recast 8 ExposoGraph 2.0 modules as first-class records + add execution/interaction edges`

---

## Summary

Phase 3 recasts 8 ExposoGraph 2.0 module stubs into fully-populated first-class JSON records
and adds a new execution/interaction edge layer (`data/registry/execution_edges.json`).
The baseline registry (`registry_graph.json`, `nodes.json`, `edges.json`) remains **immutable** at
**212 nodes / 313 edges**.

### Final counts

| Artifact                          | Count |
|-----------------------------------|-------|
| Registry nodes (baseline)         | 212   |
| Registry edges (baseline)         | 313   |
| Execution edges (new — Phase 3)   | 74    |
| Module records populated          | 8     |
| Total module parameters           | 358   |
| Phase 3 module fields required    | 22    |
| Modules at 100% field completeness| 8 / 8 |

---

## Per-Module Completeness

All 8 modules achieved **100% Phase 3 field completeness** (22/22 required fields present).

### EG3.MOD.EXPOSURE.WAVE2.v1

| Field            | Value                                             |
|------------------|---------------------------------------------------|
| maturity_class   | C (Candidate)                                     |
| equation_type    | lookup                                            |
| promotion_status | causal                                            |
| parameters       | 14 (one record per carcinogen class)              |
| input_ports      | 3 (exposure_vector, route_of_exposure, dose_magnitude) |
| output_ports     | 3 (carcinogen_class_tag, exposure_intensity_score, route_tag) |
| evidence sources | exposure_database.json (ExposoGraph 2.0 v0.0.5)  |

Covers 14 carcinogen classes (PAH, Nitrosamines, Aflatoxins, Benzene/Aromatic amines, Arsenic,
Formaldehyde, Acrylamide, Vinyl chloride, Chromium VI, Cadmium, Nickel, Asbestos, UV radiation,
Ethanol/Acetaldehyde). Each parameter record includes `default_intensity`, `route`, and
`carcinogen_class`.

---

### EG3.MOD.BIOTRANS.FLUX.v1

| Field            | Value                                                    |
|------------------|----------------------------------------------------------|
| maturity_class   | E (Executable)                                           |
| equation_type    | score-based / michaelis_menten                           |
| promotion_status | executable                                               |
| parameters       | 37 (Km/Vmax/CLint for 12 phase-I + 7 phase-II enzymes)   |
| input_ports      | 4 (substrate_node_id, enzyme_node_id, gsh_pool_mM, dose_mg_per_kg) |
| output_ports     | 3 (flux_score, metabolite_tag, gsh_delta)                |
| internal_state   | gsh_pool_mM: 7.5 (baseline), threshold 1.5, synthesis 40 µmol/h/g, t½ 2.5 h |
| evidence sources | kinetic_parameters.json; PMC9412641, PMC3525274          |

Michaelis–Menten parameters sourced from kinetic_parameters.json with full enzyme–substrate
coverage. Standard genotype activity scale applied (PM=0.0, IM=0.5, NM=1.0, RM=1.5, UM=2.0).
ALDH2\*2 heterozygote special case: 25% wildtype activity (dominant-negative; PMC3525274).

---

### EG3.MOD.MECHANISM.INTERACTION.v1

| Field            | Value                                                    |
|------------------|----------------------------------------------------------|
| maturity_class   | C (Candidate)                                            |
| equation_type    | rule-based                                               |
| promotion_status | causal                                                   |
| parameters       | 86 (34 Ki_curated + 52 Ki_assumed_equal_Km competitive inhibition pairs) |
| input_ports      | 3 (active_carcinogen_set, enzyme_node_id, gsh_pool_mM)   |
| output_ports     | 4 (inhibition_flag, competing_substrate_set, induction_fold, gsh_depletion_flag) |
| gsh_depletion    | baseline 7.5 mM, threshold 1.5 mM (PMC9412641)          |
| evidence sources | interaction_parameters.json (competitive_inhibition + gsh_depletion sections) |

Coverage summary: 91 total enzyme–substrate pairs; 34 Ki values curated from primary literature;
57 Ki values assumed equal to Km (conservative approximation for unmeasured Ki). 12 phase-I
enzymes and 7 phase-II enzymes represented.

---

### EG3.MOD.MECHANISM.OXSTRESS.v1

| Field            | Value                                                    |
|------------------|----------------------------------------------------------|
| maturity_class   | C (Candidate)                                            |
| equation_type    | rule-based                                               |
| promotion_status | causal                                                   |
| mechanism_type   | oxidative_stress                                         |
| parameters       | 7 (ROS threshold, NRF2 induction fold, GSTP1 induction, GSH threshold; 4 carcinogen classes) |
| input_ports      | 3 (carcinogen_class_tag, gsh_pool_mM, ros_burden_score)  |
| output_ports     | 3 (oxidative_stress_flag, nrf2_activation_flag, gsh_depletion_severity) |
| evidence sources | interaction_parameters.json (gsh_depletion section); PMID 29126897 |

Carries the oxidative stress branch of mechanism evaluation: GSH pool depletion, ROS-mediated
DNA damage signaling, NRF2 induction, and GSTP1 upregulation.

---

### EG3.MOD.TISSUE.SUBGRAPH.v1

| Field            | Value                                                           |
|------------------|-----------------------------------------------------------------|
| maturity_class   | C (Candidate)                                                   |
| equation_type    | lookup                                                          |
| promotion_status | causal                                                          |
| parameters       | 53 (per-gene expression weight across 8 tissues)                |
| input_ports      | 2 (gene_node_id, tissue_context)                               |
| output_ports     | 1 (tissue_expression_weight)                                    |
| tissues          | Liver, Lung, Prostate, Bladder, Colon, Breast, Kidney, Esophagus |
| evidence sources | tissue_expression_data.json; GTEx v8; Human Protein Atlas       |

Full per-gene per-tissue expression weight table for 53 CYP/GST/SULT/UGT/NQO/ALDH/ADH
metabolizing enzyme genes across 8 cancer-relevant tissues. Weights are normalized expression
values (0–1 scale, 1.0 = highest expresser).

---

### EG3.MOD.MODIFIER.POPGEN.v1

| Field            | Value                                                               |
|------------------|---------------------------------------------------------------------|
| maturity_class   | C (Candidate)                                                       |
| equation_type    | lookup multiplier                                                   |
| promotion_status | causal                                                              |
| parameters       | 27 (per-enzyme phenotype: activity_multiplier, frequency, alleles)  |
| input_ports      | 2 (enzyme_node_id, genotype_phenotype)                              |
| output_ports     | 1 (activity_multiplier)                                             |
| evidence sources | interaction_parameters.json (genotype_modifiers); kinetic_parameters.json (special_cases) |

Standard 5-phenotype scale: PM=0.0, IM=0.5, NM=1.0, RM=1.5, UM=2.0. Allele assignments and
population frequencies from kinetic_parameters.json and interaction_parameters.json. ALDH2\*2
special case modeled with dominant-negative heterozygote activity = 0.25 (PMC3525274).
Covers CYP1A1, CYP1B1, CYP2A6, CYP2D6, CYP2E1, CYP3A4, GSTM1, GSTT1, GSTP1,
NQO1, NAT1, NAT2, ALDH2, SULT1A1, UGT1A1, ADH1B, SLC22A2, ABCB1, TP53, XRCC1,
BRCA1, MTHFR, DNMT3A.

---

### EG3.MOD.OUTCOME.MUTSIG.v1

| Field            | Value                                                              |
|------------------|--------------------------------------------------------------------|
| maturity_class   | C (Candidate)                                                      |
| equation_type    | lookup                                                             |
| promotion_status | causal                                                             |
| parameters       | 28 (12 COSMIC SBS signatures + 16 carcinogen→signature map entries)|
| input_ports      | 3 (carcinogen_class_tag, tissue_context, dna_adduct_tag)           |
| output_ports     | 3 (primary_signature, secondary_signatures, confidence_tier)       |
| evidence sources | mutational_signatures.json; COSMIC Mutational Signatures v3.3      |

COSMIC SBS signatures included: SBS1, SBS2, SBS4, SBS5, SBS6, SBS7a, SBS13, SBS18, SBS22,
SBS24, SBS26, SBS92. Carcinogen class → SBS signature map covers PAH (SBS4), Nitrosamines
(SBS92), Aflatoxins (SBS24), Benzene (SBS18), Arsenic (SBS22), Formaldehyde (SBS84),
Acrylamide (SBS5), Vinyl chloride (SBS4/SBS18), Chromium VI (SBS18), UV radiation (SBS7a),
Ethanol/Acetaldehyde (SBS2).

---

### EG3.MOD.EVIDENCE.PROVENANCE.v1

| Field            | Value                                                               |
|------------------|---------------------------------------------------------------------|
| maturity_class   | D (Defined)                                                         |
| equation_type    | lookup                                                              |
| promotion_status | registry                                                            |
| parameters       | 106 (15 biomarker entries + 91 parameter provenance pairs)          |
| input_ports      | 2 (parameter_id, evidence_tier)                                     |
| output_ports     | 1 (provenance_record)                                               |
| evidence sources | parameter_provenance.json; biomarker_mapping.json                   |

Serves as the evidence registry for all Phase 3 parameters. 15 biomarker entries cover DNA
adducts, protein adducts, urinary metabolites, and oxidative stress markers. 91 parameter
provenance pairs link parameter IDs to PMID/DOI, evidence tier (Tier 1–3), and primary
data sources.

---

## Execution Edge Layer

**File**: `data/registry/execution_edges.json`  
**Total edges**: 74  
**version_origin**: `ExposoGraph 3.0 Phase 3 (module recast)`

### Edge counts by type

| Type                    | Count | Edge family |
|-------------------------|-------|-------------|
| competes_at             | 30    | causal      |
| detoxifies              | 15    | causal      |
| bioactivates            | 12    | causal      |
| feeds_input             | 5     | execution   |
| maps_to_twin_state      | 5     | execution   |
| consumes_parameter      | 3     | execution   |
| emits_output            | 2     | execution   |
| writes_observation      | 2     | execution   |
| **Total**               | **74**|             |

### Edge family breakdown

| Edge family  | Count |
|--------------|-------|
| causal       | 57    |
| execution    | 17    |

### Enzyme–substrate mapping: mapped vs unmapped

**Mapped**: 27 enzyme→substrate pairs (both endpoints are valid registry node IDs).
Covers `bioactivates` (12 edges) and `detoxifies` (15 edges) with Km/Vmax attributes from
`kinetic_parameters.json`.

**Unmapped pairs (10)** — not added to execution_edges.json, reasons documented below:

| Pair                              | Reason unmapped                                   |
|-----------------------------------|---------------------------------------------------|
| EPHX1 / BaP-7,8-oxide             | BaP-7,8-oxide is a reaction intermediate, not a registry node |
| GSTA1 / AFBO                      | GSTA1 not in registry (GSTM1/GSTP1/GSTT1 present) |
| ALDH1A1 / Acetaldehyde            | ALDH1A1 not in registry (ALDH2 present)           |
| CYP2A13_methyl / various          | Variant key, not an enzyme node ID                |
| carbonyl_reduction / various      | Pathway descriptor, not an enzyme node ID         |
| ADH5_formaldehyde / Formaldehyde  | ADH5 not in registry (ADH1B present)              |
| CYP2F2_lung / various             | Tissue-specific variant; CYP2F1 present, CYP2F2 absent |
| AS3MT / Inorganic arsenic         | Substrate text "Inorganic arsenic" does not match registry node "As" |
| general_ROS / various             | Descriptive pathway key, not an enzyme node ID    |
| AhR_binding / various             | Receptor binding key, not an enzyme node ID       |

---

## Schema Extensions (Phase 3)

### schema/module.schema.json

Extended to require 22 fields:
`module_id`, `module_name`, `module_class`, `maturity_class`, `extends`, `scope`, `version`,
`evidence_bundle`, `input_ports`, `output_ports`, `parameters`, `equation_type`, `update_rule`,
`uncertainty`, `validation_status`, `cedt_mapping`, `causal_role_map`, `graph_nodes`,
`graph_edges`, `causal_edges`, `internal_state`, `promotion_status`.

### schema/execution_edge.schema.json (NEW)

New schema file for Phase 3 execution edges. Required fields:
`edge_id`, `source`, `target`, `type`, `edge_family`, `promotion_status`, `version_origin`.

---

## Script Updates (Phase 3)

### scripts/validate.py

- Added Section 5: validates `execution_edges.json` (existence, edge count > 0, required fields,
  schema validation against `execution_edge.schema.json`)
- Added Section 6: Phase 3 module completeness check (22 required fields per module, schema
  validation, parameter counts, equation_type reporting)
- Added Section 10: app/data mirror checks (modules mirror + execution_edges mirror; non-fatal warnings)
- Baseline checks unchanged: 212 nodes / 313 edges / promotion_status=registry

### scripts/build_registry_summary.py

- Added execution edges block: total count, breakdown by type and edge_family, bioactivates /
  detoxifies / competes_at / module-execution breakdown
- Per-module Phase 3 reporting: params, ports, completeness percentage (N/22 fields), equation_type,
  promotion_status
- Updated acceptance line: `212 nodes / 313 baseline edges + 74 execution edges + 8 module records`
- Updated `registry_summary.json` output with `execution_edge_count`, `execution_edges` breakdown,
  and per-module `phase3_completeness_pct`

---

## Browser App Updates (Phase 3)

**File**: `app/exposograph-3-browser.html`

New capabilities added to the zero-build/CDN-only single-file app:

1. **Module Records tab**: browse all 8 modules with maturity badge (E/D/C), module_class,
   parameter count, port counts, promotion_status. Module detail panel shows full parameter table,
   ports, internal state, CEDT mapping, and evidence bundle.
2. **Execution Edges tab**: browse all 74 execution edges; filter by edge_family and type; edge
   detail shows all kinetic attributes (Km, Vmax, Ki, fold_induction).
3. **Toggle execution edges** button on Registry Nodes tab: shows/hides execution edges (⚡)
   for the selected node in the detail pane, with Km/Vmax/Ki displayed inline.
4. Header stat badge for execution edge count.
5. Phase indicator updated to "Phase 3" in header.

**Data mirror** (`app/data/`):
- `app/data/modules/` — 8 module JSON files (EG3_MOD_*_v1.json)
- `app/data/registry/execution_edges.json` — 74 execution edges
- `app/data/registry/registry_summary.json` — updated Phase 3 summary

---

## Baseline Immutability Confirmation

The following files were **not modified** in Phase 3 (confirmed by validate.py checks):

- `data/registry/registry_graph.json` — 212 nodes / 313 edges (bundle: Registry Graph v2-compat)
- `data/registry/nodes.json` — 212 nodes
- `data/registry/edges.json` — 313 edges

All baseline nodes carry `promotion_status=registry` and
`version_origin=ExposoGraph 2.0 (v0.0.5; 212 nodes / 313 edges reference bundle)`.

---

## Data Sources

| Source file                    | Data used in Phase 3                                          |
|-------------------------------|---------------------------------------------------------------|
| `exposure_database.json`       | 14 carcinogen class records → EG3.MOD.EXPOSURE.WAVE2.v1       |
| `kinetic_parameters.json`      | Km/Vmax/CLint for 19 enzymes → BIOTRANS_FLUX + execution edges|
| `interaction_parameters.json`  | Ki (competitive inhibition) + GSH depletion + genotype modifiers |
| `tissue_expression_data.json`  | 53 genes × 8 tissues → TISSUE_SUBGRAPH + MODIFIER_POPGEN      |
| `mutational_signatures.json`   | 12 COSMIC SBS + carcinogen_class_map → OUTCOME_MUTSIG          |
| `parameter_provenance.json`    | 91 provenance pairs → EVIDENCE_PROVENANCE                      |
| `biomarker_mapping.json`       | 15 biomarker entries → EVIDENCE_PROVENANCE                     |
| GTEx v8 / Human Protein Atlas  | Expression weights (TISSUE_SUBGRAPH)                           |
| COSMIC Signatures v3.3         | SBS mutational signature definitions (OUTCOME_MUTSIG)          |
| PMC9412641                     | GSH pool kinetics (baseline 7.5 mM, synthesis 40 µmol/h/g)    |
| PMC3525274                     | ALDH2\*2 dominant-negative heterozygote activity = 25%        |
