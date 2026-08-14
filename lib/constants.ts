import { site } from "@/config/site"

/**
 * Derived view of `config/site.ts`, kept for the import sites that already
 * read `METADATA`. Nothing here is authored: every string comes from that file.
 */
export const METADATA = {
  TITLE: site.seo.title,
  DESCRIPTION: site.seo.description,
  AI_ASSISTANT_NAME: site.agent.name,
  KEYWORDS: site.seo.keywords,
} as const
