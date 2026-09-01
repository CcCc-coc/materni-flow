---
description: "这一篇不教新东西, 它是一道闸门. 它把这门课默认你已经会的四件事各指向一门前置课: 本地开发环境与 coding agent, 把网站送上线的 Vercel, SQLite 与 DBeaver, 以及云端 Postgres 与 Neon. 读完你能对着一份自检清单判断自己缺哪一块, 缺的先去补, 不缺的直接往下走."
---

# 开工之前的四门前置课

> 这一篇没有练习, 也不写代码. 它只回答一个问题: 往下走之前, 你手上该有哪些东西.

## 1. 概览

从下一篇开始你就要动手了: 装依赖, 起服务器, 连数据库, 灌数据, 部署上线. 这些动作背后
压着四块基础技能, 而这门课**不打算把它们再教一遍**.

不再教一遍不是省事, 是因为它们各自都值一门课的篇幅. 把注册 Neon, 装 DBeaver, 讲清楚
Vercel 的 Preview 和 Production 有什么区别这些内容塞进来, 这门课会被稀释成一本工具手册,
而它真正要讲的东西 (怎么造一个能反复换领域的 AI Agent 应用) 会被埋掉.

所以这一篇是一道闸门: 四块技能, 各对应一门独立的前置课. **会的直接跳过, 不会的现在去补.**
补完再回来, 后面每一篇都会顺很多.

---

## 2. 学习目标

跳过这一篇的代价是延迟发作的, 而且发作的时候看起来不像是缺前置知识.

举个真实的例子: 第 4 篇要你把 `DB_HOST` 填进 `.env`. 如果你没有一个云端 Postgres, 你会
卡在这个值到底从哪儿来. 这时候大多数人的反应是回头去读这门课的文档, 而这门课的文档里根本
不会有怎么注册一个 Neon 项目这一段, 因为那是另一门课的内容. 于是你会怀疑是教程写漏了.

同样的事会在后面反复发生: 数据灌进去之后想打开看看, 没有 DBeaver 就只能靠命令行一行行
`SELECT`; 部署到 Vercel 之后线上报错, 不知道 Build Log 和 Runtime Log 分别在哪, 就只能靠猜.

**先花十分钟对着自检清单过一遍, 比后面卡住再回头便宜得多.**

学完这个 Task, 你将能够:

1. 说出这门课默认你已经具备的四块技能, 以及每一块在后面哪几篇会被用到
2. 对着自检清单判断自己缺哪一块
3. 知道缺的那一块该去学哪门课, 以及那门课具体覆盖到什么程度

---

## 3. 这一篇的前置

只有两样, 而且几乎人人都有:

- 一台能上网的电脑. 没有 Mac 也行, 前置课里那条 GitHub Codespace 的路子一样走得通
- 一个 GitHub 账号

其余全部由下面四门课负责.

---

## 4. 四门课一览

| 前置课 | 教什么 | 这门课在哪里要用 |
| :--- | :--- | :--- |
| learn_dev_tools_basic_v1 | mise, Terminal, VS Code, GitHub Desktop, coding agent | 全程 |
| learn_sqlite_basic | 关系数据库, Python DB API, DBeaver, 多表 schema | 数据那一组 |
| learn_psql_in_neon_db_basic | 注册云端 Postgres, 拿连接信息, SQLAlchemy Core | 从第 4 篇开始一直到最后 |
| learn_vercel_basic_v1 | 部署, Preview 与 Production, 看日志 | 部署那一篇 |

四门课彼此独立, 顺序上只有一条约束: **先学 dev tools 那门**, 因为另外三门都要用到它装出来
的环境.

---

## 5. 一, 本地开发环境与 coding agent

**课程地址**: https://github.com/easyscale-academy/learn_dev_tools_basic_v1-project/tree/01-readup

它覆盖这些:

- 用 **mise** 统一管理开发工具的版本, 以及为什么它被叫做开发工具的万能遥控器
- Mac 上的三件套: VS Code, Terminal (或 Ghostty), GitHub Desktop
- 在 VS Code 里打开一个 repo, 用右键 Copy Path 拿到精确路径, 打开集成终端
- 把那个路径交给一个 coding agent, 让它准确改到你想改的文件
- **GitHub Codespace**: 没有 Mac 的时候, 整套环境在浏览器里也能跑

**这门课为什么最要紧**: 这个仓库所有命令都从 `mise run` 走. [`mise.toml`](../../mise.toml) 同时钉住工具版本
和定义任务, 所以你不需要分别去装 Python 3.12 和 Node 24, 也不需要记住 uv 和 pnpm 各自的
写法. 一个没装 mise 的人在第 4 篇的第一条命令上就走不动.

至于 coding agent, 它在这门课里不是一个可选的加速器. 后面有整整一篇讲怎么和 AI 一起改这个
仓库, 而那一篇默认你已经知道怎么让它读一个文件, 改一个文件, 跑一条命令.

---

## 6. 二, SQLite, DB API 与 DBeaver

**课程地址**: https://github.com/easyscale-academy/learn_sqlite_basic-project/tree/01-upskill

它覆盖这些:

- 关系数据库和 SQLite 是什么关系, 为什么一个 `.db` 文件就是一个完整的数据库
- Python **DB API** 这套统一接口规范, 以及 DB API 规范, driver, SDK 这三层各自的分工
- 写幂等的建表, 插入, 查询, 删库脚本, 查询结果拿到手是 `{列名: 值}` 形态的 dict
- **transaction 和 commit 到底在保护什么**, 不管是代码里调 `conn.commit()` 还是在 DBeaver
  里点一下 Save, 背后都是同一件事
- 装 **DBeaver**, 连上一个 SQLite 文件, 浏览表结构, 写 SQL, 像 Excel 一样编辑数据
- 设计一套带外键的多表 schema, 覆盖一对多和多对多两种关系, 并写 JOIN 查出来

**这门课在这里怎么用**: 这个仓库的数据集种子就是一个 SQLite 文件, 由 [`dataset/`](../../dataset) 下那个
生成器造出来. 后面你要打开它看里面有什么, DBeaver 就是那个工具. 幂等脚本的心智模型也会
直接用上: 这个仓库把种子同步到 PostgreSQL 的那个脚本, 每次都是先 drop 再重建, 跑几次结果
一样, 靠的正是同一个思路.

**transaction 那一节尤其值得学扎实.** 这个仓库的只读保证不是靠禁止关键词做到的, 而是靠
事务永远回滚: 一条溜过检查的写操作照样执行, 但它跑在一个没人提交的事务里, 落不到磁盘.
不理解 commit 在保护什么, 这个设计就只是一句口号.

---

## 7. 三, 云端 Postgres 与 Neon

**课程地址**: https://github.com/easyscale-academy/learn_psql_in_neon_db_basic-project/tree/01-upskill

它覆盖这些:

- 关系数据库, 网络数据库, Postgres 分别是什么, 三者不是一回事
- 注册一个免费的 **Neon** 账号, 建一个 Postgres 项目, 找到连接信息
- 用 SQLAlchemy Core 写幂等的建表, 插入, 查询, 清理脚本
- 用三种客户端连同一个数据库: Python 脚本, DBeaver, Neon 控制台自带的 SQL Editor
- 设计一套一对多加多对多的多表 schema, 插入上千条数据, 写跨表 JOIN

**这门课是四门里最硬的前置**, 因为这个仓库有一条不常见的设计:
**它在任何环境下都读同一个云端 PostgreSQL, 本地开发也一样**, 没有本地 SQLite 兜底.
理由第 20 篇会讲透, 一句话是查这个库的不是人而是模型, 而模型的 SQL 来自一份只能对着一种
方言写的提示词.

后果是: **没有一个 Neon 实例, 这门课从第 4 篇起就走不下去.** 那一篇要你把 `DB_HOST`,
`DB_USER`, `DB_PASS`, `DB_NAME` 填进 `.env`, 这四个值只能从你自己的 Neon 项目里拿.

免费额度完全够用. 前置课里那个实例可以直接接着用, 这个项目只占它的一个 schema, 和你之前
建的表互不干扰.

---

## 8. 四, 把网站送上线

**课程地址**: https://github.com/easyscale-academy/learn_vercel_basic_v1-project/tree/01-upskill

它覆盖这些:

- 一个网站上线到底难在哪, Vercel 把哪几层复杂度吃掉了
- 注册 Vercel, Hobby 免费计划给了多少额度, 超额会发生什么
- 用一个现成的 Template 几分钟部署上线, 拿到一个全世界都能打开的网址
- **Deployment 和 Environment 分别是什么**, Vercel 默认怎么根据 git branch 决定一次部署是
  Production 还是 Preview
- **Build Log 和 Runtime Log** 各自解决什么问题, 在哪里找, 各自保留多久

**这门课在这里怎么用**: 这个项目最后要部署到 Vercel, 而部署那一篇只讲这个项目特有的部分
(哪些密钥要在面板里手填, 为什么 `.env.defaults` 不用重录一遍, serverless 上 stdout 为什么
会把响应流搅坏), 不会回头讲 Vercel 本身怎么用.

日志那一节也别跳过. 线上和本地不一样的地方通常不会在本地复现, 而唯一的证据就在那两种日志
里. 知道去哪取证据, 和只会重试一遍, 是两种完全不同的排查能力.

---

## 9. 这门课在哪几处会用到它们

按顺序列一遍, 你可以据此决定先补哪一门:

| 从哪一篇开始要用 | 用到什么 | 出自 |
| :--- | :--- | :--- |
| 第 4 篇 把它跑起来 | mise, 命令行, VS Code | dev tools |
| 第 4 篇 把它跑起来 | 一个能连的 Neon Postgres, 以及它的连接信息 | Neon Postgres |
| 第 7 篇 和 AI 一起改仓库 | coding agent 的基本操作 | dev tools |
| 数据那一组 | SQLite 是什么, 怎么用 DBeaver 打开它看 | SQLite |
| 数据那一组 | 幂等脚本, transaction 和 commit | SQLite |
| 第 20 篇 种子到 PostgreSQL | Postgres 和 SQLite 的差别, schema 是什么 | Neon Postgres |
| 第 34 篇 部署到 Vercel | 部署, Preview 与 Production, 两种日志 | Vercel |

看得出来 dev tools 和 Neon Postgres 这两门最早被用到, 缺哪门就先补哪门.

---

## 10. 自检: 你缺哪一块

一条一条问自己, 判据是**你能不能现在就做出来**, 不是我好像见过. 有任何一条答不上来,
就去学那一门, 学完再回来.

**本地开发环境:**

- 你能在终端里敲出 `mise --version` 并拿到一个版本号吗
- 给你一个陌生 repo, 你能在 VS Code 里打开它, 找到某个文件, 复制出它的完整路径吗
- 你能在 VS Code 里打开集成终端, 并且知道它此刻的工作目录是哪儿吗
- 你能让一个 coding agent 读一个指定文件, 改一处, 然后跑一条命令验证吗

**数据库基础:**

- 你能说清 transaction 和 commit 在保护什么, 以及不 commit 会怎样吗
- 你装过 DBeaver, 并且用它连上过至少一个数据库吗
- 你能读懂一个带外键的多表 schema, 说出哪张表指向哪张表吗
- 你写过幂等脚本吗, 也就是跑第二遍不会出错也不会写重复数据的那种

**云端数据库:**

- 你有一个能用的 Neon 账号和一个 Postgres 项目吗
- 你知道从哪里拿到 host, user, password, database 这四个值吗
- 你能用 DBeaver 或者 Neon 网页控制台连上它, 跑一句 `SELECT 1` 吗

**部署:**

- 你有一个 Vercel 账号, 并且至少部署过一次东西吗
- 你能说清 Production 和 Preview 的区别, 以及是什么决定了一次部署属于哪一种吗
- 线上报错的时候, 你知道 Build Log 和 Runtime Log 分别去哪儿看吗

**没有及格线.** 这十四条不是考试, 是一张地图: 哪一块答不上来, 那一块就去补.

---

## 11. 回顾: 你现在站在哪

| 这门课默认你会 | 出自 | 缺了会在哪儿卡住 |
| :--- | :--- | :--- |
| mise, 终端, VS Code, coding agent | learn_dev_tools_basic_v1 | 第一条命令就敲不出去 |
| SQLite, DB API, transaction, DBeaver | learn_sqlite_basic | 看得见数据但打不开来看, 也读不懂只读保证 |
| 云端 Postgres, Neon 账号与连接信息 | learn_psql_in_neon_db_basic | `.env` 里那四个值填不出来, 整个应用连不上库 |
| Vercel 部署与两种日志 | learn_vercel_basic_v1 | 上不了线, 线上报错只能靠猜 |

---

## 12. 导师寄语

**为什么专门用一篇讲前置:**

一门课最容易劝退人的地方, 往往不是它教的东西太难, 而是它默认你会的东西你正好不会. 而这种
卡壳有个特点: 它不像我这段没看懂, 它像这个教程写漏了一步. 于是人会一遍遍回头翻文档,
找一个根本不在这里的答案.

把默认前提摊开写出来, 就是为了让这种卡壳当场变成一个明确的动作: 去学那门课, 学完回来.

**关键洞见:**

- 前置知识缺失的症状不是看不懂, 是觉得教程写漏了. 认出这个信号能省下大量时间
- 四门课里最硬的是云端 Postgres, 因为这个应用连本地开发都读远程库, 没有它寸步难行
- 补前置课不是绕路. 这门课后面每一篇都会更省力, 而且那四样技能本来就不只服务于这一个项目

**下一步:**

四块都齐了就往下走. 第 4 篇 ([把它跑起来](../04-get-it-running/README-cn.md)) 你会真的把这个项目在自己机器上跑起来.

---

## 13. 速查

**四门前置课:**

- 本地开发环境与 coding agent:
  https://github.com/easyscale-academy/learn_dev_tools_basic_v1-project/tree/01-readup
- SQLite, DB API 与 DBeaver:
  https://github.com/easyscale-academy/learn_sqlite_basic-project/tree/01-upskill
- 云端 Postgres 与 Neon:
  https://github.com/easyscale-academy/learn_psql_in_neon_db_basic-project/tree/01-upskill
- 部署与日志, Vercel:
  https://github.com/easyscale-academy/learn_vercel_basic_v1-project/tree/01-upskill

**建议顺序:**

先 dev tools, 再 Neon Postgres, 然后 SQLite 和 Vercel 随便哪个在前.

**最低限度:**

要开始第 4 篇, 你至少需要装好 mise, 加上一个能连的 Neon Postgres 实例.
