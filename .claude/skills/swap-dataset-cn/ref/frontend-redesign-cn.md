# 阶段二: 重新设计前端

只有在用户确认阶段一没问题之后才做这一步. 两个阶段混着做, 效果不对时分不清是内容错了还是
样式错了.

---

## 先定调性, 再动手

调性从这个 App 的**行业观感**来, 不是从个人偏好来. 干这行的人每天盯着的屏幕长什么样? 交易
台是暗的, 医疗系统是冷白的, 行业刊物是纸白的.

**先用一句话把调性说出来, 再去挑颜色和构图.** 反过来做会得到一堆好看但互相不认识的色块.

调性至少要覆盖这四件事, 缺一件就等于没定:

| 维度 | 要说清什么 |
| :--- | :--- |
| 情绪 | 一个词. 稳重 / 锐利 / 温和 / 精密 |
| 底色 | 浅底还是深底. 这个仓库目前是浅底, 改成深底是一次完整的动作, 不是加几个 `dark:` |
| 主色 | 一个主色加一个强调色, 说清它为什么是这个行业的颜色 |
| 排版气质 | 字体的性格 (人文衬线 / 几何无衬线 / 等宽感), 以及标题和正文的对比度 |

定下来之后把那句话写成 `tailwind.config.ts` 顶上的注释: 下一个人需要知道的不是 `#0A1628`
是什么, 而是**为什么是深蓝的**.

---

## 必须真的加载那两个 skill

**不要凭记忆写"我觉得好看的配色".**

1. 用 Skill 工具加载 `frontend-design:frontend-design` (注意是带 plugin 前缀的全名), 按它
   给的规范做视觉方向, 排版和层级
2. 改图表配色那一步加载 `dataviz` skill, 按它的色板公式配 `--viz-*`, 并跑它自带的调色板
   validator

动手之前**用一句话告诉用户你要进入阶段二了, 并且明说你正在加载哪个 skill**. 用户看到的是
一堆 diff, 他需要知道你依据的是什么.

---

## 视觉相关的文件, 别只改首页

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

图标有两个来源: 从 lucide-react 挑现成的 (**记得同步注册进 `lib/icons.ts`**), 或者自己画
SVG 放进 `components/chat/icons/`. 后者适合行业特有的形状.

---

## 三样只许换色和组合, 不许重写

踩了不会报错, 所以单独列出来:

1. **`components/chat/` 那套对话** —— AI SDK 的传输, 流式, 草稿, 错误处理, 自动滚动.
   重写一遍就是重写一遍流式 bug
2. **`components/chat/blocks/` 和 `markdown.tsx`** —— 它们是一份跨前后端契约的一半, 另一半
   是 `data/system-prompt.md` 的 Rendering Triggers 表, `data/site.toml` 的 `render` 配额,
   和 Python 侧的 `normalize_render_blocks`. 自己写一套围栏分发, 会让 `mise run check` 一路
   全绿地校验一个已经不成立的承诺
3. **`ConceptTooltip` 和 `BusinessContextModal`** —— hover / focus / tap / Escape,
   `aria-describedby`, 焦点转移, 滚动锁. 重写一遍通常是重写坏一遍, 而且看不出来

---

## 两条容易踩的样式约束

**没有暗色模式, 所以不要写 `dark:` 变体.** `tailwind.config.ts` 里没有 `darkMode` 策略, 没
有主题切换开关, 没有任何地方给 `<html>` 加 `dark` 类. 一个开不出来的配色永远渲染不出来,
因此也永远无法被验证 —— 每个容器的 class 长一倍, 其中一半是没人能看见的猜测.

要做深色主题, 那是**换掉浅底本身** (改 `:root` 和 `colors` 的语义), 不是补 `dark:`.

**圆角用 Tailwind 自己的刻度, 不要在 `borderRadius` 里派生.** 现在的阶梯是: 行内 `sm`/默认,
小控件 `md`, 内嵌块 `lg`, 卡片 `xl`, 面板 `2xl`, 药丸 `full` —— 容器越大圆角越大, 嵌套时内圈
比外圈紧. 用 `calc(var(--radius) - 2px)` 那套派生会让 `rounded-lg` 和 `rounded-xl` 编译成
同一个值, 于是"内嵌块"和"卡片"这一层区分静默消失.

**`@layer components` 和 `@layer utilities` 保持是空的.** 用 `@apply` 攒一批 `.finance-card`
这样的语义类, 会产生两套讲同一件事的词汇, 而且没有任何东西能告诉你哪一套在某个组件上生效.
复用靠 React 组件, 不靠 CSS 类.

---

## 验收

```bash
npx next build
mise run check
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
