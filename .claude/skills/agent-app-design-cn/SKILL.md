---
name: agent-app-design-cn
description: 本仓库 agent app 的设计约定, 记录代码本身讲不清楚的取舍. 目前覆盖 /chat 页的渲染层 (Markdown 里的围栏代码块怎么分发到 Mermaid 等渲染器, 怎么一行开关). 改动 components/chat/ 下任何文件, 新增一种块渲染器 (Mermaid, chart), 或者要动 markdown 渲染逻辑之前先读.
paths:
  - components/chat/**
  - app/chat/**
---

# Agent App 设计约定

这里放的是 "为什么这么写", 不是 "代码在哪". 后者看 `CLAUDE.md`.

每份文档都是一条生效中的约定. 要么照做, 要么在改代码的同一个 commit 里改文档, 别让两边对不上.

按你要动的东西读对应那一份, 不要全读.

| 你在改 | 读 |
| :--- | :--- |
| /chat 页, 消息渲染, Markdown, Mermaid, 图表 | [ref/chat-frontend.md](ref/chat-frontend.md) |

新增文档就放进 `ref/`, 在上表加一行. 如果它覆盖的文件不在本文件 frontmatter 的 `paths` 里, 记得同步放宽, 否则编辑那些文件时 skill 不会自动加载.
