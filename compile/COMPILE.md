# Compiling an instruction file

Give this page to a coding agent together with one prose instruction file (a slash
command, a skill, a runbook, a system prompt) and `compile/procedure.schema.json`.
It describes how to turn the prose into one YAML file the validator will accept.

The compile is a quality gate, not a rewrite. Do not improve the procedure. Record
what the prose says, and report what it leaves unclear.

## Output

One file, `<name>.yaml`, next to the others, with:

- `skill`: the file name without its extension.
- `source`: the path of the prose file, relative to the sources folder.
- `purpose`: one sentence.
- `inputs`: what the caller passes in, each with a `name` and a `type`.
- `steps`: in execution order.
- `notes`: every ambiguity or contradiction you had to resolve to produce the steps.

## One step per action

Split the prose wherever the actor, the tool or the effect changes. A step has:

| Field | How to decide |
|---|---|
| `kind` | `script` if it is a fixed command or file operation. `judgment` if the model decides something. `gate` if it is an automatic check that can stop the run. `approval` if a human must answer. `report` if it hands output to the human. |
| `effect` | `read` if it only reads. `local` if it writes on this machine. `spend` if it calls something that costs money or quota. `remote` if it changes anything outside this machine: a push, a merge, an issue, a message, a deploy, a publish. |
| `tool` | The one tool the step uses, or `none`. |
| `conditional` | `true` only when the prose says the step happens in some runs ("if unclear, ask"). A conditional approval does not count as approval in the queries. |
| `destructive` | `true` when the step deletes something. |
| `in` | Names of values this step consumes. Each must be a skill input or an output of a step above. |
| `out` | Values this step produces, each with a `name` and a `type`. |
| `after` | Ids of earlier steps it must wait for without consuming their output. |
| `uses` | The id of a shared rule in `subprocedures.yaml`, when the same rule appears in other files. |
| `touches` | Files or folders the step reads or writes, when that matters across files. |
| `quote` | Text copied exactly from one line of the prose that justifies this step. |

## Rules

1. **Every step needs a quote.** If you cannot quote a line for a step, the step is
   your invention. Remove it.
2. **Classify by what the prose says, not by what would be sensible.** If the prose
   says "merge without asking", that is a `remote` step with no approval before it.
3. **Do not add approvals or checks the prose does not contain.**
4. **When two readings are possible, pick one and write a note.** The notes are a
   deliverable. They are often the most useful output.
5. **Run the validator and fix what it reports until it passes:**
   `python3 compile/validate.py --skills <folder> --sources <folder>`

## Then have a human review it

The validator proves that every quote exists and every input resolves. It cannot tell
whether you chose `script` where `judgment` was right, or `read` where `remote` was
right. Those calls decide what the queries return, so a person should check them.
