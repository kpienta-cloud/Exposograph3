# ExposoGraph 3.0

An ontology-backed, causal, module-oriented evolution of the ExposoGraph platform — designed for carcinogen pathway interpretation, exposure-context integration, and Cancer Ecology Digital Twin interoperability.

## Architecture

ExposoGraph 3.0 uses a four-layer architecture:

| Layer | Path | Description |
|-------|------|-------------|
| **Layer 0** — Ontology & Interface | `data/ontology/` | Semantic contracts: base interfaces and entity/module classes |
| **Layer 1** — Registry Graph | `data/registry/` | ExposoGraph 2.0 graph as `Registry Graph v2-compat` baseline |
| **Layer 2** — Causal Graph | `data/causal/` | Promoted causal motifs (seed library) |
| **Layer 3** — Execution/Modules | `data/modules/` | 8 module records with typed scope and evidence bundles |

## Repository Structure

```
Exposograph3/
  README.md
  app/exposograph-3-browser.html        # Browser-first viewer (CDN D3, no build step)
  app/data/registry/                    # Registry JSON mirror for GitHub Pages
  data/ontology/                        # interfaces.json + classes.json
  data/registry/                        # registry_graph.json, nodes.json, edges.json, registry_summary.json
  data/causal/                          # motifs.json (5 seed causal motifs)
  data/modules/                         # 8 module records (EG3.MOD.*)
  data/evidence/                        # Evidence bundles (Phase 2+)
  data/adapters/                        # cedt_mappings.json (CEDT adapter seed)
  schema/                               # JSON schemas for all entity types
  docs/                                 # blueprint.md, PHASE1_NOTES.md
  scripts/                              # validate.py, build_registry_summary.py
  .github/workflows/validate.yml        # CI validation
```

## Phase 1 Status

**Phase 1 Complete** — Registry baseline ingested from ExposoGraph 2.0.

- 212 nodes / 313 edges ingested as `Registry Graph v2-compat`
- All nodes and edges enriched with 6 Phase 1 metadata fields:
  `entity_type`, `edge_family`, `module_membership`, `evidence_id`, `version_origin`, `promotion_status`
- 8 module records created from 2.0 quantitative modules
- 5 causal motifs seeded (Layer 2)
- 5 CEDT adapter mappings seeded (Layer 3 bridge)
- JSON schemas for all entity types

## Quick Start

```bash
# Install dependencies
pip install jsonschema

# Validate all data
python3 scripts/validate.py

# Build registry summary
python3 scripts/build_registry_summary.py

# Browse the graph
# Open app/exposograph-3-browser.html in a local server, e.g.:
python3 -m http.server 8080
# Then visit http://localhost:8080/app/exposograph-3-browser.html
```

## Module Registry (Phase 1)

| Module ID | Class | Maturity | Nodes | Description |
|-----------|-------|----------|-------|-------------|
| `EG3.MOD.EXPOSURE.WAVE2.v1` | ExposureSource | D | 56 | Wave 2 carcinogen classes (Aldehydes, Dioxins, Nitrosamines, Chlorinated Solvents) |
| `EG3.MOD.BIOTRANS.FLUX.v1` | BiotransformationProcess | E | 58 | Biotransformation/Flux engine (Km/Vmax kinetics, proxy flux) |
| `EG3.MOD.MECHANISM.INTERACTION.v1` | Mechanism | C | 20 | Multi-carcinogen competitive inhibition at shared CYP/GST enzymes |
| `EG3.MOD.MECHANISM.OXSTRESS.v1` | Mechanism | C | 12 | Oxidative stress / DNA repair pathway perturbation |
| `EG3.MOD.TISSUE.SUBGRAPH.v1` | TissueContext | D | 53 | Tissue-specific expression weights (GTEx v8, 8 tissues, 53 genes) |
| `EG3.MOD.MODIFIER.POPGEN.v1` | Modifier | C | 21 | Susceptibility modifiers / population genomics (genotype_modifiers) |
| `EG3.MOD.OUTCOME.MUTSIG.v1` | Outcome | C | 27 | Mutational signatures (COSMIC SBS v3.4) + DNA adduct outcomes |
| `EG3.MOD.EVIDENCE.PROVENANCE.v1` | EvidenceAssertion | D | 85 | Evidence & provenance records (parameter_provenance, biomarker_mapping) |

## Migration Map

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Freeze EG2.0 graph as registry baseline; enrich with metadata |
| Phase 2 | Planned | Build interface and ontology layer |
| Phase 3 | Planned | Recast EG2.0 modules as formal module records (extended) |
| Phase 4 | Planned | Promote high-confidence relationships into causal motifs |
| Phase 5 | Planned | Attach execution contracts to selected modules |
| Phase 6 | Planned | Build Cancer Ecology Digital Twin adapters |

## Blueprint

See `docs/exposograph_3_blueprint.md` for the full architecture specification.
