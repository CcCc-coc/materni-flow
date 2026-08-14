import type { ComponentType } from "react"

import { CodeBlock } from "./CodeBlock"
import { MermaidBlock } from "./MermaidBlock"
import type { BlockProps } from "./types"

/**
 * 围栏代码块渲染器目录, 按 ```后面的语言标记查表。
 *
 * 这里就是开关: 加一行支持一种新块, 删一行关掉一种。没在表里的语言 (包括
 * ```python 这种普通代码) 全部落到 CodeBlock。
 *
 * 加新渲染器时别忘了最容易漏的一步: 前端认得这个格式不等于模型会输出它,
 * 得同时在 agent_app/prompts/bi-agent-system-prompt.md 里告诉 agent 什么时候产出。
 */
const BLOCK_RENDERERS: Record<string, ComponentType<BlockProps>> = {
  mermaid: MermaidBlock,
}

/** 按语言查渲染器, 查不到就用兜底的 CodeBlock。 */
export function getBlockRenderer(language: string): ComponentType<BlockProps> {
  return BLOCK_RENDERERS[language] ?? CodeBlock
}

export type { BlockProps }
