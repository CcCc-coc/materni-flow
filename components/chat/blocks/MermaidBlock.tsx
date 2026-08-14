"use client"

import { useEffect, useId, useState } from "react"

import { CodeBlock } from "./CodeBlock"
import type { BlockProps } from "./types"

/**
 * mermaid 整包接近 1MB, 而大多数对话里一张图都没有。所以它只在页面上真的出现
 * 第一个 ```mermaid 块时才被动态 import, 之后整页共用这一个 promise。
 */
let mermaidPromise: Promise<typeof import("mermaid").default> | null = null

function loadMermaid() {
  if (!mermaidPromise) {
    mermaidPromise = import("mermaid").then(({ default: mermaid }) => {
      mermaid.initialize({
        startOnLoad: false,
        // 图的内容来自 LLM, 而 LLM 又在转述数据库里的数据。strict 会让 mermaid
        // 用 DOMPurify 洗一遍输出并禁掉 HTML 标签, 这是我们敢用
        // dangerouslySetInnerHTML 的唯一原因。
        securityLevel: "strict",
        // 仓库里 darkMode 是 "class" 策略, 目前没有任何地方给 <html> 加 dark,
        // 所以这里实际总是取到亮色。写成读 class 是为了以后接主题时自动跟上。
        theme: document.documentElement.classList.contains("dark") ? "dark" : "default",
        fontFamily: "inherit",
      })
      return mermaid
    })
  }
  return mermaidPromise
}

/**
 * 把 ```mermaid 块渲染成图。
 *
 * 失败就退回 CodeBlock, 而且失败是**常态**而非异常: 流式输出时收尾围栏还没到,
 * 块里就是半张图, 每来一个 chunk 都会解析失败一次。用户看到的效果是代码先出现,
 * 写完的瞬间变成图。
 */
export function MermaidBlock({ source, language }: BlockProps) {
  const [svg, setSvg] = useState<string | null>(null)

  // useId 保证同一条消息里多张图不会撞 id。mermaid 拿 id 当 DOM 元素 id 用,
  // 而 useId 的原始形态带冒号, 在选择器里是非法的, 必须洗掉。
  const domId = `mermaid-${useId().replace(/[^a-zA-Z0-9]/g, "")}`

  useEffect(() => {
    let cancelled = false

    loadMermaid()
      .then(async (mermaid) => {
        // parse 会在语法非法或图还没写完时抛出, 挡在 render 前面更省事。
        await mermaid.parse(source)
        const { svg: rendered } = await mermaid.render(domId, source)
        if (!cancelled) setSvg(rendered)
      })
      .catch(() => {
        if (!cancelled) setSvg(null)
      })

    return () => {
      cancelled = true
      // mermaid 渲染失败时会把临时测量用的节点留在 body 上, 不清理会越积越多。
      document.getElementById(domId)?.remove()
      document.getElementById(`d${domId}`)?.remove()
    }
  }, [source, domId])

  if (!svg) return <CodeBlock source={source} language={language} />

  return (
    <div
      className="my-3 p-4 flex justify-center overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800"
      // 安全性由上面的 securityLevel: "strict" 兜底。
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}
