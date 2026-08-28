# 后端代码为什么长这样

`agent_app/` 各模块的设计说明。**代码里的注释只留工程上的 why 且很短** (规矩见
[09-comments-and-docs.md](../architecture/09-comments-and-docs.md)), 模式讲解、格式规范、
历史包袱这些展开的内容在这里。

两边都不完整, 加起来完整, 而且可以独立删除其中一边。

| 篇 | 讲什么 | 对应代码 |
| :--- | :--- | :--- |
| [01-config.md](01-config.md) | Config Pattern, `.env` / `.env.defaults` 双层, 两个工厂, runtime 检测 | `config.py`, `runtime.py` |
| [02-paths-and-vocabulary.md](02-paths-and-vocabulary.md) | 路径为什么不进配置, 枚举和小工具放哪 | `paths.py`, `constants.py`, `utils.py` |
| [03-sql-execution.md](03-sql-execution.md) | 只读保证, 为什么不用关键词黑名单, Markdown 输出 | `sql_utils.py` |
| [04-schema-encoding.md](04-schema-encoding.md) | 三步流水线 + 紧凑格式的完整规范 | `db_schema/` |
| [05-dataset-pipeline.md](05-dataset-pipeline.md) | **教学层, 会被删掉**. 生成, discover, 同步 | `dataset.py` |
| [06-quota.md](06-quota.md) | 月度花费上限, partition key 为什么是三段 | `quota.py` |
| [07-ai-sdk-adapter.md](07-ai-sdk-adapter.md) | SSE 协议形状, header 为什么和 generator 同住 | `ai_sdk_adapter.py` |
| [08-agent-response.md](08-agent-response.md) | 最后一条消息不一定是答案, 三步为什么合成一个 | `agent_response.py`, `agent_debugger.py` |

**架构与设计决定** (什么该放哪一层, 换数据集不能破什么) 在隔壁 [`../architecture/`](../architecture/01-what-this-project-is.md),
不在这里。这里只回答"这段 Python 代码为什么这么写"。
