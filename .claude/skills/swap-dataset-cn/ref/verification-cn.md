# 验证清单和验证脚本

[SKILL.md](../SKILL.md) 说什么时候验, 这篇给怎么验. **每做完一步就验一次, 不要攒到最后**
—— 攒到最后的问题是, 一次报出十个错时你分不清哪个是根因, 哪个是连锁反应.

---

## 三条命令, 都要跑, 查的东西不重叠

```bash
mise run check      # 建表顺序 / 提示词表名 / 内容文件 / kickstart 渲染配额
mise run test       # check + Python 测试 + Node 测试
npx next build      # site.toml 的必填 key 和图标名, 只有这里查得到
```

**最常见的漏是只跑前两条.** 于是一个拼错的图标名安静地渲染成兜底图标, 卡片看着好好的, 就是
配错了图, 而且没有任何东西会说一句.

`mise run check` 的四项:

| 检查 | 拦住什么 |
| :--- | :--- |
| 建表顺序 | 种子的外键成环 (没有任何插入顺序能满足), 或者种子里一张表都没有 |
| 提示词表名 | 提示词 SQL 例子里 `FROM` / `JOIN` 了一张不存在的表 |
| 内容文件 | `data/` 下三个文件缺失或者只是个残桩 (少于 500 字符) |
| 渲染配额 | 12 条 kickstart 的 `render` 和它自己的措辞对不上, 或者四类不是各 3 条 |

`npx next build` 的两项都在 `lib/site/load.ts` 里, 都会 throw:

| 检查 | 拦住什么 |
| :--- | :--- |
| `REQUIRED_SITE_KEYS` | `site.toml` 少一个必填 key (报出 key 名) |
| `assertIconsExist` | `icon` 不在 `lib/icons.ts` 里 (报出坏名字和全部合法名字) |

---

## 数据体检: 空表 / 孤儿外键 / 日期越界

**对象是 `dataset/<name>.sqlite` 这个种子, 不是线上的 PostgreSQL.** 同步是逐行复制, 种子
干净则线上干净, 而 SQLite 的 `PRAGMA foreign_key_list` 拿孤儿行比写 PostgreSQL 的等价查询
省事得多. 顺序上**先体检再同步**, 别把脏数据发上去再回头查.

标准到这里为止: 不需要逐行对账, 不需要和源文档的统计量严格吻合. **能跑, 且没有一眼假的
结论**, 就算过 —— 违约率 0%, 某张表全是空的, 日期落在 1970 年, 金额是负数, 这些不行.

```bash
.venv/bin/python - <<'EOF'
import sqlite3, datetime
from agent_app.dataset import path_dataset_sqlite

path = path_dataset_sqlite()
db = sqlite3.connect(str(path))
db.row_factory = sqlite3.Row
tables = [r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

print(f"{path.name}: {len(tables)} tables\n")
issues = []
for t in tables:
    n = db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    if n == 0:
        issues.append(f"{t}: empty table")
    print(f"  {t:<28} {n:>9,} rows")

    # 外键指向一个不存在的父行
    for fk in db.execute(f'PRAGMA foreign_key_list("{t}")').fetchall():
        col, parent, pcol = fk["from"], fk["table"], fk["to"] or "id"
        orphans = db.execute(
            f'SELECT COUNT(*) FROM "{t}" c LEFT JOIN "{parent}" p ON c."{col}" = p."{pcol}" '
            f'WHERE c."{col}" IS NOT NULL AND p."{pcol}" IS NULL').fetchone()[0]
        if orphans:
            issues.append(f"{t}.{col} -> {parent}.{pcol}: {orphans} orphan rows")

    # 落在常识之外的日期
    for col in db.execute(f'PRAGMA table_info("{t}")').fetchall():
        if "date" not in col["name"].lower() and "DATE" not in col["type"].upper():
            continue
        lo, hi = db.execute(
            f'SELECT MIN("{col["name"]}"), MAX("{col["name"]}") FROM "{t}"').fetchone()
        if lo is None:
            continue
        for label, v in (("min", lo), ("max", hi)):
            try:
                y = datetime.date.fromisoformat(str(v)[:10]).year
            except ValueError:
                continue
            if not (1990 <= y <= 2035):
                issues.append(f"{t}.{col['name']} {label} = {str(v)[:10]}")

print()
print("FAIL " + "\nFAIL ".join(issues) if issues
      else "OK: no empty tables, no orphan FKs, dates all sane")
EOF
```

脚本查的是机械可判的那几样. 剩下**要靠眼睛看一遍**的, 是提示词里那几条核心指标算出来的
数字: 比率类落在这个行业说得过去的区间里 (不是 0%, 不是 80%), 分档之间的排序符合常识,
金额没有负数也没有比总资产还大的单笔.

有一条明显离谱, 说明数据集本身有问题, **回去找用户确认, 不要在提示词里绕过它**.

---

## 提示词里每一段 SQL 对着真库跑一遍

**必须走 `one.engine`, 也就是 PostgreSQL.** 拿本地 sqlite 验过的 SQL 在这里一条都不算数.

跑不通的 SQL 例子比没有例子更糟: 模型会照抄, 然后在用户面前失败. 这一步还会顺带暴露"语法
对但公式写错" —— 结果数字明显不对就能看出来.

```bash
.venv/bin/python - <<'EOF'
import re, pathlib, sqlalchemy as sa
from agent_app.api import one

blocks = re.findall(r"```sql\n(.*?)```",
                    pathlib.Path("data/system-prompt.md").read_text(encoding="utf-8"), re.S)
ok = fail = 0
for i, b in enumerate(blocks, 1):
    if not b.strip().upper().startswith(("SELECT", "WITH")):
        continue
    try:
        with one.engine.connect() as c:
            rows = c.execute(sa.text(b)).fetchall()
            c.rollback()
        ok += 1
        print(f"[{i}] OK   {len(rows)} rows | {rows[0] if rows else ''}"[:110])
    except Exception as e:
        fail += 1
        print(f"[{i}] FAIL {str(e).splitlines()[0][:130]}")
print(f"\n{ok} ok, {fail} fail")
EOF
```

---

## 体积预算

线上 Neon 是 500MB 配额, **和别的项目共用一个实例**, 我们只占一个 schema. 所以真实预算比
500MB 还小. 这条比任何一条内容质量的要求都硬: 内容写差了可以改, 数据塞不进去是直接上不了线.

**动手前估一次.** PostgreSQL 存同一份数据比 SQLite 大 (每行的元组头, 对齐填充, 索引和主键
约束), 约 1.5 倍; 宽表多, 索引多的数据集会更高. 拿 **乘 4** 当上界估还是稳的:

```bash
ls -lh dataset/*.sqlite
```

sqlite 超过 **120MB** 就在动手前跟用户确认要不要减行, 别等同步的时候才发现.

**同步之后量一次真实数字:**

```bash
.venv/bin/python - <<'EOF'
import sqlalchemy as sa
from agent_app.api import one

sql = sa.text('''
    SELECT pg_size_pretty(COALESCE(SUM(pg_total_relation_size(c.oid)), 0)) AS ours,
           COUNT(*) AS n_tables,
           pg_size_pretty(pg_database_size(current_database())) AS whole_db
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r' AND n.nspname = :schema
''')
with one.remote_postgres_engine.connect() as conn:
    r = conn.execute(sql, {"schema": one.config.schema_name}).one()
print(f"our {r.n_tables} tables: {r.ours}; whole db {r.whole_db} / 500 MB")
EOF
```

看的是两个数: 我们这个 schema 别失控, 整库别顶到线. 逼近了就回去减行, 通常是把最大那张
流水表按时间截一段, 而不是删表 —— 删表会让提示词里的分析失效.

---

## 旧领域词汇扫描

换完之后跑一次. 词表是命令行参数, **不提交进仓库**:

```bash
mise run check -- --retired "loan,lending,borrower,default_event,risk_grade"
```

填**上一个数据集最有辨识度的名词**. 挑词要挑准: 拿 `node` 这种通用词去扫, 报出来的全是
mermaid 文档里的正常用词, 你会学会忽略这个检查的输出.

它扫 `app/ components/ lib/ data/ types/ api/ agent_app/ scripts/ tests_python/ config/`
下的代码和配置, **不扫 `docs/` 和 `README`** —— 教学材料合法地讨论过去的数据集.

有残留它会精确报出文件和行号.

---

## 上一个数据集在 PostgreSQL 上的残表

它们住在**别的 schema 里**, 新的同步永远不会碰到, 所以会一直占着 Neon 的配额而不发出任何
声音. 而那个配额是和别的项目共用的.

先看有什么:

```bash
.venv/bin/python - <<'EOF'
import sqlalchemy as sa
from agent_app.api import one

sql = sa.text('''
    SELECT n.nspname AS schema,
           COUNT(*) AS n_tables,
           pg_size_pretty(SUM(pg_total_relation_size(c.oid))) AS size
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'r'
      AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    GROUP BY n.nspname
    ORDER BY SUM(pg_total_relation_size(c.oid)) DESC
''')
with one.remote_postgres_engine.connect() as conn:
    for r in conn.execute(sql):
        print(f"{r.schema:<45} {r.n_tables:>3} tables  {r.size}")
print(f"\nours is: {one.config.schema_name}")
EOF
```

**这个库是和别的项目共用的, 所以列出来的 schema 里多数不是我们的.** 只有上一个数据集那个
是可以删的, 而且**必须先把 schema 名报给用户, 等他明确说删, 再删**:

```bash
# 只在用户点名确认之后运行, 把 <old_schema> 换成他确认的那一个
.venv/bin/python -c "
import sqlalchemy as sa
from agent_app.api import one
with one.remote_postgres_engine.connect() as c:
    c.execute(sa.text('DROP SCHEMA \"<old_schema>\" CASCADE'))
    c.commit()
print('dropped')"
```

---

## 一个环境坑

`dataset/<name>.sqlite` 不进 git, 切分支不会跟着变, 新 clone 里根本不存在. 如果 `mise run
check` 报"数据库一张表都没有", 先造数据再说, 别急着改代码:

```bash
.venv/bin/python .claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py gen-data
```
