# 路由, 布局, 和 server/client 的那条线

> `app/` 下面只有两个页面, 但它切了三层壳: 全局 layout 管字体和 SEO, 路由分组各自管导航条,
> 页面本身负责读盘. 这篇讲这三层各管什么, 以及 `"use client"` 那条线画在哪.

**对应代码**: `app/layout.tsx`, `app/(marketing)/`, `app/chat/`,
`app/_components/layouts/Navigation.tsx`, `lib/seo/`

**依赖**: [03](03-content-pipeline.md) 的 `loadSite()`.

---

## 目录

```
app/
├── layout.tsx                  根: <html>, 三个字体变量, 全站 SEO
├── globals.css                 见 [08]
├── icon.png                    favicon
│
├── (marketing)/                路由分组, 不出现在 URL 里
│   ├── layout.tsx              导航条
│   ├── page.tsx                /      server: 读盘 + SEO
│   ├── HomePageContent.tsx     "use client" 的外壳 + 页脚
│   ├── loading.tsx
│   └── _components/Hero.tsx    首页的全部内容, 见 [05]
│
├── chat/
│   ├── layout.tsx              导航条 + Toaster
│   ├── page.tsx                /chat  server: 读盘
│   └── loading.tsx
│
└── _components/layouts/Navigation.tsx    两个分组共用
```

`(marketing)` 带括号是 **Next.js 的路由分组**: 它只是为了让首页和 chat 页能有各自的 layout,
不进 URL. `_components` 带下划线是**私有目录**, Next 不会把它当成路由.

---

## 三层壳各管什么

| 层 | 管 |
| :--- | :--- |
| `app/layout.tsx` | `<html lang="en">`, 三个 Google 字体的 CSS 变量, favicon, viewport, 全站默认 SEO |
| `(marketing)/layout.tsx` / `chat/layout.tsx` | 导航条. chat 那层还挂了 `<Toaster />` |
| `page.tsx` | **读盘** (`loadSite()` / `loadBusinessContext()`), 页面级 SEO 覆盖 |

`chat/layout.tsx` 里那个 `<Toaster />` 不能省: 少了它, chat 页里每一次 `toast.error()`
都是静默的 no-op —— 包括"上一条还在跑"那条提示.

---

## server / client 的线画在哪

```
page.tsx            server   读盘, 生成 metadata
   │  props
   ▼
HomePageContent     client   因为 Hero 有动画和状态
Chat                client   因为 useChat 是一个 hook
```

规矩是一句话: **读盘的往上放, 有状态的往下放, 中间用 props 连.**

`app/chat/page.tsx` 全文就三行:

```tsx
export default function Page() {
  return <Chat site={loadSite()} />;
}
```

`SiteConfig` 是从 TOML 解析出来的**纯对象**, 所以它能作为 props 跨过 server/client 边界被
序列化. 往 `site.toml` 里加任何 TOML 支持但 JSON 不支持的东西 (比如日期) 之前, 先想一下
这件事.

---

## SEO

```
lib/seo/config.ts            站点默认值, 从 site.toml 来
lib/seo/generateMetadata.ts  SEOConfig 类型 + 合并函数
```

`generateSEOMetadata()` 把页面级配置盖在站点默认值上, 并且 **Open Graph 和 Twitter 的标题
自动回退到 `title`**. 所以页面只需要传 `title` 和 `description`.

**不要把 `ogTitle` / `ogDescription` / `imageAlt` / `twitterTitle` /
`twitterDescription` 再填一遍.** 它们本来就回退到 `title` 和 `description`, 显式重复一遍只是
多出五个可以和标题不一致的地方.

**没有 `author` / `creator`, 也没有社交预览图**. 这个站点展示的是产品不是人 (见
[01](01-what-the-ui-must-do.md)). Twitter 卡片因此是 `summary` 而不是
`summary_large_image` —— 没有图的大图卡片会渲染成一个空框.

**`lib/seo/config.ts` 和 `lib/site/load.ts` 一样是 server only**, 因为它在模块顶层调用
`loadSite()`. 它的两个使用者都是 `generateMetadata` 函数, 永远不在客户端跑.

---

## `Navigation`: 两个分组共用一个

它接收 `logoPrefix` / `logoAccent` 当 props, 而不是自己去 `loadSite()` —— 因为它是
`"use client"` 的.

导航项写死在组件里的 `DEFAULT_NAV_ITEMS`, 理由见 [02](02-the-elements.md) 末尾那张表:
这个 app 有几个页面是脚手架的事实, 不随数据集变.

**已知可以更好的地方**: 桌面版和移动版各写了一遍几乎一样的分支逻辑 (约 45 行重复), 而
"哪个导航项是行动召唤"是靠 `item.href === "/chat"` 硬编码判断的, `NavItem` 类型表达不了
这件事. 没动是因为收敛它要重新设计 `NavItem`, 收益主要是好看.
