#!/usr/bin/env python3
"""Load the compiled graph into Neo4j, run the governance queries, export for the viewer.

  graphdb.py load     rebuild the :SkillGraph namespace from build/graph.json
  graphdb.py query    run every queries/*.cypher and print the rows
  graphdb.py export   read the graph and the query results back out of Neo4j
                      into docs/data.js

Optional: --graph FILE (default build/graph.json) for load, --out FILE
(default docs/data.js) for export.

Talks to the Neo4j HTTP Query API, so it needs no driver and works the same
against a local instance and Aura. Connection comes from the environment:

  SKILLGRAPH_NEO4J_URL       default http://127.0.0.1:17474
  SKILLGRAPH_NEO4J_USER      default neo4j
  SKILLGRAPH_NEO4J_PASSWORD  required
  SKILLGRAPH_NEO4J_DATABASE  default neo4j

Every node carries the :SkillGraph label and `load` deletes and rewrites only
nodes with that label, so it is safe beside other graphs in the same database.
`load` refuses a non-local URL unless --allow-remote is passed.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def option(flag, default):
    """Value following `flag` on the command line, or the default."""
    return Path(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default
URL = os.environ.get("SKILLGRAPH_NEO4J_URL", "http://127.0.0.1:17474").rstrip("/")
USER = os.environ.get("SKILLGRAPH_NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("SKILLGRAPH_NEO4J_PASSWORD")
DATABASE = os.environ.get("SKILLGRAPH_NEO4J_DATABASE", "neo4j")


def run(statement, parameters=None):
    """Run one Cypher statement. Returns a list of row dicts."""
    body = json.dumps({"statement": statement, "parameters": parameters or {}}).encode()
    auth = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
    req = urllib.request.Request(
        f"{URL}/db/{DATABASE}/query/v2", data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "Authorization": f"Basic {auth}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"Neo4j rejected the statement ({e.code}): {e.read().decode()[:600]}")
    except urllib.error.URLError as e:
        sys.exit(f"Cannot reach Neo4j at {URL}: {e.reason}")
    data = payload["data"]
    return [dict(zip(data["fields"], row)) for row in data["values"]]


LOAD = [
    "MATCH (n:SkillGraph) DETACH DELETE n",
    """UNWIND $skills AS s
       CREATE (:SkillGraph:Command {name: s.name, source: s.source, purpose: s.purpose,
                                  sha256: s.sha256, source_lines: s.source_lines})""",
    """UNWIND $subprocedures AS p
       CREATE (:SkillGraph:Procedure {id: p.id, does: p.does})""",
    """UNWIND $inputs AS i
       MATCH (s:SkillGraph:Command {name: i.skill})
       CREATE (s)-[:DECLARES_INPUT]->(:SkillGraph:Input {key: i.key, name: i.name, type: i.type})""",
    """UNWIND $steps AS st
       MATCH (s:SkillGraph:Command {name: st.skill})
       CREATE (s)-[:HAS_STEP]->(n:SkillGraph:Step {key: st.key, id: st.id, order: st.order,
              kind: st.kind, does: st.does, tool: st.tool, effect: st.effect,
              conditional: st.conditional, destructive: st.destructive,
              quote: st.quote, line: st.line, outputs: st.outputs})
       WITH n, st WHERE st.uses IS NOT NULL
       MATCH (p:SkillGraph:Procedure {id: st.uses})
       CREATE (n)-[:USES]->(p)""",
    """UNWIND $data_edges AS e
       MATCH (a:SkillGraph {key: e.from}), (b:SkillGraph:Step {key: e.to})
       CREATE (a)-[:INPUTS_TO {name: e.name, type: e.type}]->(b)""",
    """UNWIND $order_edges AS e
       MATCH (a:SkillGraph:Step {key: e.from}), (b:SkillGraph:Step {key: e.to})
       CREATE (a)-[:THEN]->(b)""",
    """UNWIND $touches AS t
       MATCH (st:SkillGraph:Step {key: t.step})
       MERGE (r:SkillGraph:Resource {path: t.path})
       FOREACH (_ IN CASE WHEN t.mode = 'write' THEN [1] ELSE [] END | MERGE (st)-[:WRITES]->(r))
       FOREACH (_ IN CASE WHEN t.mode = 'read' THEN [1] ELSE [] END | MERGE (st)-[:READS]->(r))""",
    """UNWIND $notes AS n
       MATCH (s:SkillGraph:Command {name: n.skill})
       CREATE (s)-[:HAS_NOTE]->(:SkillGraph:Note {text: n.text})""",
]


def load():
    host = urlparse(URL).hostname
    if host not in ("127.0.0.1", "localhost", "::1") and "--allow-remote" not in sys.argv:
        sys.exit(f"Refusing to write to {host}. Pass --allow-remote to load a non-local database.")
    graph = json.loads(option("--graph", ROOT / "build" / "graph.json").read_text())
    for statement in LOAD:
        run(statement, graph)
    counts = run("MATCH (n:SkillGraph) UNWIND labels(n) AS l WITH l WHERE l <> 'SkillGraph' "
                 "RETURN l AS label, count(*) AS n ORDER BY label")
    rels = run("MATCH (:SkillGraph)-[r]->(:SkillGraph) RETURN type(r) AS type, count(*) AS n ORDER BY type")
    print(f"Loaded into {URL} ({DATABASE})")
    print("  nodes: " + ", ".join(f"{c['label']} {c['n']}" for c in counts))
    print("  rels:  " + ", ".join(f"{r['type']} {r['n']}" for r in rels))


def read_queries():
    out = []
    for path in sorted((ROOT / "queries").glob("*.cypher")):
        text = path.read_text().strip()
        lines = text.splitlines()
        question = " ".join(l[2:].strip() for l in lines if l.startswith("//"))
        cypher = "\n".join(l for l in lines if not l.startswith("//"))
        out.append({"id": path.stem, "question": question, "cypher": cypher})
    return out


def query():
    for q in read_queries():
        rows = run(q["cypher"])
        print(f"\n{q['id']}  ({len(rows)} rows)\n  {q['question']}")
        for row in rows:
            print("  - " + " | ".join(f"{k}={v}" for k, v in row.items()))


def export():
    queries = read_queries()
    for q in queries:
        q["rows"] = run(q["cypher"])
    data = {
        "source": {"url": URL, "database": DATABASE},
        "skills": run("""MATCH (s:SkillGraph:Command)
                         OPTIONAL MATCH (s)-[:HAS_NOTE]->(n:SkillGraph:Note)
                         WITH s, collect(n.text) AS notes
                         RETURN s.name AS name, s.source AS source, s.purpose AS purpose,
                                s.sha256 AS sha256, notes ORDER BY name"""),
        "steps": run("""MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(st:SkillGraph:Step)
                        OPTIONAL MATCH (st)-[:USES]->(p:SkillGraph:Procedure)
                        RETURN s.name AS skill, st.key AS key, st.id AS id, st.order AS order,
                               st.kind AS kind, st.does AS does, st.tool AS tool, st.effect AS effect,
                               st.conditional AS conditional, st.destructive AS destructive,
                               st.quote AS quote, st.line AS line, st.outputs AS outputs,
                               p.id AS uses ORDER BY skill, order"""),
        "inputs": run("""MATCH (s:SkillGraph:Command)-[:DECLARES_INPUT]->(i:SkillGraph:Input)
                         RETURN s.name AS skill, i.key AS key, i.name AS name, i.type AS type"""),
        "edges": run("""MATCH (a:SkillGraph)-[e:INPUTS_TO|THEN]->(b:SkillGraph:Step)
                        RETURN a.key AS source, b.key AS target, type(e) AS rel,
                               e.name AS name, e.type AS type"""),
        "queries": queries,
    }
    out = option("--out", ROOT / "docs" / "data.js")
    out.write_text("// Generated by compile/graphdb.py export. Read back out of Neo4j; do not edit.\n"
                   "window.SKILLGRAPH = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n")
    print(f"Exported {len(data['skills'])} skills, {len(data['steps'])} steps, "
          f"{len(data['edges'])} edges, {len(queries)} query results -> {out}")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command not in ("load", "query", "export"):
        sys.exit(__doc__)
    if not PASSWORD:
        sys.exit("Set SKILLGRAPH_NEO4J_PASSWORD.")
    {"load": load, "query": query, "export": export}[command]()
