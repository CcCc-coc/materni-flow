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
  /**
   * What the term means, for a reader who does not know the domain.
   *
   * The label is a heading, not an explanation -- "Portfolio Concentration"
   * tells someone who already works in lending exactly what it is, and tells
   * everyone else nothing. This is the sentence that closes that gap, shown on
   * hover and on keyboard focus.
   *
   * Two or three plain sentences. Define the term, then say why the number
   * moves. No jargon inside the explanation of the jargon.
   */
  tooltip: string
}

interface Insight {
  icon: IconName
  title: string
  description: string
}

/** One scrollable section of the business-context explainer. */
interface ContextSection {
  heading: string
  paragraphs: string[]
  /** Optional term/detail pairs, for enumerating concepts rather than prose. */
  bullets?: { term: string; detail: string }[]
  /** Prose that reads *after* the bullets, for a takeaway that needs them first. */
  closingParagraphs?: string[]
  /**
   * One optional mermaid diagram, rendered after this section's prose.
   *
   * Reserved for the one thing prose is genuinely worse at: a sequence or a
   * branch the reader has to hold in their head all at once. At most one in
   * the whole explainer, kept under ten nodes. A second diagram, or one that
   * merely restates a sentence, is decoration and should be a sentence.
   */
  mermaid?: string
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
  /**
   * The long-form explainer behind the home page's one-paragraph pitch.
   *
   * Two or three screens of scrollable prose, opened from the home page and
   * dismissed again without navigating. It exists because a headline and one
   * paragraph cannot carry a whole business domain, and a reader who does not
   * already know the industry will otherwise not understand what any of the
   * agent's answers are *for*.
   *
   * This describes the **app**, not the dataset. What ships outward looks like
   * a dataset with an agent attached, but what a reader actually needs is what
   * the app is for: whose problem it solves, on what evidence, and how far it
   * goes today. First half explains the world, second half explains what the
   * agent does in it.
   *
   * Write it for a stranger with no domain knowledge and no context about who
   * built this: explain the industry, not an employer; the problem, not a
   * project. Common sense should be enough to follow every sentence.
   */
  businessContext: {
    /** Label on the home-page control that opens it. */
    triggerLabel: string
    title: string
    subtitle: string
    sections: ContextSection[]
  }
  home: {
    headline: { prefix: string; accent: string }
    description: string
    capabilities: Capability[]
    techStack: string[]
    cta: { title: string; subtitle: string }
  }
  /**
   * Interface messages that are not about the dataset.
   *
   * They live here for the same reason the business copy does: a user-visible
   * string typed into a component is a string nobody can find later. These do
   * not change when the dataset changes, but they do change with the product's
   * voice, so they belong with the rest of the voice.
   */
  messages: {
    /** Server refused because this deployment's spend cap was reached. */
    rateLimited: string
    /** User submitted while a reply was still streaming. */
    waitForResponse: string
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
    title: "SMB Lending Lens: AI-Powered Fintech Analytics Agent",
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
      "Analyzing SMB lending data: 10 tables, ~111,000 records covering applications, loans, payments, and defaults",
  },

  businessContext: {
    triggerLabel: "What problem does this solve?",
    title: "The business behind the agent",
    subtitle:
      "A small-business lender can grow its book, hold its rates, and still lose money, because the losses arrive quietly and late. This is where they come from, and what this agent does about them.",
    sections: [
      {
        heading: "How a small-business lender makes money",
        paragraphs: [
          "The model is simple enough to state in a sentence: raise money at one rate, lend it to small businesses at a higher one, and keep the difference. A bakery wants $80,000 for a second location, the lender funds it, and the business repays a fixed amount every month for a few years.",
          "What makes it hard is that the difference is thin and the downside is total. Interest on a healthy loan earns a few percentage points a year; a loan that is never repaid loses most of the principal at once. So the business does not really run on how much it lends. It runs on how accurately it can price the chance of not being repaid.",
        ],
        bullets: [
          {
            term: "Interest",
            detail:
              "The main revenue line, charged as an annual rate on the outstanding balance. The rate is set from the borrower's risk grade, which is assigned from their credit profile at the time of approval.",
          },
          {
            term: "Origination fees",
            detail:
              "A one-time charge when the loan is funded. Smaller than interest, and earned whether or not the loan is repaid.",
          },
          {
            term: "Defaults",
            detail:
              "The dominant cost. When a borrower stops paying, the lender pursues what it can recover and writes off the rest. One default can erase the interest earned on a dozen healthy loans.",
          },
        ],
      },
      {
        heading: "Where the money quietly leaks",
        paragraphs: [
          "None of the following show up as a line item on a financial statement. Each one is structural, a consequence of how lending is normally run, and each stays invisible unless somebody deliberately goes looking. That is what this agent is for.",
        ],
        bullets: [
          {
            term: "Pricing rests on an assumption nobody re-checks",
            detail:
              "Each risk grade is priced against an assumed default rate, set when the grading system was designed. Reality drifts. If a grade was priced for six percent losses and is running near ten, every loan written in that grade is underpriced. And because the loans are performing when they are written, nothing signals the problem for a year or more.",
          },
          {
            term: "Concentration accumulates without anyone choosing it",
            detail:
              "No committee ever decides to put a sixth of the book into restaurants. It happens one approval at a time, each defensible on its own. The risk is that loans in one industry do not fail independently. A bad season hits all of them together, which is exactly the scenario a portfolio is supposed to be spread against.",
          },
          {
            term: "The warning arrives months before the loss",
            detail:
              "Borrowers rarely stop paying without a run-up. Payments start landing a few days late, then short of the full amount. Most defaults are preceded by that pattern. But a monthly report that shows only what was collected against what was due will show a loan as current until the month it is not.",
          },
          {
            term: "The best applicants look like the risky ones",
            detail:
              "Approval rules are tuned to keep bad loans out, and they succeed partly by turning away good ones. A rejected applicant whose profile is stronger than the average borrower already on the books is revenue the lender declined. The borrower who repays goes on to become a repeat customer, who defaults at roughly half the rate of a first-timer, so the cost of that rejection compounds.",
          },
        ],
      },
      {
        heading: "What that looks like in the data",
        paragraphs: [
          "Every one of those leaks leaves a trace, but never in one place. Proving a grade is underpriced means putting the pricing assumption next to two years of outcomes. Proving a default was foreseeable means putting a loan's schedule next to the payments that actually arrived, in the right order, for the months before it failed.",
          "So the record covers the full lending lifecycle together: the businesses that applied, the applications that were approved and rejected and why, the loans that were funded and their terms, the repayment schedule each one was supposed to follow, every payment actually received, and the defaults with what was ultimately recovered.",
          "It is a fixed snapshot rather than a live feed, which is what makes the same question return the same answer whenever it is asked.",
          "The whole record hangs off one path, and every question in this app is really a question about some step along it:",
        ],
        mermaid: `flowchart LR
    A[Business applies] --> B{Approved?}
    B -- No --> R[Rejected]
    B -- Yes --> L[Loan funded]
    L --> P[Monthly payments]
    P --> D[Paid off]
    P --> F[Defaulted]`,
      },
      {
        heading: "What the agent does with it",
        paragraphs: [
          "You ask in plain English. The agent reads the database structure, works out which tables have to be joined and at what grain, writes the query, runs it, and then explains what came back in business terms rather than handing you a grid of numbers.",
          "It picks its format to match the question. Exact values arrive as a table. When the shape of the numbers is the point, such as a ranking across grades, a trend across quarters, or a gap between two measures, it draws a chart. When the answer is about how something flows rather than how much, it draws a diagram.",
          "Every number it reports comes from a query it actually ran against the data, not from its own recollection. If you want to check it, ask it to show you the SQL and the reasoning; it keeps both.",
        ],
      },
      {
        heading: "What you can ask, and how to read the answers",
        paragraphs: [
          "Almost every useful question falls into one of four groups. You do not need to phrase them precisely or know any table names.",
        ],
        bullets: [
          {
            term: "Risk pricing",
            detail:
              "Which risk grades are priced for fewer losses than they are actually producing, how wide the gap is, and how much of the book was written inside it.",
          },
          {
            term: "Portfolio concentration",
            detail:
              "Which industries hold the largest share of outstanding balance, how their loss rates compare to the rest of the book, and where a single downturn would land hardest.",
          },
          {
            term: "Early warning",
            detail:
              "What payment behaviour preceded the loans that defaulted, how far ahead of the write-off it started, and which currently-performing loans are showing the same pattern now.",
          },
          {
            term: "Customer value",
            detail:
              "How repeat borrowers compare to first-time ones on default rate and loan size, and whether any rejected applicants had a stronger profile than the average approved borrower.",
          },
        ],
        closingParagraphs: [
          "Two habits make the answers far more useful. First, averages hide the finding: a portfolio-wide default rate is the average of grades that are fine and grades that are not, and it will look reassuring in both cases. Ask for the breakdown, not the mean.",
          "Second, a gap is only actionable with its size attached. A grade mispriced by four percentage points matters differently depending on whether it holds two percent of the book or thirty. The agent will report both together if you ask for them.",
        ],
      },
      {
        heading: "Beyond read-only",
        paragraphs: [
          "This app only reads. It can query anything in the record and explain it, but it cannot change a single row. That is a deliberate choice for something anyone can open, not a limitation of what the approach can do.",
          "The same architecture supports the other half. An agent can be given tools that act rather than only report: flag a loan for collections review, queue a risk grade for repricing at the next committee, open a case on an applicant who looks wrongly rejected. The analysis and the action then live in one place, instead of ending in a slide deck that someone has to act on by hand a week later.",
          "That step is only responsible with two things attached. Guardrails: an agent gets narrowly scoped permissions, and the consequential actions need human approval rather than a broad key and good intentions. An auditable trail: every action it takes is attributable, reviewable, and reversible after the fact. An agent that can act without both is not a more capable product, it is an unaccountable one. That is why what you are looking at here stops at read-only.",
        ],
      },
    ],
  },


  home: {
    headline: { prefix: "SMB Lending ", accent: "Lens" },
    description:
      "An AI agent that helps fintech lending teams analyze loan portfolios through natural conversation. Query risk metrics, identify mispriced segments, detect early warning signals, and surface actionable insights from your lending data.",
    capabilities: [
      {
        icon: "BarChart3",
        label: "Risk Pricing Analysis",
        tooltip:
          "Every loan is priced on an assumed default rate, meaning the share of borrowers in that risk grade expected not to repay. Pricing analysis puts that assumption next to how many actually defaulted, because the gap between the two is margin the lender never charged for.",
      },
      {
        icon: "Shield",
        label: "Portfolio Concentration",
        tooltip:
          "Concentration is how much of the money out on loan sits in one industry. It matters because loans in the same industry fail together, so one bad year for restaurants hits every restaurant loan at once. Nobody ever decides to become concentrated. It accumulates one approval at a time.",
      },
      {
        icon: "AlertTriangle",
        label: "Early Warning Signals",
        tooltip:
          "A borrower rarely stops paying without warning: payments start arriving late, or arriving short, months before the loan is written off. Early warning is reading those patterns while there is still time to call the customer, rather than after the loss is booked.",
      },
      {
        icon: "Users",
        label: "Customer Lifecycle Value",
        tooltip:
          "A borrower who has already repaid a loan is a known quantity, and defaults at roughly half the rate of a first-time borrower. Lifecycle value is what that track record is worth, and what it costs to turn away a good applicant who would have become one.",
      },
    ],
    techStack: ["Strands SDK", "AWS Bedrock", "PostgreSQL", "Next.js"],
    cta: {
      title: "Start Analyzing",
      subtitle: "Ask questions about your lending portfolio in plain English",
    },
  },

  messages: {
    rateLimited:
      "This demo runs on a monthly token budget and it is used up for now. It resets at the start of next month.",
    waitForResponse: "Wait for the current answer to finish first.",
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
