# 渲染契约: 从提示词到屏幕

> 后端 agent 返回的只是一段流式文本. 这篇讲那段文本怎么在界面上变成 Markdown 表格,
> mermaid 流程图和 chart 图表, 以及让这件事发生的那份三方契约 —— 提示词, kickstart
> 问题, 前端查找表, 缺一半都不报错.

## chat 页到底能画什么

agent 说的每句话都是流式文本. 页面上看到的一切都是从那段文本渲染出来的, 一共四种:

| 能力 | 载体 | 谁渲染 |
| :--- | :--- | :--- |
| 业务问答 | 普通 Markdown | `react-markdown` + `remark-gfm` |
| 表格 | Markdown 表格 | 同上 (GFM 表格语法) |
| 流程图 | ` ```mermaid ` 围栏块 | `mermaid` (动态 import) |
| 图表 | ` ```chart ` 围栏块 | **手写 SVG**, 零第三方图表库 |
| SQL 高亮 | ` ```sql ` 围栏块 | `CodeBlock` |

**图表为什么不用图表库**: recharts 之类 500KB 起步, 而 bar 和 line 手写各几十行. 更要紧的
是 dataviz 规范要的 mark 规格 (圆角柱顶, 柱间隙, 克制的网格) 用库反而要一路对抗默认样式.
所以 `components/chat/blocks/chart/` 下面零新增依赖, 纯 SVG.

## 这份契约有三半, 缺一不可

这是这一章最重要的一件事. "让 agent 画一张图"不是一个地方的事, 是三个地方必须对上:

```
data/system-prompt.md          data/site.toml                components/chat/
## Rendering Triggers    <->   [[chat.suggestedActions]] <->  blocks/index.ts
(告诉模型什么短语出什么块)      (12 条问题的短语 + render)     (围栏语言 -> 渲染器)
```

**三半各自失败的方式不同, 而且都不报错:**

- 提示词那节被精简 -> 模型不知道短语意味着什么, 问了也不出块
- kickstart 里的短语写错一个词 -> 触发不稳定, 尤其在小模型上
- 查找表里没有这种语言 -> 块落到 `CodeBlock`, 用户看到一坨 JSON

## 第一半: 提示词里的触发表

`data/system-prompt.md` 里有五节管这件事, 位置在 `## Response Guidelines` 之后,
`## Safety` 之前:

| 节 | 管什么 |
| :--- | :--- |
| `## Rendering Triggers` | 短语 -> 块的对照表. 这是契约本体 |
| `## Diagrams and Charts: The Fence Rule` | 围栏怎么写, 以及**绝不能**用尖括号标签包起来 |
| `## Showing the SQL` | 什么时候把查询给读者看 |
| `## Diagrams` | 什么时候值得画图, 十个节点以内 |
| `## Charts` | chart 的 JSON 形状和渲染器的硬上限 |

触发表长这样:

| 用户说 | 你产出 |
| :--- | :--- |
| "as a Markdown table" | Markdown 表格 |
| "show the SQL" | ` ```sql ` 围栏块 |
| "as a flowchart" / "as a diagram" | ` ```mermaid ` 围栏块 |
| "as a bar chart" / "as a line chart" | ` ```chart ` 围栏块 |

**这五节换数据集时逐字抄, 只换例子.** 母本在 `swap-dataset-cn/ref/system-prompt-render-blocks.md`.
它们描述的是前端能渲染什么, 与数据集无关, 而且措辞是对着渲染器的真实行为调出来的.

为什么措辞不能随便改: 这个仓库跑得起小模型, 而小模型跟的是措辞不是意图. 仓库里已经有一个
补丁 (`agent_app/agent_debugger.py` 的 `normalize_render_blocks`) 专门收拾模型把 chart 包进
`<chart>` 标签的毛病 —— 尖括号标签会被 Markdown 渲染器静默丢弃, 答案到达时图没了, 也没有
任何报错解释为什么. 改写这几节, 就是把那个补丁要防的事重新放出来.

## 第二半: 12 条 kickstart 的渲染配额

`data/site.toml` 里 `[[chat.suggestedActions]]` 恰好 12 条, 每条带一个 `render` 字段.

**为什么要配额**: 随手写 12 个问题, 结果大概率是 12 段纯文字 —— 于是 mermaid 渲染器,
chart 渲染器, SQL 高亮全都没人看得见. 这些按钮是橱窗, 不是问题列表.

所以四类各恰好 3 条:

| `render` | action 里必须原样出现 |
| :--- | :--- |
| `"table"` | `as a Markdown table` **且** `show the SQL` |
| `"flowchart"` | `as a flowchart` |
| `"chart"` | `as a bar chart` 或 `as a line chart` |
| `"free"` | 以上短语一个都不能出现 (含第 1 条固定的 Introduction) |

**`render` 和短语是两件事, 两个都要对.**

- `render` 是**按钮对读者的承诺**: 前端 `components/chat/RenderBadge.tsx` 据它在按钮上画一个
  表格 / 流程 / 柱状的小图标, 读者不点开就知道会画出什么. `free` 故意什么都不画 —— 每个
  按钮都有徽章等于没有徽章
- **短语才是真正让块出现的东西**

只查短语, 图标会撒谎; 只查 `render`, 一个标着图表的按钮会回一段散文. `mise run check-content` 的
`render quota` 一项**两个方向都验**.

### 选题比措辞更要紧

不是随便挑三条加上短语就行:

- **流程图**挑本来就是流程或状态迁移的问题: 生命周期, 漏斗, 状态流转. 给一个排名问题硬套
  流程图, 出来的是装饰. 让节点标签带上查出来的数字, 那才是它比表格强的地方
- **图表**挑形状就是答案的问题: 排名, 趋势, 两个量的差距. `line` 留给有序刻度 (时间, 账龄),
  其余用 `bar`. 差距类问题用双 series
- **表格 + SQL** 挑读者会想验算的问题: 评分卡, 分档明细, 敞口清单

还有两条实用的:

- **点名要哪几列.** 说清楚要 A/B/C/D 四列, 比说"给我一张表"更能让模型真的吐出表格
- **问题问小.** 一条要连着调三次以上工具才能凑齐答案的问题, 直接拆小. 这是给人现场点开看
  的按钮, 转很久的圈就等于坏了

## 第三半: 前端的查找表

```typescript
// components/chat/blocks/index.ts
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
  chart: ChartBlock,
}
```

加一行支持一种块, 删一行关掉一种. 没在表里的语言 (包括 ```python 这种普通代码) 全部落到
`CodeBlock` 兜底.

**chart 的 JSON 形状**, 渲染器只认这个:

```json
{
  "type": "bar",
  "title": "Actual default rate by risk grade",
  "yLabel": "%",
  "categories": ["A", "B", "C", "D", "E"],
  "series": [{ "name": "actual", "values": [3.9, 6.23, 9.89, 15.16, 18.91] }]
}
```

渲染器强制的规则 (不符合一律退回纯文本):

- `type` 是 `bar` (比较类别) 或 `line` (有序刻度上的变化)
- **最多 4 个 series, 最多 24 个 category**
- 每个 series 的值数量必须等于 category 数量, 顺序一致
- 值是纯数字: 不带单位, 不带 `%`, 不能有 `null`

单位放 `yLabel`, 不放值里. 负数没问题, 而且以零为基线, 这正是 `bar` 适合表达"两个量之间
差距"的原因 —— 双 series 一条放假设值一条放实际值, 差距一眼可见.

渲染器内部怎么实现的 (流式期间的残缺围栏, 懒加载, 安全等级, 兜底策略), 见
`agent-app-design-cn` skill 的 `ref/chat-frontend.md`. 那是另一个高度的文档.

## 加一种新块渲染器: 三步, 第三步最常被忘

1. 在 `components/chat/blocks/` 写组件, 入参 `BlockProps`, 失败时 `return <CodeBlock {...props} />`
2. 在 `index.ts` 的 `BLOCK_RENDERERS` 加一行
3. **在 `data/system-prompt.md` 里告诉 agent 什么时候产出这种块**

第三步是分界线: **前端认得一个格式, 不等于模型会输出它.** 跳过它的结果是渲染器一行代码
都跑不到, 而前端测试全绿, 你会以为功能做完了.

如果这种块也要进 kickstart 橱窗, 那就是第四步: 在触发表里加一行短语, 在 `site.toml` 里
分配配额, 在 `RenderBadge` 里加图标.

## 验收: 必须手点

配额脚本只能证明**问法**写对了, 证明不了**模型照做了**. 所以换完数据集必须把 12 条逐条
点一遍, 确认 3 条出表格加 SQL 高亮, 3 条出流程图, 3 条出图表.

出不来最常见的原因是提示词里 `Rendering Triggers` 那节被精简过.
