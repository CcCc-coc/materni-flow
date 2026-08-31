---
name: about-bi-agent-app-scaffold-cn
description: 这个仓库的事实标准, 分四块: architecture (边界与设计决定), backend (agent_app/ 的 Python), frontend (Next.js 界面), operations (怎么把它跑起来). 动手改这个仓库之前先读, 尤其是重构, 挪文件, 加模块, 加 agent tool, 改界面, 换数据集, 或者要判断某个东西该放哪一层的时候.
---

# BI Agent App 脚手架: 事实标准

这个 skill 是这个仓库的**总纲**. 它回答"这是什么, 为什么长成这样", 不回答"代码在哪"
(那个看 `CLAUDE.md`), 也不回答"怎么一步步换数据集" —— 那件事分两条命令走,
`/run-swap-dataset-phase-1-cn` 换内容, `/run-swap-dataset-phase-2-cn` 换视觉, 它们共用的
知识库是 `swap-dataset-cn` skill.

**用法: 在下面那张表里找到你要做的事, 只读那一篇.** 不要全读.

---

## 按任务查

| 我要做的事 | 读 |
| :--- | :--- |
| **第一次把仓库跑起来** | [operations/01](ref/operations/01-overview.md) |
| 填 `.env`, 换 LLM provider, 打开花费配额 | [operations/02](ref/operations/02-configuration.md) |
| 造数据集, 同步 PostgreSQL, 换完数据集重灌 | [operations/03](ref/operations/03-the-database.md) |
| 起 / 停开发服务器, 搞不清 mise 和 pnpm/uv 谁调谁 | [operations/04](ref/operations/04-dev-servers.md) |
| 改完之后要跑什么才算验过, **或者要加一项检查** | [architecture/08](ref/architecture/08-what-guards-the-boundaries.md) |
| | |
| 重构, 挪文件, 加模块, **判断一个东西该放哪一层** | [architecture/04](ref/architecture/04-modular-design.md) |
| 加东西时拿不准算教学层还是生产层 | [architecture/02](ref/architecture/02-teaching-and-production.md) |
| 加一个配置项 | [architecture/07](ref/architecture/07-config-and-content.md) |
| 写 `data/` 下那三个文件 (提示词 / 文案 / 业务说明) | [architecture/07](ref/architecture/07-config-and-content.md) |
| 动 `dataset/` 的源材料 | [architecture/03](ref/architecture/03-the-dataset.md) |
| 写 SQL, 动数据库, 估体积 | [architecture/05](ref/architecture/05-why-postgres-everywhere.md) |
| 要对外介绍这个项目 | [architecture/01](ref/architecture/01-what-this-project-is.md) |
| 写注释 / docstring, **或者要写这批文档本身** | [architecture/09](ref/architecture/09-comments-and-docs.md) |
| | |
| **给 agent 加一个 tool**, 或动 `one/` 里任何东西 | [backend/08](ref/backend/08-the-one-object.md) |
| 改 `/api/chat` 的流程 | [backend/09](ref/backend/09-http-entry-point.md) |
| 写 Python 测试, 或要用 `# pragma: no cover` | [backend/10](ref/backend/10-testing.md) |
| 改 agent 看到的库结构字符串 | [backend/04](ref/backend/04-schema-encoding.md) |
| 改 SQL 执行 / 只读保证 | [backend/03](ref/backend/03-sql-execution.md) |
| 改别的 `agent_app/` 模块 | [backend/README](ref/backend/README.md) 的索引, **编号就是依赖顺序** |
| | |
| **改界面上任何一块**, 想知道它的文字从哪来 | [frontend/02](ref/frontend/02-the-elements.md) 的元素对照表 |
| 加一个文案项, 或动 `lib/site/` | [frontend/03](ref/frontend/03-content-pipeline.md) |
| 改首页 / 改 agent 页 | [frontend/05](ref/frontend/05-home-page.md) / [frontend/06](ref/frontend/06-chat-page.md) |
| 动路由, 布局, SEO | [frontend/04](ref/frontend/04-pages-and-shell.md) |
| 改配色 / 圆角 / 卡片外观 | [frontend/08](ref/frontend/08-design-tokens.md) |
| | |
| **加一种新的渲染块** (表格 / 流程图 / 图表之外) | 三处一起改, 见 [architecture/06](ref/architecture/06-rendering-contract.md) |
| 让 agent 画图但它不画 | [architecture/06](ref/architecture/06-rendering-contract.md) |
| 动 Markdown 渲染或某个块渲染器 | [frontend/07](ref/frontend/07-markdown-and-blocks.md) |
| agent 的回答解析不对 (思考 / 空答案) | [backend/07](ref/backend/07-agent-response.md) |

---

## 四个目录

拿不准该查哪一块时, 按这个问题分:

| 目录 | 回答的问题 | 完整索引 |
| :--- | :--- | :--- |
| `ref/architecture/` | 这该放哪一层? 这条边界破了会怎样? | [README](ref/architecture/README.md), 9 篇 |
| `ref/backend/` | `agent_app/` 这段 Python 为什么这么写? | [README](ref/backend/README.md), 11 篇, **按依赖顺序编号** |
| `ref/frontend/` | 界面必须做到什么? 这段 TypeScript 为什么这么写? | [README](ref/frontend/README.md), 8 篇, **前两篇讲需求** |
| `ref/operations/` | 怎么让它跑起来? | [README](ref/operations/README.md), 4 篇, **按四步排序** |

一件事同时落在两块时, 先读 `architecture/` 那篇拿边界, 再读 `backend/` 或 `frontend/` 那篇
拿实现. 渲染契约就是典型: 规则在 `architecture/06`, 而三处实现分别在 `frontend/07`,
`backend/07` 和 `data/system-prompt.md`.

---

## 这批文档的地位

**它们是事实标准, 不是参考读物.** 要么照做, 要么在改代码的**同一个 commit 里改文档**,
别让两边对不上. 一份描述着三个月前目录结构的规范, 比没有规范更糟: 它会让下一个人 (或者
下一个 AI) 自信地改错地方.

写法本身也有规矩, 见 [architecture/09](ref/architecture/09-comments-and-docs.md):

- **代码里只留很短的工程 why**, 展开的部分放这里 —— 两边都不完整, 加起来完整, 而且可以
  独立删掉其中一边
- **文档写现在, 不写过去** —— 写"现在是怎么做的, 为什么", 不写"我们以前怎么错的"
- **文档可以引用代码路径, 代码不能引用文档路径** —— 这是单向的

加一篇新文档: 放进对应的子目录, 在那个目录的 README 里加一行; 如果它是一个常见任务的入口,
再在上面那张按任务查的表里加一行.

---

## `scripts/teaching_cli.py`

教学自动化的命令行: 造数据集, 发布到 PostgreSQL, 逐表核对.

```bash
.venv/bin/python .agents/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py --help
```

它住在这里而不是 `mise.toml` 里, 因为 mise 跑的是应用, 而这些都不是应用 —— 教学层要能靠
"删几个目录"擦掉, 不该留下需要从共用配置里一行行挑的残渣. 用法见
[operations/03](ref/operations/03-the-database.md).

---

## 一条贯穿全仓库的判断

这个仓库的每一个设计决定, 追到底都是同一个问题:

> **这个东西是随数据集变的, 还是随脚手架不变的?**

变的东西全部在 `data/` 一个目录里, 换数据集就是重写那个目录. 不变的东西是脚手架本体,
换数据集时一行都不该动. 拿不准一个新增的东西该放哪, 先问这句话 —— 具体怎么切的见
[architecture/04](ref/architecture/04-modular-design.md).

---

> **一处已知重复**: `agent-app-design-cn` skill 的 `ref/chat-frontend.md` 讲的是
> `components/chat/` 那同一段代码, 而且有过期内容 (它还在描述已经删掉的暗色模式). 它唯一
> 的独有价值是那个 `components/chat/**` 的 `paths` 自动触发器. 两边合并之前, **以
> `ref/frontend/` 为准**.
