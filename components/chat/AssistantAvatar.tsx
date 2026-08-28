import { cn } from "@/lib/utils"

/**
 * The square that marks a bubble as the agent's.
 *
 * Three places show it: the banner above the conversation, every assistant
 * message, and the "thinking" placeholder. One component so they cannot drift
 * into three slightly different squares.
 *
 * The label is a fixed two letters rather than the agent's name from
 * `site.toml`: it has to fit a 32px box, and a dataset is free to name its
 * agent something long.
 */
export function AssistantAvatar({ size = "sm" }: { size?: "sm" | "md" }) {
  return (
    <div
      className={cn(
        "bg-brand flex items-center justify-center shrink-0 rounded-lg",
        size === "md" ? "w-10 h-10" : "w-8 h-8",
      )}
      aria-hidden="true"
    >
      <span className={cn("font-display text-white", size === "md" ? "text-sm" : "text-xs")}>
        AI
      </span>
    </div>
  )
}
