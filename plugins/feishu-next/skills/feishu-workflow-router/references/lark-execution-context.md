# lark-cli execution context

Read this reference before any business or lifecycle `lark-cli` invocation,
including current-channel bot work, shared resources, `lark-channel-bridge`, a
system `lark-cli`, authentication, profile selection, identity-policy changes,
a profile or App ID mismatch, or isolated login state.

This reference separates safe discovery from execution. A natural-language
request does not need to contain internal profile or App fields; discover those
fields first, freeze them into an execution contract, and only then run the
business operation.

## Contents

- [Four-stage model](#four-stage-model)
- [Draft and frozen contracts](#draft-and-frozen-contracts)
- [Discovery before question](#discovery-before-question)
- [Expected App anchors](#expected-app-anchors)
- [Context selection](#context-selection)
- [Channel caller responsibilities](#channel-caller-responsibilities)
- [Environment evidence](#environment-evidence)
- [Parameter boundaries](#parameter-boundaries)
- [Preflight and execution](#preflight-and-execution)
- [Error classification](#error-classification)
- [Prohibited recovery](#prohibited-recovery)
- [Diagnostic response](#diagnostic-response)

## Four-stage model

Use these stages in order:

1. **Bootstrap discovery**: inspect the installed runtime, official skills,
   command help, profile candidates, current message resources, and caller
   metadata. This stage does not require a complete `lark_execution` because it
   performs no business call, authentication mutation, or configuration
   mutation.
2. **Draft**: record the proposed context, identity, resource, and operation in
   `lark_execution_draft`. Internal fields may remain `unknown`; a draft never
   authorizes a business call.
3. **Freeze**: select one execution context and profile, establish an
   independent expected App anchor, and resolve the exact command and argv from
   current runtime guidance. Produce a complete `lark_execution`.
4. **Preflight and execute**: verify actual profile, App, identity, and token
   state against the frozen contract. Run the business command only after the
   preflight matches.

The following read-only commands are allowed during bootstrap without a frozen
business contract:

```bash
command -v lark-cli
lark-cli --version
lark-cli skills list
lark-cli skills read <lark-skill>
lark-cli <domain> --help
lark-cli <domain> <command> --help
lark-cli profile list
```

`lark-cli config plugins show` is also discovery-only when distribution policy
diagnostics are needed. Do not run business commands, `auth login`, profile
mutations, or config mutations during bootstrap.

## Draft and frozen contracts

Build a draft from the user's natural language plus discovered evidence:

```yaml
lark_execution_draft:
  context: channel | system | unknown
  profile: string | unknown
  expected_app_id: string | unknown
  expected_app_name: string | unknown
  identity: bot | user | unknown
  resource_owner: bot | user | shared | unknown
  operation:
    domain: string | unknown
    command: string | unknown
    argv: string[] | unknown
```

Before any business, authentication, profile, or identity-policy invocation,
resolve draft fields and freeze the contract. The caller may provide a complete
contract, but an ordinary user must not be required to know raw profile names
or App IDs.

Freeze this contract before the business call:

```yaml
lark_execution:
  context: channel | system
  profile: string
  expected_app_id: string
  expected_app_name: string | unknown
  identity: bot | user
  resource_owner: bot | user | shared | unknown
  operation:
    domain: string
    command: string
    argv: string[]
```

`expected_app_name: unknown` is valid when the caller and runtime do not report
an independently anchored name. `resource_owner: unknown` is valid for a
bounded read or metadata probe when ownership cannot be known before access; it
is not valid for a write whose authorization or representative depends on
ownership. `unknown` is an explicit evidence state, not permission to guess.
Read-only export may retain `resource_owner: unknown` when the selected
representative and authorization do not depend on ownership.

Apply the frozen contract to bot-owned and shared resources as well as
user-owned resources.

## Discovery before question

Use discovery before question:

1. Resolve phrases such as "this document" from the current message, selected
   resource, reply/quote, attachment, incoming event, or supplied URL before
   asking the user for a link.
2. Infer a proposed context and identity from the operation class, not from
   process environment variables.
3. Read the current official skill or command help to resolve the exact domain,
   command, flags, identity support, and risk.
4. For `system`, run `lark-cli profile list` in the system invocation context.
   Select automatically only when one candidate clearly matches the user's
   stated representative. If several candidates represent different business
   identities, show human-readable account/App labels and ask which identity to
   represent. Do not ask the user to supply a raw App ID or profile name.
   If the available labels cannot distinguish the representatives, stop as
   `system_candidate_ambiguous` and request a business-readable account choice
   or richer non-secret caller metadata; do not expose raw selectors as the
   choice interface.
5. Ask only for business information that discovery cannot supply, such as the
   resource, time range, intended representative, target, content, write scope,
   or a choice between materially different accounts.

Do not manufacture `operation.command` or `operation.argv` before reading the
owning runtime skill/help. Do not block bootstrap merely because the draft is
incomplete.

## Expected App anchors

`expected_app_id` is the primary stable App anchor. Establish it before
preflight from one of these independent sources:

- non-secret target App metadata in a channel/caller envelope;
- the user's selection from discovered account/App candidates;
- one unambiguous discovered candidate that matches the explicitly requested
  context and representative, recorded before preflight;
- an already frozen upstream workflow context.

`expected_app_name` may come from the same independent source. If no source
reports a name, keep it `unknown`. An `appName` reported under
`auth status --json --verify` may be recorded as actual evidence, but do not
retroactively use the same preflight value as both expected and actual.

Never copy `config show.appId`, `whoami.appId`, or auth status `appId` from the
current preflight into `expected_app_id` and then claim that the App verified
itself. Freeze the expected anchor first, then compare all available actual
values to it.

## Context selection

Classify the operation before freezing the contract:

| Operation | Proposed context | Proposed identity |
| --- | --- | --- |
| Receive or reply in the current bot conversation | `channel` | `bot` |
| Card callback or application event handling | `channel` | `bot` |
| Bot-owned resources and service-side automation | `channel` | `bot` |
| User Wiki, Docs, Drive, Base, Sheets, calendar, or mail | `system` | `user` |
| Search user-visible IM history | `system` | `user` |
| Shared resource | Choose from the intended representative and actual ownership | Explicitly select |

These are routing proposals, not verified identity facts. The `im` domain is
not globally bot-only or user-only. Route current-channel bot sending
separately from user-visible message search.

## Channel caller responsibilities

For current-channel work, the caller or harness must provide non-secret target
metadata from the incoming event or channel envelope:

- intended `context: channel`;
- expected App ID and, when available, App name;
- intended profile, or enough expected App metadata to resolve exactly one
  profile inside the bound channel config;
- chat, message, or thread target required by the operation;
- the bot representative implied by the event.

Use these values to build the draft and expected App anchor. Use
`LARK_CHANNEL*` only to verify the actual process binding. If the caller omits
the expected App anchor or target ID, stop and request caller metadata; do not
fall back to the system CLI, infer a business target from environment
variables, or read secrets/raw config files to reconstruct it.

## Environment evidence

Use the presence of `LARK_CHANNEL`, `LARK_CHANNEL_PROFILE`,
`LARK_CHANNEL_CONFIG`, and `LARKSUITE_CLI_CONFIG_DIR` only to identify the
actual process binding. Do not treat those variables as the requested target.

When `LARK_CHANNEL=1`, plain `lark-cli` is channel-bound and uses that bridge
profile's private config directory. Do not unset, replace, or bypass the
binding variables. When the frozen contract requests `context: system` but the
current process exposes only the channel profile, stop with
`execution_context_mismatch`; the caller must supply the correct execution
context.

## Parameter boundaries

| Input | Meaning | Does not do |
| --- | --- | --- |
| `context` | Selects the caller-provided execution/config context | It is not a `lark-cli` flag |
| `profile` | Maps to global `--profile` inside the current config directory | It cannot cross config directories |
| `identity` | Maps to `--as user` or `--as bot` inside the selected app | It cannot select another app |
| `expected_app_id` / `expected_app_name` | Assert the resolved app before execution | They do not modify configuration |
| `resource_owner` | Guides bot/user routing based on ownership | A CLI domain name does not override it |
| `operation` | Supplies the business domain, command, and argv | `argv` must not contain shell environment operations |
| `--domain` / `--scope` / `--exclude` | Select OAuth authorization scope | They select OAuth scope, not an app, profile, or user |

The same executable path can be used with different config directories, apps,
profiles, and login states. Do not infer the requested business context from
`command -v lark-cli`.

## Preflight and execution

Run these read-only status commands in the frozen caller-selected context:

```bash
lark-cli --profile <profile> config show
lark-cli --profile <profile> whoami --json
lark-cli --profile <profile> auth status --json --verify
```

Validate all available evidence before the business call:

1. `config show.profile` and `whoami.profile` equal
   `lark_execution.profile`.
2. When `config show.profileSource` or `profile list.effectiveSource` exists,
   record `config`, `flag`, or `environment`. Older runtimes such as `1.0.83`
   may omit both fields; record `unknown/legacy-runtime` and preserve the
   explicit `--profile`, caller context, and binding evidence. Do not block a
   matching legacy runtime solely because this optional field is absent, and
   do not invent a source value.
3. `config show.appId`, `whoami.appId`, and auth status `appId` equal the frozen
   `expected_app_id`.
4. If `expected_app_name` is known and auth status reports an App name, compare
   them. If either side is `unknown`, rely on the App ID as the stable anchor;
   never guess a missing name.
5. `whoami.identity` equals the requested `identity`.
6. The selected identity is ready and verified for the requested operation.
7. Ownership or representative evidence is sufficient for the operation's
   risk. Resolve `resource_owner: unknown` before a write when ownership affects
   authorization.

Only after preflight succeeds, construct the business call without shell
rewriting:

```bash
lark-cli --profile <profile> <domain> <command> <argv...> --as <identity>
```

Require a successful CLI envelope and, when returned, verify its `identity`
matches the contract. A process exit code of zero and `ok == true` are the
success conditions for structured responses.

Preserve `--profile <profile>` and `--as <identity>` on every later command in
the workflow, especially when it consumes an ID, token, task ticket, or
`next_command` derived earlier. A new process does not inherit the prior
identity. If a downstream command rejects the source identity, stop and report
the boundary; do not omit `--as` or switch identities to make the call pass.

Generic first-use authentication guidance from an owning runtime skill applies
only after this context and App preflight succeeds. It never overrides an
`execution_context_mismatch` or `identity_unverified` stop.

## Error classification

Classify failures before suggesting a remedy:

| Classification | Evidence | Required response |
| --- | --- | --- |
| `execution_context_mismatch` | Requested profile is absent, resolved App differs, or channel/system context differs | Stop; return expected and actual non-secret identity metadata |
| `caller_context_incomplete` | Channel caller omitted expected App anchor or message/chat/thread target | Stop; request the missing caller metadata without switching context |
| `system_candidate_ambiguous` | System candidates cannot be distinguished by business-readable account/App labels | Stop; request a representative choice or richer non-secret caller metadata, never a raw selector |
| `bot_backend_scope_missing` | Bot identity plus `app_scope_not_applied`, `missing_scopes`, or `console_url` | Preserve the exact `console_url`; do not run user auth |
| `user_oauth_scope_missing` | App and user identity match, but user OAuth lacks a required scope | Request the narrowest scope only after explicit user confirmation |
| `resource_not_shared` | App and identity match, scopes are sufficient, but the resource denies access | Ask the owner to share or grant access to that identity |
| `identity_unverified` | App ID, profile, identity, or token state cannot be verified | Stop; do not infer success from environment variables |

Do not turn `profile not found` into an auth flow. Do not interpret `--domain`,
`--scope`, or `--exclude` as App-selection parameters.

## Prohibited recovery

On `execution_context_mismatch` or `identity_unverified`, do not run:

```text
lark-cli auth login
lark-cli profile add
lark-cli profile use
lark-cli config bind
lark-cli config strict-mode
lark-cli config default-as
```

Do not unset or override `LARK_CHANNEL`, `LARK_CHANNEL_HOME`,
`LARK_CHANNEL_PROFILE`, `LARK_CHANNEL_CONFIG`, or
`LARKSUITE_CLI_CONFIG_DIR`. Do not read App secrets, tokens, cookies, or raw
credential files to recover an identity.

Identity-policy changes on the correct App still require explicit user intent.
They are not a remedy for selecting the wrong App or config directory.

## Diagnostic response

Return a bounded, non-secret response for stopped operations:

```yaml
classification: execution_context_mismatch
expected:
  context: system
  profile: <requested-profile>
  app_id: <requested-app-id>
  identity: user
actual:
  context: channel
  profile: <resolved-profile-or-unknown>
  app_id: <resolved-app-id-or-unknown>
  identity: <resolved-identity-or-unknown>
action: caller_must_supply_matching_execution_context
```

Never include secrets, access tokens, cookies, verification URLs, private
configuration contents, or unrelated private paths in this diagnostic.
