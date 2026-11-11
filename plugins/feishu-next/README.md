# Feishu Next

Feishu Next is a **workflow capability layer** built from BlueSkyXN's personal
Feishu/Lark playbooks and experience. It connects operations with step order,
dependencies, identity, evidence, backups and quality standards, rather than
forwarding an entire task to one official skill.

Current source version: **0.11.0**, with **eleven skills**: the bundled
`$feishu-next:feishu-workflow-router` plus ten playbooks. Router selects a
playbook or composes multiple steps and navigates to official `lark-suite` for
atomic capabilities. Next retains the enclosing workflow state; suite owns
its official guide aggregation and skill-list compression. There is no separate
Router plugin, copied official snapshot or automatic installation dependency.

## Two navigation paths, eleven flat skills

Router explains what official Feishu capabilities can do through five on-demand
maps: documents/knowledge, tables/data, communication/collaboration, visuals/apps,
and platform/extensions. Each describes user phrasing, capability boundaries and
when a Next method adds value; it is not a copied API manual.

Official basic operations and existing official workflows can be selected directly.
Next methods add evidence, fidelity, backup/recovery or cross-task state; step
count is not the boundary. A capability question needs no login or remote access.

All eleven skill entries remain flat. Every playbook links to
[shared Router cooperation](skills/feishu-workflow-router/references/playbook-handoff.md):
missing context or a requested extension can consult Router; an already matching
verified context is reused without redispatch. Changed scope, identity or write
authority is revalidated. Results and unresolved states return to the caller.

## Workflow entry and playbooks

- `feishu-workflow-router`: choose and connect playbooks, track prerequisites and
  verified outputs, preserve authorization checkpoints and navigate to suite.
- `feishu-readonly-doc-export`: export documents, sheets, Base and slides with
  artifact and completion evidence.
- `feishu-slides-preview-to-pdf`: capture a viewable slide deck through the
  signed-in browser, verify page order and image fidelity, and assemble an
  image-based PDF when the user requests this method.
- `feishu-doc-asset-map`: inventory document images, attachments, whiteboards and
  embedded resources without losing resource identity.
- `feishu-im-chat-archive`: archive chat history, threads and resources with
  pagination and evidence-preserving boundaries.
- `feishu-whiteboard-ops`: inspect, edit, redraw and recover whiteboards with
  raw rollback baselines and validation, including `.drawio` publishing.
- `feishu-whiteboard-semantic-cards`: apply the Semantic Card Diagrams style
  using semantic colors, modular cards and clear relationships, generate local
  editable SVG and inspect previews before handing off board operations.
- `feishu-doc-format-align`: apply a reference document or explicit style rules,
  preserving material boundaries and text with paragraph/cell comparisons.
- `feishu-doc-format-repair`: diagnose and repair misplaced headings, material
  boundaries and confirmed paste residue from one or multiple sources; verify
  each authorized structural and textual change.
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

`feishu-whiteboard-semantic-cards` owns the Semantic Card Diagrams style,
its layouts, a standard-library Python SVG kit and local preview checks. It adapts to the content instead of
requiring a fixed category count or palette meaning.

Keep one Next whiteboard operations playbook, `feishu-whiteboard-ops`. Atomic board commands
come from official `lark-whiteboard` guidance through Router. This playbook owns
target confirmation, backup, merge/recovery strategy, render/check gates and
post-write verification. `.drawio` publishing is its conditional reference,
not a separate public skill. Design-to-publish tasks pass the checked source,
preview, target and authorized scope from design to operations; remote changes
still require the operations playbook's own preflight and readback.

## Dependencies and manual install

For CLI-backed workflows, the official `lark-cli` must be installed. Router verifies the selected runtime
and freezes profile/App/identity context before business calls; do not silently
fall back to default identity if the Router is unavailable. Pure local planning
can continue without remote access, but business execution must stop at a missing
dependency. A directly invoked playbook can request Router preflight and then
continue without redispatching itself.

Explicit slide-preview capture uses the selected browser's login state and
does not require a CLI profile. Verify the browser identity, document and capture
scope. If the workflow switches to CLI queries or official export, establish the
CLI execution contract first; browser login is not CLI authentication.

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
$feishu-next:feishu-slides-preview-to-pdf
$feishu-next:feishu-whiteboard-ops
$feishu-next:feishu-whiteboard-semantic-cards
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
or credentials. A UI fallback in a CLI workflow requires a proven CLI gap and
explicit authorization. The dedicated slide-preview workflow may start directly
when the user requests browser capture; it does not permit browser writes or
broader fallback in other workflows.

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
