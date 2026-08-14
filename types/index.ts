import { IconType } from "react-icons"

// ============================================================================
// SEO Types
// ============================================================================

export interface SEOConfig {
  // 基础信息
  title: string
  description: string
  keywords?: string[]

  // URL 和站点信息
  url?: string
  siteName?: string

  // 图片
  image?: string
  imageWidth?: number
  imageHeight?: number
  imageAlt?: string

  // 作者和创建者
  author?: {
    name: string
    url: string
  }
  creator?: string

  // Open Graph 自定义
  ogTitle?: string
  ogDescription?: string

  // Twitter 自定义
  twitterTitle?: string
  twitterDescription?: string

  // 其他
  locale?: string
  type?: "website" | "article"

  // 索引控制
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

// ============================================================================
// Component Props Types
// ============================================================================

export interface MarkdownModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  content: string
  icon?: IconType
}
