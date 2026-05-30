# ExposoGraph 3.0

An ontology-backed, causal, module-oriented evolution of the ExposoGraph platform — designed for carcinogen pathway interpretation, exposure-context integration, and Cancer Ecology Digital Twin interoperability.

**All 6 phases complete. Live app:** [https://kpienta-cloud.github.io/Exposograph3/](https://kpienta-cloud.github.io/Exposograph3/)

---

## Architecture

ExposoGraph 3.0 uses a five-layer architecture:

| Layer | Path | Description |
|-------|------|-------------|
| **Layer 0** — Ontology & Interface | `data/ontology/` | Semantic contracts: base interfaces and entity/module classes |
| **Layer 1** — Registry Graph | `data/registry/` | ExposoGraph 2.0 graph as `Registry Graph v2-compat` baseline |
| **Layer 2** — Causal Graph | `data/causal/` | Promoted causal motifs (seed library) |
| **Layer 3** — Execution/Modules | `data/modules/` | 8 module records with typed scope and evidence bundles |
| **Layer 4** — Digital Twin | `data/adapters/` + `data/execution/` | CEDT adapter mappings and per-scenario twin state vectors |

## Repository Structure

```
Exposograph3/
  README.md
  index.html                              # GitHub Pages root redirect
  .nojekyll                               # GitHub Pages Jekyll bypass
  app/exposograph-3-browser.html          # Browser-first viewer (CDN D3, no build step)
  app/data/registry/                      # Registry JSON mirror for GitHub Pages
  app/data/adapters/                      # Adapter JSON mirror for GitHub Pages
  app/data/execution/                     # Execution JSON mirror for GitHub Pages
  data/ontology/                          # interfaces.json + classes.json
  data/registry/                          # registry_graph.json, nodes.json, edges.json, registry_summary.json
  data/causal/                            # motifs.json (5 seed causal motifs)
  data/modules/                           # 8 module records (EG3.MOD.*)
  data/evidence/                          # Evidence bundles (Phase 2+)
  data/adapters/                          # twin_state_schema.json + cedt_mappings.json
  data/execution/                         # scenarios.json, example_runs.json, twin_states.json
  schema/                                 # JSON schemas for all entity types
  docs/                                   # blueprint.md + PHASE1–PHASE6_NOTES.md
  scripts/                                # validate.py, build_registry_summary.py
  scripts/engine/                         # cedt.py, runner.py, modules.py, aliases.py
  .github/workflows/validate.yml          # CI validation
```

## Roadmap Status — All Phases Complete

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Freeze EG2.0 graph as registry baseline; enrich with metadata |
| **Phase 2** | ✅ Complete | Build interface and ontology layer |
| **Phase 3** | ✅ Complete | Recast EG2.0 modules as formal module records (extended) |
| **Phase 4** | ✅ Complete | Promote high-confidence relationships into causal motifs (169 edges) |
| **Phase 5** | ✅ Complete | Executable engine — Exposure→Flux→MutSig chain; 4 golden runs |
| **Phase 6** | ✅ Complete | CEDT adapters — 8 active adapters, 4 twin state vectors, Pages-ready app |

## Quick Start

```bash
# Install dependencies
pip install jsonschema

# Validate all data (all 14 checks must pass)
python3 scripts/validate.py

# Build registry summary
python3 scripts/build_registry_summary.py

# Browse the graph locally
python3 -m http.server 8080
# Then visit http://localhost:8080/app/exposograph-3-browser.html

# Or use the live GitHub Pages app:
# https://kpienta-cloud.github.io/Exposograph3/
```

## Module Registry (Phase 6)

| Module ID | Class | Maturity | Nodes | Twin-Ready | Description |
|-----------|-------|----------|-------|------------|-------------|
| `EG3.MOD.EXPOSURE.WAVE2.v1` | ExposureSource | D | 56 | false | Wave 2 carcinogen classes (Aldehydes, Dioxins, Nitrosamines, Chlorinated Solvents) |
| `EG3.MOD.BIOTRANS.FLUX.v1` | BiotransformationProcess | **T** | 58 | **true** | Biotransformation/Flux engine (Km/Vmax kinetics, proxy flux) — Phase 6 twin-elevated |
| `EG3.MOD.MECHANISM.INTERACTION.v1` | Mechanism | C | 20 | false | Multi-carcinogen competitive inhibition at shared CYP/GST enzymes |
| `EG3.MOD.MECHANISM.OXSTRESS.v1` | Mechanism | C | 12 | false | Oxidative stress / DNA repair pathway perturbation |
| `EG3.MOD.TISSUE.SUBGRAPH.v1` | TissueContext | D | 53 | false | Tissue-specific expression weights (GTEx v8, 8 tissues, 53 genes) |
| `EG3.MOD.MODIFIER.POPGEN.v1` | Modifier | C | 21 | false | Susceptibility modifiers / population genomics (genotype_modifiers) |
| `EG3.MOD.OUTCOME.MUTSIG.v1` | Outcome | C | 27 | false | Mutational signatures (COSMIC SBS v3.4) + DNA adduct outcomes |
| `EG3.MOD.EVIDENCE.PROVENANCE.v1` | EvidenceAssertion | D | 85 | false | Evidence & provenance records (parameter_provenance, biomarker_mapping) |

**Maturity classes:** C = Lookup/curated, D = Data-backed, E = Executable (deterministic kinetics), T = Twin-adapted

## Registry Statistics (Phase 6)

| Metric | Value |
|--------|-------|
| Registry nodes | 212 |
| Registry edges | 313 |
| Promoted causal edges | 169 |
| Module records | 8 |
| Execution scenarios | 4 |
| Golden runs | 4 |
| CEDT active adapters | 8 |
| Twin state variables | 18 (across 5 layers) |
| Twin state vectors | 4 (one per scenario) |
| Execution edges total | 94 |

## CEDT Digital Twin (Phase 6)

The Cancer Ecology Digital Twin adapter layer bridges ExposoGraph module outputs to a 5-layer twin state vector:

| Layer | Variables | Description |
|-------|-----------|-------------|
| L1 — Exposure Burden | 3 | Carcinogen dose, exposure multiplier, tissue ID |
| L2 — Molecular Processing | 5 | Enzyme activation/detox scores, flux ratio, GSH pool*, oxidative stress* |
| L3 — DNA Damage | 4 | Predicted SBS signatures, adduct burden*, confidence, dominant mutation |
| L4 — Phenotypic Risk | 3 | Cancer risk index, tissue specificity, genomic instability |
| L5 — Population Context | 3 | Genotype risk tier, susceptibility percentile, exposure percentile |

*`null` in all 4 scenarios (INTERACTION/OxStress modules not run — no co-exposure or ROS inputs; documented with `null_reason`)*

## Integrity Constraints

- **Registry baseline:** 212 nodes / 313 edges — byte-stable across all phases
- **Causal projection:** 169 promoted edges — not mutated
- **Phase 5 golden runs:** flux_ratio values preserved at 1e-6 tolerance
- **validate.py:** exits 0 with all 14 check sections passing
- **No fabricated biology:** all numeric twin state values trace to Phase 5 engine outputs

## Blueprint

See `docs/exposograph_3_blueprint.md` for the full architecture specification.
See `docs/PHASE6_NOTES.md` for Phase 6 detailed implementation notes.
