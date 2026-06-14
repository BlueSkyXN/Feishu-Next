# Feishu Next 项目协作规则

本仓库是一个 Codex V2 plugin-first 插件包，目标是把飞书 / Lark 常用工作流沉淀成可安装的 Codex Skills。

## 项目边界

- 生产态入口是 `plugins/feishu-next/`，仓库 marketplace 是 `.agents/plugins/marketplace.json`。
- 不在仓库根保留裸 `skills/` 目录；共享能力必须进入插件包。
- 不复制官方 `lark-cli` 内嵌 skills 的完整内容；本项目只写组合工作流、路由策略、证据和安全边界。
- 当前安装的 `lark-cli` 是运行时真相源。涉及命令、scope、身份、参数时先用 `lark-cli skills read ...` 或 `lark-cli <domain> --help` 核对。

## 改动原则

- 保持公开安全：不要提交 token、app secret、cookie、私有文档内容、内部 URL、真实导出文件或聊天归档。
- 写入、删除、发送消息、权限变更、发布、加 `--yes` 这类动作只能作为 workflow 说明，不在验证中真实执行。
- Skill 的 `description` 必须包含触发场景；正文只保留执行所需的核心步骤。
- 需要详细 API 说明时，优先引用官方 `lark-*` skill runtime reads，而不是把 API 文档复制进本仓库。

## 验证

改完插件或 skills 后运行：

```bash
python3 scripts/validate_project.py
```

如果只验证插件 manifest：

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/feishu-next
```

如果只验证单个 skill：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/feishu-next/skills/<skill-name>
```
