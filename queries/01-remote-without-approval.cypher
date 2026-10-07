// Which steps change something outside this machine with no human approval before them?
// A conditional "ask if unclear" does not count as approval.
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(w:SkillGraph:Step {effect: "remote"})
WHERE NOT EXISTS {
  MATCH (a:SkillGraph:Step {kind: "approval", conditional: false})-[:INPUTS_TO|THEN*]->(w)
}
OPTIONAL MATCH (g:SkillGraph:Step {kind: "gate"})-[:INPUTS_TO|THEN*]->(w)
WITH s, w, collect(DISTINCT g.id) AS gates_before
RETURN s.name AS skill, w.id AS step, w.does AS does, gates_before
ORDER BY size(gates_before), skill, w.order
