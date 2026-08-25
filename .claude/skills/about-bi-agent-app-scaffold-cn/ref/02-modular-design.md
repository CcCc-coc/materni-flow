# 模块化设计: 为了让"换一个领域"变成一件小事

## 这篇讲什么

[01](01-what-this-project-is.md) 说这个脚手架能在 1 到 2 小时里换掉整个业务领域. 这篇讲
为了让那件事成立, 代码被切成了什么样.

**读法上的一个提醒**: 下面写到的具体路径是**当前的**, 重构会改动它们. 真正要记住的是
每一节的**边界和理由** —— 边界为什么划在这里, 破了会怎样. 路径变了就改这篇文档, 理由
基本不会变.

---

## 0. 一条总原则

> **随数据集变的东西, 和随脚手架不变的东西, 必须分开存放.**

变的部分要能被整体替换, 不变的部分在替换时一行都不该动. 下面五节是这条原则在五个地方
的具体落法.

判断一个新东西该放哪, 就问一句: **换个业务领域, 它要不要改?** 要改 -> 归数据集; 不改 ->
归脚手架. 答案是"看情况"的, 说明它其实是两个东西粘在一起了, 先拆开再放.

---

## 1. 数据分离: 所有会变的东西, 一个目录

```
data/
├── dataset.toml          后端读: PostgreSQL schema 名, 建表顺序
├── site.toml             前端读: 界面上说的每一句话
├── business-context.md   首页那个"这解决什么问题"弹窗的正文
├── system-prompt.md      agent 的领域大脑
└── data.sqlite.example   数据本体的种子
```

**换数据集 = 重写这一个目录.** 这是整个设计里最重要的一条边界.

它以前不是这样: 配置在 `config/`, 提示词在 `agent_app/prompts/`, kickstart 问题在
`data/`, 数据库种子在仓库根目录. 四个地方, 而且和脚手架代码混在一起. 那种布局下, 一次
替换是一个散落全仓库的 diff, 没有人能一眼确认"改全了没有".

唯一的例外是**写操作的 `@tool`**: 它在 `agent_app/one/one_04_agent.py` 里, 因为那是代码
不是内容. 一个数据集需要写操作时, 在那里加方法.

### 按读者切, 不按主题切

`dataset.toml` 只有 Python 读, `site.toml` 只有 TypeScript 读. 它们曾经是同一个文件, 而
那个文件其实是两份不相关的配置钉在一起 —— 两个运行时读的 key 集合完全不重叠.

所以规矩是: **加一个值之前, 先问哪个运行时消费它.** 如果答案是"两个都要", 把这件事说
出来, 因为今天没有任何一个值是这样.

---

## 2. 前端配置: 一份契约, 加载时校验

`site.toml` 是 TOML 而不是 TypeScript, 这是一个**有代价的选择**, 值得说清楚.

它以前是 `config/site.ts`, 编译器免费帮你查字段和图标名. 改成 TOML 丢掉了这个, 换来的是
"数据集的全部产出集中在一个目录". 权衡的结论是后者更重要: 编译期检查是在**写的时候**
帮你, 而目录集中是在**每一次替换和每一次 review** 时帮你.

丢掉的检查没有消失, 它们搬到了加载时 (`lib/site/`):

| 文件 | 干什么 |
| :--- | :--- |
| `lib/site/schema.ts` | `SiteConfig` 类型 + `REQUIRED_SITE_KEYS` 必填清单 |
| `lib/site/load.ts` | 解析 TOML, 查必填 key, 查图标名, 两者都 throw |

**两个检查都在 `next build` 时真的会拦住构建** —— 少一个 key 会报出 key 名, 图标名拼错会
报出坏名字和全部合法名字. 所以换完数据集必须跑一次 `npx next build`, 光跑
`mise run check` 查不到这两样.

`load.ts` 是 **server only** (读文件系统), 所以 `site` 是在 server component 里加载, 然后
**当 props 传进 client component** 的. 这不是麻烦, 是边界: client 组件不许自己去读配置,
它只能接收.

---

## 3. 首页模块化: 同一份内容, 两处渲染

首页和 agent 页展示的是**同一组四条业务主线**, 来自 `site.toml` 里唯一的一份
`[[capabilities]]`, 由共享组件渲染:

```
components/CapabilityCard.tsx     一条业务主线, 首页和 chat 页共用
components/ConceptTooltip.tsx     概念名背后那段白话解释的气泡
components/BusinessContextModal.tsx  把 business-context.md 渲染成弹窗
```

**这里有一个真实教训值得记住.** 它曾经是两份配置: `home.capabilities` 和 `chat.insights`,
各写各的. 结果它们已经漂移了 —— 同一条主线在首页叫 "Portfolio Concentration", 在 agent
页叫 "Portfolio Health", 图标不一样, tooltip 只有一边有. 没有任何测试失败, 因为两边各自
都是合法的.

**一份数据两处渲染, 漂移在结构上就不可能发生.** 一份数据两份配置, 漂移是迟早的事.

`BusinessContextModal` 走的是 chat 页那个同一个 Markdown 渲染器, 所以
`business-context.md` 里写 ` ```mermaid ` 围栏就真的会画出图, 而且自动享有懒加载和
`securityLevel: "strict"`. 弹窗组件本身完全不知道"图"这个概念的存在.

---

## 4. chat 模块化: 围栏块的查找表

agent 说的每句话都是流式文本, 页面上看到的几乎所有东西 —— 表格, 流程图, 图表, 高亮的
SQL —— 都是从那段文本渲染出来的. 开关是一张查找表:

```typescript
// components/chat/blocks/index.ts
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
  chart: ChartBlock,
}
```

**加一行支持一种块, 删一行关掉一种.** 没在表里的语言全部落到 `CodeBlock` 兜底.

这里的模块边界有一个容易被忽略的部分: **前端认得一个格式, 不等于模型会输出它.** 所以
"加一种块"是三步, 第三步在后端:

1. 写渲染器组件
2. 在查找表里加一行
3. **在 `data/system-prompt.md` 里告诉 agent 什么时候产出这种块**

跳过第三步的结果是渲染器一行代码都跑不到, 而前端测试全绿.

同一份契约还有第三半: `site.toml` 里那 12 条 kickstart 问题, 每条带一个 `render` 字段和
一句触发短语. `mise run check` 双向校验它们. 细节见 [04-rendering-contract.md](04-rendering-contract.md).

---

## 5. 后端模块化: 包名本身就是承诺

Python 包叫 `agent_app`, 不叫 `smb_lending_anything`. 这个名字是故意起得通用的, 它的含义
是一句承诺: **换数据集时, `agent_app/` 下面一行都不用改.**

支撑这句承诺的是几层拆分:

| 位置 | 职责 |
| :--- | :--- |
| `agent_app/paths.py` | 所有路径, 集中一处. 路径是源码树的事实, 所以不进配置 |
| `agent_app/project_config.py` | 读 `data/dataset.toml` 的类型化入口 |
| `agent_app/config/` | 读 `.env` 的密钥和凭据. **和上一行完全不同的东西** |
| `agent_app/one/one_0*.py` | 按关注点切开的 mixin: 配置, 数据库, boto3, agent |
| `agent_app/sql_utils.py` | 纯函数, 拿 `engine` 当第一个参数, 不依赖类 |
| `agent_app/db_schema/` | 把库结构编码成 LLM 好读的紧凑格式 |

### 两种"config"绝不能混

这是后端最容易搞错的一处:

| | `data/dataset.toml` | `.env` -> `agent_app/config/` |
| :--- | :--- | :--- |
| 装什么 | 项目身份, schema 名, 建表顺序 | API key, 数据库密码, LLM provider |
| 随什么变 | **数据集** | **机器** |
| 进 Git 吗 | 进 | 不进 |

判据是一句话: **它会因为换一台机器而不同吗?** 会 -> `.env`; 不会 -> `dataset.toml`.
一个值不能两边都有, 哪怕用环境变量做"逃生舱"也不行 —— 那等于给它两个家, 迟早两个答案.

### 通用代码里不许出现本数据集的例子

在 `agent_app/` 或 `scripts/` 里写注释举例时, 不要用当前数据集的表名. 写
`# e.g. the "loan" table` 这种例子, 等于把这个数据集焊进了通用代码 —— 换数据集之后它
不报错, 不失败, 只是变成一句谎话躺在那里.

用永远虚构的占位领域 (`acme` / `widget` / `part`), 它们不属于任何真实数据集, 所以永远
不会过期.

---

## 6. 数据库: 用 schema 隔离, 不用表名前缀

线上是一个 Neon PostgreSQL 实例, 多个项目共用. 隔离靠的是 **PostgreSQL schema**, 表名两边
完全一样:

```
本地 SQLite 种子        远程 PostgreSQL
loan            ->      schema fintech_smb_lending_pipeline_medium 里的 loan
```

**表名一致是这里的全部设计目标.** 早先的做法是给表名加前缀 (`smbll_loan`), 它失败在一个
致命的地方: agent 看到的表名取决于背后是哪个引擎, 于是提示词里每一段 SQL 例子在一个环境
对, 在另一个环境错, 而且没有任何东西会报错.

同一个理由还导致了另一条边界: **agent 在任何环境下读的都是 PostgreSQL, 本地也一样.**
以前本地读 SQLite 线上读 PostgreSQL, 结果每段提示词 SQL 都是对着 SQLite 写的, 发到线上
`strftime` / `JULIANDAY` / `ROUND(double precision, int)` 全不存在. 回头验过一次: **16 段
例子里 6 段在 PostgreSQL 上跑不通**, 而线上从来没崩过 —— agent 的 SQL 工具把数据库报错
转成字符串还给模型, 症状只是答案变差.

SQLite 没有消失, 它是**种子和同步源**: `data/data.sqlite.example` -> `tmp/data.sqlite` ->
`mise run sync-db` 发布进 PostgreSQL schema.

---

## 7. 边界靠什么守住

模块化设计不会自己维持, 它要么被机械检查守住, 要么慢慢烂掉. 现在守着的是三条命令:

```bash
mise run check     # 建表顺序 / 提示词表名 / 内容文件 / kickstart 渲染配额
mise run test      # Python 单元测试
npx next build     # site.toml 的必填 key 和图标名, 只有这里查得到
```

每一项具体拦住什么, 机械检查盖不住的部分怎么人工验, 以及"什么该自动检查什么不该"的判据,
全在 [06-what-guards-the-boundaries.md](06-what-guards-the-boundaries.md).

---

## 8. 重构时请守住的东西

这一节是给**接下来那次重构**看的. 路径可以改, 下面这些边界不要破:

1. **`data/` 是一个整体.** 别把某个数据集相关的文件挪回代码树, 也别把脚手架代码放进 `data/`.
2. **`agent_app/` 换数据集时一行不改.** 任何让它需要改的设计, 都是把数据集焊进了代码.
3. **两种 config 不合并.** 密钥和数据集身份是两件事.
4. **一份数据, 多处渲染.** 别为了"这个页面稍微不一样"复制一份配置.
5. **渲染契约的三半要一起动.** 渲染器 / 提示词 / kickstart 配额, 改一个就得改另外两个.
6. **通用代码里不出现真实表名.**
7. **改了结构就改这篇文档**, 在同一个 commit 里.
