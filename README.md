# Feishu Next

Feishu Next is a Codex plugin package for common Feishu/Lark workflows powered
by the official `lark-cli` runtime.

It is the plugin-first replacement for standalone Feishu guide skills under
`~/.codex/skills`: install it through the repository marketplace, start from
`$feishu-next:feishu-workflow-router`, and keep official `lark-*` skill details
in the installed `lark-cli` runtime instead of vendoring them here.

An optional sibling plugin, `feishu-traework-local-auth` `0.2.1`, can reuse
this computer's already-granted TraeWork Feishu authorization with official
`lark-cli` environment credentials. Windows looks for `lark-cli.exe`; macOS
and Linux use unsuffixed `lark-cli`. See
[plugins/feishu-traework-local-auth/README.md](plugins/feishu-traework-local-auth/README.md)
and [docs/traework-local-auth/](docs/traework-local-auth/).

For Chinese documentation and local installation steps, see [README_CN.md](README_CN.md).
