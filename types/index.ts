// ============================================================================
// SEO Types
// ============================================================================

export interface SEOConfig {
  // Basics
  title: string
  description: string
  keywords?: string[]

  // URL and site identity
  url?: string
  siteName?: string

  // Image
  image?: string
  imageWidth?: number
  imageHeight?: number
  imageAlt?: string

  // Open Graph overrides
  ogTitle?: string
  ogDescription?: string

  // Twitter overrides
  twitterTitle?: string
  twitterDescription?: string

  // Misc
  locale?: string
  type?: "website" | "article"

  // Indexing control
  noIndex?: boolean
  noFollow?: boolean
}

// ============================================================================
// Navigation Types
// ============================================================================

export interface NavItem {
  label: string
  href: string
}

export interface NavigationProps {
  items?: NavItem[]
}
