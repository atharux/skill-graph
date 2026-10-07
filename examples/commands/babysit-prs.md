Drive every open PR to merged or closed. Nothing sits.

Twelve open PRs across the portfolio, two over 35 days old, is the single largest gap
between work done and value delivered. This command exists to close it.

## Gather

For every repo under ~/code with a GitHub remote:

```
gh pr list --state open --json number,title,createdAt,headRefName,mergeable,mergeStateStatus,isDraft
```

For each PR also get: commits ahead of base, files changed, and whether CI exists and passed.
`git fetch --all -q` first. Never judge a PR from a stale local ref.

## Triage — assign every PR exactly one verdict

| Verdict | When | Action |
|---|---|---|
| MERGE NOW | mergeable, scope still wanted, build passes | squash-merge, delete branch |
| NEEDS BUILD | mergeable but unverified | build it in a worktree (see below), then merge or report the failure |
| NEEDS REBASE | conflicts or behind base | say what conflicts; do not force-push without asking |
| SUPERSEDED | its change already landed another way | close with a one-line reason |
| CLOSE | scope no longer wanted | close with a one-line reason |
| ASK | you cannot tell whether it is still wanted | list it under decisions, do not guess |

Sort output oldest-first. Age is the point.

## Verify without disturbing the working tree

He is often mid-edit on another branch. Never checkout or stash in his repo. Use a worktree:

```
git worktree add /tmp/<slug> <branch>
ln -s <repo>/node_modules /tmp/<slug>/node_modules   # only if package.json is unchanged vs base
cd /tmp/<slug> && npm run build
git worktree remove /tmp/<slug> --force && git worktree prune
```

Confirm `git diff base..branch -- package.json package-lock.json` is empty before symlinking
node_modules. If it is not, install in the worktree instead.

## Act

Merge everything in MERGE NOW and NEEDS BUILD-that-passed, without asking — merging a green PR
into his own repo is the point of the command. Do NOT: force-push, deploy, or touch anything
outside the PR's own branch.

Flag separately any PR whose merge does not actually ship the change (edge functions, migrations,
secrets) with the exact command still required.

## Report

```
## PR BABYSIT — [date]

MERGED        [repo #n — title]
CLOSED        [repo #n — title — reason]
BLOCKED       [repo #n — what is blocking, exact next step]
NEEDS YOU     [repo #n — the question, one line]
```

End with the count still open and the age of the oldest. If that number did not go down,
say so plainly.
