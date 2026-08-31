---
name: swap-dataset-cn
description: "换数据集的索引与路由: 这件事的全貌, 两个阶段各做什么, ref/ 里每篇文档管什么, 以及现在该敲哪条命令. 本身不含任何操作步骤 -- 那些在 /run-swap-dataset-phase-1-cn 和 /run-swap-dataset-phase-2-cn 里, 这两条命令会在开工前加载它当索引."
---

# 换数据集: 索引与路由

**这个 skill 不执行任何步骤, 也不含操作指南.** 它只回答两个问题:

1. 这件事的全貌是什么
2. 现在该敲哪条命令

**怎么一步步做**, 在两个 invoker 和它们各自指定的 `ref/` 文档里.

---

## 1. 这件事是什么

这个仓库的本质是三样东西: **一个提示词, 一个数据库, 一个网站**. 换数据集就是把这三样同时
换掉, 而且必须换得一致.

网站说自己是贷款分析, 提示词教的是医院排班, 数据库里躺着电商订单 —— 这种状态是能跑起来的.
它不报错, 它只是全程撒谎. 这就是整套流程存在的理由.

---

## 2. 两个阶段

| 阶段 | 命令 | 做什么 | 它会读的 `ref/` |
| :--- | :--- | :--- | :--- |
| 一 | `/run-swap-dataset-phase-1-cn` | 造库, 同步 PostgreSQL, 重写 `data/` 下的提示词/文案/业务说明 | `phase-1-cn.md`, `data-files-spec-cn.md`, `writing-style-cn.md`, `verification-cn.md`, `system-prompt-render-blocks.md` |
| 二 | `/run-swap-dataset-phase-2-cn` | 重新设计前端: 布局, 配色, 字体, 图表色板 | `phase-2-cn.md`, `verification-cn.md` |

**两个阶段之间有一道用户验收闸门.** 阶段一做完页面还穿着上一个行业的衣服, 那是预期结果.

### 为什么是两条命令而不是一个大 skill

被调用的 skill 作为**一条消息**留在对话里, 之后不会被重新读取; 而自动压缩每个 skill 只保留
**前 5,000 token**. 一个把两个阶段写在一起的 skill, 跑完阶段一通常已经压缩过, 排在文件末尾
的阶段二正是被截断的那一段 —— 于是用户说"开始改前端"的时候, 模型手里可能已经没有阶段二的
正文了, 只剩阶段一的残影.

拆开之后, 阶段二在真正需要它的那一刻**第一次完整进入上下文**.

同一个理由让阶段二**值得 `/clear` 之后再敲**: 阶段一结束时上下文已经被内容工作塞满, 清空
之后视觉设计能拿到一个干净的注意力. 该知道的东西全在文件里, 清掉不丢任何上下文.

---

## 3. `ref/` 里每篇管什么

| 文档 | 管什么 | 谁读 |
| :--- | :--- | :--- |
| [`ref/phase-1-cn.md`](ref/phase-1-cn.md) | 阶段一全流程, 十步, 含最后那段交接话术 | 阶段一 |
| [`ref/data-files-spec-cn.md`](ref/data-files-spec-cn.md) | `data/` 三个文件各自长什么样, 含渲染配额和 PostgreSQL 方言 | 阶段一 |
| [`ref/writing-style-cn.md`](ref/writing-style-cn.md) | 文案的口吻和格式规矩 (不许破折号, tooltip 怎么写) | 阶段一 |
| [`ref/system-prompt-render-blocks.md`](ref/system-prompt-render-blocks.md) | 要逐字抄进提示词的那五节原文 | 阶段一 |
| [`ref/phase-2-cn.md`](ref/phase-2-cn.md) | 阶段二全流程, 含力度边界和收尾交付 | 阶段二 |
| [`ref/verification-cn.md`](ref/verification-cn.md) | 全部验证脚本和判据 | **两个阶段** |

仓库本身的事实标准 (边界, 为什么这么设计) 在 `about-bi-agent-app-scaffold-cn` skill, 不在
这里.

---

## 4. 路由: 现在该敲哪条命令

> 这一节只在**用户直接敲了 `/swap-dataset-cn`** 时才用得上. 被两个 invoker 加载进来的话,
> 跳过它, 回去继续执行.

看仓库现在处在哪个状态:

```bash
ls dataset/
head -30 dataset/00-*summary*.md
grep -n "displayName\|tagline" data/site.toml
```

| 状态 | 敲这条 |
| :--- | :--- |
| `dataset/` 已经换成新数据集, `data/` 还是旧领域 | `/run-swap-dataset-phase-1-cn` |
| `data/` 和 `dataset/` 已经对上, 网站功能正常, 只是视觉还是旧的 | `/clear` 然后 `/run-swap-dataset-phase-2-cn` |
| `dataset/` 里还是当前这个数据集 | 都不是. 先把新数据集的六个文件放进 `dataset/` |

**给命令, 不要直接开工.** 那两条命令各自会加载自己那份完整剧本, 而这里没有剧本.
