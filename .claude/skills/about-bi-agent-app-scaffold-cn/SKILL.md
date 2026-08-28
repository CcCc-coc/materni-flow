---
name: about-bi-agent-app-scaffold-cn
description: 这个仓库的事实标准. 它是什么性质的项目, 为什么这样切模块, 以及换数据集时哪些边界不能破. 动手改这个仓库之前先读, 尤其是重构, 挪文件, 加模块, 或者要判断某个东西该放哪一层的时候.
---

# BI Agent App 脚手架: 事实标准

这个 skill 是这个仓库的**总纲**. 它回答的是"这是什么, 为什么长成这样", 不回答"代码在哪"
(那个看 `CLAUDE.md`) 也不回答"怎么换数据集" (那个看 `swap-dataset-cn`).

规范都在 `ref/` 下面, 一篇一个主题. **按你要动的东西读对应那篇, 不要全读.**

| 你在做什么 | 读 |
| :--- | :--- |
| 想搞清楚这个项目的定位, 或者要对外介绍它 | [01-what-this-project-is.md](ref/01-what-this-project-is.md) |
| 重构, 挪文件, 加模块, 判断某个东西该放哪一层 | [02-modular-design.md](ref/02-modular-design.md) |
| 动数据库, 写 SQL, 同步数据, 估体积 | [03-one-database-everywhere.md](ref/03-one-database-everywhere.md) |
| 让 agent 画图 / 出表格, 或者加一种新的渲染块 | [04-rendering-contract.md](ref/04-rendering-contract.md) |
| 写 `data/` 下面那几个文件 (配置, 文案, 提示词) | [05-authoring-the-data-directory.md](ref/05-authoring-the-data-directory.md) |
| 想知道改完要跑什么, 或者要加/改一项检查 | [06-what-guards-the-boundaries.md](ref/06-what-guards-the-boundaries.md) |
| 写注释 / docstring, 或者要加教学材料 | [07-comments-explain-why.md](ref/07-comments-explain-why.md) |
| 开发服务器起不来 / 杀不掉, 或者要动 `kill-dev-servers.py` | [08-killing-dev-servers.md](ref/08-killing-dev-servers.md) |
| **要改 `agent_app/` 里某个模块, 想知道它为什么这么写** | [source-code/](ref/source-code/README.md) |

渲染器**内部**怎么实现的 (流式期间的残缺围栏, 懒加载, 安全等级, 兜底), 在另一个 skill:
`agent-app-design-cn` 的 `ref/chat-frontend.md`. 它有 `paths` 触发器, 你编辑
`components/chat/` 时会自动加载.

---

## 这几篇文档的地位

**它们是事实标准, 不是参考读物.** 要么照做, 要么在改代码的**同一个 commit 里改文档**,
别让两边对不上. 一份描述着三个月前的目录结构的规范, 比没有规范更糟: 它会让下一个人
(或者下一个 AI) 自信地改错地方.

写新规范就放进 `ref/`, 在上面那张表里加一行.

`ref/` 的 01-08 讲的是**边界**: 什么该放哪一层, 换数据集时不能破什么. `ref/source-code/`
讲的是**某段代码为什么长这样**, 一篇对一组模块. 代码里的注释只留很短的工程 why, 展开的
部分在那里 —— 两边都不完整, 加起来完整, 而且可以独立删掉其中一边.

## 一条贯穿全仓库的判断

这个仓库的每一个设计决定, 追到底都是同一个问题:

> **这个东西是随数据集变的, 还是随脚手架不变的?**

变的东西全部在 `data/` 一个目录里, 换数据集就是重写那个目录. 不变的东西是脚手架本体,
换数据集时一行都不该动. 拿不准一个新增的东西该放哪, 先问这句话.

具体怎么切的, 看 02.
