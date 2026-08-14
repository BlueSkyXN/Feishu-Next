# 参考对象：cockpit-tools（写清楚）

## 它是什么

| 项 | 内容 |
| --- | --- |
| 项目 | [jlcodes99/cockpit-tools](https://github.com/jlcodes99/cockpit-tools) |
| 定位 | 通用 **AI IDE 账号管理** 桌面工具（多平台切号、导入、配额等） |
| 官方支持 OS | macOS、Windows、Linux（其 README 声明） |
| 与飞书关系 | **不提供**飞书 / TraeWork / `lark-cli` 桥接 |

相关公开讨论：

- Issue：[trae 登录失败，以及修复逻辑 #894](https://github.com/jlcodes99/cockpit-tools/issues/894)  
  背景：Trae 本地账号信息从明文变为客户端编码存储后，切号/导入需要按同一格式读写。
- 实现位置（上游）：`crates/cockpit-core/src/modules/trae_account.rs`（及 Tauri 镜像模块）
- 修复类提交说明：*Fix Trae auth cipher storage handling*（将其作为「上游已处理本地会话编码」的证据，而不是攻击教程）

## 他们解决什么问题

1. 在用户本机 **导入 / 切换 / 管理** Trae 套件账号（Trae、TRAE SOLO、Trae CN、TRAE SOLO CN）  
2. 按各 OS 的标准应用数据目录找到 `storage.json`  
3. 读出会话；切号时再写回（含编码格式）  
4. 用会话访问 **Trae 自身** 的账号/配额等接口  

**他们不解决：** 把 TraeWork 的飞书授权交给其它 Agent 或 `lark-cli`。

## 他们怎么测 / 怎么验证（产品侧理解）

| 能力 | 上游如何体现「可用」 |
| --- | --- |
| 跨平台路径 | 代码内 `get_default_trae_data_dir_for_platform`：macOS Application Support、Windows `%APPDATA%`、Linux `~/.config` |
| 本地会话编码 | Issue #894 给出读写逻辑；CHANGELOG 写明「正确处理 iCube 密文记录」；持续发版维护 |
| 导入本机账号 | `import_from_local` / 读 `User/globalStorage/storage.json` |
| 多端用户 | 工具本身以 macOS/Windows/Linux 安装包发布，路径逻辑随版本回归 |

我们 **不** 把上游 issue 里的算法细节复述成「如何攻击 Trae」；只引用其 **已公开、面向账号管理** 的数据目录与只读字段约定。

## 路径约定（我们与上游对齐的部分）

会话文件：

```text
{dataDir}/{AppSupportName}/User/globalStorage/storage.json
```

| OS | `{dataDir}` |
| --- | --- |
| macOS | `~/Library/Application Support` |
| Windows | `%APPDATA%`（Roaming） |
| Linux | `~/.config`（或 `XDG_CONFIG_HOME`） |

`AppSupportName` 示例：`Trae`、`TRAE SOLO`、`Trae CN`、`TRAE SOLO CN`（与上游 `display_name` / `app_support_dir_name` 一致）。

会话键：典型为 `iCubeAuthInfo://icube.cloudide`（忽略 device / usertag 类键）。

字段（只读取值顺序，概念上）：`accessToken` / `token` 及常见嵌套路径。

## 我们复用什么 / 不复用什么

| 项目 | cockpit-tools | 本仓库插件 |
| --- | --- | --- |
| 读本机 Trae 会话 | 有 | 有（只读） |
| 写回 / 切号 | 有 | **无** |
| Trae 配额/签到等 | 有 | 无 |
| `GetThirdPartyToken` → 飞书 UAT | 无 | **有** |
| `LARKSUITE_CLI_*` + `lark-cli` | 无 | **有** |
| 目标用户 | 管多个 AI IDE 账号 | 本机复用 TraeWork 飞书授权 |

```text
cockpit-tools:  本地会话 ⇄ Trae 账号管理
本插件增量:      本地会话 → Trae 云端第三方飞书令牌 → lark-cli 环境凭据
```

## 如何向 Windows 用户说明「参考了谁」

建议话术：

> 本机 Trae 会话文件的位置与开源账号管理工具 cockpit-tools 使用的约定相同：Windows 在 `%APPDATA%\<Trae产品名>\User\globalStorage\storage.json`。  
> 该工具用于 Trae 账号导入/切号；我们的插件 **只读取** 当前用户会话，用于把你已在 TraeWork 里授权过的飞书身份注入本机 `lark-cli`，**不会**改写 Trae 登录文件。

## 引用时注意

- 致谢路径约定与「本地会话编码已被账号工具生态处理」这一事实即可。  
- 不要把本插件描述成 cockpit-tools 的官方功能或分支。  
- 不要在 skill 正文粘贴上游 issue 中的长篇算法常量；算法保留在实现脚本中，文档保持用户操作 + 契约级。  
