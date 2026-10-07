Run the eval gate for: $ARGUMENTS

Evals score the model's judgement with real calls against labelled fixtures. Tests only
prove plumbing. Standing rules: CLAUDE.md → DEV LIFECYCLE → Eval gate.

## Steps

1. Resolve the repo from $ARGUMENTS (a shortname, `owner/repo`, or a PR number in the
   current repo). For a PR, verify in a worktree and never in his working tree:
   `git worktree add /tmp/<slug> <branch>`, then symlink `node_modules` only if
   `package.json` is unchanged vs base.

2. If there's no `evals/` folder, report "No eval coverage in <repo>" and stop. Offer to
   open an issue that creates one. Do not improvise a one-off eval.

3. Read `evals/README.md`, then run `npm run eval`. Run it on the production model first.
   Use a substitute (`EVAL_GROQ_MODEL`) only if production can't be reached, and label the
   scorecard with the substitute model.

4. Report:
   - each scorecard from `evals/results/*.md`, verbatim
   - PASS / FAIL against the baseline, and any metric that regressed
   - every failed case with its reason
   - a zero-parse run as **BROKEN PIPE**, not as a score. Name the cause if the logs show it.

5. For a PR, paste the scorecards into the PR body's Evals section with `gh pr edit`.

## Never
- Lower a baseline (`EVAL_UPDATE_BASELINE=1`) unless I've said so for this PR.
- Relabel a fixture case so the model passes. A disputed label is my decision.
- Describe a substitute-model score as the production score.
