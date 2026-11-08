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
  // The cyan that used to be here came from the personal-portfolio template
  // this app started as. Nothing else in the design is cyan, and the only place
  // it still showed was this footer.
  return (
    <div className="min-h-screen bg-[#071A2B] text-[#EAF7F6] font-body">
      <div className="relative">
        <Hero site={site} businessContext={businessContext} />

        <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-[#23445A] bg-[#071A2B]">
          <div className="max-w-7xl mx-auto text-center">
            <p className="text-sm text-[#8DAFC0]">
              &copy; {new Date().getFullYear()} {site.brand.footerName}. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
