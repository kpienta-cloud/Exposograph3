#!/usr/bin/env python3
"""
Phase 2 helper: compute conformance notes for all 8 modules and build wiring.json.
Writes _conformance_notes into each module JSON, then writes data/ontology/wiring.json.
"""

import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent
MODULES_DIR = REPO_ROOT / "data/modules"
ONTOLOGY_DIR = REPO_ROOT / "data/ontology"


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    # Load ontology artefacts
    classes = load_json(ONTOLOGY_DIR / "classes.json")
    interfaces = load_json(ONTOLOGY_DIR / "interfaces.json")
    port_types = load_json(ONTOLOGY_DIR / "port_types.json")

    entity_class_ids = {c["class_id"] for c in classes["entity_classes"]}
    module_class_ids = {c["class_id"] for c in classes["module_classes"]}
    interface_map = {i["interface_id"]: i for i in interfaces["interfaces"]}
    port_type_ids = {pt["type_id"] for pt in port_types["port_types"]}

    # Phase 3 required fields (from validate.py)
    MODULE_PHASE3_REQUIRED = [
        "module_id", "module_name", "module_class", "maturity_class", "extends", "scope",
        "version", "evidence_bundle", "input_ports", "output_ports", "parameters",
        "equation_type", "update_rule", "uncertainty", "validation_status", "cedt_mapping",
        "causal_role_map", "graph_nodes", "graph_edges", "causal_edges", "internal_state",
        "promotion_status"
    ]

    # ── Conformance checking ───────────────────────────────────────────────────
    conformance_results = {}

    for mf in sorted(MODULES_DIR.glob("*.json")):
        data = load_json(mf)
        module_id = data.get("module_id", "")
        notes = []
        gaps = []

        # 1. module_class resolves
        mc = data.get("module_class")
        if mc not in module_class_ids:
            gaps.append(f"module_class '{mc}' not in defined module_classes")

        # 2. every extends resolves to an interface
        for ext in data.get("extends", []):
            if ext not in interface_map:
                gaps.append(f"extends '{ext}' not in defined interfaces")

        # 3. check required fields for each interface
        for ext in data.get("extends", []):
            if ext not in interface_map:
                continue
            iface = interface_map[ext]
            for req in iface.get("required_fields", []):
                val = data.get(req)
                if val is None or val == [] or val == "":
                    gaps.append(f"Interface {ext} requires field '{req}' — missing or empty")
                else:
                    pass  # present and non-empty

        # 4. every port dtype is in port_types
        for port in data.get("input_ports", []) + data.get("output_ports", []):
            dtype = port.get("dtype")
            if dtype is None:
                gaps.append(f"Port '{port.get('name')}' missing dtype annotation")
            elif dtype not in port_type_ids:
                gaps.append(f"Port '{port.get('name')}' dtype '{dtype}' not in port_types.json")

        # 5. maturity floor check for ExecutableModule
        if "ExecutableModule" in data.get("extends", []):
            mat = data.get("maturity_class", "")
            if mat not in {"E", "T"}:
                gaps.append(f"ExecutableModule requires maturity_class E or T, got '{mat}'")

        # 6. Interface port-type contracts satisfaction
        for ext in data.get("extends", []):
            if ext not in interface_map:
                continue
            iface = interface_map[ext]
            module_dtypes = set()
            for port in data.get("input_ports", []) + data.get("output_ports", []):
                if port.get("dtype"):
                    module_dtypes.add(port["dtype"])

            for req_port in iface.get("required_input_port_types", []):
                req_dtype = req_port.get("dtype")
                if req_dtype is None:
                    continue  # nullable (ExecutableModule typed_input check)
                if req_port.get("required", True) and req_dtype not in module_dtypes:
                    gaps.append(
                        f"Interface {ext} requires input dtype '{req_dtype}' — not found in module ports"
                    )

            for req_port in iface.get("required_output_port_types", []):
                req_dtype = req_port.get("dtype")
                if req_dtype is None:
                    continue
                if req_port.get("required", True) and req_dtype not in module_dtypes:
                    gaps.append(
                        f"Interface {ext} requires output dtype '{req_dtype}' — not found in module ports"
                    )

        # Determine conformant
        conformant = len(gaps) == 0

        if conformant:
            notes.append("CONFORMANT: all interface required_fields present; all port dtypes resolve; all interface port-type contracts satisfied.")
        else:
            notes.append("GAPS RECORDED (not fabricated):")
            notes.extend(f"  - {g}" for g in gaps)

        conformance_results[module_id] = {
            "conformant": conformant,
            "gaps": gaps
        }

        # Write _conformance_notes back into module
        data["_conformance_notes"] = {
            "phase": "Phase 2",
            "conformant": conformant,
            "notes": notes,
            "gaps": gaps
        }

        mf.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        status = "✓ CONFORMANT" if conformant else f"✗ {len(gaps)} gap(s)"
        print(f"  {module_id}: {status}")
        for g in gaps:
            print(f"    GAP: {g}")

    # ── Build wiring.json ──────────────────────────────────────────────────────
    # For every output port, find consumer input ports with matching dtype
    print("\nBuilding wiring.json...")

    # Load all modules and collect ports
    all_modules = {}
    for mf in sorted(MODULES_DIR.glob("*.json")):
        data = load_json(mf)
        all_modules[data["module_id"]] = data

    # Index: dtype -> list of (module_id, port_name, direction)
    dtype_to_outputs = defaultdict(list)  # dtype -> [(module_id, port_name)]
    dtype_to_inputs = defaultdict(list)   # dtype -> [(module_id, port_name)]

    for mod_id, mod in all_modules.items():
        for port in mod.get("output_ports", []):
            dtype = port.get("dtype")
            if dtype:
                dtype_to_outputs[dtype].append((mod_id, port["name"]))
        for port in mod.get("input_ports", []):
            dtype = port.get("dtype")
            if dtype:
                dtype_to_inputs[dtype].append((mod_id, port["name"]))

    # Build wiring connections: output → inputs with same dtype, cross-module only
    wiring_connections = []
    for dtype, producers in dtype_to_outputs.items():
        consumers = dtype_to_inputs.get(dtype, [])
        for from_module, from_port in producers:
            for to_module, to_port in consumers:
                if from_module != to_module:  # cross-module only
                    wiring_connections.append({
                        "from_module": from_module,
                        "from_port": from_port,
                        "to_module": to_module,
                        "to_port": to_port,
                        "dtype": dtype,
                        "compatible": True
                    })

    # Sort for determinism
    wiring_connections.sort(key=lambda x: (x["from_module"], x["from_port"], x["to_module"]))

    wiring = {
        "schema_version": "3.0.0",
        "description": "ExposoGraph 3.0 type-checked producer→consumer wiring map (Layer 0 Phase 2). Lists all cross-module port connections where the output and input dtypes match.",
        "connection_count": len(wiring_connections),
        "connections": wiring_connections
    }

    wiring_path = ONTOLOGY_DIR / "wiring.json"
    wiring_path.write_text(json.dumps(wiring, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Wrote wiring.json: {len(wiring_connections)} type-compatible cross-module connections")

    # Summary
    conformant_count = sum(1 for r in conformance_results.values() if r["conformant"])
    total = len(conformance_results)
    print(f"\n=== CONFORMANCE SUMMARY: {conformant_count}/{total} modules conformant ===")

    return conformance_results, len(wiring_connections)


if __name__ == "__main__":
    main()
