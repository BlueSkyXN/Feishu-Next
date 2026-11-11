# Official suite navigation

Feishu Next orchestrates the user's workflow; official `lark-suite` selects and
loads official capabilities. Next does not bundle the suite or try to compress
its own copy of official skill registrations.

## Choose the available route

1. Inspect the skills actually exposed by the host. If `lark-suite` is available,
   load that exact entry using the host's supported mechanism or read its observed
   entry file. Never fabricate a Skill tool call for an unavailable skill.
2. Follow the suite's selected `references/<skill-name>/GUIDE.md`, relative to
   its observed installation directory. Read only the needed guide, prerequisites
   and references. Nested guides are not independent public skills; do not call
   `Skill(lark-doc)` merely because its guide exists inside suite. Do not scan all
   guides or infer a global installation path.
3. When the host uses separate official `lark-*` skills instead, use the selected
   domain skill. Next supports both layouts without converting the installation.
4. When neither layout is exposed, discover and read the binary's embedded
   content with `lark-cli skills list` and `lark-cli skills read <skill>`.
   That list is not a host installation inventory: it does not prove suite is
   present, and `lark-suite` is not assumed to be an embedded runtime skill.
5. Runtime-only reads do not provide every machine resource: the CLI omits skill
   scripts/assets. If an official procedure requires one, use an observed,
   compatible installed official resource or report a dependency gap. Do not
   skip mandatory checks, invent a path, or silently install missing resources.

## Return to the enclosing workflow

Navigation means loading the step's official procedure, not changing the overall
owner. Carry the frozen `lark_execution`, exact target/range, authorized effects
and needed outputs into each step. Return IDs, revisions, artifacts and validation
results to Next's step ledger. Preserve stronger caller backup/evidence rules.
If this Router was called only for a preflight, return to the active playbook
without sending it through the full workflow selection again.

Current CLI skills/help remain authoritative for commands, flags, scopes,
identities, risk labels and available domains. Verify discrepancies between
installed suite guides and the executing binary; do not reread both entire trees.
A guide present in suite never overrides distribution policy or enables a
command absent from the current runtime.

## No automatic maintenance

Updates and separate/suite layout changes occur only when the user explicitly
directs AI to perform them. Ordinary business requests, missing capabilities and
version notices do not authorize `lark-cli update`, installing/removing skills,
changing client settings, or updating Next.

Official layout conversion is not a harmless discovery command: the suite path
can install the aggregated entry and remove prior separate registrations. Do
not run it as a validation step or prerequisite without user authorization.
Keep any user's disabled skills disabled. Next neither installs suite nor
modifies global skill directories.
