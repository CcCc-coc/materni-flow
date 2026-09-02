# dataset: 领域数据从哪来

> `dataset/` 是一个数据集的**全部源材料**: 四份领域文档, 一个造数据的生成器, 和生成器
> 自己的依赖. 这篇讲这个目录装什么, 为什么它的产物不进 Git, 以及它和 `data/` 的分工.

## 一个"数据集"包含什么

换一个业务领域, 换掉的不只是几张表. 换掉的是一整套互相咬合的东西:

```
dataset/
├── 00-<name>_summary-cn.md            这个领域一页纸讲清楚
├── 01-<name>_business_context-cn.md   这门生意怎么运转, 钱在哪漏
├── 02-<name>_er_document-cn.md        完整的表结构和外键关系
├── 03-<name>_sql_queries-cn.md        20 条业务分析查询, 带业务解读
├── 04-<name>_data_generator-cn.py     照着上面这些造一份假数据
├── requirements.txt                   生成器要装的东西
│
├── <name>.sqlite                      ← 生成器的产物, 不进 Git
└── data/*.tsv                         ← 中间产物, 不进 Git
```

前六个进 Git, 后两个被 `dataset/.gitignore` 排除.

**这四份文档是原料, 不是成品.** `data/` 下面那三个文件 (`system-prompt.md`,
`business-context.md`, `site.toml`) 是从它们**提炼**出来的 —— 提炼的规则在
[07](07-config-and-content.md), 提炼的顺序在 `swap-dataset-cn` skill. 换数据集时先换
`dataset/`, 再照着它重写 `data/`.

## 为什么产物不进 Git

数据库文件 7.7 MB, 是二进制. 进了 Git 之后, 每一次重新生成都是一次没人读得懂的 diff,
而仓库体积一去不回.

更根本的理由是**它是可再生的**: 生成器是确定性的, 同一份代码跑两遍拿到同样的行数和同样
的数据 (实测两次都是 111,153 行 / 2231 笔贷款). 一个能用一条命令重建的东西不值得进版本控制.

代价是新 clone 打不开就用, 得先造一份:

```bash
.venv/bin/python .claude/skills/about-ba-agent-app-scaffold-cn/scripts/teaching_cli.py gen-data
```

这条命令做两件事: 把 `dataset/requirements.txt` 装进 `.venv`, 然后用 `.venv/bin/python`
跑生成器. 默认**已经有 `.sqlite` 就不重跑**, 要重造加 `--force`.

## 生成器不是我们的代码

`04-*_data_generator-cn.py` 属于数据集, 不属于脚手架. 我们不改它, 只跑它. 所以:

- 它的依赖单独放在 `dataset/requirements.txt`, 不进 `pyproject.toml` (理由见
  [02](02-teaching-and-production.md))
- 它的文件名带着数据集的名字, 所以代码里**不能写死**

`agent_app/dataset.py` 用 **discovery** 找它和它的产物 —— `dir_dataset.glob("*.sqlite")`,
`glob("*_data_generator*.py")` —— 而不是配置文件名. 文件名属于数据集, 写死它就等于让换
数据集要去改 `agent_app/`, 而那正是这个包承诺不需要的事.

**找到零个和找到多个都报错**, 而且错误信息里带着修复办法. 绝不静默挑一个: 静默挑一个正是
"跑起来了, 但服务的是上一个数据集"这类 bug 的来源.

## 从生成器到 agent 能读的地方

```
生成器  ──gen-data──>  dataset/<name>.sqlite        种子, 本地, 不进 Git
                              │
                        ──sync-db──>  PostgreSQL schema <SCHEMA_NAME>
                              │                      ↑ agent 唯一读的地方
                        ──verify-db──>  逐表对行数
```

**SQLite 只是种子和同步源, 不是任何人查询的对象.** agent 在任何环境下读的都是 PostgreSQL,
本地也一样 —— 理由是 [05](05-why-postgres-everywhere.md) 一整篇.

**`sync-db` 不是可选步骤.** 不同步就等于没有数据库, 而且失败方式很阴: agent 的 schema 工具
会反射到一个空 schema, 而**空 schema 和不存在的 schema 在反射器看来一模一样** —— agent 会
以为这个库没有表, 然后凭空编出一些看起来合理的表名来回答. 所以代码里专门有一个检查, 缺表
就抛异常并告诉你去跑 `sync-db`.

同步是幂等的: 每次都先 drop 本项目 schema 里的表再重建, 跑几次结果一样. 它**只碰自己的
schema**, 共用实例上别的项目的表不会被动到.

## 中间没有工作副本

同步直接读 `dataset/` 下那个种子, **不在 `tmp/` 里复制一份工作副本**. 复制一份的理由通常是
"保护种子不被改坏", 但这里的种子既不进 Git 也不金贵: 重建是一条命令, 结果确定.

一层没有理由的间接就是一层要维护的东西, 而且它让"我在看的是哪一份数据"多出一个答案.

## 换数据集时这个目录整个换掉

新数据集来的时候, `dataset/` 里六个文件全部替换, 然后:

1. 跑 `gen-data` 造出新的 `.sqlite`
2. 改 `.env.defaults` 的 `SCHEMA_NAME` (见 [07](07-config-and-content.md))
3. 跑 `sync-db` 和 `verify-db`
4. 照着新的源文档重写 `data/` 下那三个文件

`agent_app/` 一行不动. 这是 [04](04-modular-design.md) 那句承诺在数据这一侧的兑现.
