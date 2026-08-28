# 怎么让它跑起来

维护这个仓库的日常操作: 装依赖, 配置, 灌数据, 起服务. 这里**不讲代码为什么那么写** ——
那在 [`../backend/`](../backend/README.md) 和 [`../frontend/`](../frontend/README.md);
也不讲边界和设计决定 —— 那在 [`../architecture/`](../architecture/01-what-this-project-is.md).

---

## 索引

第一次跑起来: 按 [01](01-overview.md) 的四步走, 顺序不能换.

| 篇 | 讲什么 | 对应文件 |
| :--- | :--- | :--- |
| [01-overview.md](01-overview.md) | 四步的顺序, 以及为什么 2 和 3 跳不过去 | 全部 |
| [02-configuration.md](02-configuration.md) | `.env` / `.env.defaults` 怎么填, 三层优先级, 三个会咬人的地方 | `.env.example` `.env.defaults` |
| [03-the-database.md](03-the-database.md) | 造种子, 同步, 逐表核对, 换数据集之后重灌 | `teaching_cli.py` `dataset/` |
| [04-dev-servers.md](04-dev-servers.md) | mise 任务表, mise/pnpm/uv 谁调谁, 以及杀服务器为什么要一个脚本 | `mise.toml` `package.json` `kill-dev-servers.py` |

---

## 两条容易忘的

**一, 命令都从 `mise run` 走.** `mise.toml` 同时钉工具版本和定义任务, 所以不用分别记 `uv`
和 `pnpm` 的写法. `package.json` 里那几个同名 script 少了标记和先 kill 那一步, 别用 —— 见
[04](04-dev-servers.md).

**二, 造数据和同步数据库不在 `mise.toml` 里**, 它们在 skill 自己的 `scripts/teaching_cli.py`.
`mise.toml` 跑的是应用, 而这些不是应用 —— 见
[architecture/02](../architecture/02-teaching-and-production.md).
