# 首页: 把一个外行带到能提第一个问题的位置

> 首页只有一个真正的组件 (`Hero`), 但它身后挂着三个各自解决一个具体问题的小件:
> **概念名读不懂**, **一段话装不下一门生意**, **两列布局下气泡会跑出屏幕**.

**对应代码**: `app/(marketing)/_components/Hero.tsx`, `HomePageContent.tsx`,
`components/CapabilityCard.tsx`, `components/ConceptTooltip.tsx`,
`components/BusinessContextModal.tsx`

**依赖**: [03](03-content-pipeline.md) 的 `SiteConfig`, [07](07-markdown-and-blocks.md) 的
`Markdown` (覆盖层用它渲染业务说明).

---

## 组件树

```
page.tsx (server)  loadSite() + loadBusinessContext()
  └ HomePageContent (client)   页面底色 + 页脚
      └ Hero (client)          入场动画 + 全部内容
          ├ CapabilityCard × 4
          │   └ ConceptTooltip     解释气泡
          └ BusinessContextModal   覆盖层
```

---

## 入场动画: 一个 state, 一串 delay

`Hero` 里 `useState(false)` + `useEffect(() => setIsVisible(true))`, 各段用
`delay-100` / `delay-300` / `delay-500` / `delay-700` 错开.

**这是 CSS 过渡, 不是动画库.** 值得记一笔: chat 页用的是 framer-motion, 而 framer-motion
靠 `requestAnimationFrame` 驱动 —— 在一个 `document.visibilityState === "hidden"` 的标签页
里 (比如无头浏览器截图), 它的元素会**停在 `initial` 状态永远不显示**. 首页这套不受影响,
因为最终状态是靠 class 切换到位的.

---

## `CapabilityCard`: 一份数据, 两处渲染

首页和 agent 页展示的是**同一组四条业务主线**, 同一个组件, 只差一个 `compact` 开关 (agent
页地方小). 为什么必须是一个组件而不是两个, 见 [02](02-the-elements.md) 末尾那段漂移事故.

卡片底部那条**虚线短横**不是装饰: 它是唯一在告诉读者"这里有东西可以 hover"的东西. 去掉它,
那个提示就是隐形的.

---

## `ConceptTooltip`: 三种打开方式, 一个定位难题

**为什么自己写而不是装一个库**: 这个 app 没有任何 tooltip 基础设施, 而一个非交互的提示气泡
不值得引入一个定位库.

### 三种打开方式

hover 是显而易见的那种, 也是**手机用户和键盘用户都用不了**的那种. 所以:

| 入口 | 事件 |
| :--- | :--- |
| 鼠标 | `onMouseEnter` / `onMouseLeave` |
| 键盘 | `onFocus` / `onBlur`, 触发器带 `tabIndex={0}` |
| 触屏 | `onClick` 切换 |
| 关闭 | 额外监听 `Escape` |

触发器用 `aria-describedby` 指向气泡, 这是 ARIA 的 tooltip 模式: 描述会和它所描述的东西
**一起被读出来**, 而不是孤零零地留在阅读顺序的后面某处.

### `align` 这个 prop 解决的是什么

手机上卡片是两列, 而气泡比卡片宽. 居中对齐在宽屏上是对的, 在手机上会让外侧那一列的气泡
**跑出屏幕**. 所以外侧的卡片让气泡贴着自己的外边缘挂:

```tsx
align={index % 2 === 0 ? "start" : "end"}
```

`md` 以上网格开到四列, 有地方了, 两个值都回退成居中.

气泡带 `pointer-events-none`: 它绝不能挡在指针和卡片之间, 否则鼠标穿过气泡离开卡片时会
闪烁着关掉又打开.

---

## `BusinessContextModal`: 一段话装不下一门生意

首页能承载一个标题和一段话. 它承载不了一整个行业, 而一个不懂这行的读者**没有办法判断 agent
的答案是干什么用的**. 这个覆盖层放的是补上那个缺口的两三屏, 而且不用占一个路由, 也不会把
行动召唤挤到折叠线以下.

### 三个细节

**关闭方式给得很宽**: 关闭按钮, 点背景, `Escape`, 三个都行. 但**点面板内部不关** —— 那听起来
像个显然的想法, 直到你在滚一份长文档时它从你手底下消失.

**打开时锁住背后的滚动**, 并把焦点移进面板, 这样 `Escape` 和方向键落在这里而不是落在下面
那一页上.

**正文走的是 chat 页那同一个 `Markdown` 组件**, 所以 `business-context.md` 里写
` ```mermaid ` 围栏会真的画出图, 并且自动享有懒加载和 `securityLevel: "strict"` —— 这个组件
完全不知道"图"这个概念存在.

那个 Markdown 组件是按聊天气泡的尺寸调的, 而这里是一份文档, 所以标题和正文是在**外面用
`[&_h2]:...` 这类任意变体放大的**, 而不是去 fork 一份渲染器.
