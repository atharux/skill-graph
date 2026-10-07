// Which skills run git or gh steps but never fetch first?
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(st:SkillGraph:Step)
WHERE st.tool IN ["git", "gh"]
WITH s, collect(st.id) AS repo_steps
WHERE NOT EXISTS {
  MATCH (s)-[:HAS_STEP]->(:SkillGraph:Step)-[:USES]->(:SkillGraph:Procedure {id: "fetch-before-read"})
}
RETURN s.name AS skill, repo_steps
ORDER BY skill
