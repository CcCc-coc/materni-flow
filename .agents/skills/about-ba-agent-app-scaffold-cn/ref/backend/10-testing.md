# 测试怎么组织的

> 这篇讲 `tests_python/` 的布局, 为什么**没有一个测试连网**, `# pragma: no cover` 什么时候
> 才够格用, 以及 fixture 里为什么不许出现这个数据集的真表名.

**对应代码**: `tests_python/`, `agent_app/tests/`, `.coveragerc`, `mise.toml` 的
`test-python` / `cov-python`

---

## 布局: 镜像 `agent_app/`

```
agent_app/quota.py              ->  tests_python/test_quota.py
agent_app/one/one_02_db.py      ->  tests_python/one/test_one_one_02_db.py
agent_app/db_schema/encoder.py  ->  tests_python/db_schema/test_db_schema_encoder.py
```

一个源文件对一个测试文件, 目录结构一致. 这样"这个模块有没有测试"是一个看目录就能回答的
问题, 而不是一个要 grep 的问题.

**开发工具也算在内.** `content_check.py` 和 `cli.py` 是给人跑的命令, 不在请求路径上, 但它们
住在 `agent_app/` 里就一样被覆盖率量着, 一样各有一个镜像测试文件. 判据不是"它上不上生产",
是"它在不在这个包里" —— 和 `dataset.py` 特意不被 `.coveragerc` omit 掉是同一条.

**纯声明式的模块没有自己的测试文件**: `paths.py`, `constants.py`, `db_schema/model.py`,
`db_schema/api.py`. 它们里面没有分支, 断言"这个枚举有这几个成员"只是把代码抄一遍, 抄错了
两边一起错. 它们的覆盖率来自读它们的那些测试 —— 当前 `agent_app/` 是 100%.

`tests_python/test_api.py` 是个例外, 它只有一行 `_ = api.one`. 那不是在测行为, 是在证明
**这个 import 路径还活着** —— 它是外部唯一该用的入口, 断了就是所有调用方一起断.

```bash
mise run test-python     # pytest tests_python
mise run cov-python      # 同上, 加覆盖率报告 (term + htmlcov/)
mise run test            # check + python + node
```

---

## 每个测试文件底部那段是干什么的

```python
if __name__ == "__main__":
    from agent_app.tests import run_cov_test

    run_cov_test(__file__, "agent_app.quota", preview=False)
```

**直接 `python tests_python/test_quota.py` 会只跑这一个文件, 并且只报这一个模块的覆盖率.**
写一个模块的时候这比跑整个测试套件快得多, 而且输出里不会混进另外二十个文件的未覆盖行.

`agent_app/tests/` 是这套东西的实现: `helper.py` 把项目根目录和 `htmlcov/` 的路径填好,
`pytest_cov_helper.py` 是拷进来的第三方小工具 (所以 `.coveragerc` 把它 omit 掉 —— 它是
测试工具, 不是被测代码).

`tests_python/all.py` 和各子目录的 `all.py` 是同一个东西的目录版: 跑整个包或整个子包的
覆盖率.

---

## 没有一个测试连网

这是这套测试最重要的一条性质, 而且它不是自然发生的 —— 被测的东西里有数据库, 有 AWS,
有 LLM. 三种手段:

| 要测什么 | 怎么做到不连网 |
| :--- | :--- |
| `db_schema/` 的反射和编码 | 手搓 `sa.MetaData`, 或者反射**内存 SQLite** (`sqlite://`) |
| `quota.py` 的 DynamoDB 读写 | **moto** (`mock_aws`), 一个进程内的 DynamoDB 实现 |
| `one/` 的引擎和 model 构造 | monkeypatch 掉 `one.config`, 断言构造参数而不是真去连 |

`sql_utils` 和 `dataset` 的同步逻辑也走内存或临时文件 SQLite.

**真正需要 PostgreSQL 的事** —— `search_path` 钉得住不住, 同步是不是真的把行搬过去了 ——
不由 pytest 覆盖, 由 `scripts/` 下的编号脚本覆盖 (`test_05` 连通性, `test_06` 同步,
`test_07` 逐表对行数). 那些是**要人去跑的验证**, 不是 CI 里的单元测试. 把它们塞进 pytest
只会得到一套在没配 `DB_*` 的机器上必然红的测试.

### moto 而不是手写的桩

这个区别在 `quota.py` 上是实质性的, 值得单独说.

**手写的桩断言的是作者对 API 形状的信念.** `quota.py` 走的是 DynamoDB 的低层 client API,
数字长成 `{"N": "42"}`, 计数器用 `ADD` 表达式更新. 如果作者以为写进去的是 `{":i": 1}` 而
实际要 `{":i": {"N": "1"}}`, 那么代码和桩会**一起错**, 测试照样绿, 上线才炸.

moto 跑的是真实现, 于是两件事第一次可以被断言:

- **计数器真的在累加** —— 桩只能记录"`update_item` 被调用了", moto 会真的执行 `ADD`,
  三次 increment 之后读回来是 3. 这正是不用 read-then-write 的理由 (并发下丢更新)
- **故障是真故障** —— "计量出错不能拒绝服务"那几条现在指向一张**不存在的表**, botocore
  抛的是它真正会抛的 `ResourceNotFoundException`

fixture 里塞了假 AWS 凭证, 所以就算 mock 没生效也够不到真账号.

---

## fixture 用虚构领域, 不用真表名

```python
schema_name="acme_widgets"
Table("widget", ...), Table("part", ...)
```

**不要写 `loan` / `customer` / `risk_grade`.** 一个断言 `loan` 的测试在换数据集之后不会
失败 —— 它只是变成一句谎话, 描述着一个不存在的领域. 而且它会让读的人以为这个测试和当前
数据集有关系, 于是不敢动.

`acme` / `widget` / `part` 不属于任何真实数据集, 所以永远不会过期. 这条和
[architecture/09](../architecture/09-comments-and-docs.md) 里注释那条是同一条.

---

## `# pragma: no cover` 的判据

> **给这行写一个测试, 需要一个这台机器上没有的东西, 还是根本写不出有意义的断言?**

两者之一 -> 够格. 只是"懒得测" -> 不够格, 去写测试.

现在全仓库 24 处, 分四类:

| 类 | 处数 | 例子 |
| :--- | :--- | :--- |
| **真的够不到的外部依赖** | 9 | `boto_ses` `bedrock_model` (要 AWS), `self.agent` `chat()` (要真模型), `sync_sqlite_to_postgres` 的函数体和 dataset 里跑子进程那几个 (要真库/真文件) |
| **走不到的防御分支** | 8 | `config.new()` 的 `else: raise`, `raise NotImplementedError`, 驱动异常的兜底 `except`, `extractor.py` 里别的方言才走得到的分支 |
| `if T.TYPE_CHECKING:` | 5 | 四个 mixin 加 `quota.py`, 顶部那个只为类型检查存在的 import |
| 测试工具自身 | 2 | `pytest_cov_helper.py` (本来就被 omit 了) |

第二类值得单独说一句: **它们不是"测不了", 是"测了也没意义"** —— 一个为了将来加第三个部署
目标而留着的 `else: raise` 今天定义上就走不到, 给它编一个测试等于测试那句 `raise` 本身.
判断标准是"删掉这个分支会不会让代码更危险": 会 -> 留着并 pragma; 不会 -> 那它是死代码,
删掉而不是 pragma.

**pragma 不是覆盖率的挡箭牌, 是一句声明**: 这行代码的正确性只能靠真跑一次来证明. 所以每个
pragma 后面**应该跟一句为什么**, 像 `# pragma: no cover - needs AWS`. 现在 24 处里只有 6 处
写了, 剩下的靠上下文自明 —— 新加的时候请写上.

`.coveragerc` 另外 omit 掉两个目录: `agent_app/tests/*` (测试工具, 不是被测代码) 和
`agent_app/vendor/*` (拷进来的第三方). **`agent_app/dataset.py` 特意不 omit** —— 它虽然是
会被删掉的教学层, 但删之前它是真在跑的代码, 而且它写数据库.

---

## 有一条测试守着架构边界

```python
class TestNotOnTheProductionPath:
    def test_the_app_does_not_import_the_authoring_layer(self):
```

它用 AST 扫 `agent_app/one/*.py` 和 `ai_sdk_adapter.py` 的 import 语句, 确认没有任何一个
import 了 `agent_app.dataset`.

这条靠人自觉守不住: 总有一天有人想"启动时顺手检查一下数据库有没有数据吧", 而那一行 import
就把整个应用钉死在了教学层上, 删教学材料会把 app 一起删坏. 边界的完整论证在
[architecture/02](../architecture/02-teaching-and-production.md).

**这是一个模式, 不是一次性的**: 一条能被机械判断的架构约束, 值得写成测试而不是写成文档.
判断哪些约束够格, 见 [architecture/08](../architecture/08-what-guards-the-boundaries.md).

---

## `source_code.py` 是什么

`agent_app/source_code.py` 里只有一个 `add_two(a, b)`, 对应
`tests_python/test_source_code.py`. 它不参与任何业务, 是课程里讲 TDD 那一节的靶子.

**它属于教学层**, 擦教学痕迹时和它的测试一起删.
