# Workflow orchestration

Use this when the user requests several connected Feishu operations, not merely
a single domain command. The Router owns the overall goal and checkpoints;
Next playbooks own their specific methods; official suite/domain guidance owns
atomic operations. This is agent-executed workflow guidance, not a scheduler,
background service or automatic subagent launcher.

## Build the smallest sufficient plan

1. Identify the requested outcome, resources, time range, identity, output format
   and explicit exclusions. Inspect available message context before asking.
   Do not add publishing, notifications, schedules or tasks merely because they
   might be useful after the requested operation.
2. Prefer a matching Next playbook. Compose multiple playbooks and official
   capabilities only when the user's goal needs them. An exact official workflow
   can be a step; do not copy it into Next. For a purely atomic request, navigate
   directly to official guidance and skip unnecessary workflow machinery.
3. For each step, state its inputs, prerequisites, outputs, risk, authorization
   boundary and acceptance check. Use a small step ledger for nontrivial tasks:

   | Field | Meaning |
   | --- | --- |
   | step / depends_on | stable local label and required predecessor steps |
   | capability | Next playbook or selected official guide |
   | inputs / outputs | known resource IDs, bounded range, artifact/evidence paths |
   | execution | reference to the frozen profile/App/identity contract |
   | effect / authorization | read, local artifact or exact remote change allowed |
   | state / verification | planned, ready, running, verified, blocked or uncertain |

   This is a private task record, not a new public skill or required remote table.
   Preserve actual IDs locally; never put business artifacts into the plugin.
4. Resolve the `lark_execution` contract before business calls. Carry the same
   explicit profile and identity across handoffs. If a later operation needs a
   different acting representative, stop that branch and establish a separately
   authorized context; do not silently switch to a default.

## Execute and carry evidence

- Load official suite guidance only for the current step and its prerequisites.
  Return the resulting IDs, pagination status, revisions and artifacts to the
  enclosing Next workflow. Do not delegate the whole plan to suite and forget
  downstream steps, and do not redispatch a Next sub-skill already running.
- Pass only verified predecessor outputs. A link in source text is not proof of
  access, and a successful command exit alone is not every playbook's acceptance
  condition. Preserve source references and check the current result envelope.
- Complete required pagination before claiming a complete archive or analysis.
  Recheck revisions/schema before writes that depend on earlier reads.
- An authorized read does not authorize a later create, publish or send. Build
  the exact payload and target; use `--dry-run` and the runtime confirmation gate.
  A fully specified current-turn write request can supply bounded authorization;
  do not demand a redundant confirmation unless ambiguity or a runtime gate
  requires it. Never treat a broad workflow goal as blanket `--yes` consent.

## Failure and resume

- Mark a step verified only after its acceptance check succeeds. If it fails,
  block dependent steps while keeping prior evidence. Independent branches may
  continue only within the original authorization and unchanged context.
- A timed-out or interrupted write has uncertain outcome. Read back before
  retrying, reconcile by the original business/idempotency key, and do not create
  duplicate docs, messages or records just because no success response arrived.
- Resume from verified checkpoints using the same plan and sources. If sources,
  schema, acting identity or authorized scope changed, stop and revise the plan.
  Do not present a mixed-source partial rerun as one consistent snapshot.
- Never perform compensating deletes or destructive rollback without explicit
  authority. Preserve recovery evidence and follow the owning playbook.

## Completion

Report the requested outcome, verified steps, resulting artifacts/links, any
blocked or uncertain step, and actions deliberately not performed. Distinguish
plan/draft from remote execution; do not label a partly completed workflow done.

## Examples

- "Archive this week's chat, use the evidence to draft a document, don't publish."
  Use the IM archive playbook for complete bounded evidence, then draft locally.
  Do not create a remote document or send a message.
- "Inventory this document's assets, export it, then send the result to this group."
  Compose asset mapping and export, carry verified export artifacts to official
  IM guidance, and resolve the precise send content/target and authorization
  before the last step. Export failure blocks sending a nonexistent result.
- "Adjust the whiteboard and then update its surrounding explanation."
  Use the whiteboard playbook's backup/write/verification first, then official
  Doc guidance with the actual board result and current revision. A failed board
  update blocks an explanation claiming the new board is already live.
