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

### 它曾经是坏的, 值得记一笔

`tailwind.config.ts` 里原来有一段 shadcn 的覆盖:

```ts
borderRadius: {
  lg: "var(--radius)",              // --radius: 12px
  md: "calc(var(--radius) - 2px)",
  sm: "calc(var(--radius) - 4px)",
}
```

它把 `lg` 从 Tailwind 默认的 8px 顶到 12px —— **正好是 Tailwind 给 `xl` 的值**. 于是
`rounded-lg` 和 `rounded-xl` 在屏幕上完全一样, 而这两个类名一共用在 19 个地方. 写代码的人
随手挑哪一个看起来都对, 所以这条阶梯读起来像是随意的.

更麻烦的是它把我们自己的刻度**绑在了一个为 shadcn 设的变量上**: 谁改一下 `--radius`, 那 19
个站点会静默分成两拨.

而它并不服务任何东西 —— `components/ui/*` 里每一个 `rounded-md` 在调用点都被覆盖掉了. 所以
整段删掉了, `--radius` 也随之没了读者一并删除.

**教训**: 两个类名编译成同一个值, 就等于那一层区分不存在, 而代码还在假装它存在.

---

## 那个重复了 20 次的卡片外壳

`border border-slate-200` 在组件里出现 **20 次**. 按角色归类之后它们是自洽的 (上面那张圆角
表就是这么归出来的), 但其中有一个**逐字相同的壳**被写了 5 遍:

```
bg-white border border-slate-200 rounded-xl
```

出现在: chat 横幅, kickstart 上方的提示条, 输入框, agent 消息气泡, "Thinking" 气泡.

它们的 class 顺序一度有四种写法, 现在统一了, 所以 `grep "bg-white border border-slate-200
rounded-xl"` 能把它们全找出来. 顺序统一那次顺带发现了唯一一处真正的不一致: 提示条是 `p-3`
而横幅是 `p-4`, 而这两者互斥出现在同一个位置 —— 发出第一条消息时会跳 4px. 已经统一成 `p-4`.

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

它曾经是 306 行. 删掉的是上一个模板的遗物: `@layer components` 里 10 个零引用的类
(`.finance-card` `.finance-button` `.glass-card` `.kpi-card` `.feature-card` `.status-*`,
其中一个的注释还写着 "Bluevine style"), `@layer utilities` 里 4 个零引用的类, 以及约 25 个
零读者的 CSS 变量 —— 包括十个 `--sidebar-*`, 而这个 app 没有侧边栏.

---

## 没有暗色模式

没有主题切换按钮, 没有 `next-themes`, 没有任何地方给 `<html>` 加 `dark` 类, `tailwind.config.ts`
里也没有 `darkMode` 策略.

**这是一个决定, 不是遗漏.** 之前的状态是: 组件里散着 121 个 `dark:` 变体, `globals.css` 里
有一整块暗色调色板, 而它们**永远渲染不出来, 因此也永远无法被验证**. 每一个容器的 class 都
是双份长度, 其中一半是没人能看见的猜测.

要加回来的话, 那是一个明确的动作: 装 `next-themes`, 加一个切换开关, 然后逐屏过一遍暗色 ——
而不是在改别的东西时顺手补几个 `dark:`.

---

## 这个前端是从一个作品集模板改出来的

上面几处清理 (青色页脚, `.finance-*` 死类, sidebar 变量, `--radius` 覆盖, 未被使用的
`fontSize` / `animation` / `boxShadow` 配置) 都是同一个来历. 再看到类似的东西 —— 一个没有
读者的类, 一个和整站配色无关的色相, 一个 app 里不存在的组件的 token —— 先怀疑它是模板残留,
查一下引用数再决定.
