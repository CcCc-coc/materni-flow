# 一段纯文本怎么变成表格, 流程图和图表

> agent 交回来的只是一段 Markdown 字符串. 页面上看到的一切都是从它渲染出来的. 这篇讲那个
> 分发点在哪一行, 以及为什么**每个块渲染器的失败路径都是正常路径**.

**对应代码**: `components/chat/markdown.tsx`, `components/chat/blocks/`

**依赖**: 无项目内依赖. 使用者是 [05](05-home-page.md) 的覆盖层和 [06](06-chat-page.md) 的
消息气泡.

---

## 分发点只有一行

`markdown.tsx` 给 `react-markdown` 传了一组自定义组件, 其中 `code` 那一个是整个块渲染层的
开关:

```tsx
code: ({ className, children }) => {
  if (!className) return <code className="...">{children}</code>   // 行内代码
  const language = /language-(\w+)/.exec(className)?.[1] ?? ''
  const Block = getBlockRenderer(language)
  return <Block source={String(children).replace(/\n$/, '')} language={language} />
}
```

**行内代码没有 `className`, 围栏块带 `language-*`** —— 这就是两者的全部区别. 语言名去查一张表:

```ts
// components/chat/blocks/index.ts
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
  chart: ChartBlock,
}
```

**加一行支持一种块, 删一行关掉一种.** 没在表里的语言 (包括 ` ```python `) 全部落到
`CodeBlock` 兜底.

**这张表刻意不放进 `data/site.toml`.** 那个文件装的是"这个数据集说什么", 而渲染器开关是
"这个 app 能渲染什么", 两件事换的频率不一样. 何况一个数据集不需要图, 让 agent 不输出就行.
真到了要按数据集裁剪打包产物那天再说.

注意和 kickstart 那 12 条各自带的 `render` 字段区分: **那个不是开关, 是按钮对读者的承诺**
(画在按钮上的小图标, 见 [06](06-chat-page.md)). 真正让块出现的是 `action` 里那句触发短语.

还有一个配套的小改动容易漏: `pre` 被改成了直接透传. 围栏块自己会渲染外层容器, 再包一层
就会得到 `<pre>` 套 `<pre>`, 或者 `<div>` 套在 `<pre>` 里面.

---

## 失败是正常路径, 不是异常处理

这是这一层最重要的一件事.

agent 的回答是**流式到达**的. 所以在它写完之前, 页面上一定存在一个**没有闭合的围栏块**:
一段写到一半的 mermaid 语法, 一个截断的 JSON. 这不是边缘情况, 是每一次画图的必经状态.

所以:

```
解析不了  ->  return <CodeBlock {...props} />
```

读者先看到原始代码, 收尾的围栏一到就变成图. 三个渲染器都这么写, 而 `CodeBlock` 因此
**不做任何可能抛异常的事**.

`CodeBlock` 同时是四种情况的落点: 未知语言, 被删掉的渲染器, mermaid 语法错误, 以及还在流的
块.

**失败还必须是局部的.** 模型迟早会吐出非法的 mermaid. 整个渲染包在 `.catch()` 里, 一张坏图
只损失它自己那一个块 —— 不影响这条消息, 更不影响整个对话. 用户永远看得到内容, 最差也是一段
可读的代码文本, 不会白屏.

---

## `MermaidBlock`: 一个近 1MB 的包, 按需加载

```ts
let mermaidPromise: Promise<...> | null = null
function loadMermaid() { if (!mermaidPromise) mermaidPromise = import("mermaid").then(...) }
```

**大部分对话里一张图都没有**, 所以这个包只在页面真的遇到第一个 ` ```mermaid ` 块时才加载,
之后每个块复用同一个 promise.

三个不能改的细节:

**`securityLevel: "strict"`.** 图的源码来自 LLM, 而 LLM 又在转述数据库内容. strict 会把
mermaid 的输出过一遍 DOMPurify 并禁掉 HTML 标签 —— **这是下面那行
`dangerouslySetInnerHTML` 唯一可以接受的理由**.

**先 `parse` 再 `render`.** `parse` 在源码不合法或不完整时抛异常, 这比让 `render` 失败再去
收拾便宜.

**卸载时清理临时节点.** 一次失败的渲染会把 mermaid 用来测量的临时节点留在文档里. 不清的话
它们会在页面的整个生命周期里累积.

DOM id 由 `useId()` 去掉非字母数字得来 —— mermaid 拿它当元素 id, 而 `useId` 的原始值带冒号,
在选择器里是非法的.

---

## `ChartBlock`: 手写 SVG, 零图表库

**为什么不用图表库**: recharts 之类 500KB 起步, 而 bar 和 line 手写各几十行. 更要紧的是
dataviz 规范要的那些 mark 规格 (圆角的数据端, 柱间隙, 克制的网格) 用库反而要一路对抗默认
样式.

所以 `blocks/chart/` 下面零新增依赖, 三个文件:

| 文件 | 职责 |
| :--- | :--- |
| `schema.ts` | 线上格式 + 一个**敌意假设**的解析器 |
| `scale.ts` | 轴的数学, 纯函数, 和组件分开 |
| `ChartFigure.tsx` | 画 SVG |

### 解析器假设输入是敌意的

生产者是一个 LLM, 所以任何不严格符合下面这个形状的输入一律返回 `null`, 调用方退回显示原始
JSON:

```json
{
  "type": "bar",
  "title": "...",
  "yLabel": "%",
  "categories": ["A", "B", "C"],
  "series": [{ "name": "actual", "values": [3.9, 6.2, 9.9] }]
}
```

硬性规则: `type` 只能是 `bar` 或 `line`; **最多 4 个 series, 最多 24 个 category**; 每个
series 的值数量必须等于 category 数量; 值必须是有限数字.

那条"数量必须相等"不是洁癖: **少一格会画出一根高度为 `NaN` 的柱子, 它渲染成什么都没有,
看起来就像一个真实的零值.**

流式期间的半截 JSON 走的是同一条 `return null` 路径, 所以**不需要另外一个"是不是还在流"的
信号**.

### 三条 dataviz 取舍

**没做饼图.** dataviz 规范的 job-to-form 对照表里根本没有饼图: 单个比值该用 meter, 部分对
整体该用堆叠柱, 超过 7 类该用表格. 想加之前先回去读那张表.

**单序列用单色, 不是一根柱一个颜色.** 一根柱一个颜色是在用颜色编码排名, 会让读者看出数据
里并不存在的分组. 只有多序列时才启用分类色板 (`seriesColor()` 里那个 `total === 1` 分支).

**右下角那个 "Show data" 切换不能删.** 四个色槽跑过对比度校验, 其中一条 WARN 是浅背景下
某两个色相的对比度低于 3:1, 而规范说这条不可忽略, 必须配一个"可见标签或表格视图" —— 那个
切换就是为了满足它.

### 轴永远包含零

```ts
const lo = Math.min(0, ...values)
const hi = Math.max(0, ...values)
```

**柱状图的基线不从零开始, 是图表说谎最常见的方式** —— 它会把差异放大. 这个领域里负数是有
意义的 (定价缺口可以为负), 所以轴会在需要时从零往下长.

刻度用累加而不是 `for (v = min; v <= max; v += step)`, 因为反复的浮点加法会漂移, 可能把最后
一个刻度丢掉.

### 颜色来自 CSS 变量, 顺序有意义

`globals.css` 里的 `.viz-root` 定义了 `--viz-series-1..4`. **分类色的槽位顺序本身是色盲安全
机制, 不是美观选择** —— 按顺序分配, 而且永远不要循环用回第一个 (这也是为什么 series 上限
是 4).

---

## 加一种新块: 三步, 第三步在后端

1. 在 `components/chat/blocks/` 写组件, 入参 `BlockProps`, 失败时 `return <CodeBlock />`
2. 在 `index.ts` 的 `BLOCK_RENDERERS` 加一行
3. **在 `data/system-prompt.md` 里告诉 agent 什么时候产出这种块**

第三步是分界线: **前端认得一个格式, 不等于模型会输出它.** 跳过它的结果是渲染器一行代码都
跑不到, 而前端测试全绿.

如果这种块还要进 kickstart 橱窗, 那就是第四步: 在 `site.toml` 里分配配额, 在 `RenderBadge`
里加图标. 三方契约的完整规则见
[architecture/06](../architecture/06-rendering-contract.md).
