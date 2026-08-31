# 从零把这个仓库跑起来

> `operations/` 讲的是**怎么让它跑**, 不讲代码为什么那么写 (那在 `backend/` 和
> `frontend/`). 这篇是顺序: 装依赖, 配密钥, 灌数据, 起服务, 四步, 缺一步都跑不起来.

**对应代码**: `mise.toml`, `.env.example`, `.env.defaults`, `pyproject.toml`,
`package.json`, `.agents/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py`

---

## 四步

1. **装依赖** —— `mise run inst`, 见 [04](04-dev-servers.md)
2. **配密钥** —— `cp .env.example .env`, 填 `DB_*` 和一个 LLM 凭据, 见 [02](02-configuration.md)
3. **灌数据** —— `gen-data` -> `sync-db` -> `verify-db`, 见 [03](03-the-database.md)
4. **起服务** —— `mise run dev`, 见 [04](04-dev-servers.md)

**第 2 步和第 3 步不能跳过, 而且顺序不能换.** 这个 app **在任何环境下都读同一个 PostgreSQL,
本地也一样** —— 没有本地 SQLite 兜底 (完整理由见
[architecture/05](../architecture/05-why-postgres-everywhere.md)). 所以没有 `DB_*` 就连不上,
而连上了一个没同步过的 schema 比连不上更糟: 空 schema 和不存在的 schema 在反射器看来一模
一样, agent 会以为这个库没有表, 然后凭空编出表名来回答.

---

## 索引

| 你要做什么 | 读 |
| :--- | :--- |
| 第一次跑起来 | 这一篇, 然后按顺序读 02 03 04 |
| 填 `.env`, 换 LLM provider, 打开配额 | [02-configuration.md](02-configuration.md) |
| 造数据集, 同步到 PostgreSQL, 换数据集之后重灌 | [03-the-database.md](03-the-database.md) |
| 起 / 停开发服务器, 跑测试, 搞清楚 mise 和 pnpm/uv 谁调谁 | [04-dev-servers.md](04-dev-servers.md) |

---

## 一句话: 命令都从 `mise` 走

`mise.toml` 同时管两件事: **钉住工具版本** (Python 3.12, Node 24, uv, pnpm) 和**定义任务**.
所以 `mise run <task>` 是唯一需要记的入口, 不用记 `uv` 和 `pnpm` 各自的写法.

**唯一的例外是造数据和同步数据库那三条**, 它们在 skill 自己的 `teaching_cli.py` 里, 不在
`mise.toml` 里. 那是刻意的: `mise.toml` 跑的是**应用**, 而造数据不是应用 —— 完整理由见
[architecture/02](../architecture/02-teaching-and-production.md).
