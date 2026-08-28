# 注释只写 why, 设计说明放 skill

> 一段解释该写在代码注释里, 项目文档里, 还是这个 skill 里? 这篇给判据. 结论是: 代码里只
> 留很短的工程 why, 展开的设计说明放 skill —— 两边都不完整, 加起来完整, 而且**可以独立
> 删掉其中一边**.

## 一段话有三个可能的家

| 放哪 | 读者是谁 | 跟着成品出去吗 |
| :--- | :--- | :--- |
| 代码注释 / docstring | 以后维护这段代码的人 | **会**. 它就长在代码里 |
| `README.md` / `TICKET.md` / `docs/` | 学这门课的学生 | 不会, 交付前删掉 |
| `.claude/skills/` (就是你正在读的) | AI 和仓库维护者 | 不会, 交付前删掉 |

三个家的区别不是"写得深不深", 是**擦掉教学痕迹的时候它会怎样**. 后两个是 `rm -rf` 一个
目录; 第一个是打开文件逐行判断 —— 而那件事有风险, 会删漏, 而且改代码.

## 为什么架构说明住在 skill 里

这些文档讲的是"这个仓库为什么长成这样": 哪条边界破了会怎样, 哪个显而易见的写法踩过坑,
哪次事故换来了现在这个设计. 这类内容有两个性质决定了它的位置.

**一, 它的读者是维护者和 AI, 不是产品的读者.** 一个面试官打开成品仓库, 不需要读一篇讲
"我们为什么放弃了表名前缀"的复盘. 那是内部取舍记录, 露出去只会显得这个项目还在建设中.

**二, 它跟教学是连着的.** 这里面有大量"上一版是怎么错的"和"这条规矩是给下一个改这里的人
看的", 那本来就是课程内容的一部分, 不适合作为交付物公开.

所以它们整块住在 `.claude/skills/`. 交付时删掉这个目录, 成品仓库里就只剩代码和它自己的
简短 why —— 而且**一行代码都不用改**. 这是 [02](02-teaching-and-production.md) 那条边界在
文字这一侧的落法.

**反过来是单向的**: 这些文档可以随便引用代码路径, **代码不能引用这些文档的路径**. 一条
`见 .claude/skills/xxx/ref/...` 的指针在擦除之后既不报错也不失败, 只是变成一句死链躺在
成品里, 而且明白写着"这个项目是从一门课里长出来的".

## 代码里留什么

> **注释和 docstring 解释的是"为什么", 不是"怎么做". 而且通常很短.**

**教学内容一律不进代码.** 讲设计模式, 讲这门技术是什么, 讲一个新人需要的背景 —— 那些属于
教学层, 不属于 docstring.

这条规矩不是洁癖, 它换来的是三个同时成立的好处:

- 代码保留了 **why** —— 那是任何生产仓库都想要的东西, 而且是最容易失传的东西
- 代码没有冗长的 **how** —— 因为 how 就是代码本身, 写第二遍只会和代码漂移
- 教程可以放开讲 —— 不用担心把一个 40 行的 mixin 讲解塞进函数头

## 判断标准

写下一段注释之前, 问这两句:

**第一句: 一个已经懂这个模式的人, 还需要读这段话吗?**

- 需要 —— 因为这里有个坑 / 这里做了个反直觉的取舍 / 这个值是踩坑试出来的 -> 留在代码里
- 不需要 —— 因为这段话在讲"mixin 是什么"/"依赖注入的好处" -> 挪进教学层

**第二句: 如果我把 `docs/` 和 `README.md` 全删了, 这段注释会变得孤立或者莫名其妙吗?**

会 -> 说明它其实是教程的一部分, 现在就该挪走.

## 什么算 why

看这个仓库里真实的例子:

```python
# Three ways to pin `search_path`, and only the third one holds.
#
# The libpq start-up option (`options=-csearch_path=...`) is the obvious one.
# A pooled endpoint rejects the *connection*, not the query: Neon's `-pooler`
# host, and PgBouncer generally, answer with "unsupported startup parameter in
# options: search_path". It fails inside the driver before anything runs, so it
# surfaces as the app being unable to reach the database at all.
```

这段很长, 但它是合格的 why: 它解释的是**为什么不是那两种显而易见的写法**. 没有它, 下一个
人一定会把代码"简化"成第一种, 然后线上连不上数据库. 它保存的是一次事故的成本.

反过来, 下面这种就是应该挪走的:

```python
# This class uses the Mixin pattern. A mixin is a class that provides methods to
# other classes without being their parent in the usual sense. Python supports
# multiple inheritance, which means...
```

对已经懂的人是废话, 对不懂的人是教程 —— 而教程有更好的地方放, 那里还能配图、配练习、配
上下文.

**一条经验**: why 注释往往在讲**否定的东西** —— 为什么不用那个更明显的写法, 为什么这个
参数不能省, 为什么这里看起来多余的一步不能删. 如果一段注释通篇都在肯定地描述代码在做
什么, 它多半是 how.

## 长度

**通常很短**, 一到三行. 上面那段 `search_path` 是例外, 因为它替代的是一次生产事故的
调试过程 —— 那种密度的信息值得占篇幅.

判断方式不是数行数, 是问: **这段话里有多少内容是代码本身读不出来的?** 全是, 那多长都
值得; 一半是复述代码, 那就砍掉那一半.

## 不要复述代码

```python
# Loop over the tables and count the rows
for table in tables:
    counts[table] = count_rows(table)
```

这行注释的信息量是零, 而且它会先于代码腐烂 —— 循环改了, 注释不会跟着改.

## 语言

**注释、docstring、标识符一律英文**, 哪怕产生它的对话是中文的. 中文只出现在
`.claude/skills/*-cn/` 的文档和聊天里.

理由不是形式主义: 混合语言的注释对后来加入的人不可读, 而且**按关键词搜不到** —— 你没法
用一个英文词搜到一段中文注释, 反之亦然.

## 通用代码里不要用本数据集举例

这条和 [04](04-modular-design.md) 里那条是同一条, 但值得在注释规范里再说一次, 因为它
最常犯在注释里:

```python
# 不要: 把当前数据集焊进了通用代码
#   local SQLite     remote PostgreSQL
#   loan        ->   schema xxx 里的 loan

# 要: 永远虚构的占位领域
#   local SQLite     remote PostgreSQL
#   widget      ->   schema acme 里的 widget
```

`acme` / `widget` / `part` 不属于任何真实数据集, 所以永远不会过期. 用真表名的注释在换
数据集之后不报错、不失败, 只是变成一句谎话躺在那里.

## 教学层放什么

| 放哪 | 内容 |
| :--- | :--- |
| `README.md` / `README-cn.md` | 这一课教什么, 学完能做什么 |
| `TICKET.md` | 这一课的任务和验收清单 |
| `docs/tutorials/` | 分章节的教学正文 |
| `docs/dev-guide/` | 面向开发者的走读: 前端怎么组织, 后端怎么组织 |
| `.claude/skills/` | 给 AI 和维护者看的规范 (就是你正在读的这些) |

**设计模式的讲解属于 `docs/`.** 如果某个模式的存在理由是这个仓库特有的 (比如"为什么
`One` 用 mixin 而不是一堆独立模块"), 那么:

- 代码里留一行 why: 这个类为什么这样组织
- 教程里展开讲: mixin 是什么, 什么时候该用, 这里为什么合适

两边都不完整, 但两边加起来完整, 而且可以独立删除其中一边.
