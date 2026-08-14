/**
 * 围栏代码块渲染器的统一入参。
 *
 * Markdown 里每个 ```lang 块都会被解析成这个形状, 然后交给 `index.tsx` 里
 * 按 language 查出来的组件。
 */
export interface BlockProps {
  /** 围栏之间的原始文本, 模型输出什么就是什么, 已去掉结尾换行。 */
  source: string
  /** 围栏上的语言标记, 例如 "mermaid"。没写语言时是空字符串。 */
  language: string
}
