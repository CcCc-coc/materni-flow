---
name: swap-dataset-cn
description: 把整个仓库从当前数据集换到 dataset/ 里的新数据集, 然后重新设计前端. 两个阶段, 中间有一道用户验收闸门: 阶段一造库, 同步 PostgreSQL, 重写 data/ 下的提示词/文案/业务说明; 阶段二做视觉. 用户敲 /swap-dataset-cn 时执行.
disable-model-invocation: true
allowed-tools: Bash(mise run *) Bash(.venv/bin/python *) Bash(.venv/bin/agent-app *) Bash(pnpm exec *) Bash(git status *) Bash(git diff *) Bash(ls *) Bash(head *) Bash(grep *) Read Edit Write Glob Skill AskUserQuestion
---

# 换数据集

这个仓库的本质是三样东西: **一个提示词, 一个数据库, 一个网站**. 换数据集就是把这三样同时
换掉, 而且必须换得一致.

网站说自己是贷款分析, 提示词教的是医院排班, 数据库里躺着电商订单 —— 这种状态是能跑起来的.
它不报错, 它只是全程撒谎. 所以工作方式不是"看到哪改哪", 而是**先建立完整映射, 再按固定
顺序执行, 最后靠工具验证**.

---

## 十二步, 分两个阶段

**阶段一 (第 0 到 9 步)** 换内容, 做完之后功能是对的, 但页面还穿着上一个行业的衣服;
**阶段二 (第 10 到 12 步)** 换视觉. **中间那道闸门 (第 9 步) 不能跳** —— 两个阶段混着做,
一旦效果不对, 分不清是内容错了还是样式错了.

```
0 开场白与模型自检            5 推导链: 提示词 -> kickstart -> 文案 -> 业务说明 -> 硬编码
1 预检: 仓库现在健康吗        6 完备性核对表
2 认输入: dataset/ 换了吗     7 验证: 三条命令 + SQL 真库跑一遍 + 数据体检
3 问用户: 文档里没有的        8 自己先跑一遍网站
4 建库并同步到 PostgreSQL     ───── 闸门: 用户验收 (第 9 步) ─────
                              10 定调性并问用户   11 改视觉   12 收尾与交付
```

五份配套文档, 用到再读:

| 读 | 什么时候 |
| :--- | :--- |
| [`ref/data-files-spec-cn.md`](ref/data-files-spec-cn.md) | 第 5 步. `data/` 三个文件各自长什么样 |
| [`ref/writing-style-cn.md`](ref/writing-style-cn.md) | 第 5 步. 文案的口吻和格式规矩 |
| [`ref/verification-cn.md`](ref/verification-cn.md) | 第 4 和第 7 步. 全部验证脚本 |
| [`ref/frontend-redesign-cn.md`](ref/frontend-redesign-cn.md) | 第 11 步. 视觉要动哪些文件 |
| [`ref/system-prompt-render-blocks.md`](ref/system-prompt-render-blocks.md) | 第 5 步. 逐字抄进提示词的那五节 |

---

## 第 0 步. 开场白与模型自检

**先说话, 再动手.** 用户敲下这个命令时, 他不知道接下来要花多久, 也不知道自己要在什么时候
插手. 开场白就是回答这两件事.

照这个意思说一段 (措辞自便, 别照抄成模板腔):

> 这次要做两件事:
>
> **第一步, 换数据集.** 我会把 `dataset/` 里的新数据造成数据库, 同步到 PostgreSQL, 然后照
> 着它重写 `data/` 下面的提示词, 全部界面文案和业务说明. 做完之后功能是对的, 但页面还是上
> 一个行业的配色.
>
> **第二步, 重新设计前端.** 配色, 字体, 构图, 图表色板. 这一步要等你确认第一步没问题之后
> 才开始.
>
> 中间会停下来让你自己跑一遍 `mise run dev` 点一点. 你说没问题, 我才往下走.

然后**报一次自己的模型**, 并说明这件事够不够格:

> 这个流程要写一份长提示词, 挑 12 个问题, 还要保证它们和提示词一致, 对模型的要求不低.
> 建议用 **Claude Sonnet / GPT Terra / Gemini Flash 同档或更高**的模型.
> 我现在是 `<你自己的模型名>`.

- 够格 -> 说一句"这一档没问题", 继续
- **不够格 -> 停下来.** 明确建议用户切换模型之后重新敲一次 `/swap-dataset-cn`, 并说清楚
  为什么: 小模型在这个流程里的典型失败是提示词覆盖不全, 12 条 kickstart 的触发短语写漏,
  以及文案里满是破折号. 这三样都不会报错, 全都要人回头返工

**不要因为"想帮上忙"就用一个不够格的模型硬着头皮往下做.** 返工的成本比重来一次高.

---

## 第 1 步. 预检: 仓库现在是健康的吗

在动任何东西之前先确认基线是绿的. **在一个本来就坏了的仓库上换数据集, 你分不清后面报的错
是新引入的还是原来就有的.**

```bash
git status --short          # 工作区应该是干净的, 或者只有你知道的改动
mise run cov                # 全部 Python + Node 测试, 带覆盖率. 必须全绿
mise run kill               # dev 端口是干净的
```

`mise run cov` 红了就先停下来, 把结果报给用户, 问他要不要先修. 不要带着红的测试往下走.

**再确认数据库凭据和 LLM 凭据是活的.** `.env` 里装的是密钥, **AI 不许读也不许改它**, 所以
只能靠探活脚本间接确认:

```bash
.venv/bin/python scripts/test_05_connect_remote_database.py     # DB_* 通不通
grep -n "^LLM_PROVIDER" .env.defaults                           # 默认走哪家
```

按 `LLM_PROVIDER` 跑对应的那一个探活脚本 (`.env` 可能覆盖了这个值, 但你读不到, 所以跑挂了
就直接问用户):

| provider | 脚本 |
| :--- | :--- |
| `bedrock` | `scripts/test_11_ai_aws_bedrock.py` |
| `anthropic` | `scripts/test_13_ai_anthropic_claude.py` |
| `openai` | `scripts/test_14_ai_openai.py` |
| `google` | `scripts/test_15_ai_google_gemini.py` |

**最后确认开发服务器能起来.** `mise run dev` 永远不会自己退出, 所以后台起, 另开一个会自己
退出的循环去等两个就绪标记 (Next.js 打 `Ready in`, uvicorn 打 `Application startup
complete.`), 看到之后立刻 `TaskStop` 停掉:

```bash
until grep -q "Ready in" <task-output-file> \
   && grep -q "Application startup complete" <task-output-file>; do sleep 0.5; done
```

`kill` 步骤返回 1 且没起服务, 说明有**别的 checkout** 占着 3000 或 8000. 那不是 bug, 是设计
好的拦截 —— 报给用户, 让他自己处理, 不要 `--force` 抢端口.

**最后一项: `frontend-design` plugin 装了吗.** 阶段二要用它. 看你自己的可用 skill 列表里
有没有 `frontend-design:frontend-design`. 没有的话**现在**就告诉用户, 让他从官方
marketplace 装上, 而不是等到阶段二才发现:

```bash
ls ~/.claude/plugins/cache/*/frontend-design 2>/dev/null || echo "NOT INSTALLED"
```

**没装不阻塞阶段一**, 只要在第 9 步交接的时候再提醒一次.

---

## 第 2 步. 认输入: `dataset/` 真的换成新的了吗

这一步要回答的只有一个问题: **`dataset/` 里躺着的, 是新数据集还是当前这个?**

```bash
ls -la dataset/
head -40 dataset/00-*summary*.md
grep -m 3 "^# \|^## " data/system-prompt.md
grep -n "displayName\|tagline" data/site.toml
```

| 你看到的 | 怎么办 |
| :--- | :--- |
| `dataset/` 的领域和 `data/` 完全不同 | 正常, 往下走 |
| `dataset/` 的领域和 `data/` 是同一个 | **停下**. 告诉用户新数据集还没放进去, 让他先把六个文件替换掉再来 |
| 一半新一半旧 (比如只换了两份文档) | **停下**. 半个数据集写不出一致的提示词, 让他补齐 |
| 有多个 `.sqlite` 或多个 `04-*generator*.py` | **停下**. `agent_app/dataset.py` 靠 discovery 找它们, 多个就抛异常. 让用户删掉不用的那些 |

### `dataset/` 里应该有什么

| 文件 | 里面是什么 | 拿它干什么 |
| :--- | :--- | :--- |
| `00-<name>_summary*.md` | 一段话讲清公司, 业务, 表数量, 行数, 能回答什么问题 | **最先读**. 全局地图, 决定文案基调 |
| `01-<name>_business_context*.md` | 公司画像, 商业模式, 行业科普, 术语表, 关键指标公式 | 提示词的领域概念; 业务说明的前两节 |
| `02-<name>_er_document*.md` | ER 图, 表定义, 完整 DDL, 数据生成规则 | 表清单, 外键顺序, 提示词的 Table Relationships |
| `03-<name>_sql_queries*.md` | 20 条业务 SQL, 每条带业务背景和难度 | 提示词的 Analysis Index 和 SQL Patterns |
| `04-<name>_data_generator*.py` | 造数脚本 | **只跑, 不改**. 只在要理解字段取值范围时翻 |
| `requirements.txt` | 生成器的依赖 | `gen-data` 会装它 |
| `<name>.sqlite`, `data/*.tsv` | 生成器的产物 | **不进 Git**, 新 clone 里不存在, 第 4 步造 |

带 `-cn` 后缀的是中文版. **有英文版就读英文版**, 只有中文版就读中文版 —— 但无论读哪个,
**产出一律是英文**.

`.tsv` **每个只看前 3 行**, 确认字段名和取值形态即可. 不要整个读, 有几十 MB.

### 读完之后你应该能回答这四个问题

答不上来就回去再读:

- 这家公司做什么生意, 靠什么赚钱?
- 有哪些表, 外键依赖顺序是什么 (父表在前)?
- 这个领域有哪些**外行会猜错**的术语和公式? (这些是提示词的核心, 通用 SQL 知识不是)
- 用户最想问的 12 个业务问题是什么?

---

## 第 3 步. 问用户: 文档里不会有的那几样

这几样任何业务文档里都没有. **开工前一次问完, 不要自己编了就往下走**, 也不要挤牙膏式地
问四轮. 用 AskUserQuestion, 每项都给一个你推荐的默认值:

| 要问的 | 决定什么 | 你该给的建议 |
| :--- | :--- | :--- |
| **品牌名 / 产品名** | `[brand]` 的 displayName, logoPrefix + logoAccent (会被拆成两种颜色), footerName; `[home.headline]` | 从 summary 里提两三个候选 |
| **agent 的名字** | `[chat] agent`, chat 页面里它怎么称呼自己 | 通常是品牌名的短形式 |
| **`SCHEMA_NAME`** | PostgreSQL schema 名, 也是 `quota.py` 的配额分区 key | 默认建议**数据集目录里的那个 `<name>`**: 小写字母/数字/下划线, 首字符非数字, <= 63 字符 |
| **教学材料改不改** | `README.md` / `TICKET.md` / `README-cn.md` / `docs/` | **默认不改**. 那是课程材料, 换数据集不等于改课程 |

配色方向**留到阶段二再问**. 现在问, 用户还没见过新网站长什么样, 答不准.

---

## 第 4 步. 建库并同步到 PostgreSQL

**这一步必须在写任何内容之前完成**, 因为后面每一步的验证都拿它当基准. 顺序错了当场就报.

```bash
CLI=.claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py

.venv/bin/python $CLI gen-data --force      # 装 dataset/requirements.txt, 跑生成器
ls -lh dataset/*.sqlite                     # 大小对得上 er_document 声称的量级吗
```

`--force` 会**先删光 `dataset/` 下所有 `.sqlite`** 再造. 换数据集必须用它: 上一个数据集留下
的文件会让 discovery 拒绝在两个文件之间选, 于是一次刚刚成功的重建看起来是坏的.

生成要几分钟. 跑挂一半会留下一个能打开但只有几张表的文件, **那种失败不报错**, 所以造完
要看一眼大小.

接着改配置, 然后同步:

```bash
# 1. 改 .env.defaults 的 SCHEMA_NAME (它进 Git, AI 可以自由编辑)
#    .env 装密钥, AI 不许读也不许改
# 2. 估一次体积: sqlite 超过 120MB 先和用户确认要不要减行
# 3. 先体检再同步 —— 脚本见 ref/verification-cn.md
mise run check-content                      # 空表 / 外键成环, 当场就报

.venv/bin/python $CLI sync-db               # 发布进 PostgreSQL 的 SCHEMA_NAME
.venv/bin/python $CLI verify-db             # 逐表对行数, 不一致就 exit 1
# 4. 量一次真实体积 —— 脚本见 ref/verification-cn.md
```

**`sync-db` 和 `verify-db` 不是可选的.** agent 在任何环境下读的都是 PostgreSQL, 本地也一样,
所以不同步就等于没有数据库. 而且失败方式很阴: **空 schema 和不存在的 schema 在反射器看来
一模一样** —— agent 会以为这个库没有表, 然后凭空编出一些看起来合理的表名来回答, 答得还很
自信.

同步是幂等的, 而且**只碰自己那个 schema**, 共用实例上别的项目的表不会被动到.

`dataset/<name>.sqlite` 现在**只是种子和同步源**, 不是任何人查询的对象.

---

## 第 5 步. 推导链: 顺序本身就是质量保证

**这一节是整个 skill 最重要的部分, 比第 6 步那张清单重要.**

要产出的东西 (提示词, kickstart 问题, 能力卡, 首页文案, tooltip, 业务说明) 描述的是**同一份
领域知识**. 如果它们各自去读数据集文档, 并行地写出来, 就一定会漂移 —— 不是可能, 是一定.

失败长这样, 而且**没有任何东西会报错**: 提示词只覆盖了源文档 20 条 query 里的 13 条, 而 12
个 kickstart 是另起炉灶从源文档写的, 于是首页多出两个按钮, 问的分析提示词根本没教. 测试
全过, 构建成功, 只有用户点下去的时候模型才开始即兴发挥.

**根治办法不是加校验, 是改顺序.** 串行推导可以让漂移**根本无法发生**: 每一步只从上一步的
产物推导, 不回头读原始文档.

### 铁律

> **提示词定义能力边界. 下游只能换措辞, 不能新增一项提示词没教的能力.**

想让首页出现某个分析, 唯一的合法路径是**先把它写进提示词**.

### 五步, 严格按顺序

每一步的文件形状见 [`ref/data-files-spec-cn.md`](ref/data-files-spec-cn.md), 文案口吻见
[`ref/writing-style-cn.md`](ref/writing-style-cn.md).

**第 1 步. `data/system-prompt.md` —— 唯一允许通读全部数据集文档的一步.**
输入: business_context + er_document + sql_queries 全文.

- 先写 `## Analysis Index`, 源文档每条 query 一行, **一条都不能漏**
- 再从中挑**外行会算错的**, 在 `## Derived Business Concepts` 里给精确公式和 SQL
- 把 [`ref/system-prompt-render-blocks.md`](ref/system-prompt-render-blocks.md) **整段逐字
  抄进去**, 只换例子
- **SQL 一律写 PostgreSQL 方言.** 方言对照表在 spec 里
- 写完**把每一段 SQL 对着真库跑一遍** (脚本见 `ref/verification-cn.md`). 跑不通的例子比没有
  例子更糟, 模型会照抄然后在用户面前失败

**第 2 步. `[[chat.suggestedActions]]` 12 条.**
输入: **只看第 1 步产出的提示词**, 不要回头翻 sql_queries.

逐条对着 `## Analysis Index` 挑 11 条改写成用户口吻的问题 (第 1 条固定是 Introduction).
**挑不出来说明提示词覆盖不够, 回第 1 步补, 不要在这里现编.**

渲染配额 (四类各恰好 3 条) 和选题的判据在 spec 里, 这是整个 `site.toml` 里最容易做砸的一节.

**第 3 步. `site.toml` 的其余部分.**
输入: 提示词 (定能力) + 数据库 (定数字) + business_context (定叙事口吻) + 用户给的品牌名.

`[[capabilities]]` 四条 = 提示词里最重要的四条主线. `home.blurb` 里的表数和行数**此刻现场
从数据库数出来**, 不要抄旧值也不要估.

**第 4 步. `data/business-context.md`.**
输入: 提示词 (定第 5 节) + business_context 全文 (定第 1 2 节) + er_document (定第 3 节).

六节结构和每节必须回答的问题在 spec 里.

**第 5 步. 清掉脚本和测试里的硬编码.** 见下面 D 组.

### 为什么不给这些一致性加 lint

判据是自然语言语义, 只能做成模糊匹配, 必然产出一堆需要人工判断的 warn, 最后没人看.
**一个会误报的检查比没有检查更糟, 因为它训练人忽略输出.**

分界线在这里: **"这 12 条里有没有恰好 3 条写了 `as a flowchart`" 是机械问题, "这 12 条问得
好不好" 不是.** 前者写成脚本 (`mise run check-content` 已经在做), 后者靠上面这个顺序和用户验收.

---

## 第 6 步. 完备性核对表

**这不是执行顺序, 是核对表.** 按第 5 步做完之后, 逐行过一遍确认没有漏项.

**A. 业务大脑**

| 文件 | 说明 |
| :--- | :--- |
| `data/system-prompt.md` | 整份重写, 含 Analysis Index 和逐字抄的渲染层五节 |

**B. 配置** —— 后端只有一行

| 文件 | 要改的 key |
| :--- | :--- |
| `.env.defaults` | `SCHEMA_NAME` —— **后端唯一要改的一行** |
| `.env` | **一个字都不许动**, 也不许读. 它装的是密钥 |

**C. 内容** —— 无法配置化, 只能手写

| 文件 | 数量 |
| :--- | :--- |
| `data/site.toml` | 全部段落, 含 4 张能力卡和 12 条 kickstart |
| `data/business-context.md` | 六节 |

**D. 脚本和测试里的硬编码** —— 这一组最容易漏

| 文件 | 里面是什么 |
| :--- | :--- |
| `scripts/test_21_agent.py` | 10 个 `request_NN` 变量, 全是上一个领域的业务问题, 全部重写 |
| `scripts/test_02_run_sql_locally.sql` | 一条示例 SQL, 引用了旧表名 |
| `tests_python/one/test_one_one_04_agent.py` | 断言里写死了旧表名 (`FROM loan`, `DROP TABLE loan`), 换成新库里真实存在的表 |

**E. 明确不用改的**

- **`agent_app/` 下除提示词外的所有代码.** 包名 `agent_app` 就是为了换数据集时不用改
- **`components/chat/blocks/` 渲染层.** Mermaid 和 chart 与数据集无关
- **`README.md`, `TICKET.md`, `README-cn.md`, `docs/`.** 那是教学材料 (第 3 步已经问过用户)
- **schema 参考文件.** 没有需要维护的文件, 要看就跑
  `.venv/bin/python scripts/test_04_print_database_schema.py`, 它直接读库, 永远是真的

E 组第一行能成立, 靠的是一条纪律: **通用代码的注释和 docstring 里不许用本数据集的表名举
例.** 写 `# e.g. the "loan" table` 等于把当前数据集焊进了通用代码 —— 换数据集之后它不报错,
不失败, 只是变成一句谎话躺在那里. 用永远虚构的 `acme` / `widget` / `part`.

新写通用代码时同样适用: 只要你在 `agent_app/` 或 `scripts/` 里写下一个表名做例子, 先问一句
**换数据集之后这句话还对吗**.

---

## 第 7 步. 验证

全部脚本和判据在 [`ref/verification-cn.md`](ref/verification-cn.md). 这里只列该跑什么:

```bash
mise run check-content      # 建表顺序 / 提示词表名 / 内容文件 / 渲染配额
mise run test       # check + Python + Node
mise run build-web      # site.toml 的缺 key 和图标名, 只有这里查得到
```

**三条都要跑, 它们查的东西不重叠.** 只跑前两条的话, 一个拼错的图标名会安静地渲染成兜底
图标, 卡片看着好好的, 就是配错了图.

外加四件 `mise` 查不到的:

1. **提示词里每一段 SQL 对着真库 (PostgreSQL) 跑一遍**
2. **数据体检**: 空表 / 孤儿外键 / 日期越界, 外加用眼睛看核心指标算出来的数字合不合常识
3. **破折号自查**: `data/site.toml` 和 `data/business-context.md` 里一个都不许有
4. **体积**: 同步之后量一次真实数字, 别顶到 500MB 那条共享线

---

## 第 8 步. 自己先跑一遍网站

**不要把一个自己没打开过的网站交给用户验收.**

后台起 `mise run dev`, 等两个就绪标记 (方法见第 1 步), 然后自己过一遍:

- 打开 `/`, 确认四张能力卡, 弹窗, 页脚都是新领域的话
- 打开 `/chat`, **至少各点一条**: 一条 table, 一条 flowchart, 一条 chart. 确认块真的出来了
- 出不来最常见的原因是提示词里 `Rendering Triggers` 那节被精简过

自己跑完就 `TaskStop` 停掉这个服务器 —— 它是你为了验证起的, 归你清理.

---

## 第 9 步. 闸门: 交给用户验收

**明确告诉用户: 内容已经换完, 但页面还是上一个行业的视觉, 请先自己跑一下看功能对不对.**

```bash
mise run dev
```

告诉他打开 `http://localhost:3000/` 和 `http://localhost:3000/chat`, 然后**给他这张清单**:

- agent 回答得像不像这个领域的专家
- **12 条 kickstart 逐条点一遍, 该出的块真的出来了**: 3 条出表格加 SQL 高亮, 3 条出流程图,
  3 条出图表. 这一条必须手点 —— 配额脚本只能证明问法写对了, 证明不了模型照做了
- 每条问题不要转太久. 转很久的那条不是慢, 是要回去把问题问小
- 答案里的数字没有一眼假的 (比率不是 0%, 排序符合常识). 不必逐行对账, 但明显离谱的必须查
- 首页文案和 chat 页文案有没有残留旧领域的说法
- 点开首页那个业务说明弹窗, 一个完全不懂这行的人读完能不能明白这个 App 解决什么问题
- 四张能力卡 hover / Tab 聚焦 / 手机点按, tooltip 都能弹出, 窄屏下不跑出屏幕.
  **首页和 agent 页各看一遍** —— 两边渲染的是同一份 `[[capabilities]]`

然后说清楚**怎么进入第二步**:

> 有意见随时说, 我改完你再看, 直到功能你满意为止. 满意之后跟我说一声"进入第二步"或者
> "开始改前端", 我就开始做视觉: 配色, 字体, 构图, 图表色板.

如果第 1 步发现 `frontend-design` plugin 没装, **在这里再提醒一次**.

**用户没有明确说满意之前, 不要开始阶段二.** 他说了三处小意见并不等于验收通过 —— 改完再问
一次.

---

## 第 10 步. 阶段二: 定调性并问用户

用户放行之后, 先做两件事, 顺序不能反:

**一, 说一句话告诉用户你要进入阶段二了, 并且明说你正在加载视觉设计 skill.** 用户看到的是
一堆 diff, 他需要知道你依据的是什么.

**二, 真的用 Skill 工具加载 `frontend-design:frontend-design`** (带 plugin 前缀的全名), 按它
给的规范做. **不要凭记忆写"我觉得好看的配色".**

然后**先分析调性, 再问用户**. 调性从这个 App 的**行业观感**来, 不是从个人偏好来: 干这行的
人每天盯着的屏幕长什么样?

用 AskUserQuestion 给**两到三个方向**, 每个方向要**连色值带构图一起说清楚**, 而不是只给一句
形容词. 至少覆盖: 情绪一个词, 浅底还是深底, 主色加强调色, 排版气质. 判据和展开见
[`ref/frontend-redesign-cn.md`](ref/frontend-redesign-cn.md).

---

## 第 11 步. 动手改视觉

文件清单, 三样不许重写的东西, 两条样式约束, 全在
[`ref/frontend-redesign-cn.md`](ref/frontend-redesign-cn.md).

三件最容易出事的:

- **别只改首页.** 首页很漂亮而 chat 页还是旧配色, 是这一步最典型的失败
- **改图表配色时加载 `dataviz` skill**, 跑它自带的调色板 validator, 别靠眼睛判断
- **加了新图标要同步注册进 `lib/icons.ts`**, 否则 `next build` 直接失败

改完再跑一次 `mise run build-web` / `mise run check-content` / `mise run test` —— 改图标名或删组件都可能
把编译打断.

然后**亲眼看两个页面**, 按 `ref/frontend-redesign-cn.md` 那张验收清单走一遍, 再交给用户.

---

## 第 12 步. 收尾与交付

用户对视觉也满意之后, 做完这四件事才算结束:

**一, 旧领域词汇扫描.** 词表是一次性参数, 不提交进仓库:

```bash
mise run check-content -- --retired "旧数据集最有辨识度的几个名词"
```

挑词要挑准 —— 拿 `node` 这种通用词去扫会报出一堆正常用词, 你会学会忽略这个检查.

**二, 清理上一个数据集在 PostgreSQL 上的残表.** 它们住在别的 schema 里, 新的同步永远不会
碰到, 所以会一直占着那个**和别的项目共用**的 500MB 配额而不发出任何声音.

先列出全库的 schema (脚本在 `ref/verification-cn.md`), **把旧 schema 的名字报给用户, 等他
明确说删, 再删**. 那个库上还住着别的项目, 删错一个是不可逆的.

**三, 最后跑一次全套:**

```bash
mise run check-content
mise run test
mise run build-web
git status --short
```

`git status` 应该只落在这几处: `data/`, `dataset/`, `.env.defaults`, 视觉相关的
`app/ components/ lib/icons.ts tailwind.config.ts`, 以及 D 组那三个硬编码文件. **落到别处
就是信号**, 回去看一眼那是不是越界了.

**四, 给用户一段交付说明**, 讲清四件事:

- 换成了什么数据集, schema 名是什么, 多少张表多少行
- 视觉定的调性是什么, 一句话
- 还需要他自己做的事 (比如部署时要在 Vercel 面板里录 `.env` 那些密钥, 因为 `.env` 不进 Git)
- 旧 schema 删了没有

顺便提一句: 要把这个仓库作为作品集交付出去的话, **教学层是可以整块删掉的** (`README.md`,
`TICKET.md`, `docs/`, `.claude/skills/`, `dataset/`, `agent_app/dataset.py`,
`tests_python/test_dataset.py`, `scripts/`, 外加 `mise.toml` 里依赖 `scripts/` 的 `check`
任务), 删完仍然是一个能跑的 app, 一行代码都不用改. **这件事要单独问用户, 不要顺手做掉.**
