#!/usr/bin/env python3
"""
ExposoGraph 3.0 — Build Registry Summary (Phase 4)
Reads registry + causal layer data and writes data/registry/registry_summary.json.
Prints summary table with node/edge counts, execution edge counts,
per-module Phase 3/4 field completeness, causal layer counts,
promoted-vs-retained breakdown, and per-module causal_edge counts.
"""

import json
import sys
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).parent.parent

# Phase 3 required module fields (22 total)
MODULE_PHASE3_REQUIRED = [
    "module_id", "module_name", "module_class", "maturity_class", "extends", "scope",
    "version", "evidence_bundle", "input_ports", "output_ports", "parameters",
    "equation_type", "update_rule", "uncertainty", "validation_status", "cedt_mapping",
    "causal_role_map", "graph_nodes", "graph_edges", "causal_edges", "internal_state",
    "promotion_status"
]


def main():
    print("=== ExposoGraph 3.0 — Registry Summary Builder (Phase 4) ===\n")

    # ─── Load registry graph ───────────────────────────────────────────────────
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
    print(f"Edges:   {len(edges)} (baseline registry edges — immutable)")

    # ─── Node type distribution ────────────────────────────────────────────────
    node_type_counts = Counter(n.get("entity_type", n.get("type", "unknown")) for n in nodes)
    print("\n--- Node Types ---")
    for ntype, cnt in sorted(node_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ntype:20s}: {cnt}")

    # ─── Baseline edge type distribution ──────────────────────────────────────
    edge_type_counts = Counter(e.get("type", "unknown") for e in edges)
    print("\n--- Baseline Edge Types (original predicates) ---")
    for etype, cnt in sorted(edge_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {etype:30s}: {cnt}")

    # ─── Baseline edge family distribution ────────────────────────────────────
    edge_family_counts = Counter(e.get("edge_family", "unknown") for e in edges)
    print("\n--- Baseline Edge Family Distribution ---")
    for fam, cnt in sorted(edge_family_counts.items(), key=lambda x: -x[1]):
        print(f"  {fam:20s}: {cnt}")

    # ─── Execution edges (Phase 3) ────────────────────────────────────────────
    exec_edges_path = REPO_ROOT / "data/registry/execution_edges.json"
    exec_edges = []
    exec_edge_counts_by_type = {}
    exec_edge_counts_by_family = {}
    if exec_edges_path.exists():
        ee_data = json.loads(exec_edges_path.read_text(encoding="utf-8"))
        exec_edges = ee_data.get("edges", [])
        exec_edge_counts_by_type = dict(Counter(e.get("type", "unknown") for e in exec_edges))
        exec_edge_counts_by_family = dict(Counter(e.get("edge_family", "unknown") for e in exec_edges))

        print(f"\n--- Execution Edges (Phase 3 — data/registry/execution_edges.json) ---")
        print(f"  Total execution edges: {len(exec_edges)}")
        print(f"  version_origin:        {ee_data.get('version_origin', '?')}")
        print(f"\n  By type:")
        for etype, cnt in sorted(exec_edge_counts_by_type.items(), key=lambda x: -x[1]):
            print(f"    {etype:30s}: {cnt}")
        print(f"\n  By edge_family:")
        for fam, cnt in sorted(exec_edge_counts_by_family.items(), key=lambda x: -x[1]):
            print(f"    {fam:20s}: {cnt}")

        causal_edges_exec = [e for e in exec_edges if e.get("edge_family") == "causal"]
        bioactivates = [e for e in causal_edges_exec if e.get("type") == "bioactivates"]
        detoxifies_e = [e for e in causal_edges_exec if e.get("type") == "detoxifies"]
        competes = [e for e in causal_edges_exec if e.get("type") == "competes_at"]
        mod_edges = [e for e in exec_edges if e.get("edge_family") == "execution"]
        print(f"\n  Breakdown:")
        print(f"    bioactivates (enzyme→substrate):  {len(bioactivates)}")
        print(f"    detoxifies (enzyme→substrate):    {len(detoxifies_e)}")
        print(f"    competes_at (inhibition):         {len(competes)}")
        print(f"    module-to-module execution:       {len(mod_edges)}")
    else:
        print("\n  WARNING: execution_edges.json not found", file=sys.stderr)

    # ─── Causal layer (Phase 4 new) ────────────────────────────────────────────
    causal_edges_path = REPO_ROOT / "data/causal/causal_edges.json"
    causal_edges_list = []
    causal_layer_summary = {}
    motif_coverage = {}
    if causal_edges_path.exists():
        ce_data = json.loads(causal_edges_path.read_text(encoding="utf-8"))
        causal_edges_list = ce_data.get("causal_edges", [])
        promoted_count = ce_data.get("promoted_count", len(causal_edges_list))
        retained_count = ce_data.get("retained_in_registry_count", 0)

        # Counts by causal_relation
        by_relation = dict(Counter(ce.get("causal_relation","?") for ce in causal_edges_list))
        # Counts by source_predicate
        by_predicate = dict(Counter(ce.get("source_predicate","?") for ce in causal_edges_list))
        # Counts by origin_layer
        by_origin = dict(Counter(ce.get("origin_layer","?") for ce in causal_edges_list))
        # Motif coverage: how many edges use each motif
        by_motif = dict(Counter(ce.get("motif_id","?") for ce in causal_edges_list))
        # PMIDs attached
        all_pmids = []
        for ce in causal_edges_list:
            ev = ce.get("evidence", {})
            all_pmids.extend(ev.get("pmid_refs", []))
        all_pmids = list(set(all_pmids))

        print(f"\n--- Causal Layer (Phase 4 — data/causal/causal_edges.json) ---")
        print(f"  Promoted causal edges:         {promoted_count}")
        print(f"  Retained in registry:          {retained_count}")
        print(f"  Total directional accounted:   {promoted_count + retained_count}")
        print(f"  Promotion rule: {ce_data.get('promotion_rule','N/A')[:80]}...")

        print(f"\n  By causal_relation:")
        for rel, cnt in sorted(by_relation.items(), key=lambda x: -x[1]):
            print(f"    {rel:15s}: {cnt}")

        print(f"\n  By source_predicate:")
        for pred, cnt in sorted(by_predicate.items(), key=lambda x: -x[1]):
            print(f"    {pred:20s}: {cnt}")

        print(f"\n  By origin_layer:")
        for orig, cnt in sorted(by_origin.items(), key=lambda x: -x[1]):
            print(f"    {orig:25s}: {cnt}")

        print(f"\n  By motif_id (motif coverage):")
        for motif, cnt in sorted(by_motif.items(), key=lambda x: -x[1]):
            print(f"    {motif}: {cnt} edges")

        print(f"\n  PMIDs attached to promoted edges ({len(all_pmids)} unique): {all_pmids[:10]}{'...' if len(all_pmids) > 10 else ''}")

        causal_layer_summary = {
            "promoted_causal_edges": promoted_count,
            "retained_in_registry": retained_count,
            "total_directional_accounted": promoted_count + retained_count,
            "by_causal_relation": by_relation,
            "by_source_predicate": by_predicate,
            "by_origin_layer": by_origin,
            "motif_coverage": by_motif,
            "pmids_attached": all_pmids
        }
    else:
        print("\n  WARNING: data/causal/causal_edges.json not found (Phase 4 incomplete)", file=sys.stderr)

    # ─── Causal motif library ──────────────────────────────────────────────────
    motifs_path = REPO_ROOT / "data/causal/motifs.json"
    motifs_summary = []
    if motifs_path.exists():
        motifs_data = json.loads(motifs_path.read_text(encoding="utf-8"))
        motif_list = motifs_data.get("motifs", [])
        print(f"\n--- Causal Motif Library (Phase 4) ---")
        print(f"  Total motifs: {len(motif_list)}")
        for m in motif_list:
            n_edges_using = causal_layer_summary.get("motif_coverage", {}).get(m["motif_id"], 0)
            print(f"  [{m.get('status','?')}] {m['motif_id']}: {m['name']} ({m.get('causal_relation','?')}) — {n_edges_using} edges")
            motifs_summary.append({
                "motif_id": m["motif_id"],
                "name": m["name"],
                "causal_relation": m.get("causal_relation"),
                "status": m.get("status"),
                "edges_using_motif": n_edges_using
            })

    # ─── Module records ────────────────────────────────────────────────────────
    modules_dir = REPO_ROOT / "data/modules"
    module_files = sorted(modules_dir.glob("*.json"))
    modules = []
    for mf in module_files:
        try:
            m = json.loads(mf.read_text(encoding="utf-8"))
            modules.append(m)
        except Exception as e:
            print(f"WARNING: Could not load {mf.name}: {e}", file=sys.stderr)

    print(f"\n--- Module Records ({len(modules)}) — Phase 4 (with causal_edge counts) ---")
    module_summary_rows = []
    total_params = 0
    for m in sorted(modules, key=lambda x: x.get("module_id", "")):
        mod_id = m.get("module_id", "?")
        mc = m.get("maturity_class", "?")
        eq = m.get("equation_type", "?")
        promo = m.get("promotion_status", "?")
        n_in = len(m.get("input_ports", []))
        n_out = len(m.get("output_ports", []))
        n_params = len(m.get("parameters", []))
        n_nodes = len(m.get("graph_nodes", []))
        n_edges = len(m.get("graph_edges", []))
        n_causal = len(m.get("causal_edges", []))
        val_status = m.get("validation_status", "?")

        populated = [f for f in MODULE_PHASE3_REQUIRED if f in m]
        completeness_pct = round(len(populated) / len(MODULE_PHASE3_REQUIRED) * 100, 1)
        total_params += n_params

        print(f"  [{mc}] {mod_id}")
        print(f"       params={n_params:3d}  ports={n_in}in/{n_out}out  "
              f"graph={n_nodes}nodes/{n_edges}edges  causal={n_causal}  eq={eq}")
        print(f"       val={val_status}  promotion={promo}  completeness={completeness_pct}%")

        module_summary_rows.append({
            "module_id": mod_id,
            "module_name": m.get("module_name"),
            "module_class": m.get("module_class"),
            "maturity_class": mc,
            "equation_type": eq,
            "promotion_status": promo,
            "validation_status": val_status,
            "input_ports_count": n_in,
            "output_ports_count": n_out,
            "parameters_count": n_params,
            "graph_nodes_count": n_nodes,
            "graph_edges_count": n_edges,
            "causal_edges_count": n_causal,
            "phase3_fields_populated": len(populated),
            "phase3_fields_total": len(MODULE_PHASE3_REQUIRED),
            "phase3_completeness_pct": completeness_pct,
        })

    print(f"\n  Total parameters across all modules: {total_params}")

    # ─── Phase 1 metadata field completeness ──────────────────────────────────
    node_field_complete = sum(1 for n in nodes
                              if all(f in n for f in ["entity_type", "module_membership",
                                                       "evidence_id", "version_origin",
                                                       "promotion_status"]))
    edge_field_complete = sum(1 for e in edges
                              if all(f in e for f in ["edge_family", "module_membership",
                                                       "evidence_id", "version_origin",
                                                       "promotion_status"]))

    print(f"\n--- Phase 1 Metadata Completeness (Baseline) ---")
    print(f"  Nodes with all 5 metadata fields: {node_field_complete}/{len(nodes)}")
    print(f"  Edges with all 5 metadata fields: {edge_field_complete}/{len(edges)}")

    # ─── Build and write summary dict ─────────────────────────────────────────
    # ─── Layer-0 stats (Phase 2) ──────────────────────────────────────────────
    layer0_stats = {"entity_class_count": 0, "interface_count": 0, "port_type_count": 0,
                    "modules_conformant": 0, "modules_total": 8, "wiring_connection_count": 0}
    try:
        _classes_doc = json.loads((REPO_ROOT / "data/ontology/classes.json").read_text(encoding="utf-8"))
        _ifaces_doc  = json.loads((REPO_ROOT / "data/ontology/interfaces.json").read_text(encoding="utf-8"))
        _pt_doc      = json.loads((REPO_ROOT / "data/ontology/port_types.json").read_text(encoding="utf-8"))
        _wiring_doc  = json.loads((REPO_ROOT / "data/ontology/wiring.json").read_text(encoding="utf-8"))
        _ec_count = len(_classes_doc.get("entity_classes", []))
        _ifc_count = len(_ifaces_doc.get("interfaces", []))
        _pt_count = len(_pt_doc.get("port_types", []))
        _wiring_count = _wiring_doc.get("connection_count", len(_wiring_doc.get("connections", [])))
        _pt_ids = {pt["type_id"] for pt in _pt_doc.get("port_types", [])}
        _iface_map = {i["interface_id"]: i for i in _ifaces_doc.get("interfaces", [])}
        _mc_ids = {c["class_id"] for c in _classes_doc.get("module_classes", [])}
        _iface_ids = {i["interface_id"] for i in _ifaces_doc.get("interfaces", [])}
        _conformant = 0
        for _m in modules:
            _ok = True
            if _m.get("module_class") not in _mc_ids:
                _ok = False
            for _ext in _m.get("extends", []):
                if _ext not in _iface_ids:
                    _ok = False; break
                _ifc = _iface_map[_ext]
                for _rf in _ifc.get("required_fields", []):
                    if _m.get(_rf) is None or _m.get(_rf) == [] or _m.get(_rf) == "":
                        _ok = False; break
            for _port in _m.get("input_ports", []) + _m.get("output_ports", []):
                if not _port.get("dtype") or _port["dtype"] not in _pt_ids:
                    _ok = False; break
            if _ok:
                _conformant += 1
        layer0_stats = {
            "entity_class_count": _ec_count,
            "interface_count": _ifc_count,
            "port_type_count": _pt_count,
            "modules_conformant": _conformant,
            "modules_total": len(modules),
            "wiring_connection_count": _wiring_count
        }
        print(f"\n--- Layer-0 Stats (Phase 2) ---")
        print(f"  Entity classes:         {_ec_count}")
        print(f"  Interfaces defined:     {_ifc_count}")
        print(f"  Port types defined:     {_pt_count}")
        print(f"  Modules conformant:     {_conformant}/{len(modules)}")
        print(f"  Wiring connections:     {_wiring_count}")
    except Exception as _e:
        print(f"  WARNING: Could not compute Layer-0 stats: {_e}", file=sys.stderr)

    summary = {
        "bundle": reg.get("bundle"),
        "version_origin": reg.get("version_origin"),
        "phase": "Phase 2+4: Ontology + Causal layer promotion",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "execution_edge_count": len(exec_edges),
        "module_count": len(modules),
        "total_module_parameters": total_params,
        "node_type_distribution": dict(node_type_counts),
        "edge_type_distribution": dict(edge_type_counts),
        "edge_family_distribution": dict(edge_family_counts),
        "execution_edges": {
            "total": len(exec_edges),
            "by_type": exec_edge_counts_by_type,
            "by_family": exec_edge_counts_by_family,
        },
        "causal_layer": causal_layer_summary,
        "causal_motifs": {
            "total": len(motifs_summary),
            "motifs": motifs_summary
        },
        "modules": module_summary_rows,
        "phase1_metadata_completeness": {
            "nodes_complete": node_field_complete,
            "nodes_total": len(nodes),
            "edges_complete": edge_field_complete,
            "edges_total": len(edges),
        },
        "layer0_ontology": layer0_stats,
    }

    out_path = REPO_ROOT / "data/registry/registry_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Wrote {out_path}")

    # ─── Final acceptance line ─────────────────────────────────────────────────
    promoted = causal_layer_summary.get("promoted_causal_edges", 0)
    print(f"\n=== SUMMARY: {len(nodes)} nodes / {len(edges)} baseline edges "
          f"+ {len(exec_edges)} execution edges + {len(modules)} modules "
          f"+ {promoted} promoted causal edges ===")

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
    if len(exec_edges) == 0:
        print("FAIL: No execution edges found", file=sys.stderr)
        ok = False
    if promoted == 0:
        print("FAIL: No promoted causal edges found (Phase 4 requirement)", file=sys.stderr)
        ok = False

    if ok:
        print(f"✓ Acceptance criteria met: 212 nodes / 313 edges / "
              f"{len(exec_edges)} execution edges / 8 modules / {promoted} causal edges")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
