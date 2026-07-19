---
name: feishu-workflow-router
description: Plugin-first router for Feishu/Lark lark-cli work. Use instead of a standalone lark-cli-guide for any Feishu/Lark URL, token, resource, or lark-cli domain, including documents, Drive, Wiki, Sheets, Base, native Markdown, mindnotes, IM, calendar, mail, tasks, approval, attendance, OKR, meetings, whiteboards, Miaoda/Spark apps, Open Platform slash commands, events, official workflows, custom lark-cli skills, exports, comments, permissions, auth, and scope issues.
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

## First checks

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

Use diagnostics only when their signal is needed:

```bash
lark-cli whoami                         # current effective identity
lark-cli auth status --json --verify   # complete auth/token verification
lark-cli doctor --offline              # local config/runtime diagnosis
```

## Runtime discovery order

1. Identify the resource type from the URL path, token prefix, or user intent.
2. Run `lark-cli skills list` and look for an exact matching official skill.
3. When a matching skill exists, read it and every reference it requires:

   ```bash
   lark-cli skills read <skill>
   lark-cli skills list lark-doc/references
   lark-cli skills read lark-doc references/lark-doc-fetch.md
   ```

4. When the domain exists but has no embedded skill, read the domain and
   shortcut help instead. `application` is the current canonical example; do not invent a `lark-application` skill:

   ```bash
   lark-cli application --help
   lark-cli application +slash-command-list --help
   ```

5. If an optional domain is absent from the current CLI, report that the
   installed runtime does not expose it and suggest `lark-cli update`. Do not
   misclassify an unavailable command as a scope or permission failure.
6. Prefer an exact official runtime workflow when one exists. Use Feishu Next
   only for the stateful workflows explicitly owned by this plugin.
7. Use `lark-openapi-explorer`, `lark-cli schema`, or `lark-cli api` only when
   neither an official skill nor a registered domain/shortcut covers the task.

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

## Resource parsing rules

- `/docx/` and `/doc/`: document content goes through `lark-doc`; export,
  comments, permissions, metadata, and Drive search go through `lark-drive`.
- `/wiki/`: use the domain skill appropriate to the task. `drive +export --url`
  can unwrap Wiki URLs directly; use `drive +inspect` when evidence or explicit
  object type/token is needed.
- `/sheets/`: use `lark-sheets` for internal data and `lark-drive` for export,
  search, comments, permissions, or versions.
- `/base/` or `/bitable/`: use `lark-base` for internal data and management;
  use `lark-drive` for import/export.
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
2. identity assumption (`user` or `bot`)
3. required runtime reads
4. first safe command, usually read-only or `--dry-run`
5. unavailable runtime capability, risk, or missing information

## Safety

- Read before write. Use `--dry-run` for write, move, delete, send, permission,
  and publish actions.
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
