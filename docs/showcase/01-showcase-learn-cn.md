# 换行业的 AI 数据分析脚手架 学习索引

> 这门课要学的东西有哪些, 分别在哪, 按什么顺序过. showcase-learn-cn skill 就是按这份索引带着你往前走的.

## 1. 学习素材

这门课属于**情况 B**: 真正要学的东西是这个仓库里那个跑得起来的应用本身, `examples/` 只是带你一步步走一遍它. 所以这一节是主菜.

**后端, 按依赖顺序从下往上读 (文件名的编号就是依赖方向, 箭头只从大指向小):**

- [agent_app/paths.py](../../agent_app/paths.py), [constants.py](../../agent_app/constants.py), [utils.py](../../agent_app/utils.py): 零依赖的叶子, 路径集中一处, 共用名词表, 两个小工具 (`debug` 走 stderr 不走 stdout, 理由见第 35 篇)
- [agent_app/sql_utils.py](../../agent_app/sql_utils.py): 跑 SQL 的纯函数, 连接当第一个参数. 只读靠事务永远回滚, 不靠关键词黑名单 (第 24 篇)
- [agent_app/agent_response.py](../../agent_app/agent_response.py): 从模型交回的一串消息里挖出思考和答案. 那句"去掉思考之后还剩东西才记成答案"的判断是全篇重点 (第 26 篇)
- [agent_app/config.py](../../agent_app/config.py), [runtime.py](../../agent_app/runtime.py): 三层优先级靠 `load_dotenv` 不覆盖已设变量这一个性质实现; 校验放在 `__post_init__` 而不是工厂里 (第 30 篇)
- [agent_app/db_schema/](../../agent_app/db_schema): 反射, 建模, 编码三步单向. `encoder.py` 完全不碰数据库, 所以测它不需要数据库 (第 22 篇)
- [agent_app/ai_sdk_adapter.py](../../agent_app/ai_sdk_adapter.py) 与 [vendor/vercel_ai_sdk.py](../../agent_app/vendor/vercel_ai_sdk.py): 唯一同时懂前端格式和模型格式的翻译官. 请求体模型故意宽松, 判据是对读的东西严格对不读的东西宽容 (第 17 篇)
- [agent_app/quota.py](../../agent_app/quota.py): 月度花费上限. 开关住在模块内部而不是调用方; 计量出故障要放行, 但超限那个异常必须抛出去 (第 33 篇)
- [agent_app/one/](../../agent_app/one): 四个 mixin 拼成的唯一组装点, 每样东西用到才建. [one_00_main.py](../../agent_app/one/one_00_main.py) 真正的代码只有两行 (第 29 篇)
- [api/index.py](../../api/index.py): 后端唯一对外的门, 162 行, **自己不做任何业务**. 那条路上六个决定换个写法都会静默出错 (第 28 篇)

**前端:**

- [app/](../../app): 路由与三层壳. 带括号的目录不进网址, 下划线开头的不当路由 (第 8 篇)
- [components/](../../components): 界面积木. 重点是 [chat/markdown.tsx](../../components/chat/markdown.tsx) 那个分发点和 [chat/blocks/](../../components/chat/blocks) 那张查找表 —— 解析失败是正常路径不是异常 (第 12 篇)
- [lib/site/load.ts](../../lib/site/load.ts) 与 [lib/icons.ts](../../lib/icons.ts): 读盘加两个构建期检查. TOML 换掉 TypeScript 之后, 编译器丢掉的东西是在这里补回来的 (第 9 篇)
- [hooks/use-scroll-to-bottom.tsx](../../hooks/use-scroll-to-bottom.tsx): 对话自动滚动, [components/chat/chat.tsx](../../components/chat/chat.tsx) 在用它

**内容与数据 (换一个行业, 改的就是这些):**

- [data/system-prompt.md](../../data/system-prompt.md): agent 的领域大脑, 五百多行, 每次请求全量重发. **散文没有编译器**, 里面的数字没有任何检查看着 (第 25 篇)
- [data/site.toml](../../data/site.toml): 界面上说的每一句话, 含四张能力卡与 12 条 kickstart
- [data/business-context.md](../../data/business-context.md): 首页那个长说明的正文
- [dataset/](../../dataset): 五份源文档加生成器. **数据库是跑出来的, 不进 Git** (第 14 篇)

**测试与检查:**

- [tests_python/](../../tests_python): 269 个用例, 一个都不联网. 三类外部依赖三种换法 (第 31 篇)
- [tests_python/test_dataset.py](../../tests_python/test_dataset.py) 末尾那条用 AST 扫 import 的测试: 一条能被机械判断的架构约束, 值得写成测试而不是文档 (第 7 篇)
- [agent_app/content_check.py](../../agent_app/content_check.py): 四项内容检查. 判不了的时候用顺序代替检查 (第 32 篇)
- [tests_node/](../../tests_node)

**配置:**

- [mise.toml](../../mise.toml): 工具版本加全部任务. 怎么跑见 [02-showcase-runbook-cn.md](02-showcase-runbook-cn.md)
- [.env.defaults](../../.env.defaults) 与 [.env.example](../../.env.example): 按**是不是密钥**切, 不按环境切 (第 5 篇, 第 30 篇)
- [next.config.js](../../next.config.js): 那条把 `/api/*` 转发到 8000 的 rewrite, **只在开发环境生效** (第 16 篇)
- [vercel.json](../../vercel.json), [tsconfig.json](../../tsconfig.json), [tailwind.config.ts](../../tailwind.config.ts), [postcss.config.mjs](../../postcss.config.mjs), [.coveragerc](../../.coveragerc)
- [kill-dev-servers.py](../../kill-dev-servers.py): 只杀本 checkout 的进程, 靠三种证据证明归属 (第 16 篇)

**给 AI 读的项目文档 (32 篇, 不是给终端用户的):**

- [.claude/skills/about-bi-agent-app-scaffold-cn/ref/](../../.claude/skills/about-bi-agent-app-scaffold-cn/ref): `architecture/` 9 篇讲边界与设计决定, `backend/` 11 篇讲每个 Python 模块, `frontend/` 8 篇讲界面每一层, `operations/` 4 篇讲怎么跑起来
- 换数据集那三条: [swap-dataset-cn](../../.claude/skills/swap-dataset-cn) 是索引与路由, [run-swap-dataset-phase-1-cn](../../.claude/skills/run-swap-dataset-phase-1-cn) 换内容, [run-swap-dataset-phase-2-cn](../../.claude/skills/run-swap-dataset-phase-2-cn) 换视觉
- [frontend-design](../../.claude/skills/frontend-design): 阶段二配色与排版靠它, 没加载会拿到一个长得像所有 AI 生成页面的东西

## 2. 引导路径

`examples/` 下 43 个 Task 是一条渐进序列, 而且它有一个刻意的节奏: **做一次, 懂一层, 再做一次, 再懂几层**. 账号和花钱的门槛只有一处, 在第四段.

整条线分成九段:

- **这门课是什么**: examples/02 到 03, 定位与四门前置课的闸门 (覆盖学习素材: 无, 这一段不碰代码)
- **先让它在你机器上亮起来**: examples/04 到 05, 和 AI 一起改仓库的方法, 然后装依赖起服务 (覆盖: mise.toml, .env.example, 那三套给 AI 的东西)
- **读懂你看得见的那一半**: examples/06 到 12, 全仓库地图, 教学层边界, 路由, 文案, 首页, agent 页, 块渲染. **这七篇一个账号都不需要** (覆盖: app/, components/, lib/, hooks/, data/site.toml, lib/site/load.ts)
- **接上真数据和真模型**: examples/13, 整门课唯一一次真正的门槛 (覆盖: .env, dataset/, 那三条教学层命令)
- **一次提问在系统里怎么流动**: examples/14 到 17, 保持在高处看 (覆盖: dataset/, agent_app/dataset.py, next.config.js, ai_sdk_adapter.py, vendor/)
- **agent 到底在干什么**: examples/18 到 28, 最长的一段, 按数据链路排 (覆盖: db_schema/, sql_utils.py, agent_response.py, one/one_04_agent.py, data/system-prompt.md, api/index.py)
- **这些代码为什么这么组织**: examples/29 到 34, 讲的全是不这么做会静默地坏在哪里 (覆盖: one/, config.py, tests_python/, content_check.py, quota.py, 渲染契约那三半)
- **把它送上线, 挂上你自己的域名**: examples/35 到 36 (覆盖: vercel.json, .vercelignore, utils.py 那个 `debug`)
- **换一个行业, 和它背后的打法**: examples/37 到 40, 这门课的落点 (覆盖: 换数据集那三个 skill, dataset-for-swap/, data/ 全部)

走完第九段之后还有三个环节, 各归各的 skill: examples/41 自测归 `/showcase-quiz-cn`, examples/42 排练归 `/showcase-demo-cn`, examples/43 收尾归我.

另见 [索引 Task](../../examples/01-start-here/README-cn.md) 与 [SYLLABUS](../tasks/SYLLABUS-cn.md).
