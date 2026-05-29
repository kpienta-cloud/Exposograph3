#!/usr/bin/env python3
"""
ExposoGraph 3.0 — Phase 4 Validation Script
Validates all JSON files against schemas and checks Phase 1 + Phase 3 + Phase 4 requirements.
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
schema_files = [
    "registry_node.schema.json", "registry_edge.schema.json",
    "module.schema.json", "causal_motif.schema.json", "ontology_class.schema.json",
    "execution_edge.schema.json", "causal_edge.schema.json"
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

# ─── 12. Summary ──────────────────────────────────────────────────────────────
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
