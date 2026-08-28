# 库结构怎么编码给 LLM 看

> 把 SQLAlchemy 反射出来的库结构压成一段紧凑字符串, 让 agent 花七成更少的 token 看懂这个
> 库. 三步单向流水线: 反射 -> 中间模型 -> 字符串.

**对应代码**: `agent_app/db_schema/` (`extractor.py` `model.py` `encoder.py` `api.py`)

**依赖**: `constants` (类型和约束的词汇表), `utils` (`match`) —— 都在 [01](01-leaves.md).
唯一的使用者是 [08](08-the-one-object.md) 的 `database_schema_str`.

---

## 三步, 单向

```
extractor.py    SQLAlchemy metadata  ->  model.py 的模型
model.py        中间表示
encoder.py      模型  ->  agent 看到的那段紧凑字符串
api.py          对外的再导出
```

没有反向流动. `extractor` 只碰 SQLAlchemy 对象, `encoder` 只做字符串拼接不碰数据库,
中间那层是纯 pydantic 模型.

**`model.py` 里每一个字段都有 encoder 这个读者.** 不要逐字段镜像 SQLAlchemy 的 `Column`
(`autoincrement`, `computed`, `identity`, `deferrable`, `onupdate` 那十几个): 抽取一个没人
编码的字段既费反射时间, 又像是给输出许了个不兑现的承诺. **加字段要和发出它的那行 encoder
代码一起加.**

---

## 紧凑格式规范

### 列

```
${列名}:${类型}${PK}${UQ}${NN}${IDX}${FK}
```

约束缩写:

| 记号 | 含义 |
| :--- | :--- |
| `*PK` | 主键 (蕴含唯一和有索引) |
| `*UQ` | 唯一约束 (蕴含有索引) |
| `*NN` | 非空 |
| `*IDX` | 有索引 |
| `*FK->表.列` | 外键指向 |

**冗余的会被省掉**: 主键不再标 `*NN` 和 `*IDX`, 唯一列不再标 `*IDX`. 一列可以有多个外键,
编码成 `*FK->A.x*FK->B.y`.

例子:

```
UserId:INT*PK
CategoryId:INT*NN*IDX*FK->Category.CategoryId
Email:STR*UQ*NN
Description:STR
```

`llm_type` 为空时 (词汇表里没有这个类型) 退回方言原始拼写, 比如 `geom:GEOMETRY`.

### 表 / 视图

```
Table Product(
  ProductId:INT*PK,
  ProductName:STR*NN,
  CategoryId:INT*NN*FK->Category.CategoryId,
  Price:DEC*NN,
)
```

开头那个词是 `TableTypeEnum`: `Table` / `View` / `MaterializedView`. **这个标签就是告诉
agent 哪些关系写不得. **

### schema 和库

```
postgresql Database acme_data(
  Schema acme(
    Table Customer(
      CustomerId:INT*PK,
      Email:STR*UQ*NN,
    )
    Table Order(
      OrderId:INT*PK,
      CustomerId:INT*NN*FK->Customer.CustomerId,
    )
  )
)
```

最外层那个 `postgresql` 是方言标签, **它是这一层唯一有信息量的东西** —— 决定 agent 写哪种
SQL. 库名直接用 schema 名, 不另配一个显示名: 只有一个 schema, 给它起第二个名字就是第二个
要同步维护的东西, 而且它就印在下一行旁边.

schema 名为空时 (SQLite 没有 schema) 显示成 `default`.

---

## 为什么是这个格式

- **省 token**: 比 SQL DDL 或 JSON 省大约七成. 这段字符串每次对话都要进上下文, 是常驻成本
- **贴近 LLM 见过的东西**: 结构像 `CREATE TABLE`, 模型不用现学
- **关系直接可见**: 外键把目标表和列写在行内, 不需要跨行拼
- **类型统一**: 各家方言的类型压成 `STR` / `INT` / `DEC` 这类通用类别

---

## 类型映射表

`extractor.py` 的 `SQLALCHEMY_TYPE_MAPPING` 用 `__visit_name__` 做 key, 而不是用类. 这样
一个泛型类型和它的方言拼法能映到同一条: `sa.String` 的 visit name 是 `"string"`,
`sa.VARCHAR` 是 `"VARCHAR"`, 对 agent 来说都是 `str`.

**它比 PostgreSQL 需要的宽, 这是故意的.** 反射返回什么取决于方言, 而同步过程还要反射
SQLite 种子, 所以 `BLOB` / `DATETIME` 这些条目有用. 缺 key 不是错误 ——
`sqlalchemy_type_to_llm_type` 会退回方言原始拼写 —— 所以这张表是压缩辅助, 不是白名单,
宽一点零成本.

---

## 只做到适配 PostgreSQL 就够

`DbTypeEnum` 只列有代码路径的两个引擎 (SQLite 种子, PostgreSQL 服务). **一份没实现的选项
菜单读起来像是支持, 而它不是** —— 加一项要和用它的代码路径一起加.

同一条判据还砍掉了另一类枚举: **不要给一个模型加"我是什么类型"的字段.** 每个模型静态地知道
自己是什么, 那个字段永远只装它所属的类已经蕴含的值, 于是它和一张把枚举翻译回类的表一起
成为纯开销. 这里只剩 `TableTypeEnum` 一个枚举, 三个成员, 而它是真的有信息量的 —— 那个标签
就是告诉 agent 哪些关系写不得的东西.
