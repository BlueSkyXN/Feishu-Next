---
name: feishu-workflow-router
description: Plugin-first router for Feishu/Lark lark-cli work. Use when handling any Feishu/Lark URL, token, resource, or lark-cli domain, including documents, Drive, Wiki, Sheets, Base, native Markdown, mindnotes, IM, calendar, mail, tasks, approval, attendance, OKR, meetings, whiteboards, Miaoda/Spark apps, Open Platform slash commands, events, official workflows, custom lark-cli skills, exports, comments, permissions, auth, and scope issues; use it instead of a standalone lark-cli-guide. Also use for lark-channel-bridge or system CLI context selection, LARK_CHANNEL detection, App ID or profile mismatches, isolated login states, and bot-versus-user routing; before concluding lark-cli cannot do something; and before any browser or UI-automation fallback that touches a Feishu/Lark resource.
---

# Feishu workflow router

Use this as the Feishu Next entrypoint. The runtime truth is the installed
`lark-cli`, not this repository or older local source trees.

This skill supersedes the standalone global `lark-cli-guide` for installed
Feishu Next usage. Keep Feishu-specific guidance in this plugin so Codex can
discover it through the marketplace, while continuing to read official
embedded `lark-*` skills at runtime. Do not copy or vendor official `lark-*`
skill bodies into this plugin.

## Authority model

Use official runtime guidance and Feishu Next together, but keep their
responsibilities separate:

| Authority | Owns |
| --- | --- |
| Latest user instruction | target resource, business intent, risk acceptance |
| Official `lark-cli skills read <lark-*>` output | skill-owned commands, flags, identity behavior, scopes, risk labels, API support, error handling |
| Current `lark-cli <domain> --help` / shortcut help | domains or commands that do not have an embedded skill, plus current command availability |
| `feishu-workflow-router` | resource classification, runtime discovery, official skill selection, workflow handoff |
| Feishu Next sub-skills | cross-step order, evidence capture, backups, validation gates, local artifact boundaries |
| Feishu Next references | optional branch details loaded only when their trigger is present |

If official runtime guidance conflicts with this repository on command syntax,
scope, identity, or supported behavior, follow the current runtime. If the
conflict is about workflow discipline such as backup-before-write, pagination,
export evidence, or post-write validation, keep the Feishu Next guardrail
unless the user explicitly accepts the risk.

## Bootstrap discovery

Bootstrap is read-only and does not require a complete business contract. Use
it to turn an ordinary natural-language request into a proposed
`lark_execution_draft`; do not ask the user for raw profile names or App IDs.

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

If `lark-cli` is missing, stop and explain that Feishu Next requires the
official CLI. Do not infer installed capabilities from this repository.

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
2. Run `lark-cli skills list` and look for an exact matching official skill.
3. When a matching skill exists, read it and every reference it requires:

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
6. Prefer an exact official runtime workflow when one exists. Use Feishu Next
   only for the stateful workflows explicitly owned by this plugin.
7. Use `lark-openapi-explorer`, `lark-cli schema`, or `lark-cli api` only when
   neither an official skill nor a registered domain/shortcut covers the task.
   `lark-cli api` has only a generic `Risk: write` classification and cannot
   infer whether an arbitrary endpoint is destructive. For raw
   `POST`/`PUT`/`PATCH`/`DELETE`, classify the business action yourself, use
   `--dry-run`, and obtain the same explicit confirmation that the equivalent
   typed write or high-risk write would require.

## Capability gaps and UI fallback

When a required step looks unsupported by the current CLI, do not switch tools
silently. Escalate in this order:

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
5. Do not encode a browser fallback into reusable skills, templates, or docs
   as a normal step. Record it as a temporary workaround tied to the proven
   gap and the `lark-cli` version, so it is re-checked when the CLI updates.

An unavailable command is a capability gap, not a scope or permission failure;
report it as such.

## Atomic routing

| User intent | Read first | Typical command family |
| --- | --- | --- |
| Document read/edit/media, Docx cover | `lark-doc` | `lark-cli docs ...` |
| Mindnote content or nodes | `lark-doc` | `lark-cli mindnotes ...` |
| Drive search/import/export/comments/permissions/secure labels/versions | `lark-drive` | `lark-cli drive ...` |
| Locate Docx text from review comments | `lark-drive`, then `references/lark-drive-comment-location.md` | `lark-cli drive +list-comments --need-relation ...` |
| Native Drive Markdown create/fetch/patch/diff | `lark-markdown` | `lark-cli markdown ...` |
| Wiki spaces, members, nodes, move/copy/move-to-drive | `lark-wiki` | `lark-cli wiki ...` |
| Sheets cells, formulas, charts, pivots, formatting | `lark-sheets` | `lark-cli sheets ...` |
| Base records, fields, views, dashboards, workflows, forms, roles/permissions | `lark-base` | `lark-cli base ...` |
| IM messages, chats, resources, cards, reactions | `lark-im` | `lark-cli im ...` |
| Calendar events and meeting rooms | `lark-calendar` | `lark-cli calendar ...` |
| Mail read, draft, send, reply | `lark-mail` | `lark-cli mail ...` |
| Tasks, task lists, subtasks, task agents | `lark-task` | `lark-cli task ...` |
| Approval definitions, instances, and approval tasks | `lark-approval` | `lark-cli approval ...` |
| Personal attendance records | `lark-attendance` | `lark-cli attendance ...` |
| OKR objectives, KRs, alignments, and progress | `lark-okr` | `lark-cli okr ...` |
| Minutes upload/search/content/permission | `lark-minutes` | `lark-cli minutes ...` |
| Known meeting note ID or transcript | `lark-note` | `lark-cli note ...` |
| Ended meetings and meeting artifacts | `lark-vc` | `lark-cli vc ...` |
| Live meeting join/leave/events/messages/reactions | `lark-vc-agent` | `lark-cli vc ...` |
| Slides create/read/edit/lint/XML workflows | `lark-slides` | `lark-cli slides ...` |
| Whiteboards | `lark-whiteboard` | `lark-cli whiteboard ...` |
| Contact lookup | `lark-contact` | `lark-cli contact ...` |
| Miaoda/Spark development, deploy, DB, files, keys, observability, env, roles, automation | `lark-apps` | `lark-cli apps ...` |
| Open Platform app slash commands | domain help; no `lark-application` skill | `lark-cli application ...` |
| Events and subscriptions | `lark-event` | `lark-cli event ...` |
| Create a reusable custom lark-cli skill | `lark-skill-maker` | follow the runtime skill |
| Unsupported raw API | `lark-openapi-explorer` | `lark-cli schema ...`, then `lark-cli api ...` |

## Official workflow routing

Prefer an official workflow skill when the user request matches it exactly:

| User intent | Use |
| --- | --- |
| Summarize meetings over a time range | `lark-workflow-meeting-summary` |
| Combine calendar agenda and incomplete tasks into a standup report | `lark-workflow-standup-report` |

Do not replace an exact official workflow with a new Feishu Next skill.

## Feishu Next workflow routing

Use Feishu Next for the reusable, stateful workflows it explicitly owns:

| Workflow signal | Use |
| --- | --- |
| Export a doc/sheet/base/slides file with artifact evidence | `$feishu-next:feishu-readonly-doc-export` |
| Inventory document assets or embedded resources | `$feishu-next:feishu-doc-asset-map` |
| Archive IM history with pagination/evidence | `$feishu-next:feishu-im-chat-archive` |
| Modify, redraw, recover, or validate a whiteboard | `$feishu-next:feishu-whiteboard-ops` |
| Publish/sync `.drawio` or diagrams.net to a Feishu whiteboard | `$feishu-next:feishu-whiteboard-ops` |

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
