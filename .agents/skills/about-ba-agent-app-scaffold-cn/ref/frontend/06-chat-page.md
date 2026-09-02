# agent 页: 一个输入框, 和它周围的所有防呆

> chat 页本身很薄 —— 状态全在 AI SDK 的 `useChat` 里, 后端无状态. 这篇讲那层薄壳做的几件
> 事: 空状态放什么, 12 个按钮怎么变成一次提问, 以及消息气泡里那三种内容.

**对应代码**: `components/chat/chat.tsx`, `multimodal-input.tsx`, `message.tsx`,
`overview.tsx`, `AssistantAvatar.tsx`, `RenderBadge.tsx`, `hooks/use-scroll-to-bottom.tsx`

**依赖**: [03](03-content-pipeline.md) 的 `SiteConfig`, [07](07-markdown-and-blocks.md) 的
`Markdown`.

---

## 组件树和状态

```
page.tsx (server)   loadSite()
  └ Chat (client)              useChat() ── POST /api/chat
      ├ Overview               messages.length === 0 时显示
      ├ 横幅                    messages.length > 0 且没被关掉时显示
      ├ PreviewMessage × n
      │   ├ AssistantAvatar
      │   ├ ReasoningBlock     可展开的思考
      │   └ Markdown           正文 / 表格 / 图 / 图表
      ├ ThinkingMessage        最后一条是用户消息且在等回复时
      └ MultimodalInput
          ├ 12 × Button + RenderBadge    messages.length === 0 时显示
          └ Textarea + 发送/停止键
```

**对话状态住在浏览器内存里**, 由 `useChat` 管. AI SDK 每次都把完整消息列表 POST 上去, 所以
后端是无状态的 (见 [backend/09](../backend/09-http-entry-point.md)). 刷新页面对话就没了 ——
这是设计, 不是缺陷: 没有登录, 也就没有地方存.

唯一落盘的是**输入框里还没发出去的草稿**, 存在 `localStorage`.

---

## 空状态不能是空的

一个只有输入框的聊天页, 用户不知道能问什么. 所以 `messages.length === 0` 时同时显示两样:

- **`Overview`** —— agent 自称 + 一句副标题 + **和首页同一份的四张能力卡** + 一行示例
- **12 个 kickstart 按钮**

一旦发出第一条消息, 这两样都消失, 换成可关闭的横幅. 所以它们和横幅**永远不会同时在屏幕上**
—— 这一点值得知道, 因为它们长得像同一个东西, 而在代码里它们分属两个组件.

## 12 个按钮是橱窗, 不是问题列表

四类各恰好 3 条, 分别产出表格 / 流程图 / 图表 / 纯文字. 为什么要这个配额, 以及 `render`
字段和触发短语这两件事怎么互相校验, 完整规则在
[architecture/06](../architecture/06-rendering-contract.md).

前端这一侧只做一件事: **`RenderBadge` 把那份配额画成读者看得见的东西.**

```
render = "table"      表格图标
render = "flowchart"  流程图标
render = "chart"      柱状图标
render = "free"       什么都不画
```

`free` 故意什么都不画 —— **每个按钮都有徽章等于没有徽章**.

这三个图标是直接 import 的, 不走 `lib/icons.ts`. 那张表是数据集作者可以在 `site.toml` 里
点名的集合; 这个映射由渲染器固定, 不是数据集作者能选的.

---

## 输入框

`MultimodalInput` 这个名字来自上游模板, **它只收文本**, 没有上传.

几件小事:

- **高度自适应**: 每次输入把 `height` 归零再设成 `scrollHeight`, 否则删字时框不会缩回去
- **Enter 发送, Shift+Enter 换行**
- **上一条还在跑时按 Enter** 不是静默丢弃, 而是弹一条吐司 (`waitForResponse`)
- **草稿存 `localStorage`**, 刷新回来还在
- 宽屏 (>768px) 发送后把焦点还给输入框, 窄屏不还 —— 手机上抢焦点会把软键盘顶起来

---

## 消息气泡里有三种东西

`message.parts` 是 AI SDK v5 的形状, 一条消息由若干带类型的 part 组成. 这里只认两种:

| part | 渲染成 |
| :--- | :--- |
| `reasoning` | `ReasoningBlock`, 默认折叠, 展开看全文 |
| `text` | 交给 `Markdown`, 于是表格 / 流程图 / 图表都从这里出来 |

其余类型直接跳过.

### 分发点有两个, 深度不同

很容易把渲染能力想成四层叠起来: 纯文本, Markdown, 流程图, 图表. 作为能力清单这么理解没
问题, 但**它不是代码的形状**, 照着它建结构会把开关做错地方.

| 层 | 在哪 | 分什么 |
| :--- | :--- | :--- |
| message part 级 | `message.tsx` 的 `if` 链 | `reasoning` 还是 `text` |
| 围栏块级 | `markdown.tsx` 的 `code` 组件 | ` ```mermaid ` 还是 ` ```chart ` 还是普通代码 |

流程图和图表**不是 part**, 它们是 text part 内部的围栏块, 被发现时已经深了三层. 所以那个
开关只可能在第二层, 见 [07](07-markdown-and-blocks.md).

第一层至今还是一条 `if` 链, 没有抽象 —— 只有两种 part, 而且短期不会变. 等 AI SDK 开始送
tool call 或 source part 时再抽; 现在抽是空转.

**思考默认折叠**是必要的: 这个 agent 每调一次工具就产生一段思考, 展开的话正文会被埋掉.
折叠状态下显示前 100 个字符当预览, 让人知道里面是什么.

**agent 交回来的那段文本本身是后端解析过的** —— 从整个消息列表里挖出 (thinking, answer),
以及为什么"最后一条消息不一定是答案", 见
[backend/07](../backend/07-agent-response.md).

---

## 一个可以点的链接: `#ask:`

`Markdown` 认一种特殊链接: `[文字](#ask:一个问题)` 渲染成一个按钮, 点了就把那个问题作为
新的一轮发出去. agent 可以在回答末尾建议追问, 而读者一点即走.

因为问题里通常有空格, 而 Markdown 的链接语法对空格不友好, 所以渲染前有一步预处理把它包成
`<#ask:...>` 尖括号形式.

---

## 一个已知的重复

**自动滚动有两套机制同时在跑**:

- `hooks/use-scroll-to-bottom.tsx` 用 `MutationObserver` 监听子节点增加
- `chat.tsx` 里另有一个 `useEffect` 监听 `messages.length`

两个都在调 `scrollIntoView`. 行为上大概率无害 (滚到同一个地方), 但读代码的人会不知道该改
哪一个. 留在这里是因为改动它需要真的在慢网络下验一遍流式滚动的手感, 而那件事没法靠读代码
判断.
