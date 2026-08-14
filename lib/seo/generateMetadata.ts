import { Metadata } from "next"
import { SEOConfig } from "@/types"
import { DEFAULT_SEO_CONFIG, COMMON_KEYWORDS } from "./config"

export function generateSEOMetadata(config: SEOConfig): Metadata {
  // Page config wins over the site-wide defaults
  const mergedConfig = {
    ...DEFAULT_SEO_CONFIG,
    ...config,
    keywords: config.keywords
      ? [...new Set([...COMMON_KEYWORDS, ...config.keywords])]
      : COMMON_KEYWORDS,
  }

  const {
    title,
    description,
    keywords,
    url,
    siteName,
    image,
    imageWidth,
    imageHeight,
    imageAlt,
    ogTitle,
    ogDescription,
    twitterTitle,
    twitterDescription,
    locale,
    type,
    noIndex,
    noFollow,
  } = mergedConfig

  return {
    title,
    description,
    keywords,

    openGraph: {
      title: ogTitle || title,
      description: ogDescription || description,
      url,
      siteName,
      images: image
        ? [{
            url: image,
            width: imageWidth,
            height: imageHeight,
            alt: imageAlt || title,
          }]
        : undefined,
      locale,
      type,
    },

    twitter: {
      // No profile photo to preview any more, so a large-image card would render
      // as an empty box. Upgrade to "summary_large_image" if a product OG image
      // is ever added.
      card: image ? "summary_large_image" : "summary",
      title: twitterTitle || title,
      description: twitterDescription || description,
      images: image ? [image] : undefined,
    },

    robots: {
      index: !noIndex,
      follow: !noFollow,
      googleBot: {
        index: !noIndex,
        follow: !noFollow,
        "max-video-preview": -1,
        "max-image-preview": "large",
        "max-snippet": -1,
      },
    },
  }
}
