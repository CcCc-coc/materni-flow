# 阶段二: 重新设计前端

> 由 `/run-swap-dataset-phase-2-cn` 驱动. 前提是[阶段一](phase-1-cn.md)已经做完, 而且用户
> 明确说过功能没问题.

---

## 0. 这一阶段的力度: 重新设计, 不是换皮

**默认按大刀阔斧来.** 用户敲这条命令的意思是"给这个 App 一张属于它这个行业的脸", 不是
"把蓝色换成绿色".

允许并且**鼓励**做的:

- **重排首页布局.** 居中窄栏改成左右分栏, 四张能力卡改成带编号的清单或者时间线, 眼睛最先
  落在哪, 这些都可以重来
- **换整套配色和字体**, 包括从浅底换到深底 (那是一次完整的动作, 见下面的约束)
- **加这个行业特有的元素**: 一条状态流转的示意, 一组关键指标的排布, 一个这一行的人认得的
  视觉隐喻
- **重写 `Hero.tsx` 的结构**, 而不是只改它的 class

判断标准就一句: **换个颜色再把原来的卡片网格原样搬过来, 等于没做.** 构图本身要是从这个行业
里长出来的.

**但这不是"随便改".** 下面第 4 节那三样重写了会坏, 而且坏了不报错. 力度放在布局和视觉上,
不要放在那三样的内部实现上.

---

## 1. 先定调性, 再动手

调性从这个 App 的**行业观感**来, 不是从个人偏好来. 干这行的人每天盯着的屏幕长什么样? 交易
台是暗的, 医疗系统是冷白的, 行业刊物是纸白的, 播控室是黑的.

**先用一句话把调性说出来, 再去挑颜色和构图.** 反过来做会得到一堆好看但互相不认识的色块.

调性至少要覆盖这四件事, 缺一件就等于没定:

| 维度 | 要说清什么 |
| :--- | :--- |
| 情绪 | 一个词. 稳重 / 锐利 / 温和 / 精密 |
| 底色 | 浅底还是深底 |
| 主色 | 一个主色加一个强调色, 说清它为什么是这个行业的颜色 |
| 排版气质 | 字体的性格 (人文衬线 / 几何无衬线 / 等宽感), 以及标题和正文的对比度 |
| 构图 | 首页那四条业务主线**换成什么形状**. 这一条最容易漏 |

用 AskUserQuestion 给**两到三个方向**, 每个方向要**连色值带构图一起说清楚**, 而不是只给一句
形容词. 让用户挑.

定下来之后把那句话写成 `tailwind.config.ts` 顶上的注释: 下一个人需要知道的不是 `#0A1628`
是什么, 而是**为什么是深蓝的**.

---

## 2. 两个 skill 必须真的加载

**不要凭记忆写"我觉得好看的配色".**

1. `frontend-design:frontend-design` (带 plugin 前缀的全名) —— 视觉方向, 排版, 层级.
   **这一步在 invoker 里已经做过了**, 如果你是直接读到这篇文档的, 现在补上
2. `dataviz` —— 改图表配色那一步加载, 按它的色板公式配 `--viz-*`, 并跑它自带的调色板
   validator

---

## 3. 视觉相关的文件, 别只改首页

| 层面 | 文件 |
| :--- | :--- |
| 配色系统 | `tailwind.config.ts` 的 `colors`, `app/globals.css` 的 `:root` |
| 字体 | `app/layout.tsx` 里的 `next/font/google` (三个 CSS 变量) |
| favicon | `app/icon.png` |
| 导航栏 | `app/_components/layouts/Navigation.tsx` (logo 的两段式着色在这里) |
| 首页 | `app/(marketing)/_components/Hero.tsx`, `app/(marketing)/HomePageContent.tsx` |
| **能力卡与气泡** | `components/CapabilityCard.tsx`, `components/ConceptTooltip.tsx` |
| **业务说明弹窗** | `components/BusinessContextModal.tsx` (遮罩, 面板, 滚动条, Markdown 排版) |
| **chat 空状态** | `components/chat/overview.tsx` (标题 + 4 张能力卡) |
| **chat 输入区** | `components/chat/multimodal-input.tsx` (12 张 kickstart 卡片的排布), `components/chat/RenderBadge.tsx` (按钮上那个小图标) |
| **chat 对话气泡** | `components/chat/message.tsx` (AI 头像方块, 用户头像, 气泡配色) |
| **chat 顶部横幅** | `components/chat/chat.tsx` |
| 图表配色 | `app/globals.css` 的 `.viz-root` token |

**加粗的五行是最常被忘掉的.** 首页改得很漂亮而 chat 页还是旧配色, 是这一步最典型的失败.

图标有两个来源: 从 lucide-react 挑现成的 (**记得同步注册进 `lib/icons.ts`**, 否则
`mise run build-web` 直接失败), 或者自己画 SVG 放进 `components/chat/icons/`. 后者适合行业
特有的形状.

---

## 4. 三样只许换色和重新组合, 不许重写

第 0 节说了力度可以很大. **这三样是那个力度的边界**, 因为它们坏了不报错:

1. **`components/chat/` 那套对话** —— AI SDK 的传输, 流式, 草稿, 错误处理, 自动滚动.
   重写一遍就是重写一遍流式 bug. 换配色, 换气泡形状, 换排布都可以; 别碰它的状态逻辑
2. **`components/chat/blocks/` 和 `markdown.tsx`** —— 它们是一份跨前后端契约的一半, 另一半
   是 `data/system-prompt.md` 的 Rendering Triggers 表, `data/site.toml` 的 `render` 配额,
   和 Python 侧的 `normalize_render_blocks`. 自己写一套围栏分发, 会让
   `mise run check-content` 一路全绿地校验一个已经不成立的承诺
3. **`ConceptTooltip` 和 `BusinessContextModal`** —— hover / focus / tap / Escape,
   `aria-describedby`, 焦点转移, 滚动锁. 重写一遍通常是重写坏一遍, 而且看不出来.
   外观随便改, 那几条交互路径要原样留着

**还有一样不许动: `data/` 里的文案.** 那是阶段一的产物, 阶段二只改它长什么样, 不改它说什么.
真觉得某句话该改, 单独跟用户说, 不要顺手改掉.

---

## 5. 两条容易踩的样式约束

**要深色主题就换掉浅底本身, 不要补 `dark:` 变体.** `tailwind.config.ts` 里没有 `darkMode`
策略, 没有主题切换开关, 没有任何地方给 `<html>` 加 `dark` 类. 一个开不出来的配色永远渲染
不出来, 因此也永远无法被验证 —— 每个容器的 class 长一倍, 其中一半是没人能看见的猜测.

所以深色是**改 `:root` 和 `colors` 的语义**, 让浅底那套值直接变成深底那套. 这条完全在第 0
节允许的力度之内, 只是不要用 `dark:` 那条路走.

**圆角用 Tailwind 自己的刻度, 不要在 `borderRadius` 里派生.** 现在的阶梯是: 行内 `sm`/默认,
小控件 `md`, 内嵌块 `lg`, 卡片 `xl`, 面板 `2xl`, 药丸 `full` —— 容器越大圆角越大, 嵌套时内圈
比外圈紧. 用 `calc(var(--radius) - 2px)` 那套派生会让 `rounded-lg` 和 `rounded-xl` 编译成
同一个值, 于是"内嵌块"和"卡片"这一层区分静默消失.

**`@layer components` 和 `@layer utilities` 保持是空的.** 用 `@apply` 攒一批 `.finance-card`
这样的语义类, 会产生两套讲同一件事的词汇, 而且没有任何东西能告诉你哪一套在某个组件上生效.
复用靠 React 组件, 不靠 CSS 类.

---

## 6. 验收

```bash
mise run build-web
mise run check-content
mise run test
```

改图标名或删组件都可能把编译打断, 所以三条都要跑.

然后**亲眼看两个页面**:

- 首页: 卡片和面板浮在底色上, 没有陷进去; 最浅的那一档文字还读得见
- 四张能力卡的 tooltip: **hover / Tab 聚焦 / 手机点按三条路都要能弹出**, 窄屏下不跑出屏幕.
  首页和 agent 页**各看一遍** —— 两边渲染的是同一份 `[[capabilities]]`
- 业务说明弹窗: 遮罩, 滚动, Escape 关闭, 点面板内部**不**关
- 窄屏 (375px) 下整页不横向滚动
- agent 页: 让 agent 出一张表, 一张流程图, 一张图表. mermaid 和 chart 各自有底色, 确认没有
  哪一块还是旧配色

图表那三样尤其容易漏, 因为它们要等 agent 真的画出来才看得见.

改完交给用户看, 他有意见就继续改, 直到他满意.

---

## 7. 收尾与交付

用户对视觉也满意之后, 做完这四件事才算结束.

**一, 旧领域词汇扫描.** 词表是一次性参数, 不提交进仓库:

```bash
mise run check-content -- --retired "旧数据集最有辨识度的几个名词"
```

挑词要挑准 —— 拿 `node` 这种通用词去扫会报出一堆正常用词, 你会学会忽略这个检查.

**二, 清理上一个数据集在 PostgreSQL 上的残表.** 它们住在别的 schema 里, 新的同步永远不会
碰到, 所以会一直占着那个**和别的项目共用**的 500MB 配额而不发出任何声音.

先列出全库的 schema (脚本在 [`verification-cn.md`](verification-cn.md)), **把旧 schema 的
名字报给用户, 等他明确说删, 再删**. 那个库上还住着别的项目, 删错一个是不可逆的.

**三, 最后跑一次全套:**

```bash
mise run check-content
mise run test
mise run build-web
git status --short
```

`git status` 应该只落在这几处: `data/`, `dataset/`, `.env.defaults`, 视觉相关的
`app/ components/ lib/icons.ts tailwind.config.ts`, 以及阶段一 D 组那三个硬编码文件.
**落到别处就是信号**, 回去看一眼那是不是越界了.

**四, 给用户一段交付说明**, 讲清四件事:

- 换成了什么数据集, schema 名是什么, 多少张表多少行
- 视觉定的调性是什么, 一句话
- 还需要他自己做的事 (比如部署时要在 Vercel 面板里录 `.env` 那些密钥, 因为 `.env` 不进 Git)
- 旧 schema 删了没有

顺便提一句: 要把这个仓库作为作品集交付出去的话, **教学层是可以整块删掉的** (`README.md`,
`TICKET.md`, `docs/`, `.claude/skills/`, `dataset/`, `agent_app/dataset.py`,
`tests_python/test_dataset.py`, `scripts/`), 删完仍然是一个能跑的 app, 一行代码都不用改 ——
`mise.toml` 也一行不用动. **这件事要单独问用户, 不要顺手做掉.**
