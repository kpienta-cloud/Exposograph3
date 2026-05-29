#!/usr/bin/env python3
"""
ExposoGraph 3.0 — Build Registry Summary
Reads registry data and writes data/registry/registry_summary.json.
Prints summary table with node/edge counts by type/family, and module counts.
"""

import json
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).parent.parent


def main():
    print("=== ExposoGraph 3.0 — Registry Summary Builder ===\n")

    # Load registry
    reg_path = REPO_ROOT / "data/registry/registry_graph.json"
    if not reg_path.exists():
        print(f"ERROR: {reg_path} not found. Run ingestion first.", file=sys.stderr)
        sys.exit(1)

    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    nodes = reg.get("nodes", [])
    edges = reg.get("edges", [])

    print(f"Bundle:  {reg.get('bundle')}")
    print(f"Origin:  {reg.get('version_origin')}")
    print(f"Nodes:   {len(nodes)}")
    print(f"Edges:   {len(edges)}")

    # Node type distribution
    node_type_counts = Counter(n.get("entity_type", n.get("type", "unknown")) for n in nodes)
    print("\n--- Node Types ---")
    for ntype, cnt in sorted(node_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ntype:20s}: {cnt}")

    # Edge type distribution (original type field)
    edge_type_counts = Counter(e.get("type", "unknown") for e in edges)
    print("\n--- Edge Types (original predicates) ---")
    for etype, cnt in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype:30s}: {cnt}")

    # Edge family distribution
    edge_family_counts = Counter(e.get("edge_family", "unknown") for e in edges)
    print("\n--- Edge Family Distribution ---")
    for fam, cnt in sorted(edge_family_counts.items(), key=lambda x: -x[1]):
        print(f"  {fam:20s}: {cnt}")

    # Module records
    modules_dir = REPO_ROOT / "data/modules"
    module_files = sorted(modules_dir.glob("*.json"))
    modules = []
    for mf in module_files:
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            modules.append(m)
        except Exception as e:
            print(f"WARNING: Could not load {mf.name}: {e}", file=sys.stderr)

    print(f"\n--- Module Records ({len(modules)}) ---")
    for m in sorted(modules, key=lambda x: x.get("module_id", "")):
        nn = len(m.get("graph_nodes", []))
        ne = len(m.get("graph_edges", []))
        mc = m.get("maturity_class", "?")
        print(f"  [{mc}] {m['module_id']}: {nn} nodes, {ne} edges")

    # Phase 1 metadata field presence check
    node_field_complete = sum(1 for n in nodes
                              if all(f in n for f in ["entity_type","module_membership","evidence_id","version_origin","promotion_status"]))
    edge_field_complete = sum(1 for e in edges
                              if all(f in e for f in ["edge_family","module_membership","evidence_id","version_origin","promotion_status"]))

    print(f"\n--- Phase 1 Metadata Completeness ---")
    print(f"  Nodes with all 5 metadata fields: {node_field_complete}/{len(nodes)}")
    print(f"  Edges with all 5 metadata fields: {edge_field_complete}/{len(edges)}")

    # Build summary dict
    summary = {
        "bundle": reg.get("bundle"),
        "version_origin": reg.get("version_origin"),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "module_count": len(modules),
        "node_type_distribution": dict(node_type_counts),
        "edge_type_distribution": dict(edge_type_counts),
        "edge_family_distribution": dict(edge_family_counts),
        "modules": [
            {
                "module_id": m.get("module_id"),
                "module_name": m.get("module_name"),
                "module_class": m.get("module_class"),
                "maturity_class": m.get("maturity_class"),
                "graph_nodes_count": len(m.get("graph_nodes", [])),
                "graph_edges_count": len(m.get("graph_edges", [])),
            }
            for m in sorted(modules, key=lambda x: x.get("module_id", ""))
        ],
        "phase1_metadata_completeness": {
            "nodes_complete": node_field_complete,
            "nodes_total": len(nodes),
            "edges_complete": edge_field_complete,
            "edges_total": len(edges),
        },
    }

    out_path = REPO_ROOT / "data/registry/registry_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Wrote {out_path}")

    # Final acceptance line
    print(f"\n=== SUMMARY: {len(nodes)} nodes / {len(edges)} edges + {len(modules)} module records ===")

    # Verify acceptance criteria
    ok = True
    if len(nodes) != 212:
        print(f"FAIL: Expected 212 nodes, got {len(nodes)}", file=sys.stderr)
        ok = False
    if len(edges) != 313:
        print(f"FAIL: Expected 313 edges, got {len(edges)}", file=sys.stderr)
        ok = False
    if len(modules) != 8:
        print(f"FAIL: Expected 8 modules, got {len(modules)}", file=sys.stderr)
        ok = False

    if ok:
        print("✓ Acceptance criteria met: 212 nodes / 313 edges / 8 modules")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
