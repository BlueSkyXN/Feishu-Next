# Feishu Next

Feishu Next is a **workflow capability layer** built from BlueSkyXN's personal
Feishu/Lark playbooks and experience. It connects operations with step order,
dependencies, identity, evidence, backups and quality standards, rather than
forwarding an entire task to one official skill.

Current source version: **0.7.0**, with **eight skills**: the bundled
`$feishu-next:feishu-workflow-router` plus seven playbooks. Router selects a
playbook or composes multiple steps and navigates to official `lark-suite` for
atomic capabilities. Next retains the enclosing workflow state; suite owns
its official guide aggregation and skill-list compression. There is no separate
Router plugin, copied official snapshot or automatic installation dependency.

## Two navigation paths, eight flat skills

Router explains what official Feishu capabilities can do through five on-demand
maps: documents/knowledge, tables/data, communication/collaboration, visuals/apps,
and platform/extensions. Each describes user phrasing, capability boundaries and
when a Next method adds value; it is not a copied API manual.

Official basic operations and existing official workflows can be selected directly.
Next methods add evidence, fidelity, backup/recovery or cross-task state; step
count is not the boundary. A capability question needs no login or remote access.

All eight skill entries remain flat. Every playbook links to
[shared Router cooperation](skills/feishu-workflow-router/references/playbook-handoff.md):
missing context or a requested extension can consult Router; an already matching
verified context is reused without redispatch. Changed scope, identity or write
authority is revalidated. Results and unresolved states return to the caller.

## Workflow entry and playbooks

- `feishu-workflow-router`: choose and connect playbooks, track prerequisites and
  verified outputs, preserve authorization checkpoints and navigate to suite.
- `feishu-readonly-doc-export`: export documents, sheets, Base and slides with
  artifact and completion evidence.
- `feishu-doc-asset-map`: inventory document images, attachments, whiteboards and
  embedded resources without losing resource identity.
- `feishu-im-chat-archive`: archive chat history, threads and resources with
  pagination and evidence-preserving boundaries.
- `feishu-whiteboard-ops`: inspect, edit, redraw and recover whiteboards with
  raw rollback baselines and validation, including `.drawio` publishing.
- `feishu-doc-format-align`: align document formatting while preserving text.
- `feishu-mindnote-outline`: maintain an existing Mindnote outline and hierarchy.
- `feishu-base-snapshot-maintain`: check, plan, resume and verify generic
  weekly/monthly Base snapshots without rewriting history.

Personal methods do not mean publishing private data. Five organization-specific
workflows and the project-specific snapshot implementation remain in their own
workspace. Public admission requires reusable Feishu execution value, not merely
using Feishu as a source or destination. The generic snapshot method ships no
one-click executor and does not depend on the originating project's scripts.
See [public/private boundaries](../../docs/skill-migration.md).

## Whiteboard boundary

Keep one Next whiteboard playbook, `feishu-whiteboard-ops`. Atomic board commands
come from official `lark-whiteboard` guidance through Router. The playbook owns
target confirmation, backup, merge/recovery strategy, render/check gates and
post-write verification. `.drawio` publishing is its conditional reference,
not a separate public skill.

## Dependencies and manual install

The official `lark-cli` must be installed. Router verifies the selected runtime
and freezes profile/App/identity context before business calls; do not silently
fall back to default identity if the Router is unavailable. Pure local planning
can continue without remote access, but business execution must stop at a missing
dependency. A directly invoked playbook can request Router preflight and then
continue without redispatching itself.

When suite is exposed by the host, read its selected
`references/<skill-name>/GUIDE.md` from the actual installed location. Otherwise
use available separate official skills or `lark-cli skills read`. The latter does
not include machine scripts/assets; report missing mandatory resources instead
of skipping validation. Runtime catalog discovery does not prove suite is
installed. See [workflow architecture](../../docs/workflow-architecture.md).

```bash
codex plugin marketplace add /path/to/Feishu-Next
codex plugin list --marketplace feishu-next --available --json
codex plugin add feishu-next@feishu-next
```

These are manual installation instructions, not actions run by this package.
For updates, use your client's plugin management flow and verify the installed
versions in a new session. Do not equate editing source with updating the cache.

Start from the workflow Router or invoke a playbook directly:

```text
$feishu-next:feishu-workflow-router
$feishu-next:feishu-readonly-doc-export
$feishu-next:feishu-whiteboard-ops
$feishu-next:feishu-doc-format-align
```

The Router namespace remains `$feishu-next:feishu-workflow-router`. Next does
not contain copies of official `lark-cli` skills. Updates or separate/suite layout
changes occur only when the user explicitly directs AI; ordinary requests never
install suite, delete global skills or rewrite client settings. An old standalone
`lark-cli-guide` under `~/.codex/skills` is not required for this workflow entry,
but Next never removes that user-owned registration automatically.

Trial: "Use $feishu-next:feishu-workflow-router to plan a chat archive followed
by a document draft; do not access remote resources or publish."
Expected: a bounded archive step, a dependent local drafting step, official
guide navigation as needed, and no business calls or unrequested sends.

## Safety and validation

Preserve each playbook's read-before-write, explicit identity, pagination,
evidence and backup rules. Prepare the exact write with `--dry-run`; satisfy
runtime high-risk approval before `--yes`. Never publish private URLs, content
or credentials. A UI fallback requires a proven CLI gap and explicit authorization.

The original 0.3.0 workflow baseline was runtime-validated against the installed
`lark-cli 1.0.83` and source-audited against `lark-cli 1.0.86`. Those historical
checks do not prove this source version is installed or business-tested. Current
local runtime validation reads selected skills/references and `--help` only.

```bash
python3 scripts/validate_project.py
python3 -m unittest discover -s scripts/tests -v
python3 scripts/validate_lark_runtime.py
```

Run from the repository root. Missing Codex plugin/skill validators fail the normal
validation gate. For non-release local checks only, explicitly pass
`--allow-missing-codex-validators`. No validator should authenticate, write a
Feishu resource, publish, install a plugin or change global skill registrations.
