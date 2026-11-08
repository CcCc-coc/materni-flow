"use client"

import ConceptTooltip from "@/components/ConceptTooltip"
import { getIcon } from "@/lib/icons"
import type { Capability } from "@/lib/site/schema"

/**
 * One of the app's four business lines, as a card with an explanation behind it.
 *
 * The home page and the agent's welcome screen both show these four, at
 * different sizes. One component rather than two so they cannot drift: the
 * previous arrangement had `home.capabilities` and `chat.insights` as separate
 * config, and they had already drifted -- the second thread was "Portfolio
 * Concentration" on the home page and "Portfolio Health" on the agent, with a
 * different icon, and the tooltip existed on one screen and not the other.
 *
 * `title` is a concept name and is therefore unreadable to anyone outside the
 * domain. `subtitle` is the one-line translation; the tooltip is the paragraph
 * behind it, on hover, focus, or tap.
 */
export default function CapabilityCard({
  capability,
  align = "start",
  compact = false,
  className = "",
}: {
  capability: Capability
  /** Which edge the tooltip hangs from while the grid is two columns wide. */
  align?: "start" | "end"
  /** The agent's welcome screen has less room than the home page. */
  compact?: boolean
  className?: string
}) {
  const Icon = getIcon(capability.icon)

  return (
    <ConceptTooltip
      text={capability.tooltip}
      align={align}
      className={`group rounded-xl bg-[#102F45] border border-[#23445A] cursor-help hover:border-[#49D3C7] transition-colors ${
 compact ?"p-4" : "p-5"
      } ${className}`}
    >
      <Icon
        className={`text-[#49D3C7] ${compact ?"w-5 h-5 mb-2" : "w-6 h-6 mb-3"}`}
        aria-hidden="true"
      />
      <p
        className={`font-medium text-[#EAF7F6] ${
 compact ?"text-sm" : "text-sm"
        }`}
      >
        {capability.title}
      </p>
      <p
        className={`text-[#8DAFC0] mt-0.5 leading-snug ${
 compact ?"text-xs" : "text-xs"
        }`}
      >
        {capability.subtitle}
      </p>
      {/* The dashed rule is the only thing telling a reader there is something
          to hover over. Without it the hint is invisible. */}
      <span
        aria-hidden="true"
        className="mt-3 block w-8 border-b border-dashed border-[#41677B] group-hover:border-[#49D3C7] transition-colors"
      />
    </ConceptTooltip>
  )
}
