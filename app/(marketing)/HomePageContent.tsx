"use client"

import Hero from "./_components/Hero"
import type { SiteConfig } from "@/lib/site/schema"

export default function HomePageContent({
  site,
  businessContext,
}: {
  site: SiteConfig
  businessContext: string
}) {
  return (
    <div className="min-h-screen bg-cyan-50 dark:bg-slate-950 text-cyan-900 dark:text-cyan-50 font-body">
      <div className="relative">
        <Hero site={site} businessContext={businessContext} />

        <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-cyan-200 dark:border-cyan-800 bg-white dark:bg-slate-900">
          <div className="max-w-7xl mx-auto text-center">
            <p className="text-sm text-cyan-600 dark:text-cyan-400">
              &copy; {new Date().getFullYear()} {site.brand.footerName}. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
