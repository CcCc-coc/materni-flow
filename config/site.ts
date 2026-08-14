import type { IconName } from "@/lib/icons"

/**
 * Everything the *frontend* says, in one typed file.
 *
 * Why TypeScript and not JSON
 * ---------------------------
 * Nothing in here is read by Python. The previous `config/dataset.json` was
 * shared with the backend on paper, but the two runtimes turned out to read
 * disjoint sets of keys, so the sharing bought nothing and cost the type
 * system. As TypeScript this file gets autocomplete, real comments, and
 * refactor safety, and `icon` below is constrained to the names `lib/icons.ts`
 * actually exports, so a typo fails the build instead of rendering a silent
 * fallback that nobody notices.
 *
 * What belongs here
 * -----------------
 * Every product name, tagline, and sentence of business copy the UI shows. If
 * you are about to type a user-visible string into a component, it belongs
 * here instead. That is the whole point of the file: swapping datasets means
 * editing this and `config/dataset.toml`, not hunting through `components/`.
 *
 * What does NOT belong here
 * -------------------------
 * Secrets (`.env`), anything Python reads (`config/dataset.toml`), and author
 * or personal identity, which this app deliberately has none of: it presents a
 * product, not a person.
 */

interface Capability {
  icon: IconName
  label: string
}

interface Insight {
  icon: IconName
  title: string
  description: string
}

export interface SiteConfig {
  project: {
    displayName: string
    tagline: string
    /** The wordmark, split so the two halves can be coloured differently. */
    logo: { prefix: string; accent: string }
    footerName: string
  }
  agent: {
    /** What the assistant calls itself in the chat UI. */
    name: string
    /** Filled into "I'm here to help you with ___". */
    domainLabel: string
  }
  seo: {
    locale: string
    title: string
    description: string
    keywords: string[]
  }
  database: {
    /** One line describing the dataset, shown on the home page. */
    blurb: string
  }
  home: {
    headline: { prefix: string; accent: string }
    description: string
    capabilities: Capability[]
    techStack: string[]
    cta: { title: string; subtitle: string }
  }
  chat: {
    welcomeSubtitle: string
    insights: Insight[]
    tryExamples: string
    suggestionsHint: string
    inputPlaceholder: string
  }
}

export const site: SiteConfig = {
  project: {
    displayName: "SMB Lending Lens",
    tagline: "Fintech Lending Analytics Agent",
    logo: { prefix: "lending", accent: "lens" },
    footerName: "LendingLens",
  },

  agent: {
    name: "Lending Lens",
    domainLabel: "SMB lending analytics",
  },

  seo: {
    locale: "en_US",
    title: "SMB Lending Lens — AI-Powered Fintech Analytics Agent",
    description:
      "An AI agent for fintech lending analytics. Query loan portfolios, analyze risk pricing, detect approval leakage, identify early warning signals, and understand customer lifecycle value through natural conversation.",
    keywords: [
      "Fintech",
      "SMB Lending",
      "Loan Analytics",
      "Risk Pricing",
      "AI Agent",
      "Portfolio Analysis",
      "Credit Risk",
      "Lending Intelligence",
    ],
  },

  database: {
    blurb:
      "Analyzing Pacific Bridge Lending data: 10 tables, ~52,500 records covering applications, loans, payments, and defaults",
  },

  home: {
    headline: { prefix: "SMB Lending ", accent: "Lens" },
    description:
      "An AI agent that helps fintech lending teams analyze loan portfolios through natural conversation. Query risk metrics, identify mispriced segments, detect early warning signals, and surface actionable insights from your lending data.",
    capabilities: [
      { icon: "BarChart3", label: "Risk Pricing Analysis" },
      { icon: "Shield", label: "Portfolio Concentration" },
      { icon: "AlertTriangle", label: "Early Warning Signals" },
      { icon: "Users", label: "Customer Lifecycle Value" },
    ],
    techStack: ["Strands SDK", "AWS Bedrock", "PostgreSQL", "Next.js"],
    cta: {
      title: "Start Analyzing",
      subtitle: "Ask questions about your lending portfolio in plain English",
    },
  },

  chat: {
    welcomeSubtitle: "Ask questions about the SMB lending portfolio in plain English.",
    insights: [
      {
        icon: "BarChart3",
        title: "Risk Pricing",
        description: "Compare implied vs actual default rates",
      },
      {
        icon: "TrendingUp",
        title: "Portfolio Health",
        description: "Industry concentration & exposure",
      },
      {
        icon: "AlertTriangle",
        title: "Early Warnings",
        description: "Payment patterns before defaults",
      },
      {
        icon: "Users",
        title: "Customer Value",
        description: "Repeat vs first-time borrowers",
      },
    ],
    tryExamples:
      'Try: "What\'s the default rate by risk grade?" or "Which industries have the highest concentration?"',
    suggestionsHint: "Ask me directly or click a suggestion",
    inputPlaceholder: "Enter your question...",
  },
}
