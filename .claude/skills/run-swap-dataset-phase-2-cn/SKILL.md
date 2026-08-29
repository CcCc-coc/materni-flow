---
name: run-swap-dataset-phase-2-cn
description: "换数据集的阶段二: 结合新数据集的行业调性重新设计前端. 允许并鼓励大刀阔斧地改布局, 配色, 字体, 并加入业务相关的元素, 前提是不动那三样重写了会坏的东西. 先加载 frontend-design 规范再动手. 用户敲 /run-swap-dataset-phase-2-cn 时执行."
argument-hint: "[可选: 圈定范围, 比如 导航栏保持现状]"
allowed-tools: Bash(mise run *) Bash(.venv/bin/python *) Bash(.venv/bin/agent-app *) Bash(pnpm exec *) Bash(git status *) Bash(git diff *) Bash(ls *) Bash(head *) Bash(grep *) Read Edit Write Glob Skill AskUserQuestion
---

# 执行: 换数据集 阶段二 (重新设计前端)

用户圈定的范围 (可能为空, 空就是不设限): $ARGUMENTS

---

## 第一件事, 现在就做: 加载设计规范

**在读任何别的东西之前**, 用 Skill 工具加载:

```
frontend-design:frontend-design
```

带 plugin 前缀的全名. 这一步不是可选的, 也不能靠回忆代替 —— 这一阶段的产出要按它的规范来,
不是按"我觉得好看的配色"来.

加载不到就停下来告诉用户: 这个 plugin 没装, 让他从官方 marketplace 装上再敲一次.

---

## 第二件事: 读剧本

用 Read 工具把这份文件整个读完:

```
.claude/skills/swap-dataset-cn/ref/phase-2-cn.md
```

它是阶段二的完整剧本: 力度边界, 定调性的方法, 文件清单, 三样不许重写的东西, 验收清单,
收尾交付. 照着它走.

改图表配色那一步再加载 `dataviz` skill, 跑它自带的调色板 validator.

---

## 力度: 重新设计, 不是换皮

**这是这一阶段最容易做错的地方, 所以放在最前面.**

用户敲这条命令的意思是"给这个 App 一张属于它这个行业的脸", 不是"把蓝色换成绿色". 默认按
**大刀阔斧**来:

- **重排首页布局.** 居中窄栏可以改成左右分栏, 四张能力卡可以改成带编号的清单, 时间线, 或者
  别的形状. 眼睛最先落在哪, 可以重来
- **换整套配色和字体**, 包括从浅底换到深底
- **加这个行业特有的元素**: 一条状态流转的示意, 一组关键指标的排布, 一个这一行的人认得的
  视觉隐喻
- **重写 `Hero.tsx` 的结构**, 而不是只改它的 class

判据一句话: **换个颜色再把原来的卡片网格原样搬过来, 等于没做.** 构图本身要是从这个行业里
长出来的.

如果上面 `$ARGUMENTS` 里用户圈了范围, 按他圈的来; 没圈就是不设限.

### 但有边界, 而且踩了不报错

剧本第 4 节那三样**只许换色和重新组合, 不许重写**:

1. `components/chat/` 那套对话的状态逻辑 (传输, 流式, 草稿, 自动滚动)
2. `components/chat/blocks/` 和 `markdown.tsx` 的围栏分发 —— 它是一份跨前后端契约的一半
3. `ConceptTooltip` 和 `BusinessContextModal` 的交互 (hover/focus/tap/Escape, 焦点转移,
   滚动锁)

外观随便改, 内部实现不要动.

**还有一样: `data/` 里的文案是阶段一的产物**, 这一阶段只改它长什么样, 不改它说什么.

---

## 顺序

1. 加载 `frontend-design:frontend-design` (上面第一件事)
2. 读 `ref/phase-2-cn.md`
3. 读 `data/site.toml` 和 `data/business-context.md`, 搞清楚这是个什么行业
4. **定调性, 用 AskUserQuestion 给两到三个方向让用户挑** —— 每个方向要连色值带**构图**一起
   说清楚, 只给形容词等于没给
5. 动手, 按剧本第 3 节那张表逐层改, 别只改首页
6. `mise run build-web` / `mise run check-content` / `mise run test`, 三条都跑
7. 亲眼看两个页面, 按剧本第 6 节那张清单验
8. 交给用户看, 有意见继续改
9. 用户满意之后走剧本第 7 节的收尾与交付

---

## 前提

这一阶段假设**阶段一已经做完并且用户验收过**: `data/` 已经是新领域, 网站功能正常.

如果打开 `data/site.toml` 发现文案还是上一个行业的, 说明阶段一没做或没做完 —— 停下来告诉
用户先敲 `/run-swap-dataset-phase-1-cn`.
