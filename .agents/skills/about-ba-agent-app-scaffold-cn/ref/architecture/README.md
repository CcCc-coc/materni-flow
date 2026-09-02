# 架构与设计决定

这个仓库为什么被切成现在这样, 每条边界划在哪, 破了会怎样. **和具体某段代码无关** —— 那在
[`../backend/`](../backend/README.md) 和 [`../frontend/`](../frontend/README.md).

---

## 索引

| 篇 | 讲什么 |
| :--- | :--- |
| [01-what-this-project-is.md](01-what-this-project-is.md) | 这是什么项目, 六个深化方向, 为什么"换领域"是它存在的理由 |
| [02-teaching-and-production.md](02-teaching-and-production.md) | 它同时是一个应用和一门课, 两层怎么分, 交付前怎么擦干净 |
| [03-the-dataset.md](03-the-dataset.md) | `dataset/` 装什么, 产物为什么不进 Git, 它和 `data/` 的分工 |
| [04-modular-design.md](04-modular-design.md) | **模块化的四个目的, 以及全部边界** |
| [05-why-postgres-everywhere.md](05-why-postgres-everywhere.md) | 本地为什么也连生产的 PostgreSQL, schema 隔离, 方言清单 |
| [06-rendering-contract.md](06-rendering-contract.md) | **提示词 / kickstart 配额 / 前端查找表, 三方契约** |
| [07-config-and-content.md](07-config-and-content.md) | 什么进环境变量, 什么进 `data/`, 那三个文件怎么写 |
| [08-what-guards-the-boundaries.md](08-what-guards-the-boundaries.md) | 每条边界谁在守, 哪三条根本没有机械检查 |
| [09-comments-and-docs.md](09-comments-and-docs.md) | 注释写 why, 文档写现在, 一段话该放哪个家 |

从 01 往下读是一条完整的路线. 只想解决一个具体问题的话, 看
[SKILL.md](../../SKILL.md) 那张按任务查的表.

---

## 一条贯穿全部的判断

> **这个东西是随数据集变的, 还是随脚手架不变的?**

变的东西全部在 `data/` 一个目录里, 换数据集就是重写那个目录. 不变的东西是脚手架本体,
换数据集时一行都不该动. 拿不准一个新增的东西该放哪, 先问这句话.

具体怎么切的见 [04](04-modular-design.md).
