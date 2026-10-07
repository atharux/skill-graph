// Where does a model judgment feed a remote write directly, with nothing in between?
MATCH (s:SkillGraph:Command)-[:HAS_STEP]->(j:SkillGraph:Step {kind: "judgment"})
      -[e:INPUTS_TO]->(w:SkillGraph:Step {effect: "remote"})
RETURN s.name AS skill, j.id AS judgment, e.name AS value, w.id AS remote_step
ORDER BY skill, remote_step
