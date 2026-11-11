# Feishu Next

**Connect a user's Feishu/Lark operations into complete, verifiable workflows.**
Feishu Next is a Codex V2 plugin-first workflow capability layer, built from
BlueSkyXN's personal playbooks and experience. It adds step order, dependencies,
explicit identity, evidence, validation and partial-failure recovery—not another
copy of official API instructions.

Start with `$feishu-next:feishu-workflow-router` when choosing capabilities or
composing a task, or invoke a matching playbook directly. All eleven skills remain
flat public entries; internal references do not become extra skills. The Router
explains official capabilities through five on-demand domain maps and stays
inside Next:

- Select a reusable Next playbook or compose several operations around the user's
  requested outcome. Keep workflow state and pass verified outputs between steps.
- Navigate to an actually available official **`lark-suite`** for a step's
  capability. The suite owns official guide aggregation and skill-list compression;
  Next owns the enclosing workflow. Atomic requests can go directly to suite.
- Support separate official `lark-*` skills or `lark-cli skills read` when suite
  is not exposed. Never pretend suite is installed, guess a cache path, or copy
  official guides/resources into this repository.
- Reuse official multi-step methods when they already satisfy the request; step
  count alone does not make something a Next workflow. Each playbook refers to
  Router for missing context, capability ambiguity or requested extensions, and
  returns verified outputs without redispatching itself or repeating valid reads.

Current source version: **0.11.0**, with **eleven skills** (Router plus ten
playbooks): exports, slide-preview capture to PDF, document assets, chat archives,
whiteboard visual design and whiteboard/draw.io operations, text-preserving formatting and paste repair, Mindnote outlines and
generic Base snapshots.
Five organization-specific workflows remain private; project-specific snapshot
code is separate from the generic public method. Private adapters, resource maps
and business data are not distributed.

The optional **feishu-traework-local-auth 0.2.1** plugin contributes one more
public skill (**twelve total**) and reuses this machine's user-owned TraeWork
Feishu authorization with official CLI environment credentials. It is not the
default auth path; see its [README](plugins/feishu-traework-local-auth/README.md)
and [project docs](docs/traework-local-auth/).

**Maintenance is user-directed:** AI updates plugins, CLI or skill layouts only
when the user explicitly requests it. Next never installs suite, converts
separate/suite layouts, removes global skills or updates itself automatically.
Reading local runtime help does not modify an installation.

Use `$feishu-next:feishu-whiteboard-semantic-cards` to apply the **Semantic Card
Diagrams** style: organize materials with semantic colors, modular cards and
clear relationship layouts, build
editable local SVG, and inspect rendered previews. It includes a standard-library
Python component kit and synthetic examples. The existing whiteboard operations
playbook owns remote targeting, backups, writes and recovery.

For an explicitly requested screenshot PDF of a viewable slide deck, use
`$feishu-next:feishu-slides-preview-to-pdf`. This browser workflow uses the
selected browser's login state and validates page order, canvas bounds, image
encoding and pixel size. CLI identity is required only if a step uses the CLI.
The output is an image-based PDF; it preserves visible watermarks.

Before committing, run `make validate-privacy`; before a release, also run
`make validate-privacy-history` and check the final ZIP against a reviewed commit.
These local checks cover worktree candidates and staged content without publishing
or using credentials. See [privacy checks and clean packaging](docs/privacy-and-release.md).

See [Chinese installation and usage](README_CN.md),
[plugin details](plugins/feishu-next/README.md),
[workflow and suite boundaries](docs/workflow-architecture.md),
[naming/version rules](docs/skill-governance.md), [public catalog](skill-catalog.json),
[public/private boundaries](docs/skill-migration.md) and [changelog](CHANGELOG.md).
Source changes do not imply publication, installation or live business testing.
