# ExposoGraph 3.0 — Phase 4 Notes: Causal Layer Promotion

## Overview

Phase 4 promotes high-confidence directional relations from the registry and execution layers into the Layer-2 causal layer, binds each promoted edge to a motif from the expanded motif library, and exposes the causal projection in a new browser tab. Promotion is strictly evidence-governed: no edge is promoted without meeting both the directional-semantics criterion and the evidence-support criterion.

---

## Promotion Rule (verbatim)

> An edge is PROMOTED to the causal layer iff BOTH conditions hold:
> (1) Directional semantics: its predicate is one of {ACTIVATES, DETOXIFIES, FORMS_ADDUCT, REPAIRS, INDUCES, INHIBITS, TRANSPORTS} (baseline) OR {bioactivates, detoxifies, competes_at} (Phase 3 execution).
> (2) Evidence support: baseline edge has non-empty provenance OR a non-null evidence_id; OR Phase 3 edge has confidence in {high, medium} AND non-empty sources.
> Edges failing the evidence test are NOT promoted — they remain in the registry as promotion_status='registry'.

---

## Promoted vs. Retained Tally

| Layer | Directional edges | Promoted to causal | Retained in registry |
|---|---|---|---|
| Registry baseline | 225 | 156 | 69 |
| Phase 3 execution | 57 | 13 | 44 |
| **Total** | **282** | **169** | **113** |

### Promoted count by causal_relation

| causal_relation | Promoted edges |
|---|---|
| activates | 98 |
| detoxifies | 31 |
| damages | 21 |
| mediates | 14 |
| precedes | 2 |
| increases | 2 |
| decreases | 1 |
| **Total** | **169** |

### Promoted count by source_predicate

| source_predicate | Layer | Promoted |
|---|---|---|
| ACTIVATES | registry_baseline | 89 |
| DETOXIFIES | registry_baseline | 27 |
| FORMS_ADDUCT | registry_baseline | 21 |
| REPAIRS | registry_baseline | 14 |
| TRANSPORTS | registry_baseline | 2 |
| INDUCES | registry_baseline | 2 |
| INHIBITS | registry_baseline | 1 |
| bioactivates | phase3_execution | 9 |
| detoxifies | phase3_execution | 4 |

---

## Retained-in-Registry Counts with Reasons

### Baseline edges retained (69 total)

**Reason for all: no_provenance_no_evidence_id** — the edge has provenance=[] and evidence_id=null, failing condition (2) of the promotion rule.

| Predicate | Retained count |
|---|---|
| DETOXIFIES | 20 |
| FORMS_ADDUCT | 16 |
| ACTIVATES | 15 |
| REPAIRS | 11 |
| TRANSPORTS | 7 |

#### Explicitly retained directional-but-unevidenced baseline edges

| Source | Target | Predicate | Reason |
|---|---|---|---|
| BaP | Oxo_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| Testosterone | Oxo_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| CYP1A1 | 2OHE2 | ACTIVATES | no provenance, no evidence_id |
| CYP3A4 | HydroxyTestosterone | DETOXIFIES | no provenance, no evidence_id |
| EPHX1 | BaP_diol | ACTIVATES | no provenance, no evidence_id |
| EPHX1 | AFB1_epoxide | DETOXIFIES | no provenance, no evidence_id |
| CYP17A1 | DHEA | ACTIVATES | no provenance, no evidence_id |
| SRD5A2 | DHT | ACTIVATES | no provenance, no evidence_id |
| SRD5A1 | DHT | ACTIVATES | no provenance, no evidence_id |
| CYP19A1 | E2_from_T | ACTIVATES | no provenance, no evidence_id |
| CYP3A5 | HydroxyTestosterone | DETOXIFIES | no provenance, no evidence_id |
| AKR1C3 | Testosterone | ACTIVATES | no provenance, no evidence_id |
| GSTM1 | NOH_4ABP | DETOXIFIES | no provenance, no evidence_id |
| GSTM1 | AFB1_GSH | DETOXIFIES | no provenance, no evidence_id |
| GSTT1 | AFB1_GSH | DETOXIFIES | no provenance, no evidence_id |
| GSTT1 | Benzene_oxide | DETOXIFIES | no provenance, no evidence_id |
| GSTT1 | Chloroethylene_oxide | DETOXIFIES | no provenance, no evidence_id |
| NAT2 | NOH_PhIP | ACTIVATES | no provenance, no evidence_id |
| NAT2 | PhIP_NAc | DETOXIFIES | no provenance, no evidence_id |
| NAT2 | 4ABP | DETOXIFIES | no provenance, no evidence_id |
| NAT1 | NOH_4ABP | ACTIVATES | no provenance, no evidence_id |
| SULT1A1 | NOH_PhIP | ACTIVATES | no provenance, no evidence_id |
| SULT1A1 | HydroxyE2 | DETOXIFIES | no provenance, no evidence_id |
| UGT1A1 | PhIP_gluc | DETOXIFIES | no provenance, no evidence_id |
| UGT1A1 | HydroxyE2 | DETOXIFIES | no provenance, no evidence_id |
| UGT2B7 | NNK_hydroxyl | DETOXIFIES | no provenance, no evidence_id |
| NQO1 | E2_quinone | DETOXIFIES | no provenance, no evidence_id |
| NQO1 | Benzoquinone | DETOXIFIES | no provenance, no evidence_id |
| COMT | E2_methyl | DETOXIFIES | no provenance, no evidence_id |
| UGT2B17 | Testosterone_gluc | DETOXIFIES | no provenance, no evidence_id |
| UGT2B15 | DHT_gluc | DETOXIFIES | no provenance, no evidence_id |
| HSD3B2 | Androstenedione | ACTIVATES | no provenance, no evidence_id |
| AKR1C2 | 3aAdiol | DETOXIFIES | no provenance, no evidence_id |
| ABCB1 | BPDE_GSH | TRANSPORTS | no provenance, no evidence_id |
| ABCB1 | NNK_hydroxyl | TRANSPORTS | no provenance, no evidence_id |
| ABCB1 | DHT_gluc | TRANSPORTS | no provenance, no evidence_id |
| ABCC2 | BPDE_GSH | TRANSPORTS | no provenance, no evidence_id |
| ABCC2 | AFB1_GSH | TRANSPORTS | no provenance, no evidence_id |
| ABCG2 | PhIP_gluc | TRANSPORTS | no provenance, no evidence_id |
| ABCG2 | Testosterone_gluc | TRANSPORTS | no provenance, no evidence_id |
| XRCC1 | PhIP_dG | REPAIRS | no provenance, no evidence_id |
| XRCC1 | ABP_dG | REPAIRS | no provenance, no evidence_id |
| XRCC1 | BQ_dG | REPAIRS | no provenance, no evidence_id |
| XRCC1 | etheno_dA | REPAIRS | no provenance, no evidence_id |
| XPC | BPDE_dG | REPAIRS | no provenance, no evidence_id |
| XPC | AFB1_Gua | REPAIRS | no provenance, no evidence_id |
| XPC | DMBA_dA | REPAIRS | no provenance, no evidence_id |
| ERCC2 | BPDE_dG | REPAIRS | no provenance, no evidence_id |
| ERCC2 | DMBA_dA | REPAIRS | no provenance, no evidence_id |
| OGG1 | Oxo_dG | REPAIRS | no provenance, no evidence_id |
| MGMT | O6_methyl_dG | REPAIRS | no provenance, no evidence_id |
| BPDE | BPDE_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| NOH_PhIP | PhIP_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| NOH_4ABP | ABP_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| NNK_hydroxyl | O6_methyl_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| NNK_hydroxyl | POB_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| AFB1_epoxide | AFB1_Gua | FORMS_ADDUCT | no provenance, no evidence_id |
| HydroxyE2 | E2_quinone | ACTIVATES | no provenance, no evidence_id |
| E2_quinone | E2_depurin | FORMS_ADDUCT | no provenance, no evidence_id |
| Benzene_oxide | HQ | ACTIVATES | no provenance, no evidence_id |
| HQ | Benzoquinone | ACTIVATES | no provenance, no evidence_id |
| Benzoquinone | BQ_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| Chloroethylene_oxide | etheno_dA | FORMS_ADDUCT | no provenance, no evidence_id |
| Chloroethylene_oxide | etheno_dC | FORMS_ADDUCT | no provenance, no evidence_id |
| NDMA_hydroxyl | O6_methyl_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| DMBA_diol_epoxide | DMBA_dA | FORMS_ADDUCT | no provenance, no evidence_id |
| MeIQx_acetoxy | PhIP_dG | FORMS_ADDUCT | no provenance, no evidence_id |
| E2_from_T | HydroxyE2 | ACTIVATES | no provenance, no evidence_id |
| E2_from_T | E2_depurin | FORMS_ADDUCT | no provenance, no evidence_id |

### Phase 3 execution edges retained (44 total)

| Edge ID | Source | Target | Predicate | Confidence | Reason |
|---|---|---|---|---|---|
| EG3.EXEC.EDGE.0002 | CYP1B1 | BaP | bioactivates | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0003 | GSTM1 | BPDE | detoxifies | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0004 | GSTP1 | BPDE | detoxifies | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0007 | CYP3A4 | AFB1 | detoxifies | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0012 | ALDH2 | Acetaldehyde | detoxifies | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0013 | ADH5 | Formaldehyde | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0015 | CYP2A6 | NNK | bioactivates | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0021 | SULT1A1 | NOH_PhIP | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0022 | NAT2 | PhIP | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0023 | CYP2E1 | Benzene | bioactivates | moderate | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0024 | NQO1 | Benzoquinone | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0025 | GSTT1 | Benzene_oxide | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0026 | CYP2E1 | TCE | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0027 | GSTT1 | TCE | detoxifies | low | confidence not in {high,medium} |
| EG3.EXEC.EDGE.0028–0057 | Various | Various | competes_at | None | no confidence, no sources (all 30 competes_at edges) |

Note: the 30 `competes_at` edges (EG3.EXEC.EDGE.0028–0057) all have confidence=null and sources=null, failing condition (2) of the evidence rule. The rule uses the vocabulary term `decreases` for competes_at, but because they lack evidence they are not promoted.

---

## Final Motif Library

| Motif ID | Name | causal_relation | Edge types mapped | Status | Edges using |
|---|---|---|---|---|---|
| EG3.MOTIF.001 | Exposure → Metabolite → Target Damage | activates | ACTIVATES, FORMS_ADDUCT, bioactivates | active | 119 |
| EG3.MOTIF.002 | Detoxification / Competing Elimination | detoxifies | DETOXIFIES, INHIBITS, detoxifies, competes_at | active | 32 |
| EG3.MOTIF.003 | Pathway → Phenotype / Outcome | precedes | TRANSPORTS, REPAIRS | active | 2 |
| EG3.MOTIF.004 | Modifier → Susceptibility | modifies | INHIBITS, DETOXIFIES, competes_at | active | 0 |
| EG3.MOTIF.005 | Tissue Context → Outcome | modifies | ACTIVATES, FORMS_ADDUCT | active | 0 |
| EG3.MOTIF.006 | Repair → Damage Mitigation | mediates | REPAIRS | active | 14 |
| EG3.MOTIF.007 | Induction → Increased Activation | increases | INDUCES, ACTIVATES | active | 2 |

Notes:
- M004 (Modifier→Susceptibility) and M005 (Tissue-Context→Outcome) have 0 promoted edges at this phase. These motifs represent modifying relationships that require genotype-level or tissue-expression-level contextual edges to be populated. The registry baseline lacks explicit genotype→enzyme edges with evidence sufficient for promotion; tissue context edges are informational (PATHWAY type), not directional. These motifs are library-ready for Phase 5 curation.
- Motif IDs are assigned per primary role: FORMS_ADDUCT maps to M001 (damage step in Exposure→Metabolite→Damage chain), REPAIRS to M006, INDUCES to M007, TRANSPORTS to M003.

---

## Per-Module Causal Edge Counts

| Module ID | Causal edges | Maturity class | Validation status |
|---|---|---|---|
| EG3.MOD.BIOTRANS.FLUX.v1 | 150 | E (unchanged) | curated-causal |
| EG3.MOD.EVIDENCE.PROVENANCE.v1 | 165 | C | curated-causal |
| EG3.MOD.EXPOSURE.WAVE2.v1 | 13 | C | curated-causal |
| EG3.MOD.MECHANISM.INTERACTION.v1 | 9 | C | curated-causal |
| EG3.MOD.MECHANISM.OXSTRESS.v1 | 14 | C | curated-causal |
| EG3.MOD.MODIFIER.POPGEN.v1 | 9 | C | curated-causal |
| EG3.MOD.OUTCOME.MUTSIG.v1 | 0 | C | curated |
| EG3.MOD.TISSUE.SUBGRAPH.v1 | 13 | C | curated-causal |

**Notes on module counts:**
- The Flux module (EG3.MOD.BIOTRANS.FLUX.v1) retains maturity E (Executable) as specified — it is not downgraded. It gains 150 causal edges from its graph_edges and node-set coverage.
- The Evidence Provenance module (EG3.MOD.EVIDENCE.PROVENANCE.v1) has 165 causal edges because the majority of baseline directional edges carry EG3.MOD.EVIDENCE.PROVENANCE.v1 in their module_membership (consistent with Phase 1 design where all evidenced edges belong to the provenance module).
- The Outcome Mutsig module (EG3.MOD.OUTCOME.MUTSIG.v1) has 0 causal edges: its graph nodes are predominantly DNA adduct target nodes (BPDE_dG, PhIP_dG, ABP_dG, etc.) that appear as targets of FORMS_ADDUCT edges, but those target nodes' modules are assigned to the Flux/Biotrans scope, not Mutsig. Mutsig's causal scope will be populated in a future phase when mutational-signature linking edges (Adduct→Signature) are formalized.

---

## PMIDs Attached to Promoted Edges (29 unique)

The following PMIDs/PMC IDs appear in the `evidence.pmid_refs` field of at least one promoted causal edge. These are sourced directly from the registry edge records and module evidence bundles — no PMIDs were fabricated.

| PMID/PMC reference | Evidence context |
|---|---|
| PMC1829392 | CYP1A2/CYP1A1/CYP1B1 → PhIP bioactivation (Phase 3) |
| PMC3525274 | ADH1B/ALDH2 kinetics for ethanol/acetaldehyde (Phase 3) |
| PMC9469084 | AFB1 CYP3A4/CYP1A2 kinetics — Lootens 2022 (Phase 3) |
| PMID 10950860 (Koop 1992) | CYP2E1/benzene kinetics (Phase 3 module evidence) |
| PMID 7865919 | CYP3A4/AFB1 kinetics — Gallagher 1994 (Phase 3 module evidence) |
| PMID 9187241 | CYP1A1/BaP kinetics — Shimada 1996 (Phase 3 module evidence) |
| PMID:10064842 | MDA → M1_dG adduct formation |
| PMID:10220571 | Cyclophosphamide activation/elimination pathway |
| PMID:10417614 | ROS_metal → 8-OHdG oxidative adduct |
| PMID:12860588 | Urethane/vinyl carbamate → etheno adduct pathway |
| PMID:12960109 | Busulfan → DNA ICL mustard adduct |
| PMID:12975327 | CYP2A13 → NNK bioactivation (Phase 3) |
| PMID:1444447 | CYP2E1 → NDMA bioactivation (Phase 3) |
| PMID:17872912 | Glycidamide/XRCC1 N7-GA-dG acrylamide pathway |
| PMID:1937131 | ALDH2/GSTP1 → 4-HNE detoxification |
| PMID:19705912 | Acrolein → Acr-dG adduct; XRCC1 repair |
| PMID:20577029 | CYP2E1 → NDMA bioactivation (Phase 3) |
| PMID:20663906 | TCE → DCVC/renal DNA damage pathway |
| PMID:21222454 | Formaldehyde → N2-HOMedG adduct |
| PMID:21538843 | Furfural/SULT1A1 → SMF |
| PMID:21801416 | GSTM1/GSTT1/GSTO1/GSTO2 arsenic methylation pathway |
| PMID:2185966 | MNU/Methyldiazonium → N7/O6-methyl-dG adducts |
| PMID:34730462 | AS3MT/Arsenic methylation → MMA_V/DMA_V |
| PMID:40390554 | NDMA/Hydroxymethylnitrosamine → O6-methyl-dG / CYP2E1 |
| PMID:7523912 | Chlorambucil aziridinium → DNA ICL mustard |
| PMID:7614537 | Acrylamide → Glycidamide activation |
| PMID:8635461 | Sulfur mustard episulfonium → DNA ICL |
| PMID:8975785 | AFB1 epoxidation kinetics (Phase 3) |
| PMID:9327140 | Temozolomide → MTIC → Methyldiazonium |

---

## Directional-but-Unevidenced Edges: Explicit Registry-Only List

The following edges have directional semantics (meet criterion 1) but fail the evidence test (criterion 2). They remain in the registry with promotion_status='registry' and are intentionally NOT promoted to the causal layer.

### Baseline edges (directional, no provenance, no evidence_id)

See the full table in the "Retained-in-Registry Counts" section above (69 baseline edges across FORMS_ADDUCT, ACTIVATES, DETOXIFIES, REPAIRS, TRANSPORTS predicates).

### Phase 3 execution edges (directional, confidence below threshold)

| Edge ID | Edge | Predicate | Confidence | Retention reason |
|---|---|---|---|---|
| EG3.EXEC.EDGE.0002 | CYP1B1 → BaP | bioactivates | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0003 | GSTM1 → BPDE | detoxifies | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0004 | GSTP1 → BPDE | detoxifies | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0007 | CYP3A4 → AFB1 | detoxifies | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0012 | ALDH2 → Acetaldehyde | detoxifies | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0013 | ADH5 → Formaldehyde | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0015 | CYP2A6 → NNK | bioactivates | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0021 | SULT1A1 → NOH_PhIP | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0022 | NAT2 → PhIP | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0023 | CYP2E1 → Benzene | bioactivates | moderate | moderate ≠ high/medium |
| EG3.EXEC.EDGE.0024 | NQO1 → Benzoquinone | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0025 | GSTT1 → Benzene_oxide | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0026 | CYP2E1 → TCE | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0027 | GSTT1 → TCE | detoxifies | low | low ≠ high/medium |
| EG3.EXEC.EDGE.0028–0057 | Various CYP/substrate | competes_at | null | null confidence, null sources (30 edges) |

---

## Files Created / Modified

### New files
- `data/causal/causal_edges.json` — 169 promoted causal edges with full evidence blocks
- `schema/causal_edge.schema.json` — JSON Schema for causal edge records

### Modified files
- `data/causal/motifs.json` — 5 seed motifs promoted to active; 2 new motifs added (M006, M007); all 7 have causal_relation field
- `schema/causal_motif.schema.json` — tightened: causal_relation (enum) + status (enum: seed|active) now required
- `schema/module.schema.json` — added `curated-causal` to validation_status enum
- `data/modules/EG3_MOD_*.json` (8 files) — causal_edges field populated; 7 modules bumped to curated-causal; Flux maturity stays E
- `data/registry/registry_summary.json` — regenerated with Phase 4 causal layer counts
- `scripts/validate.py` — Phase 4 assertions added (baseline frozen at 212/313, endpoint validity, motif_id validity, evidence rule)
- `scripts/build_registry_summary.py` — causal layer counts, motif coverage, per-module causal_edge counts
- `app/exposograph-3-browser.html` — Causal Layer tab added (motif library + filtered causal edge list + detail pane)
- `app/data/causal/motifs.json` — mirrored
- `app/data/causal/causal_edges.json` — mirrored

---

## Acceptance Criteria Verification

- [x] `validate.py` exits 0
- [x] Baseline 212 nodes / 313 edges — unchanged and byte-stable
- [x] Every promoted causal edge has valid endpoint nodes, valid motif_id, promotion_status='causal'
- [x] Every promoted edge satisfies the evidence rule (verified in validate.py assertion d)
- [x] `build_registry_summary.py` shows causal layer counts + 8 modules with causal_edge counts
- [x] `registry_summary.json` includes causal_layer section with by_relation, by_predicate, motif_coverage, pmids_attached
- [x] Motif library: 7 motifs, all status='active', all with valid causal_relation
- [x] 29 unique PMIDs attached — none fabricated
- [x] Browser app has Causal Layer tab with motif library + edge list + detail pane + filters
