import { site } from "@/config/site"

/**
 * Site-wide metadata defaults.
 *
 * No `author`, `creator`, or profile image: this site presents a product, not a
 * person. Page metadata that names an individual (or uses their photo as the
 * social preview) is a leftover from the personal-portfolio template this
 * scaffolding came from, not something the app needs.
 */
export const DEFAULT_SEO_CONFIG = {
  siteName: site.project.displayName,
  locale: site.seo.locale,
  type: "website" as const,
}

export const COMMON_KEYWORDS = site.seo.keywords
