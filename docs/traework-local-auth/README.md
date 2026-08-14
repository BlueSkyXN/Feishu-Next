# TraeWork 本机授权复用（项目文档）

本目录是 **仓库级说明**，与 Codex skill 本体分离。

## Layers

| Layer | 路径 | 写什么 |
| --- | --- | --- |
| **Skill 本体** | `plugins/feishu-traework-local-auth/skills/...` | Agent 执行步骤、命令、硬规则、路径/环境契约（短） |
| **插件入口** | `plugins/feishu-traework-local-auth/README.md` | 安装、依赖、一句话定位 |
| **项目文档（本目录）** | `docs/traework-local-auth/` | 用词规范、参考对象说明、架构与验证记录 |

Skill 安装后应能独立完成 `status` / `whoami`；本目录给维护者、审阅者和需要「为什么可以这样做」的读者。

## 文档索引

| 文件 | 内容 |
| --- | --- |
| [wording.md](wording.md) | 公开用词规范：推荐说法 / 禁止说法 |
| [reference-cockpit-tools.md](reference-cockpit-tools.md) | 参考对象 cockpit-tools 是什么、他们解决什么、我们复用什么、差异是什么 |
| [architecture.md](architecture.md) | 架构分层、跨平台路径、验证结论、边界 |

## 一句话定位（对外可用）

> 若你已在 **本机** Trae 客户端完成飞书（TraeWork）授权，可选插件可在 **同一台机器** 上，用 **当前系统用户自己的** 登录会话，取回你已同意给 TraeWork 的短时飞书用户令牌，并通过官方 `lark-cli` 的环境变量凭据模式注入，供本机 Agent 使用。  
> 这不是默认鉴权路径；不是共享给第三方的公共应用；长期多人请自建飞书应用。

## 插件与脚本

- 插件：`plugins/feishu-traework-local-auth/`
- 脚本：`plugins/feishu-traework-local-auth/skills/feishu-traework-local-auth/scripts/traework_local_auth.py`
- 调用：`$feishu-traework-local-auth:feishu-traework-local-auth`
