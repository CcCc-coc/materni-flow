# 配置是怎么读进来的

> 一个 `Config` dataclass, 两个文件, 两个工厂. 所有"我跑在哪个环境"的判断集中在这一个
> 模块里, 别处只读 `one.config.xxx`.

**对应代码**: `agent_app/config.py`, `agent_app/runtime.py`

**依赖**: `constants` (provider 枚举和默认 model ID), `paths` (两个 env 文件的位置),
`runtime` —— 都在 [01](01-leaves.md).

---

## Config Pattern: 为什么值得单开一个模块

应用在不同环境下需要不同的配置:

- **本地**: 用 `~/.aws/credentials`, 数据库连自己的
- **Vercel**: 密钥来自环境变量, 没有 `~/.aws` 可用

朴素的做法是在代码各处写 `if runtime.is_vercel()`. 那样会产生三个问题: 逻辑在多个文件里
重复, 没人说得清两个环境到底差哪些配置, 而且漏掉一个判断就是一个 bug.

Config Pattern 把**所有环境相关的判断集中到一个地方**. 别处只管读 `one.config.xxx`,
不需要知道自己跑在哪.

**加一个配置项的完整步骤**:

1. 往 `Config` dataclass 加一个字段
2. 在 `new_from_env_var()` 里读它
3. 在 `.env.defaults` (非密钥) 或 `.env.example` (密钥) 里记一笔
4. 别处用 `one.config.your_new_field`

不需要在任何别的地方加 `if runtime.is_xxx()`.

---

## 两个文件, 按"是不是密钥"切

这条边界的**为什么**在 [architecture/07](../architecture/07-config-and-content.md);
这里只讲代码怎么落实它.

`load_env_files()` 依次读两个文件:

| | `.env` | `.env.defaults` |
| :--- | :--- | :--- |
| 装什么 | 凭证 | 其余全部, 含数据集的 `SCHEMA_NAME` |
| 进 Git | 不进 | **进** |
| AI 能开吗 | **不能** (`.claude/settings.json` 的 `deny`) | 能, 换数据集改的就是它 |
| 加载顺序 | **先, 所以它赢** | 后, 补空缺 |

把 `.env.defaults` 里的某个 key 在 `.env` 里重复一遍, 就在那台机器上覆盖了它 —— 比如让
一个 checkout 指向 staging schema.

**这个分层和"一个值两个家"不是一回事.** 分层发生在**同一个配置系统内部**, 只有一个读取者;
禁止的是同一个值躺在两个**互不相关**的配置系统里, 那种情况没有谁覆盖谁的规则, 只有两个都得
记得改.

**另一条看着也讲得通的切法是"会因为换一台机器而不同吗".** 不要用它: 按那条线切, 数据集的
身份 (一个字符串) 会被切成第三个配置文件, 于是要为它养一个格式和一个读取模块. 按密钥切的
这条线能挣回成本, 因为它决定的是**谁能打开这个文件**, 包括 AI.

---

## 两个工厂, 一个共享核心

```
new_from_env_var(**overrides)   读 os.environ, 不碰磁盘
new_in_local_runtime()          load_env_files() + new_from_env_var()
new_in_vercel_runtime()         load_env_files() + new_from_env_var(aws_access_key_id=..., ...)
new()                           按 runtime 分派
```

**两个工厂真正的差异只有一处: AWS 凭证.**

- 本地**故意不读** `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`. boto3 查环境变量早于
  `~/.aws/credentials`, 所以 `.env` 里一个占位符就能遮蔽一个好好的本地 profile, 报出来
  的是 `UnrecognizedClientException: The security token included in the request is invalid`
  —— 一条完全指不到原因的错.
- Vercel **必须读**: serverless 没有 `~/.aws`, 没有凭证链可以兜底.

用 `**overrides` 而不是布尔开关, 是为了让这个差异表现成调用点上的一小段参数列表, 而不是
第二份 17 行的字段赋值.

**Vercel 那边也调 `load_env_files()`, 这看起来多余但不是**: `.env` 在 Vercel 上不存在
(`load_dotenv` 对不存在的路径是无害 no-op), 但 `.env.defaults` 是 committed 的, 跟着部署
包上去, `SCHEMA_NAME` 靠它送达, 不用在面板里再填一遍. 面板里设的变量仍然优先, 因为 Vercel
在这之前就把它设进真实环境了.

---

## 校验在 `__post_init__`, 不在工厂里

三件事在 dataclass 的 `__post_init__` 里做, 不在两个工厂里:

- `SCHEMA_NAME` 的形状 (小写字母/数字/下划线, 不以数字开头, <= 63)
- `llm_provider` 归一化 (`strip().lower()`), 未知值直接报错
- `model_id` 为空时填上这个 provider 的默认值
- 打开了配额却没给表名 -> 报错

**放在 `__post_init__` 是为了让测试里手搓的 `Config(...)` 和从环境变量建出来的走同一条路.**
放在工厂里的话, 单测拿到的是一个没经过校验的对象, 于是测试通过而线上炸.

这几条共同的目的是把"某个用户的第一次请求失败"变成"启动失败". 一个拼错的 schema 名如果不
在这里拦, 表现出来是几层之外的一条 PostgreSQL 错误; 一个开了配额却没配表名的部署会**完全
正常地启动**, 直到有人打第一个字.

---

## 为什么没有模块级的 `config` 单例

一个很自然的写法是在模块底部写 `config = Config.new()`, 然后各处 `from agent_app.config
import config`. 这个仓库**不这么做**.

理由: 那会在 **import 时**读环境, 早于任何测试布置环境的机会. 而 `ConfigMixin` 已经通过
`one.config` 提供了懒加载的同一个东西 —— 见 [08](08-the-one-object.md).

---

## runtime 检测

`agent_app/runtime.py` 只回答一个问题: 我在哪跑. 实质是一句
`os.environ.get("VERCEL") == "1"`.

它保持独立模块而不是并进 `config.py`, 是因为它是一个**扩展点**: 加一个部署目标 (比如 AWS
Lambda) 意味着这里加一个 `is_*` 方法, `config.py` 加一个工厂和一个分支, 别处一行不改.

`Config.new()` 里那个 `else: raise RuntimeError` 今天**走不到** —— `is_local()` 定义就是
`not is_vercel()`. 留着它是为了将来加第三个目标却忘了改 `new()` 时会响, 而不是静默拿到
本地配置.

---

## 选哪个 LLM provider

每个进程只跟一个 LLM 后端说话, 由 `LLM_PROVIDER` 决定. 各家鉴权方式不同, 所以只有**被选中
那个** provider 的凭证是必需的:

```
LLM_PROVIDER=bedrock     -> AWS 凭证 (环境变量, 或 ~/.aws/credentials)
LLM_PROVIDER=anthropic   -> ANTHROPIC_API_KEY
LLM_PROVIDER=openai      -> OPENAI_API_KEY
LLM_PROVIDER=google      -> GOOGLE_API_KEY
```

`Config.validate()` 在缺凭证时给一条能读的错误, 而不是等 SDK 抛. 它由 `one.model` 在构造
模型之前调用, 所以配错在**建 agent 的时候**就炸, 不会拖到第一个用户提问.

**四家 SDK 全是核心依赖**, 所以换 provider 是改一个环境变量, 不是重装依赖也不是改部署
配置. 把它们做成 extra 是很自然的想法 (用 Bedrock 的人何必下载三个用不到的 SDK), 但**extra
按定义是 opt-in**: `uv sync` 不点名就一个都不装, 而 Vercel 的 Python 构建没有办法知道该点
哪一个 —— 结果是一个部署起来之后连不上任何模型.

---

## `"..."` 当作未设置

`.env.example` 里的占位符是 `"..."`. `load_dotenv` 不认识占位符这个概念 —— 一份从
`.env.example` 抄来, `AWS_ACCESS_KEY_ID="..."` 忘了注释掉的 `.env`, 会给你一个已设置,
非空, 且没用的变量.

`get_env()` 把这个值当成 unset 返回 `None`, 于是各家 SDK 能回退到自己的凭证链.
