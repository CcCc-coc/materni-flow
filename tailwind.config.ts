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
      colors: {
        // Fintech Color System (Navy + Gold)
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
      fontFamily: {
        display: ["var(--font-figtree)", "sans-serif"],
        body: ["var(--font-noto-sans)", "sans-serif"],
        heading: ["var(--font-figtree)", "sans-serif"],
        inter: ["var(--font-inter)", "sans-serif"],
      },
      fontSize: {
        "display-xl": ["clamp(4rem, 15vw, 12rem)", { lineHeight: "0.9", letterSpacing: "-0.02em" }],
        "display-lg": ["clamp(3rem, 10vw, 8rem)", { lineHeight: "0.95", letterSpacing: "-0.02em" }],
        "display-md": ["clamp(2rem, 6vw, 4rem)", { lineHeight: "1", letterSpacing: "-0.01em" }],
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-in-out",
        "slide-up": "slideUp 0.5s ease-out",
        "slide-in-left": "slideInLeft 0.6s ease-out",
        "slide-in-right": "slideInRight 0.6s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(20px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideInLeft: {
          "0%": { transform: "translateX(-30px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
        slideInRight: {
          "0%": { transform: "translateX(30px)", opacity: "0" },
          "100%": { transform: "translateX(0)", opacity: "1" },
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        none: "0px",
      },
      boxShadow: {
        "fintech": "0 4px 6px -1px rgba(10, 22, 40, 0.1), 0 2px 4px -2px rgba(10, 22, 40, 0.1)",
        "fintech-lg": "0 10px 15px -3px rgba(10, 22, 40, 0.1), 0 4px 6px -4px rgba(10, 22, 40, 0.1)",
        "fintech-accent": "0 4px 6px -1px rgba(245, 158, 11, 0.2), 0 2px 4px -2px rgba(245, 158, 11, 0.1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

export default config
