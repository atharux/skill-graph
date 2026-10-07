// Which files or folders are written by more than one skill?
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(st:SkillGraph:Step)-[:WRITES]->(r:SkillGraph:Resource)
WITH r, collect(DISTINCT s.name) AS writers
WHERE size(writers) > 1
RETURN r.path AS resource, writers
ORDER BY resource
