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

### 2.2 建立映射关系

这是完整清单. **每一行都要过一遍**, 确认是改了还是明确判断不用改.

**A. 业务大脑.** 信息量最大, 最花时间的一块.

| 文件 | 来源 | 说明 |
| :--- | :--- | :--- |
| `agent_app/prompts/bi-agent-system-prompt.md` | business_context + er_document + sql_queries | 整份重写. 保留 `## Diagrams` 和 `## Charts` 两段的结构 (那是前端能力, 与数据集无关), 只把里面的例子换成新领域的 |

写提示词时注意一个坑: `mise run check` 会把提示词里的 `FROM x` 和 `JOIN x` 当表名校验, 它分不清散文和 SQL. `drawn from a zero baseline` 里的 `from a` 会被判成表 `a` 而让构建失败. 换个说法即可.

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

`capabilities` 和 `insights` 里的 `icon` 必须是 `lib/icons.ts` 里已注册的名字, 否则**编译报错**. 需要新图标就在那个文件里 import 并加进 `ICONS`. 从 lucide-react 挑.

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
| `data/database-exploration/database-schema.txt` | schema 参考文件. 不要手写, 跑 `.venv/bin/python scripts/test_04_print_database_schema.py` 重新生成 |

**E. 用户必须提供的.** 输入文档里不会有这些.

这几样任何业务文档里都不会有, 开工前先问用户. 不要自己编了就往下走:

- **品牌名 / 产品名**: 决定 `displayName`, `logo.prefix` + `logo.accent` (会被拆成两种颜色), `footerName`
- **`project.name` 短标识**: 远程 Postgres 的表前缀, 多项目共用一个库靠它隔离, 越短越好
- **agent 的名字**: chat 页面里它怎么称呼自己
- **配色方向**: 可以从行业推断 (金融偏藏青, 医疗偏青绿), 但要让用户确认

**F. 明确不用改的.**

不要浪费时间在这些上面:

- `agent_app/` 下除提示词外的所有代码. 它是通用的, 包名 `agent_app` 就是为了换数据集时不用改
- `components/chat/blocks/` 渲染层. Mermaid 和 chart 与数据集无关
- `README.md`, `TICKET.md`, `README-cn.md`, `docs/`. 那是教学材料, 换数据集不等于改课程. **要改就单独问用户**

### 2.3 执行

顺序有讲究. 先数据库, 因为后面每一步的验证都依赖它.

1. 复制 sqlite, 跑 `mise run setup-db`
2. 改 `config/dataset.toml` 的 `tableInsertOrder`, 立刻跑 `mise run check`. 它会拿配置和真实 sqlite 对撞, 顺序错了当场报
3. 重写提示词
4. 改 `config/site.ts` (需要新图标就先改 `lib/icons.ts`)
5. 改 `data/suggested-actions.json`
6. 改脚本和测试里的硬编码
7. 重新生成 `database-schema.txt`

每改完一块就验证, 不要攒到最后:

```bash
mise run check
mise run test
```

跑 `mise run dev` 起本地服务 (Next.js + FastAPI), 打开 `/` 和 `/chat` 看效果. 注意 `mise run dev` 会先杀掉旧进程再起, 不用手动清理.

最后跑一次带旧领域词汇的检查. 这是专门用来抓 "改漏了" 的, 词表是一次性参数, 不提交进仓库:

```bash
mise run check -- --retired "loan,lending,borrower,default_event,risk_grade"
```

把上一个数据集**最有辨识度的名词** 填进去. 有残留它会精确报出文件和行号.

### 2.4 停下来让用户验收, 然后做视觉

阶段一到此为止. **明确告诉用户: 内容已经换完, 但页面还是上一个行业的视觉, 请先跑一下看功能对不对.** 让他确认这几件事:

- agent 回答得像不像这个领域的专家
- 12 个 kickstart 问题点下去是否都能出结果
- 首页文案和 chat 页文案有没有残留旧领域的说法

用户满意之后再进入视觉改造, 这一步**加载 `frontend-design:frontend-design` skill** 来做 (注意是带 plugin 前缀的全名).

视觉相关的代码就这些, 别只改首页就收工:

| 层面 | 文件 |
| :--- | :--- |
| 配色系统 | `tailwind.config.ts` (现在是 Navy + Gold 的 "Fintech Color System"), `app/globals.css` 的 `:root` 变量 |
| 字体 | `app/layout.tsx` 里的 `next/font/google` (现在是 Inter + Figtree + Noto Sans) |
| favicon | `app/icon.png` |
| 导航栏 | `app/_components/layouts/Navigation.tsx` (logo 的两段式着色在这里) |
| 首页 | `app/(marketing)/_components/Hero.tsx`, `app/(marketing)/HomePageContent.tsx` |
| **chat 空状态** | `components/chat/overview.tsx` (标题, 4 张洞察卡) |
| **chat 输入区** | `components/chat/multimodal-input.tsx` (12 张 kickstart 卡片的排布) |
| **chat 对话气泡** | `components/chat/message.tsx` (AI 头像那个方块, 用户头像, 气泡配色) |
| **chat 顶部横幅** | `components/chat/chat.tsx` (那条介绍 agent 的 banner) |
| 图表配色 | `app/globals.css` 的 `.viz-root` token |

加粗的四行是最常被忘掉的. 首页改得很漂亮而 chat 页还是旧配色, 是这一步最典型的失败.

图标有两个来源: 从 lucide-react 挑现成的 (记得同步注册进 `lib/icons.ts`), 或者自己画 SVG 放进 `components/chat/icons/`. 后者适合行业特有的形状.

改图表配色时注意 `app/globals.css` 里 `.viz-root` 的深色 token 只认 `.dark` class, 不认系统偏好, 因为全站 Tailwind 是 `darkMode: ["class"]` 策略, 别去接 `prefers-color-scheme`. 换配色之后加载 `dataviz` skill, 跑它自带的调色板 validator, 别靠眼睛判断.

视觉改完再跑一次 `mise run check` 和 `mise run test`, 因为改图标名或删组件都可能把编译打断.
