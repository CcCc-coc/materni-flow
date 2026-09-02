# 屏幕上有哪些元素, 每一块的内容从哪来

> [01](01-what-the-ui-must-do.md) 说了要做到什么. 这篇把两个页面拆成一块一块, 对上三件事:
> **这块是什么, 它的文字从哪个文件的哪个字段来, 哪个组件画它**. 改任何一块之前先查这张表.

**对应代码**: `data/site.toml`, `components/`, `app/`

---

## 首页

```
┌──────────────────────────────────────────────────┐
│ 1  lendinglens              Home   [Start Chat]  │  nav bar
├──────────────────────────────────────────────────┤
│ 2  SMB Lending Lens                              │  headline, two colours
│ 3  Fintech Lending Analytics Agent               │  tagline
│    ====                                          │  gold rule
│ 4  An AI agent that helps ...                    │  description
│ 5  [ What problem does this solve? ]             │  opens the overlay
│ 6  ┌──────┐┌──────┐┌──────┐┌──────┐              │  four capability cards
│    │Risk  ││Portf ││Early ││Custo │              │  hover -> tooltip bubble
│    └──────┘└──────┘└──────┘└──────┘              │
│ 7  (Strands SDK)(AWS Bedrock)(PostgreSQL)..      │  tech-stack tags
│ 8  ┌───────────────────────────────────┐         │
│    │ Start Analyzing                -> │         │  call to action
│    └───────────────────────────────────┘         │
│ 9  Analyzing SMB lending data: 10 tables,..      │  data-size line
│ 10 (c) 2026 LendingLens.                         │  footer
└──────────────────────────────────────────────────┘
```

| # | 元素 | 文案来自 | 组件 |
| :--- | :--- | :--- | :--- |
| 1 | 导航条 + 两截着色的字标 | `[brand] logoPrefix` `logoAccent` | `app/_components/layouts/Navigation.tsx` |
| 2 | 大标题 | `[home.headline] prefix` `accent` | `Hero.tsx` |
| 3 | 副标题 | `[home] tagline` | `Hero.tsx` |
| 4 | 一段介绍 | `[home] description` | `Hero.tsx` |
| 5 | 覆盖层触发按钮 | `[home.businessContext] triggerLabel` | `Hero.tsx` |
| 6 | 四张能力卡 | `[[capabilities]]` × 4 | `components/CapabilityCard.tsx` |
| — | 卡片后面的解释气泡 | 同上的 `tooltip` 字段 | `components/ConceptTooltip.tsx` |
| 7 | 技术栈标签 | `[home] techStack` | `Hero.tsx` |
| 8 | 行动召唤 | `[home.cta] title` `subtitle` | `Hero.tsx` |
| 9 | 数据规模 | `[home] blurb` | `Hero.tsx` |
| 10 | 页脚 | `[brand] footerName` | `HomePageContent.tsx` |
| — | 业务说明覆盖层 | `data/business-context.md` + `[home.businessContext] title` `subtitle` | `components/BusinessContextModal.tsx` |

---

## agent 页

```
┌──────────────────────────────────────────────────┐
│ 1  lendinglens              Home   [Start Chat]  │  the same nav bar
├──────────────────────────────────────────────────┤
│ A  ┌───────────────────────────────────┐         │
│    │        Lending Lens               │         │  agent's own name
│    │  Ask questions about ...          │         │  welcome subtitle
│    │  ┌───────┐┌───────┐               │         │  the same four cards,
│    │  └───────┘└───────┘               │         │  compact variant
│    │  ┌───────┐┌───────┐               │         │
│    │  └───────┘└───────┘               │         │
│    │  Try: "What's the default rate..."│         │  example prompts
│    └───────────────────────────────────┘         │
│ B  ┌───────────────────────────────────┐         │
│    │  Ask me directly or click a ...   │         │  hint strip
│    └───────────────────────────────────┘         │
│ C  ┌─────────┐┌─────────┐                        │  12 kickstart buttons
│    │Introduct││Risk Pric│  ... x12               │  each with a render badge
│    │[t] What ││[c] Is pr│                        │
│    └─────────┘└─────────┘                        │
│ D  ┌───────────────────────────┐  [up]           │  composer + send key
│    └───────────────────────────┘                 │
└──────────────────────────────────────────────────┘
```

对话开始之后 A B C 消失, 换成:

```
│ E  ┌───────────────────────────────────┐         │
│    │ [AI] Lending Lens             [x] │         │  dismissable banner
│    │      I'm here to help you with ...│         │
│    └───────────────────────────────────┘         │
│ F  [AI] ┌───────────────────────────┐            │  the agent's bubble
│         │ > Thinking  ...           │            │  collapsible reasoning
│         │ prose / table / diagram   │            │  -> Markdown renderer
│         └───────────────────────────┘            │
│ G            ┌───────────────┐ [you]             │  the user's bubble
│              └───────────────┘                   │
```

| # | 元素 | 文案来自 | 组件 |
| :--- | :--- | :--- | :--- |
| A | 欢迎卡的标题 | `[chat] agent` | `components/chat/overview.tsx` |
| — | 欢迎卡的副标题 | `[chat] welcomeSubtitle` | 同上 |
| — | **四张能力卡** | `[[capabilities]]` —— **和首页同一份** | `CapabilityCard`, `compact` |
| — | 示例提示 | `[chat] tryExamples` | `overview.tsx` |
| B | 提示条 | `[chat] suggestionsHint` | `components/chat/multimodal-input.tsx` |
| C | 12 个 kickstart 按钮 | `[[chat.suggestedActions]]` × 12 | `multimodal-input.tsx` |
| — | 按钮上的渲染徽章 | 每条的 `render` 字段 | `components/chat/RenderBadge.tsx` |
| D | 输入框占位文字 | `[chat] inputPlaceholder` | `multimodal-input.tsx` |
| — | "上一条还在跑" 的吐司 | `[chat.messages] waitForResponse` | `multimodal-input.tsx` |
| E | 横幅 | `[chat] agent` + `[chat.messages] welcomeMessage` | `components/chat/chat.tsx` |
| F, G | 消息气泡 | agent 的回答 (不是文案) | `components/chat/message.tsx` |
| — | 头像方块 | 固定两个字母 `AI` | `components/chat/AssistantAvatar.tsx` |
| — | 思考块 | agent 的 reasoning | `message.tsx` 里的 `ReasoningBlock` |

---

## 一条被复用了两次的数据

`[[capabilities]]` **只写一份, 渲染两次**: 首页的能力卡和 agent 页的洞察卡, 走同一个
`CapabilityCard` 组件, 只差一个 `compact` 开关.

这不是省事, 是防漂移. **两份配置描述同一组东西, 迟早会各走各的**: 同一条主线在两个页面上
起了不同的名字, 配了不同的图标, 只有一边有 tooltip —— 而且这种情况不会有任何测试失败, 因为
两边各自都是合法的配置.

**一份数据两处渲染, 漂移在结构上就不可能发生.**

---

## 哪些元素**不是**文案

这几处的文字写死在组件里, 而且应该写死 —— 它们不随数据集变:

| 文字 | 在哪 | 为什么不进 `site.toml` |
| :--- | :--- | :--- |
| `Home` / `Start Chat` | `Navigation.tsx` | 这个 app 有几个页面是脚手架的事实, 不是数据集的 |
| `AI` | `AssistantAvatar.tsx` | 要塞进 32px 的方块, 而数据集可以给 agent 起一个很长的名字 |
| `Thinking` / `Thinking...` | `message.tsx` | 描述的是 agent 的运行状态, 不是业务 |
| `Loading` / `Loading Chat` | 两个 `loading.tsx` | 同上 |
| `Close` (aria-label) | 多处 | 无障碍标签, 不是展示文案 |
| 三个渲染徽章的 aria-label | `RenderBadge.tsx` | 描述的是渲染器能力, 由前端定义, 不由数据集作者选 |

**判据和后端那条一样**: 换个业务领域, 它要不要改? 要改就进 `site.toml`; 不改就留在组件里.
