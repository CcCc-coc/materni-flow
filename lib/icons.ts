import {
  AlertTriangle,
  BarChart3,
  Building2,
  Clock,
  DollarSign,
  LineChart,
  type LucideIcon,
  Package,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Users,
} from "lucide-react"

/**
 * Icon names usable from `config/dataset.json`.
 *
 * JSON cannot hold a React component, so the config files name an icon and this
 * map resolves it. Keeping the map explicit (rather than indexing all of
 * `lucide-react`) means a typo in the config surfaces here as a visible fallback
 * instead of a blank card, and the bundle only carries icons we actually use.
 *
 * Need one that is not here? Import it above and add it to the map.
 */
export const ICONS: Record<string, LucideIcon> = {
  AlertTriangle,
  BarChart3,
  Building2,
  Clock,
  DollarSign,
  LineChart,
  Package,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Users,
}

/** Resolve an icon name from config, falling back to a neutral icon. */
export function getIcon(name: string): LucideIcon {
  return ICONS[name] ?? Sparkles
}
