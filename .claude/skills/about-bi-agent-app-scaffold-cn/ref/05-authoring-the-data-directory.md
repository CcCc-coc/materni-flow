# `data/` 下那几个文件怎么写

换数据集就是重写这一个目录. 这篇讲每个文件里该写什么, 以及每个字段对应屏幕上的哪块东西.

完整的执行顺序 (先写哪个后写哪个, 为什么) 在 `swap-dataset-cn` skill 里, 这篇只讲**形状**.

---

## `dataset.toml` — 后端读的那几个值

```toml
[project]
name = "smbll"                    # 这个部署在 LLM 花费配额里的标识, 不再命名任何数据库对象

[database]
schemaName = "..."                # PostgreSQL schema 名: 小写, 下划线, <= 63 字符
displayName = "..."               # 只是给 agent 看的标签, 不必对应任何真实库名
tableInsertOrder = [...]          # 外键依赖顺序, 父表在前
```

`tableInsertOrder` 是**两个方向的唯一真相**: 插入正着走, 删除倒着走. 从一个列表推导两个
方向, 是它们不会漂移的原因. `mise run check` 拿它对撞 SQLite 种子, 两个方向都验 —— 多了
一张或少了一张都当场报.

**不要手写这个顺序**, 从种子文件的外键关系拓扑排序出来.

---

## `site.toml` — 界面上说的每一句话

前端唯一的文案来源. 结构和它在屏幕上对应的位置:

| TOML 段 | 屏幕上是什么 |
| :--- | :--- |
| `[brand]` | 导航栏那个两段着色的 logo (`logoPrefix` + `logoAccent`), 页脚名字 |
| `[seo]` | `<head>` 里的 title / description / keywords, 分享出去时的预览 |
| `[[capabilities]]` × 4 | **首页四张能力卡, 和 agent 页四张洞察卡, 同一份** |
| `[home]` | 首页大标题 / 副标题 / 一段介绍 / 技术栈标签 / 数据规模那行 |
| `[home.headline]` | 大标题拆成两截, 两种颜色 |
| `[home.cta]` | 首页底部那个大按钮 |
| `[home.businessContext]` | 打开说明弹窗那个按钮的文字, 和弹窗的标题副标题 |
| `[chat]` | agent 自称的名字, 欢迎语, 输入框 placeholder, 建议提示 |
| `[chat.messages]` | 对话上方那条 banner, 限额提示, "上一条还在跑"提示 |
| `[[chat.suggestedActions]]` × 12 | 输入框上方那 12 个 kickstart 按钮 |

### 三条硬约束

**一, 必填 key 会在 build 时拦住你.** `lib/site/schema.ts` 的 `REQUIRED_SITE_KEYS` 列了每个
必须存在的 key, `lib/site/load.ts` 在解析时逐个查, 少一个就抛异常并报出 key 名. 因为 TOML
不被编译器检查, 缺一个 key 的后果是组件收到 `undefined` 然后在线上渲染成一个空标题.

**二, 图标名会在 build 时拦住你.** `icon` 必须是 `lib/icons.ts` 里注册过的名字.
`assertIconsExist` 会报出坏名字和全部合法名字. 不查的话, 拼错的图标会静默渲染成兜底图标 ——
卡片看着好好的, 就是配错了图, 没人会注意到.

**这两个检查只在 `npx next build` 时跑**, `mise run check` 查不到. 换完数据集两个都要跑.

**三, TOML 数组表的坑.** 一旦开始 `[[...]]` 数组, 后面每个裸 key 都属于该数组的最后一个
元素. 所以每一节的普通字段必须写在 `[[...]]` 之前. 写反了不报错, 只会静默错位.

### `[[capabilities]]` 只有一份

四条业务主线, 首页和 agent 页渲染的是**同一份**, 共享 `components/CapabilityCard.tsx`.

每条三段:

- `title` — 概念名. 对内行精确, 对其他所有人等于没写
- `subtitle` — 一句白话. 陌生人先读到的是这句
- `tooltip` — 两三句解释, hover / 键盘聚焦 / 手机点按时弹出

**tooltip 里不许再有黑话.** 用一个内行词去解释另一个内行词, 是这个字段存在的意义所反对的
那件事.

它曾经是两份配置 (`home.capabilities` 和 `chat.insights`), 结果已经漂移: 同一条主线在首页
叫 "Portfolio Concentration", 在 agent 页叫 "Portfolio Health", 图标不同, tooltip 只有一边
有. 没有测试失败, 因为两边各自都合法. **一份数据两处渲染, 漂移在结构上就不可能发生.**

### `[[chat.suggestedActions]]` 恰好 12 条, 四类各 3 条

这是渲染契约的一半, 完整规则见 [04-rendering-contract.md](04-rendering-contract.md).
要点:

- 第 1 条固定是 Introduction / "What can you do?", `render = "free"`
- 其余 11 条逐条对着提示词的 `## Analysis Index` 改写成用户口吻
- **挑不出来说明提示词覆盖不够, 回去补提示词, 不要在这里现编**

最后这条是纪律: 提示词定义能力边界, 下游只能换措辞, 不能新增一项提示词没教的能力. 仓库里
真出过事故 —— 提示词只覆盖了源文档 20 条分析里的 13 条, 而 12 个 kickstart 是另起炉灶从
数据集文档写的, 于是首页有两个按钮问的分析提示词根本没教. 所有测试通过, 用户点下去模型
只能即兴发挥.

---

## `business-context.md` — 首页那个说明弹窗

普通 Markdown, 走的是 chat 页同一个渲染器, 所以里面写 ` ```mermaid ` 围栏会真的画成图.

**它讲的是这个 App, 不是这个数据集.** 露出去的是"一份数据加一个能查它的 agent", 但读者
真正需要知道的是这个 App 替谁解决什么问题. 标题走"the business behind the agent"这个调子,
不要写成"the business behind the data".

**两条硬要求**: 写给完全不懂这行的陌生人看, 只靠常识能读完; 讲行业不讲雇主, 讲问题不讲
项目 (不出现实习 / 公司名 / 课程 / 作业这类痕迹).

**六节结构**, 前三节讲世界, 后三节讲这个 App 在这个世界里干什么:

1. 这门生意怎么赚钱
2. 钱从哪里悄悄漏掉 —— **全篇重心**, 每条都要回答"为什么它不会自己暴露"
3. 这些事在数据里长什么样
4. agent 拿这些数据做什么
5. 你可以问什么, 以及怎么读答案
6. 只读之外 (本 App 不含)

第 6 节要同时说清三件事, 少一件就变成吹牛: 这个 App 是**故意**只读的; 同一套架构可以挂写
操作的 tool; 真上写操作的前提是**权限护栏**和**可审计轨迹**. 第三点不能省, 少了它这节读
起来就是"我们还能让 AI 乱改数据".

**两个格式约束**:

- 整份最多一张 mermaid 图, 十个节点以内. 判据很简单: 如果这张图只是把上一句话又说了一遍,
  那就删图留话. 第二张图一定是装饰
- **HTML 注释会被加载器剥掉再渲染**. 这是补过的一个真 bug: `react-markdown` 没装
  `rehype-raw`, 不解释 HTML, 于是 `<!-- 给下一个作者的说明 -->` 会原样打印成弹窗里的一段
  正文. 现在 `loadBusinessContext()` 会先剥注释, 所以你可以放心在文件里写批注

---

## `system-prompt.md` — agent 的领域大脑

结构大致是:

| 节 | 装什么 |
| :--- | :--- |
| 身份和工具 | 你是谁, 有哪几个 tool |
| `## Core Domain Concepts` | 这个行业的基本规则, 外行会猜错的那些 |
| `## Analysis Index` | **源文档每条分析一行, 一条都不能漏** |
| `## Derived Business Concepts` | 从 Index 里挑出外行会算错的, 给精确公式和 SQL |
| `## Table Relationships` | 怎么 JOIN |
| `## Key Status Codes` | 状态码取值 |
| `## SQL Dialect` | PostgreSQL 方言清单, 见 [03](03-one-database-everywhere.md) |
| `## SQL Patterns` | 这个领域常用的查询骨架 |
| `## Response Guidelines` | 回答的组织方式 |
| **渲染层五节** | **逐字抄, 只换例子**, 见 [04](04-rendering-contract.md) |
| `## Safety` | 只读, 不许写 |

### 覆盖靠索引, 篇幅靠取舍

`## Analysis Index` 必须覆盖源文档里的每一条分析, 每条一行说清它回答什么问题. 但只有其中
**外行会算错的**那些才值得在 `## Derived Business Concepts` 里展开成公式和 SQL.

这两件事不要混为一谈: 索引管的是"能不能被问到", 展开管的是"会不会算错".

### 写完必须把每段 SQL 对着真库跑一遍

**而且必须走 PostgreSQL**, 不能拿本地 sqlite 验 —— 理由见 [03](03-one-database-everywhere.md),
那正是这套流程踩过的坑.

跑不通的例子比没有例子更糟: 模型会照抄, 然后在用户面前失败. 这一步还会顺带暴露"语法对但
公式写错" —— 结果数字明显不对就能看出来.

### 一个和检查脚本打架的坑

`mise run check` 会扫提示词里 ` ```sql ` 块中 `FROM x` / `JOIN x` 的表名, 确认它们真的存在.
它扫的是围栏块内部, 所以散文里写 `EXTRACT(QUARTER FROM d)` 不会误报. 但如果你在 SQL 例子
里用了 CTE, 记得检查脚本认得 `WITH name AS (` 这种自定义名字, 不会把它当成缺失的表.

---

## 前端文案的写法规范

这一节管 `site.toml` 和 `business-context.md` 里每一个会显示给用户的字符串. 不管代码注释,
不管提示词.

**第一条: 不要用破折号.** 不要用 `—`, 也不要用 `--` 当停顿. 这是最容易暴露"AI 写的"的一个
特征, 因为模型极其偏爱用它来塞补充说明, 一段话里出现三四次是常态, 而人类文案很少这样写.

破折号出现的地方通常说明这句话本来就该断开. 三种改法: 断成两句; 换成逗号从句; 把补充说明
挪进另一个字段. 标题里非要分隔就用冒号.

**第二条: 叙述性语言, 简单格式.** 用完整句子把事情讲清楚, 不要写成关键词罗列. 允许的格式
只有加粗, 标题, bullet. 不要表格, 不要嵌套列表, 不要 emoji, 不要行内代码块 (那是给开发者
看的, 这里的读者不是).

**第三条: 数字要现场数出来.** `home.blurb` 里的表数和行数, 此刻从数据库数, 不要抄旧值也
不要估. 仓库里曾经写着 "~52,500 records" 而真实是 111,153, 差一倍多, 而它恰好摆在读者判断
"这 demo 有多真"的位置.
