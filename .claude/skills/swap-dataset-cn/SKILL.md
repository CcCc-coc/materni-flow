---
name: swap-dataset-cn
description: "换数据集这件事的知识库和路由. 真正执行分两条命令 -- /run-swap-dataset-phase-1-cn 换内容, /run-swap-dataset-phase-2-cn 换视觉. 直接敲 /swap-dataset-cn 会告诉你现在该走哪一条."
---

# 换数据集

这个仓库的本质是三样东西: **一个提示词, 一个数据库, 一个网站**. 换数据集就是把这三样同时
换掉, 而且必须换得一致.

网站说自己是贷款分析, 提示词教的是医院排班, 数据库里躺着电商订单 —— 这种状态是能跑起来的.
它不报错, 它只是全程撒谎. 所以工作方式不是"看到哪改哪", 而是**先建立完整映射, 再按固定
顺序执行, 最后靠工具验证**.

---

## 这个 skill 本身不执行, 它只指路

真正干活的是两条命令. **这不是为了好看, 是因为一次性把两个阶段的正文都灌进上下文会让第二
个阶段丢掉**: 被调用的 skill 作为一条消息留在对话里, 而自动压缩每个 skill 只保留**前 5,000
token**. 阶段一跑完通常已经压缩过, 排在文件末尾的阶段二正是被截断的那一段.

拆成两条命令, 阶段二就在真正需要它的那一刻**第一次完整进入上下文**, 而且它的 invoker 会在
干活之前先把 `frontend-design` 规范加载进来.

| 敲这条 | 做什么 |
| :--- | :--- |
| `/run-swap-dataset-phase-1-cn` | 造库, 同步 PostgreSQL, 重写 `data/` 下的提示词/文案/业务说明 |
| `/run-swap-dataset-phase-2-cn` | 重新设计前端: 布局, 配色, 字体, 图表色板 |

**两条之间隔着一道用户验收闸门, 不能跳.** 混着做, 一旦效果不对, 分不清是内容错了还是样式
错了.

**阶段二强烈建议 `/clear` 之后再敲.** 阶段一结束时上下文已经被内容工作塞满, 清空之后视觉
设计能拿到一个干净的注意力. 该知道的东西全在文件里, 清掉不丢任何上下文.

---

## 现在该走哪一条

用户直接敲了 `/swap-dataset-cn` 的话, 先判断他在哪一步, 再把对应的命令给他:

| 情况 | 告诉他敲 |
| :--- | :--- |
| `dataset/` 已经换成新数据集, `data/` 还是旧领域 | `/run-swap-dataset-phase-1-cn` |
| `data/` 和 `dataset/` 已经对上, 网站功能正常, 只是视觉还是旧的 | `/clear` 然后 `/run-swap-dataset-phase-2-cn` |
| `dataset/` 里还是当前这个数据集 | 都不是. 先把新数据集的六个文件放进 `dataset/` |

判断方法:

```bash
ls dataset/
head -30 dataset/00-*summary*.md
grep -n "displayName\|tagline" data/site.toml
```

---

## 文档

阶段一和阶段二的完整流程各自一篇, 由对应的 invoker 加载. 其余四篇是它们共用的规范, 用到
再读:

| 文档 | 讲什么 |
| :--- | :--- |
| [`ref/phase-1-cn.md`](ref/phase-1-cn.md) | **阶段一全流程**, 十步, 含最后那段交接话术 |
| [`ref/phase-2-cn.md`](ref/phase-2-cn.md) | **阶段二全流程**, 含力度边界和收尾交付 |
| [`ref/data-files-spec-cn.md`](ref/data-files-spec-cn.md) | `data/` 三个文件各自长什么样 |
| [`ref/writing-style-cn.md`](ref/writing-style-cn.md) | 文案的口吻和格式规矩 |
| [`ref/verification-cn.md`](ref/verification-cn.md) | 全部验证脚本和判据 |
| [`ref/system-prompt-render-blocks.md`](ref/system-prompt-render-blocks.md) | 逐字抄进提示词的那五节 |

仓库本身的事实标准 (边界, 为什么这么设计) 在 `about-bi-agent-app-scaffold-cn` skill, 不在
这里.
