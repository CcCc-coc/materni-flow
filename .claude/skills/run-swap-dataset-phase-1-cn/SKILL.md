---
name: run-swap-dataset-phase-1-cn
description: "换数据集的阶段一: 造库, 同步 PostgreSQL, 照着 dataset/ 里的新数据集重写 data/ 下的提示词, 全部界面文案和业务说明. 做完停下来让用户验收, 视觉留给阶段二. 用户敲 /run-swap-dataset-phase-1-cn 时执行."
argument-hint: "[可选: 额外的要求或限制]"
allowed-tools: Bash(mise run *) Bash(.venv/bin/python *) Bash(.venv/bin/agent-app *) Bash(pnpm exec *) Bash(git status *) Bash(git diff *) Bash(ls *) Bash(head *) Bash(grep *) Read Edit Write Glob Skill AskUserQuestion
---

# 执行: 换数据集 阶段一 (换内容)

用户的额外要求 (可能为空): $ARGUMENTS

**这份 invoker 本身不是执行依据.** 它只规定开工前的装载顺序. 真正照着做的是下面第二步读进来
的那几份文档.

---

## 第一步: 加载索引

用 Skill 工具加载:

```
swap-dataset-cn
```

它是这件事的索引: 全貌是什么, 两个阶段各做什么, `ref/` 里每篇文档管什么. **它不含操作步骤**,
所以读完它你还不知道怎么做 —— 那是第二步那几份文档的事.

它最后那节"路由"是给"用户不知道该敲哪条命令"准备的. **你是被这条命令叫起来的, 跳过它**,
直接回到这里往下走.

---

## 第二步: 读这四份文档

下面的 `${SKILLS_DIR}` 指**这个仓库放 skill 的那个目录**, 按工具不同:

| 工具 | `${SKILLS_DIR}` |
| :--- | :--- |
| Claude Code | `.claude/skills` |
| Codex / Antigravity | `.agents/skills` |

**它不是一个会被自动替换的变量, 是要你自己解析的占位符.** 拿不准就先
`ls .claude/skills .agents/skills 2>/dev/null` 看哪个存在.

用 Read 工具读, 一份都不能跳:

| 顺序 | 文档 | 什么时候用得上 |
| :--- | :--- | :--- |
| 1 | `${SKILLS_DIR}/swap-dataset-cn/ref/phase-1-cn.md` | **完整剧本**, 十步. 现在就整个读完 |
| 2 | `${SKILLS_DIR}/swap-dataset-cn/ref/data-files-spec-cn.md` | 第 5 步写 `data/` 三个文件时 |
| 3 | `${SKILLS_DIR}/swap-dataset-cn/ref/writing-style-cn.md` | 第 5 步写文案时 |
| 4 | `${SKILLS_DIR}/swap-dataset-cn/ref/verification-cn.md` | 第 4 步和第 7 步验证时 |

第 1 份**现在必须整个读完**, 它是接下来一切动作的依据. 后三份可以等走到对应步骤再读, 但
**别等到写完了才回头对规范** —— 那时候改的成本已经产生了.

还有第五份 `${SKILLS_DIR}/swap-dataset-cn/ref/system-prompt-render-blocks.md`, 它是要**逐字
抄进提示词**的原文, 不是读来理解的. 走到第 5 步推导链的第 1 小步时再打开, 整段复制过去只换
里面的例子.

**阶段二那份 `ref/phase-2-cn.md` 现在不要读.** 这一阶段不碰视觉, 提前读只会稀释注意力.

---

## 第三步: 从剧本的第 0 步开始执行

先按它的第 0 步跟用户打招呼 (说清两个阶段, 报一次自己的模型, 不够格就停下来), 然后一步步
往下走到第 9 步.

### 这一阶段在做什么 (地图, 不是执行依据)

```
0 开场白与模型自检            5 推导链: 提示词 -> kickstart -> 文案 -> 业务说明 -> 硬编码
1 预检: 仓库现在健康吗        6 完备性核对表
2 认输入: dataset/ 换了吗     7 验证: 三条命令 + SQL 真库跑一遍 + 数据体检
3 问用户: 文档里没有的        8 自己先跑一遍网站
4 建库并同步到 PostgreSQL     9 闸门: 交给用户验收, 并交接到阶段二
```

### 三条纪律, 剧本里会展开

**第一条是铁律, 这一阶段的质量全押在它上面:**

> **提示词定义能力边界. 下游只能换措辞, 不能新增一项提示词没教的能力.**

kickstart 问题, 能力卡, tooltip, 首页文案, 业务说明的"能问什么", 全部是
`data/system-prompt.md` 的**改写**, 不是数据集源文档的**再解读**. 想让首页出现某个分析, 唯一
的合法路径是**先把它写进提示词**.

绕开它的方式很自然, 而且**所有检查都会通过**: 12 条 kickstart 直接照着数据集源文档写, 于是
按钮里混进几条提示词根本没覆盖的分析. 问法合法, 配额也对, 只有用户点下去的时候模型才开始
即兴发挥.

另外两条:

- **`.env` 一个字都不许读也不许改.** 它装的是密钥. 要改的那一行在 `.env.defaults`
- **视觉一律不碰.** 配色, 字体, 布局全是阶段二的事. 这一阶段做完页面还穿着上一个行业的衣服,
  那是**预期结果**, 不是没做完

---

## 结束方式是固定的

阶段一不以"我做完了"结束, 而是以**一段把用户送进阶段二的交接**结束. 剧本最后一节
"交接: 给用户一条命令, 不要给一句口令"规定了那段话必须说到哪三件事. **照那一节写, 不要自由
发挥** —— 少说一件, 阶段二就会退化成一次配色微调.

用户没有明确说功能满意之前, 不要发那段交接.
