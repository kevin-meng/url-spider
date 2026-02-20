---
title: OpenClaw 多 Agent 配置实战：踩坑指南与最佳实践如果你已经用了一段时间 OpenClaw，肯定会遇到这样的 - 掘金
source: https://juejin.cn/post/7605810996125548578
author: [[]]
published: published
created: 2026-02-19 18:43:59.007808
description: 如果你已经用了一段时间 OpenClaw，肯定会遇到这样的需求：我需要一个专门写博客的 AI 助手，一个写小说的，一个做代码开发的……每个都有独立的角色定位、工作目录和配置。这就是多 Agent 配置
TODO: 
notes: 
标星: 
是否已读: 
概要: "[OpenClaw]多Agent配置实战指南，涵盖创建独立角色Agent、配置工作目录、模型设置、[Telegram]多账号路由等流程，并详细说明config.patch整体替换、dmPolicy默认值、BOOTSTRAP.md卡住、[Telegram]409冲突等常见坑及解决方案。"
tags:
  - 多Agent配置
  - OpenClaw
  - Telegram Bot
  - 配置教程
  - 最佳实践
人物: 
组织公司: 
产品服务: "OpenClaw#Telegram#WhatsApp"
概念实体: "多Agent配置#SOUL.md#BOOTSTRAP.md#dmPolicy#Workspace#Model#Tool Policy#bindings#路由规则"
地点: 
事件: 
书籍: 
相关问题: 如何创建多个独立角色的Agent？;如何配置Telegram bot路由到不同Agent？;config.patch为什么会把配置冲掉？;为什么Agent会卡在bootstrapping状态？;Telegram bot不响应消息怎么办？
原则库: |
  1. 配置变更前先备份 - 任何config.patch、gateway restart等操作前，先用openclaw config get导出当前配置，避免误操作导致配置丢失。
  2. 嵌套对象需完整替换 - config.patch对嵌套对象是整体替换而非增量，patch accounts、bindings等时必须带完整对象。
  3. 分阶段逐步配置 - 先本地测试单个Agent，验证通过后再添加Telegram bot，逐步扩展以降低排查难度。
问题库: |
  - 错误：直接patch嵌套对象的单个子项（如只patch accounts.blog） → 教训：patch嵌套对象时必须包含完整对象结构，或先导出配置编辑后再patch回去。
  - 错误：手动创建BOOTSTRAP.md导致Agent一直卡在启动状态 → 教训：BOOTSTRAP.md是Agent的初始化任务清单，手动创建不完整文件会导致Agent永远无法进入正常状态，应删除或保持空白。
  - 错误：dmPolicy使用默认值pairing导致消息被静默丢弃 → 教训：明确设置dmPolicy为allowlist并配置allowFrom列表，确保消息能正常接收。
生命之花: 职业发展 - OpenClaw作为AI助手工具，可提升技术写作、代码开发等工作效率，直接服务于职业能力提升。
四精练: |
  思维模型：配置继承与覆盖模型 - 理解顶层配置与account级别配置的继承关系，避免配置冲突和混淆。
  行动杠杆点：分阶段配置流程 - 通过先本地测试再逐步添加channel的方式，降低配置复杂度，提升排查效率。
量化的结论:
点子库: |
  ## 认知和创业领导力
  - 领域：认知和创业领导力
  - 点子标题：从踩坑中提炼可复用的配置方法论
  - 核心内容：文章详细记录了config.patch陷阱、BOOTSTRAP.md卡住、dmPolicy默认值、Telegram 409冲突等实际踩坑经验及解决方案
  - 对我的价值：学习如何将实战经验系统化整理成可复用指南，提升问题排查和知识沉淀能力
  - 行动建议：建立自己的工具配置踩坑记录文档，类似本文风格整理常用开发工具的配置要点
  
  ## 金融风控技能
  - 领域：金融风控技能（模型、算法、风险管理）
  - 点子标题：配置策略的分层继承思想可应用于风控规则管理
  - 核心内容：OpenClaw的配置存在顶层默认与account级别覆盖的继承关系，类似风控规则的系统默认与特定规则的分层配置
  - 对我的价值：理解分层配置思想，可应用于风控系统中通用规则与特定场景规则的层级管理
  - 行动建议：设计风控规则时，明确区分全局默认规则和特定规则，覆盖关系需清晰文档化
  
  ## 写作《AI提升效率》《向AI学习》
  - 领域：写作《AI提升效率》《向AI学习》
  - 点子标题：AI工具的多角色配置实战指南素材
  - 核心内容：OpenClaw多Agent配置完整教程，包含创建Agent、模型设置、SOUL.md角色定义、Telegram多账号路由、常见问题排查等
  - 对我的价值：提供AI助手配置这一具体场景的详细操作案例，可作为AI工具使用教程的写作素材
  - 行动建议：以此文结构为参考，撰写类似的多Agent AI助手配置教程或向AI学习Prompt工程实践文章
socre: 5
reason: 文章聚焦于OpenClaw这个特定AI助手工具的配置使用，虽有一定技术价值但属于较为小众的工具教程。与我的核心关注领域（金融风控、认知创业、写作投资）直接相关性较低，分数偏低以示区别。
---

如果你已经用了一段时间 OpenClaw，肯定会遇到这样的需求：我需要一个专门写博客的 AI 助手，一个写小说的，一个做代码开发的……每个都有独立的角色定位、工作目录和配置。这就是多 Agent 配置要解决的问题。

本文不是理论教程，而是实战踩坑记录。我会告诉你配置过程中会遇到哪些坑，为什么会踩坑，以及怎么避免和解决。

## 为什么需要多 Agent

**场景隔离**。不同的工作场景需要不同的 AI 助手：

**博客助手**：专注于技术写作，熟悉你的博客部署流程，有独立的文章草稿目录**小说助手**：创意写作风格，管理小说章节和人物设定，不需要访问技术代码**开发助手**：熟悉代码规范，可以执行敏感命令，但不应该访问私人笔记**家庭助手**：绑定到家庭 WhatsApp 群，只能访问受限的工具集，保护隐私

**独立配置**。每个 Agent 有自己的：

**Workspace**：独立的工作目录，互不干扰**SOUL.md**：独立的角色定位和性格设定**Model**：可以给不同 Agent 配置不同模型（Opus 做深度思考，Sonnet 做日常聊天）**Tool Policy**：限制某些 Agent 的工具权限（比如家庭助手不能执行 shell 命令）

**账号路由**。多个 Telegram bot 或 WhatsApp 账号，路由到不同的 Agent，一个 Gateway 管理所有账号。

举个例子，你可能会配置这样的 Agent：

`main`

：日常聊天，全功能`work`

：工作场景，可以访问项目文档`creative`

：创作助手，专注于写作`coding`

：开发助手，执行代码相关任务

## 多 Agent 配置流程

### 1. 创建 Agent

`bash 体验AI代码助手 代码解读复制代码````
# 创建一个新 Agent
openclaw agents add blog --workspace ~/.openclaw/workspace-blog
# 验证创建结果
openclaw agents list
```


这会在配置文件中添加：

json5体验AI代码助手代码解读复制代码`{ agents: { list: [ { id: "main", default: true, workspace: "~/.openclaw/workspace", }, { id: "blog", workspace: "~/.openclaw/workspace-blog", }, ], }, }`


### 2. 设置模型

**⚠️ 第一个坑：模型 ID 格式**

配置模型时，要用**别名**，不要带日期后缀！

`bash 体验AI代码助手 代码解读复制代码````
# ✅ 正确：使用别名
openclaw config patch agents.list.1.model "anthropic/claude-sonnet-4-5"
# ❌ 错误：带日期后缀的完整 ID
openclaw config patch agents.list.1.model "anthropic/claude-sonnet-4-20250514"
```


**为什么？**

带日期的 ID 会在新版本发布时失效。别名（如 `claude-sonnet-4-5`

）会自动指向最新版本。

验证配置：

`bash 体验AI代码助手 代码解读复制代码````
openclaw config get agents.list.1.model
# 应该输出：anthropic/claude-sonnet-4-5
```


### 3. 编写 SOUL.md 定义角色

每个 Agent 的 workspace 下创建 `SOUL.md`

，定义它的角色：

`bash 体验AI代码助手 代码解读复制代码````
cd ~/.openclaw/workspace-blog
```


创建 `SOUL.md`

：

`markdown 体验AI代码助手 代码解读复制代码````
# SOUL.md - 工作助手
你是工作助手，帮助处理日常工作任务。
## 角色定位
- 专注于工作场景，风格专业高效
- 熟悉常用开发工具和工作流程
- 所有重要操作需要确认后执行
## 工作流程
1. 接收任务需求
2. 分析任务并制定执行计划
3. 执行任务
4. 汇报结果
## 工作规范
- 代码示例要完整可用
- 文档结构清晰
- 操作前确认权限
```


**⚠️ 第二个坑：不要创建 BOOTSTRAP.md**

如果你手动创建了 `BOOTSTRAP.md`

，Agent 会一直卡在 bootstrapping 状态！

**为什么？**

`BOOTSTRAP.md`

是 Agent 的"初始化任务清单"。Agent 启动后会执行里面的指令，执行完才会删除这个文件。如果你手动创建了这个文件但内容不完整，Agent 会不断尝试执行，永远无法进入正常状态。

**解决方法：**

`bash 体验AI代码助手 代码解读复制代码````
# 如果发现 Agent 卡住了，检查是否有 BOOTSTRAP.md
ls ~/.openclaw/workspace-blog/BOOTSTRAP.md
# 如果存在，直接删除
rm ~/.openclaw/workspace-blog/BOOTSTRAP.md
# 重启 Gateway
openclaw gateway restart
```


### 4. 测试 Agent

`bash 体验AI代码助手 代码解读复制代码````
# 列出所有 Agent
openclaw agents list
# 查看 Agent 详细配置
openclaw config get agents.list.1
# 重启 Gateway 让配置生效
openclaw gateway restart
```


## Telegram 多账号配置

多 Agent 的典型用法是配置多个 Telegram bot，每个 bot 路由到不同的 Agent。

### 1. 创建 Telegram Bot

在 Telegram 找 [@BotFather](https://link.juejin.cn?target=https%3A%2F%2Ft.me%2FBotFather)，创建 bot：

bash体验AI代码助手代码解读复制代码`/newbot`


按提示输入名称和用户名，获得 token（类似 `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

）。

假设你创建了两个 bot：

`@MyMainBot`

→ token1`@MyWorkBot`

→ token2

### 2. 配置多账号

编辑 `~/.openclaw/openclaw.json`

（或用 `openclaw config patch`

）：

json5体验AI代码助手代码解读复制代码`{ channels: { telegram: { accounts: { main: { token: "token1", dmPolicy: "allowlist", allowFrom: ["123456789"], // 你的 Telegram user ID }, blog: { token: "token2", dmPolicy: "allowlist", allowFrom: ["123456789"], }, }, }, }, }`


**⚠️ 第三个坑：dmPolicy 默认值**

如果不设置 `dmPolicy`

，默认是 `pairing`

，这意味着用户必须先执行 `/pair`

命令才能聊天。但如果配置有问题，`/pair`

可能也不会响应，消息会被**静默丢弃**！

**解决方法：**

明确设置 `dmPolicy: "allowlist"`

，并配置 `allowFrom`

列表：

json5体验AI代码助手代码解读复制代码`{ dmPolicy: "allowlist", allowFrom: ["123456789", "987654321"], // 允许的 user ID 列表 }`


获取你的 Telegram user ID：给 [@userinfobot](https://link.juejin.cn?target=https%3A%2F%2Ft.me%2Fuserinfobot) 发消息。

### 3. 配置路由规则

添加 `bindings`

将不同的 Telegram 账号路由到不同的 Agent：

json5体验AI代码助手代码解读复制代码`{ bindings: [ { agentId: "main", match: { channel: "telegram", accountId: "main" }, }, { agentId: "blog", match: { channel: "telegram", accountId: "blog" }, }, ], }`


**路由规则优先级**：

`peer`

精确匹配（具体的 DM 或群组 ID）`accountId`

匹配（哪个 Telegram 账号）`channel`

匹配（哪个平台）- 默认 Agent（
`default: true`

或列表中第一个）

### 4. 重启 Gateway

`bash 体验AI代码助手 代码解读复制代码````
openclaw gateway restart --reason "添加新 Telegram bot"
```


测试：给两个 bot 发 `/start`

，应该分别收到来自不同 Agent 的回复。

## 常见问题与解决

### 问题 1：config.patch 把配置冲掉了

**现象：**

我想给 `telegram.accounts`

添加一个新账号，执行：

`bash 体验AI代码助手 代码解读复制代码````
openclaw config patch channels.telegram.accounts.blog '{"token":"xxx"}'
```


结果其他账号的配置全没了！

**原因：**

`config.patch`

对**嵌套对象**是**整体替换**，不是增量修改！

如果配置是：

json5体验AI代码助手代码解读复制代码`{ channels: { telegram: { accounts: { main: {...}, novel: {...}, }, }, }, }`


执行 `patch channels.telegram.accounts.blog {...}`

会导致：

json5体验AI代码助手代码解读复制代码`{ channels: { telegram: { accounts: { blog: {...}, // 只剩这一个！ }, }, }, }`


**解决方法：**

patch 时带上**完整的对象**：

`bash 体验AI代码助手 代码解读复制代码````
# ❌ 错误：只 patch 一个子项
openclaw config patch channels.telegram.accounts.blog '{"token":"xxx"}'
# ✅ 正确：patch 整个 accounts 对象
openclaw config patch channels.telegram.accounts '{
"main": {"token":"token1", "dmPolicy":"allowlist", "allowFrom":["123456789"]},
"blog": {"token":"token2", "dmPolicy":"allowlist", "allowFrom":["123456789"]}
}'
```


同样适用于 `bindings`

、`agents.list`

等数组或对象。

**最佳实践：**

配置变更前，先导出当前配置：

`bash 体验AI代码助手 代码解读复制代码````
# 导出当前配置
openclaw config get channels.telegram.accounts > telegram-accounts-backup.json
# 编辑后再 patch 回去
openclaw config patch channels.telegram.accounts "$(cat telegram-accounts-edited.json)"
```


### 问题 2：Telegram bot 不响应消息

**现象：**

给 bot 发 `/start`

或任何消息，都没有回复。

**可能的原因 1：dmPolicy 配置问题**

检查配置：

bash体验AI代码助手代码解读复制代码`openclaw config get channels.telegram.accounts.blog.dmPolicy`


如果是 `pairing`

或未设置，改成 `allowlist`

：

`bash 体验AI代码助手 代码解读复制代码````
openclaw config patch channels.telegram.accounts.blog.dmPolicy '"allowlist"'
openclaw config patch channels.telegram.accounts.blog.allowFrom '["123456789"]'
openclaw gateway restart
```


**可能的原因 2：Telegram 409 冲突**

**症状：** 日志中有 `getUpdates conflict (409)`

错误。

**原因：** 同一个 bot token 被多个实例同时使用！常见场景：

- OpenClaw.app (GUI) 和 CLI gateway 同时运行
- 两个 terminal 同时启动了 gateway

**检查：**

bash体验AI代码助手代码解读复制代码`ps aux | grep -i openclaw`


如果看到多个进程（GUI app 和 CLI gateway），说明冲突了。

**解决方法：**

- 退出 OpenClaw.app (GUI)
- 重启 CLI gateway：

`bash 体验AI代码助手 代码解读复制代码````
openclaw gateway restart --reason "清除 Telegram bot 冲突"
```


**教训：**

同一个 Telegram bot token **只能被一个 Gateway 实例使用**。如果要切换 GUI/CLI，必须先停掉其中一个。

### 问题 3：绑定规则不生效

**现象：**

配置了 `bindings`

，但消息还是路由到了错误的 Agent。

**检查绑定：**

bash体验AI代码助手代码解读复制代码`openclaw agents list --bindings`


**常见错误：**

**顺序错误**：更具体的规则要放在前面

json5体验AI代码助手代码解读复制代码`// ❌ 错误：通配规则在前，精确规则在后 bindings: [ { agentId: "main", match: { channel: "telegram" } }, // 会匹配所有 telegram 消息 { agentId: "blog", match: { channel: "telegram", accountId: "blog" } }, // 永远不会执行 ] // ✅ 正确：精确规则在前 bindings: [ { agentId: "blog", match: { channel: "telegram", accountId: "blog" } }, { agentId: "main", match: { channel: "telegram", accountId: "main" } }, ]`


**accountId 拼写错误**：检查是否与`channels.telegram.accounts`

中的 key 一致

`bash 体验AI代码助手 代码解读复制代码````
# 列出所有配置的账号
openclaw config get channels.telegram.accounts | jq 'keys'
```


### 问题 4：Agent 配置变更后不生效

**解决方法：**

Gateway 需要重启才能加载新配置：

`bash 体验AI代码助手 代码解读复制代码````
openclaw gateway restart --reason "更新 Agent 配置"
```


检查 Agent 是否正常启动：

bash体验AI代码助手代码解读复制代码`openclaw status --deep`


如果看到某个 Agent 状态异常，查看日志：

`bash 体验AI代码助手 代码解读复制代码````
tail -n 100 ~/.openclaw/gateway.err.log
```


### 问题 5：配置了嵌套对象，但只有部分生效

**现象：**

我在顶层配置了 `channels.telegram.dmPolicy`

，为什么某个账号还是用了不同的策略？

**原因：**

配置有**继承关系**，account 级别的配置会**覆盖**顶层配置：

json5体验AI代码助手代码解读复制代码`{ channels: { telegram: { dmPolicy: "allowlist", // 顶层默认 allowFrom: ["123456789"], accounts: { main: { token: "token1", // 继承顶层的 dmPolicy 和 allowFrom }, public: { token: "token2", dmPolicy: "pairing", // 覆盖顶层配置 }, }, }, }, }`


**最佳实践：**

- 如果所有账号都用相同策略，配置在顶层
- 如果某个账号需要不同策略，在 account 级别覆盖
- 明确写出每个 account 的
`dmPolicy`

，避免继承混淆

## 最佳实践

### 1. 配置变更前先审查

**教训：** 我曾因为没仔细审查 patch 命令，把所有 Telegram 账号配置冲掉，导致所有 bot 连接中断。

**规则：**

- 任何
`config.patch`

、`gateway restart`

、模型变更等操作，**先审查一遍** - 嵌套对象（
`bindings`

、`accounts`

）必须带完整列表 - 有疑问先导出当前配置对比

`bash 体验AI代码助手 代码解读复制代码````
# 变更前备份
openclaw config get > openclaw-config-backup.json
# 变更后对比
openclaw config get > openclaw-config-new.json
diff openclaw-config-backup.json openclaw-config-new.json
```


### 2. 使用 status --deep 诊断

bash体验AI代码助手代码解读复制代码`openclaw status --deep`


输出包括：

- 每个 Agent 的状态
- Channel 连接状态
- 最近的错误日志

如果某个 Agent 或 Channel 异常，会直接显示。

### 3. 查看错误日志

`bash 体验AI代码助手 代码解读复制代码````
# 实时查看日志
tail -f ~/.openclaw/gateway.err.log
# 搜索特定错误
grep -i "error\|conflict\|fail" ~/.openclaw/gateway.err.log | tail -n 50
```


常见错误关键词：

`409 conflict`

：Telegram bot 冲突`unauthorized`

：token 错误或过期`dmPolicy`

：消息被访问控制策略拦截`binding`

：路由规则问题

### 4. 分阶段配置

不要一次性配置所有 Agent 和 Channel，容易出错且难以排查。

**推荐流程：**

- 先配置一个新 Agent（不配置 Telegram），本地测试
- Agent 正常后，添加一个 Telegram bot，测试路由
- 验证通过后，再添加其他 Agent 和 bot
- 每次变更后，验证所有已有功能正常

### 5. 文档化你的配置

在 workspace 下创建 `SETUP.md`

，记录：

- 每个 Agent 的用途和配置
- Telegram bot 对应关系
- 特殊配置的原因

`markdown 体验AI代码助手 代码解读复制代码````
# SETUP.md
## Agents
- main: 日常聊天，全功能，Telegram @MyMainBot
- blog: 技术写作，workspace-blog，Telegram @MyWorkBot
- novel: 小说创作，workspace-novel，仅本地使用
## Telegram Bots
- @MyMainBot (123456789): main agent
- @MyWorkBot (987654321): work agent
## 特殊配置
- work agent 的 dmPolicy 设为 allowlist，只允许授权用户访问
- main agent 启用了 heartbeat，定期检查日程
```


## 总结

OpenClaw 多 Agent 配置不复杂，但有几个容易踩的坑：

**config.patch 陷阱**：嵌套对象是整体替换，不是增量修改**模型 ID**：用别名（`claude-sonnet-4-5`

），不要带日期**BOOTSTRAP.md**：不要手动创建，会导致 Agent 卡住**dmPolicy**：默认是`pairing`

，建议改成`allowlist`

**Telegram 409**：同一个 bot token 只能被一个 Gateway 使用**配置继承**：account 级别配置会覆盖顶层配置

**核心原则：**

- 配置前先备份
- 变更后先验证
- 出问题先看日志
- 分阶段逐步配置

希望这篇文章能帮你少走弯路。如果还有其他问题，欢迎在评论区讨论！