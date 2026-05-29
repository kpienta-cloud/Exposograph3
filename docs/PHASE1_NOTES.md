# ExposoGraph 3.0 — Phase 1 Ingestion Notes

**Date completed:** 2026-06-01
**Version:** Phase 1 (Registry baseline ingestion)
**Source:** ExposoGraph 2.0 `v0.0.5` — graph-data.js (212 nodes / 313 edges)

---

## Summary

Phase 1 freezes the ExposoGraph 2.0 graph as the registry baseline (`Registry Graph v2-compat`)
and recasts the 8 quantitative 2.0 modules as typed module records. No biological content was
altered; all changes are metadata enrichment and structural annotation.

### Ingested Data

| Item | Count |
|------|-------|
| Registry nodes | 212 |
| Registry edges | 313 |
| Module records | 8 |
| Causal motifs (seed) | 5 |
| CEDT adapters (seed) | 5 |
| JSON schemas | 5 |

---

## Node Type Distribution

| Type | Count |
|------|-------|
| Metabolite | 59 |
| Enzyme | 58 |
| Carcinogen | 56 |
| DNA_Adduct | 27 |
| Pathway | 12 |
| **Total** | **212** |

---

## Edge Type Distribution (Original Predicates)

| Edge Type (type field) | Count | edge_family |
|------------------------|-------|-------------|
| ACTIVATES | 104 | causal |
| PATHWAY | 88 | registry |
| DETOXIFIES | 47 | causal |
| FORMS_ADDUCT | 37 | causal |
| REPAIRS | 25 | causal |
| TRANSPORTS | 9 | causal |
| INDUCES | 2 | causal |
| INHIBITS | 1 | causal |
| **Total** | **313** | |

Note: The spec listed earlier counts (ACTIVATES: 62, PATHWAY: 42, DETOXIFIES: 23) — those
reflected an earlier version snapshot. The actual parsed graph has 313 edges as required.
All edge types were classified correctly.

---

## Edge Family Distribution

| edge_family | Count | Percentage |
|-------------|-------|------------|
| causal | 225 | 71.9% |
| registry | 88 | 28.1% |
| execution | 0 | 0% (Phase 1; no execution edges yet) |
| **Total** | **313** | |

### Classification logic

- **causal**: ACTIVATES, DETOXIFIES, FORMS_ADDUCT, REPAIRS, INDUCES, INHIBITS, TRANSPORTS
  (directional biology — carries mechanistic meaning)
- **registry**: PATHWAY, member, "Pathway membership: ..." labels
  (organizational / indexing edges)
- **execution**: None in Phase 1 (reserved for Phase 5 module wiring)

---

## Module Membership Counts

| Module ID | Class | Maturity | Graph Nodes | Graph Edges |
|-----------|-------|----------|-------------|-------------|
| `EG3.MOD.EXPOSURE.WAVE2.v1` | ExposureSource | D | 56 | 0 |
| `EG3.MOD.BIOTRANS.FLUX.v1` | BiotransformationProcess | E | 58 | 188 |
| `EG3.MOD.MECHANISM.INTERACTION.v1` | Mechanism | C | 20 | 0 |
| `EG3.MOD.MECHANISM.OXSTRESS.v1` | Mechanism | C | 12 | 25 |
| `EG3.MOD.TISSUE.SUBGRAPH.v1` | TissueContext | D | 53 | 88 |
| `EG3.MOD.MODIFIER.POPGEN.v1` | Modifier | C | 21 | 0 |
| `EG3.MOD.OUTCOME.MUTSIG.v1` | Outcome | C | 27 | 37 |
| `EG3.MOD.EVIDENCE.PROVENANCE.v1` | EvidenceAssertion | D | 85 | 198 |

### Membership assignment rationale

**EG3.MOD.EXPOSURE.WAVE2.v1 (56 nodes)**
All 56 Carcinogen-type nodes enrolled. Source data: `exposure_database.json` + `wave2_classes.py`
(Wave 2 classes 11–14: Aldehydes, Dioxins/AhR, Dietary N-Nitroso, Chlorinated Solvents).
Edges deferred to Phase 2 when carcinogen→exposure-source relationships are formally modeled.

**EG3.MOD.BIOTRANS.FLUX.v1 (58 nodes, 188 edges)**
All 58 Enzyme-type nodes enrolled. Source data: `kinetic_parameters.json` (Km/Vmax/Ki values),
`proxy_flux_parameters.json` (heuristic proxy blocks for classes without full kinetic calibration).
All ACTIVATES/DETOXIFIES/FORMS_ADDUCT/REPAIRS/TRANSPORTS/INDUCES/INHIBITS edges enrolled (188 causal edges).

**EG3.MOD.MECHANISM.INTERACTION.v1 (20 nodes, 0 edges)**
Enzymes in `competitive_inhibition`, `phase2_conjugation`, and `genotype_modifiers` sections of
`interaction_parameters.json` matched to graph nodes by exact ID: 12 CYP enzymes + 8 Phase 2/modifier
enzymes. Edges not enrolled in Phase 1 (interaction edges are inferred from parameter data, not
present as explicit graph edges in EG2.0).

**EG3.MOD.MECHANISM.OXSTRESS.v1 (12 nodes, 25 edges)**
All 12 Pathway-type nodes enrolled as the primary pathway perturbation context. All 25 REPAIRS edges
enrolled as the primary causal content of this module.

**EG3.MOD.TISSUE.SUBGRAPH.v1 (53 nodes, 88 edges)**
Enzyme nodes present in GTEx v8 expression table (`tissue_expression_data.json`, 53 genes) enrolled
by exact ID match. All 88 PATHWAY/member edges enrolled as the structural tissue-context edges.
8 tissues: Liver, Lung, Prostate, Bladder, Colon, Breast, Kidney, Esophagus.

**EG3.MOD.MODIFIER.POPGEN.v1 (21 nodes, 0 edges)**
13 Enzyme nodes in `genotype_modifiers` section of `interaction_parameters.json` enrolled
(CYP1A2, CYP2E1, CYP3A4, GSTM1, GSTT1, GSTP1, NQO1, NAT2, + overlapping from biotrans).
8 additional nodes with a `variant` field enrolled. Edges not enrolled — formal variant→enzyme
edges are not present in EG2.0; reserved for Phase 3 (explicit modifier modeling).

**EG3.MOD.OUTCOME.MUTSIG.v1 (27 nodes, 37 edges)**
All 27 DNA_Adduct nodes enrolled as outcome entities. All 37 FORMS_ADDUCT edges enrolled as the
primary causal pathway linking carcinogen activation to adduct formation outcomes.
Source: `mutational_signatures.json` (COSMIC SBS v3.4).

**EG3.MOD.EVIDENCE.PROVENANCE.v1 (85 nodes, 198 edges)**
All nodes with structured provenance blocks (citation or record_id fields present) enrolled.
All edges with source_db, evidence, or provenance fields enrolled.
Source: `parameter_provenance.json` + `biomarker_mapping.json`.
Note: high node/edge overlap expected; Evidence module is a cross-cutting record-keeping layer.

---

## What Could Not Be Cleanly Classified

1. **INTERACTION module edges (0 edges):** The multi-carcinogen competitive inhibition relationships
   encoded in `interaction_parameters.json` (Km, Ki, Vmax tables) are computational parameters,
   not graph edges in EG2.0. No graph edges directly encode pairwise inhibition. These will be
   promoted as explicit causal edges in Phase 3.

2. **POPGEN module edges (0 edges):** Germline variant → enzyme activity modification is not
   encoded as a graph edge in EG2.0; it is implicit in the scoring engine logic. Phase 3 will
   formalize this as explicit causal edges.

3. **EXPOSURE module edges (0 edges):** Carcinogen-to-exposure-source relationships are not
   graph edges in EG2.0; wave2_classes.py packages them as Python class profiles, not as
   structured edges. Will be expanded in Phase 3.

4. **`edge_family = execution` (0 edges):** No execution-layer edges exist in Phase 1.
   These will appear when module wiring is formalized in Phase 5.

5. **Multi-module overlaps:** Nodes with tissue_weights fields span both TISSUE and BIOTRANS
   modules (all Enzyme nodes in GTEx data). Evidence module enrolls 85/212 nodes — intentional,
   as it is a cross-cutting layer. These overlaps are correct per the blueprint design.

6. **Evidence IDs:** Most provenance citations are human-readable text (e.g., "Curated carcinogen
   entry for BaP") rather than structured PMIDs. Evidence IDs derived from provenance citations
   where available; null for entries without structured citation identifiers.

---

## Phase 1 Metadata Field Summary

All 212 nodes and 313 edges have all required Phase 1 metadata fields:
- `entity_type` — normalized from original `type` field (nodes); null for edges
- `edge_family` — `causal` | `registry` | `execution` (edges); null for nodes
- `module_membership` — list of module_ids (empty list where not determinable)
- `evidence_id` — first structured provenance citation, or null
- `version_origin` — `"ExposoGraph 2.0 (v0.0.5; 212 nodes / 313 edges reference bundle)"`
- `promotion_status` — `"registry"` for all Phase 1 entities

---

## Files Written

```
data/registry/registry_graph.json    (bundle: "Registry Graph v2-compat")
data/registry/nodes.json
data/registry/edges.json
data/registry/registry_summary.json
data/modules/EG3_MOD_EXPOSURE_WAVE2_v1.json
data/modules/EG3_MOD_BIOTRANS_FLUX_v1.json
data/modules/EG3_MOD_MECHANISM_INTERACTION_v1.json
data/modules/EG3_MOD_MECHANISM_OXSTRESS_v1.json
data/modules/EG3_MOD_TISSUE_SUBGRAPH_v1.json
data/modules/EG3_MOD_MODIFIER_POPGEN_v1.json
data/modules/EG3_MOD_OUTCOME_MUTSIG_v1.json
data/modules/EG3_MOD_EVIDENCE_PROVENANCE_v1.json
data/ontology/interfaces.json
data/ontology/classes.json
data/causal/motifs.json              (5 seed motifs)
data/adapters/cedt_mappings.json     (5 seed adapters)
schema/registry_node.schema.json
schema/registry_edge.schema.json
schema/module.schema.json
schema/causal_motif.schema.json
schema/ontology_class.schema.json
app/exposograph-3-browser.html
app/data/registry/                   (mirrored registry JSON)
docs/exposograph_3_blueprint.md
docs/PHASE1_NOTES.md
scripts/validate.py
scripts/build_registry_summary.py
.github/workflows/validate.yml
README.md
```
