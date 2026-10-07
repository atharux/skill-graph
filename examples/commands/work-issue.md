Work on GitHub issue: $ARGUMENTS

## Step 0: Detect the target repo

Run this and capture the result:
```
gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null
```

If that returns a valid `owner/repo`, use it for all subsequent `gh` calls.

If $ARGUMENTS begins with a string matching `owner/repo` or a known repo shortname (e.g. `web-app`, `api`, `docs`), resolve it to `your-org/<name>`.

If still unclear, ask: "Which repo? (e.g. your-org/web-app)"

Store the result as REPO. The issue number is the remaining part of $ARGUMENTS.

## Steps

1. Read the issue:
   ```
   gh issue view <issue-number> --repo $REPO
   ```

2. Understand scope from the acceptance criteria. If anything is unclear, ask ONE question before touching code.

3. Find the local directory for this repo:
   ```
   git -C <local-dir> remote get-url origin
   ```
   Match against REPO to confirm the right directory.

4. Create a branch:
   ```
   git -C <local-dir> checkout -b issue-<number>-<slug>
   ```
   where `<slug>` is 2-4 words from the issue title, kebab-cased.

5. Implement — stay within the acceptance criteria. No refactoring outside scope.

6. Build-verify after every file change. Fix errors before continuing.

6b. Eval gate. If the diff touches anything model-facing (a prompt, a model string, the AI
    client, a rubric the model feeds, or eval fixtures):
    - Repo has an `evals/` folder → run `npm run eval` (see its `evals/README.md`). If a metric
      regressed past tolerance, stop and report; do not lower the baseline yourself.
    - Repo has no eval suite → write "No eval coverage" in the PR's Evals section.
    Not model-facing → write "Not model-facing" there. Never leave the section blank.

7. Commit with a message referencing the issue:
   ```
   git commit -m "brief description (#<number>)"
   ```

8. Push and open a PR:
   ```
   gh pr create \
     --repo $REPO \
     --title "<issue title>" \
     --body "$(cat <<'EOF'
   Closes #<number>

   ## Changes
   -

   ## Test
   - [ ] Build passes
   - [ ] Feature works end-to-end in browser

   ## Evals
   <paste evals/results/*.md scorecards | "No eval coverage" | "Not model-facing">
   EOF
   )"
   ```

9. Report: PR URL, files changed, what was done.

## Constraints
- One issue = one PR. Do not bundle unrelated fixes.
- If you discover a bug outside scope, open a new issue — do not fix it here.
- If acceptance criteria cannot be met without out-of-scope changes, stop and report.
