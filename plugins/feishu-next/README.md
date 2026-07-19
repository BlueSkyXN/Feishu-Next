# Feishu Next

Feishu Next is an installable Codex plugin for common Feishu/Lark workflows.
It does not replace the official `lark-cli` skills. It layers reusable workflow
guidance on top of the current `lark-cli` runtime so Codex can execute common
multi-step Feishu tasks with the right identity, permissions, pagination,
export, and evidence boundaries.

Feishu Next `0.2.0` is validated against `lark-cli 1.0.72`. It does not hard
lock that exact version: the router and runtime validator inspect the installed
skills, domain help, shortcut help, and required flags before relying on a
capability.

## Plugin-First Migration

Feishu Next is the plugin replacement for keeping Feishu routing guidance as a
standalone global skill under `~/.codex/skills`. After installing this plugin
through its marketplace, start from `feishu-workflow-router`; it contains the
former guide-level behavior: classify Feishu URLs, pick the official embedded
`lark-*` skill, remind Codex to read `lark-shared`, and route stateful work to
the bundled sub-skills.

Do not copy official `lark-cli` skills into this package. The installed
`lark-cli` remains authoritative for commands, flags, scopes, identities,
current API behavior, and confirmation rules.

## What It Includes

- `feishu-workflow-router`: entrypoint for routing Feishu tasks to the right
  official `lark-*` skill or bundled workflow; use it instead of a standalone
  `lark-cli-guide` in plugin-based Codex sessions. It also handles runtime
  domains without an embedded skill, such as Open Platform `application` slash
  commands, by reading current domain and shortcut help.
- `feishu-readonly-doc-export`: read-only export workflow for doc/docx, sheet,
  bitable, and slides resources.
- `feishu-doc-asset-map`: document asset inventory workflow for images, files,
  whiteboards, and embedded sheet/base references.
- `feishu-im-chat-archive`: IM chat/message archive workflow with pagination,
  resource download boundaries, and evidence-friendly output.
- `feishu-whiteboard-ops`: whiteboard inspect/modify/redraw workflow with raw
  rollback baselines, visual checks, safe write-back strategy, and optional
  `.drawio` source-to-whiteboard publishing discipline.

## Whiteboard Skill Boundary

Feishu Next intentionally keeps one whiteboard workflow skill:
`feishu-whiteboard-ops`.

- Ordinary atomic board query/update commands still come from the official
  embedded `lark-whiteboard` skill, which remains authoritative for command
  names, flags, scopes, identities, and current API behavior.
- Multi-step edit, redraw, recovery, preview/raw backup, and validation loops
  use `feishu-whiteboard-ops`, which is authoritative for workflow discipline:
  target confirmation, rollback baselines, render/check gates, merge strategy,
  and post-write verification.
- `.drawio` / diagrams.net publishing is a conditional reference inside
  `feishu-whiteboard-ops` (`references/drawio-pipeline.md`), not a second
  Feishu Next skill. This keeps routing unambiguous while preserving progressive
  disclosure.

## Runtime Dependency

This plugin expects the official `lark-cli` to be installed and configured:

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
```

When a workflow needs Feishu access, follow the current embedded runtime rules:

```bash
lark-cli skills read lark-shared
lark-cli skills read <lark-domain-skill>
lark-cli whoami
lark-cli auth status --json --verify
```

Use `lark-cli doctor --offline` only when diagnosing local configuration or
runtime health. An older or newer CLI is acceptable when the required runtime
surface passes `python3 scripts/validate_lark_runtime.py`.

## Package Layout

```text
plugins/feishu-next/
  .codex-plugin/plugin.json
  README.md
  skills/
    feishu-workflow-router/
    feishu-readonly-doc-export/
    feishu-doc-asset-map/
    feishu-im-chat-archive/
    feishu-whiteboard-ops/
```

The repo marketplace is outside this package:

```text
.agents/plugins/marketplace.json
```

## Local Install

From a checked-out copy of this repository:

```bash
codex plugin marketplace add /path/to/Feishu-Next
codex plugin list --marketplace feishu-next --available --json
codex plugin add feishu-next@feishu-next
```

Run the first two commands when you only want to confirm marketplace visibility.
Run `codex plugin add` when you want to install the plugin into the current
Codex environment.

When replacing an already installed version, refresh the independent plugin
cache and then verify the installed manifest:

```bash
codex plugin remove feishu-next@feishu-next --json
codex plugin add feishu-next@feishu-next --json
codex plugin list --json
```

After installation, start with:

```text
$feishu-next:feishu-workflow-router
```

Once the plugin is installed and visible from the marketplace, Feishu-specific
global skills under `~/.codex/skills` are no longer needed for normal routing.
Keep any old standalone skill only as a temporary fallback until the plugin has
been reinstalled in the Codex environment you are using.

## Safety Model

- Prefer read-only commands and `--dry-run` before writes.
- Always run the exact prepared whiteboard update with `--dry-run` before any
  additive or overwrite write; clear user intent does not waive payload preflight.
- Use the current `lark-cli skills read ...` output as the runtime truth.
- Do not expose app secrets, access tokens, private URLs, or private document
  contents in public artifacts.
- Stop for explicit user confirmation before sending messages, deleting files,
  changing permissions, moving resources, or adding `--yes`.

## Validate

From the repository root:

```bash
python3 scripts/validate_project.py
python3 scripts/validate_lark_runtime.py
make validate-all
```

The project validator checks marketplace wiring, manifest structure, expected
skill surface, text hygiene, and Codex plugin/skill validators. The separate
runtime validator performs local-only `lark-cli skills read` and `--help`
probes; it does not authenticate, call Feishu APIs, or mutate remote resources.

Release validation requires the Codex plugin and skill validators to be
installed. For a deliberately degraded static-only inspection on another
machine, use:

```bash
python3 scripts/validate_project.py --allow-missing-codex-validators
```

Do not use that option for release checks.
