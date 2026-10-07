#!/usr/bin/env python3
"""Validate the compiled procedures and build the graph the loader writes.

The prose instruction files are the source of truth. The YAML is derived from
them, and this script is the gate between the two. It fails when:

  - a file breaks the schema
  - a step consumes a value nothing above it produced (typed I/O must resolve)
  - a step's quote is no longer in the source prose (provenance must hold)
  - a `uses` or `after` points at something that does not exist

On success it writes build/graph.json. Run with --check to also fail when a
source file changed since the last build (the compiled graph is then stale).

  validate.py [--skills DIR] [--sources DIR] [--out FILE] [--check]

  --skills   folder of compiled *.yaml          (default: examples/skills)
  --sources  folder that `source:` paths are relative to   (default: examples)
  --out      where to write the graph           (default: build/graph.json)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "compile" / "procedure.schema.json").read_text())


def line_of(text, quote):
    """1-based line number of the first line containing the quote, or None."""
    for n, line in enumerate(text.splitlines(), 1):
        if quote in line:
            return n
    return None


def main():
    parser = argparse.ArgumentParser(description="Validate compiled procedures and build the graph.")
    parser.add_argument("--skills", type=Path, default=ROOT / "examples" / "skills")
    parser.add_argument("--sources", type=Path, default=ROOT / "examples")
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "graph.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check_drift, build = args.check, args.out
    errors = []
    subs = yaml.safe_load((args.skills / "subprocedures.yaml").read_text())
    sub_ids = {s["id"] for s in subs}
    validator = Draft202012Validator(SCHEMA)

    graph = {"skills": [], "steps": [], "data_edges": [], "order_edges": [],
             "inputs": [], "subprocedures": subs, "touches": [], "notes": []}

    for path in sorted(args.skills.glob("*.yaml")):
        if path.name == "subprocedures.yaml":
            continue
        doc = yaml.safe_load(path.read_text())
        name = doc.get("skill", path.stem)
        schema_errors = [f"{name}: {'/'.join(map(str, e.path))}: {e.message}"
                         for e in validator.iter_errors(doc)]
        if schema_errors:
            errors += schema_errors
            continue
        if name != path.stem:
            errors.append(f"{name}: file is named {path.name}")

        source_path = args.sources / doc["source"]
        if not source_path.exists():
            errors.append(f"{name}: source {doc['source']} does not exist")
            continue
        source = source_path.read_text()
        sha = hashlib.sha256(source.encode()).hexdigest()

        graph["skills"].append({"name": name, "source": doc["source"], "purpose": doc["purpose"],
                                "sha256": sha, "source_lines": len(source.splitlines())})
        for note in doc.get("notes", []):
            graph["notes"].append({"skill": name, "text": note})

        # name -> (producer key, type). Skill inputs are produced by an Input node.
        produced = {}
        for inp in doc["inputs"]:
            key = f"{name}/input:{inp['name']}"
            graph["inputs"].append({"key": key, "skill": name, **inp})
            produced[inp["name"]] = (key, inp["type"])

        seen = set()
        for order, step in enumerate(doc["steps"], 1):
            sid = f"{name}/{step['id']}"
            if step["id"] in seen:
                errors.append(f"{sid}: duplicate step id")
            line = line_of(source, step["quote"])
            if line is None:
                errors.append(f"{sid}: quote not found in {doc['source']}: {step['quote'][:60]!r}")
            if step.get("uses") and step["uses"] not in sub_ids:
                errors.append(f"{sid}: uses unknown sub-procedure {step['uses']!r}")
            for value in step["in"]:
                if value not in produced:
                    errors.append(f"{sid}: consumes {value!r}, which nothing above it produces")
                    continue
                producer, vtype = produced[value]
                graph["data_edges"].append({"from": producer, "to": sid, "name": value, "type": vtype})
            for dep in step.get("after", []):
                if dep not in seen:
                    errors.append(f"{sid}: after {dep!r}, which is not an earlier step")
                else:
                    graph["order_edges"].append({"from": f"{name}/{dep}", "to": sid})
            for out in step["out"]:
                if out["name"] in produced:
                    errors.append(f"{sid}: output {out['name']!r} is already produced above")
                produced[out["name"]] = (sid, out["type"])
            for touch in step.get("touches", []):
                graph["touches"].append({"step": sid, **touch})
            seen.add(step["id"])
            graph["steps"].append({
                "key": sid, "skill": name, "id": step["id"], "order": order,
                "kind": step["kind"], "does": step["does"], "tool": step["tool"],
                "effect": step["effect"], "conditional": bool(step.get("conditional", False)),
                "destructive": bool(step.get("destructive", False)),
                "uses": step.get("uses"), "quote": step["quote"], "line": line,
                "outputs": [f"{o['name']}: {o['type']}" for o in step["out"]],
            })

    if check_drift and build.exists():
        old = {s["name"]: s["sha256"] for s in json.loads(build.read_text())["skills"]}
        for s in graph["skills"]:
            if s["name"] in old and old[s["name"]] != s["sha256"]:
                errors.append(f"{s['name']}: {s['source']} changed since the last build; recompile it")

    if errors:
        print(f"FAIL  {len(errors)} error(s)")
        for e in errors:
            print("  " + e)
        sys.exit(1)

    build.parent.mkdir(parents=True, exist_ok=True)
    build.write_text(json.dumps(graph, indent=1, ensure_ascii=False) + "\n")
    print(f"OK    {len(graph['skills'])} skills, {len(graph['steps'])} steps, "
          f"{len(graph['data_edges'])} typed edges, {len(graph['order_edges'])} order edges, "
          f"{len(graph['notes'])} compile notes -> {build}")


if __name__ == "__main__":
    main()
