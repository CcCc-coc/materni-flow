# 前端文案的写法规范

这一节管 `data/site.toml` 里每一个会显示给用户的字符串, 以及 `data/business-context.md`
的全文. **不管代码注释, 不管系统提示词** —— 那两样各有自己的规矩.

---

## 第一条: 不要用破折号

不要用 `—`, 也不要用 `--` 当停顿.

这是最容易暴露"AI 写的"的一个特征: 模型极其偏爱用破折号塞入补充说明, 一段话里出现三四次
是常态, 而人类文案很少这样写.

破折号出现的地方, 通常说明这句话本来就该断开. 三种改法, 按优先级:

| 原样 | 改成 |
| :--- | :--- |
| `... is underpriced — and because ...` | 断成两句. `... is underpriced. And because ...` |
| `Each is structural — a consequence of X — and ...` | 换成逗号从句. `Each one is structural, a consequence of X, and ...` |
| `"Interest — the main revenue line"` | 把补充说明挪进另一个字段. `title = "Interest"`, 解释放进 `tooltip` |

标题里非要分隔就用冒号: `"SMB Lending Lens: AI-Powered Fintech Analytics Agent"`.

写完自查一遍 (mermaid 的边语法和 HTML 注释天生带 `--`, 必须排除, 否则噪音大到没人看):

```bash
.venv/bin/python - <<'EOF'
import re, pathlib
bad = 0
for p in ("data/site.toml", "data/business-context.md"):
    text = pathlib.Path(p).read_text(encoding="utf-8")
    text = re.sub(r"```mermaid.*?```", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"(?m)^\s*#.*$", "", text)          # TOML 注释
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"—|(?<!\w)--(?!\w)", line):
            print(f"{p}:{i}: {line.strip()}")
            bad += 1
print("no dashes" if not bad else f"{bad} 处要改")
EOF
```

---

## 第二条: 叙述性语言, 简单格式

用完整的句子把事情讲清楚, 不要写成关键词罗列.

允许的格式只有三样: **加粗**, 标题, bullet. 不要表格, 不要嵌套列表, 不要 emoji, 不要行内
代码块 —— 行内代码是给开发者看的, 这里的读者不是开发者.

---

## 第三条: 一切文案都是英文

界面是英文的. 中文只出现在 `*-cn` 那些 skill 的文档和聊天里. 源文档给的是中文版也
一样, 产出必须是英文.

---

## 第四条: 陌生人读得完

`site.toml` 和 `business-context.md` 的读者是**一个没听说过这个行业的人**: 面试官, 招聘方,
任何点开链接的人.

- 内行缩写和黑话要用就**当场解释**
- **讲行业, 不讲雇主; 讲问题, 不讲项目.** 不出现实习, 公司名, 个人经历, 课程, 作业这类
  痕迹. 这和仓库"不放作者身份"是同一条规矩
- 页面元数据里没有 `author` / `creator`, 也不要加

---

## `capabilities[].tooltip`: 把概念名翻译成人话

首页那四张能力卡上写的是**概念名**. "Sponsor Exposure Audit" 对内行精确, 对其他所有人等于
没写. hover / 键盘聚焦 / 手机点按时弹出的这段 tooltip 就是用来补这一刀的.

写法:

- **两到三句白话.** 先定义这个词, 再说这个数为什么会动
- **解释里不能再有黑话.** 用一个内行词去解释另一个内行词, 正是这个字段存在的意义所反对的
  那件事
- 来源是源文档的术语表和关键指标公式, 但要**重写成口语**, 不要直接抄公式

四条要和 `[[capabilities]]` 一一对应, 也就是和四条业务主线一一对应.

---

## `business-context.md` 里的 mermaid: 最多一张

写成普通的 ` ```mermaid ` 围栏块, **整份说明里最多用一次**, 十个节点以内.

它留给"读者必须一次性装进脑子里的顺序或分支", 比如一条生命周期主线.

判断标准很简单: **如果这张图只是把上一句话又说了一遍, 那就删掉图, 留那句话.** 第二张图
一定是装饰.

渲染走 chat 页那同一个 Markdown 渲染器 (已做懒加载和 `securityLevel: "strict"`), 组件与
数据集无关, 不用改.

---

## 数字要现场数出来

`home.blurb` 里的表数和行数, 此刻从数据库数, **不要抄旧值, 不要估**. 这一句恰好摆在读者
判断"这个 demo 有多真"的位置, 而一个差着一倍的行数比不写更糟.

```bash
.venv/bin/python - <<'EOF'
import sqlite3
from agent_app.dataset import path_dataset_sqlite

db = sqlite3.connect(str(path_dataset_sqlite()))
tables = [r[0] for r in db.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
rows = sum(db.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables)
print(f"{len(tables)} tables, {rows:,} rows")
EOF
```

---

## HTML 注释可以放心写

`lib/site/load.ts` 在渲染前会把 `business-context.md` 里的 HTML 注释剥掉, 所以给下一个
作者的批注可以直接留在文件里, 不会打印到弹窗正文中.

`site.toml` 用 TOML 的 `#` 注释, 同理.
