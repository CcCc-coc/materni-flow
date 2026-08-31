# 后端代码为什么长这样

`agent_app/` 和 `api/index.py` 各模块的设计说明. **代码里的注释只留工程上的 why 且很短**
(规矩见 [09-comments-and-docs.md](../architecture/09-comments-and-docs.md)), 模式讲解,
格式规范, 历史包袱这些展开的内容在这里.

两边都不完整, 加起来完整, 而且可以独立删除其中一边.

---

## 编号就是依赖顺序

下面每一篇只用到它前面几篇讲过的东西. 从 01 往下读是一条不会有前向引用的路线; 只想改某一个
模块的话, 直接跳到那一篇.

```
        无依赖
  01  paths  constants  utils                              叶子
  03  sql_utils                                            叶子, 纯函数
  07  agent_response  (+ agent_debugger)                   叶子, 纯字符串
      │
  02  config          <- constants, paths, runtime
  04  db_schema/      <- constants, utils
  06  vercel_ai_sdk (叶子) + ai_sdk_adapter <- utils
      │
  05  quota           <- config, utils
      │
  08  one/            <- config, constants, paths, sql_utils, db_schema
      │
  09  api/index.py    <- 上面几乎所有 + one
      │
  11  dataset.py      <- paths, sql_utils, one     教学层, 会被删掉
```

`10` 是横切的测试策略, 不在这条链上.

---

## 索引

| 篇 | 讲什么 | 对应代码 |
| :--- | :--- | :--- |
| [01-leaves.md](01-leaves.md) | 路径为什么不进配置, 枚举和小工具放哪 | `paths.py` `constants.py` `utils.py` |
| [02-config.md](02-config.md) | Config Pattern, `.env` / `.env.defaults` 双层, 两个工厂, 校验为什么在 `__post_init__` | `config.py` `runtime.py` |
| [03-sql-execution.md](03-sql-execution.md) | 只读保证靠回滚不靠黑名单, 失败为什么返回文本 | `sql_utils.py` |
| [04-schema-encoding.md](04-schema-encoding.md) | 三步流水线 + 紧凑格式的完整规范 | `db_schema/` |
| [05-quota.md](05-quota.md) | 月度花费上限, partition key 为什么是三段 | `quota.py` |
| [06-frontend-protocol.md](06-frontend-protocol.md) | 请求体模型为什么 vendor 且宽松, SSE 协议形状 | `vendor/vercel_ai_sdk.py` `ai_sdk_adapter.py` |
| [07-agent-response.md](07-agent-response.md) | 最后一条消息不一定是答案, 三步为什么合成一个 | `agent_response.py` `agent_debugger.py` |
| [08-the-one-object.md](08-the-one-object.md) | **mixin 组装, 两个 engine, 四家 provider, 怎么加一个 tool** | `one/one_0*.py` `api.py` |
| [09-http-entry-point.md](09-http-entry-point.md) | **一次请求的九步, 和其中四个踩出来的决定** | `api/index.py` |
| [10-testing.md](10-testing.md) | **没有一个测试连网, `pragma: no cover` 的判据** | `tests_python/` `agent_app/tests/` |
| [11-dataset-pipeline.md](11-dataset-pipeline.md) | **教学层, 会被删掉**. 生成, discover, 同步 | `dataset.py` |

最常改的是 [08](08-the-one-object.md) —— 加 agent tool 在那里.

---

## 三条贯穿全部的规矩

**一, 纯函数拿 `engine` 当第一个参数, 不依赖类.** `sql_utils.py` 是模板. 这样它能被单测,
能被教学层复用, 也能在删掉 `one/` 之后独立存在.

**二, 依赖注入注的是具体那一个东西, 不是万能钥匙.** `quota.py` 收的是 `dynamodb_client`
而不是 `boto_ses`, 所以它够不到任何别的 AWS 服务.

**三, 通用代码里不出现本数据集的表名.** 注释和测试 fixture 一律用虚构领域
(`acme` / `widget` / `part`). 用真表名的东西在换数据集之后不报错, 只是变成一句谎话.

---

**架构与设计决定** (什么该放哪一层, 换数据集不能破什么) 在隔壁
[`../architecture/`](../architecture/01-what-this-project-is.md), 不在这里. 这里只回答
"这段 Python 代码为什么这么写".
