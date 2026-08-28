# `one`: 把所有零件装起来的那个对象

> 前面七篇讲的是零件, 这篇讲它们怎么被装成一个东西. `one` 是这个后端唯一的**组装点**:
> 配置, 数据库引擎, AWS client, LLM model, agent 和它的工具, 全部挂在它身上, 全部懒加载.

**对应代码**: `agent_app/one/one_00_main.py` `one_01_config.py` `one_02_db.py`
`one_03_boto3.py` `one_04_agent.py` `one/api.py` `agent_app/api.py`

**依赖**: `config`, `constants`, `paths`, `sql_utils`, `db_schema/api` —— 也就是前面几篇的
全部. 这是依赖最多的一层, 所以排在最后面讲.

---

## 一个类, 四个 mixin

```python
class One(ConfigMixin, DbMixin, Boto3Mixin, AgentMixin):
    """Central class that combines all mixin functionalities."""

one = One()
```

`One` 自己是空的. 四个 mixin 各管一块:

| 文件 | 提供 |
| :--- | :--- |
| `one_01_config.py` | `self.config` |
| `one_02_db.py` | `self.engine`, `self.remote_postgres_engine`, `self.database_schema_str`, `self.execute_sql_query()` |
| `one_03_boto3.py` | `self.boto_ses`, `self.bedrock_runtime_client()`, `self.dynamodb_client()` |
| `one_04_agent.py` | `self.model`, `self.agent`, 和三个 `@tool` 方法 |

编号是**加载顺序也是依赖顺序**: `one_02_db` 用 `self.config`, `one_04_agent` 用
`self.config` 和 `self.boto_ses`. 加第五个 mixin 就叫 `one_05_*`, 在 `one_00_main.py` 里
import 并加进继承列表.

### 为什么是 mixin 而不是四个独立模块

因为这四块**互相要用对方的东西**, 而且用的方式是"读一个已经建好的东西", 不是"调一个纯函数".
`database_schema_str` 要 `self.config.schema_name` 和 `self.engine`; `bedrock_model` 要
`self.boto_ses` 和 `self.config.model_id`.

写成独立模块的话, 每个函数都要把上游的东西当参数传进来, 而调用方 (`api/index.py`) 就得
自己按顺序建 config, 建 engine, 建 session, 建 model, 再建 agent —— **组装逻辑会漏到
使用者那里**, 而且每个使用者都得抄一遍.

mixin 把组装收在一个类里, 使用者只写 `one.agent`.

**代价要认**: mixin 之间的依赖是隐式的 —— `DbMixin` 用 `self.config`, 但它并不声明这一点.
所以有一条纪律: **mixin 之间只能通过 `self.<别的 mixin 的属性>` 互相用, 不能 import 对方**.
真需要一个不依赖 `One` 的东西, 那它就该是纯函数, 放 `sql_utils.py` 那种地方.

### `self: "One"` 这个写法

```python
if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One

class DbMixin:
    @cached_property
    def engine(self: "One") -> sa.Engine:
        ...
```

`DbMixin` 里访问 `self.config`, 但 `config` 是 `ConfigMixin` 给的, 类型检查器看 `DbMixin`
一个类是看不出来的. 把 `self` 标成 `"One"` 就让 IDE 和 mypy 知道运行时它一定是完整的
`One`, 于是 `self.config.` 有补全.

`import One` 只在 `TYPE_CHECKING` 下发生, 因为运行时真去 import 就是循环 ——
`one_00_main` import 每个 mixin, mixin 又 import `one_00_main`.

---

## 一切都是 `cached_property`, 这就是这里的依赖注入

没有 DI 容器, 没有 `__init__` 参数, 只有 `cached_property`. 它同时买到三件事:

**一, 懒加载.** `one = One()` 这一行不连数据库, 不建 AWS session, 不读提示词. 导入这个
模块是免费的 —— 这对 serverless 冷启动和对"只想 import 一个常量"的脚本都要紧.

**二, 单例语义.** 一个进程里只有一个 engine, 一个 agent, 一个 config. 建好之后所有调用方
拿到的是同一个.

**三, 可替换.** 测试里 `monkeypatch.setattr(one, "config", fake)` 就替掉了, 因为
`cached_property` 写进的是实例 `__dict__`.

`bedrock_runtime_client()` 和 `dynamodb_client()` 是**方法不是属性**, 这是有意的:
构造一个 boto3 client 要解析那个服务的模型文件, 不便宜, 而一个只用 OpenAI 的部署一个
client 都不该建. 属性会被顺手求值, 方法不会.

---

## 两个 engine, 分工不能混

| | 用途 | `search_path` |
| :--- | :--- | :--- |
| `engine` | **agent 读的那一个**, 也是 `execute_sql_query` 用的 | 钉在 `config.schema_name` |
| `remote_postgres_engine` | 跨 schema 的活: 建 schema, 看有什么 | 不钉, 用服务端默认 |

两个都由 `_new_postgres_engine(schema_name=...)` 造出来, 差别只有传不传 schema.

**agent 永远不碰 `remote_postgres_engine`.** 它存在的唯一理由是同步过程要在 schema 还没建
出来的时候连上去 —— 一个钉了不存在 schema 的 `search_path` 连不上任何东西.

`engine` 在任何环境下都是 PostgreSQL, 本地也一样. 这条边界的完整论证见
[architecture/05](../architecture/05-why-postgres-everywhere.md), 一句话是: 查这个库的是
模型, 而模型的 SQL 来自一份写死的提示词, 提示词只能对着一种方言写.

### `search_path` 三种钉法, 只有第三种成立

这是全仓库最长的一段代码注释, 因为前两种写法都是显而易见的, 而且都会在生产上咬人:

| 做法 | 结果 |
| :--- | :--- |
| libpq 启动参数 `options=-csearch_path=...` | **连不上**. Neon 的 `-pooler` 和 PgBouncer 一律拒绝, 在驱动层就失败, 表现为整个应用连不上数据库 |
| `connect` 事件上 `SET search_path` | **看起来能用, 不安全**. 事务池化下代理按事务分配服务端连接, SET 跑过的那条不一定是后续查询拿到的那条. 症状是"表突然消失" |
| `begin` 事件上 `SET LOCAL search_path` | **对**. 事务是代理保证留在同一条服务端连接上的单位 |

SQLAlchemy 在第一次 execute 时隐式开事务, 所以 schema 反射和 agent 的 SQL 工具都免费拿到.

schema 名拼进 SQL 之前会把 `"` 转义成 `""`. `Config.__post_init__` 已经用
`SCHEMA_NAME_PATTERN` 卡过一遍, 这是第二道.

### `database_schema_str` 里两个不能省的细节

```python
metadata = sa.MetaData(schema=self.config.schema_name)
metadata.reflect(bind=self.engine, schema=self.config.schema_name)
```

**schema 要给两次.** `reflect()` 那个决定反射谁, `MetaData(schema=...)` 那个决定编码器
在块头上写什么 —— 少了后者, agent 被告知它在看一个叫 `default` 的 schema.

**反射出零张表要当场抛异常.** 因为**空 schema 和不存在的 schema 在反射器看来一模一样**,
不抛的话 agent 拿到一份没有表的库结构, 然后凭空编出一些看起来合理的表名来回答, 而且答得
很自信. 异常信息里直接给出跑哪个脚本.

---

## LLM provider: 一个进程一个后端

`self.model` 按 `config.llm_provider` 分支, 四家各建各的 strands model 类.

**先 `self.config.validate()`.** 缺凭证在这里就报, 而不是等第一个用户提问时收到一条
认证错误 —— 那时候错误已经离配置很远了.

### 三个踩出来的细节

**一, provider SDK 是可选依赖, 不是核心依赖.**

```
LLM_PROVIDER=bedrock     开箱可用 (boto3 本来就是核心依赖)
LLM_PROVIDER=anthropic   uv sync --extra anthropic
LLM_PROVIDER=openai      uv sync --extra openai
LLM_PROVIDER=google      uv sync --extra gemini
```

`strands.models` 对每家是懒 import 的, 所以没装的时候原始报错是一句
`ModuleNotFoundError: No module named 'anthropic'` —— 它没告诉你该干什么.
`load_strands_model_class()` 把它换成一条带 `uv sync --extra ...` 的可执行指示,
外加"或者切回 bedrock"这条退路.

**二, OpenAI 用的是 `OpenAIResponsesModel`, 不是 chat-completions.**

reasoning 系列 (gpt-5.x) 在 `/v1/chat/completions` 上**拒绝把 function tool 和 reasoning
一起用**:

```
Function tools with reasoning_effort are not supported for <model> in
/v1/chat/completions. To use function tools, use /v1/responses or set
reasoning_effort to 'none'.
```

而这个 agent 除了工具什么都没有. 设 `reasoning_effort='none'` 也能绕开, 但那只对 reasoning
模型有效, 老模型会直接拒收这个参数. Responses 也是 OpenAI 现在的主 API, 所以跨代都能用.

**三, `max_tokens` 只有 Anthropic 要.** 别家不传, 传了也无害, 但只在需要的分支上出现更能
说明"这是那家的要求"而不是我们的选择.

---

## 三个 `@tool`

```python
tools=[
    self.tool_get_database_schema,
    self.tool_execute_sql_query,
    self.tool_write_debug_report,
]
```

**tool 的 docstring 是给模型读的, 不是给人读的.** 它们是这个仓库里唯一一处 docstring 会
进 LLM 上下文的地方, 所以那里的详细程度和别处的规矩不一样 —— 参数含义, 返回值形状, 什么
时候该调, 都要写出来. 这不违反[只写 why 那条规矩](../architecture/09-comments-and-docs.md),
因为它们不是注释, 是**接口文本**.

### 那个被注释掉的类型注解

```python
def tool_get_database_schema(
    # self: "One",  # keep for IDE type hints, strands @tool doesn't support typed self
    self,
) -> str:
```

strands 的 `@tool` 会读函数签名去生成 JSON schema, 而一个带类型注解的 `self` 会被它当成
一个参数. 所以注解只能注释掉留着当文档. **不要"顺手修好"它.**

### 加一个写操作的 tool

写操作是**数据集特有的**, 所以默认一个都不带. 需要的时候:

1. 底层逻辑写成纯函数, 拿 `engine` 当第一个参数, 返回 dict —— 跟 `sql_utils.py` 一样,
   这样它能被单测而不用建 `One`
2. 在 `AgentMixin` 上加 `@tool` 方法, 转调那个纯函数
3. 加进 `self.agent` 的 `tools=[]` 列表
4. 在 `data/system-prompt.md` 里告诉 agent 什么时候用它

第 4 步最容易忘, 而忘了的症状是这个工具一次都不会被调用, 且没有任何报错.

**只读的承诺在 `sql_utils` 那一层**, 不在这里 —— `execute_sql_query` 靠事务永远回滚兜底
(见 [03](03-sql-execution.md)). 加写操作 tool 就是有意在这个承诺之外开一个口子, 所以它必须
走自己的代码路径, 不能借道 `execute_sql_query`.

---

## `api.py` 那两层再导出

```
agent_app/api.py      →  from .one.api import one
agent_app/one/api.py  →  from .one_00_main import one
```

两个文件都只有一行, 都带 `__all__`. 它们的作用是**给外部一个稳定的 import 路径**: 使用者
写 `from agent_app.api import one`, 于是 `one_00_main.py` 改名, 拆分, 重排都不会波及调用方.

`__all__` 是给 linter 看的 —— 一个 re-export 在 pyflakes 眼里就是"import 了没用", 写出
`__all__` 才能表明这是故意的.
