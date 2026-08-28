# 前端为什么长这样

`app/`, `components/`, `lib/`, `data/` 各部分的设计说明. **代码里的注释只留工程上的 why 且
很短** (规矩见 [09-comments-and-docs.md](../architecture/09-comments-and-docs.md)), 展开的
内容在这里.

---

## 读法: 前两篇讲需求, 从 03 开始才是代码

这套文档是围绕**这个界面必须做到什么**组织的, 不是围绕目录结构. 先读 01 和 02 就能回答
"改这块要动哪里"; 03 之后才是代码走读.

```
需求
  01  这个界面是什么, 必须做到什么          两个页面, 两种读者
  02  屏幕上有哪些元素, 内容从哪来          一块一块对到 site.toml 的字段

代码 (按渲染路径, 从内容进来到画到屏幕上)
  03  data/ -> lib/site/ -> 组件            读盘, 构建期校验, server/client 边界
  04  app/ 的路由和三层壳                   layout, 分组, SEO
  05  首页                                  Hero + 能力卡 + 气泡 + 覆盖层
  06  agent 页                              空状态, 12 个按钮, 消息气泡
  07  Markdown 和块渲染器                    表格 / 流程图 / 图表 从哪来

横切
  08  设计 token                            配色一个文件, 圆角一条阶梯
```

---

## 索引

| 篇 | 讲什么 | 对应代码 |
| :--- | :--- | :--- |
| [01-what-the-ui-must-do.md](01-what-the-ui-must-do.md) | 两个页面服务两种读者, 四条硬要求, 以及**不做**什么 | 全部 |
| [02-the-elements.md](02-the-elements.md) | **每一块元素对到 `site.toml` 的哪个字段, 哪个组件画它** | `data/site.toml` |
| [03-content-pipeline.md](03-content-pipeline.md) | 为什么是 TOML, 两个构建期检查, 那次把文案内联进组件的事故 | `lib/site/`, `lib/icons.ts` |
| [04-pages-and-shell.md](04-pages-and-shell.md) | 路由分组, server/client 的线画在哪, SEO | `app/`, `lib/seo/` |
| [05-home-page.md](05-home-page.md) | 概念名读不懂怎么办, 气泡为什么会跑出屏幕 | `Hero`, `CapabilityCard`, `ConceptTooltip`, `BusinessContextModal` |
| [06-chat-page.md](06-chat-page.md) | 空状态放什么, 渲染徽章, 消息气泡里的三种内容 | `components/chat/*` |
| [07-markdown-and-blocks.md](07-markdown-and-blocks.md) | **分发点那一行, 以及为什么失败是正常路径** | `markdown.tsx`, `blocks/` |
| [08-design-tokens.md](08-design-tokens.md) | 改配色动哪里, 圆角阶梯, 没有暗色模式 | `tailwind.config.ts`, `globals.css` |

---

## 三条贯穿全部的规矩

**一, 组件里不出现业务文案.** 界面上说的每一句话都在 `data/site.toml` 里. 破坏它的代价见
[03](03-content-pipeline.md) 末尾那次事故 —— 欢迎语在屏幕上印了两遍, 而且没有任何东西报错.

**二, 读盘的往上放, 有状态的往下放.** `loadSite()` 碰文件系统, 所以只有 server component
能调它; 客户端组件通过 props 接收, 从不自己去读.

**三, 流式期间的失败是正常路径.** 每一次画图, 在收尾的围栏到达之前都必然有一段解析不了的
文本. 块渲染器解析不了就退回 `CodeBlock`, 这不是错误处理.

---

**渲染契约的完整规则** (提示词 / kickstart 配额 / 前端查找表三方怎么对上) 在
[architecture/06](../architecture/06-rendering-contract.md), 不在这里. 这里只回答"这段
TypeScript 为什么这么写".
