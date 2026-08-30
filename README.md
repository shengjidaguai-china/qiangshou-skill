<p align="center">
  <a href="https://github.com/shengjidaguai-china"><strong>升级打怪开源社区</strong></a> 首批开放共建项目 ·
  <a href="https://github.com/shengjidaguai-china">点击组织首页右上角 <strong>Follow</strong></a>，及时获取新项目与共建活动
</p>

<div align="center">

# 枪手 QIANGSHOU

### 把真实技术经历，写成有人愿意读完的公众号长文

[![GitHub Stars](https://img.shields.io/github/stars/shengjidaguai-china/qiangshou-skill?style=for-the-badge&logo=github&label=Stars&color=f5b301)](https://github.com/shengjidaguai-china/qiangshou-skill/stargazers)
[![Version](https://img.shields.io/badge/version-0.1-4c8bf5?style=for-the-badge)](https://github.com/shengjidaguai-china/qiangshou-skill/releases/tag/v0.1)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-7c5cff?style=for-the-badge)](./qiangshou/SKILL.md)

**如果枪手对你有帮助，请点一个 Star。你的 Star 会帮助更多独立开发者发现它。**

<img src="./assets/qiangshou-tech-stack.png" alt="枪手 Skill 技术栈" width="100%" />

</div>

## 枪手是什么

枪手是一套面向独立开发者、Vibe Coding 创作者和 AI 创作者的中文技术长文 Skill。

它读取仓库、代码、日志、实验、提交记录、用户反馈和作者口述，先建立事实边界，再把真实技术经历写成具有冲突、选择、技术取舍和结果边界的公众号长文。

枪手不是把 README 扩写成文章，也不是用高级词汇覆盖作者原本的表达。

> 它要做的，是保留作者本人，同时让真实技术经历变得可信、好懂，而且有人愿意读完。

## 为什么做枪手

很多技术创作者遇到的并不是“没有内容”，而是：

- 项目事实散落在仓库、日志、实验和聊天记录中；
- 普通 AI 容易把技术项目写成功能说明书；
- 技术内容专业，但普通读者看不懂；
- 为了传播效果，模型容易夸大数据和用户反馈；
- 润色以后，作者的大白话、情绪和判断被磨掉；
- 作者已经确认终稿，AI 仍会主动修改；
- 用户删除或否决的内容，会在下一轮被重新加回来；
- 每写一篇文章，都要重新向 AI 解释自己的文风。

枪手把这些问题变成一条可执行的内容生产管线。

## 核心能力

### 1. 多源材料读取

枪手可以从以下材料建立文章：

- README、许可证和架构文档；
- 关键代码、测试、日志和提交记录；
- 实验数据、图表和时间线；
- 用户口述、评论与反馈；
- 旧稿、参考文章与已确认终稿。

它不会直接扩写材料，而是先寻找事实、主问题、冲突、选择和结果。

### 2. 五类事实核验

重要说法会被区分为：

1. 仓库可验证；
2. 用户亲述；
3. 第三方反馈；
4. 作者推断；
5. 时效数据。

单个反馈不会被包装成普遍效果，局部指标不会被偷换成整体提升，推断也不会伪装成事实。

### 3. 自适应长文编排

枪手不再给每篇文章套同一套章节表。“项目故事”和“观点实证”只用于判断高层写作意图，真正结构从本篇事实、冲突、证据、选择和后果中生成。

每篇只选择一条主导推进线：事件变化、认知变化、决策变化、实验变化或人物关系变化。其他变化可以辅助，但不会争夺主线。版本更新、技术踩坑和迭代复盘只是可选变体，不会不断扩张成新的固定引擎。

### 4. 六步技术写法

```text
问题 → 为什么难 → 尝试与取舍 → 具体实现 → 可量化结果 → 适用边界
```

技术深度来自真实问题、工程决策和结果边界，而不是术语密度。

### 5. 作者声音与去 AI 味

枪手会保留作者自然的大白话、幽默、自嘲、真实情绪和技术判断。

终稿检查采用“删除优先”：先删掉不增加事实、因果、判断或人物变化的句子，再做必要的局部改写。

它不会为了“高级感”统一润色，也不会用禁词表机械替换。模板连接词、伪完整长列表、重复总结和自动升华会被优先清理，作者真实的不确定、失败、改判和自然口语会被保留下来。

### 6. 终稿保护

用户确认“终稿”“发布版”或“最终文案”，或一次写作已经完成“配图 + 公众号可复制 HTML”交付后：

- 不再主动润色正文；
- 不改变现有文字和顺序；
- 用户删除的内容不得恢复；
- 用户否决的建议不得反复提出；
- 除明确授权的错别字外，只能建议，不能直接修改。

### 7. 轻量自进化

每当用户确认终稿，或完成“配图 + 公众号可复制 HTML”交付，枪手会对比模型前稿与用户手改终稿：

- 原样保留固定归因给助手，不冒充用户写作；
- 删除、改写和新增分别识别，纯排版变化不会进入学习；
- 推断偏好需要在至少两篇不同终稿中重复才会晋升；
- 用户明确指令立即生效，最新选择覆盖旧信号；
- 文字与视觉偏好分别记忆，每篇最多新增或修正 2 条；
- 用户说“这次不要学习”就跳过。

自进化由匿名终稿 ID 和本地信号台账确定性去重、晋升并同步 Markdown 记忆，不是重新训练模型。枪手不会保存终稿正文，也不会学习文章事实、观点、人物、项目名、奖项或单篇章节结构。

### 8. 公众号交付

根据用户授权范围，枪手可以继续生成：

- 用户实际需要的标题、摘要、正文、配图或 HTML；
- 内容冻结排版稿；
- 微信兼容内联 HTML；
- Markdown 表格的内联样式渲染；
- 图片宽高不超过 2000px 的交付检查；
- 无可点击超链接、无本地失效图片路径的最终校验；
- 经明确授权后保存公众号草稿。

事实表、推进表和配图蓝图可以在内部用于保证质量，但不会默认全部展示。保存草稿不等于发布；未经单独授权，不会群发、发表、提交审核或定时发送。

## 当前能力规模

| 能力 | 当前版本 |
| --- | ---: |
| 任务模式 | 6 种 |
| Markdown 参考模块 | 9 个 |
| 持久化信号台账 | 2 份 |
| 真实测试场景 | 11 类 |
| 确定性工具 | 5 个 |
| 高层写作意图 | 2 类 |
| 主导推进线 | 5 类 |
| 事实类型 | 5 类 |
| 技术写作步骤 | 6 步 |
| 动态记忆文件 | 2 份 |
| 自动化行为测试 | 25 项 |
| 单篇终稿学习上限 | 2 条 |
| 单套记忆有效规则上限 | 15 条 |

当前实现不保存完整范文；历史基线覆盖 3 篇用户确认手改终稿，只有存在可靠前稿对照或用户明确指令时才会形成偏好证据。

## 适合谁

- 有真实项目，却总把文章写成开发日志的人；
- 想写技术公众号，但不想生成标准 AI 文风的人；
- 需要同时兼顾故事、技术、事实和传播的人；
- 希望 AI 逐渐理解个人文风，又不保存整篇终稿的人；
- 经常遭遇“终稿被继续优化”或“删除内容被恢复”的人。

## 与替代方案的区别

| 方案 | 优势 | 常见限制 |
| --- | --- | --- |
| 通用 AI 对话 | 快速生成文字 | 容易模板化，不理解终稿状态 |
| 提示词模板 | 能规范单次输出 | 每篇重新调教，无法沉淀作者偏好 |
| 普通润色工具 | 修改句子快 | 无法建立事实链和技术主线 |
| 人工代笔 | 采访与写作深入 | 成本高、周期长、技术沟通成本大 |
| **枪手** | 事实核验、自适应编排、终稿保护、双记忆自进化与公众号交付 | 仍然需要用户提供真实素材和最终判断 |

## 安装

### 方式一：复制 Skill 文件夹

```bash
git clone https://github.com/shengjidaguai-china/qiangshou-skill.git
mkdir -p ~/.codex/skills
cp -R qiangshou-skill/qiangshou ~/.codex/skills/qiangshou
```

重新打开 Codex 后即可使用 `$qiangshou`。

### 方式二：仅更新已有版本

```bash
git clone https://github.com/shengjidaguai-china/qiangshou-skill.git
cp -R qiangshou-skill/qiangshou/. ~/.codex/skills/qiangshou/
```

更新前请备份以下动态记忆和信号台账，直接覆盖会丢失已经学习的规则：

- `references/author-voice.md`
- `references/author-voice-signals.json`
- `references/visual-preferences.md`
- `references/visual-preference-signals.json`

## 快速开始

### 写项目故事

```text
使用 $qiangshou，读取这个项目的仓库、日志和提交记录，
把真实开发过程写成一篇公众号技术长文。
先建立事实边界，再设计主矛盾和文章结构。
```

### 写观点实证长文

```text
使用 $qiangshou，把我的观点、个人经历和实验材料写成观点实证长文。
公平呈现大众认知，区分实验观察、外部研究和作者判断，
允许实验结果与我最初的预期不同。
```

### 保护终稿

```text
这是最终发布版。不要修改正文和顺序，只提出必要建议。
这次终稿可以学习文风，但不要保存文章事实和观点。
```

## 技术架构

```text
Codex 宿主模型
  └── SKILL.md 控制与任务路由
      ├── 9 个按需加载的 Markdown 参考模块
      ├── 自适应编排与五类事实边界
      ├── 文字 / 视觉双记忆与匿名信号台账
      └── 5 个确定性 Python 工具
```

枪手采用渐进式知识加载：主文件负责流程和边界，详细方法按任务读取，减少上下文膨胀和规则冲突。

## 项目结构

```text
qiangshou/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── author-voice.md
│   ├── author-voice-signals.json
│   ├── facts-and-strategy.md
│   ├── format-preserving-layout.md
│   ├── review-and-deliverables.md
│   ├── self-evolution.md
│   ├── test-scenarios.md
│   ├── visual-preferences.md
│   ├── visual-preference-signals.json
│   ├── wechat-layout-and-draft.md
│   └── writing.md
├── scripts/
│   ├── render_wechat_html.py
│   ├── self_evolution.py
│   ├── validate_wechat_html.py
│   ├── validate_wechat_images.py
│   └── verify_content_preservation.py
└── tests/
    └── 25 项行为与合同测试
```

## 版本

当前版本：**0.1**

当前源码包含自适应编排、事实核验、自动终稿保护、文字 / 视觉双记忆自进化和更严格的公众号交付校验。

## 支持枪手

如果枪手帮你完成了一篇文章、保护了一版终稿，或者让技术项目终于有人愿意读完，请点一个 Star。

<div align="center">

### ⭐ Star 是对独立开发最直接的支持

[给枪手一个 Star](https://github.com/shengjidaguai-china/qiangshou-skill) · [提交问题](https://github.com/shengjidaguai-china/qiangshou-skill/issues) · [查看版本](https://github.com/shengjidaguai-china/qiangshou-skill/releases)

</div>
