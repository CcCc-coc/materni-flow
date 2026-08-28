# 叶子: 路径, 词汇, 小工具

> 三个零依赖的模块, 别的模块都从这里取东西, 它们谁也不取. 共同的规矩只有一条:
> **只放第二个模块也要用的东西** —— 只有一个读者的, 属于那个读者旁边.

**对应代码**: `agent_app/paths.py`, `agent_app/constants.py`, `agent_app/utils.py`

**依赖**: 无. 这是依赖图的底.

---

## paths.py: 路径是源码树的事实, 不是配置

所有路径集中一处, 别处一律写 `path_enum.your_new_path`.

**为什么不进配置**: 换数据集重写的是 `data/` 里那些文件的**内容**, 从来不是文件名. 曾经
把系统提示词的路径放进配置, 结果什么也没换来, 还造成了 `paths` 和读配置的模块之间的循环
import.

**数据集相关的路径不在这里.** 它们的文件名属于数据集, 所以是 discover 出来的, 代码在
`agent_app/dataset.py` —— 那个模块整体是教学层, 会被删掉. `paths.py` 只放**这个源码树自己
的事实**.

**不要投机性地加条目.** 一个没有读者的路径会悄悄烂成一个指向不存在目录的指针 —— 这个仓库
真发生过: `dir_unit_test` / `dir_int_test` / `dir_load_test` 指向 `tests/`, `tests_int/`,
`tests_load/` 三个根本不存在的目录 (实际是 `tests_python/`), 而 `dir_prompts` 那一族指向
早已搬走的 `agent_app/prompts/` —— `instruction_content` 只要被读一次就是
`FileNotFoundError`. 全部零引用, 所以从来没人发现.

---

## constants.py: 只放第二个模块也要用的东西

**一个只有一个读者的常量, 属于那个读者旁边**, 不属于这里. `TAB` 曾经在这, 但只有
`db_schema/encoder.py` 用它, 而且它是那个编码器的排版细节, 已经下沉过去了.

现在装两族互不相关的东西, 放在一起只是因为这个文件是零依赖叶子:

- `LlmProviderEnum` + `DEFAULT_MODEL_ID` —— `config.py` 和 `one_04_agent.py` 读
- `LLMTypeEnum` / `LLMColumnConstraintEnum` / `TableTypeEnum` / `DbTypeEnum` ——
  `db_schema/` 和 `one_02_db.py` 读

按"按读者切"的原则第二族可以下沉进 `db_schema/`, 目前没做.

### 那几个 model ID 会过期

`DEFAULT_MODEL_ID` 是一份快照, **不是永久事实**. 各家厂商按自己的节奏发布, 改名, 下线模型.
碰到 "unknown model" / "model not found" 时先去查那家当前的模型列表, 别先debug 别的地方;
一次性的替换用 `.env` 里的 `LLM_MODEL_ID` 覆盖, 不要改这个 dict.

---

## utils.py: 同一条规矩

现在只有两个:

- `debug()` —— 打到 **stderr 而不是 stdout**. Vercel 上 stdout 是响应流的一部分, 打到那里
  的东西会流进浏览器. 同一个理由让 [09](09-http-entry-point.md) 在调 agent 时把 stdout 顶掉.
- `match()` —— include/exclude 的通配符/正则匹配, `db_schema/extractor.py` 用它把某张表
  挡在 agent 视野之外而不用从库里删掉. 正则编译带 `lru_cache`, 因为 schema 反射时每张表都
  要拿同一批 pattern 匹配一次.

`dedent()` 曾经在这, 零引用, 而且它只是 `textwrap.dedent(x).strip()` 的一层包装, 已删.
