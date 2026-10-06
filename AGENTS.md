# Feishu Next 项目协作规则

本仓库是一个 Codex V2 plugin-first 插件包，目标是把飞书 / Lark 常用工作流沉淀成可安装的 Codex Skills。

## 项目边界

- 生产态入口是 `plugins/feishu-next/`，定位为飞书工作流能力：沉淀个人玩法，把一系列操作串成带依赖、证据、验证和恢复边界的完整任务。仓库 marketplace 是 `.agents/plugins/marketplace.json`，保持 Codex V2 协议。
- 不在仓库根保留裸 `skills/` 目录；共享能力必须进入插件包。
- `feishu-workflow-router` 留在 Next，选择和编排本插件工作流，也支持导航到官方 `lark-suite`。官方负责原子能力与技能清单压缩；本仓库不复制其正文或资源快照，不另建独立 Router 插件。
- Next 保持跨步骤状态和执行上下文；调用官方指南只提供当前步骤的方法，不把整个流程丢给 suite。兼容 separate 技能与 CLI runtime reads，不假定 suite 已安装。
- Router 与七个工作流平铺，内部参考按需加载。Router 说明官方能力与 Next 增量方法；各工作流按需引用 Router、复用有效上下文并回传结果，不循环分派。官方本身的多步方法也直接复用，不按步骤数机械区分官方/Next。
- 仅在用户明确指挥 AI 时更新插件、CLI 或技能布局；不自动更新、下载、安装、移除全局技能。
- 当前安装的 `lark-cli` 是运行时真相源。涉及命令、scope、身份、参数时先用 `lark-cli skills read ...` 或 `lark-cli <domain> --help` 核对。

## 改动原则

- 保持公开安全：不要提交 token、app secret、cookie、私有文档内容、内部 URL、真实导出文件或聊天归档。
- 提交前运行 `make validate-privacy`，发布前增加 `make validate-privacy-history` 并核对最终 ZIP。例外必须绑定具体文件、规则和值哈希，不整目录放行；不以通过扫描代替人工内容审查。
- `/local/` 使用仓库级忽略保护，不删除私人资料来通过检查。发布从审核提交的插件文件与 LICENSE 清单生成，不直接压缩工作目录，详见 `docs/privacy-and-release.md`。
- 写入、删除、发送消息、权限变更、发布、加 `--yes` 这类动作只能作为 workflow 说明，不在验证中真实执行。
- Skill 的 `description` 必须包含触发场景；正文只保留执行所需的核心步骤。
- 命名与版本遵循 `docs/skill-governance.md`：目录与 name 一致，公共技能使用稳定的 `feishu-*` 名称，不带版本后缀；`metadata.version` 使用完整 SemVer，并维护 `metadata.updated`。
- 新增/改名同步 `skill-catalog.json`、Router 工作流入口、README 和 `CHANGELOG.md`。版本真相分别是 plugin manifest 与 Skill metadata，不在公共清单另存版本。
- 公共收录按能力价值，不按“用到了飞书”判断：去掉公司规则和历史案例后，仍须具备独立、可复用的飞书操作方法；泛化后的业务说明不单独注册为公共 Skill。
- 项目专用技能和脚本在原项目正常目录维护；公共能力按需独立提炼，不以薄入口替代仍需独立执行的私有实现。资源映射、业务系统适配器、人员与历史数据不迁入公开仓。
- 迁移或撤回先核对原件哈希，保留可回溯归档；公共包不得反向依赖私有路径，职责不同的本地技能不得登记为公共别名。
- 官方指南按当前实际可用的 suite/separate/runtime 路径按需读取；涉及命令、scope、身份核对当前 runtime reads/help，不在个人玩法中另存官方 API 文档副本。

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
