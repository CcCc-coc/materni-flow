# 本地 SQLite 怎么同步到远程 PostgreSQL

对应代码: `agent_app/tests/db_sync.py`, `scripts/test_06_*.py`, `scripts/test_07_*.py`

命名空间为什么是 schema 而不是表名前缀, 见 [03-one-database-everywhere.md](../03-one-database-everywhere.md).

---

## 表名两边必须一样

```
本地 SQLite          远程 PostgreSQL
widget         ->    schema acme_widgets 里的 widget
part           ->    schema acme_widgets 里的 part
```

**表名一致是这里的全部设计目标.** 早先用表名前缀 (`acme_widget`), 它失败在: agent 读到的
schema 字符串取决于背后是哪个引擎, 于是提示词里每一段 SQL 例子在一个环境对、在另一个环境
错, 而且没有任何东西会报错。schema 把命名空间从表名上挪开, agent 看到的名字就再也不变了。

外键会被重新指向同一个 schema 内部, 所以目标库是自包含的, 永远不会伸手去够别的项目的表。

---

## 插入顺序是算出来的

`table_insert_order()` 就是 SQLAlchemy `metadata.sorted_tables` 的一层薄封装 —— 那本来就
是按反射到的外键做的拓扑排序。

- **插入**正着走, 一行的父记录已经存在
- **删除**倒着走, 不会在还有别的表引用它时删掉一张表

**曾经有一份手写的 `tableInsertOrder` 配置**, 外加一个把它和种子文件对比的检查。两个都删
了: 一份手抄的拓扑排序是一个可能抄错的值, 而那个检查唯一能抓到的就是有人抄错。从同步过程
本来就要反射的那份 metadata 上读出来, 值和检查一起消失。

而且那个检查比的是**集合不是顺序**, 所以它从来没验证过顺序对不对。

`mise run check` 现在验的是推导也修不了的东西: 外键成环 (没有任何插入顺序能满足), 或者
种子里一张表都没有。

---

## 同步的五步

1. 反射本地 SQLite 的结构
2. 按依赖顺序把每张表的数据读出来 —— **走反射出来的 `Table` 对象而不是裸 SQL 文本**, 这样
   类型处理器会跑, `DATE` 出来是 `datetime.date`, `BOOLEAN` 出来是真的 bool. 裸
   `SELECT *` 跳过这些处理器, 拿到的无类型值在写进有类型的远程列时会被拒
3. 确保 schema 存在, 然后倒着删掉本项目的表 (`CASCADE`, PostgreSQL 专用语法, 所以有个
   `is_postgres` 判断 —— 那个判断也让这个函数能用 SQLite 替身来测)
4. 同名重建
5. 正着插, 分批 (`INSERT_BATCH_SIZE`). 一次性发一张六位数的表有超出驱动参数上限的风险, 而且
   会把整张表缓冲在内存里; 一行一次往返在网络上又慢到不能用

**只碰自己那个 schema.** 别的项目住在别的 schema 里, 永远不会被删。

---

## 验证

`scripts/test_07_verify_remote_data.py` 逐表比对远程和本地的行数, 不一致就 exit 1。
同步"成功"和数据真的到齐是两件事。
