---
name: feishu-workflow-router
description: Use when asking what Feishu/Lark can do or choosing how to read, create, edit, search, export or manage docs, files, Wiki, tables, messages, meetings or apps; select official lark-suite guidance, a Next playbook, or a composed workflow. Also use for execution-context checks and before browser/UI fallback; directly matched Next skills can run without redispatch.
metadata:
  version: "0.11.0"
  updated: "2026-11-10"
---

# Feishu workflow router

Use this as the Feishu Next workflow entrypoint: connect the user's Feishu
operations into an ordered, verifiable outcome, rather than merely choosing one
API or forwarding the whole task to another skill. Next preserves personal
playbooks, step dependencies, evidence and recovery discipline. Official
`lark-suite` owns its aggregated capability entry and compressed skill list.
The installed `lark-cli` remains the runtime truth.

This skill supersedes the standalone global `lark-cli-guide` for Next workflow
usage, not the official suite. Do not copy or vendor official `lark-*` skill
bodies into this plugin. Next has no separate Router plugin or official snapshot.

## Choose official usage, a Next playbook, or composition

For capability questions, explain what the requested domain can do and where its
boundary lies. Read only the matching capability map below; do not demand a URL,
profile, login or business access just to explain capabilities. The maps describe
routing, not executable API contracts or proof of access.

Next keeps this Router plus ten independently discoverable playbooks. A directly
matched playbook need not restart here; references are internal detail, not more
public skills.

- If official guidance fully covers the requested result, use it, including its
  own multi-step procedures. **Step count does not decide ownership.** Document
  creation, permission governance and folder organization can already be official
  workflows. Do not replace them merely because they contain several commands.
- For a matching Next method or an explicit Next invocation, preserve that
  playbook's added evidence, fidelity, backup or recovery requirements.
- Compose when the user's goal connects results across methods/capabilities or
  needs an enclosing state/acceptance contract. Read
  [workflow-orchestration.md](references/workflow-orchestration.md) only then.
  Do not invent a persistent skill for each request or add unrequested steps.
- Next retains ownership of multi-step state: step order, inputs/outputs,
  authorization boundaries, validation and partial-failure checkpoints.
  Navigating to suite supplies a step's official procedure, not permission to
  abandon the overall plan or its stronger evidence/backup rules.
- A directly invoked Next sub-skill may use this Router only for context or
  capability discovery. Return that result to the caller without redispatching
  the same sub-skill. Reuse a valid frozen context; do not loop between entries.
  Apply [playbook-handoff.md](references/playbook-handoff.md) when a directly
  invoked playbook needs shared context or an extension to another step.

## Official capability overview

Choose by the user's goal, not a skill name or URL alone. Read only the relevant
map when explaining capabilities, resolving overlap or choosing between official
usage and Next. Known unambiguous tasks may go straight to the selected official
guide. Do not read every map or copy its descriptions into every playbook.

| User goal | Official guide candidates | Read when needed |
| --- | --- | --- |
| Read/create/edit a document, manage media or history; find/copy/export files; organize Wiki; edit native Markdown | `lark-doc`, `lark-drive`, `lark-wiki`, `lark-markdown` | [Documents and knowledge](references/capabilities-documents.md) |
| Read/write cells, formulas and charts; manage Base records/schema, forms, dashboards and BaseApp | `lark-sheets`, `lark-base`; file transfer may use `lark-drive` | [Tables and data](references/capabilities-data.md) |
| Messages/mail, calendar/rooms, meeting content, tasks/approvals, contacts, attendance and OKR | `lark-im`, `lark-mail`, `lark-calendar`, `lark-meeting`, `lark-task`, `lark-approval`, `lark-contact`, `lark-attendance`, `lark-okr` | [Communication and collaboration](references/capabilities-collaboration.md) |
| Native Slides, document whiteboards, Miaoda/Spark development and creative apps | `lark-slides`, `lark-whiteboard`, `lark-apps` | [Visuals and apps](references/capabilities-visual-apps.md) |
| Auth/identity, events, Open Platform management, missing API coverage and custom skills | `lark-shared`, `lark-event`, domain help, `lark-openapi-explorer`, `lark-skill-maker` | [Platform and extensions](references/capabilities-platform.md) |

Each map explains capabilities, natural-language triggers, domain boundaries and
when a Next method adds value. It is a small navigation summary, not an official
skill copy. Read current official guides/references before using actual commands.

## Official workflows and aliases

Prefer an exact official workflow when it satisfies the whole request:
`lark-workflow-meeting-summary` for meeting summaries over a time range and
`lark-workflow-standup-report` for calendar plus incomplete-task summaries.
Document creation and Drive permission governance/organization also have official
procedures inside their domain guides; follow them rather than rebuilding them.
A method used as a step returns evidence to the enclosing Next workflow.

The compatibility names `lark-minutes`, `lark-note`, `lark-vc` and
`lark-vc-agent` lead to `lark-meeting` in the current runtime. They are not four
independent capabilities; verify older or restricted distributions at runtime.

## Official suite navigation

Read [official-suite-navigation.md](references/official-suite-navigation.md)
when choosing between suite, separate skills and runtime reads:

- If `lark-suite` is actually exposed by the current host, load it through the
  host's available skill mechanism (or its observed entry file). Follow its
  selected `references/<skill-name>/GUIDE.md`; do not invoke nested guides as
  independent Skill tools, scan all guides, or assume an install cache path.
- If only separate `lark-*` skills are exposed, use the selected official skill.
  If neither layout is visible, use `lark-cli skills read <skill>` for embedded
  guidance. Missing machine resources must still be reported, not ignored.
- `lark-cli skills list` enumerates binary-embedded domain guides, not host
  registrations. It does not prove `lark-suite` is installed. Do not invent
  `lark-cli skills read lark-suite` when the runtime does not list it.
- Commands, identity, scopes and risk behavior still require current runtime
  guidance/help. An installed suite does not prove an unavailable domain exists.
- Updates and layout changes happen only when the user explicitly directs AI to
  perform them. Never automatically run `lark-cli update`, switch layouts,
  install plugins, remove global skills or refresh a snapshot during a task.

## Authority model

Use official runtime guidance and Feishu Next together, but keep their
responsibilities separate:

| Authority | Owns |
| --- | --- |
| Latest user instruction | target resource, business intent, risk acceptance |
| Official `lark-cli skills read <lark-*>` output | skill-owned commands, flags, identity behavior, scopes, risk labels, API support, error handling |
| Current `lark-cli <domain> --help` / shortcut help | domains or commands that do not have an embedded skill, plus current command availability |
| Official `lark-suite` or separate skills | official capability selection and selective guide loading; not Next workflow state |
| `feishu-workflow-router` | goal decomposition, step dependencies, shared execution context, official navigation and workflow checkpoints |
| Feishu Next sub-skills | cross-step order, evidence capture, backups, validation gates, local artifact boundaries |
| Feishu Next references | optional branch details loaded only when their trigger is present |

If official runtime guidance conflicts with this repository on command syntax,
scope, identity, or supported behavior, follow the current runtime. If the
conflict is about workflow discipline such as backup-before-write, pagination,
export evidence, or post-write validation, keep the Feishu Next guardrail
unless the user explicitly accepts the risk.

## Bootstrap discovery

For a local Semantic Card Diagrams design request, select
`$feishu-next:feishu-whiteboard-semantic-cards` without requiring CLI authentication.
Read-only online references or a later board write use the normal CLI context
and whiteboard operations handoff.

For an explicit browser-capture request for a viewable slide deck, select
`$feishu-next:feishu-slides-preview-to-pdf` before CLI bootstrap. That workflow
checks the selected browser identity, document and capture scope. It does not
require CLI installation or login unless it also invokes a CLI operation.

Bootstrap is read-only and does not require a complete business contract. Use
it to turn an ordinary natural-language request into a proposed
`lark_execution_draft`; do not ask the user for raw profile names or App IDs.

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

If `lark-cli` is missing, stop CLI-dependent steps and explain the dependency.
Do not infer installed capabilities from this repository. The dedicated browser
capture path remains governed by its own browser prerequisites.

Read `lark-shared` whenever credentials, identity, scopes, permission errors,
`verification_url`, `console_url`, `_notice.update`, QR flow, unsafe paths,
`--dry-run`, or exit-10 confirmation behavior is involved:

```bash
lark-cli skills read lark-shared
```

After reading the relevant skill/help, use `lark-cli profile list` to discover
system candidates when profile selection is needed. Use identity diagnostics
only after one profile candidate and an independent expected App anchor have
been selected:

```bash
lark-cli profile list
lark-cli --profile <profile> whoami --json
lark-cli --profile <profile> auth status --json --verify
lark-cli --profile <profile> doctor --offline
```

The profile-qualified form above is the executable preflight. The equivalent
diagnostic capability is `lark-cli auth status --json --verify`; never use it
without the frozen `--profile` when execution context matters.
Likewise, `lark-cli doctor --offline` names the available local diagnostic; use
the profile-qualified form above for a selected execution context.

## Execution context contract

This contract governs CLI business, authentication, profile and identity-policy
calls. The dedicated browser-capture workflow verifies browser identity and scope
instead; browser login never establishes a CLI contract.

Read
[`references/lark-execution-context.md`](references/lark-execution-context.md)
and follow its preflight, parameter mapping, error classification, and stop
conditions. Bootstrap discovery is contract-free; it may inspect runtime
version, official skills/help, profile candidates, and non-secret caller
metadata, but it must not make a business, authentication, profile-mutation, or
identity-policy call.

Build `lark_execution_draft` from the current message and discovered evidence,
allowing internal fields to remain `unknown`. Before any business,
authentication, profile, or identity-policy invocation, freeze a complete
`lark_execution` for user-owned, bot-owned, and shared resources alike. The
Router, not an ordinary user, owns discovery of internal profile/App fields.

The caller selects `context: channel|system`; environment variables only
describe the process's actual binding. A shared `lark-cli` binary does not
imply a shared config directory, app, profile, or login state. In particular:

- `--profile` selects an existing profile only inside the current config
  directory.
- `--as user|bot` selects an identity only inside the selected app/profile.
- `--domain`, `--scope`, and `--exclude` select OAuth scope, not an app.
- `LARK_CHANNEL*` and `LARKSUITE_CLI_CONFIG_DIR` are diagnostic evidence, not
  instructions for choosing the business target.

Freeze `expected_app_id` from an independent caller/channel anchor, a user's
human-readable candidate selection, an unambiguous requested representative,
or an upstream frozen context. Do not copy an actual App ID read during
preflight into the expected side of the same comparison. Run `whoami` and
`auth status` with the requested profile and continue only when profile, App,
and identity match the contract. Treat a missing requested
profile or a channel/system mismatch as `execution_context_mismatch`, not as
missing authorization. Stop without running `auth login`, `profile add/use`,
`config bind`, `config strict-mode`, or `config default-as`; do not unset or
override binding environment variables to force a different context.
Generic first-use authentication guidance from an owning runtime skill applies
only after this context and app preflight succeeds; it never overrides an
`execution_context_mismatch` stop.

Keep `profile` and `identity` explicit across the full workflow. Any command
that consumes an ID or token returned by an earlier command must reuse the same
`--profile` and `--as`; omission re-enters runtime default selection and is not
identity continuation. If the downstream command does not support that
identity, stop instead of silently switching identities.

## Runtime discovery order

1. Resolve the target from the current message, selected resource, reply/quote,
   attachment, incoming event, URL path, token prefix, or user intent. For
   phrases such as "this document", inspect available message context before
   asking the user for a URL.
2. Classify the request as a Next playbook, a composed workflow, or a direct
   official operation. Navigate through an actually available `lark-suite` or
   separate skill; run `lark-cli skills list` to verify the embedded surface.
   Reuse discovery within the same binary/profile/distribution context.
3. Read the chosen official guide and the references needed by this step.
   For runtime-only discovery or command/identity verification, use:

   ```bash
   lark-cli skills read <skill>
   lark-cli skills list lark-doc/references
   lark-cli skills read lark-doc references/lark-doc-fetch.md
   ```

   A restricted or embedded distribution may deliberately trim its command and
   skill tree. Treat `skills list` and actual help in that invocation as the
   available surface; use `lark-cli config plugins show` only when distribution
   policy diagnostics are available and the missing capability needs
   explanation. Do not infer stock capabilities from this repository or an
   upstream source checkout.

4. When the domain exists but has no embedded skill, read the domain and
   shortcut help instead. `application` is the current canonical example; do not invent a `lark-application` skill:

   ```bash
   lark-cli application --help
   lark-cli application +slash-command-list --help
   ```

5. If an optional domain is absent from the current CLI, report that this
   invocation does not expose it. Check distribution/plugin diagnostics when
   available; otherwise suggest `lark-cli update`. Do not misclassify an
   unavailable or deliberately concealed command as a scope or permission
   failure.
6. Prefer an exact official workflow when it satisfies the whole request. When
   it is one step of a larger Next workflow, retain the enclosing dependencies,
   authorization, evidence and validation requirements.
7. Use `lark-openapi-explorer`, `lark-cli schema`, or `lark-cli api` only when
   neither an official skill nor a registered domain/shortcut covers the task.
   `lark-cli api` has only a generic `Risk: write` classification and cannot
   infer whether an arbitrary endpoint is destructive. For raw
   `POST`/`PUT`/`PATCH`/`DELETE`, classify the business action yourself, use
   `--dry-run`, and obtain the same explicit confirmation that the equivalent
   typed write or high-risk write would require.

## Capability gaps and UI fallback

The dedicated `$feishu-next:feishu-slides-preview-to-pdf` workflow is an explicit
browser-capture method. When the user requests it, follow its browser context,
page-fidelity and local PDF checks without first proving a CLI gap. An ordinary
export failure alone is not permission to switch to screenshot capture; explain
the image-based result and obtain acceptance unless already authorized. This
exception covers read-only slide capture, not browser editing or permissions.

When a required step looks unsupported by the current CLI, do not switch tools
silently. For other CLI-to-UI fallbacks, escalate in this order:

1. Prove the gap with runtime evidence first. Read the owning skill and its
   relevant references, then quote the exact line that marks the operation
   unsupported. Example: `lark-doc references/lark-doc-xml.md` lists block
   types that cannot be created. Also confirm no `+shortcut`, typed command,
   `lark-cli schema ...`, or `lark-cli api` escape hatch covers the step.
2. Check whether a newer runtime closes the gap. Compare `lark-cli --version`
   with the update notice and surface `lark-cli update` to the user before
   designing a workaround.
3. Ask for explicit authorization before any browser or UI-automation action
   on a Feishu resource. Suggestion-style wording such as "感觉可以…" or
   "或许能…" is a proposal, not execution authorization. State the proven CLI
   gap, the exact UI action, and its blast radius, then wait for confirmation.
4. Keep the fallback bounded to the single proven gap. Reads, revision checks,
   backups, and post-write verification stay on `lark-cli`.
5. Outside the dedicated slide-capture workflow above, do not encode a browser
   fallback into reusable skills, templates, or docs as a normal step. Record
   it as a temporary workaround tied to the proven gap and the `lark-cli`
   version, so it is re-checked when the CLI updates.

An unavailable command is a capability gap, not a scope or permission failure;
report it as such.

## Feishu Next workflow routing

Use Feishu Next for the reusable, stateful workflows it explicitly owns:

| Workflow signal | Use |
| --- | --- |
| Export a doc/sheet/base/slides file with artifact evidence | `$feishu-next:feishu-readonly-doc-export` |
| Explicitly capture a viewable Slides deck through the browser into an image-based PDF | `$feishu-next:feishu-slides-preview-to-pdf` |
| Inventory document assets or embedded resources | `$feishu-next:feishu-doc-asset-map` |
| Archive IM history with pagination/evidence | `$feishu-next:feishu-im-chat-archive` |
| Design whiteboards in the Semantic Card Diagrams style with semantic colors and modular cards | `$feishu-next:feishu-whiteboard-semantic-cards` |
| Modify, redraw, recover, or validate a whiteboard | `$feishu-next:feishu-whiteboard-ops` |
| Publish/sync `.drawio` or diagrams.net to a Feishu whiteboard | `$feishu-next:feishu-whiteboard-ops` |
| Apply a reference or explicit style rules while preserving text | `$feishu-next:feishu-doc-format-align` |
| Diagnose and repair heading/material-boundary damage or confirmed paste residue | `$feishu-next:feishu-doc-format-repair` |
| Update an existing Mindnote outline and parent relationships | `$feishu-next:feishu-mindnote-outline` |
| Maintain weekly/monthly Base snapshots and comparison batches | `$feishu-next:feishu-base-snapshot-maintain` |

For a whiteboard redraw that needs visual decisions, design first, then pass
the inspected source and preview to whiteboard-ops for the authorized remote
change. Simple text/color edits and recovery can stay in ops. Neither playbook
redispatches itself through Router.

For a vague request such as “格式乱了”, inspect the symptoms before choosing
between alignment and repair. Known style rules select align; damaged heading
relationships, material boundaries or pasted content select repair, including
single-source content. When both are requested, verify repair first, then pass
the latest snapshot, revision and block mapping to align with the valid context.
Each workflow carries its own complete editing and verification rules.

Only publish workflows with Feishu-specific, reusable execution value beyond
an organization's policy or template. Business reports, job assessments,
usage statistics and company-system integrations remain project-owned; do not
invent a bundled workflow for them. Use an explicitly available project skill
when appropriate, and route its atomic Feishu operations to the official runtime.

The generic snapshot workflow accepts the caller's schema, period and policy
inputs; it does not require a particular workspace, resource-map file or private
script. A project-specific snapshot skill is a separate implementation, not an
automatically registered alias or dependency. Missing inputs never authorize
inventing defaults, changing schema or switching identity.

## Identity and permission reminders

Do not default mechanically to user identity. Choose `--as user` / `--as bot`
deliberately for the target resource and operation.

- Prefer `--as bot` for bot-owned resources, application messages, service-side
  automation, event subscriptions, and resources explicitly visible to the bot.
- Prefer `--as user` for personal Drive/Wiki/docs, calendar, mail, user-visible
  Base/Sheets/Slides, IM search, and resources the bot cannot see.
- Use `lark-cli whoami` when the effective identity is unclear before changing
  authentication or retrying a failed command.
- Permission failures can mean app scope is missing, user OAuth scope is
  missing, or the target resource is not shared with the current identity.
  Follow `missing_scopes`, `console_url`, and `hint` from the CLI.
- For bot identity, do not run `auth login`; ask the user/admin to open the
  exact `console_url` when the app backend lacks scope.
- For user identity, request the narrowest `lark-cli auth login --scope ...`
  or `--domain ...` after confirming the app backend scope exists.
- Calendar, mail, approval, attendance, OKR, live meeting, and broad contact
  operations are sensitive. Start read-only or with `--dry-run`.
- Resolve relative calendar ranges such as "today" or "this week" with the
  timezone supplied by the caller/user context and current `lark-calendar`
  guidance. Ask only when no timezone evidence is available; do not guess a
  date boundary.

## Resource parsing rules

- `/docx/` and `/doc/`: document content goes through `lark-doc`; export,
  comments, permissions, metadata, and Drive search go through `lark-drive`.
- `/wiki/`: use the domain skill appropriate to the task. `drive +export --url`
  can unwrap Wiki URLs directly; use `drive +inspect` when evidence or explicit
  object type/token is needed.
- `/sheets/`: use `lark-sheets` for internal data and `lark-drive` for export,
  search, comments, permissions, or versions.
- `/base/` or `/bitable/`: use `lark-base` for internal data and management;
  use `lark-drive` for import/export. For a vague read such as "look at the
  records", use a bounded Base read: if the URL identifies a table/view, read
  only a finite first page; otherwise list tables/views first. Ask for a filter
  or range only when it materially changes the requested business scope.
- Mindnote URLs/tokens or explicit mindnote intent: read `lark-doc`, then use
  `lark-cli mindnotes ...` as directed by the runtime skill.
- Native Markdown intent goes to `lark-markdown`; importing Markdown as a Docx
  remains a `lark-drive` import task.
- IM group/chat/message work goes to `lark-im`; prefer known `oc_...` chat IDs,
  or resolve by `+chat-search`.
- Document-embedded whiteboards: use `lark-doc` to extract the token, then
  `lark-whiteboard`; multi-step edit/verify/recovery uses Feishu Next.
- `.drawio` or diagrams.net source diagrams bound for Feishu whiteboards use
  `$feishu-next:feishu-whiteboard-ops` so source and reconciliation boundaries
  stay explicit.

## Recommended response

When routing rather than executing, return:

1. selected official skill, domain help, or Feishu Next workflow
2. proposed identity (routing only; must be verified before execution)
3. required runtime reads
4. first safe command, usually read-only or `--dry-run`
5. unavailable runtime capability, risk, or missing information

For a composed workflow, also give the ordered steps, dependencies, per-step
outputs/acceptance checks and write boundaries. On completion, distinguish
verified, blocked and uncertain steps; a routed or planned step is not execution.

## Safety

- Read before write. Use `--dry-run` for write, move, delete, send, permission,
  and publish actions.
- A current-turn instruction that specifies the send/reply target and exact
  content normally supplies the bounded business authorization; do not ask for
  a mechanical second confirmation. Ask when the target, content, acting
  representative, or blast radius is ambiguous. A runtime exit-10 gate still
  requires explicit approval of the exact high-risk action before `--yes`.
- Do not add `--yes` after an exit-10 confirmation gate unless the user
  explicitly approves the exact high-risk action.
- Treat writes, deletes, sends, imports, publishes, permission changes, real
  meeting join/leave, and bulk updates as confirmation-required unless the
  official runtime skill says they are safe.
- Preserve Feishu URLs, `verification_url`, and `console_url` exactly; treat
  them as opaque strings and follow the current `lark-shared` QR/split flow.
- Do not expose app secrets, access tokens, cookies, private document content,
  or private URLs in public artifacts.
- Use relative paths under the current working directory for CLI file
  parameters. Do not place private absolute paths into public examples or
  generated documentation.
