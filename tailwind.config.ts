import type { Config } from "tailwindcss"

// This app is light-only: there is no theme toggle, so no `darkMode` strategy
// and no `dark:` variants anywhere in the tree.
const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      /* The palette. Components name these instead of repeating a hex or a raw
       * Tailwind step, so a rebrand is this block and nothing else.
       *
       * Only the colours a rebrand actually changes live here. The neutral
       * scale stays as Tailwind's own `slate-*`: it is a vocabulary every React
       * developer already reads, and it survives a rebrand unchanged.
       *
       * Every value below is the exact hex of the Tailwind step it replaced, so
       * introducing these names changed no pixel. */
      colors: {
        /** Brand navy. Wordmark, headings, dark surfaces, the user bubble. */
        primary: {
          DEFAULT: "#0A1628",
          foreground: "#FFFFFF",
        },
        /** The action colour: links, the send button, focus rings, hover edges. */
        brand: {
          DEFAULT: "#2563EB", // was blue-600
          dark: "#1D4ED8", // was blue-700, hover on a filled surface
          light: "#3B82F6", // was blue-500, focus rings and hover borders
          soft: "#60A5FA", // was blue-400
          foreground: "#FFFFFF",
        },
        /** Gold. The one non-blue highlight: logo second half, active nav, rules. */
        accent: {
          DEFAULT: "#F59E0B", // was amber-500
          foreground: "#0A1628",
        },
        /** Page and card backgrounds. */
        background: "#FFFFFF",
        foreground: "#0A1628",
        surface: "#F8FAFC", // slate-50
        border: "#E2E8F0", // slate-200, what `@apply border-border` resolves to
        muted: {
          DEFAULT: "#F1F5F9", // slate-100
          foreground: "#64748B", // slate-500
        },

        // shadcn/ui primitives. Kept whole because `components/ui/*` and any
        // component added with the shadcn CLI expect these exact names.
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      fontFamily: {
        display: ["var(--font-figtree)", "sans-serif"],
        body: ["var(--font-noto-sans)", "sans-serif"],
        heading: ["var(--font-figtree)", "sans-serif"],
        inter: ["var(--font-inter)", "sans-serif"],
      },
      /* Radius is a size ladder, and each step names a role:
       *
       *   rounded-full   pill        nav CTA, tech-stack tags
       *   rounded-2xl    panel       home CTA, agent welcome card, the modal
       *   rounded-xl     card        capability card, kickstart button, bubbles
       *   rounded-lg     block       code block, table, chart, avatars, buttons
       *   rounded-md/sm  inline      chart tooltip, legend swatches
       *
       * Nothing is extended here: these are Tailwind's own steps. There used to
       * be a shadcn override (`lg: var(--radius)` and two more derived from it)
       * which lifted `lg` from 8px to 12px -- the same value Tailwind already
       * gives `xl`. Two class names for one value is why the ladder read as
       * arbitrary in the components: half of the tree could pick either and
       * still look right. It also coupled our own scale to a variable set for
       * shadcn, so changing `--radius` would have split the design silently.
       * Nothing needed it: every shadcn `rounded-md` in `components/ui/*` is
       * overridden at its call site.
       */
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
