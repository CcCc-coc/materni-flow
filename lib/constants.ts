import { loadSite } from "@/lib/site/load"

/**
 * Derived view of `data/site.toml`, kept for the import sites that already
 * read `METADATA`. Nothing here is authored: every string comes from that file.
 *
 * **Server only**, because `loadSite` reads the filesystem. Both importers are
 * `generateMetadata` functions, which never run on the client.
 */
const site = loadSite()

export const METADATA = {
  TITLE: site.seo.title,
  DESCRIPTION: site.seo.description,
  AI_ASSISTANT_NAME: site.chat.agent,
  KEYWORDS: site.seo.keywords,
} as const
