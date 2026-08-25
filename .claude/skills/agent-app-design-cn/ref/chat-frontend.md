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
| `ChartBlock.tsx` | 解析 ```chart 的 JSON, 交给 `chart/` |
| `chart/schema.ts` | 严格校验, 任何不合规状一律返回 null |
| `chart/scale.ts` | 坐标轴数学, 与组件分开以便单独推敲 |
| `chart/ChartFigure.tsx` | 手写 SVG 的柱状图和折线图 |
| `index.ts` | `BLOCK_RENDERERS` 查找表和 `getBlockRenderer()` |

开关就是 `index.ts` 里那张表, 加一行支持一种块, 删一行关掉一种:

```typescript
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
  chart: ChartBlock,
}
```

没在表里的语言 (包括 ```python 这种普通代码) 全部落到 `CodeBlock`.

刻意**没有** 把这个开关放进 `data/site.toml`. 那个文件装的是 "这个数据集说什么", 而渲染器开关是 "这个 app 能渲染什么", 两件事换的频率不一样. 何况一个数据集不需要图, 让 agent 不输出就行. 真到了要按数据集裁剪 bundle 那天再搬.

注意区分 `site.toml` 里 kickstart 那 12 条各自带的 `render` 字段: 它不是开关, 是**按钮对读者的承诺** (画在按钮上的那个小图标, 见 `components/chat/RenderBadge.tsx`). 真正让块出现的是 `action` 里那句触发短语. 两者由 `mise run check` 的 render quota 双向校验.

---

## 3. 兜底是常态, 不是异常

`CodeBlock` 是整层站着的地板. 语言不认识, 渲染器被删掉, Mermaid 语法错, chart 的 JSON 不合规, 流式还没写完, 这些情况全都落到它. 所以它不做任何可能抛异常的事.

这条规则的实际后果是: 用户永远看得到内容, 最差也是一段可读的代码文本, 不会白屏, 不会看到报错.

---

## 4. 流式带来的两条硬约束

这两条是拿写完的文本去测渲染器时想不到的.

**流式期间围栏块一定是残缺的.** 收尾的三个反引号到达之前, 块里就是半张图. remark 会把未闭合的围栏一路吃到结尾, 所以 `MermaidBlock` 每来一个 chunk 都会拿到一份更长的残图. 做法是先 `mermaid.parse()`, 抛异常就退回 `CodeBlock`. 用户看到的效果是代码先出现, 写完那一刻变成图. 不需要额外的 `isStreaming` 标志, 解析失败本身就是信号.

**失败必须局部化.** 模型迟早会吐出非法 Mermaid. 整个渲染包在 `.catch()` 里, 坏图只损失那一个块, 不影响这条消息, 更不影响整个对话.

---

## 5. Chart 的取舍

**没用图表库.** recharts 之类要 500KB 以上, 而 bar 和 line 手写各几十行. 更重要的是 dataviz 规范要求的 mark 规格 (4px 圆角柱顶, 2px 柱间隙, 克制的网格) 用库反而要一路对抗默认样式. 所以 `chart/` 下面零新增依赖, 纯 SVG.

**没做饼图.** dataviz 的 job 到 form 对照表里根本没有饼图: 单个比值该用 meter, 部分对整体该用 stacked bar, 超过 7 类该用表格. 想加之前先回去读那张表.

**单序列用单色, 不是一根柱一个颜色.** 一根柱一个颜色是在用颜色编码排名, 会让读者看出数据里并不存在的分组. 只有多序列时才启用分类色板, 且按固定槽位顺序取, 不循环.

**颜色跑过 validator, 不是靠眼睛选的.** 四个槽位在明暗两种模式下都跑了 `dataviz/scripts/validate_palette.js`, 全部 PASS. 光色模式有一条 WARN: aqua 和 yellow 对浅背景对比度低于 3:1, 规范说这条不可忽略, 必须配 "可见标签或表格视图". 图表右下角那个 "Show data" 切换就是为了满足它, 别把它删掉.

**深色只认 `.dark` class, 不认系统偏好.** 全站 Tailwind 是 `darkMode: ["class"]`, 如果图表去听 `prefers-color-scheme`, 系统设成暗色的用户会在白色聊天页里看到一张深色图. token 定义在 `app/globals.css` 的 `.viz-root` 里.

---

## 6. 三个实现上的坑

`mermaid` 整包接近 1MB, 而大多数对话一张图都没有, 所以它是**动态 import**, 页面上真的出现第一个 ```mermaid 块时才加载, 之后整页共用一个 promise. 别把它改成顶层 import.

`securityLevel: "strict"` 不能拿掉. 图的内容来自 LLM, 而 LLM 在转述数据库里的数据, strict 会让 mermaid 用 DOMPurify 洗一遍输出并禁掉 HTML 标签. 这是我们敢对它的输出用 `dangerouslySetInnerHTML` 的唯一理由.

`markdown.tsx` 里的 `pre` 现在是**透传**. 围栏块自带外层容器 (`CodeBlock` 自己渲染 `<pre>`), 如果 `pre` 还包一层, 会套出 `<pre>` 里嵌 `<pre>` 或者 `<pre>` 里嵌 `<div>` 的非法结构.

---

## 7. 加一种新块渲染器

按这个顺序做, 最后一步是最常被忘掉的.

1. 在 `components/chat/blocks/` 写组件, 入参是 `BlockProps`, 失败时 `return <CodeBlock {...props} />`.
2. 在 `index.ts` 的 `BLOCK_RENDERERS` 加一行.
3. 在 `data/system-prompt.md` 里告诉 agent 什么时候产出这种块.

第三步是分界线: 前端认得一个格式, 不等于模型会输出它. 跳过这步的结果是渲染器一行代码都跑不到, 而前端测试全绿, 你会以为功能做完了.

提示词里现在有五段管这件事: `## Rendering Triggers` (kickstart 短语到块的对照表), `## Diagrams and Charts: The Fence Rule`, `## Showing the SQL`, `## Diagrams`, `## Charts`. 后四段都约束到了 "什么时候用" 和 "确切格式" 这个粒度, 加新块时照这个粒度写, 并在 Rendering Triggers 表里加一行.

这五段的母本在 `.claude/skills/swap-dataset-cn/ref/system-prompt-render-blocks.md`, 换数据集时整段逐字抄过去, 只换例子. 改渲染器行为时**两边一起改**, 否则下次换数据集会把旧措辞抄回来.

写提示词时注意一个坑: `mise run check` 会扫提示词里的 `FROM x` 和 `JOIN x` 当表名校验, 而它认不出这是散文还是 SQL. `drawn from a zero baseline` 里的 `from a` 会被判成表 `a` 而让构建失败. 换个说法即可.
