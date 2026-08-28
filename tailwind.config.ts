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
      // The palette. Components name these rather than repeating a hex, so a
      // rebrand is this file and nothing else. `primary` is the brand navy and
      // doubles as the dark-mode page background -- the same colour by design,
      // so it gets one name rather than two.
      colors: {
        primary: {
          DEFAULT: "#0A1628", // navy
          foreground: "#FFFFFF",
          light: "#1E3A5F", // navy-light
          dark: "#050D17", // navy-dark
        },
        secondary: {
          DEFAULT: "#3B82F6", // blue-500
          foreground: "#FFFFFF",
        },
        accent: {
          DEFAULT: "#F59E0B", // amber-500
          foreground: "#0A1628",
          light: "#FBBF24", // amber-400
          dark: "#D97706", // amber-600
        },
        background: {
          DEFAULT: "#FFFFFF",
          dark: "#0A1628",
        },
        surface: {
          DEFAULT: "#F8FAFC", // slate-50
          dark: "#0F1D32",
        },
        muted: {
          DEFAULT: "#F1F5F9", // slate-100
          foreground: "#64748B", // slate-500
          dark: "#1E293B",
        },
        border: {
          DEFAULT: "#E2E8F0", // slate-200
          dark: "#334155",
        },
        // Fintech specific
        "text-primary": "#0A1628", // navy
        "text-secondary": "#1E3A5F", // navy-light
        highlight: "#F59E0B", // amber-500 (gold)
        "cta-button": "#3B82F6", // blue-500
        "regular-button": "#0A1628", // navy
        contrast: "#F59E0B", // amber-500
        // shadcn/ui compatibility
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        foreground: "hsl(var(--foreground))",
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
      // Nothing else is extended here on purpose. This file once also
      // carried a fontSize scale, four keyframe animations and three
      // shadows, none of which any component ever used -- a theme nobody
      // reads reads as a design system, and it is not one.
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
