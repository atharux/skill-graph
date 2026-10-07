// Which skills share a sub-procedure? Each row is one rule written out in several places.
MATCH (p:SkillGraph:Procedure)<-[:USES]-(:SkillGraph:Step)<-[:HAS_STEP]-(s:SkillGraph:Command)
WITH p, collect(DISTINCT s.name) AS skills
WHERE size(skills) > 1
RETURN p.id AS subprocedure, size(skills) AS used_by, skills, p.does AS rule
ORDER BY used_by DESC, subprocedure
