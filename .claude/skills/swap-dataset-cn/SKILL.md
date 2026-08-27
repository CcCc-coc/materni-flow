---
name: swap-dataset-cn
description: 把整个仓库从当前数据集切换到另一个数据集和另一个业务领域. 输入默认是 tmp/dataset 目录 (summary, business context, ER, SQL queries, data/*.tsv, *.sqlite). 覆盖提示词, 两个配置文件, kickstart 问题, 数据库本体, 脚本里的硬编码问题, 以及之后的视觉改造. 用户敲 /swap-dataset-cn 时执行.
disable-model-invocation: true
---

# 换数据集

---

## 1. 这件事到底在做什么

这个仓库的本质是三样东西: **一个提示词, 一个数据库, 一个网站**. 换数据集就是把这三样同时换掉, 而且必须换得一致. 网站说自己是贷款分析, 提示词教的是医院排班, 数据库里躺着电商订单, 这种状态是能跑起来的, 它不报错, 它只是全程撒谎.

这就是这个 skill 存在的理由. 仓库历史上真发生过: 一次换数据集只改了提示词和前端, 留下了整整一个模块的医院写操作和三段描述 "产科病房排班数据库" 的 docstring, 在一个借贷代码库里躺了几个月. 没有任何测试失败.

所以工作方式不是 "看到哪改哪", 而是**先建立完整映射, 再逐项执行, 最后靠工具验证**. 下面第 2.2 节那张清单就是完整映射, 它是这个 skill 最重要的部分. 漏掉其中一行, 就会重演上面那件事.

还有一条贯穿始终的判断: **能配置化的东西早就配置化了, 剩下要手改的都是 "内容"**. 提示词, kickstart 问题, 数据库, 这三样不可能从配置里生成, 它们必须被重写. 不要试图把它们塞进配置文件.

### 一个目录: `data/`

这个仓库**一个 repo 只服务一个数据集**, 没有 `dataset/<name>/` 那种一个目录装一个
App 的机制. 但换数据集要改的东西**全部在 `data/` 一个目录里**, 换数据集是把这个目录
的内容整体重写:

| 文件 | 装什么 | 谁读 |
| :--- | :--- | :--- |
| `.env.defaults` | `SCHEMA_NAME` —— 后端唯一要改的一行 (不在 `data/` 里) | Python |
| `data/site.toml` | 界面上说的每一句话, 4 张能力卡, 12 条 kickstart | Next.js |
| `data/business-context.md` | 首页那个 "这解决什么问题" 弹窗的正文 | Next.js |
| `data/system-prompt.md` | agent 的领域大脑 | 提示词 |
| `data/data.sqlite.example` | 数据本体, 播种到 `tmp/data.sqlite` | 两边 |

**唯一的例外是写操作的 `@tool`**, 它在 `one_04_agent.py` 里, 因为那是代码不是内容.

`site.toml` 曾经是 `config/site.ts`, 改成 TOML 是为了让一次换数据集变成"换一个目录"
而不是"一个散落全仓库的 diff". 代价是编译器不再检查它, 补偿在 `lib/site/load.ts`:
`REQUIRED_SITE_KEYS` 查缺 key, `assertIconsExist` 查图标名, 两者都在 `next build`
时抛. 所以**换完数据集必须跑一次 `npx next build`**, 光跑 `mise run check` 查不到
图标名和缺 key.

**这个结构有一个代价, 必须正视.** ba 那种"一次接入只准碰一个目录, 用 `git status`
就能验收"的机械标准, 在这里只对一半成立: `data/` 之外确实还有要动的 (脚本里的硬编码
问题, 测试里的表名). 补偿办法是 2.2 那张完备性清单和 2.3 那一串验证, 两个都不能省.

---

最后, 换数据集分**两个阶段**, 中间必须停下来让用户验收:

- **阶段一 (2.1 到 2.3)**: 换内容. 做完之后功能是对的, 但页面还穿着上一个行业的衣服.
- **阶段二 (2.4)**: 换视觉. 配色, 排版, 图标, 首页和 chat 页的布局. 这一步要用 `frontend-design:frontend-design` skill, 而且必须在用户确认阶段一没问题之后才开始.

不要把两个阶段混在一起做. 混在一起的话, 一旦效果不对, 分不清是内容错了还是样式错了.

---

## 2. 工作流

### 2.1 鉴别输入信息

默认输入目录是 `tmp/dataset/`. 用户可能给别的路径, 但结构是固定的.

先 `ls` 一遍确认拿到了什么. 典型长这样 (`<name>` 是数据集名, 比如 `fintech_smb_lending_pipeline_medium`):

| 文件 | 里面是什么 | 拿它干什么 |
| :--- | :--- | :--- |
| `00-<name>_summary.md` | 一段话讲清公司, 业务, 表数量, 行数, 能回答什么问题 | 最先读. 它是全局地图, 决定 site.ts 的措辞基调 |
| `01-<name>_business_context.md` | 公司画像, 商业模式, 行业科普, 术语表, 关键指标公式 | 提示词的 "Core Domain Concepts" 和 "Derived Business Concepts" 全部来自这里 |
| `02-<name>_er_document.md` | ER 图, 表定义, 完整 DDL, 数据生成规则 | 表清单, 外键依赖顺序, 提示词的 "Table Relationships" |
| `03-<name>_sql_queries.md` | 20 条业务 SQL, 每条带业务背景和难度 | 提示词的 "SQL Patterns", kickstart 问题, 脚本里的测试问题 |
| `04-<name>_data_generator.py` | 造数脚本 | 一般不用. 只在需要理解字段取值范围时翻 |
| `<name>.sqlite` | 数据库本体 | 直接替换 `data.sqlite.example` |
| `data/NN_<table>.tsv` | 每张表的数据 | **每个只看前 3 行**, 确认字段名和取值形态即可. 不要整个读, 有几十 MB |

带 `-cn` 后缀的是中文版, 内容等价. **读英文版**, 因为产出的代码和提示词都是英文的, 读中文版会在翻译上浪费一轮.

读完之后, 你手上应该能回答这几个问题. 答不上来就回去再读:

- 这家公司做什么生意, 靠什么赚钱?
- 有哪些表, 外键依赖顺序是什么 (父表在前)?
- 这个领域有哪些**外行会猜错** 的术语和公式? (这些是提示词的核心, 通用 SQL 知识不是)
- 用户最想问的 5 到 10 个业务问题是什么?

### 2.2 推导链: 顺序本身就是质量保证

**这一节是整个 skill 最重要的部分, 比下面那张清单重要.**

换数据集要产出的东西 (提示词, kickstart 问题, 首页文案, tooltip, businessContext)
描述的是**同一份领域知识**. 如果它们各自去读数据集文档、并行地写出来, 就一定会漂
移 —— 不是可能, 是一定. 这不是假设, 仓库里就有现成的事故:

> 借贷那版的提示词只保留了源文档 20 条 query 里的 13 条, 丢掉了第 6 条
> "Monthly Application Volume Trends" 和第 7 条 "Loan Officer Performance
> Scorecard". 而 12 个 kickstart 问题是**另起炉灶从数据集文档写的**, 于是又把这两
> 条捡了回来. 结果: 首页有两个按钮, 问的分析提示词根本没教. 所有测试通过, 构建
> 成功, 没有任何东西报错 —— 用户点下去, 模型只能即兴发挥.

**根治办法不是加校验, 是改顺序.** 自然语言的一致性没法 lint, 那是模糊标准, 硬做
只会得到一堆 warn 然后没人看. 但**串行推导可以让漂移根本无法发生**: 每一步只从上
一步的产物推导, 不回头读原始文档.

#### 铁律

> **提示词定义能力边界. 下游只能换措辞, 不能新增一项提示词没教的能力.**

kickstart 问题、能力卡、tooltip、businessContext 的"能问什么", 全部是提示词的**改写**,
不是数据集文档的**再解读**. 想让首页出现某个分析, 唯一的合法路径是先把它写进提示词.

#### 六步, 严格按顺序

**第 1 步. 数据库落地. 而且"落地"到 PostgreSQL 才算数.**

**先确认输入目录里有没有 `.sqlite`**, 因为数据集有两种给法:

```bash
ls tmp/dataset/*.sqlite
```

| 情况 | 怎么办 |
| :--- | :--- |
| 有 `.sqlite` | 直接用它 |
| 没有, 只有 `04-<name>_data_generator.py` | **先跑生成器造出 sqlite**, 再往下走 |

跑生成器之前先读一眼它的开头: 它通常要指定输出路径, 有的还要装额外的包 (faker 之类).
造完再 `ls -lh` 看一眼大小对不对得上 er_document 里声称的量级 -- 生成器跑挂一半会留下
一个能打开但只有几张表的文件, 那种失败不报错.

拿到 sqlite 之后:

```bash
cp tmp/dataset/<name>.sqlite data/data.sqlite.example
mise run setup-db      # 播种到 tmp/data.sqlite
# 填 .env.defaults 的 SCHEMA_NAME (建表顺序是算出来的, 不用填)
mise run check         # 种子有没有表, 外键成不成环, 当场就报
mise run sync-db       # 发布到 PostgreSQL 的本项目 schema
mise run verify-db     # 逐表对行数
```

**最后两步不是可选的.** agent 在任何环境下读的都是 PostgreSQL, 本地也一样, 所以不同步
就等于没有数据库: 第 2 步验证 SQL 会报 schema 缺表, `mise run dev` 起来的 agent 也答
不出东西. `data/data.sqlite.example` 现在只是**种子和同步源**, 不再是任何人查询的对象.

`schemaName` 用数据集名 (下划线, 不要连字符, 63 字符以内). 它是这个项目在共享 Neon 实例
里的命名空间, 别的项目在别的 schema 里, 我们的任何一条 SQL 都不会提到它们.

*为什么必须第一:* 后面每一步的验证都要拿它当基准. 顺序错了当场就报.

**同时把体积预算过一眼.** 线上是 NeonDB 的 500MB 配额, 而且那个库是**和别的项目共用
的**, 我们只占其中一个 schema, 所以真实预算比 500MB 还小. 这条比下面任何一条内容质量
的要求都硬 -- 内容写差了可以改, 数据塞不进去是直接上不了线.

```bash
ls -lh data/data.sqlite.example
```

PostgreSQL 存同一份数据比 SQLite 大 (每行的元组头, 对齐填充, 索引和主键约束). 这个
数据集实测是 7.4MB -> 11MB, 约 1.5 倍; 宽表多, 索引多的数据集会更高. 拿 **乘 4** 当
上界估还是稳的: sqlite 超过 **120MB** 就在动手前跟用户确认要不要减行, 别等同步的时候
才发现.

估算只是估算, 真实数字在同步之后量, 见 2.3.

**第 2 步. 写提示词. 这是唯一允许通读数据集全部文档的一步.**
输入: business_context + er_document + sql_queries 全文.

- **必须覆盖 sql_queries 里的每一条 query.** 做法是先写一节 `## Analysis Index`,
  20 条每条一行 (这条分析回答什么问题), 然后挑其中**外行会算错的**那些, 在
  `## Derived Business Concepts` 里给出精确公式和 SQL. 覆盖靠索引, 篇幅靠取舍 ——
  两者不要混为一谈.
- **把 [`ref/system-prompt-render-blocks.md`](ref/system-prompt-render-blocks.md)
  整段逐字抄进去**, 放在 `## Response Guidelines` 之后, `## Safety` 之前. 只替换里面
  的例子 (表名, 指标名, 数字), 不要改结构, 不要改措辞, 不要精简.

  那五节 (`Rendering Triggers` / `The Fence Rule` / `Showing the SQL` / `Diagrams` /
  `Charts`) 管的是**前端能渲染什么**, 与数据集无关, 措辞是对着
  `components/chat/blocks/` 的真实行为调出来的. 仓库里已经有一个补丁
  (`agent_app/agent_debugger.py` 的 `normalize_render_blocks`) 专门收拾模型把 chart
  包进 `<chart>` 标签的毛病, 改写这几节等于把那个教训重踩一遍.

  **`Rendering Triggers` 那张表和第 3 步的 kickstart 措辞是同一份契约的两半.** 表里
  写的短语, 就是 kickstart 的 `action` 里要原样出现的短语. 两边对不上, 触发就不稳定.
- 写完**把提示词里每一段 SQL 对着真库跑一遍**. 跑不通的例子比没有例子更糟, 模型会
  照抄.

*一个坑:* `mise run check` 会把 `FROM x` / `JOIN x` 当表名校验, 它分不清散文和 SQL.
`drawn from a zero baseline` 里的 `from a` 会被判成表 `a`. 换个说法即可.

*另一个坑, 这条曾经真的上过线:* **提示词里的 SQL 一律写 PostgreSQL 方言.**

这个仓库以前本地读 SQLite, 线上读 PostgreSQL, 于是每一段提示词 SQL 都是对着 SQLite
写的、对着 SQLite 验的, 然后发到 PostgreSQL 环境. 症状不是崩溃 -- agent 的 SQL 工具把
数据库报错转成字符串还给模型, 所以只表现为答案变差, 没人看得见. 这次改成两边都读
PostgreSQL 之后回头验了一遍旧提示词: **16 段例子里 6 段在 PostgreSQL 上跑不通.**

写的时候直接避开这几个:

| 别写 (SQLite) | 写成 (PostgreSQL) |
| :--- | :--- |
| `strftime('%Y-%m', d)` | `TO_CHAR(d, 'YYYY-MM')` |
| 用 `strftime('%m', ...)` 算季度 | `EXTRACT(QUARTER FROM d)` |
| `DATE(d, '-90 days')` | `d - INTERVAL '90 days'` |
| `JULIANDAY(a) - JULIANDAY(b)` | `a - b` (日期相减直接得整数天) |
| `WHERE is_flag = 1` | `WHERE is_flag` (布尔就是布尔) |
| 浮点列上的 `ROUND(x, 2)` | `ROUND(x::numeric, 2)` |

最后一条最阴: `ROUND(numeric, int)` 存在而 `ROUND(double precision, int)` 不存在, 所以
`ROUND(100.0 * a / b, 2)` 没问题 (`100.0` 这个字面量把整个表达式变成 numeric), 而表达式
里一旦混进 float 列就炸. 表达式里有浮点列就加 `::numeric`.

另外 PostgreSQL 比 SQLite 严的两处, 写的时候就绕开: `GROUP BY` 要列全 SELECT 里所有
非聚合列; `HAVING` 不认 SELECT 里的别名, 把表达式重写一遍.

**提示词里那节 `## SQL Dialect` 是给模型看的同一份规则**, 换数据集时保留结构只换例子,
和 `## Rendering Triggers` 一样待遇.

**第 3 步. 写 kickstart 12 条.**
输入: **只看第 2 步产出的提示词**, 不要回头翻 sql_queries.

逐条对着 `## Analysis Index` 挑 11 条改写成用户口吻的问题 (第 1 条固定是
"Introduction / What can you do?"). 挑不出来说明提示词覆盖不够, 回第 2 步补, 不要
在这里现编.

##### 渲染配额: 这 12 条是橱窗, 不是问题列表

随手写 12 个问题, 结果大概率是 12 段纯文字 -- 于是 mermaid 渲染器
(`MermaidBlock.tsx`), chart 渲染器 (`ChartBlock.tsx`), SQL 高亮 (`CodeBlock.tsx`)
全都没人看得见. 这个 App 是拿去给人看的, 三个渲染器一个都不露面, 等于白写. 所以配额
写死, **四类各恰好 3 条**:

| 类别 | 要出什么 | `action` 里必须原样出现 |
| :--- | :--- | :--- |
| 表格 | Markdown 表格 **且** SQL | `as a Markdown table` 且 `show the SQL` |
| 流程图 | mermaid 流程图 | `as a flowchart` |
| 图表 | chart 图表 | `as a bar chart` 或 `as a line chart` |
| 自由 | 散文 (含第 1 条 Introduction) | 以上短语**一个都不能出现** |

这些短语和第 2 步那份 `Rendering Triggers` 表是同一份契约的两半. 措辞对不上, 触发就
不稳定 -- 尤其在小模型上, 它跟的是措辞不是意图.

**两半缺一不可.** 每条都要写 `render` 字段, 它是**按钮对读者的承诺** -- 前端据它在
按钮上画一个表格 / 流程 / 柱状的小图标 (`components/chat/RenderBadge.tsx`), 读者不
点开就知道会画出什么, `render = "free"` 故意什么都不画. 而真正让块出现的是 `action`
里那句短语.

只查短语, 图标会撒谎; 只查 `render`, 一个标着图表的问题会回一段散文.
`mise run check` 的 render quota **两个方向都验**, 所以两边写反了当场就报.

**选题比措辞更要紧**, 不是随便挑三条加上短语就行:

- **流程图**挑本来就是流程或状态迁移的问题: 生命周期, 漏斗, 状态流转. 给一个排名
  问题硬套流程图, 出来的是装饰. 让节点标签带上查出来的数字, 那才是它比表格强的地方.
- **图表**挑形状就是答案的问题: 排名, 趋势, 两个量的差距. `line` 留给有序刻度 (时间,
  账龄), 其余用 `bar`. 差距类问题用双 series (一条是定价假设的, 一条是实际发生的).
- **表格 + SQL** 挑读者会想验算的问题: 评分卡, 分档明细, 敞口清单.

**点名要哪几列.** 说清楚要 grade, loan count, implied rate, actual rate 这四列, 比说
"给我一张表" 更能让模型真的吐出表格, 顺带还能让回答快下来.

**问题问小一点.** 一条要连着调三次以上工具才能凑齐答案的问题, 不要靠调措辞救, 直接
拆小. 这是给人现场点开看的按钮, 转很久的圈就等于坏了, 哪怕最后答案是对的.

**第 4 步. 写 site.ts 的业务部分.**
输入: 提示词 (定能力) + 数据库 (定数字) + business_context (定叙事口吻).

- `home.capabilities` 四条 = 提示词里最重要的四条主线, tooltip 是它们的白话解释
- `chat.insights` 四条 = 同样四条主线, 换成更短的措辞
- `businessContext` 六节 = 见下面的 spec
- **`database.blurb` 里的表数和行数, 此刻现场从数据库数出来.** 不要抄旧值, 不要
  估. 借贷那版曾经写着 "~52,500 records" 而真实是 111,153, 差一倍多, 而它恰好摆在
  读者判断"这 demo 有多真"的位置

```bash
.venv/bin/python -c "
import sqlite3; db=sqlite3.connect('tmp/data.sqlite')
ts=[r[0] for r in db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")]
print(len(ts),'tables', sum(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ts),'rows')"
```

**第 5 步. 改脚本和测试里的硬编码.**
输入: 提示词 + 数据库. 见下面 D 组清单.

**第 6 步. 重新生成 schema 参考文件.**
`.venv/bin/python scripts/test_04_print_database_schema.py`

#### 为什么不加 lint

我评估过给这些一致性加检查 (前端词汇正向扫描、kickstart 与提示词的覆盖校验), 结论
是**不值得**: 判据是自然语言语义, 只能做成模糊匹配, 必然产出一堆需要人工判断的
warn, 最后没人看. **顺序是零成本的, 检查是有成本且不可靠的.**

保留的检查只有机械可判的那几条: 表顺序对撞 sqlite, 提示词 FROM/JOIN 的表名, 内容
文件存在性, 以及 2.3 里新加的那两个脚本 (渲染配额的短语计数, 数据的空表 / 孤儿外键 /
日期越界). 这些判据都是字符串匹配或整数比较, 没有歧义, 所以值得自动化.

分界线就在这里: **"这 12 条里有没有恰好 3 条写了 `as a flowchart`" 是机械问题,
"这 12 条问得好不好" 不是.** 前者写成脚本, 后者靠 2.2 的推导顺序和用户验收.

---

下面这张清单**不是执行顺序, 是完备性核对表**. 按上面六步做完之后, 逐行过一遍确认
没有漏项.

**A. 业务大脑.**

| 文件 | 来源 | 说明 |
| :--- | :--- | :--- |
| `data/system-prompt.md` | 第 2 步 | 整份重写, 含 Analysis Index |

**B. 配置.** 后端一行, 前端一个 TOML.

| 文件 | 要改的 key | 来源 |
| :--- | :--- | :--- |
| `.env.defaults` | `SCHEMA_NAME` (PostgreSQL schema 名, 也是配额分区 key) | 数据集名转成合法标识符: 小写字母/数字/下划线, 首字符非数字, <= 63 |
| `data/site.toml` | `[brand]` (displayName, logoPrefix, logoAccent, footerName) | **用户提供品牌名** |
| | `[seo]` (title, description, keywords) | summary |
| | `[[capabilities]]` × 4 (icon, title, subtitle, tooltip) | 提示词的四条主线, 见下 |
| | `[home]` (tagline, description, blurb, techStack, headline, cta) | summary + business_context |
| | `[home.businessContext]` (triggerLabel, title, subtitle) | 弹窗的标题, 正文在 `business-context.md` |
| | `[chat]` (agent, welcomeSubtitle, tryExamples, suggestionsHint, inputPlaceholder) | 用户提供 agent 名 + sql_queries 的主题分类 |
| | `[chat.messages]` (welcomeMessage, rateLimited, waitForResponse) | 与数据集无关, 照抄 |
| | `[[chat.suggestedActions]]` × 12 | 第 3 步, 见渲染配额那节 |

**`[[capabilities]]` 只有一份, 首页和 agent 页渲染的是同一份.** 别去找
`chat.insights` —— 那是旧形态, 它和 `home.capabilities` 曾经各写各的, 结果第二条
在首页叫 "Portfolio Concentration" 在 agent 页叫 "Portfolio Health", 图标不同,
tooltip 只有一边有. 现在两边都走 `components/CapabilityCard.tsx`.
| | `businessContext.*` (triggerLabel, title, subtitle, sections × 6) | **business_context 全文** + sql_queries 的主题分类. 见下面的 spec |

`capabilities` 和 `insights` 里的 `icon` 必须是 `lib/icons.ts` 里已注册的名字, 否则**编译报错**. 需要新图标就在那个文件里 import 并加进 `ICONS`. 从 lucide-react 挑.

#### 前端文案的写法规范 (所有 `data/site.toml` 字符串都适用)

这一节管的是 `site.ts` 里每一个会显示给用户的字符串: seo, home, chat, tooltip,
businessContext 全部在内. 也管 `data/business-context.md`. 不管代码注释和
提示词.

**第一条: 不要用破折号.**

不要用 `—`, 也不要用 `--` 当停顿. 这是最容易暴露"AI 写的"的一个特征, 因为模型
极其偏爱用它来塞入补充说明, 一段话里出现三四次是常态, 而人类文案很少这样写.

破折号出现的地方, 通常说明这句话本来就该断开. 三种改法, 按优先级:

| 原样 | 改成 |
| :--- | :--- |
| `... is underpriced — and because ...` | 断成两句. `... is underpriced. And because ...` |
| `Each is structural — a consequence of X — and ...` | 换成逗号从句. `Each one is structural, a consequence of X, and ...` |
| `term: "Interest — the main revenue line"` | 把补充说明挪进 detail. `term: "Interest"`, detail 以 `The main revenue line, ...` 开头 |

标题里如果非要分隔, 用冒号: `"SMB Lending Lens: AI-Powered Fintech Analytics Agent"`.

**第二条: 叙述性语言, 简单格式.**

用完整的句子把事情讲清楚, 不要写成关键词罗列. 允许的格式只有三样: **加粗**, 标题,
bullet. 不要用表格, 不要嵌套列表, 不要 emoji, 不要行内代码块 (那是给开发者看的,
这里的读者不是).

**第三条: business-context.md 允许一张 mermaid 流程图.**

写成普通的 ` ```mermaid ` 围栏块, 整份说明里**最多用一次**, 十个节点以内. 它是留给"读者必须一次性装进脑子里的顺序或分支"的, 比如借贷那版画的是
"申请 -> 批/拒 -> 放款 -> 还款 -> 结清/违约" 这条主线.

判断标准很简单: **如果这张图只是把上一句话又说了一遍, 那就删掉图, 留那句话.**
第二张图一定是装饰.

渲染走 `components/chat/blocks/MermaidBlock.tsx` (已做懒加载和 `securityLevel:
"strict"`), 组件与数据集无关, 不用改. 弹窗和 chat 页共用它, 所以这里能画的图和
agent 能画的图是同一套能力.

**改完自查一遍:**

```bash
grep -n "—" data/site.toml data/business-context.md | grep -v "^\s*#"
```

有输出就是还有破折号没清干净 (那两个 `grep -v` 是排除代码注释).

#### capabilities[].tooltip: 把概念名翻译成人话

首页那四张能力卡上写的是**概念名** —— "Sponsor Exposure Audit" 对内行精确, 对其他
所有人等于没写. 每张卡 hover / 聚焦 / 点按时弹出的这段 tooltip 就是用来补这一刀的,
组件是 `app/(marketing)/_components/ConceptTooltip.tsx` (与数据集无关, 不用改).

写法:

- **两到三句白话.** 先定义这个词, 再说这个数为什么会动.
- **解释里不能再有黑话.** 这是最容易犯的错 —— 用一个内行词去解释另一个内行词.
- 来源是 business_context 的术语表和关键指标公式, 但要重写成口语, 不要直接抄公式.

四条要和 `capabilities` 一一对应, 也就是和四条业务主线一一对应.

#### `data/business-context.md` 的 spec

这是整份内容里最花笔墨的一项, 也最容易做砸, 所以单独定一份 spec. 它是首页那个按钮
打开的弹窗, 2 到 3 屏可滚动内容, 由 `components/BusinessContextModal.tsx` 渲染
(组件与数据集无关, 换数据集时不用动).

**它是一份普通 Markdown**, 走的是 chat 页那个同一个 Markdown 渲染器, 所以里面的
` ```mermaid ` 围栏会真的画成图, 而且是懒加载 + `securityLevel: "strict"` 那一套.
六节就是六个 `##` 标题, 术语表用加粗开头的 bullet.

弹窗的标题和副标题不在这个文件里, 在 `site.toml` 的 `[home.businessContext]` --
那三行是**按钮和窗框的标签**, 不是正文.

**它讲的是这个 agentic App, 不是这个数据集.**

这条决定了全篇的取景. 对外展示时露出去的是"一个数据集加一个能查它的 agent", 但读
者真正需要知道的是**这个 App 是干什么的** —— 它替谁解决什么问题, 凭什么解决, 以及
它今天做到哪一步. 所以标题走 "The business behind the agentic App" 这个调子, 不要
写成 "The business behind the data". 一字之差, 前者在介绍产品, 后者在介绍附件.

**两条硬要求:**

- **写给完全不懂这行的陌生人看, 只靠常识就能读完.** 内行缩写和黑话要用就当场解释.
- **讲行业, 不讲雇主; 讲问题, 不讲项目.** 不出现实习, 公司名, 个人经历, 课程, 作业
  这类痕迹 —— 和仓库"不放作者身份"是同一条规矩 (见 CLAUDE.md).

**六节结构, 按顺序填. 前三节讲世界, 后三节讲这个 App 在这个世界里干什么:**

| # | 节 | 必须回答 | 来源 |
| :--- | :--- | :--- | :--- |
| 1 | 这门生意怎么赚钱 | 收入几条线各占多少, 最大的成本是什么 | business_context 商业模式段 |
| 2 | 钱从哪里悄悄漏掉 | 每条都要回答"**为什么它不会自己暴露**" | business_context 的四个 Q |
| 3 | 这些事在数据里长什么样 | **先说清楚为什么这些线索必须放在一起看**, 再说记录了什么, 覆盖多长时间, 并点明 REFERENCE_DATE 是固定的 | er_document + summary |
| 4 | agent 拿这些数据做什么 | 读 schema, 写 SQL, 解读结果; 该出图时出 diagram 和 chart | 通用能力, 不来自数据集 |
| 5 | 你可以问什么, 以及怎么读答案 | 按四条主线分组的问题清单, 末尾补这个领域特有的解读陷阱 (比如平均值会稀释掉结论) | sql_queries 的主题分类 + er_document 的 Embedded Business Traps |
| 6 | 只读之外 (本 App 不含) | 同一套架构可以做真写操作, 前提是权限护栏加可审计轨迹 | 通用, 见下 |

**第 2 节是全篇的重心.** 每一条都要回答"为什么这个亏损在财报上看不出来" —— 那才是
这个 App 存在的理由. 只罗列"我们能查 X"没有说服力, 因为读者不知道为什么需要查.

**第 6 节的分寸.** 这一节讲产品边界和方向, 必须同时说清三件事, 少一件就变成吹牛:

1. 这个 App 是**故意**只读的 —— 它是给外部看的演示;
2. 同一套 agent 架构可以挂上写操作的 tool, 真正改后端状态 (这不是设想, 仓库本来就
   支持: 写操作是 dataset-specific 的 `@tool`, 见 `one_04_agent.py`);
3. 真要上写操作, 前提是**权限护栏**和**可审计轨迹** —— 谁在什么时候改了什么, 每一
   笔都要留痕, 而不是让模型直接对生产库动手.

第 3 点不能省. 少了它, 这一节读起来就是"我们还能让 AI 乱改数据", 反而减分.

**C. 内容.** 无法配置化, 只能手写.

| 文件 | 数量 | 来源 |
| :--- | :--- | :--- |
| `data/business-context.md` | 六节 | business_context 全文, 见下面的 spec |
| `data/data.sqlite.example` | 1 个文件 | 直接复制 `tmp/dataset/<name>.sqlite` 覆盖 |

覆盖数据库之后必须跑 `mise run setup-db`, 它把 `data/data.sqlite.example` 播种到
`tmp/data.sqlite`, 后者才是本地实际读的库.

kickstart 12 条不在这张表里, 它们是 `site.toml` 的 `[[chat.suggestedActions]]`, 见
B 组.

**D. 脚本和测试里的硬编码.** 这一组最容易漏.

| 文件 | 里面是什么 |
| :--- | :--- |
| `scripts/test_21_agent.py` | 10 个 `request_NN` 变量, 全是上一个领域的业务问题, 全部重写 |
| `scripts/test_02_run_sql_locally.sql` | 一条示例 SQL, 引用了旧表名 |
| `tests_python/one/test_one_one_04_agent.py` | 断言里写死了 `FROM loan` 和 `DROP TABLE loan`, 换成新库里真实存在的表 |
| (schema 参考) | **没有需要维护的文件.** 要看 schema 就跑 `.venv/bin/python scripts/test_04_print_database_schema.py`, 它直接读库, 永远是真的 |

**E. 用户必须提供的.** 输入文档里不会有这些.

这几样任何业务文档里都不会有, 开工前先问用户. 不要自己编了就往下走:

- **品牌名 / 产品名**: 决定 `displayName`, `logo.prefix` + `logo.accent` (会被拆成两种颜色), `footerName`
- **`database.schemaName`**: 远程 Postgres 的 schema 名, 多项目共用一个库靠它隔离 (不是表
  前缀 —— 表名两边必须一样). 也是 `quota.py` 的配额分区 key. 必须是合法标识符: 小写字母/
  数字/下划线, 首字符不能是数字, <= 63 字符; 写错了 `ProjectConfig` 加载时就报
- **agent 的名字**: chat 页面里它怎么称呼自己
- **配色方向**: 可以从行业推断 (金融偏藏青, 医疗偏青绿), 但要让用户确认

**F. 明确不用改的.**

不要浪费时间在这些上面:

- `agent_app/` 下除提示词外的所有代码. 它是通用的, 包名 `agent_app` 就是为了换数据集时不用改

**这条能成立, 靠的是一条纪律: 代码注释和 docstring 里的例子必须与数据集无关.**

在通用代码里写 `# e.g. the "loan" table` 这种例子, 等于把当前数据集焊进了通用代码. 换数据集之后它不报错、不失败, 只是变成谎话躺在那里 —— 和 skill 开头讲的那个
"医院 docstring 躺在借贷仓库里几个月"是同一个形状, 只是规模小.

正确写法是用永远虚构的占位领域:

```python
#   local SQLite          remote PostgreSQL
#   widget          ->    acme_widget
#   part            ->    acme_part
```

`acme` / `widget` / `part` 这类词不属于任何真实数据集, 所以永远不会过期, 也就永远
不需要出现在换数据集的清单里. 已经明显虚构的例子 (比如 `db_schema/encoder.py` 里那
段 `Schema ecommerce(...)` 的格式示例) 不用动, 它本来就不声称在描述本数据集.

**新增通用代码时同样适用.** 只要你在 `agent_app/` 或 `scripts/` 里写下一个表名做
例子, 先问一句: 换数据集之后这句话还对吗?
- `components/chat/blocks/` 渲染层. Mermaid 和 chart 与数据集无关
- `README.md`, `TICKET.md`, `README-cn.md`, `docs/`. 那是教学材料, 换数据集不等于改课程. **要改就单独问用户**

### 2.3 验证

执行顺序在 2.2, 不要在这里再排一遍. 这一节只讲怎么验.

**每做完一步就验一次, 不要攒到最后.** 攒到最后的问题是, 一次报出十个错时你分不清
哪个是根因、哪个是连锁反应.

```bash
mise run check     # 表顺序 / 提示词表名 / 内容文件 / 渲染配额
mise run test      # Python + Node
npx next build     # site.toml 的缺 key 和图标名, 只有这里查得到
```

**三条都要跑, 它们查的东西不重叠.** `mise run check` 读 TOML 的形状和配额;
`next build` 是唯一会把 `site.toml` 的 `icon` 拿去对 `lib/icons.ts` 的地方, 也是唯一
会真的把 `business-context.md` 渲染一遍的地方.

**第 2 步做完额外做一件事: 把提示词里每一段 SQL 对着真库跑一遍.**

**必须走 `one.engine`, 也就是 PostgreSQL.** 拿本地 sqlite 验过的 SQL 在这里一条都不
算数 -- 那正是这套流程以前踩的坑.

```bash
.venv/bin/python - <<'EOF'
import re, pathlib, sqlalchemy as sa
from agent_app.api import one
blocks = re.findall(r"```sql\n(.*?)```",
                    pathlib.Path("data/system-prompt.md").read_text(), re.S)
ok = fail = 0
for i, b in enumerate(blocks, 1):
    if not b.strip().upper().startswith(("SELECT", "WITH")):
        continue
    try:
        with one.engine.connect() as c:
            rows = c.execute(sa.text(b)).fetchall()
            c.rollback()
        ok += 1
        print(f"[{i}] OK   {len(rows)} rows | {rows[0] if rows else ''}"[:110])
    except Exception as e:
        fail += 1
        print(f"[{i}] FAIL {str(e).splitlines()[0][:130]}")
print(f"\n{ok} ok, {fail} fail")
EOF
```

跑不通的 SQL 例子比没有例子更糟: 模型会照抄, 然后在用户面前失败. 顺便这一步还会
暴露"公式写错了但语法没错"的情况 —— 结果数字明显不对就能看出来.

**第 3 步做完核对渲染配额.** 不用自己写脚本, `mise run check` 里的 `render quota`
那一项就是干这个的, 两个方向都验:

```bash
mise run check
```

它会报三类问题: 条数不是 12 或四类不是各 3 条; 某条的 `render` 和它 `action` 里的
措辞对不上; 某条同时命中两种格式的短语. 报出来的信息带序号和标题, 直接能定位.

**图标名和缺 key 它查不到**, 那两样在 `next build` 时由 `lib/site/load.ts` 抛:

```bash
npx next build
```

这两条要一起跑. 只跑 `mise run check` 的话, 一个拼错的图标名会安静地渲染成兜底图标,
卡片看着好好的, 就是配错了图.

**数据本身要体检一遍. 这一条 ba 那个仓库可以跳过, 我们不行.**

体检的对象是 `tmp/data.sqlite` 这个**种子**, 不是线上的 PostgreSQL: 同步是逐行复制,
种子干净则线上干净, 而 SQLite 的 `PRAGMA foreign_key_list` 拿孤儿行比写 PostgreSQL 的
等价查询省事得多. 顺序上先体检再同步, 别把脏数据发上去再回头查.

那边是纯 demo, 图表里的数字"大差不差就行". 这个 App 是要拿去给人认真看的, 所以数据
不能出现**一眼假**的结论: 违约率 0%, 某张表全是空的, 日期落在 1970 年, 金额是负数.
标准也就到这里为止 -- 不需要逐行对账, 不需要和源文档的统计量严格吻合, **能跑, 且没有
一眼假的结论**, 就算过.

```bash
.venv/bin/python - <<'EOF'
import sqlite3, datetime

db = sqlite3.connect("tmp/data.sqlite")
db.row_factory = sqlite3.Row
tables = [r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

print(f"{len(tables)} tables\n")
issues = []
for t in tables:
    n = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    if n == 0:
        issues.append(f"{t}: 空表")
    print(f"  {t:<28} {n:>9,} rows")

    # 外键指向一个不存在的父行
    for fk in db.execute(f"PRAGMA foreign_key_list({t})").fetchall():
        col, parent, pcol = fk["from"], fk["table"], fk["to"] or "id"
        orphans = db.execute(
            f"SELECT COUNT(*) FROM {t} c LEFT JOIN {parent} p ON c.{col} = p.{pcol} "
            f"WHERE c.{col} IS NOT NULL AND p.{pcol} IS NULL").fetchone()[0]
        if orphans:
            issues.append(f"{t}.{col} -> {parent}.{pcol}: {orphans} 条孤儿行")

    # 落在常识之外的日期
    for col in db.execute(f"PRAGMA table_info({t})").fetchall():
        if "date" not in col["name"].lower() and "DATE" not in col["type"].upper():
            continue
        lo, hi = db.execute(
            f"SELECT MIN({col['name']}), MAX({col['name']}) FROM {t}").fetchone()
        if lo is None:
            continue
        for label, v in (("min", lo), ("max", hi)):
            try:
                y = datetime.date.fromisoformat(str(v)[:10]).year
            except ValueError:
                continue
            if not (1990 <= y <= 2035):
                issues.append(f"{t}.{col['name']} {label} = {str(v)[:10]}")

print()
print("❌ " + "\n❌ ".join(issues) if issues
      else "✅ 无空表, 无孤儿外键, 日期都在常识范围内")
EOF
```

脚本查的是机械可判的那几样. 剩下**要靠眼睛看一遍**的, 是提示词里那几条核心指标算出来
的数字: 违约率, 定价缺口, 逾期率. 拿第 2 步跑 SQL 那一步的输出直接看:

- 比率类落在这个行业说得过去的区间里 (不是 0%, 不是 80%)
- 分档之间的排序符合常识 (风险高的档位违约率更高)
- 金额没有负数, 没有比总资产还大的单笔

有一条明显离谱, 说明数据集本身有问题, 回去找用户确认, 不要在提示词里绕过它.

**同步到线上之后, 量一次真实体积.** 第 1 步只是估.

```bash
mise run sync-db
mise run verify-db
.venv/bin/python - <<'EOF'
import sqlalchemy as sa
from agent_app.api import one

sql = sa.text('''
    SELECT pg_size_pretty(COALESCE(SUM(pg_total_relation_size(c.oid)), 0)) AS ours,
           COUNT(*) AS n_tables,
           pg_size_pretty(pg_database_size(current_database())) AS whole_db
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r' AND n.nspname = :schema
''')
with one.remote_postgres_engine.connect() as conn:
    r = conn.execute(sql, {"schema": one.config.schema_name}).one()
print(f"我们这 {r.n_tables} 张表占 {r.ours}; 整库 {r.whole_db} / 500 MB")
EOF
```

那 500MB 是整库配额, **和别的项目共用**, 所以看的是两个数: 我们这个 schema 别失控,
整库别顶到线. 逼近了就回去减行, 通常是把最大那张流水表按时间截一段, 而不是删表 -- 删表会让提
示词里的分析失效.

**起本地服务看效果:**

```bash
mise run dev
```

Next.js + FastAPI 一起起, 会先杀掉旧进程, 不用手动清理. 打开 `/` 和 `/chat`.

**最后跑一次旧领域词汇扫描.** 词表是一次性参数, 不提交进仓库:

```bash
mise run check -- --retired "loan,lending,borrower,default_event,risk_grade"
```

把上一个数据集**最有辨识度的名词**填进去. 有残留它会精确报出文件和行号.

**一个环境坑:** `tmp/data.sqlite` 不进 git, 切分支不会跟着变. 如果测试报了一堆表
不存在, 先 `mise run setup-db` 再说, 别急着改代码.

### 2.4 停下来让用户验收, 然后做视觉

阶段一到此为止. **明确告诉用户: 内容已经换完, 但页面还是上一个行业的视觉, 请先跑一下看功能对不对.** 让他确认这几件事:

- agent 回答得像不像这个领域的专家
- **12 条 kickstart 逐条点一遍, 该出的块真的出来了**: 3 条出表格加 SQL 高亮, 3 条出
  流程图, 3 条出图表. 这一条必须手点, 不能靠读配置 -- 配额脚本只能证明问法写对了,
  证明不了模型照做了. 出不来最常见的原因是提示词里 `Rendering Triggers` 那节被精简过
- 答案里的数字没有一眼假的 (违约率不是 0%, 排序符合常识). 不必逐行对账, 但明显离谱
  的必须回去查
- 首页文案和 chat 页文案有没有残留旧领域的说法
- 所有前端文案里没有破折号, 且 businessContext 里最多一张 mermaid 图
- 点开首页那个 business context 弹窗, 一个完全不懂这行的人读完能不能明白这个 App 解决什么问题
- 四张能力卡 hover / Tab 聚焦 / 手机点按, tooltip 都能弹出, 窄屏下不跑出屏幕

用户满意之后再进入视觉改造.

**这一步开始之前, 先做两件事, 顺序不能反:**

1. **用一句话告诉用户你要进入阶段二了, 并且明说你正在加载视觉设计 skill.** 比如:
   "阶段一验收通过, 我现在进入视觉改造, 先加载 `frontend-design` skill 拿它的设计
   规范." 不要闷头就开始改颜色 -- 用户看到的是一堆 diff, 不知道你依据的是什么.
2. **真的用 Skill 工具加载 `frontend-design:frontend-design`** (注意是带 plugin 前缀
   的全名), 然后按它给的规范做. 不要凭记忆写"我觉得好看的配色".

同理, 改图表配色那一步要加载 `dataviz` skill, 跑它自带的调色板 validator, 别靠眼睛
判断.

视觉相关的代码就这些, 别只改首页就收工:

| 层面 | 文件 |
| :--- | :--- |
| 配色系统 | `tailwind.config.ts` (现在是 Navy + Gold 的 "Fintech Color System"), `app/globals.css` 的 `:root` 变量 |
| 字体 | `app/layout.tsx` 里的 `next/font/google` (现在是 Inter + Figtree + Noto Sans) |
| favicon | `app/icon.png` |
| 导航栏 | `app/_components/layouts/Navigation.tsx` (logo 的两段式着色在这里) |
| 首页 | `app/(marketing)/_components/Hero.tsx`, `app/(marketing)/HomePageContent.tsx` |
| **business context 弹窗** | `components/BusinessContextModal.tsx` (遮罩, 面板, 滚动条, Markdown 排版), `components/ConceptTooltip.tsx` (气泡与小尖角) |
| **chat 空状态** | `components/chat/overview.tsx` (标题 + 4 张能力卡, 卡片本身是 `components/CapabilityCard.tsx`, 首页共用) |
| **chat 输入区** | `components/chat/multimodal-input.tsx` (12 张 kickstart 卡片的排布), `components/chat/RenderBadge.tsx` (按钮上那个表格/流程/柱状小图标) |
| **chat 对话气泡** | `components/chat/message.tsx` (AI 头像那个方块, 用户头像, 气泡配色) |
| **chat 顶部横幅** | `components/chat/chat.tsx` (那条介绍 agent 的 banner) |
| 图表配色 | `app/globals.css` 的 `.viz-root` token |

加粗的四行是最常被忘掉的. 首页改得很漂亮而 chat 页还是旧配色, 是这一步最典型的失败.

图标有两个来源: 从 lucide-react 挑现成的 (记得同步注册进 `lib/icons.ts`), 或者自己画 SVG 放进 `components/chat/icons/`. 后者适合行业特有的形状.

改图表配色时注意 `app/globals.css` 里 `.viz-root` 的深色 token 只认 `.dark` class, 不认系统偏好, 因为全站 Tailwind 是 `darkMode: ["class"]` 策略, 别去接 `prefers-color-scheme`. 换配色之后跑一遍 `dataviz` skill 的调色板 validator (上面已经说过要加载它).

视觉改完再跑一次 `mise run check` 和 `mise run test`, 因为改图标名或删组件都可能把编译打断.
