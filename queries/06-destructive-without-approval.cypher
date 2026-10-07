// Which steps delete something with no human approval before them?
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(d:SkillGraph:Step {destructive: true})
WHERE NOT EXISTS {
  MATCH (a:SkillGraph:Step {kind: "approval", conditional: false})-[:INPUTS_TO|THEN*]->(d)
}
RETURN s.name AS skill, d.id AS step, d.does AS does
ORDER BY skill
