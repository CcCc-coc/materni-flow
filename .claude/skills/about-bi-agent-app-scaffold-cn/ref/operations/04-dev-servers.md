# 开发服务器和 mise 任务

> 所有命令都从 `mise run` 走. 这篇先给任务表和 `mise` / `pnpm` / `uv` 三者的联动, 然后讲
> 为什么"关掉我的服务器"这件小事需要一个专门的脚本.

**对应代码**: `mise.toml`, `package.json`, `pyproject.toml`, `kill-dev-servers.py`,
`next.config.js`

---

## 任务表

```bash
mise run inst              装依赖 (Python + Node)
mise run dev               起两个开发服务器 (会先 kill)
mise run kill              停掉本 checkout 的服务器
mise run check             配置一致性检查 (换数据集之后跑)
mise run test              check + Python 测试 + Node 测试
mise run cov               覆盖率报告, 写到 htmlcov/
```

细分的任务 (`inst-python-deps` / `inst-node-deps` / `test-python` / `test-node` /
`next-dev` / `fastapi-dev`) 平时不用直接敲, 它们是上面这几条的组成部分.

`mise run export` 生成 `requirements.txt`, **Vercel 不读它** —— 留着是为了部署到只认
`requirements.txt` 的地方. 产物不提交: 第二份依赖清单就是第二个会漂移的东西.

---

## mise, pnpm, uv 谁调谁

`mise.toml` 管两件事: **钉工具版本**和**定义任务**.

```
[tools]  python 3.12   node 24   uv   pnpm   ruff   claude
```

所以 clone 之后不需要各自去装 Python 和 Node —— `mise` 按这张表准备好, 再由它调下面两个
包管理器:

| 生态 | 谁装 | 读哪个文件 |
| :--- | :--- | :--- |
| Python | `uv sync --all-extras` | `pyproject.toml` + `uv.lock` |
| Node | `pnpm install` | `package.json` + `pnpm-lock.yaml` |

`--all-extras` 是为了带上 `test` 那个 extra (pytest, pytest-cov, moto). **四家 LLM 的 SDK
不在 extra 里, 它们是核心依赖** —— 理由见 [backend/02](../backend/02-config.md).

### `mise run dev` 这一条绕了一圈

```
mise run dev
  ├─ depends: mise run kill          先清掉本 checkout 的旧进程
  └─ pnpm exec concurrently
       ├─ mise run next-dev          next dev --port 3000
       └─ mise run fastapi-dev       uvicorn api.index:app --reload --port 8000
```

**mise 调 pnpm 再调回 mise**, 因为并发跑两个进程这件事用 `concurrently` 最省事, 而它是一个
node 包.

两个子任务都带 `env = { AGENT_APP_DEV_SERVER = "{{config_root}}" }` —— 那个标记是
`mise run kill` 认出"哪些进程是我的"的依据, 详见下面.

### `package.json` 里那几个同名 script 不要用

```json
"dev": "concurrently \"npm run next-dev\" \"npm run fastapi-dev\""
```

它跑起来的东西看着一样, 但**少了两样**: 没有 `AGENT_APP_DEV_SERVER` 标记 (于是
`mise run kill` 认不出它), 也没有先 kill 那一步 (于是端口可能还被占着). 留着是因为
Vercel 的构建要 `package.json` 的 `build`, 而**日常一律用 `mise run dev`**.

### 前后端怎么接上

`next.config.js` 在开发环境把 `/api/*` rewrite 到写死的 `127.0.0.1:8000`. 这解释了两件事:

- 为什么 `next-dev` 把端口**钉死在 3000**: Next.js 默认在 3000 被占时会跳到 3001, 而跳过去
  的前端仍然指着 8000 —— 那里坐着的可能是另一个 checkout 的后端. 起不来比静默接错好
- 为什么 `mise run kill` 必须精确: 见下

生产环境那三条 rewrite 指向 `/api/`, 由 Vercel 把 `api/` 目录下的东西发现成 serverless
function.

---

## `mise run kill` 凭什么判定一个进程是"我的"

`kill-dev-servers.py` 看起来是个杂活脚本, 但它背后有一条硬规矩.

### 问题长什么样

三件事叠在一起:

1. **开发服务器永远不会自己退出.** `mise run dev` 起两个进程 (Next.js 和 uvicorn), 它们会
   一直跑到被杀
2. **一台机器上常常有好几个 checkout.** 这个脚手架的全部意义就是长出很多个项目, 于是同一
   台笔记本上同时躺着好几个同构的仓库
3. **它们用同一对端口** (3000 和 8000), 因为它们是同一个脚手架

所以"关掉我的服务器"这句话里的"我的", 需要被精确定义. 定义错了就会杀掉别人的.

### 两种想当然的做法都会误杀

- 扫 `ps`, 命令行里含 `npm run dev` / `concurrently` / `uvicorn` / `fastapi` 就算命中
- 对 3000 / 3001 / 3002 / 8000 / **8080** 无条件 `lsof -ti` 再 `kill -9`

两条都会误杀:

- 关键词匹配完全不看进程属于哪个目录. 机器上任何一个 Node 项目的 `npm run dev` 都会中枪
- `lsof -ti :3000` **不区分 LISTEN 和已连接**, 浏览器标签页, 任何远端端口恰好是 3000 的
  进程都会被返回并杀掉. 而 `8080` 更是随便什么东西都在用

### 规矩

> **一个进程只有能被证明属于**这个** checkout, 才会被杀.**

证明有三种, 满足任意一种即可:

1. 它的环境变量里带着这个 checkout 的 **dev marker** (子进程自动继承, 所以给树顶打标就等于
   给整棵树打标)
2. 它的**工作目录**就是项目根目录, 或者它的命令行里含项目根路径 (手工起的服务器的兜底)
3. 它是满足 1 或 2 的进程的**后代**

其余一律不动, 只报告.

### marker 的设计: 名字通用, 身份在值里

```
AGENT_APP_DEV_SERVER=<这个 checkout 的绝对路径>
```

脚本匹配的是**整串 `名字=路径`**, 不是只匹配名字. 这带来一个不直观但很有用的性质:

**变量名可以被整个脚手架家族共用.** 从这个脚手架长出的第 2, 第 3 个项目都可以用同一个
变量名, 各自的脚本靠路径区分, 谁也杀不到谁.

所以**不要为了"独一无二"把项目名塞进变量名** (`SMB_LENDING_LENS_DEV_SERVER` 那种): 那是在
用一个被设计成随时可换的东西去命名, 第一次换数据集它就过期了.

#### 为什么环境要单独扫一遍

读环境用的是 `ps -Eww`, 和读命令行是**两趟**, 这是故意的:

如果把环境和命令行拼成一个字符串一起匹配, 那么**任何从这个目录启动过的进程都会被判成
我们的** —— 因为环境里有 `PWD=<项目根目录>`. 你在项目目录里开一个 python REPL, 它就会被
杀掉.

### 几个 `lsof` 上的坑

```bash
lsof -nP -a -u <uid> -iTCP:3000 -sTCP:LISTEN -t
```

- **`-a` 是必须的.** lsof 默认把选择条件**或**起来. 没有 `-a`, `-u me -iTCP:3000` 的意思是
  "我的文件 **或** 任何 3000 端口上的东西", 返回的是机器上几乎所有进程
- **`-sTCP:LISTEN` 是重点.** 不加就会把连到开发服务器的每个浏览器标签页也算进来
- **`-u <uid>`**: 只看当前用户的进程. 既不会碰别人的账号, 也不需要 sudo

### 杀之前和杀的时候

**永远不杀自己的祖先.** 脚本先算出自己这条父进程链并保护起来 —— 否则 `mise run dev` 会把
调用它的那个 shell 杀掉.

**一棵树一起杀.** 认定一个进程属于我们, 就连它的所有后代一起杀: `next dev` 会派生
next-server, next-server 再派生 postcss worker, `uvicorn --reload` 会派生真正的应用进程.
只杀父进程会留下孤儿继续占着端口.

**先 SIGTERM, 宽限几秒, 再 SIGKILL.** 这不只是礼貌: 优雅关闭会让 uvicorn 打出
`Application shutdown complete`, 日志里能一眼看出这是正常谢幕而不是崩溃. 一上来
`kill -9` 只留下一个退出码 137 和一片空白日志.

### 挡路的不是我们的, 怎么办

这是最关键的一条.

放过别人的进程是对的, 但**放过之后不能假装没事发生**. 报告一句"这个不是我们的"然后
**正常退出**, `mise run dev` 就会看到依赖成功而继续启动 —— 然后启到一半撞墙:

- uvicorn 撞上 `Address already in use` 直接死掉
- 而 Next.js **悄悄退到 3001** 起来了

于是 `localhost:3001` 上跑着 A 项目的前端, 而它的 `/api` 被 rewrite 到写死的
`127.0.0.1:8000`, 那里坐着 **B 项目的后端**. 页面能打开, 能聊天, 底下是另一个仓库的 agent
和数据库. **这比直接报错危险得多.**

所以是两条一起上:

1. **端口钉死**: `next dev --port 3000`, 不允许漂移
2. **`kill` 在端口仍被占时以非零状态退出**, 而 `dev` 依赖 `kill`, 依赖失败整条链就停住

报错信息也重写成人话: 这些端口被不是本项目的进程占着, 我不乱动, 多半是你另开了一个 app,
自己看一眼 —— 本 app 设计成一次只跑一个.

### `--force`: 抢端口, 不是清场

`--force` 的语义必须是"**把我要的端口拿过来**", 不是"杀光所有不是我的东西".

写成后者的话, 它就是本篇开头那种误杀, 只是藏在一个 flag 后面: 跑一次 `--force` 会把隔壁
仓库那些只占着 3001, 跟我们要的端口八竿子打不着的进程一起杀掉.

规则:

- 只有**真正占着 3000 或 8000** 的外来进程才够格
- 够格之后**连根拔起**: 从它往上追到那套 dev server 的树根, 整棵树一起杀. 只杀监听者会留下
  对方的 `concurrently` 和 `mise run` 包装层, 而且 `uvicorn --reload` 的父进程会把刚杀掉的
  worker 重新拉起来

**往上追的边界很重要**: 只在父进程"长得像 dev server"时才继续往上走. 用户的 shell 和终端
不匹配任何 dev server 特征, 所以走到那里就停 —— 绝不会往上误伤到终端.

## 退出码怎么读

| 码 | 含义 |
| :--- | :--- |
| 143 | SIGTERM. 通常是同一个 checkout 里第二次 `mise run dev` 把前一个替换掉了. **不是错误** |
| `kill` 步骤返回 1 且没起服务 | 有别的 checkout 占着 dev 端口. 这是设计好的拦截 |

143 那条值得记住: mise 会把它报成 `task failed`, 看起来像出事了, 其实是被替换者的正常
谢幕.

## 在 agent 会话里跑开发服务器

这条不在脚本里, 在 `CLAUDE.md`, 但和这篇是一件事的两面:

`mise run dev` 永远不会自己退出, 所以**不要在前台等它**. 起服务和等就绪要拆成两件事: 服务
后台跑不去等它, 另起一个**会自己退出的** `until` 循环去等日志里那行就绪标记.

两半的就绪标记不一样: Next.js 打 `Ready in`, uvicorn 打 `Application startup complete.`.
只等前者会误判成"起好了"而后端还没起.

还有一条: **起之前先想清楚这个服务器归谁.** 自己验证用的就后台起, 验完就停; 用户要留着
用的就用 `nohup` 脱离, 免得它挂在某个任务上, 几十分钟后甩出一条过期的失败通知.
