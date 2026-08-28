# 为什么本地开发也连生产的那个 PostgreSQL

> 造数据用 SQLite 最省事, 上云只能用 PostgreSQL. 这篇讲为什么本地开发**不**读那份现成的
> SQLite, 而是和生产读同一个 PostgreSQL —— 因为查这个库的不是人, 是模型.

## 两种数据库, 各有各的理由

**种子这一侧用 SQLite.** 数据集自带的生成器要把十来张表几十万行写进一个地方, SQLite 是
单文件, 不用起服务, 不用配账号, 跑完就是一个 `dataset/<name>.sqlite` 拷走就能用. 造数据
这件事上它没有对手.

**生产这一侧只能是 PostgreSQL.** 应用部署在 Vercel, 是无状态的函数, 本地文件系统里那个
`.sqlite` 根本不在那儿. 数据得住在一个连得上的托管库里, 这里用的是 Neon.

于是有一个看起来完全合理的做法, 而且这个仓库以前就是这么干的: **按运行环境自动选引擎**,
本地读 SQLite, 线上读 PostgreSQL. 本地不用连网, 线上用真库, 两边都舒服.

## 为什么这个做法在这里行不通

因为查这个数据库的**不是人, 是模型**, 而模型写 SQL 的依据是一份写死在仓库里的提示词.

`data/system-prompt.md` 里有十几段 SQL 例子, 它们是给模型照抄的模板. 这些例子是在本地写
的, 在本地验的 —— 于是它们全都是 SQLite 方言. 发到线上以后:

- `strftime('%Y-%m', d)` 不存在
- `JULIANDAY(a) - JULIANDAY(b)` 不存在
- `DATE(d, '-90 days')` 不存在
- `is_flag = 1` 报 `operator does not exist: boolean = integer`
- `ROUND(x, 2)` 在 `x` 是浮点列时报 `function round(double precision, integer) does not exist`

**而线上从来没崩过.** agent 的 SQL 工具把数据库报错转成字符串还给模型, 模型换个写法再试
或者干脆绕过去, 所以症状不是异常, 是**答案悄悄变差**. 没有任何监控会报这种事, 没有任何
测试会红.

改成两边都读 PostgreSQL 之后, 回头把旧提示词逐段跑了一遍: **16 段例子里 6 段跑不通.**
那 6 段在本地跑了几个月, 每次都绿.

换成一句话: **人可以在两套方言之间切换, 一份提示词不能.** 提示词只有一份, 它必须对着一个
确定的数据库写. 让本地和生产是同一个数据库, 是让这份提示词诚实的唯一办法.

**代价要认**: 本地开发现在需要 `DB_*` 环境变量, 而且第一次要跑一次同步才能工作. 这是一个
安装步骤, 换掉的是一个静默的错误答案. 这笔交易划算.

SQLite 没有消失, 它退回到它擅长的位置: **种子和同步源**, 不是任何人查询的对象. 数据怎么
从生成器走到 PostgreSQL, 见 [03](03-the-dataset.md).

## 命名空间用 schema, 不用表名前缀

线上是一个 Neon 实例, 多个项目共用. 隔离靠 PostgreSQL schema:

```
本地 SQLite 种子              远程 PostgreSQL
loan                  ->      schema <SCHEMA_NAME> 里的 loan
customer              ->      schema <SCHEMA_NAME> 里的 customer
```

**表名两边一模一样, 这是全部设计目标.**

早先的做法是给表加前缀 (`smbll_loan`). 它失败在同一个地方: agent 看到的表名取决于背后是
哪个引擎, 于是提示词里每一段 SQL 在一个环境对, 在另一个环境错. schema 把命名空间从表名上
移走了, 所以 agent 看到的名字永远不变.

schema 名在 `.env.defaults` 的 `SCHEMA_NAME`. 用数据集名, 下划线, 63 字符以内.
`Config` 加载时用 `SCHEMA_NAME_PATTERN` 校验, 写错当场报错. 配置本身见 [07](07-config-and-content.md).

## search_path 有三种钉法, 只有一种是对的

让 agent 写 `FROM loan` 而不用写 `FROM some_schema.loan`, 靠的是把 `search_path` 钉到我们
的 schema. 三种做法, 前两种都会在生产上咬人:

| 做法 | 结果 |
| :--- | :--- |
| libpq 启动参数 `options=-csearch_path=...` | **连不上**. Neon 的 `-pooler` 和 PgBouncer 一律拒绝: `unsupported startup parameter in options: search_path`. 在驱动层就失败, 表现为整个应用连不上数据库 |
| `connect` 事件上 `SET search_path` | **看起来能用, 不安全**. 事务池化下代理按事务分配服务端连接, SET 跑过的那条连接不一定是后续查询拿到的那条. 症状是"表突然消失" |
| 事务内 `SET LOCAL search_path` | **对**. 事务是代理保证留在同一条服务端连接上的单位 |

所以引擎是在 `begin` 事件上发 `SET LOCAL`. SQLAlchemy 在第一次 execute 时隐式开事务, 所以
schema 反射和 agent 的 SQL 工具都免费拿到.

## 体积预算

线上 Neon 是 500MB 配额, **和别的项目共用一个实例**, 我们只占一个 schema.

实测这个数据集: SQLite 种子 7.4MB -> PostgreSQL 11MB, 约 **1.5 倍**. 宽表多, 索引多的
数据集会更高.

动手前用 `sqlite 文件大小 x 4` 当上界估, 超过 120MB 就先和人确认要不要减行, 别等同步的
时候才发现. 同步之后量真实数字:

```sql
SELECT pg_size_pretty(SUM(pg_total_relation_size(c.oid)))
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND n.nspname = :schema
```

**换数据集之后记得清理上一个数据集留下的表.** 它们不会被新的同步碰到 (同步只管本 schema
里那些表), 会一直占着配额. 这个仓库真发生过: 前缀时代的 10 张
`smbll_*` 表在 `public` 里躺着占了 11MB, 整库 30MB 里有 11MB 是死数据.

## 写 SQL 时的方言清单

给模型的那份在 `data/system-prompt.md` 的 `## SQL Dialect` 一节. 人写代码时同样适用:

| 别写 (SQLite) | 写成 (PostgreSQL) |
| :--- | :--- |
| `strftime('%Y-%m', d)` | `TO_CHAR(d, 'YYYY-MM')` |
| 用 `strftime('%m', ...)` 算季度 | `EXTRACT(QUARTER FROM d)` |
| `DATE(d, '-90 days')` | `d - INTERVAL '90 days'` |
| `JULIANDAY(a) - JULIANDAY(b)` | `a - b` (日期相减直接得整数天) |
| `WHERE is_flag = 1` | `WHERE is_flag` |
| 浮点列上的 `ROUND(x, 2)` | `ROUND(x::numeric, 2)` |

最后一条最阴: `ROUND(numeric, int)` 存在而 `ROUND(double precision, int)` 不存在. 所以
`ROUND(100.0 * a / b, 2)` **没问题** —— `100.0` 这个字面量把整个表达式变成 numeric ——
而 `ROUND(some_float_column * 1.0, 2)` 会炸. 表达式里混进浮点列就加 `::numeric`.

另外 PostgreSQL 比 SQLite 严的两处: `GROUP BY` 要列全 SELECT 里所有非聚合列; `HAVING`
不认 SELECT 里的别名.
