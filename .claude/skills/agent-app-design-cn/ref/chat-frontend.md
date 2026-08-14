# Chat 页渲染层

`/chat` 是基于 Vercel AI SDK 的流式对话. agent 说的每句话都是流式文本, 页面上看到的几乎所有东西都是这段文本渲染出来的结果. 这份文档定义那一层怎么切, 目的是让以后加 chart 是 "加文件", 不是 "改结构".

---

## 1. 两个分发点, 不是一个

容易把渲染能力想成四层叠起来: 纯文本, Markdown, Mermaid, chart. 作为能力清单这么理解没问题, 但它不是代码的形状, 照着它建结构会把开关做错地方.

真实情况是两个分发点, 深度不同.

第一个在 **message part 级**. AI SDK 把一条消息给成 `message.parts[]`, 每个 part 带 `type`. `components/chat/message.tsx` 现在用 `if` 链分: `reasoning` 渲染成可折叠的思考块, `text` 交给 Markdown. 纯文本和 Markdown 是这一级的同辈.

第二个在 **围栏代码块级**. Mermaid 和 chart 不是 part, 它们是 text part 内部的围栏块, 被发现时已经深了三层. 分发点在 `components/chat/markdown.tsx` 的 `code` 组件里, `react-markdown` 每遇到一个 code 节点就调它一次.

所以 Mermaid 的开关只可能在第二个点上. 第一个点目前还是 `if` 链, 没有抽象, 因为只有两种 part 且短期不会变. 等 SDK 开始送 tool call 或 source part 时再抽, 现在抽是空转.

---

## 2. 围栏块渲染器

代码在 `components/chat/blocks/`:

| 文件 | 作用 |
| :--- | :--- |
| `types.ts` | `BlockProps`, 所有渲染器的统一入参 (`source` 和 `language`) |
| `CodeBlock.tsx` | 普通代码块, 同时是整层的兜底 |
| `MermaidBlock.tsx` | 把 ```mermaid 渲染成图 |
| `index.ts` | `BLOCK_RENDERERS` 查找表和 `getBlockRenderer()` |

开关就是 `index.ts` 里那张表, 加一行支持一种块, 删一行关掉一种:

```typescript
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
}
```

没在表里的语言 (包括 ```python 这种普通代码) 全部落到 `CodeBlock`.

刻意**没有** 把这个开关放进 `config/dataset.json`. 那套 (JSON 写名字, TS 查表, checker 卡拼写) 是 `lib/icons.ts` 的做法, 值得抄的前提是 "换数据集时真的要改". 渲染能力不是这种东西: 一个数据集不需要图, 让 agent 不输出就行, 没必要为它多一层配置和一条校验. 真到了要按数据集裁剪 bundle 那天再加.

---

## 3. 兜底是常态, 不是异常

`CodeBlock` 是整层站着的地板. 语言不认识, 渲染器被删掉, Mermaid 语法错, 流式还没写完, 这四种情况全都落到它. 所以它不做任何可能抛异常的事.

这条规则的实际后果是: 用户永远看得到内容, 最差也是一段可读的代码文本, 不会白屏, 不会看到报错.

---

## 4. 流式带来的两条硬约束

这两条是拿写完的文本去测渲染器时想不到的.

**流式期间围栏块一定是残缺的.** 收尾的三个反引号到达之前, 块里就是半张图. remark 会把未闭合的围栏一路吃到结尾, 所以 `MermaidBlock` 每来一个 chunk 都会拿到一份更长的残图. 做法是先 `mermaid.parse()`, 抛异常就退回 `CodeBlock`. 用户看到的效果是代码先出现, 写完那一刻变成图. 不需要额外的 `isStreaming` 标志, 解析失败本身就是信号.

**失败必须局部化.** 模型迟早会吐出非法 Mermaid. 整个渲染包在 `.catch()` 里, 坏图只损失那一个块, 不影响这条消息, 更不影响整个对话.

---

## 5. 三个实现上的坑

`mermaid` 整包接近 1MB, 而大多数对话一张图都没有, 所以它是**动态 import**, 页面上真的出现第一个 ```mermaid 块时才加载, 之后整页共用一个 promise. 别把它改成顶层 import.

`securityLevel: "strict"` 不能拿掉. 图的内容来自 LLM, 而 LLM 在转述数据库里的数据, strict 会让 mermaid 用 DOMPurify 洗一遍输出并禁掉 HTML 标签. 这是我们敢对它的输出用 `dangerouslySetInnerHTML` 的唯一理由.

`markdown.tsx` 里的 `pre` 现在是**透传**. 围栏块自带外层容器 (`CodeBlock` 自己渲染 `<pre>`), 如果 `pre` 还包一层, 会套出 `<pre>` 里嵌 `<pre>` 或者 `<pre>` 里嵌 `<div>` 的非法结构.

---

## 6. 加一种新块渲染器

按这个顺序做, 最后一步是最常被忘掉的.

1. 在 `components/chat/blocks/` 写组件, 入参是 `BlockProps`, 失败时 `return <CodeBlock {...props} />`.
2. 在 `index.ts` 的 `BLOCK_RENDERERS` 加一行.
3. 在 `agent_app/prompts/bi-agent-system-prompt.md` 里告诉 agent 什么时候产出这种块.

第三步是分界线: 前端认得一个格式, 不等于模型会输出它. 跳过这步的结果是渲染器一行代码都跑不到, 而前端测试全绿, 你会以为功能做完了.

Mermaid 的这一段写在提示词的 `## Diagrams` 里, 约束了三件事: 只在讲结构和流程时用, 数字一律走 Markdown 表格, 一次回答最多一张图. 加 chart 时照这个粒度写.
