import { cn } from "@/lib/utils"

import type { BlockProps } from "./types"

/**
 * A plain fenced code block.
 *
 * It is also the fallback for the whole block layer. An unknown language, a
 * renderer that was removed, a Mermaid syntax error, and a block that is still
 * streaming all end up here. That is why it does nothing that could throw.
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
