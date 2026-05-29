#!/usr/bin/env python3
"""
ExposoGraph 3.0 — Phase 1 Validation Script
Validates all JSON files against schemas and checks Phase 1 requirements.
Exits 0 on success, non-zero on failure.
"""

import json
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Phase 1 required metadata fields for nodes and edges
NODE_PHASE1_FIELDS = {"entity_type", "module_membership", "evidence_id", "version_origin", "promotion_status"}
EDGE_PHASE1_FIELDS = {"edge_family", "module_membership", "evidence_id", "version_origin", "promotion_status"}

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


# ─── 1. Check directory structure ─────────────────────────────────────────────
print("=== ExposoGraph 3.0 Phase 1 Validation ===\n")

required_dirs = [
    "app", "data/ontology", "data/registry", "data/causal",
    "data/modules", "data/evidence", "data/adapters", "schema", "docs", "scripts",
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
for schema_file in ["registry_node.schema.json", "registry_edge.schema.json",
                     "module.schema.json", "causal_motif.schema.json", "ontology_class.schema.json"]:
    path = schema_dir / schema_file
    if path.exists():
        schemas[schema_file] = load_json(path)
        print(f"   ✓ Loaded {schema_file}")
    else:
        errors.append(f"  ERROR: Missing schema file: {schema_file}")

# ─── 3. Validate registry graph ───────────────────────────────────────────────
print("\n3. Validating registry graph...")
reg_graph_path = REPO_ROOT / "data/registry/registry_graph.json"
check(reg_graph_path.exists(), "data/registry/registry_graph.json missing")

if reg_graph_path.exists():
    reg = load_json(reg_graph_path)
    if reg:
        check(reg.get("bundle") == "Registry Graph v2-compat",
              f"bundle name mismatch: got '{reg.get('bundle')}'")
        nodes = reg.get("nodes", [])
        edges = reg.get("edges", [])

        check(len(nodes) == 212, f"Expected 212 nodes, got {len(nodes)}")
        check(len(edges) == 313, f"Expected 313 edges, got {len(edges)}")
        print(f"   Node count: {len(nodes)}, Edge count: {len(edges)}")

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

        # Validate promotion_status = "registry" for all
        bad_promo_nodes = [n.get("id","?") for n in nodes if n.get("promotion_status") != "registry"]
        bad_promo_edges = [f"{e.get('source','?')}->{e.get('target','?')}"
                           for e in edges if e.get("promotion_status") != "registry"]
        check(not bad_promo_nodes, f"{len(bad_promo_nodes)} nodes with promotion_status != 'registry'")
        check(not bad_promo_edges, f"{len(bad_promo_edges)} edges with promotion_status != 'registry'")
        if not bad_promo_nodes and not bad_promo_edges:
            print("   ✓ All nodes and edges have promotion_status='registry'")

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

# ─── 5. Validate module records ───────────────────────────────────────────────
print("\n5. Validating module records...")
modules_dir = REPO_ROOT / "data/modules"
module_files = list(modules_dir.glob("*.json"))
check(len(module_files) == 8, f"Expected 8 module files, got {len(module_files)}: {[f.name for f in module_files]}")

loaded_modules = []
for mf in module_files:
    m = load_json(mf)
    if m:
        loaded_modules.append(m)
        if "module.schema.json" in schemas and schemas["module.schema.json"]:
            validate_with_jsonschema(m, schemas["module.schema.json"], mf.name)
        # Check required fields
        for req in ["module_id","module_name","module_class","maturity_class","extends","scope","version","evidence_bundle"]:
            check(req in m, f"Module {mf.name} missing required field: {req}")

print(f"   ✓ {len(loaded_modules)} module records loaded")
for m in sorted(loaded_modules, key=lambda x: x.get("module_id","")):
    nn = len(m.get("graph_nodes", []))
    ne = len(m.get("graph_edges", []))
    print(f"     {m['module_id']}: {nn} nodes, {ne} edges")

# ─── 6. Validate ontology ────────────────────────────────────────────────────
print("\n6. Validating ontology layer...")
for fname in ["interfaces.json", "classes.json"]:
    p = REPO_ROOT / "data/ontology" / fname
    check(p.exists(), f"data/ontology/{fname} missing")
    if p.exists():
        d = load_json(p)
        print(f"   ✓ {fname} loaded")

# ─── 7. Validate causal motifs ────────────────────────────────────────────────
print("\n7. Validating causal motifs...")
motifs_path = REPO_ROOT / "data/causal/motifs.json"
check(motifs_path.exists(), "data/causal/motifs.json missing")
if motifs_path.exists():
    motifs = load_json(motifs_path)
    if motifs:
        n_motifs = len(motifs.get("motifs", []))
        check(n_motifs == 5, f"Expected 5 causal motifs, got {n_motifs}")
        print(f"   ✓ {n_motifs} causal motifs")
        for mot in motifs.get("motifs", []):
            if "causal_motif.schema.json" in schemas and schemas["causal_motif.schema.json"]:
                validate_with_jsonschema(mot, schemas["causal_motif.schema.json"], mot.get("motif_id","?"))

# ─── 8. Validate adapters ─────────────────────────────────────────────────────
print("\n8. Validating CEDT adapters...")
adapters_path = REPO_ROOT / "data/adapters/cedt_mappings.json"
check(adapters_path.exists(), "data/adapters/cedt_mappings.json missing")
if adapters_path.exists():
    adp = load_json(adapters_path)
    if adp:
        n_adp = len(adp.get("adapters", []))
        print(f"   ✓ {n_adp} CEDT adapters")

# ─── 9. Validate browser app mirrored data ────────────────────────────────────
print("\n9. Validating app/data/registry mirror...")
for fname in ["registry_graph.json", "nodes.json", "edges.json"]:
    p = REPO_ROOT / "app/data/registry" / fname
    check(p.exists(), f"app/data/registry/{fname} missing (mirror not complete)")
    if p.exists():
        print(f"   ✓ {fname} present in app/data/registry/")

# ─── 10. Summary ──────────────────────────────────────────────────────────────
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
