You are in PLANNING mode. Use the claude-opus-4-8 model for this session.

Project or feature to plan: $ARGUMENTS

## Step 0: Detect the target repo

Run this and capture the result:
```
gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null
```

If that returns a valid `owner/repo`, use it for all subsequent `gh` calls.

If $ARGUMENTS begins with a string matching `owner/repo` or just a known repo name (e.g. `web-app`, `api`, `docs`), resolve it to the full `your-org/<name>` form.

If still unclear, ask: "Which repo? (e.g. your-org/web-app)"

Store the result as REPO and use it throughout.

## Your job

Produce a structured GitHub issue plan. Do NOT write any code.

### Steps

1. Read the repo CLAUDE.md and relevant source files to understand current state
2. Ask ONE clarifying question if the scope is genuinely ambiguous — otherwise proceed
3. Generate a plan with:
   - Milestone assignment (use existing milestones, or propose new ones)
   - Issues ordered by dependency (earlier issues unblock later ones)
   - Each issue: title, 2-sentence context, acceptance criteria checklist, labels, milestone

4. Create the issues on GitHub:
   ```
   gh issue create \
     --repo $REPO \
     --title "..." \
     --body "..." \
     --label "feat,layer:ui,p1" \
     --milestone "M2: CRM"
   ```

5. Report a table: issue number | title | milestone | labels

### Issue writing rules
- Title: verb phrase, present tense ("Add CSV import", not "CSV import feature")
- Body: context paragraph + acceptance criteria checklist + out-of-scope line
- One logical change per issue — if it touches >3 files or has >5 acceptance criteria, split it
- Do not mention implementation details unless they are constraints
- Model-facing issue (prompt, model string, AI client, a rubric the model feeds)? Add the
  criterion "`npm run eval` shows no regression vs baseline; scorecard in PR". If the repo
  has no eval suite, add "no eval coverage — noted in PR" instead, and consider an issue to
  create one (see CLAUDE.md → Eval gate)

### Labels to use
- Type: `feat` / `fix` / `chore`
- Layer: `layer:ui` / `layer:data` / `layer:api`
- Priority: `p1` / `p2` / `p3`
