import { cn } from "@/lib/utils"

import type { BlockProps } from "./types"

/**
 * 普通围栏代码块。
 *
 * 它同时是整个 block 层的**兜底**: 语言不认识、渲染器被摘掉、Mermaid 解析失败、
 * 流式输出还没写完, 这四种情况最后都落到这里。所以它必须永远能渲染, 不做任何
 * 可能抛异常的事。
 */
export function CodeBlock({ source, language }: BlockProps) {
  return (
    <pre
      className={cn(
        "bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700",
        "p-4 rounded-lg my-3 overflow-x-auto"
      )}
    >
      <code
        className={cn(
          "text-sm font-mono text-[#0A1628] dark:text-slate-100",
          language && `language-${language}`
        )}
      >
        {source}
      </code>
    </pre>
  )
}
