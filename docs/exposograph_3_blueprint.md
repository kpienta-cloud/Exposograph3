# ExposoGraph 3.0 Blueprint

## Overview

ExposoGraph 3.0 is best framed as an ontology-backed, causal, module-oriented evolution of the current ExposoGraph platform rather than as a larger standalone knowledge graph.[cite:1][cite:26][cite:2] The central architectural shift is to preserve the knowledge graph as the registry and provenance layer, while promoting explicit causal structure and executable module definitions into first-class components.[cite:1][cite:26][cite:2]

This design matches three needs that have become clearer as the platform expanded: preservation of the current carcinogen pathway visualization assets, formalization of mechanistic directionality, and creation of a clean bridge into Cancer Ecology Digital Twin workflows.[cite:1][cite:25][cite:2] It also aligns with published approaches showing that ontologies provide extendable schema definitions, while causal knowledge graphs distinguish broad relational content from explicitly causal subsets used for inference.[cite:1][cite:2]

## Design goals

The blueprint is built around five design goals:

- Preserve ExposoGraph 2.0 assets, including existing graph structure, visualization logic, and manuscript-compatible concepts, as a stable registry layer.[cite:1][cite:26]
- Replace semantically vague edge use with typed causal relations for modules intended to support mechanism, intervention logic, or prediction.[cite:2]
- Make modules first-class objects with declared scope, inputs, outputs, internal state, and evidence bundles, following modular digital twin design principles.[cite:2][cite:36]
- Support tissue context, susceptibility modifiers, and carcinogen-class expansion without forcing all biological logic into a single generic node-edge representation.[cite:25][cite:26]
- Create explicit adapter points into the Cancer Ecology Digital Twin, especially for the host, exposure, tissue, metabolic, and state-quality layers.[cite:2][cite:28]

## Architectural stack

ExposoGraph 3.0 should use a four-layer architecture.

### Layer 0: Ontology and interface layer

This layer defines the semantic contracts for the system: what counts as an exposure, carcinogen, metabolite, mechanism, tissue context, susceptibility modifier, phenotype, outcome, evidence assertion, or executable module.[cite:1] It should be implemented as a set of extendable base interfaces so that ExposoGraph-specific module types can inherit from shared parent classes rather than hard-coding every concept into the graph structure.[cite:1]

### Layer 1: Registry graph layer

This layer is the continuity layer from ExposoGraph 2.0.[cite:1][cite:26] It contains the current entities, relationships, identifiers, provenance records, module memberships, and graph views, preserving the existing browser and manuscript ecosystem while adding richer metadata fields for promotion into causal and executable forms.[cite:1][cite:26]

### Layer 2: Causal graph layer

This layer contains only promoted mechanistic or directional relations, not all graph edges.[cite:2] It should encode exposure-to-metabolite, metabolite-to-target, pathway-to-phenotype, modifier-to-susceptibility, and tissue-context-to-outcome motifs using explicit relation types such as increases, decreases, activates, detoxifies, damages, mediates, modifies, and precedes.[cite:2]

### Layer 3: Execution layer

This layer contains modules that can compute scores, update internal states, apply rules, or eventually serve as digital twin components.[cite:36] Modules in this layer should expose formal input and output ports and, when appropriate, parameter sets, state variables, and update rules.[cite:36]

## Module taxonomy

ExposoGraph 3.0 should define seven top-level module classes.

### 1. Exposure Source Module

Represents exogenous agents, mixtures, and exposure families such as tobacco smoke, alcohol and acetaldehyde, arsenic, benzene, chlorinated solvents, heavy metals, dioxins or PCBs, and dietary nitrosamines from the current expansion work.[cite:25][cite:26]

### 2. Biotransformation Module

Represents uptake, transport, metabolic activation, detoxification, conjugation, and elimination logic linking parent compounds to proximate or ultimate biological effectors.[cite:26] This is the natural home for CYP, GST, repair, redox, and metabolite-branching mechanisms.[cite:26]

### 3. Mechanism Module

Represents pathway perturbation and carcinogenic process logic, including oxidative stress, DNA damage, receptor signaling, immune modulation, epigenetic disruption, proliferation pressure, and other key-characteristic-linked mechanisms.[cite:1][cite:26]

### 4. Tissue Context Module

Represents tissue-specific context, including expression weighting, cell-type filters, tissue vulnerability, and local ecological or microenvironmental modifiers.[cite:25][cite:26] This module class formalizes the tissue-specific graph views already developed in ExposoGraph 2.0.[cite:25][cite:26]

### 5. Susceptibility Modifier Module

Represents host-side modifiers such as germline variation, somatic modifiers, CHIP, age, sex, ancestry-linked frequency context, comorbidity state, and prior exposure history.[cite:25][cite:28] This class provides the cleanest bridge from ExposoGraph into host and risk-stratification logic.[cite:2][cite:28]

### 6. Outcome Module

Represents intermediate and endpoint states such as adduct burden, pathway activation states, precancer phenotypes, tissue injury states, and tumor-type-specific outcomes.[cite:1][cite:26]

### 7. Evidence and Provenance Module

Represents the support structure for every mechanistic claim, including publications, assay context, species, cohort source, evidence direction, contradiction notes, confidence, and version history.[cite:1][cite:2] This module class is essential because promotion from descriptive graph content to causal or executable content should always be evidence-governed.[cite:1][cite:2]

## Maturity classes

Each module should also be labeled by computational maturity rather than biological topic alone.

| Maturity class | Meaning |
|---|---|
| D | Descriptive only; browsable graph and evidence content without formal causal interpretation.[cite:1] |
| C | Causal; edges and motifs have explicit directional or mediator semantics suitable for mechanistic interpretation.[cite:2] |
| E | Executable; module has typed inputs and outputs plus a scoring rule, transition rule, or update function.[cite:36] |
| T | Twin-ready; module outputs map directly into Cancer Ecology Digital Twin state or observation variables.[cite:2][cite:28] |

This maturity labeling makes it possible to keep partially mature modules in the platform without overstating mechanistic certainty.[cite:1][cite:2]

## Core schema fields

Each ExposoGraph 3.0 module should be stored as a typed object with the following minimum schema.

| Field | Type | Purpose |
|---|---|---|
| `module_id` | string | Stable versioned identifier for the module instance.[cite:1] |
| `module_name` | string | Human-readable module title. |
| `module_class` | enum | One of the seven biological or infrastructural module classes.[cite:26] |
| `maturity_class` | enum | One of D, C, E, or T.[cite:36] |
| `extends` | list | Parent ontology or interface classes inherited by the module.[cite:1] |
| `scope` | object | Species, tissue, cell type, exposure route, dose regime, life stage, sex, ancestry, and time horizon.[cite:25][cite:28] |
| `input_ports` | list | Required typed inputs for module execution or scoring.[cite:36] |
| `output_ports` | list | Typed outputs emitted by the module.[cite:36] |
| `internal_state` | list | Optional latent state variables for dynamic modules.[cite:36] |
| `causal_role_map` | object | Tags for treatment, mediator, moderator, confounder, collider, or outcome roles where relevant.[cite:2] |
| `graph_nodes` | list | Registry graph nodes associated with the module.[cite:26] |
| `graph_edges` | list | Registry graph edges owned or used by the module.[cite:26] |
| `causal_edges` | list | Promoted subset of explicitly directional or mechanistic relations.[cite:2] |
| `mechanism_type` | enum | Activation, inhibition, detoxification, adduct formation, oxidative stress, immune suppression, and similar categories.[cite:26] |
| `equation_type` | enum | Lookup, rule-based, score-based, Bayesian, SCM, ODE, GLV-coupled, or agent-based form.[cite:8][cite:36] |
| `update_rule` | text or object | Formal transition, score, or update description for executable modules.[cite:8] |
| `parameters` | list | Parameter names, values, bounds, units, and provenance records.[cite:8] |
| `evidence_bundle` | list | PMID or DOI support, assay type, species, effect direction, support strength, and contradiction flags.[cite:1][cite:2] |
| `uncertainty` | object | Confidence, evidence heterogeneity, missingness, and context sensitivity metadata.[cite:28] |
| `validation_status` | enum | Literature-only, curated, benchmarked, cohort-supported, or experimentally validated. |
| `cedt_mapping` | object | Maps outputs into host, exposure, tissue, metabolic, or state-quality twin variables.[cite:2][cite:28] |
| `version` | string | Version tag for governance and reproducibility.[cite:1] |

## Edge semantics

ExposoGraph 3.0 should split edges into three semantic families rather than relying on a single mixed relation pool.

### Registry edges

Registry edges support organization, indexing, and provenance rather than mechanistic inference.[cite:1] Examples include `has_component`, `measured_in`, `expressed_in`, `supported_by`, `belongs_to_module`, `maps_to_identifier`, and `contradicted_by`.[cite:1]

### Causal edges

Causal edges encode directional biology and should be used only when mechanistic or inferential semantics are intended.[cite:2] Examples include `increases`, `decreases`, `activates`, `inhibits`, `bioactivates`, `detoxifies`, `damages`, `mediates`, `modifies`, and `precedes`.[cite:2]

### Execution edges

Execution edges connect modules and data flow rather than biological meaning alone.[cite:36] Examples include `feeds_input`, `emits_output`, `updates_state`, `consumes_parameter`, `writes_observation`, and `maps_to_twin_state`.[cite:36]

A practical governance rule follows from this separation: broad association edges may remain in the registry layer, but no module labeled causal, executable, or twin-ready should depend on undefined association semantics as its operative logic.[cite:2]

## Causal motif library

Promotion into the causal layer should use a small motif library rather than ad hoc edge interpretation.

Recommended first motifs:

- Exposure  metabolite  target damage.[cite:2][cite:26]
- Exposure  pathway perturbation  tissue phenotype.[cite:2][cite:26]
- Modifier  altered detoxification  exposure burden.[cite:2][cite:28]
- Tissue context  susceptibility  outcome.[cite:2][cite:25]
- Exposure mixture  convergent mechanism  shared outcome.[cite:25][cite:26]

These motifs provide a disciplined way to promote current graph content into modules that are interpretable and eventually executable.[cite:2][cite:8]

## Migration map

The migration should be staged and additive.

### Phase 1: Freeze the current graph as the registry baseline

The ExposoGraph 2.0 node and edge inventory, tissue views, and existing scoring and visualization assets should be preserved intact as `Registry Graph v2-compat`.[cite:1][cite:26] At this stage, only metadata enrichment should be added: `entity_type`, `edge_family`, `module_membership`, `evidence_id`, `version_origin`, and `promotion_status`.[cite:1]

### Phase 2: Build the interface and ontology layer

Define the base classes and interface contracts for Exposure, BiotransformationProcess, Mechanism, TissueContext, Modifier, Outcome, EvidenceAssertion, and ExecutableModule.[cite:1] Then create ExposoGraph-specific child classes by extension rather than rewriting the base schema for every use case.[cite:1]

### Phase 3: Recast existing ExposoGraph 2.0 modules as module records

The seven existing ExposoGraph 2.0 feature modules should become explicit module objects.[cite:26] Wave 2 carcinogen expansion becomes a family of Exposure Source Modules; tissue-specific views become Tissue Context Modules; existing individual-scoring pipelines become Executable Risk Aggregation Modules; and evidence-centric support tables become Evidence and Provenance Modules.[cite:25][cite:26]

### Phase 4: Promote high-confidence relationships into causal motifs

High-confidence mechanistic relations should be promoted from the registry graph into the causal layer using the motif library above.[cite:2] Only relationships with clear directional semantics and evidence support should move into the causal layer, while looser associations remain visible but non-operative in the registry graph.[cite:1][cite:2]

### Phase 5: Attach execution contracts to selected modules

Selected high-value modules should gain input and output ports, state definitions, parameter records, and update rules.[cite:8][cite:36] The first executable modules do not need to be full mechanistic simulators; score-based or Bayesian forms are acceptable as long as their assumptions and parameter provenance are explicit.[cite:8]

### Phase 6: Build Cancer Ecology Digital Twin adapters

The final migration stage is to map module outputs into the twin architecture.[cite:2][cite:28] Exposure intensity and duration map naturally into exposure state variables, tissue-specific sensitivity into tissue variables, metabolic activation and detoxification into metabolic variables, host modifiers into host variables, and evidence confidence into state-quality variables.[cite:2][cite:28]

## Mapping from current ExposoGraph content

The current ExposoGraph content can be transformed into 3.0 objects as follows.

| Current ExposoGraph asset | ExposoGraph 3.0 destination |
|---|---|
| Core node-edge carcinogen pathway graph | Registry Graph layer with typed promotion metadata.[cite:1][cite:26] |
| Wave 2 carcinogen expansion | Exposure Source Module family with class-specific child modules.[cite:25][cite:26] |
| Tissue-specific GTEx-based graph views | Tissue Context Modules with expression and context filters.[cite:25][cite:26] |
| VCF or individual-scoring pipeline | Executable aggregation or susceptibility modules with defined input ports.[cite:26] |
| Literature support tables and manuscript references | Evidence and Provenance Modules plus assertion records.[cite:1] |
| Mechanistic pathway links | Causal layer motifs when directional evidence is sufficient.[cite:2][cite:26] |
| Future digital twin hooks | `cedt_mapping` adapters to host, exposure, tissue, metabolic, and quality layers.[cite:2][cite:28] |

## Example module

A representative 3.0 module helps make the design concrete.

### Example: Alcohol or acetaldehyde liver biotransformation module

A module such as `EG3.MOD.BIOTRANS.CYP2E1.ACETALDEHYDE.LIVER.v1` would be classified as a Biotransformation Module and likely marked executable or twin-ready once validated.[cite:25][cite:26] Its scope would specify human liver tissue, alcohol exposure context, relevant time scale, and metabolic assumptions.[cite:25]

The input ports would include ethanol exposure level, CYP2E1 or ADH or ALDH activity context, and tissue expression weighting; outputs would include acetaldehyde burden, oxidative stress burden, and adduct-related effect scores.[cite:25][cite:26] The causal motif would encode ethanol increasing acetaldehyde burden, acetaldehyde increasing macromolecular damage burden, and tissue context modifying the downstream effect profile.[cite:2][cite:25]

A `cedt_mapping` field would point those outputs into exposure, metabolic, and tissue state variables in the Cancer Ecology Digital Twin.[cite:2][cite:28] This is the kind of object that makes ExposoGraph more than a browsing tool: it becomes both a knowledge asset and a computational interface.[cite:2][cite:36]

## Governance and implementation priorities

The highest-value implementation order is:

1. Define the ontology and interface vocabulary.[cite:1]
2. Finalize the ExposoGraph 3.0 module schema.[cite:1][cite:36]
3. Convert the existing ExposoGraph 2.0 modules into explicit module records.[cite:26]
4. Promote a first library of high-confidence causal motifs.[cite:2]
5. Implement a small set of exemplar executable modules, such as alcohol or acetaldehyde, benzene, arsenic, and one tissue-filtering module.[cite:25][cite:26]
6. Add Cancer Ecology Digital Twin adapters after the module registry is stable.[cite:2][cite:28]

This order reduces technical risk because it does not require immediate full simulation capability, yet it creates a disciplined path from graph curation to mechanistic interpretation and then to executable modeling.[cite:8][cite:36]

## Strategic value

ExposoGraph 3.0 would no longer present primarily as another biomedical knowledge graph.[cite:1][cite:2] Instead, it would be a mechanistically governed, ontology-backed, causal module registry designed to support carcinogen pathway interpretation, exposure-context integration, and downstream digital twin interoperability.[cite:2][cite:28]

That shift is scientifically important because it clarifies what the platform is for: not merely organizing carcinogen information, but structuring exposure-to-mechanism-to-outcome knowledge in a way that can be curated, audited, compared across tissues and modifiers, and progressively converted into executable components.[cite:1][cite:2][cite:36]
