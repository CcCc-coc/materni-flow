# 换行业的 AI 数据分析脚手架 发布清单

> showcase-publish-cn skill 靠这份文档把这个教学 repo 转成作品 repo. 机器友好: 路径和表格, 不写散文. 针对这一棵树生成, 里面的 glob 已经展开成真实路径.

## 0. 动手之前

**这个 repo 的发布口径和 lesson-smith 的默认不一样, 是创作者逐条定的, 以本文件为准.**

**你应该有两个 repo:**

| repo | 是什么 | 里面有什么 |
| :--- | :--- | :--- |
| 开发部署用 | 你自己的机器, **永久保留** | 全套. 教学材料, 换数据集那三个 skill, `dataset/` 源文档, 全在 |
| demo 用 | 给别人看的那个 | 这份清单作用的对象, 清理过的成品 |

**下面的删除是不可逆的**, 而且它会删掉换数据集那整套工具 —— 也就是第 39 篇说的那台"能反复长出作品的机器". 那台机器住在开发那个 repo 里.

**所以第一件事是停下来确认: 开发那个 repo 还在, 而且你现在动的不是它.** 确认不了就不要往下走.

## 1. 铁律删除

- path: `examples/` (**整个目录, 43 个 Task 全删**)
  reason: 两 repo 模型下, 主线教学 Task 在 demo repo 里没有用途. 这一条比 lesson-smith 默认狠 (默认只删索引与 quiz 之后), 是创作者定的
  detected_by: 目录存在性
  展开后的真实路径:
  - `examples/01-start-here/`
  - `examples/02-why-this-project/`
  - `examples/03-prerequisites/`
  - `examples/04-work-with-ai/`
  - `examples/05-get-it-running/`
  - `examples/06-read-the-codebase/`
  - `examples/07-teaching-and-production/`
  - `examples/08-app-router-and-shells/`
  - `examples/09-copy-lives-in-one-file/`
  - `examples/10-the-home-page/`
  - `examples/11-the-agent-page/`
  - `examples/12-render-text-into-blocks/`
  - `examples/13-light-it-up/`
  - `examples/14-what-a-dataset-is/`
  - `examples/15-seed-to-postgres/`
  - `examples/16-wire-next-to-fastapi/`
  - `examples/17-the-ai-sdk-protocol/`
  - `examples/18-read-the-schema/`
  - `examples/19-sql-by-business-question/`
  - `examples/20-call-the-model-directly/`
  - `examples/21-multi-turn-and-caching/`
  - `examples/22-encode-the-schema-for-llm/`
  - `examples/23-your-first-agent/`
  - `examples/24-the-sql-tool/`
  - `examples/25-the-system-prompt/`
  - `examples/26-explain-the-reasoning/`
  - `examples/27-write-operations/`
  - `examples/28-one-chat-request/`
  - `examples/29-the-one-object/`
  - `examples/30-configuration/`
  - `examples/31-tests-without-network/`
  - `examples/32-content-checks/`
  - `examples/33-the-spend-cap/`
  - `examples/34-the-rendering-contract/`
  - `examples/35-deploy-to-vercel/`
  - `examples/36-your-own-domain/`
  - `examples/37-swap-the-dataset/`
  - `examples/38-redesign-the-frontend/`
  - `examples/39-the-real-play/`
  - `examples/40-go-deeper-by-role/`
  - `examples/41-prove-i-get-it/`
  - `examples/42-how-i-build-this/`
  - `examples/43-where-to-go-next/`
  - `examples/_lm-example-plan.md`
  - `examples/_lm-quiz-plan.md`

- path: `docs/` (整个目录)
  reason: `docs/tasks/` 是 lesson-smith 生成的汇总视图, `docs/showcase/` 是这五份给 skill 读的机器文件, 含你正在读的这一份
  detected_by: 目录存在性
  展开: `docs/tasks/`, `docs/showcase/`

- path: `.claude/`, `.agents/`, `.codex/` (三个目录整删)
  reason: 给 AI 和维护者看的规范, 加四个生成的子 skill. 它是内部记录, 露出去只显得项目还在建设中
  detected_by: 目录存在性
  注意: 这一删同时删掉 `showcase-learn-cn`, `showcase-quiz-cn`, `showcase-demo-cn`, `showcase-publish-cn` 四个子 skill, 以及 `about-bi-agent-app-scaffold-cn/scripts/teaching_cli.py` (造数据与同步), 以及换数据集那三个 skill. **这就是第 0 节说的那台机器**

- path: `CLAUDE.md`, `AGENTS.md`
  reason: 给 coding agent 的总纲, 一眼看出这个仓库是照着让 AI 改的样子设计的教学仓库
  detected_by: 文件名匹配

- path: `dataset/`, `dataset-for-swap/`
  reason: 数据集的源文档与生成器, 加那份留着练手的产科病房排班数据集. 成品仓库连的是一个已经灌好的数据库, 不需要带着造数据的工具
  detected_by: 目录存在性

- path: `agent_app/dataset.py`, `tests_python/test_dataset.py`
  reason: 唯一住在生产代码包里的教学文件, 加它的测试. 生产路径一行都不 import 它, 所以删掉不影响 app 运行 (有一条 AST 测试守着这条边界)
  detected_by: 文件名匹配

- path: `scripts/`
  reason: 只剩一个 `test_agent.py`, 本地调试用的一次性工具
  detected_by: 目录存在性
  展开: `scripts/test_agent.py`

- path: `lm.json`
  reason: lesson-smith 的 repo 类型清单
  detected_by: 文件存在性

- path: `README-ORIGINAL-cn.md` (及其余各语种)
  reason: 对外的课程电梯陈述, 只有教学 repo 才有
  detected_by: 文件名匹配
  **注意: 生成这份清单时它还不存在** (它是创作流第 13 步的产物). 跑的时候按文件名匹配一次, 有就删

- path: 全部 `TICKET` 文件 (44 个)
  reason: 教学任务卡, 根目录和每个 Task 下都有
  detected_by: 文件名匹配
  展开: `TICKET.md`, 加 `examples/` 下 43 个 `TICKET-cn.md` (随 `examples/` 整个目录一起没了)

- path: `README-cn.md` (根目录)
  reason: 见第 2 节. 它现在装的是上一门课的残留内容, 而且作品 repo 不带语种体系
  detected_by: 文件名匹配
## 2. 语种收敛

**这一节的结论是读过文件内容得出的, 不是看后缀猜的.**

作品 repo 只带一个语种. 这棵树的实际情况和 lesson-smith 的默认假设不同, 三条:

- **`examples/` 下 86 个 `-cn` 文件, 零个无后缀版.** 所以那里**不存在**"留空的占位符"这个问题, 也不需要做删占位符再改名那套动作 —— 整个目录在第 1 节已经删掉了
- **根目录那三份装的是上一门课的残留内容**, 三份都不是这门课的根文档:
  - `README.md` 是 `# SMB Lending Lens: The System Prompt`
  - `README-cn.md` 是 `# SMB Lending Lens: 系统提示词`
  - `TICKET.md` 是 `# Ticket: 03-The-System-Prompt`
- `.claude/` 与 `.agents/` 下那些无后缀的 `README.md` 随两个目录整个删掉, 不用单独处理

**所以这一节实际要做的只有一件事:**

- 保留的语种: 不适用. 作品 repo 的根 `README.md` **是学生自己手写的那一份** (见第 5 节), 不是这里任何一份现存文件
- 删除: `README-cn.md`, `TICKET.md` (已在第 1 节列出)
- 改名: **不适用**. 没有任何一份 `-cn` 文件需要被改名成无后缀版

**收尾时按 glob `**/*-cn.md` 扫一遍确认零命中**, 那是作品 repo 不该有语种体系的兜底检查.

## 3. 待定项

因为 `examples/` 整个删掉, lesson-smith 默认那条"保留下来的主线教学 Task 永远在待定项里"**在这个 repo 不适用**.

- path: `src/math.js`
  reason: TDD 相关的东西, 创作者点名保留
  default: keep
- path: `chore.txt`
  reason: deploy 用得到, 创作者点名保留
  default: keep
- path: `tmp/`, `htmlcov/`, `build/`, `.idea/`, `agent_app.egg-info/`, `.coverage`, `.pytest_cache/`
  reason: 本地产物, 都已被 `.gitignore` 排除, 不会进 commit. 但发布前顺手看一眼工作区干不干净
  default: keep
- path: `blogs/`, `img/`, `examples-staging/`, `package.json.md`, `project.README.md`
  reason: 老课程留下的素材, **生成这份清单时创作者已经删掉了**. 跑的时候确认一次它们确实不在
  default: keep

## 4. 按依赖排序的 commit 计划

最不依赖别人的先提交, 让 history 读起来像自然长出来的. 全部是这棵树的真实路径.

| # | 文件 | 建议的 commit message | 理由 |
| :- | :--- | :--- | :--- |
| 1 | `.gitignore`, `mise.toml`, `pyproject.toml`, `package.json`, `uv.lock`, `pnpm-lock.yaml` | Set up the toolchain | 根配置, 其余全都长在它上面 |
| 2 | `.env.example`, `.env.defaults` | Split config by whether it is a secret | 那条判据: 是不是密钥, 而不是会不会因机器而异 |
| 3 | `agent_app/paths.py`, `constants.py`, `utils.py` | Add the leaf modules | 零依赖, 谁都不 import 它们之外的东西 |
| 4 | `agent_app/sql_utils.py` | Make read-only a property of the transaction | 只读靠永远回滚, 不靠关键词黑名单 |
| 5 | `agent_app/config.py`, `runtime.py` | Validate config at construction time | 校验放在对象造出来那一刻, 不放在两个工厂里 |
| 6 | `agent_app/db_schema/` | Compress the schema for the model | 反射, 建模, 编码三步单向 |
| 7 | `agent_app/agent_response.py` | Pull thinking and answer apart | 最后一条消息不一定是答案 |
| 8 | `agent_app/vendor/`, `agent_app/ai_sdk_adapter.py` | Speak the AI SDK stream protocol | 对读的东西严格, 对不读的东西宽容 |
| 9 | `agent_app/quota.py` | Add a monthly spend cap | 开关住在拥有它的模块里 |
| 10 | `agent_app/one/`, `agent_app/api.py`, `agent_app/__init__.py` | Assemble everything behind one object | 四个 mixin, 用到才建 |
| 11 | `agent_app/cli.py`, `agent_app/content_check.py`, `agent_app/agent_debugger.py`, `agent_app/source_code.py` | Add the app CLI and content checks | 建立在上面那些之上 |
| 12 | `api/index.py`, `vercel.json`, `.vercelignore` | Wire up the HTTP entry point | 只有顺序, 没有业务 |
| 13 | `data/` | Put everything domain-specific in one place | 换一个行业改的就是这个目录 |
| 14 | `lib/`, `tailwind.config.ts`, `postcss.config.mjs`, `tsconfig.json`, `next.config.js` | Add the frontend foundation | 组件长在它上面 |
| 15 | `components/`, `hooks/`, `app/` | Build the two pages | 首页给陌生人, agent 页给使用者 |
| 16 | `tests_python/`, `tests_node/`, `.coveragerc` | Test without touching the network | 269 个用例, 一个包都不发 |
| 17 | `kill-dev-servers.py`, `src/math.js`, `chore.txt` | Add the local dev helpers | 收尾的零碎 |
| 18 | `README.md` | Write the project README | 门面, 最后写 |

## 5. README 大纲

**这一份和别的 showcase repo 不一样: README 学生在跑这个 skill 之前就已经写好了.**

它是换数据集那条线的倒数第二步, 位置在教学的 [examples/38 第 11 节](../../examples/38-redesign-the-frontend/README-cn.md). 所以这里的动作是**先检查, 缺了或者不合格再陪他补写**.

- 语种: **问学生一次**. 公开作品用英文很常见, 哪怕课程内容是中文的
- **长度上限 1000 词** (创作者定的, 覆盖 lesson-smith 默认那个 250 到 500). 目标落在 300 到 500 最舒服, 1000 是硬上限
- section: 项目是什么
  goal: 这是个什么东西, 谁会在乎, 用学生自己的话说
  prompts: ["一句话, 这是个什么?", "谁会在乎它?", "它让你能做到什么?"]
  length: 60 到 120 词
- section: 怎么装怎么跑
  goal: 从 clone 到跑出东西的最短路径
  prompts: ["最短的一串命令是什么, 跑完能出结果?", "要几个外部账号?"]
  length: 60 到 120 词
- section: 我做了什么, 它怎么工作
  goal: 这活的形状, 加一个值得说的设计取舍
  prompts: ["主要有哪几块?", "有哪个决定是你现在还觉得做对了的?", "只读是怎么保证的?"]
  length: 100 到 200 词
- section: 我学到了什么
  goal: 具体的东西, 不是套话
  prompts: ["什么事让你意外?", "最难的是哪一段, 你怎么过去的?"]
  length: 80 到 150 词
- section: 下一步 (可选)
  goal: 一个诚实的下一步
  prompts: ["再给你一周, 你会加什么?"]
  length: 40 到 80 词

## 6. 敌意扫描规则

假设读者就是在找破绽. 每一类给探测方式和严重度.

- 铁律删除物残留 (HIGH): glob `examples/`, `docs/`, `.claude/`, `.agents/`, `.codex/`, `CLAUDE.md`, `AGENTS.md`, `dataset/`, `dataset-for-swap/`, `scripts/`, `lm.json`, `README-ORIGINAL*`, `**/TICKET*.md`, `agent_app/dataset.py`. 报出确切路径
- 还留着带语种后缀的文件 (HIGH): glob `**/*-cn.md`. 作品 repo 不该有语种体系
- **README 缺席或带教学口吻 (HIGH)**: 先确认根 `README.md` 存在且不是那份 `SMB Lending Lens: The System Prompt` 的残留; 再 grep 它与根目录 `*.md`, 找 `本教程`, `本课`, `这门课`, `我们学过`, `我们在这门课里`, `作为学生`, `教程`, `Task`, `练习`. **这一条是创作者点名要加的检查, 以前完全漏掉过**
- README 超长 (MEDIUM): 超过 1000 词就报出来
- commit message 里的教学口吻 (MEDIUM): 同一套措辞过 `git log --all --format="%s%n%b"`
- git ref 暴露课程来源 (MEDIUM): `git tag --list` 与 `git branch --all`, 找 `01-showcase`, `ready-for-swap`, `NN-title` 那种按 Task 命名的分支, `tutorial-base`, `from-course`, `original`
- 残留的子 skill 目录 (HIGH): 任何还在的 `.claude/skills/showcase-*` 或 `docs/showcase/`
- 卫生问题 (LOW): `.DS_Store`, `__pycache__/`, `.venv/`, `*.egg-info/`, `.idea/`, `htmlcov/`, `.coverage`, `tmp/`
- 可疑的雷同 (MEDIUM): 多个文件同模板生成的注释横幅或结构. 报出来即可, 不强制改
