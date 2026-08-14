import { brand, dataset } from "@/lib/project"

/**
 * Derived view of the config files, kept for the import sites that already read
 * `METADATA`. Nothing here is authored: every string comes from
 * `config/dataset.json` or `config/brand.json`.
 */
export const METADATA = {
  TITLE: dataset.seo.title,
  DESCRIPTION: dataset.seo.description,
  AI_ASSISTANT_NAME: dataset.agent.name,
  KEYWORDS: dataset.seo.keywords,
} as const

export const CDN_ASSETS = {
  PROFILE_PHOTO: brand.avatar.src,
} as const

export const ROUTES = {
  HOME: "/",
  CHAT: "/chat",
} as const
