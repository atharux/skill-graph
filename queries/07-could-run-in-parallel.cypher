// Which steps in a skill do not consume each other's output, so could run at the same time?
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(a:SkillGraph:Step),
      (s)-[:HAS_STEP]->(b:SkillGraph:Step)
WHERE a.order < b.order
  AND a.kind <> "report" AND b.kind <> "report"
  AND NOT EXISTS { MATCH (a)-[:INPUTS_TO|THEN*]->(b) }
RETURN s.name AS skill, a.id AS step, b.id AS independent_of
ORDER BY skill, a.order, b.order
