# 灌数据: 造种子, 同步到 PostgreSQL

> 三条命令: `gen-data` 造出本地 SQLite 种子, `sync-db` 把它发布进这个项目的 PostgreSQL
> schema, `verify-db` 逐表对行数. **新 clone 必须跑一遍**, 因为数据库文件不进 Git.

**对应代码**: `.agents/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py`,
`agent_app/dataset.py`, `dataset/`

**前置**: [02](02-configuration.md) 里的 `DB_*` 已经填好.

---

## 三条命令

```bash
CLI=.agents/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py

.venv/bin/python $CLI gen-data      # 装 dataset/requirements.txt, 跑生成器
.venv/bin/python $CLI sync-db       # 发布进 PostgreSQL 的 SCHEMA_NAME
.venv/bin/python $CLI verify-db     # 逐表对行数, 不一致就 exit 1
```

`gen-data` 在 `.sqlite` 已经存在时**什么都不做** —— 生成要几分钟, 而绝大多数时候它已经在
那儿了. 要重来加 `--force`, 它会先删光 `dataset/` 下所有 `.sqlite` 再造.

---

## 为什么它们不是 mise 任务

`mise.toml` 跑的是**应用** (装依赖, 起服务, 跑测试). 造数据和同步数据库都不是应用: agent
通过 `one.engine` 读 PostgreSQL, 数据怎么进去的不是它的事.

把它们放在解释它们的那个 skill 旁边, 教学层就是"删几个目录", 而不是"从共用配置里一行行挑
出来删". 完整论证见 [architecture/02](../architecture/02-teaching-and-production.md).

---

## 数据从哪来

```
dataset/04-<name>_data_generator-cn.py    数据集自带的生成器, 进 Git
        │  gen-data
        ▼
dataset/<name>.sqlite                     种子, 不进 Git
        │  sync-db
        ▼
PostgreSQL schema <SCHEMA_NAME>           agent 唯一读的地方
        │  verify-db
        ▼
逐表行数一致
```

**数据库文件不进 Git**: 它是二进制, 每次重新生成都是一次没人读得懂的 diff; 而且它是**可再
生的** —— 生成器是确定性的, 重跑拿到同样的行. 所以新 clone 要自己造一份.

`dataset/` 目录里装什么, 文件名为什么是 discover 出来的, 见
[architecture/03](../architecture/03-the-dataset.md).

---

## `sync-db` 不是可选步骤

不同步就等于没有数据库, 而且失败方式很阴: **空 schema 和不存在的 schema 在反射器看来一模
一样**, 于是 agent 拿到一份没有表的库结构, 然后凭空编出一些看起来合理的表名来回答, 而且
答得很自信.

代码里专门有一个检查挡这件事: schema 里缺表就抛异常, 并告诉你去跑同步.

同步是**幂等**的: 每次都先倒着 drop 本项目 schema 里的表再重建, 跑几次结果一样. 它**只碰
自己的 schema**, 共用实例上别的项目的表不会被动到.

---

## 换数据集之后

1. 换掉 `dataset/` 里那六个文件
2. 改 `.env.defaults` 的 `SCHEMA_NAME`
3. `gen-data --force` -> `sync-db` -> `verify-db`
4. 照着新的源文档重写 `data/` 下那三个文件
5. `mise run check-content` 和 `mise run build-web`

**记得清理上一个数据集留下的表.** 它们在别的 schema 里, 不会被新的同步碰到, 所以会一直
占着 Neon 的配额而不发出任何声音 —— 而那个配额是和别的项目共用的.

体积估算和方言清单见 [architecture/05](../architecture/05-why-postgres-everywhere.md).

---

## 手动跑 SQL

```bash
.venv/bin/python scripts/test_03_run_sql_locally_cli.py --sql "SELECT count(*) FROM loan"
.venv/bin/python scripts/test_04_print_database_schema.py    # agent 看到的那份库结构
.venv/bin/python scripts/test_05_connect_remote_database.py  # 只验连通性
```

`scripts/` 下的脚本是**按第一次搭建的顺序编号**的, 编号是流程位置不是优先级. 05-07 需要
`DB_*`; 11-15 是每家 LLM 供应商各一个的探活脚本, 用各家最底层的 SDK 调用, 用来在调试更上层
的东西之前先确认一把凭据真的有效.
