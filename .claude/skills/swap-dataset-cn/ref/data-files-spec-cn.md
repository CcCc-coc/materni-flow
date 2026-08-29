# `data/` 三个文件的 spec

换数据集要手写的内容全部在这三个文件里. 这篇讲每个文件**长什么样**; 先写哪个后写哪个,
以及为什么顺序本身就是质量保证, 在 [SKILL.md](../SKILL.md) 的推导链那一节.

文案的口吻和格式规矩另见 [writing-style-cn.md](writing-style-cn.md).

---

## `data/system-prompt.md` —— agent 的领域大脑

### 结构

| 节 | 装什么 |
| :--- | :--- |
| 身份和工具 | 你是谁, 有哪几个 tool |
| `## Core Domain Concepts` | 这个行业的基本规则, 外行会猜错的那些 |
| `## Analysis Index` | **源文档每条分析一行, 一条都不能漏** |
| `## Derived Business Concepts` | 从 Index 里挑出外行会算错的, 给精确公式和 SQL |
| `## Table Relationships` | 怎么 JOIN |
| `## Key Status Codes` | 状态码取值 |
| `## SQL Dialect` | PostgreSQL 方言清单, 见下 |
| `## SQL Patterns` | 这个领域常用的查询骨架 |
| `## Response Guidelines` | 回答的组织方式 |
| **渲染层五节** | **逐字抄, 只换例子**. 母本是 [system-prompt-render-blocks.md](system-prompt-render-blocks.md) |
| `## Safety` | 只读, 不许写 |

### 覆盖靠索引, 篇幅靠取舍

`## Analysis Index` 必须覆盖源文档里的**每一条**分析, 每条一行说清它回答什么问题. 但只有
其中**外行会算错的**那些才值得在 `## Derived Business Concepts` 里展开成公式和 SQL.

这两件事不要混为一谈: 索引管的是"能不能被问到", 展开管的是"会不会算错". 只展开一半而
索引漏了几条, 后果是 kickstart 阶段挑不出 12 个问题, 于是有人回头去翻源文档现编 —— 那正是
铁律要防的事.

### 渲染层五节逐字抄

把 [`system-prompt-render-blocks.md`](system-prompt-render-blocks.md) 整段抄进去, 位置在
`## Response Guidelines` 之后, `## Safety` 之前. **只替换里面的例子** (表名, 指标名, 数字),
不要改结构, 不要改措辞, 不要精简.

那五节 (`Rendering Triggers` / `The Fence Rule` / `Showing the SQL` / `Diagrams` /
`Charts`) 管的是**前端能渲染什么**, 与数据集无关, 措辞是对着 `components/chat/blocks/` 的
真实行为调出来的. 这个仓库可以跑在小模型上, 小模型跟的是措辞不是意图.

`Rendering Triggers` 那张表和 kickstart 的措辞是**同一份契约的两半**: 表里写的短语, 就是
`[[chat.suggestedActions]]` 的 `action` 里要原样出现的短语. 两边对不上, 触发就不稳定.

### SQL 一律写 PostgreSQL 方言

agent 在**任何环境下**读的都是 PostgreSQL, 本地也一样. 一段 SQLite 方言的例子在本地永远绿,
在线上永远错, 而且**不报错, 只是答案变差** —— agent 的 SQL 工具把数据库报错转成字符串还给
模型, 没有任何监控会响.

| 别写 (SQLite) | 写成 (PostgreSQL) |
| :--- | :--- |
| `strftime('%Y-%m', d)` | `TO_CHAR(d, 'YYYY-MM')` |
| 用 `strftime('%m', ...)` 算季度 | `EXTRACT(QUARTER FROM d)` |
| `DATE(d, '-90 days')` | `d - INTERVAL '90 days'` |
| `JULIANDAY(a) - JULIANDAY(b)` | `a - b` (日期相减直接得整数天) |
| `WHERE is_flag = 1` | `WHERE is_flag` (布尔就是布尔) |
| `SUM(is_flag)` | `SUM(CASE WHEN is_flag THEN 1 ELSE 0 END)` |
| 浮点列上的 `ROUND(x, 2)` | `ROUND(x::numeric, 2)` |

最后一条最阴: `ROUND(numeric, int)` 存在而 `ROUND(double precision, int)` 不存在. 所以
`ROUND(100.0 * a / b, 2)` 没问题 (`100.0` 这个字面量把整个表达式变成 numeric), 而表达式里
一旦混进浮点列就炸. **表达式里有浮点列就加 `::numeric`.**

另外 PostgreSQL 比 SQLite 严的三处, 写的时候就绕开: `GROUP BY` 要列全 SELECT 里所有非聚合
列; `HAVING` 不认 SELECT 里的别名, 把表达式重写一遍; `window` 之类的保留字不能当别名.

`## SQL Dialect` 那一节是给模型看的同一份规则, 换数据集时**保留结构只换例子**, 和渲染层
五节一样待遇.

### 一个和检查脚本打架的坑

`mise run check` 会扫提示词里 ` ```sql ` 围栏块内部的 `FROM x` / `JOIN x`, 确认表真的存在.
它只扫围栏块内部, 所以散文里写 `EXTRACT(QUARTER FROM d)` 不会误报.

用了 CTE 的话, 检查脚本认得 `WITH name AS (` 这种自定义名字, 不会把它当成缺失的表.

**如果一个检查逼着你把内容写歪, 先怀疑检查, 不要怀疑内容.**

---

## `data/site.toml` —— 界面上说的每一句话

### 段落, 和它在屏幕上对应的位置

| TOML 段 | 屏幕上是什么 | 来源 |
| :--- | :--- | :--- |
| `[brand]` | 导航栏那个两段着色的 logo (`logoPrefix` + `logoAccent`), 页脚名字 | **用户提供的品牌名** |
| `[seo]` | `<head>` 的 title / description / keywords / locale | summary |
| `[[capabilities]]` × 4 | **首页四张能力卡, 和 agent 页四张洞察卡, 同一份** | 提示词的四条主线 |
| `[home]` | tagline, description, blurb, techStack | summary + 数据库现数 |
| `[home.headline]` | 大标题拆成两截, 两种颜色 | 品牌名 |
| `[home.cta]` | 首页底部那个大按钮 | 通用 |
| `[home.businessContext]` | 打开说明弹窗那个按钮的文字, 和弹窗的标题副标题 | 正文在 `business-context.md`, 这里只是**标签** |
| `[chat]` | agent 自称的名字, 欢迎语, 示例, 输入框 placeholder, 建议提示 | **用户提供的 agent 名** |
| `[chat.messages]` | 横幅正文, 等待提示 | 与数据集无关, 照抄 |
| `[[chat.suggestedActions]]` × 12 | 输入框上方那 12 个 kickstart 按钮 | 提示词的 Analysis Index |

### 四条硬约束

**一, 必填 key 少一个 build 就挂.** `lib/site/schema.ts` 的 `REQUIRED_SITE_KEYS` 列了每个
必须存在的 key, `lib/site/load.ts` 解析时逐个查. 只在 `npx next build` 时才拦得住,
`mise run check` 查不到.

**二, 图标名必须在 `lib/icons.ts` 里.** `assertIconsExist` 会报出坏名字和全部合法名字, 同样
只在 `next build` 时抛. 不查的话拼错的图标会静默渲染成兜底图标 —— 卡片看着好好的, 就是配错
了图. 需要新图标就在 `lib/icons.ts` 顶部 import 并加进 `ICONS`, 从 lucide-react 挑.

**三, TOML 数组表的坑.** 一旦开始 `[[...]]` 数组, 后面每个裸 key 都属于该数组的**最后一个
元素**. 所以每一节的普通字段必须写在 `[[...]]` 之前. 写反了不报错, 只会静默错位.

**四, 值必须是 JSON 能序列化的.** `SiteConfig` 是从 server component 当 props 传进 client
component 的. TOML 支持而 JSON 不支持的东西 (比如日期字面量) 不要写进去.

### `[[capabilities]]` 只有一份

四条业务主线, 首页和 agent 页渲染的是**同一份**, 共享 `components/CapabilityCard.tsx`.

每条四段:

- `icon` —— `lib/icons.ts` 里注册过的名字
- `title` —— 概念名. 对内行精确, 对其他所有人等于没写
- `subtitle` —— 一句白话. 陌生人先读到的是这句
- `tooltip` —— 两三句解释, 里面**不许再有黑话**. 写法见 [writing-style-cn.md](writing-style-cn.md)

**不要因为两个页面尺寸不同就写两份.** 两份配置描述同一组东西迟早会各走各的 (同一条主线起
了不同的名字, 配了不同的图标, 只有一边有 tooltip), 而且不会有任何测试失败, 因为两边各自都
合法. 一份数据两处渲染, 漂移在结构上就不可能发生.

### `[[chat.suggestedActions]]` 恰好 12 条, 四类各 3 条

这 12 条是**橱窗, 不是问题列表**. 随手写 12 个问题, 结果大概率是 12 段纯文字 —— 于是
mermaid 渲染器, chart 渲染器, SQL 高亮全都没人看得见. 所以配额写死:

| `render` | 要出什么 | `action` 里必须原样出现 |
| :--- | :--- | :--- |
| `"table"` | Markdown 表格 **且** SQL | `as a Markdown table` 且 `show the SQL` |
| `"flowchart"` | mermaid 流程图 | `as a flowchart` 或 `as a diagram` |
| `"chart"` | chart 图表 | `as a bar chart` 或 `as a line chart` |
| `"free"` | 散文 (含第 1 条 Introduction) | 以上短语**一个都不能出现** |

每条四个字段全是必填: `render`, `title`, `label`, `action`.

**两半缺一不可.** `render` 是**按钮对读者的承诺** —— 前端 `components/chat/RenderBadge.tsx`
据它在按钮上画一个表格 / 流程 / 柱状的小图标, 读者不点开就知道会画出什么, `free` 故意什么
都不画 (每个按钮都有徽章等于没有徽章). 而真正让块出现的是 `action` 里那句短语.

只查短语, 图标会撒谎; 只查 `render`, 一个标着图表的问题会回一段散文. `mise run check` 的
`render quota` **两个方向都验**.

第 1 条固定是 Introduction / "What can you do?", `render = "free"`.

**选题比措辞更要紧**, 不是随便挑三条加上短语就行:

- **流程图**挑本来就是流程或状态迁移的问题: 生命周期, 漏斗, 状态流转. 给一个排名问题硬套
  流程图, 出来的是装饰. 让节点标签带上查出来的数字, 那才是它比表格强的地方
- **图表**挑形状就是答案的问题: 排名, 趋势, 两个量的差距. `line` 留给有序刻度 (时间, 账龄),
  其余用 `bar`. 差距类问题用双 series (一条是假设值, 一条是实际值)
- **表格 + SQL** 挑读者会想验算的问题: 评分卡, 分档明细, 敞口清单

还有两条实用的:

- **点名要哪几列.** 说清楚要 A/B/C/D 四列, 比说"给我一张表"更能让模型真的吐出表格, 顺带
  还能让回答快下来
- **问题问小.** 一条要连着调三次以上工具才能凑齐答案的问题, 不要靠调措辞救, 直接拆小.
  这是给人现场点开看的按钮, 转很久的圈就等于坏了, 哪怕最后答案是对的

---

## `data/business-context.md` —— 首页那个说明弹窗

普通 Markdown, 2 到 3 屏可滚动内容, 由 `components/BusinessContextModal.tsx` 渲染. 走的是
chat 页同一个 Markdown 渲染器, 所以 ` ```mermaid ` 围栏会真的画成图.

弹窗的标题和副标题**不在这个文件里**, 在 `site.toml` 的 `[home.businessContext]` —— 那三行
是按钮和窗框的标签, 不是正文.

### 它讲的是这个 agentic App, 不是这个数据集

这条决定了全篇的取景. 对外露出去的是"一份数据加一个能查它的 agent", 但读者真正需要知道的是
**这个 App 是干什么的**: 它替谁解决什么问题, 凭什么解决, 以及它今天做到哪一步.

所以标题走 "The business behind the agent" 这个调子, 不要写成 "the business behind the
data". 一字之差, 前者在介绍产品, 后者在介绍附件.

### 六节结构, 按顺序填

前三节讲世界, 后三节讲这个 App 在这个世界里干什么. 六节就是六个 `##` 标题, 术语表用加粗
开头的 bullet.

| # | 节 | 必须回答 | 来源 |
| :--- | :--- | :--- | :--- |
| 1 | 这门生意怎么赚钱 | 收入几条线各占多少, 最大的成本是什么 | 源文档的商业模式段 |
| 2 | 钱从哪里悄悄漏掉 | 每条都要回答"**为什么它不会自己暴露**" | 源文档的关键问题 |
| 3 | 这些事在数据里长什么样 | **先说清楚为什么这些线索必须放在一起看**, 再说记录了什么, 覆盖多长时间, 并点明基准日期是固定的 | ER 文档 + summary |
| 4 | agent 拿这些数据做什么 | 读 schema, 写 SQL, 解读结果; 该出图时出 diagram 和 chart | 通用能力, 不来自数据集 |
| 5 | 你可以问什么, 以及怎么读答案 | 按四条主线分组的问题清单, 末尾补这个领域特有的解读陷阱 (比如平均值会稀释掉结论) | 提示词的 Analysis Index |
| 6 | 只读之外 (本 App 不含) | 见下 | 通用 |

**第 2 节是全篇的重心.** 每一条都要回答"为什么这个亏损在财报上看不出来" —— 那才是这个 App
存在的理由. 只罗列"我们能查 X"没有说服力, 因为读者不知道为什么需要查.

**第 6 节的分寸.** 这一节讲产品边界和方向, 必须同时说清三件事, 少一件就变成吹牛:

1. 这个 App 是**故意**只读的, 它是给外部看的演示
2. 同一套 agent 架构可以挂上写操作的 tool, 真正改后端状态 (这不是设想: 写操作是
   dataset-specific 的 `@tool`, 加在 `agent_app/one/one_04_agent.py` 里)
3. 真要上写操作, 前提是**权限护栏**和**可审计轨迹** —— 谁在什么时候改了什么, 每一笔都要
   留痕, 而不是让模型直接对生产库动手

第 3 点不能省. 少了它, 这一节读起来就是"我们还能让 AI 乱改数据", 反而减分.
