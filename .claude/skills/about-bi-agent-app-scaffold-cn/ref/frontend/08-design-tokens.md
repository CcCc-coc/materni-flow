# 配色, 圆角, 和那个重复了 20 次的卡片外壳

> 换数据集常常也要换一次视觉. 这篇讲改配色要动哪里 (一个文件), 圆角为什么是一条有名字的
> 阶梯, 以及这套样式里还留着的一处已知重复.

**对应代码**: `tailwind.config.ts`, `app/globals.css`

---

## 改配色 = 改一个文件

品牌色全在 `tailwind.config.ts` 的 `colors` 里, 组件写名字不写值:

| token | 值 | 用在哪 |
| :--- | :--- | :--- |
| `primary` | `#0A1628` | 品牌深蓝. 字标, 标题, 导航条底色, 用户气泡 |
| `brand` | `#2563EB` | 行动色. 链接, 发送键, CTA |
| `brand-dark` | `#1D4ED8` | 实心面上的 hover |
| `brand-light` | `#3B82F6` | focus ring, hover 描边 |
| `brand-soft` | `#60A5FA` | 更浅的 hover 描边 |
| `accent` | `#F59E0B` | 金色. 字标后半截, 导航高亮, 装饰短横 |

**中性色刻意不收进来**, 组件里直接写 Tailwind 原生的 `slate-*` / `white`. 两个理由: 它是每
个 React 开发者都认识的词汇表, 不需要学这个仓库的私有名字; 而且换品牌时中性色基本不动.

这些名字是从代码里读出来的, 不是设计出来的 —— 引入它们时**每个值都等于它替换掉的那个
Tailwind 色阶的原 hex, 所以一个像素都没变**.

---

## 圆角是一条有名字的阶梯

```
rounded-sm     2px    行内       图例色块
rounded        4px    行内       代码片段, 装饰短横
rounded-md     6px    小控件     图表 tooltip
rounded-lg     8px    内嵌块     代码块, 表格, 图表, 头像, 按钮
rounded-xl    12px    卡片       能力卡, kickstart 按钮, 气泡, 输入框
rounded-2xl   16px    面板       首页 CTA, agent 欢迎卡, 业务说明覆盖层
rounded-full   ∞      药丸       导航 CTA, 技术栈标签
```

**容器越大, 圆角越大**, 嵌套时内圈比外圈紧. 这条阶梯就是 Tailwind 自己的刻度, 没有任何
覆盖.

### 不要用一个变量去派生这条阶梯

shadcn 的脚手架会往 `borderRadius` 里塞这么一段:

```ts
borderRadius: {
  lg: "var(--radius)",
  md: "calc(var(--radius) - 2px)",
  sm: "calc(var(--radius) - 4px)",
}
```

**这个仓库不要它**, 两个理由:

**一, 它会撞车.** `--radius` 是 12px, 而 Tailwind 给 `xl` 的默认值也是 12px. 于是
`rounded-lg` 和 `rounded-xl` 编译成同一个值, 屏幕上完全分不开 —— 而这两个类名负担的是"内嵌
块"和"卡片"两层. **两个类名编译成同一个值, 就等于那一层区分不存在, 而代码还在假装它存在**:
写代码的人随手挑哪一个看起来都对, 阶梯读起来就是随意的.

**二, 它把刻度绑在一个不属于它的变量上.** 改一下 `--radius`, `rounded-lg` 的站点会动而
`rounded-xl` 的不会, 一套设计静默分成两拨.

而它并不服务任何东西: `components/ui/*` 里每一个 `rounded-md` 在调用点都被覆盖掉了. 所以
`borderRadius` 保持不扩展, 用 Tailwind 自己的刻度.

---

## 那个重复了 20 次的卡片外壳

`border border-slate-200` 在组件里出现 **20 次**. 按角色归类之后它们是自洽的 (上面那张圆角
表就是这么归出来的), 但其中有一个**逐字相同的壳**被写了 5 遍:

```
bg-white border border-slate-200 rounded-xl
```

出现在: chat 横幅, kickstart 上方的提示条, 输入框, agent 消息气泡, "Thinking" 气泡.

**这五处的 class 写法保持一致**, 顺序也一样, 所以 `grep "bg-white border border-slate-200
rounded-xl"` 能把它们全找出来. 顺序一旦各写各的, 差异就藏得住 —— 比如提示条用 `p-3` 而横幅
用 `p-4`, 这两者互斥出现在同一个位置, 发第一条消息时会跳 4px.

**没有把它抽成一个 `<Surface>` 组件**, 因为这 20 处里有几处的差异是有意的 (覆盖层要
`shadow-2xl`, 能力卡要 `cursor-help`, 输入框还要 focus 态), 硬收成一个组件会变成一堆 props,
反而更难维护. 等到真的改一次设计时, 哪些差异是有意的会自己显形, 那时候再收敛比现在猜准.

---

## `globals.css` 里剩下什么

92 行, 四块:

| 块 | 干什么 |
| :--- | :--- |
| `:root` | 三个字体变量, `--background` / `--foreground`, 以及 shadcn 那几个还有读者的 primitive |
| `@layer base` | 平滑滚动, body 字体和底色, 标题字体 |
| 滚动条 | `::-webkit-scrollbar` 四条规则 |
| `.viz-root` | 图表的颜色 token, 由 `blocks/chart/` 读, 见 [07](07-markdown-and-blocks.md) |

**`@layer components` 和 `@layer utilities` 都是空的, 这是有意的.** 用 `@apply` 攒一批
`.finance-card` / `.kpi-card` 这样的语义类是很自然的想法, 但它和 Tailwind 的写法并存时会产生
两套讲同一件事的词汇, 而且没有任何东西能告诉你哪一套在某个组件上生效. 这个仓库的选择是只用
一套: 组件里写工具类, 复用靠 React 组件而不是 CSS 类.

---

## 没有暗色模式

没有主题切换按钮, 没有 `next-themes`, 没有任何地方给 `<html>` 加 `dark` 类, `tailwind.config.ts`
里也没有 `darkMode` 策略.

**这是一个决定, 不是遗漏**, 所以组件里也不该出现 `dark:` 变体. 一个开不出来的配色**永远
渲染不出来, 因此也永远无法被验证**: 每个容器的 class 长一倍, 其中一半是没人能看见的猜测,
而它会在有人真的打开暗色的那天集中爆出来.

要支持暗色的话, 那是一个完整的动作: 装 `next-themes`, 加一个切换开关, 然后逐屏过一遍 ——
而不是在改别的东西时顺手补几个 `dark:`.

---

## 这个前端是从一个作品集模板改出来的

所以在这两个文件里看到**说不出用途的东西**时 —— 一个没有读者的类, 一个和整站配色无关的
色相, 一个这个 app 里根本不存在的组件的 token (比如侧边栏) —— 先查引用数, 大概率是模板残留
而不是有人特意留的.

反过来也成立: **往这两个文件里加东西之前先确认它有读者.** 一份没人读的 theme 会被当成设计
系统, 而它不是.
