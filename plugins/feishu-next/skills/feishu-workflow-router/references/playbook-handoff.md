# Playbook and Router cooperation

All seven Next playbooks remain independent public skills. Mentioning
`$feishu-next:feishu-workflow-router` makes their shared navigation and execution
rules discoverable; it does not require an extra Router invocation for every
operation, page or retry. A reference read is sufficient when only a shared rule
is needed; use a host Skill tool only for an actually exposed entry.

## Direct invocation

If the request matches the selected playbook, keep it as the active method.
Before any business call, establish the `lark_execution` contract using
[lark-execution-context.md](lark-execution-context.md) when no matching verified
context is available. Discover internal profile/App fields rather than asking an
ordinary user to name them. Capability selection or a purely local draft does
not itself require authentication or a business call.

When official capabilities or task ownership are unclear, consult the Router's
[capability overview](../SKILL.md#official-capability-overview) and read only the
relevant map. Use [official-suite-navigation.md](official-suite-navigation.md)
to find selected official instructions in the host's actual suite/separate
layout, or the runtime. Do not load all maps or both copies of an already-current
guide. Runtime command/help checks remain necessary for executable details.

## Invocation within an existing workflow

Reuse the caller's verified context only while its binary/config binding,
profile, expected App, identity, target and authorized scope still apply. Carry
the current step's operation into the contract; inherited context is not blanket
authorization for a new write. Revalidate changed/uncertain fields and obey
revision, payload, dry-run and runtime confirmation gates.

Return to the active playbook after a context or capability check. The Router
must not redispatch that same active playbook. Do not restart the overall plan,
repeat discovery for each page, ask again for known inputs or change identity
merely because a different guide was loaded.

If a user adds another requested task, ask the Router to extend only the required
step dependencies and boundaries. Carry verified results forward instead of
re-running completed steps. Do not add sending, publishing, scheduling or
permission changes just because a playbook produced a useful artifact.

## Result handoff

Return the exact resource/artifact identifiers, verified output, evidence paths,
completeness, relevant revisions and any blocked or uncertain result. Keep private
values in the current task, not in public plugin content. Downstream work uses
only verified outputs and cannot infer success from a planned command.

Official workflows can already be multi-step. Use them when they fully satisfy
the request; use Next when its distinct method or the user's explicit choice
requires additional fidelity, evidence, backups, recovery or cross-task state.
