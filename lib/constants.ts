import { dataset } from "@/lib/project"

/**
 * Derived view of `config/dataset.json`, kept for the import sites that already
 * read `METADATA`. Nothing here is authored: every string comes from that file.
 */
export const METADATA = {
  TITLE: dataset.seo.title,
  DESCRIPTION: dataset.seo.description,
  AI_ASSISTANT_NAME: dataset.agent.name,
  KEYWORDS: dataset.seo.keywords,
} as const
