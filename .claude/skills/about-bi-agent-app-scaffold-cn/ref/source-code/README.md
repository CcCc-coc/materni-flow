# 代码为什么长这样

`agent_app/` 各模块的设计说明。**代码里的注释只留工程上的 why 且很短** (规矩见
[07-comments-explain-why.md](../07-comments-explain-why.md)), 模式讲解、格式规范、
历史包袱这些展开的内容在这里。

两边都不完整, 加起来完整, 而且可以独立删除其中一边。

| 篇 | 讲什么 | 对应代码 |
| :--- | :--- | :--- |
| [01-config.md](01-config.md) | Config Pattern, `.env` / `.env.defaults` 双层, 两个工厂, runtime 检测 | `config.py`, `runtime.py` |
| [02-paths-and-vocabulary.md](02-paths-and-vocabulary.md) | 路径为什么不进配置, 枚举和小工具放哪 | `paths.py`, `constants.py`, `utils.py` |
| [03-sql-execution.md](03-sql-execution.md) | 只读保证, 为什么不用关键词黑名单, Markdown 输出 | `sql_utils.py` |
| [04-schema-encoding.md](04-schema-encoding.md) | 三步流水线 + 紧凑格式的完整规范 | `db_schema/` |
| [05-database-sync.md](05-database-sync.md) | 表名一致, 插入顺序算而不配, 同步五步 | `tests/db_sync.py` |
| [06-quota.md](06-quota.md) | 月度花费上限, partition key 为什么是三段 | `quota.py` |

**边界规范** (什么该放哪一层, 换数据集不能破什么) 在上一级 `ref/` 的 01-08, 不在这里。
这里只回答"这段代码为什么这么写"。
