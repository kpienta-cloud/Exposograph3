# ExposoGraph 3.0 — Phase 2 Notes: Layer-0 Ontology + Typed Interface Contracts

## Summary

Phase 2 formalises the Layer-0 ontology and interface layer that makes the 8 existing module records machine-checkable against typed contracts.

| Metric | Value |
|---|---|
| Entity classes defined | 11 (6 abstract, 5 leaf concrete) |
| Interfaces defined | 9 (1 root Module + 8 domain interfaces) |
| Port types in vocabulary | 29 |
| Modules conformant | **8/8** |
| Type-compatible wiring connections | **4** |
| Conformance gaps recorded (not fabricated) | 0 |
| Frozen baseline | 212 nodes / 313 edges — byte-stable |
| Causal projection | 169 edges — intact |

---

## 1. Entity Class Hierarchy

Full hierarchy from the root `Entity` down to the 5 concrete registry leaf classes. All parents are explicitly defined; no dangling references; no cycles.

```
Entity (abstract, root)
├── ExposureAgent (abstract) — maps_to_registry_type: Carcinogen
│   └── Carcinogen (leaf) — IARC/CHEBI/CASRN/PubChem
├── BiologicalEntity (abstract) — maps_to_registry_type: Enzyme
│   └── Enzyme (leaf) — HGNC/UniProt/Entrez/Ensembl
├── ChemicalEntity (abstract) — maps_to_registry_type: Metabolite
│   └── Metabolite (leaf) — CHEBI/HMDB/PubChem/CASRN
├── MolecularDamage (abstract) — maps_to_registry_type: DNA_Adduct
│   └── DNA_Adduct (leaf) — CHEBI/NCIt/MeSH
└── BiologicalProcess (abstract) — maps_to_registry_type: Pathway
    └── Pathway (leaf) — KEGG/Reactome/GO/NCIt
```

Each entity class carries: `class_id`, `label`, `description`, `parent` (null for root), `abstract` (bool), `maps_to_registry_type`, `identifier_namespaces`.

---

## 2. The 8 Interface Contracts

All 8 domain interfaces plus the root `Module` interface are defined in `data/ontology/interfaces.json`. Every domain interface extends `Module`. `ExecutableModule` is the mix-in.

### Root: Module
- **extends**: null
- **required_fields**: module_id, module_name, module_class, maturity_class, extends, version
- **maturity_floor**: D

### ExposureSourceModule
- **extends**: Module
- **required_fields**: + scope, evidence_bundle, mechanism_type
- **required input dtypes**: `category:carcinogen_class` (required), `category:exposure_scenario` (required)
- **required output dtypes**: `multiplier:exposure` (required), `concentration:uM` (required)
- **maturity_floor**: C

### BiotransformationModule
- **extends**: Module
- **required_fields**: + input_ports, output_ports, parameters
- **required input dtypes**: `concentration:uM` (required), `multiplier:genotype_activity` (required)
- **required output dtypes**: `score:flux_ratio` (required)
- **maturity_floor**: E

### MechanismModule
- **extends**: Module
- **required_fields**: + mechanism_type, causal_edges, input_ports, output_ports
- **required input dtypes**: `score:ROS_burden` (optional), `fraction:GSH_pool` (optional)
- **required output dtypes**: `score:ROS_burden` (optional)
- **maturity_floor**: C

### TissueContextModule
- **extends**: Module
- **required_fields**: + scope, input_ports, output_ports
- **required input dtypes**: `category:gene_symbol` (required), `category:tissue_name` (required)
- **required output dtypes**: `weight:tissue_expression` (required)
- **maturity_floor**: C

### SusceptibilityModifierModule
- **extends**: Module
- **required_fields**: + scope, input_ports, output_ports
- **required input dtypes**: `category:gene_symbol` (required), `multiplier:genotype_activity` (required)
- **required output dtypes**: `multiplier:genotype_activity` (required)
- **maturity_floor**: C

### OutcomeModule
- **extends**: Module
- **required_fields**: + output_ports, input_ports, evidence_bundle
- **required input dtypes**: `score:flux_ratio` (required), `category:carcinogen_class` (required)
- **required output dtypes**: `signature:SBS` (required)
- **maturity_floor**: C

### EvidenceAndProvenanceModule
- **extends**: Module
- **required_fields**: + evidence_bundle, input_ports, output_ports
- **required input dtypes**: `category:gene_symbol` (required), `category:substrate_id` (required)
- **required output dtypes**: `record:provenance` (required)
- **maturity_floor**: C

### ExecutableModule (mix-in)
- **extends**: Module
- **required_fields**: + input_ports, output_ports, equation_type, update_rule, parameters
- **required port contract**: at least one typed input and one typed output port (dtype not null)
- **allowed_equation_types**: score-based, rule-based, lookup, Bayesian, SCM, ODE, GLV-coupled, agent-based
- **maturity_floor**: E

---

## 3. Port-Type Vocabulary (29 types)

Controlled vocabulary of dtypes enabling type-checked cross-module wiring. Derived from real module ports.

| type_id | base_kind | unit | Description |
|---|---|---|---|
| `concentration:uM` | number | uM | Molar concentration in micromolar |
| `multiplier:genotype_activity` | number | dimensionless | Enzyme Vmax scaling from metabolizer phenotype |
| `multiplier:exposure` | number | dimensionless | Exposure intensity vs unexposed baseline |
| `score:flux_ratio` | number | dimensionless | activation_score / detoxification_score |
| `score:activation` | number | dimensionless | Summed activation flux (Michaelis-Menten) |
| `score:detoxification` | number | dimensionless | Summed detox flux |
| `score:ROS_burden` | number | dimensionless | Aggregate ROS score |
| `score:oxidative_adduct` | number | dimensionless | Predicted oxidative adduct score (8-OHdG) |
| `score:repair_capacity` | number | [0,1] | DNA repair enzyme availability index |
| `fraction:GSH_pool` | number | dimensionless | Remaining GSH fraction (0=depleted, 1=replete) |
| `weight:tissue_expression` | number | dimensionless | Normalised GTEx expression weight [0,1] |
| `category:carcinogen_class` | category | — | PAH, Aflatoxin, HCA, Benzene, etc. |
| `category:exposure_scenario` | category | — | unexposed, general_population, smoker, etc. |
| `category:gene_symbol` | category | — | HGNC gene symbol |
| `category:tissue_name` | category | — | Liver, Lung, Prostate, etc. |
| `category:substrate_id` | category | — | Registry node substrate identifier |
| `category:inducer_context` | category | — | smoking, chronic_alcohol, TCDD_dioxin, none |
| `flag:boolean` | boolean | — | True/False binary flag |
| `signature:SBS` | category | — | COSMIC SBS signature ID (e.g. SBS4) |
| `category:dominant_mutation` | category | — | Predicted dominant mutation type |
| `category:confidence_level` | category | — | high, medium, exploratory |
| `map:flux_ratios` | record | dimensionless | dict enzyme→flux ratio |
| `map:substrate_concentrations` | record | uM | dict substrate→concentration |
| `map:enzyme_genotypes` | record | — | dict enzyme→phenotype |
| `map:metal_exposure` | record | uM | dict metal→concentration |
| `map:genotype_context` | record | — | dict gene→modifier for exposure module |
| `list:adduct_types` | record | — | List of DNA adduct type IDs |
| `concentration:daily_intake` | number | ug/kg/day | Daily intake estimate |
| `record:provenance` | record | — | Structured kinetic + evidence provenance object |

---

## 4. Per-Module Conformance (8/8)

All 8 modules are **CONFORMANT** — no gaps recorded, no conformance notes fabricated.

| Module | module_class | extends | maturity | Conformant |
|---|---|---|---|---|
| EG3.MOD.BIOTRANS.FLUX.v1 | BiotransformationProcess | BiotransformationModule, ExecutableModule | E | ✓ |
| EG3.MOD.EXPOSURE.WAVE2.v1 | ExposureSource | ExposureSourceModule | C | ✓ |
| EG3.MOD.MECHANISM.INTERACTION.v1 | Mechanism | MechanismModule | C | ✓ |
| EG3.MOD.MECHANISM.OXSTRESS.v1 | Mechanism | MechanismModule | C | ✓ |
| EG3.MOD.MODIFIER.POPGEN.v1 | Modifier | SusceptibilityModifierModule | C | ✓ |
| EG3.MOD.OUTCOME.MUTSIG.v1 | Outcome | OutcomeModule | C | ✓ |
| EG3.MOD.TISSUE.SUBGRAPH.v1 | TissueContext | TissueContextModule | C | ✓ |
| EG3.MOD.EVIDENCE.PROVENANCE.v1 | EvidenceAssertion | EvidenceAndProvenanceModule | C | ✓ |

**ExecutableModule**: EG3.MOD.BIOTRANS.FLUX.v1 is the sole module extending both `BiotransformationModule` and `ExecutableModule`. It satisfies all ExecutableModule required_fields (input_ports, output_ports, equation_type, update_rule, parameters) and has maturity_class E.

Every module port was annotated with a `dtype` referencing a `port_types.json` type_id. Units added where applicable. No existing port name or description was removed.

---

## 5. Wiring Map Summary (4 type-compatible cross-module connections)

The wiring map (`data/ontology/wiring.json`) lists all cross-module output→input connections where dtypes match exactly. 4 connections found:

| from_module | from_port | to_module | to_port | dtype |
|---|---|---|---|---|
| BIOTRANS.FLUX | flux_ratio | OUTCOME.MUTSIG | flux_ratio | `score:flux_ratio` |
| EXPOSURE.WAVE2 | tissue_conc_uM | BIOTRANS.FLUX | substrate_conc_uM | `concentration:uM` |
| MECHANISM.INTERACTION | GSH_pool_fraction | MECHANISM.OXSTRESS | GSH_pool_fraction | `fraction:GSH_pool` |
| MODIFIER.POPGEN | activity_multiplier | BIOTRANS.FLUX | enzyme_genotype | `multiplier:genotype_activity` |

These 4 connections represent the core execution pipeline:
- Exposure → Biotransformation (dose propagation)
- Biotransformation → MutSig (flux drives mutational signature)
- Interaction (GSH depletion) → OxStress (oxidative mechanism)
- PopGen modifier → Biotransformation (genotype scales Vmax)

---

## 6. New Files

| File | Description |
|---|---|
| `data/ontology/classes.json` | Full entity class hierarchy (11 classes) |
| `data/ontology/interfaces.json` | 9 interface contracts (8 domain + Module root) |
| `data/ontology/port_types.json` | 29 port-type vocabulary entries |
| `data/ontology/wiring.json` | 4 type-compatible wiring connections |
| `schema/interface.schema.json` | JSON Schema for interface records |
| `schema/port_type.schema.json` | JSON Schema for port-type records |
| `schema/ontology_class.schema.json` | Tightened schema for entity classes |
| `app/data/ontology/` | Mirror of all 4 ontology files for browser |
| `docs/PHASE2_NOTES.md` | This file |

---

## 7. Validator Status

`scripts/validate.py` exits 0 with 12 passes:
1. Directory structure
2. Schema loading (9 schemas including Phase 2 interface.schema.json, port_type.schema.json)
3. Registry graph: 212 nodes / 313 edges byte-stable
4. Split files: nodes.json / edges.json
5. Execution edges (74)
6. Module records (8/8)
7. Ontology files exist
8. Causal motifs (7 active)
9. Causal edges (169 promoted)
10. CEDT adapters (5)
11. App mirror files
12. **ONTOLOGY CONFORMANCE PASS** — entity hierarchy (no dangling/cycles), all 8 interfaces defined, port-type vocabulary (29), all 8 modules conformant, wiring integrity (4 connections, all endpoints/dtypes valid)
