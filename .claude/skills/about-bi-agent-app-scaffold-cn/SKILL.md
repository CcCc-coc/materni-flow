---
name: about-bi-agent-app-scaffold-cn
description: 这个仓库的事实标准. 它是什么性质的项目, 为什么这样切模块, 以及换数据集时哪些边界不能破. 动手改这个仓库之前先读, 尤其是重构, 挪文件, 加模块, 或者要判断某个东西该放哪一层的时候.
---

# BI Agent App 脚手架: 事实标准

这个 skill 是这个仓库的**总纲**. 它回答的是"这是什么, 为什么长成这样", 不回答"代码在哪"
(那个看 `CLAUDE.md`) 也不回答"怎么换数据集" (那个看 `swap-dataset-cn`).

`ref/` 分三个目录, 一篇一个主题. **按你要动的东西读对应那篇, 不要全读.**

`ref/architecture/` —— 架构与设计决定, 与具体某段代码无关:

| 你在做什么 | 读 |
| :--- | :--- |
| 想搞清楚这个项目的定位, 或者要对外介绍它 | [01-what-this-project-is.md](ref/architecture/01-what-this-project-is.md) |
| 加东西时拿不准该放哪, 或者要擦掉教学痕迹交付 | [02-teaching-and-production.md](ref/architecture/02-teaching-and-production.md) |
| 动 `dataset/`, 造数据, 换数据集的源材料 | [03-the-dataset.md](ref/architecture/03-the-dataset.md) |
| 重构, 挪文件, 加模块, 判断某个东西该放哪一层 | [04-modular-design.md](ref/architecture/04-modular-design.md) |
| 动数据库, 写 SQL, 同步数据, 估体积 | [05-why-postgres-everywhere.md](ref/architecture/05-why-postgres-everywhere.md) |
| 让 agent 画图 / 出表格, 或者加一种新的渲染块 | [06-rendering-contract.md](ref/architecture/06-rendering-contract.md) |
| 加一个配置项, 或者写 `data/` 下那三个文件 | [07-config-and-content.md](ref/architecture/07-config-and-content.md) |
| 想知道改完要跑什么, 或者要加/改一项检查 | [08-what-guards-the-boundaries.md](ref/architecture/08-what-guards-the-boundaries.md) |
| 写注释 / docstring, 或者要加一篇文档但不知道放哪 | [09-comments-and-docs.md](ref/architecture/09-comments-and-docs.md) |

`ref/backend/` —— `agent_app/` 里某段 Python 为什么这么写, 一篇对一组模块:

| 你在做什么 | 读 |
| :--- | :--- |
| **要改 `agent_app/` 里某个模块** | [backend/README.md](ref/backend/README.md) 的索引表, 编号就是依赖顺序 |
| **给 agent 加一个 tool**, 或者动 `one/` 里任何东西 | [backend/08](ref/backend/08-the-one-object.md) |
| 改 `/api/chat` 的流程 | [backend/09](ref/backend/09-http-entry-point.md) |
| 写测试, 或者要用 `# pragma: no cover` | [backend/10](ref/backend/10-testing.md) |
| 要造数据集 / 同步到 PostgreSQL | `scripts/teaching_cli.py`, 说明在 [backend/11](ref/backend/11-dataset-pipeline.md) |

`ref/operations/` —— 维护这个仓库的日常参考:

| 你在做什么 | 读 |
| :--- | :--- |
| 开发服务器起不来 / 杀不掉, 或者要动 `kill-dev-servers.py` | [01-dev-servers.md](ref/operations/01-dev-servers.md) |

前端 (`app/`, `components/`, `lib/`) 目前没有对应目录, 将来是 `ref/frontend/`.

渲染器**内部**怎么实现的 (流式期间的残缺围栏, 懒加载, 安全等级, 兜底), 在另一个 skill:
`agent-app-design-cn` 的 `ref/chat-frontend.md`. 它有 `paths` 触发器, 你编辑
`components/chat/` 时会自动加载.

---

## 这几篇文档的地位

**它们是事实标准, 不是参考读物.** 要么照做, 要么在改代码的**同一个 commit 里改文档**,
别让两边对不上. 一份描述着三个月前的目录结构的规范, 比没有规范更糟: 它会让下一个人
(或者下一个 AI) 自信地改错地方.

写新规范就放进对应的子目录, 在上面那张表里加一行.

`scripts/teaching_cli.py` 是**教学自动化的命令行**: 造数据集, 发布到 PostgreSQL, 逐表核对.
它住在这里而不是 `mise.toml` 里, 因为 mise 跑的是应用, 而这些都不是应用 —— 教学层要能靠
"删几个目录"擦掉, 不该留下需要从共用配置里一行行挑的残渣.

```bash
.venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py --help
```

三个目录的分工: `architecture/` 讲**边界和设计决定** (什么该放哪一层, 换数据集时不能破
什么), `backend/` 讲**某段 Python 为什么长这样** (一篇对一组模块), `operations/` 讲
**日常维护**. 代码里的注释只留很短的工程 why, 展开的部分在这里 —— 两边都不完整, 加起来
完整, 而且可以独立删掉其中一边. 这条规矩本身见
[architecture/09](ref/architecture/09-comments-and-docs.md).

## 一条贯穿全仓库的判断

这个仓库的每一个设计决定, 追到底都是同一个问题:

> **这个东西是随数据集变的, 还是随脚手架不变的?**

变的东西全部在 `data/` 一个目录里, 换数据集就是重写那个目录. 不变的东西是脚手架本体,
换数据集时一行都不该动. 拿不准一个新增的东西该放哪, 先问这句话.

具体怎么切的, 看 02.
