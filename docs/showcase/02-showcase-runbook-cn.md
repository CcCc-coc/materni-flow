# 换行业的 AI 数据分析脚手架 跑起来

> 这门课怎么跑起来: 开始之前要做什么 setup, 推进过程中会遇到哪些环境, 命令与操作步骤. 跑不起来先看这里.

## 1. 环境准备

前置要求取自 [mise.toml](../../mise.toml) 的 `[tools]`: Python 3.12, Node 24, 外加 uv, pnpm, ruff. 你不需要自己去装 Python 和 Node, mise 会按那张表准备好.

四门前置课的技能门槛在 [examples/03](../../examples/03-prerequisites/README-cn.md) 那份自检清单里, 十四条, 缺哪块补哪门.

首次 setup 只有三步, **一个账号都不用注册**:

1. `mise run inst`
2. `cp .env.example .env` —— **复制出来一个值都不填**
3. `mise run dev`

**两个就绪标记都出现才算起来了**, 它们来自两个不同的进程:

```text
Ready in                        Next.js
Application startup complete.   uvicorn
```

打开 `http://localhost:3000`, 首页能看能点就算过. **agent 页点下去一定报错, 那是预期结果**, 到第 13 篇才补上.

## 2. 推进中的操作

整体节奏: 多数 Task 是读 README 照着做, 没有额外操作. 只有下面几处要跳出常规.

**一条贯穿全程的纪律**: 凡是练习要改仓库里的文件, 先从基线开一个分支, 名字就用那一篇的目录名 ——

```bash
git switch -c NN-title 01-showcase
```

值得单独说的几步:

- 到 **examples/05** 时: `.env` 是从 `.env.example` 复制的, **一个真值都不填**. 里面的占位符是 `"..."`, 代码把这个值当未设置, 所以从模板抄过来忘了注释掉的那一行不会变成一个已设置但没用的变量
- 到 **examples/09 起**: 改完 `data/` 下的文件**必须重启开发服务器** (Ctrl+C 再 `mise run dev`). 那几个文件是构建时读进去的, 光刷新浏览器看不到变化. 改组件代码不用重启, 会热更新
- 到 **examples/09 起**: 改完文案要跑**两条**命令, 查的东西不重叠 —— `mise run cli-check-content` 读 `data/` 里的散文, `mise run build-web` 走前端加载器查必填 key 和图标名. 只跑前一条是最常见的漏
- 到 **examples/13** 时 (**整门课唯一一次真正的门槛**), 有四件外部操作:
  1. 在 OpenAI / Anthropic / Google 里挑一家注册, 拿一把 API key, 并**在控制台里给这个账号设一个 5 到 10 美元的消费上限**. 注意月费订阅 (ChatGPT Plus, Claude Pro) **不带 API 额度**, 那是另一条计费路
  2. 注册 Neon, 开一个 Postgres 项目, 从连接信息里取四个值填进 `.env`. 主机名**要用带 `-pooler` 的那个**
  3. 造数据和同步**不是 mise 任务**, 走教学层自己的 CLI:
     ```bash
     CLI=.claude/skills/about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py
     .venv/bin/python $CLI gen-data
     .venv/bin/python $CLI sync-db
     .venv/bin/python $CLI verify-db
     ```
  4. 改完 `.env` **必须重启**才算数: `mise run kill && mise run dev`
- 到 **examples/20 与 21** 时: 那八个 `.py` 脚本直接 `.venv/bin/python examples/NN-title/0X_xxx.py` 跑, 你手上有哪家的 key 就跑哪个, 一个也够
- 到 **examples/35** 时: 环境变量在云上分三层 —— `.env.defaults` 跟着 git 自动上去, **只有密钥要在 Vercel 网页上一条条手填**, 而 `~/.aws/credentials` 那种云上根本不存在. **填完再触发第一次部署**, 顺序反了要重来. 用 bedrock 的话本地**不要**设 `AWS_ACCESS_KEY_ID` 和 `AWS_SECRET_ACCESS_KEY`, boto3 读环境变量早于读家目录, 一个占位符就能遮蔽掉一个好好的本地 profile
- 到 **examples/36** 时: 这一篇**不教点哪个按钮**. 两个平台的界面半年一变, 正确的动作是把那一屏截图连同第 9 节那段提示词一起交给 AI, 让它一次带一步
- 到 **examples/37 与 38** 时: 这两篇是同一件事的两半, **在同一个分支上做完**. 阶段二开始之前先 `/clear`. 阶段一跑完会停在一道人工闸门上, 那一步只能你自己点开网站看

## 3. 常见卡点

| 症状 | 先查什么 |
| :--- | :--- |
| 报端口被占, 而且 kill 那一步退出码非零 | 有别的东西占着端口而脚本证明不了它是你的. `.venv/bin/python kill-dev-servers.py --dry-run` 看它认领了谁 |
| 页面能开, 但按钮点了没反应 | 后端那个进程没起来. 看终端里 uvicorn 那一路的输出 |
| 页面能开, agent 也答, 但答的不像你的数据 | 你的前端不在 3000 上, 转发接到了别人的后端 |
| 改了 `data/` 下的文件页面没变 | 那几个文件是构建时读的, 重启开发服务器 |
| agent 报凭据相关的错 | `.env` 里那把 key 和 `.env.defaults` 里的 `LLM_PROVIDER` 是不是同一家 |
| agent 说库里没有表 | `verify-db` 跑过吗, 绿的吗 |
| 什么都对但答案很怪 | 改完 `.env` 重启过吗 |

**排查的本质是把可能性切成两半**, 所以这两条命令要分开跑: `mise run cli-test-db-conn` 只回答连不连得上 (不查任何表), `verify-db` 回答数据到没到齐. 这两种失败在 agent 页上长得一模一样.

卡住了把三样东西一起给 AI, 一样都别少: 你在读哪一篇的**路径**, 你敲的那条**命令**, 以及**终端打出来的原文** (整段复制, 不要截图, 不要只说一句报错了). 粘贴之前先给连接串和 key 打码.
