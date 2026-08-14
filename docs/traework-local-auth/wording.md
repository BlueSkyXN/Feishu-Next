# 公开用词规范

目的：准确描述「用户在自己电脑上复用自己已完成的 TraeWork 飞书授权」，避免被误读为攻击、盗用或绕过鉴权。

## 推荐说法

| 场景 | 推荐表述 |
| --- | --- |
| 整体能力 | 复用本机已完成的 TraeWork 飞书授权 |
| 数据来源 | 读取当前系统用户的 Trae 客户端本地会话（只读） |
| 令牌 | 用户已授权给 TraeWork 的短时飞书用户访问令牌 |
| 注入方式 | 通过官方 `lark-cli` 环境变量凭据模式（`LARKSUITE_CLI_*`） |
| 范围 | 同一台机器、同一 OS 用户、可选/高级能力 |
| 非目标 | 非 Feishu Next 默认鉴权；非多人共享公共应用 |
| 参考实现 | 与开源 Trae 账号管理工具在 **本机数据目录约定** 上对齐；本插件只读、不切号 |
| 失败引导 | 请在 Trae 内重新完成飞书授权，或改用自建飞书应用 |

## 禁止说法

| 避免 | 原因 |
| --- | --- |
| 破解 / 脱壳 / 逆向攻击 | 把用户自有会话读取说成攻击 |
| 盗 token / 偷登录态 | 主体是用户自己的机器与账号 |
| 绕过 OAuth / 免授权 | 用户已在 TraeWork 流程中完成飞书同意 |
| 白嫖 App / 官方公共共享 App | TraeWork client id 是产品应用身份，不是开放给任意第三方的公共池 |
| 劫持 CLI / 伪造官方通道 | 使用的是文档化的环境变量凭据注入 |
| 给别人用你的 Trae 号 | 超出本机自用边界 |

## 分层表述模板

**产品一句话（README / marketplace）：**

> Optional helper to reuse **your own** (user-owned) TraeWork Feishu authorization on **this machine** with official `lark-cli` environment credentials.

**Skill description（Use when）：**

> Use when the user already authorized Feishu for TraeWork inside a Trae client on the same computer and wants local agents or `lark-cli` to use that same TraeWork app identity…

**技术说明（architecture，仍避免攻击口吻）：**

> The helper reads the current user's Trae session file from the OS app-data location, requests the third-party Feishu token already associated with TraeWork for that user, and injects `LARKSUITE_CLI_APP_ID` / `USER_ACCESS_TOKEN` / `BRAND`.

## Client id 怎么写

- TraeWork 的 `cli_…` 是 **应用 client id（非 app secret）**，可在契约文档中写明。
- 禁止在文档中出现真实 JWT、UAT、refresh token、app_secret 样例。

## 审阅检查清单

- [ ] 未出现「破解 / 盗取 / 绕过 OAuth」等词  
- [ ] 主语是「用户自己的本机会话」  
- [ ] 标明 optional / 非默认鉴权  
- [ ] 标明只读、不写回 Trae 账号存储  
- [ ] 长期方案指向自建飞书应用  
