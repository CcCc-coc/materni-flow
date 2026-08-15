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

**第 1 步. 数据库落地.**
复制 sqlite 覆盖 `data.sqlite.example`, 跑 `mise run setup-db`, 按 er_document 的外
键依赖顺序填 `config/dataset.toml` 的 `tableInsertOrder`, 立刻 `mise run check`.

*为什么必须第一:* 后面每一步的验证都要拿它当基准. 顺序错了当场就报.

**第 2 步. 写提示词. 这是唯一允许通读数据集全部文档的一步.**
输入: business_context + er_document + sql_queries 全文.

- **必须覆盖 sql_queries 里的每一条 query.** 做法是先写一节 `## Analysis Index`,
  20 条每条一行 (这条分析回答什么问题), 然后挑其中**外行会算错的**那些, 在
  `## Derived Business Concepts` 里给出精确公式和 SQL. 覆盖靠索引, 篇幅靠取舍 ——
  两者不要混为一谈.
- 保留 `## Diagrams and Charts: The Fence Rule` / `## Diagrams` / `## Charts` 三节
  的结构 (那是前端能力, 与数据集无关), 只换里面的例子.
- 写完**把提示词里每一段 SQL 对着真库跑一遍**. 跑不通的例子比没有例子更糟, 模型会
  照抄.

*一个坑:* `mise run check` 会把 `FROM x` / `JOIN x` 当表名校验, 它分不清散文和 SQL.
`drawn from a zero baseline` 里的 `from a` 会被判成表 `a`. 换个说法即可.

**第 3 步. 写 kickstart 12 条.**
输入: **只看第 2 步产出的提示词**, 不要回头翻 sql_queries.

逐条对着 `## Analysis Index` 挑 11 条改写成用户口吻的问题 (第 1 条固定是
"Introduction / What can you do?"). 挑不出来说明提示词覆盖不够, 回第 2 步补, 不要
在这里现编.

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

保留的检查只有机械可判的那几条: 表顺序对撞 sqlite、提示词 FROM/JOIN 的表名、内容
文件存在性. 这些没有歧义, 所以值得自动化.

---

下面这张清单**不是执行顺序, 是完备性核对表**. 按上面六步做完之后, 逐行过一遍确认
没有漏项.

**A. 业务大脑.**

| 文件 | 来源 | 说明 |
| :--- | :--- | :--- |
| `agent_app/prompts/bi-agent-system-prompt.md` | 第 2 步 | 整份重写, 含 Analysis Index |

**B. 配置.** 两个文件, 按读者分, 前端读 TS 后端读 TOML.

| 文件 | 要改的 key | 来源 |
| :--- | :--- | :--- |
| `config/dataset.toml` | `project.name` (远程表前缀, 要短) | 用户提供或从品牌名缩写 |
| | `database.displayName` | 数据集名 |
| | `database.tableInsertOrder` | er_document 的外键依赖顺序, 父表在前 |
| `config/site.ts` | `project.*` (displayName, tagline, logo.prefix/accent, footerName) | **用户提供品牌名** |
| | `agent.*` (name, domainLabel) | 用户提供或据业务拟 |
| | `seo.*` (title, description, keywords) | summary |
| | `database.blurb` | summary 里的表数和行数 |
| | `home.*` (headline, description, capabilities × 4, techStack, cta) | summary + business_context |
| | `chat.*` (welcomeSubtitle, insights × 4, tryExamples, suggestionsHint, inputPlaceholder) | sql_queries 的主题分类 |
| | `home.capabilities[].tooltip` × 4 | business_context 的术语表, 见下 |
| | `businessContext.*` (triggerLabel, title, subtitle, sections × 6) | **business_context 全文** + sql_queries 的主题分类. 见下面的 spec |

`capabilities` 和 `insights` 里的 `icon` 必须是 `lib/icons.ts` 里已注册的名字, 否则**编译报错**. 需要新图标就在那个文件里 import 并加进 `ICONS`. 从 lucide-react 挑.

#### 前端文案的写法规范 (所有 `config/site.ts` 字符串都适用)

这一节管的是 `site.ts` 里每一个会显示给用户的字符串: seo, home, chat, tooltip,
businessContext 全部在内. 不管 `data/suggested-actions.json`, 也不管代码注释和
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

**第三条: businessContext 允许一张 mermaid 流程图.**

`ContextSection` 有一个可选的 `mermaid` 字段, 整份说明里**最多用一次**, 十个节点
以内. 它是留给"读者必须一次性装进脑子里的顺序或分支"的, 比如借贷那版画的是
"申请 -> 批/拒 -> 放款 -> 还款 -> 结清/违约" 这条主线.

判断标准很简单: **如果这张图只是把上一句话又说了一遍, 那就删掉图, 留那句话.**
第二张图一定是装饰.

渲染走 `components/chat/blocks/MermaidBlock.tsx` (已做懒加载和 `securityLevel:
"strict"`), 组件与数据集无关, 不用改.

**改完自查一遍:**

```bash
grep -n "—" config/site.ts | grep -vE ":\s*\*|:\s*//"
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

#### businessContext 的 spec

这是整个 `site.ts` 里最花笔墨的一项, 也最容易做砸, 所以单独定一份 spec. 它是首页
那个按钮打开的弹窗, 2 到 3 屏可滚动内容, 由
`app/(marketing)/_components/BusinessContextModal.tsx` 渲染 (组件与数据集无关, 换
数据集时不用动).

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
| `data/suggested-actions.json` | 12 条, 每条 `title` + `label` + `action` | sql_queries 的 20 条挑 11 条改写, 第 1 条固定是 "Introduction / What can you do?" |
| `data.sqlite.example` | 1 个文件 | 直接复制 `tmp/dataset/<name>.sqlite` 覆盖 |

覆盖数据库之后必须跑 `mise run setup-db`, 它把 `data.sqlite.example` 播种到 `tmp/data.sqlite`, 后者才是本地实际读的库.

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
- **`project.name` 短标识**: 远程 Postgres 的表前缀, 多项目共用一个库靠它隔离, 越短越好
- **agent 的名字**: chat 页面里它怎么称呼自己
- **配色方向**: 可以从行业推断 (金融偏藏青, 医疗偏青绿), 但要让用户确认

**F. 明确不用改的.**

不要浪费时间在这些上面:

- `agent_app/` 下除提示词外的所有代码. 它是通用的, 包名 `agent_app` 就是为了换数据集时不用改

**这条能成立, 靠的是一条纪律: 代码注释和 docstring 里的例子必须与数据集无关.**

写 `prefix_table_name("loan") # "smbll_loan"` 这种例子, 等于把当前数据集焊进了通用
代码. 换数据集之后它不报错、不失败, 只是变成谎话躺在那里 —— 和 skill 开头讲的那个
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
mise run check     # 表顺序 / 提示词表名 / 内容文件
mise run test      # Python + Node
npx tsc --noEmit   # site.ts 的图标名、字段结构
```

**第 2 步做完额外做一件事: 把提示词里每一段 SQL 对着真库跑一遍.**

```bash
.venv/bin/python - <<'EOF'
import re, sqlite3, pathlib
db = sqlite3.connect("tmp/data.sqlite")
for i, b in enumerate(re.findall(r"```sql\n(.*?)```",
        pathlib.Path("agent_app/prompts/bi-agent-system-prompt.md").read_text(), re.S), 1):
    if not b.strip().upper().startswith(("SELECT", "WITH")): continue
    try:
        rows = db.execute(b).fetchall()
        print(f"[{i}] OK  {len(rows)} rows | {rows[0] if rows else ''}")
    except Exception as e:
        print(f"[{i}] FAIL {e}")
EOF
```

跑不通的 SQL 例子比没有例子更糟: 模型会照抄, 然后在用户面前失败. 顺便这一步还会
暴露"公式写错了但语法没错"的情况 —— 结果数字明显不对就能看出来.

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
- 12 个 kickstart 问题点下去是否都能出结果
- 首页文案和 chat 页文案有没有残留旧领域的说法
- 所有前端文案里没有破折号, 且 businessContext 里最多一张 mermaid 图
- 点开首页那个 business context 弹窗, 一个完全不懂这行的人读完能不能明白这个 App 解决什么问题
- 四张能力卡 hover / Tab 聚焦 / 手机点按, tooltip 都能弹出, 窄屏下不跑出屏幕

用户满意之后再进入视觉改造, 这一步**加载 `frontend-design:frontend-design` skill** 来做 (注意是带 plugin 前缀的全名).

视觉相关的代码就这些, 别只改首页就收工:

| 层面 | 文件 |
| :--- | :--- |
| 配色系统 | `tailwind.config.ts` (现在是 Navy + Gold 的 "Fintech Color System"), `app/globals.css` 的 `:root` 变量 |
| 字体 | `app/layout.tsx` 里的 `next/font/google` (现在是 Inter + Figtree + Noto Sans) |
| favicon | `app/icon.png` |
| 导航栏 | `app/_components/layouts/Navigation.tsx` (logo 的两段式着色在这里) |
| 首页 | `app/(marketing)/_components/Hero.tsx`, `app/(marketing)/HomePageContent.tsx` |
| **business context 弹窗** | `app/(marketing)/_components/BusinessContextModal.tsx` (遮罩, 面板, 滚动条, 分节排版), `ConceptTooltip.tsx` (气泡与小尖角) |
| **chat 空状态** | `components/chat/overview.tsx` (标题, 4 张洞察卡) |
| **chat 输入区** | `components/chat/multimodal-input.tsx` (12 张 kickstart 卡片的排布) |
| **chat 对话气泡** | `components/chat/message.tsx` (AI 头像那个方块, 用户头像, 气泡配色) |
| **chat 顶部横幅** | `components/chat/chat.tsx` (那条介绍 agent 的 banner) |
| 图表配色 | `app/globals.css` 的 `.viz-root` token |

加粗的四行是最常被忘掉的. 首页改得很漂亮而 chat 页还是旧配色, 是这一步最典型的失败.

图标有两个来源: 从 lucide-react 挑现成的 (记得同步注册进 `lib/icons.ts`), 或者自己画 SVG 放进 `components/chat/icons/`. 后者适合行业特有的形状.

改图表配色时注意 `app/globals.css` 里 `.viz-root` 的深色 token 只认 `.dark` class, 不认系统偏好, 因为全站 Tailwind 是 `darkMode: ["class"]` 策略, 别去接 `prefers-color-scheme`. 换配色之后加载 `dataviz` skill, 跑它自带的调色板 validator, 别靠眼睛判断.

视觉改完再跑一次 `mise run check` 和 `mise run test`, 因为改图标名或删组件都可能把编译打断.
