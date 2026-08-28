import type { Config } from "tailwindcss"

const config: Config = {
  darkMode: ["class"],
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
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        none: "0px",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
