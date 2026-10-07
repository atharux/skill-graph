Validate the memory store, then fix what it finds.

```
python3 .claude/scripts/validate-memory.py
```

## Act on the output

**ERROR — always fix.** A malformed or unindexed memory actively misleads a future session:
missing frontmatter, missing `description` (recall matches on it), a bad `metadata.type`, a
memory absent from `MEMORY.md`, or an index line pointing at a file that does not exist.

**WARN — judgement.** Relative dates are the ones that matter: "currently blocked", "recently
shipped" and "this week" are true when written and wrong a month later. Convert those to
absolute dates. The check is a plain word match, so it also fires on generic prose ("things he
can ship today") and on quoted text — those are false positives, leave them and do not churn
the file to silence the linter.

Oversized files mean one memory is carrying several facts. Split only if the parts are genuinely
independent; a long file about one project is fine.

**NOTE — informational.** A `[[link]]` with no file yet is by design; it marks something worth
writing, not an error. A missing `Why:` line is worth adding to `feedback` memories especially,
since the reason is what makes the guidance transferable.

## Then verify what the memories claim

The linter checks shape, not truth. Spot-check anything time-sensitive against reality before
trusting it — `git fetch` before believing a repo claim, read the file before believing a
file:line citation. Memory is a point-in-time observation. Delete what turned out to be wrong
rather than layering a correction on top.

Report what you changed and what you deliberately left. If the store is clean, say so in one
line and stop.
