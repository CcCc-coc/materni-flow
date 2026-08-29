# 数据集是怎么进到数据库里的

> **这个模块是要被删掉的.** 它把数据集的生成器跑出来的 SQLite 种子发布进 PostgreSQL,
> 属于教学层, 生产路径一行都不 import 它 —— 所以它排在最后.

**对应代码**: `agent_app/dataset.py`, `scripts/test_06_*.py`, `scripts/test_07_*.py`

**依赖**: `paths` ([01](01-leaves.md)), `sql_utils` ([03](03-sql-execution.md)),
`one.api` ([08](08-the-one-object.md)) —— 依赖最多的一个, 而且方向是单向的: 没有任何
生产模块反过来依赖它.

命名空间为什么是 schema 而不是表名前缀, 见 [05-why-postgres-everywhere.md](../architecture/05-why-postgres-everywhere.md).

---

## 这个模块是要被删掉的

```
dataset/04-*_data_generator*.py   →   dataset/<name>.sqlite   →   PostgreSQL schema
        (进 Git, 课程产物)              (不进 Git, discover)         (agent 唯一读的)
      teaching_cli gen-data            teaching_cli sync-db
```

入口是 `.claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py`, **不在
`mise.toml` 里**: mise 跑的是应用, 而这些都不是应用. 放在解释它们的那个 skill 旁边, 教学层
就是"删几个目录", 而不是"从共用配置里挑行删".

CLI 只做参数解析, 干活的都在 `agent_app/dataset.py`; `sync-db` / `verify-db` 直接复用
`scripts/` 下那两个编号脚本的 `main()` —— **同一个行为两个入口可以, 两份实现不行**.

## 默认不重建

`generate_dataset()` 在数据库已经存在时**什么都不做**: 生成要几分钟, 而绝大多数时候它已经
在那儿了. `--force` 是"我真的要重来"的说法.

`--force` 还会**先删光 `dataset/` 下所有 `.sqlite`**. 这不是顺手打扫: 上一个数据集留下的
文件会让 discovery 拒绝在两个文件之间选, 于是一次刚刚成功的重建看起来是坏的.

**生产路径一行都不 import `agent_app/dataset.py`.** agent 通过 `one.engine` 读 PostgreSQL,
数据怎么进去的不是它的事. 删掉这个文件和顶层 `dataset/`, 剩下的仍然是一个能跑的 app ——
前提是它指向的数据库已经灌好了. **教学层里没有任何 mise 任务**, 这也是刻意的: 造数据和
同步的入口在 skill 自己的 `teaching_cli.py` 里, 见 [architecture/02](../architecture/02-teaching-and-production.md).

`dataset/requirements.txt` 和 `pyproject.toml` 分开也是这个原因: 生成器的依赖不是 app 的
依赖, 一起删才干净. 有测试 (`TestNotOnTheProductionPath`) 用 AST 扫 `agent_app/one/` 和
`ai_sdk_adapter.py`, 确保没人偷偷 import 进来.

## 为什么中间没有工作副本

同步直接读 `dataset/` 下那个种子, 中间**不复制一份工作副本**. 复制一份的理由通常是"保护
种子不被改坏", 但这里的种子既不进 Git 也不金贵: 重建是一条命令, 而且生成器是**确定性的**
—— 重跑拿到的是同样的行 (111,153 行, 2231 笔贷款). **一层没有理由的间接就是一层要维护的
东西**, 而且它会让"我在看的是哪一份数据"多一个答案.

## 两个文件名都是 discover 出来的

`.sqlite` 和 generator `.py` 都用 `DIR_DATASET.glob(...)` 找, 因为**文件名属于数据集**.
零个和多个都抛异常, 绝不静默挑一个.

`local_sqlite_engine()` 是函数不是属性, 而且**不在 `DbMixin` 上**. 只有同步和教学脚本用
它, 生产路径从不碰 —— 把它挂在 `DbMixin` 上就意味着删掉教学层会把 `one/` 一起弄坏.

## 表名两边必须一样

```
本地 SQLite          远程 PostgreSQL
widget         ->    schema acme_widgets 里的 widget
part           ->    schema acme_widgets 里的 part
```

**表名一致是这里的全部设计目标.** 隔离靠 PostgreSQL schema, **不要用表名前缀**
(`acme_widget` 那种): 加了前缀, agent 读到的表名就取决于背后是哪个引擎, 于是提示词里每一段
SQL 例子在一个环境对在另一个环境错, 而且没有任何东西会报错. schema 把命名空间从表名上挪开,
agent 看到的名字就再也不变.

外键会被重新指向同一个 schema 内部, 所以目标库是自包含的, 永远不会伸手去够别的项目的表.

---

## 插入顺序是算出来的

`table_insert_order()` 就是 SQLAlchemy `metadata.sorted_tables` 的一层薄封装 —— 那本来就
是按反射到的外键做的拓扑排序.

- **插入**正着走, 一行的父记录已经存在
- **删除**倒着走, 不会在还有别的表引用它时删掉一张表

**不要把插入顺序写成配置.** 一份手抄的拓扑排序是一个可能抄错的值, 而为了防止抄错又要加一个
把它和种子对比的检查 —— 于是一个能算出来的东西变成了两样要维护的东西. 从同步本来就要反射的
那份 metadata 上读, 值和检查一起消失.

`mise run check-content` 里留下的是推导**修不了**的那个问题: 外键成环, 或者种子里一张表都没有.

`mise run check-content` 现在验的是推导也修不了的东西: 外键成环 (没有任何插入顺序能满足), 或者
种子里一张表都没有.

---

## 动手之前先确认引擎是对的

```python
require_dialect(local_engine, "sqlite", "local")
require_dialect(remote_engine, "postgresql", "remote")
```

**两个断言都在任何 I/O 之前**, 因为第三步会 `DROP TABLE`. 把两个 engine 传反的代价是删掉
本来要读的那一份.

**不要用一个 `is_postgres` 布尔量去挑代码路径.** 那样传错引擎不会报错, 只会换一条不太一样
的路径悄悄跑下去. 函数叫 `sync_sqlite_to_postgres`, 它就该在拿到别的东西时当场拒绝, 而不是
尽力而为.

报错信息里直接说明参数顺序和"它一上来就 drop 目标库的表", 因为这是唯一能救回来的时机.

---

## 同步的五步

1. 反射本地 SQLite 的结构
2. 按依赖顺序把每张表的数据读出来 —— **走反射出来的 `Table` 对象而不是裸 SQL 文本**, 这样
   类型处理器会跑, `DATE` 出来是 `datetime.date`, `BOOLEAN` 出来是真的 bool. 裸
   `SELECT *` 跳过这些处理器, 拿到的无类型值在写进有类型的远程列时会被拒
3. 确保 schema 存在, 然后倒着删掉本项目的表 (`CASCADE` + `CreateSchema`, 都是 PostgreSQL
   专用语法)
4. 同名重建
5. 正着插, 分批 (`INSERT_BATCH_SIZE`). 一次性发一张六位数的表有超出驱动参数上限的风险, 而且
   会把整张表缓冲在内存里; 一行一次往返在网络上又慢到不能用

**只碰自己那个 schema.** 别的项目住在别的 schema 里, 永远不会被删.

---

## 验证

`scripts/test_07_verify_remote_data.py` 逐表比对远程和本地的行数, 不一致就 exit 1.
同步"成功"和数据真的到齐是两件事.
