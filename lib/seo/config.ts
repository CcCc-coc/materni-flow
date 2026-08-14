import { brand } from "@/lib/project"

export const DEFAULT_SEO_CONFIG = {
  siteName: brand.siteName,
  author: {
    name: brand.author.name,
    url: brand.author.url,
  },
  creator: brand.author.name,
  locale: brand.locale,
  image: brand.avatar.src,
  imageWidth: brand.avatar.width,
  imageHeight: brand.avatar.height,
  type: "website" as const,
}

export const COMMON_KEYWORDS = brand.keywords
