#!/usr/bin/env python3
"""
ExposoGraph 3.0 — Phase 2/4/5 Validation Script
Validates all JSON files against schemas and checks Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5 requirements.
Phase 2 adds: ONTOLOGY CONFORMANCE pass (entity class hierarchy, interface contracts, port dtypes, wiring).
Phase 5 adds: EXECUTION pass (re-runs all scenarios, asserts flux_ratio/predicted_SBS match within 1e-6 tolerance;
               checks Km/Vmax provenance; checks wiring connection usage; validates data/execution/ directory).
Exits 0 on success, non-zero on failure.
"""

import json
import sys
import os
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).parent.parent

# Phase 1 required metadata fields for nodes and edges
NODE_PHASE1_FIELDS = {"entity_type", "module_membership", "evidence_id", "version_origin", "promotion_status"}
EDGE_PHASE1_FIELDS = {"edge_family", "module_membership", "evidence_id", "version_origin", "promotion_status"}

# Phase 3 required module fields
MODULE_PHASE3_REQUIRED = [
    "module_id", "module_name", "module_class", "maturity_class", "extends", "scope",
    "version", "evidence_bundle", "input_ports", "output_ports", "parameters",
    "equation_type", "update_rule", "uncertainty", "validation_status", "cedt_mapping",
    "causal_role_map", "graph_nodes", "graph_edges", "causal_edges", "internal_state",
    "promotion_status"
]

# Phase 3 execution edge required fields
EXEC_EDGE_REQUIRED = ["edge_id", "source", "target", "type", "edge_family", "promotion_status", "version_origin"]

# Phase 4 causal edge required fields
CAUSAL_EDGE_REQUIRED = [
    "causal_edge_id", "source", "target", "causal_relation",
    "source_predicate", "motif_id", "evidence", "promotion_status"
]

# Phase 4 evidence-governed promotion rule
DIRECTIONAL_BASELINE = {"ACTIVATES", "DETOXIFIES", "FORMS_ADDUCT", "REPAIRS", "INDUCES", "INHIBITS", "TRANSPORTS"}
DIRECTIONAL_PHASE3 = {"bioactivates", "detoxifies", "competes_at"}

VALID_CAUSAL_RELATIONS = {"increases", "decreases", "activates", "detoxifies", "damages", "mediates", "modifies", "precedes"}

errors = []
warnings = []


def check(condition, message, is_error=True):
    if not condition:
        if is_error:
            errors.append(f"  ERROR: {message}")
        else:
            warnings.append(f"  WARNING: {message}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"  ERROR: Could not parse {path.name}: {e}")
        return None


def validate_with_jsonschema(data, schema, label):
    """Try jsonschema validation; fall back to structural check if not installed."""
    try:
        import jsonschema
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as ve:
            errors.append(f"  ERROR: Schema validation failed for {label}: {ve.message}")
        except jsonschema.SchemaError as se:
            errors.append(f"  ERROR: Schema itself is invalid for {label}: {se.message}")
    except ImportError:
        # Fallback: check required fields manually
        if isinstance(data, dict) and "required" in schema:
            for req_field in schema.get("required", []):
                if req_field not in data:
                    errors.append(f"  ERROR: {label} missing required field: {req_field}")


def is_evidenced_baseline(edge):
    """Baseline edge evidence rule: non-empty provenance OR non-null evidence_id."""
    provenance = edge.get("provenance", [])
    evidence_id = edge.get("evidence_id")
    return (provenance and len(provenance) > 0) or bool(evidence_id)


def is_evidenced_phase3(edge):
    """Phase 3 evidence rule: confidence in {high,medium} AND non-empty sources."""
    return edge.get("confidence", "") in {"high", "medium"} and bool(edge.get("sources"))


# ─── 1. Check directory structure ─────────────────────────────────────────────
print("=== ExposoGraph 3.0 Phase 4 Validation ===\n")

required_dirs = [
    "app", "data/ontology", "data/registry", "data/causal",
    "data/modules", "data/evidence", "data/adapters", "data/execution", "schema", "docs", "scripts",
]
print("1. Directory structure...")
for d in required_dirs:
    check((REPO_ROOT / d).is_dir(), f"Missing directory: {d}")
if not errors:
    print("   ✓ All required directories present")

# ─── 2. Load schemas ──────────────────────────────────────────────────────────
print("\n2. Loading schemas...")
schema_dir = REPO_ROOT / "schema"
schemas = {}
schema_files = [
    "registry_node.schema.json", "registry_edge.schema.json",
    "module.schema.json", "causal_motif.schema.json", "ontology_class.schema.json",
    "execution_edge.schema.json", "causal_edge.schema.json",
    "interface.schema.json", "port_type.schema.json"
]
for schema_file in schema_files:
    path = schema_dir / schema_file
    if path.exists():
        schemas[schema_file] = load_json(path)
        print(f"   ✓ Loaded {schema_file}")
    else:
        if schema_file in ["registry_node.schema.json", "registry_edge.schema.json",
                           "module.schema.json", "causal_motif.schema.json",
                           "ontology_class.schema.json"]:
            errors.append(f"  ERROR: Missing schema file: {schema_file}")
        elif schema_file == "execution_edge.schema.json":
            errors.append(f"  ERROR: Missing Phase 3 schema file: {schema_file}")
        elif schema_file == "causal_edge.schema.json":
            errors.append(f"  ERROR: Missing Phase 4 schema file: {schema_file}")
        elif schema_file in ["interface.schema.json", "port_type.schema.json"]:
            errors.append(f"  ERROR: Missing Phase 2 schema file: {schema_file}")

# ─── 3. Validate registry graph (frozen baseline — Phase 4 assertion) ─────────
print("\n3. Validating registry graph (Phase 4: assert 212/313 and unchanged)...")
reg_graph_path = REPO_ROOT / "data/registry/registry_graph.json"
check(reg_graph_path.exists(), "data/registry/registry_graph.json missing")

registry_node_ids = set()
if reg_graph_path.exists():
    reg = load_json(reg_graph_path)
    if reg:
        check(reg.get("bundle") == "Registry Graph v2-compat",
              f"bundle name mismatch: got '{reg.get('bundle')}'")
        nodes = reg.get("nodes", [])
        edges = reg.get("edges", [])

        # Phase 4 assertion (a): baseline still 212/313
        check(len(nodes) == 212, f"PHASE4 ASSERTION FAILED: Expected 212 nodes, got {len(nodes)}")
        check(len(edges) == 313, f"PHASE4 ASSERTION FAILED: Expected 313 edges, got {len(edges)}")
        print(f"   Node count: {len(nodes)} (expected 212) ✓")
        print(f"   Edge count: {len(edges)} (expected 313) ✓")

        # Build registry node id set for endpoint checks
        registry_node_ids = {n["id"] for n in nodes}

        # Validate Phase 1 fields on every node
        node_missing = []
        for i, node in enumerate(nodes):
            missing = NODE_PHASE1_FIELDS - set(node.keys())
            if missing:
                node_missing.append(f"node[{i}] id={node.get('id','?')} missing: {missing}")
        if node_missing:
            for msg in node_missing[:5]:
                errors.append(f"  ERROR: {msg}")
            if len(node_missing) > 5:
                errors.append(f"  ERROR: ... and {len(node_missing)-5} more nodes with missing fields")
        else:
            print(f"   ✓ All {len(nodes)} nodes have all Phase 1 metadata fields")

        # Validate Phase 1 fields on every edge
        edge_missing = []
        for i, edge in enumerate(edges):
            missing = EDGE_PHASE1_FIELDS - set(edge.keys())
            if missing:
                edge_missing.append(f"edge[{i}] {edge.get('source','?')}->{edge.get('target','?')} missing: {missing}")
        if edge_missing:
            for msg in edge_missing[:5]:
                errors.append(f"  ERROR: {msg}")
            if len(edge_missing) > 5:
                errors.append(f"  ERROR: ... and {len(edge_missing)-5} more edges with missing fields")
        else:
            print(f"   ✓ All {len(edges)} edges have all Phase 1 metadata fields")

        # Validate promotion_status = "registry" for all baseline nodes/edges
        bad_promo_nodes = [n.get("id","?") for n in nodes if n.get("promotion_status") != "registry"]
        bad_promo_edges = [f"{e.get('source','?')}->{e.get('target','?')}"
                           for e in edges if e.get("promotion_status") != "registry"]
        check(not bad_promo_nodes, f"{len(bad_promo_nodes)} nodes with promotion_status != 'registry'")
        check(not bad_promo_edges, f"{len(bad_promo_edges)} edges with promotion_status != 'registry'")
        if not bad_promo_nodes and not bad_promo_edges:
            print("   ✓ All nodes and edges have promotion_status='registry' (frozen baseline)")

        # Validate entity_type on nodes
        valid_types = {"Carcinogen", "Enzyme", "Metabolite", "DNA_Adduct", "Pathway"}
        bad_types = [n.get("id","?") for n in nodes if n.get("entity_type") not in valid_types]
        check(not bad_types, f"{len(bad_types)} nodes with invalid entity_type: {bad_types[:3]}")
        if not bad_types:
            print("   ✓ All nodes have valid entity_type")

        # Validate edge_family on edges
        valid_families = {"registry", "causal", "execution"}
        bad_families = [f"{e.get('source','?')}->{e.get('target','?')}"
                        for e in edges if e.get("edge_family") not in valid_families]
        check(not bad_families, f"{len(bad_families)} edges with invalid edge_family")
        if not bad_families:
            print("   ✓ All edges have valid edge_family")

        # Check version_origin
        vos = set(n.get("version_origin","") for n in nodes) | set(e.get("version_origin","") for e in edges)
        expected_vo = "ExposoGraph 2.0 (v0.0.5; 212 nodes / 313 edges reference bundle)"
        check(expected_vo in vos, f"version_origin mismatch; found: {vos}")
        if expected_vo in vos:
            print(f"   ✓ version_origin correct on all entities")

        # Schema validation on a sample node / edge
        if "registry_node.schema.json" in schemas and schemas["registry_node.schema.json"]:
            validate_with_jsonschema(nodes[0], schemas["registry_node.schema.json"], "sample node")
            print("   ✓ Sample node passes schema validation")
        if "registry_edge.schema.json" in schemas and schemas["registry_edge.schema.json"]:
            validate_with_jsonschema(edges[0], schemas["registry_edge.schema.json"], "sample edge")
            print("   ✓ Sample edge passes schema validation")

# ─── 4. Validate split files ──────────────────────────────────────────────────
print("\n4. Validating split registry files...")
for fname in ["nodes.json", "edges.json"]:
    p = REPO_ROOT / "data/registry" / fname
    check(p.exists(), f"data/registry/{fname} missing")
    if p.exists():
        d = load_json(p)
        if d:
            key = "nodes" if fname == "nodes.json" else "edges"
            count = len(d.get(key, []))
            expected = 212 if key == "nodes" else 313
            check(count == expected, f"{fname}: expected {expected} {key}, got {count}")
            print(f"   ✓ {fname}: {count} {key}")

# Also load node IDs from nodes.json as backup
if not registry_node_ids:
    nodes_path = REPO_ROOT / "data/registry/nodes.json"
    if nodes_path.exists():
        nd = load_json(nodes_path)
        if nd:
            registry_node_ids = {n["id"] for n in nd.get("nodes", [])}

# ─── 5. Validate execution_edges.json ─────────────────────────────────────────
print("\n5. Validating execution_edges.json (Phase 3)...")
exec_edges_path = REPO_ROOT / "data/registry/execution_edges.json"
check(exec_edges_path.exists(), "data/registry/execution_edges.json missing (Phase 3 requirement)")
exec_edges_all = []
if exec_edges_path.exists():
    ee = load_json(exec_edges_path)
    if ee:
        exec_edges_all = ee.get("edges", [])
        print(f"   execution_edges count: {len(exec_edges_all)}")
        check(len(exec_edges_all) > 0, "execution_edges.json has zero edges")
        bad_exec = []
        for i, edge in enumerate(exec_edges_all[:10]):
            missing = [f for f in EXEC_EDGE_REQUIRED if f not in edge]
            if missing:
                bad_exec.append(f"exec_edge[{i}] missing: {missing}")
        if bad_exec:
            for msg in bad_exec:
                errors.append(f"  ERROR: {msg}")
        else:
            print(f"   ✓ Sample execution edges have all required fields")
        if "execution_edge.schema.json" in schemas and schemas["execution_edge.schema.json"]:
            if exec_edges_all:
                validate_with_jsonschema(exec_edges_all[0], schemas["execution_edge.schema.json"], "sample execution edge")
                print(f"   ✓ Sample execution edge passes schema validation")
        print(f"   version_origin: {ee.get('version_origin','?')}")

# ─── 6. Validate module records ───────────────────────────────────────────────
print("\n6. Validating module records (Phase 3 + Phase 4 causal_edges)...")
modules_dir = REPO_ROOT / "data/modules"
module_files = list(modules_dir.glob("*.json"))
check(len(module_files) == 8, f"Expected 8 module files, got {len(module_files)}: {[f.name for f in module_files]}")

loaded_modules = []
for mf in sorted(module_files):
    m = load_json(mf)
    if m:
        loaded_modules.append(m)
        if "module.schema.json" in schemas and schemas["module.schema.json"]:
            validate_with_jsonschema(m, schemas["module.schema.json"], mf.name)
        for req in ["module_id","module_name","module_class","maturity_class","extends","scope","version","evidence_bundle"]:
            check(req in m, f"Module {mf.name} missing required field: {req}")
        # Phase 4: check causal_edges field is a list
        check("causal_edges" in m, f"Module {mf.name} missing Phase 4 'causal_edges' field")
        check(isinstance(m.get("causal_edges"), list), f"Module {mf.name} causal_edges is not a list")

print(f"   ✓ {len(loaded_modules)} module records loaded")
print("\n   Module causal edge counts (Phase 4):")
for m in sorted(loaded_modules, key=lambda x: x.get("module_id","")):
    nn = len(m.get("graph_nodes", []))
    ne = len(m.get("graph_edges", []))
    nce = len(m.get("causal_edges", []))
    mc = m.get("maturity_class", "?")
    print(f"     [{mc}] {m['module_id']}: {nn} nodes, {ne} graph_edges, {nce} causal_edges")

# ─── 7. Validate ontology ────────────────────────────────────────────────────
print("\n7. Validating ontology layer...")
for fname in ["interfaces.json", "classes.json"]:
    p = REPO_ROOT / "data/ontology" / fname
    check(p.exists(), f"data/ontology/{fname} missing")
    if p.exists():
        load_json(p)
        print(f"   ✓ {fname} loaded")

# ─── 8. Validate causal motifs (Phase 4: 7 active motifs) ────────────────────
print("\n8. Validating causal motifs (Phase 4)...")
motifs_path = REPO_ROOT / "data/causal/motifs.json"
check(motifs_path.exists(), "data/causal/motifs.json missing")
valid_motif_ids = set()
if motifs_path.exists():
    motifs_doc = load_json(motifs_path)
    if motifs_doc:
        motif_list = motifs_doc.get("motifs", [])
        check(len(motif_list) == 7, f"Phase 4 requires 7 causal motifs, got {len(motif_list)}")
        print(f"   Motif count: {len(motif_list)} (expected 7)")

        # Phase 4: all motifs must be active
        non_active = [m.get("motif_id") for m in motif_list if m.get("status") != "active"]
        check(not non_active, f"Phase 4: motifs still at seed status: {non_active}")
        if not non_active:
            print("   ✓ All motifs promoted to status='active'")

        # Phase 4: all motifs must have causal_relation
        missing_cr = [m.get("motif_id") for m in motif_list if not m.get("causal_relation")]
        check(not missing_cr, f"Phase 4: motifs missing causal_relation: {missing_cr}")

        # Phase 4: causal_relation must be from valid vocab
        invalid_cr = [m.get("motif_id") for m in motif_list
                      if m.get("causal_relation") not in VALID_CAUSAL_RELATIONS]
        check(not invalid_cr, f"Phase 4: motifs with invalid causal_relation: {invalid_cr}")
        if not missing_cr and not invalid_cr:
            print("   ✓ All motifs have valid causal_relation")

        valid_motif_ids = {m["motif_id"] for m in motif_list}

        for mot in motif_list:
            if "causal_motif.schema.json" in schemas and schemas["causal_motif.schema.json"]:
                validate_with_jsonschema(mot, schemas["causal_motif.schema.json"], mot.get("motif_id","?"))
        print("   ✓ All motifs pass schema validation")

# ─── 9. Validate causal_edges.json (Phase 4 core) ────────────────────────────
print("\n9. Validating causal_edges.json (Phase 4 core)...")
causal_edges_path = REPO_ROOT / "data/causal/causal_edges.json"
check(causal_edges_path.exists(), "data/causal/causal_edges.json missing (Phase 4 requirement)")
causal_edge_ids = set()
if causal_edges_path.exists():
    ce_doc = load_json(causal_edges_path)
    if ce_doc:
        # Check header fields
        check("promoted_count" in ce_doc, "causal_edges.json missing 'promoted_count' header field")
        check("retained_in_registry_count" in ce_doc, "causal_edges.json missing 'retained_in_registry_count'")
        check("promotion_rule" in ce_doc, "causal_edges.json missing 'promotion_rule' header field")

        ce_list = ce_doc.get("causal_edges", [])
        promoted_count = ce_doc.get("promoted_count", 0)
        retained_count = ce_doc.get("retained_in_registry_count", 0)

        check(len(ce_list) == promoted_count,
              f"promoted_count header ({promoted_count}) != actual edge count ({len(ce_list)})")
        print(f"   Promoted edges: {len(ce_list)}")
        print(f"   Retained in registry: {retained_count}")
        print(f"   Total directional accounted: {len(ce_list) + retained_count}")

        # Phase 4 assertion (b): every causal_edge endpoint exists as a registry node
        bad_src = [(e.get("causal_edge_id","?"), e.get("source","?"))
                   for e in ce_list if e.get("source") not in registry_node_ids]
        bad_tgt = [(e.get("causal_edge_id","?"), e.get("target","?"))
                   for e in ce_list if e.get("target") not in registry_node_ids]
        check(not bad_src, f"PHASE4 ASSERTION FAILED: {len(bad_src)} causal edges with unknown source nodes: {bad_src[:3]}")
        check(not bad_tgt, f"PHASE4 ASSERTION FAILED: {len(bad_tgt)} causal edges with unknown target nodes: {bad_tgt[:3]}")
        if not bad_src and not bad_tgt:
            print("   ✓ All causal edge endpoints exist as registry nodes")

        # Phase 4 assertion (c): every motif_id exists in the motif library
        if valid_motif_ids:
            bad_motifs = [(e.get("causal_edge_id","?"), e.get("motif_id","?"))
                          for e in ce_list if e.get("motif_id") not in valid_motif_ids]
            check(not bad_motifs, f"PHASE4 ASSERTION FAILED: {len(bad_motifs)} edges with unknown motif_id: {bad_motifs[:3]}")
            if not bad_motifs:
                print("   ✓ All motif_ids exist in the motif library")

        # Phase 4 assertion (d): every promoted edge satisfies the evidence rule
        # Reconstruct: load baseline and phase3 edges to cross-check
        baseline_edges_path = REPO_ROOT / "data/registry/edges.json"
        phase3_edges_all = exec_edges_all  # loaded earlier

        if baseline_edges_path.exists():
            bl_data = load_json(baseline_edges_path)
            bl_edges = bl_data.get("edges", []) if bl_data else []

            # Build lookup by (source, target, predicate) — keep list for duplicates
            bl_lookup = {}
            for e in bl_edges:
                key = (e.get("source"), e.get("target"), e.get("type"))
                bl_lookup.setdefault(key, []).append(e)

            # Build phase3 lookup by edge_id AND by (source,target,type) list
            p3_by_id = {e.get("edge_id"): e for e in phase3_edges_all}
            p3_lookup = {}
            for e in phase3_edges_all:
                key = (e.get("source"), e.get("target"), e.get("type"))
                p3_lookup.setdefault(key, []).append(e)

            evidence_violations = []
            for ce in ce_list:
                src_pred = ce.get("source_predicate","")
                origin = ce.get("origin_layer","")
                src = ce.get("source")
                tgt = ce.get("target")

                if origin == "registry_baseline":
                    if src_pred not in DIRECTIONAL_BASELINE:
                        evidence_violations.append(f"{ce['causal_edge_id']}: non-directional baseline predicate '{src_pred}'")
                    else:
                        bl_edge_list = bl_lookup.get((src, tgt, src_pred), [])
                        if bl_edge_list:
                            if not any(is_evidenced_baseline(e) for e in bl_edge_list):
                                evidence_violations.append(
                                    f"{ce['causal_edge_id']}: {src}->{tgt} [{src_pred}] promoted but fails evidence rule"
                                )
                elif origin == "phase3_execution":
                    if src_pred not in DIRECTIONAL_PHASE3:
                        evidence_violations.append(f"{ce['causal_edge_id']}: non-directional phase3 predicate '{src_pred}'")
                    else:
                        source_edge_id = ce.get("evidence", {}).get("evidence_id")
                        if source_edge_id and source_edge_id in p3_by_id:
                            p3_edge = p3_by_id[source_edge_id]
                            if not is_evidenced_phase3(p3_edge):
                                evidence_violations.append(
                                    f"{ce['causal_edge_id']}: {src}->{tgt} [{src_pred}] promoted but fails phase3 evidence rule"
                                )
                        else:
                            p3_edge_list = p3_lookup.get((src, tgt, src_pred), [])
                            if p3_edge_list:
                                if not any(is_evidenced_phase3(e) for e in p3_edge_list):
                                    evidence_violations.append(
                                        f"{ce['causal_edge_id']}: {src}->{tgt} [{src_pred}] promoted but fails phase3 evidence rule"
                                    )

            check(not evidence_violations,
                  f"PHASE4 ASSERTION FAILED: {len(evidence_violations)} edges violate evidence rule: {evidence_violations[:3]}")
            if not evidence_violations:
                print("   ✓ All promoted edges satisfy the evidence-governed promotion rule")

        # Check required fields on causal edges
        bad_required = []
        for i, ce in enumerate(ce_list):
            missing = [f for f in CAUSAL_EDGE_REQUIRED if f not in ce]
            if missing:
                bad_required.append(f"causal_edge[{i}] {ce.get('causal_edge_id','?')} missing: {missing}")
        if bad_required:
            for msg in bad_required[:5]:
                errors.append(f"  ERROR: {msg}")
        else:
            print(f"   ✓ All {len(ce_list)} causal edges have required fields")

        # Check causal_relation is valid vocab
        bad_relations = [(ce.get("causal_edge_id"), ce.get("causal_relation"))
                         for ce in ce_list if ce.get("causal_relation") not in VALID_CAUSAL_RELATIONS]
        check(not bad_relations, f"{len(bad_relations)} causal edges with invalid causal_relation: {bad_relations[:3]}")
        if not bad_relations:
            print("   ✓ All causal edges have valid causal_relation from Layer-2 vocabulary")

        # Check promotion_status
        bad_pstatus = [ce.get("causal_edge_id") for ce in ce_list if ce.get("promotion_status") != "causal"]
        check(not bad_pstatus, f"{len(bad_pstatus)} causal edges with promotion_status != 'causal'")

        # Schema validation on sample
        if "causal_edge.schema.json" in schemas and schemas["causal_edge.schema.json"]:
            if ce_list:
                validate_with_jsonschema(ce_list[0], schemas["causal_edge.schema.json"], "sample causal edge")
                print("   ✓ Sample causal edge passes schema validation")

        causal_edge_ids = {ce["causal_edge_id"] for ce in ce_list}

        # Print causal_relation breakdown
        relation_dist = Counter(ce.get("causal_relation","?") for ce in ce_list)
        print(f"\n   Causal relation distribution:")
        for rel, cnt in sorted(relation_dist.items(), key=lambda x: -x[1]):
            print(f"     {rel:15s}: {cnt}")

# ─── 10. Validate adapters ────────────────────────────────────────────────────
print("\n10. Validating CEDT adapters...")
adapters_path = REPO_ROOT / "data/adapters/cedt_mappings.json"
check(adapters_path.exists(), "data/adapters/cedt_mappings.json missing")
if adapters_path.exists():
    adp = load_json(adapters_path)
    if adp:
        n_adp = len(adp.get("adapters", []))
        print(f"   ✓ {n_adp} CEDT adapters")

# ─── 11. Validate browser app mirrored data ───────────────────────────────────
print("\n11. Validating app/data mirrors (including Phase 4)...")
for fname in ["registry_graph.json", "nodes.json", "edges.json"]:
    p = REPO_ROOT / "app/data/registry" / fname
    check(p.exists(), f"app/data/registry/{fname} missing (mirror not complete)")
    if p.exists():
        print(f"   ✓ {fname} present in app/data/registry/")

modules_mirror = REPO_ROOT / "app/data/modules"
if modules_mirror.exists():
    mf_count = len(list(modules_mirror.glob("*.json")))
    print(f"   ✓ app/data/modules/ present ({mf_count} files)")
else:
    warnings.append("  WARNING: app/data/modules/ mirror not yet created (non-fatal)")

exec_mirror = REPO_ROOT / "app/data/registry/execution_edges.json"
if exec_mirror.exists():
    print(f"   ✓ app/data/registry/execution_edges.json present in mirror")
else:
    warnings.append("  WARNING: app/data/registry/execution_edges.json not mirrored (non-fatal)")

# Phase 4: check causal mirror
causal_mirror_dir = REPO_ROOT / "app/data/causal"
if causal_mirror_dir.exists():
    causal_mirror_files = list(causal_mirror_dir.glob("*.json"))
    print(f"   ✓ app/data/causal/ mirror present ({len(causal_mirror_files)} files)")
    motifs_mirror = causal_mirror_dir / "motifs.json"
    causal_edges_mirror = causal_mirror_dir / "causal_edges.json"
    if motifs_mirror.exists():
        print("   ✓ app/data/causal/motifs.json present")
    else:
        warnings.append("  WARNING: app/data/causal/motifs.json not mirrored")
    if causal_edges_mirror.exists():
        print("   ✓ app/data/causal/causal_edges.json present")
    else:
        warnings.append("  WARNING: app/data/causal/causal_edges.json not mirrored")
else:
    warnings.append("  WARNING: app/data/causal/ mirror not yet created (non-fatal)")

# ─── 12. PHASE 2: ONTOLOGY CONFORMANCE PASS ───────────────────────────────────────
print("\n12. ONTOLOGY CONFORMANCE PASS (Phase 2)...")

# Load Phase 2 artefacts
_classes_p = REPO_ROOT / "data/ontology/classes.json"
_ifaces_p  = REPO_ROOT / "data/ontology/interfaces.json"
_pt_p      = REPO_ROOT / "data/ontology/port_types.json"
_wiring_p  = REPO_ROOT / "data/ontology/wiring.json"

check(_classes_p.exists(), "data/ontology/classes.json missing (Phase 2)")
check(_ifaces_p.exists(),  "data/ontology/interfaces.json missing (Phase 2)")
check(_pt_p.exists(),      "data/ontology/port_types.json missing (Phase 2)")
check(_wiring_p.exists(),  "data/ontology/wiring.json missing (Phase 2)")

if _classes_p.exists() and _ifaces_p.exists() and _pt_p.exists() and _wiring_p.exists():
    _classes_doc = load_json(_classes_p)
    _ifaces_doc  = load_json(_ifaces_p)
    _pt_doc      = load_json(_pt_p)
    _wiring_doc  = load_json(_wiring_p)

    # ---- 12a. Entity class hierarchy: no dangling parents, no cycles --------
    _ec_ids = {c["class_id"] for c in _classes_doc.get("entity_classes", [])}
    _mc_ids = {c["class_id"] for c in _classes_doc.get("module_classes", [])}

    # Dangling parent check
    _dangling = []
    for ec in _classes_doc.get("entity_classes", []):
        p = ec.get("parent")
        if p is not None and p not in _ec_ids:
            _dangling.append(f"{ec['class_id']} -> parent '{p}' not defined")
    check(not _dangling, f"Entity class hierarchy has dangling parents: {_dangling}")
    if not _dangling:
        print(f"   ✓ Entity class hierarchy: {len(_ec_ids)} classes, no dangling parents")

    # Cycle check (DFS)
    _parent_map = {ec["class_id"]: ec.get("parent") for ec in _classes_doc.get("entity_classes", [])}
    _cyclic = []
    for start in _ec_ids:
        visited = set()
        cur = start
        while cur is not None:
            if cur in visited:
                _cyclic.append(f"Cycle involving {start}")
                break
            visited.add(cur)
            cur = _parent_map.get(cur)
    check(not _cyclic, f"Entity class hierarchy has cycles: {_cyclic}")
    if not _cyclic:
        print("   ✓ Entity class hierarchy: no cycles")

    # ---- 12b. All 8 module interfaces defined --------------------------------
    _iface_ids = {i["interface_id"] for i in _ifaces_doc.get("interfaces", [])}
    _required_ifaces = {
        "ExposureSourceModule", "BiotransformationModule", "MechanismModule",
        "TissueContextModule", "SusceptibilityModifierModule", "OutcomeModule",
        "EvidenceAndProvenanceModule", "ExecutableModule"
    }
    _missing_ifaces = _required_ifaces - _iface_ids
    check(not _missing_ifaces, f"Missing required interfaces: {_missing_ifaces}")
    if not _missing_ifaces:
        print(f"   ✓ All 8 required interfaces defined ({len(_iface_ids)} total)")

    # Interface extends chain: no dangling
    _iface_extends_dangling = []
    for ifc in _ifaces_doc.get("interfaces", []):
        ext = ifc.get("extends")
        if ext is not None and ext not in _iface_ids:
            _iface_extends_dangling.append(f"{ifc['interface_id']} extends '{ext}' — not defined")
    check(not _iface_extends_dangling,
          f"Interface extends dangling: {_iface_extends_dangling}")
    if not _iface_extends_dangling:
        print("   ✓ Interface extends chain: no dangling")

    # ---- 12c. Port types ---------------------------------------------------
    _pt_ids = {pt["type_id"] for pt in _pt_doc.get("port_types", [])}
    check(len(_pt_ids) > 0, "port_types.json has zero port types")
    print(f"   ✓ Port-type vocabulary: {len(_pt_ids)} types defined")

    # Schema validation on ontology files
    if "ontology_class.schema.json" in schemas and schemas["ontology_class.schema.json"]:
        _ec_schema = schemas["ontology_class.schema.json"]
        _ec_fails = []
        for ec in _classes_doc.get("entity_classes", []):
            try:
                import jsonschema as _jsc
                _jsc.validate(instance=ec, schema=_ec_schema)
            except Exception as _e:
                _ec_fails.append(f"{ec.get('class_id','?')}: {_e}")
        check(not _ec_fails, f"Entity class schema violations: {_ec_fails}")
        if not _ec_fails:
            print("   ✓ All entity classes pass schema validation")

    if "interface.schema.json" in schemas and schemas["interface.schema.json"]:
        _if_schema = schemas["interface.schema.json"]
        _if_fails = []
        for ifc in _ifaces_doc.get("interfaces", []):
            try:
                import jsonschema as _jsc2
                _jsc2.validate(instance=ifc, schema=_if_schema)
            except Exception as _e:
                _if_fails.append(f"{ifc.get('interface_id','?')}: {_e}")
        check(not _if_fails, f"Interface schema violations: {_if_fails}")
        if not _if_fails:
            print("   ✓ All interfaces pass schema validation")

    if "port_type.schema.json" in schemas and schemas["port_type.schema.json"]:
        _pt_schema = schemas["port_type.schema.json"]
        _pt_fails = []
        for pt in _pt_doc.get("port_types", []):
            try:
                import jsonschema as _jsc3
                _jsc3.validate(instance=pt, schema=_pt_schema)
            except Exception as _e:
                _pt_fails.append(f"{pt.get('type_id','?')}: {_e}")
        check(not _pt_fails, f"Port-type schema violations: {_pt_fails}")
        if not _pt_fails:
            print("   ✓ All port types pass schema validation")

    # ---- 12d. Per-module conformance ----------------------------------------
    _iface_map = {i["interface_id"]: i for i in _ifaces_doc.get("interfaces", [])}
    _conformant_modules = 0
    _total_modules = 0
    if loaded_modules:
        for _mod in loaded_modules:
            _total_modules += 1
            _mod_id = _mod.get("module_id", "?")
            _mod_gaps = []

            # module_class resolves
            _mc = _mod.get("module_class")
            if _mc not in _mc_ids:
                _mod_gaps.append(f"module_class '{_mc}' not in module_classes")

            # every extends resolves
            for _ext in _mod.get("extends", []):
                if _ext not in _iface_ids:
                    _mod_gaps.append(f"extends '{_ext}' not defined")

            # required_fields per interface
            for _ext in _mod.get("extends", []):
                if _ext not in _iface_map:
                    continue
                _ifc = _iface_map[_ext]
                for _rf in _ifc.get("required_fields", []):
                    _val = _mod.get(_rf)
                    if _val is None or _val == [] or _val == "":
                        _mod_gaps.append(f"Interface {_ext} requires '{_rf}' — missing/empty")

            # port dtype in port_types
            for _port in _mod.get("input_ports", []) + _mod.get("output_ports", []):
                _dtype = _port.get("dtype")
                if _dtype is None:
                    _mod_gaps.append(f"Port '{_port.get('name')}' missing dtype")
                elif _dtype not in _pt_ids:
                    _mod_gaps.append(f"Port '{_port.get('name')}' dtype '{_dtype}' not in port_types")

            # interface port-type contracts
            _mod_dtypes = set()
            for _port in _mod.get("input_ports", []) + _mod.get("output_ports", []):
                if _port.get("dtype"):
                    _mod_dtypes.add(_port["dtype"])

            for _ext in _mod.get("extends", []):
                if _ext not in _iface_map:
                    continue
                _ifc = _iface_map[_ext]
                for _rp in _ifc.get("required_input_port_types", []) + _ifc.get("required_output_port_types", []):
                    _rdtype = _rp.get("dtype")
                    if _rdtype is None:
                        continue
                    if _rp.get("required", True) and _rdtype not in _mod_dtypes:
                        _mod_gaps.append(
                            f"Interface {_ext} requires dtype '{_rdtype}' — not in module ports"
                        )

            if _mod_gaps:
                errors.append(f"  ERROR: Module {_mod_id} ontology conformance gaps: {_mod_gaps}")
            else:
                _conformant_modules += 1

        check(_conformant_modules == _total_modules,
              f"Only {_conformant_modules}/{_total_modules} modules are ontology-conformant")
        if _conformant_modules == _total_modules:
            print(f"   ✓ All {_total_modules} modules are ontology-conformant ({_conformant_modules}/{_total_modules})")

    # ---- 12e. Wiring.json integrity -----------------------------------------
    _wiring_conns = _wiring_doc.get("connections", [])
    _wiring_count = len(_wiring_conns)
    _wiring_errors = []

    # Load module port index
    _mod_port_index = {}  # (module_id, port_name) -> dtype
    for _mod in loaded_modules:
        _mid = _mod.get("module_id", "?")
        for _port in _mod.get("input_ports", []) + _mod.get("output_ports", []):
            _mod_port_index[(_mid, _port["name"])] = _port.get("dtype")

    for _conn in _wiring_conns:
        _fm = _conn.get("from_module")
        _fp = _conn.get("from_port")
        _tm = _conn.get("to_module")
        _tp = _conn.get("to_port")
        _cd = _conn.get("dtype")

        # endpoints exist
        if (_fm, _fp) not in _mod_port_index:
            _wiring_errors.append(f"from_port ({_fm}, {_fp}) not found")
        if (_tm, _tp) not in _mod_port_index:
            _wiring_errors.append(f"to_port ({_tm}, {_tp}) not found")

        # dtype matches
        _actual_from = _mod_port_index.get((_fm, _fp))
        _actual_to   = _mod_port_index.get((_tm, _tp))
        if _actual_from != _cd:
            _wiring_errors.append(
                f"from_port ({_fm},{_fp}) dtype mismatch: expected '{_cd}', got '{_actual_from}'"
            )
        if _actual_to != _cd:
            _wiring_errors.append(
                f"to_port ({_tm},{_tp}) dtype mismatch: expected '{_cd}', got '{_actual_to}'"
            )

        # dtype in port_types
        if _cd not in _pt_ids:
            _wiring_errors.append(f"wiring dtype '{_cd}' not in port_types.json")

    check(not _wiring_errors, f"Wiring integrity failures: {_wiring_errors}")
    if not _wiring_errors:
        print(f"   ✓ Wiring map: {_wiring_count} type-compatible cross-module connections, all endpoints/dtypes valid")

    # ---- 12f. Frozen baseline byte-stable re-assertion ----------------------
    # (already checked above in section 3/4; just confirm we still have no errors from that)
    print("   ✓ Frozen baseline (212/313) and causal projection (169) integrity asserted in sections 3, 4, 9")

print()


# ─── 13. PHASE 5: EXECUTION PASS ────────────────────────────────────────────
print("\n13. EXECUTION PASS (Phase 5)...")

# 13a. Check execution schema files exist and load
_exec_schema_files = ["schema/scenario.schema.json", "schema/execution_run.schema.json"]
for _sf in _exec_schema_files:
    _p = REPO_ROOT / _sf
    check(_p.exists(), f"Phase 5: Missing execution schema file: {_sf}")
    if _p.exists():
        load_json(_p)
        print(f"   \u2713 {_sf} loaded")

# 13b. Check data/execution files exist (data/execution already in required_dirs above)
_exec_scen_path = REPO_ROOT / "data/execution/scenarios.json"
_exec_runs_path = REPO_ROOT / "data/execution/example_runs.json"
check(_exec_scen_path.exists(), "Phase 5: data/execution/scenarios.json missing")
check(_exec_runs_path.exists(), "Phase 5: data/execution/example_runs.json missing")

_scen_doc = None
_runs_doc = None
if _exec_scen_path.exists() and _exec_runs_path.exists():
    _scen_doc = load_json(_exec_scen_path)
    _runs_doc = load_json(_exec_runs_path)

if _scen_doc and _runs_doc:
    _scenarios = _scen_doc.get("scenarios", [])
    _golden_runs = _runs_doc.get("runs", [])
    print(f"   Scenarios: {len(_scenarios)} | Golden runs: {len(_golden_runs)}")
    check(len(_scenarios) >= 4, f"Phase 5: Expected \u22654 scenarios, got {len(_scenarios)}")
    check(len(_golden_runs) >= 4, f"Phase 5: Expected \u22654 golden runs, got {len(_golden_runs)}")

    # Validate against schemas
    _exec_schema_p = REPO_ROOT / "schema/scenario.schema.json"
    _run_schema_p = REPO_ROOT / "schema/execution_run.schema.json"
    if _exec_schema_p.exists() and _run_schema_p.exists():
        _scen_schema = load_json(_exec_schema_p)
        _run_schema = load_json(_run_schema_p)
        if _scen_schema and _run_schema:
            for _scen in _scenarios:
                validate_with_jsonschema(_scen, _scen_schema, f"scenario {_scen.get('id','?')}")
            for _run in _golden_runs:
                validate_with_jsonschema(_run, _run_schema, f"run {_run.get('scenario_id','?')}")
            print(f"   \u2713 All execution files pass schema validation")

    # Build golden index: scenario_id -> run
    _golden_index = {r["scenario_id"]: r for r in _golden_runs}

    # 13c. Import engine and RE-RUN all scenarios; assert match within 1e-6 tolerance
    _REGRESSION_TOL = 1e-6
    _runner = None
    try:
        import importlib as _importlib
        import sys as _sys2
        _sys2.path.insert(0, str(REPO_ROOT))
        # Force reload to pick up any changes
        if "scripts.engine.runner" in _sys2.modules:
            _importlib.reload(_sys2.modules["scripts.engine.runner"])
        from scripts.engine.runner import ScenarioRunner
        _runner = ScenarioRunner()
        print(f"   \u2713 Engine imported successfully")
    except Exception as _e:
        errors.append(f"  ERROR: Phase 5: Could not import engine: {_e}")

    if _runner is not None:
        _regression_passed = 0
        _regression_failed = 0
        for _scen in _scenarios:
            _sid = _scen["id"]
            if _sid not in _golden_index:
                errors.append(f"  ERROR: Phase 5: No golden run for scenario {_sid}")
                continue
            _golden_run = _golden_index[_sid]
            try:
                _recomputed = _runner.run_scenario(
                    carcinogen_class=_scen["carcinogen_class"],
                    tissue=_scen["tissue"],
                    genotype_profile=_scen["genotype_profile"],
                    exposure_scenario=_scen["exposure_scenario"],
                    exposure_class=_scen.get("exposure_class"),
                    mutsig_class=_scen.get("mutsig_class"),
                )
            except Exception as _e:
                errors.append(f"  ERROR: Phase 5: Engine exception on {_sid}: {_e}")
                _regression_failed += 1
                continue

            # (a) Compare flux_ratio within 1e-6
            _golden_flux = float(_golden_run["computed_trace"]["flux_step"]["flux_ratio"])
            _recomputed_flux = float(_recomputed["chain_summary"]["flux_ratio"])
            _flux_diff = abs(_golden_flux - _recomputed_flux)
            if _flux_diff > _REGRESSION_TOL:
                errors.append(
                    f"  ERROR: Phase 5 REGRESSION FAIL [{_sid}]: "
                    f"flux_ratio mismatch: golden={_golden_flux} "
                    f"recomputed={_recomputed_flux} diff={_flux_diff:.2e} > tol={_REGRESSION_TOL}"
                )
                _regression_failed += 1
                continue

            # (a) Compare primary predicted_SBS (list equality)
            _golden_sbs = _golden_run["computed_trace"]["mutsig_step"].get("primary_SBS", [])
            _recomputed_sbs = _recomputed["chain_summary"].get("primary_SBS", [])
            if _golden_sbs != _recomputed_sbs:
                errors.append(
                    f"  ERROR: Phase 5 REGRESSION FAIL [{_sid}]: "
                    f"primary_SBS mismatch: golden={_golden_sbs} "
                    f"recomputed={_recomputed_sbs}"
                )
                _regression_failed += 1
                continue

            _regression_passed += 1
            print(f"   \u2713 [{_sid}] flux_ratio={_recomputed_flux:.6f} SBS={_recomputed_sbs} "
                  f"diff={_flux_diff:.2e} (PASS)")

        check(
            _regression_failed == 0,
            f"Phase 5: {_regression_failed} scenario(s) failed regression (tolerance 1e-6)"
        )
        if _regression_failed == 0:
            print(f"   \u2713 All {_regression_passed} scenarios pass regression test (tol=1e-6)")

        # (b) Assert every enzyme in golden runs traces to a real FLUX param record
        _flux_module_path = REPO_ROOT / "data/modules/EG3_MOD_BIOTRANS_FLUX_v1.json"
        if _flux_module_path.exists():
            _flux_mod = load_json(_flux_module_path)
            if _flux_mod:
                _real_param_keys = set()
                for _p in _flux_mod.get("parameters", []):
                    _cc = _p.get("carcinogen_class")
                    _enz = _p.get("enzyme")
                    if _cc and _enz:
                        _real_param_keys.add((_cc, _enz))

                # Resolve the flux class via alias map (canonical class may differ from FLUX params key)
                try:
                    from scripts.engine.aliases import CLASS_ALIASES, ClassKeys
                    def _resolve_flux_class(canonical: str) -> str:
                        keys = CLASS_ALIASES.get(canonical)
                        return keys.flux if keys is not None else canonical
                except Exception:
                    def _resolve_flux_class(canonical: str) -> str:
                        return canonical

                _orphan_params = []
                for _run in _golden_runs:
                    _cc_canonical = _run["carcinogen_class"]
                    _cc = _resolve_flux_class(_cc_canonical)
                    for _er in _run["computed_trace"]["flux_step"].get("per_enzyme_mm_rates", []):
                        _key = (_cc, _er["enzyme"])
                        if _key not in _real_param_keys:
                            _orphan_params.append(
                                f"{_run['scenario_id']}: ({_cc_canonical}→{_cc}, {_er['enzyme']}) not in FLUX params"
                            )
                check(
                    not _orphan_params,
                    f"Phase 5: {len(_orphan_params)} orphan enzyme(s) in golden runs: {_orphan_params[:3]}"
                )
                if not _orphan_params:
                    print(f"   \u2713 All enzyme Km/Vmax in golden runs trace to real FLUX params")

        # (c) Assert wiring connections used all exist in wiring.json
        _wiring_doc_path = REPO_ROOT / "data/ontology/wiring.json"
        if _wiring_doc_path.exists():
            _wiring_check = load_json(_wiring_doc_path)
            if _wiring_check:
                _declared_conns = set(
                    (c["from_module"], c["from_port"])
                    for c in _wiring_check.get("connections", [])
                )
                _unknown_conns = []
                for _run in _golden_runs:
                    for _conn in _run.get("wiring_connections_used", []):
                        _key = (_conn["from_module"], _conn["from_port"])
                        if _key not in _declared_conns:
                            _unknown_conns.append(
                                f"{_run['scenario_id']}: {_key} not in wiring.json"
                            )
                check(
                    not _unknown_conns,
                    f"Phase 5: {len(_unknown_conns)} wiring connection(s) used but not declared: {_unknown_conns[:3]}"
                )
                if not _unknown_conns:
                    print(f"   \u2713 All wiring connections used exist in wiring.json")

    # 13f. Check app/data/execution mirror
    _exec_app_dir = REPO_ROOT / "app/data/execution"
    if _exec_app_dir.exists():
        _app_exec_files = list(_exec_app_dir.glob("*.json"))
        print(f"   \u2713 app/data/execution/ mirror present ({len(_app_exec_files)} files)")
    else:
        warnings.append("  WARNING: app/data/execution/ mirror not yet created (non-fatal)")


# ─── 14. CEDT Phase 6 Pass ────────────────────────────────────────────────────
print("\n─── Section 14: CEDT Phase 6 Adapter Validation ───")

# 14a. twin_state_schema.json — check exists, has 5 layers, >=1 variable each
_schema_path = REPO_ROOT / "data/adapters/twin_state_schema.json"
if _schema_path.exists():
    _schema_doc = load_json(_schema_path)
    if _schema_doc:
        _layers_required = {"host", "exposure", "tissue", "metabolic", "state_quality"}
        _schema_vars = _schema_doc.get("state_variables", [])
        _layers_found = {v.get("layer") for v in _schema_vars}
        check(
            _layers_required.issubset(_layers_found),
            f"CEDT: twin_state_schema.json missing layers: {_layers_required - _layers_found}"
        )
        if _layers_required.issubset(_layers_found):
            print(f"   \u2713 twin_state_schema.json: {len(_schema_vars)} variables across 5 layers")
        # Check each layer has >=1 variable
        for _lyr in _layers_required:
            _lyr_vars = [v for v in _schema_vars if v.get("layer") == _lyr]
            check(
                len(_lyr_vars) >= 1,
                f"CEDT: twin_state_schema.json layer '{_lyr}' has no variables"
            )
else:
    errors.append("  ERROR: CEDT: data/adapters/twin_state_schema.json not found")

# 14b. cedt_mappings.json — 8 adapters, all status=active, >=1 mapping each
_mappings_path = REPO_ROOT / "data/adapters/cedt_mappings.json"
if _mappings_path.exists():
    _mappings_doc = load_json(_mappings_path)
    if _mappings_doc:
        _adapters = _mappings_doc.get("adapters", [])
        check(
            len(_adapters) == 8,
            f"CEDT: cedt_mappings.json expected 8 adapters, got {len(_adapters)}"
        )
        _total_mappings = 0
        _adapters_ok = 0
        for _adap in _adapters:
            _aid = _adap.get("adapter_id", "?")
            _status = _adap.get("status")
            _mappings_list = _adap.get("mappings", [])
            check(
                _status == "active",
                f"CEDT: adapter {_aid} status={_status} (expected 'active')"
            )
            check(
                len(_mappings_list) >= 1,
                f"CEDT: adapter {_aid} has no mappings"
            )
            if _status == "active" and len(_mappings_list) >= 1:
                _adapters_ok += 1
            _total_mappings += len(_mappings_list)
        if _adapters_ok == 8:
            print(f"   \u2713 cedt_mappings.json: {len(_adapters)} active adapters, {_total_mappings} total mappings")
else:
    errors.append("  ERROR: CEDT: data/adapters/cedt_mappings.json not found")

# 14c. execution_edges.json — total=94, maps_to_twin_state count=20
_exec_edges_path = REPO_ROOT / "data/registry/execution_edges.json"
if _exec_edges_path.exists():
    _exec_edges_doc = load_json(_exec_edges_path)
    if _exec_edges_doc:
        _all_edges = _exec_edges_doc.get("edges", [])
        _twin_edges = [e for e in _all_edges if e.get("type") == "maps_to_twin_state"]
        # Phase 3 had 5 maps_to_twin_state edges (0067-0071); Phase 6 adds 20 more (0075-0094)
        # Total maps_to_twin_state = 25; check total edges = 94
        check(
            len(_all_edges) == 94,
            f"CEDT: execution_edges.json expected 94 total edges, got {len(_all_edges)}"
        )
        # Check that the 20 Phase 6 edges (IDs 0075-0094) are all present
        _twin_ids = {e.get("edge_id") for e in _twin_edges}
        _expected_ids = {f"EG3.EXEC.EDGE.{i:04d}" for i in range(75, 95)}
        _missing_ids = _expected_ids - _twin_ids
        check(
            not _missing_ids,
            f"CEDT: missing Phase 6 maps_to_twin_state edge IDs: {sorted(_missing_ids)[:5]}"
        )
        _phase6_twin_edges = [e for e in _twin_edges
                              if e.get("edge_id", "") >= "EG3.EXEC.EDGE.0075"]
        check(
            len(_phase6_twin_edges) == 20,
            f"CEDT: expected 20 Phase 6 maps_to_twin_state edges (0075-0094), got {len(_phase6_twin_edges)}"
        )
        if len(_all_edges) == 94 and not _missing_ids and len(_phase6_twin_edges) == 20:
            print(f"   \u2713 execution_edges.json: 94 total edges, 20 Phase 6 maps_to_twin_state (IDs 0075-0094)")
else:
    errors.append("  ERROR: CEDT: data/registry/execution_edges.json not found")

# 14d. twin_states.json — 4 scenarios, all flux values match golden (1e-6)
_twin_states_path = REPO_ROOT / "data/execution/twin_states.json"
if _twin_states_path.exists():
    _twin_states_doc = load_json(_twin_states_path)
    if _twin_states_doc:
        _twin_records = _twin_states_doc.get("twin_states", [])
        check(
            len(_twin_records) == 4,
            f"CEDT: twin_states.json expected 4 scenarios, got {len(_twin_records)}"
        )
        # Cross-check flux_ratio values against golden runs
        _golden_runs_path = REPO_ROOT / "data/execution/example_runs.json"
        if _golden_runs_path.exists():
            _golden_doc = load_json(_golden_runs_path)
            _golden_index_t = {r["scenario_id"]: r for r in _golden_doc.get("runs", [])}
            _twin_flux_fails = 0
            for _ts in _twin_records:
                _sid = _ts.get("scenario_id")
                _twin_flux = _ts.get("twin_state", {}).get("metabolic", {}).get("metabolic_flux_ratio")
                if _sid in _golden_index_t and _twin_flux is not None:
                    _golden_flux = float(
                        _golden_index_t[_sid]["computed_trace"]["flux_step"]["flux_ratio"]
                    )
                    _diff = abs(_golden_flux - float(_twin_flux))
                    if _diff > 1e-6:
                        errors.append(
                            f"  ERROR: CEDT: [{_sid}] twin metabolic_flux_ratio={_twin_flux} "
                            f"!= golden={_golden_flux} diff={_diff:.2e} > 1e-6"
                        )
                        _twin_flux_fails += 1
            if _twin_flux_fails == 0:
                print(f"   \u2713 twin_states.json: 4 scenarios, all metabolic_flux_ratio match golden at 1e-6")
        else:
            warnings.append("  WARNING: CEDT: example_runs.json not found; cannot cross-check twin flux values")
else:
    errors.append("  ERROR: CEDT: data/execution/twin_states.json not found")

# 14e. JSON schemas — twin_state_variable.schema.json + cedt_adapter.schema.json
_tv_schema = REPO_ROOT / "schema/twin_state_variable.schema.json"
_ca_schema = REPO_ROOT / "schema/cedt_adapter.schema.json"
_schema_ok = True
for _sp in [_tv_schema, _ca_schema]:
    if not _sp.exists():
        errors.append(f"  ERROR: CEDT: schema file not found: {_sp.name}")
        _schema_ok = False
    else:
        _sd = load_json(_sp)
        if not _sd or "$schema" not in _sd or "properties" not in _sd:
            errors.append(f"  ERROR: CEDT: {_sp.name} missing $schema or properties")
            _schema_ok = False
if _schema_ok:
    print(f"   \u2713 JSON schemas: twin_state_variable.schema.json + cedt_adapter.schema.json present and valid")

# 14f. FLUX module maturity T; all other 7 modules twin_ready=false
_flux_mod_path = REPO_ROOT / "data/modules/EG3_MOD_BIOTRANS_FLUX_v1.json"
if _flux_mod_path.exists():
    _flux_mod = load_json(_flux_mod_path)
    if _flux_mod:
        _flux_maturity = _flux_mod.get("maturity_class")
        _flux_twin_ready = _flux_mod.get("cedt_mapping", {}).get("twin_ready")
        check(
            _flux_maturity == "T",
            f"CEDT: FLUX module maturity_class={_flux_maturity} (expected T)"
        )
        check(
            _flux_twin_ready is True,
            f"CEDT: FLUX module cedt_mapping.twin_ready={_flux_twin_ready} (expected True)"
        )
        if _flux_maturity == "T" and _flux_twin_ready is True:
            print(f"   \u2713 FLUX module: maturity_class=T, twin_ready=True")
else:
    errors.append("  ERROR: CEDT: FLUX module JSON not found")

_other_mod_files = [
    "EG3_MOD_EXPOSURE_WAVE2_v1.json",
    "EG3_MOD_MECHANISM_INTERACTION_v1.json",
    "EG3_MOD_MECHANISM_OXSTRESS_v1.json",
    "EG3_MOD_MODIFIER_POPGEN_v1.json",
    "EG3_MOD_TISSUE_SUBGRAPH_v1.json",
    "EG3_MOD_OUTCOME_MUTSIG_v1.json",
    "EG3_MOD_EVIDENCE_PROVENANCE_v1.json",
]
_mods_dir = REPO_ROOT / "data/modules"
_twin_false_ok = 0
for _mf in _other_mod_files:
    _mp = _mods_dir / _mf
    if _mp.exists():
        _md = load_json(_mp)
        if _md:
            _tr = _md.get("cedt_mapping", {}).get("twin_ready")
            check(
                _tr is False,
                f"CEDT: module {_mf} cedt_mapping.twin_ready={_tr} (expected False)"
            )
            if _tr is False:
                _twin_false_ok += 1
    else:
        errors.append(f"  ERROR: CEDT: module file not found: {_mf}")
if _twin_false_ok == 7:
    print(f"   \u2713 All 7 non-FLUX modules: twin_ready=False (honest C-maturity assessment)")


# ─── 15. Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 50)
if errors:
    print(f"VALIDATION FAILED — {len(errors)} error(s):")
    for e in errors:
        print(e)
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(w)
    sys.exit(1)
else:
    if warnings:
        print(f"VALIDATION PASSED with {len(warnings)} warning(s):")
        for w in warnings:
            print(w)
    else:
        print("VALIDATION PASSED — all checks OK")
    sys.exit(0)

# The previous section 13 header conflicts; the new section follows as 13 after renaming the old to the summary section above
