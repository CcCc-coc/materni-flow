"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowRight, BookOpen } from "lucide-react"

import BusinessContextModal from "@/components/BusinessContextModal"
import CapabilityCard from "@/components/CapabilityCard"
import type { SiteConfig } from "@/lib/site/schema"

export default function Hero({
  site,
  businessContext,
}: {
  site: SiteConfig
  /** Raw Markdown of `data/business-context.md`, read on the server. */
  businessContext: string
}) {
  const [isVisible, setIsVisible] = useState(false)
  const [contextOpen, setContextOpen] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const { home, capabilities } = site

  return (
    <section className="min-h-screen flex flex-col justify-center pt-28 pb-16 px-4 sm:px-6 lg:px-8 bg-[#071A2B] relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none opacity-40 bg-[radial-gradient(circle_at_85%_15%,rgba(73,211,199,0.18),transparent_32%),linear-gradient(135deg,transparent_60%,rgba(13,38,58,0.8))]" />
      <div className="max-w-6xl mx-auto w-full relative">
        <div className="flex items-center gap-3 mb-10 text-xs uppercase tracking-[0.24em] text-[#8DAFC0]"><span className="w-2 h-2 rounded-full bg-[#49D3C7] shadow-[0_0_14px_#49D3C7]" />Live ward handover console</div>
        {/* Title */}
        <div
          className={`transition-all duration-700 delay-100 ${isVisible ?"opacity-100 translate-y-0" : "opacity-0 -translate-y-8"}`}
        >
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-[0.95] mb-5 max-w-4xl">
            <span className="text-[#EAF7F6]">{home.headline.prefix}</span>
            <span className="text-[#49D3C7]">{home.headline.accent}</span>
          </h1>

          <p className="text-xl sm:text-2xl text-[#8DAFC0] mb-4 max-w-2xl">
            {home.tagline}
          </p>

          <div className="w-20 h-1 bg-[#F4B860] rounded mb-10" />
        </div>

        {/* Description */}
        <div
          className={`transition-all duration-700 delay-300 ${isVisible ?"opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <p className="text-lg sm:text-xl text-[#B8CED7] mb-5 leading-relaxed max-w-3xl">
            {home.description}
          </p>

          {/* One paragraph cannot carry a whole business domain; this opens the
              two or three screens that can. */}
          <button
            type="button"
            onClick={() => setContextOpen(true)}
            className="group inline-flex items-center gap-2 mb-10 px-4 py-2 rounded-full text-sm font-medium bg-[#102F45] text-[#EAF7F6] border border-[#23445A] hover:border-[#49D3C7] hover:text-[#49D3C7] transition-colors cursor-pointer"
          >
            <BookOpen className="w-4 h-4" aria-hidden="true" />
            {home.businessContext.triggerLabel}
          </button>

          {/* The four business threads. Same four on the agent's welcome
              screen, from the same `[[capabilities]]`. */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            {capabilities.map((cap, index) => (
              <CapabilityCard
                key={cap.title}
                capability={cap}
                // Two columns on a phone: outer cards hang the bubble from
                // their outer edge so it cannot run off screen.
                align={index % 2 === 0 ? "start" : "end"}
                className={`transition-all duration-500 ${isVisible ?"opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
              />
            ))}
          </div>

          {/* Tech Stack Tags */}
          <div className="flex flex-wrap gap-2 mb-10">
            {home.techStack.map((tech) => (
              <span
                key={tech}
                className="px-4 py-1.5 text-sm rounded-full bg-[#0D263A] text-[#8DAFC0] border border-[#23445A]"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* CTA Button */}
        <div
          className={`transition-all duration-700 delay-500 ${isVisible ?"opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <Link
            href="/chat"
            className="group flex items-center justify-between w-full p-6 bg-[#0D263A] border border-[#23445A] rounded-2xl hover:border-[#49D3C7] hover:shadow-[0_0_32px_rgba(73,211,199,0.12)] transition-all duration-200 cursor-pointer"
          >
            <div>
              <h3 className="font-display text-2xl sm:text-3xl text-[#EAF7F6] mb-1">
                {home.cta.title}
              </h3>
              <p className="text-[#8DAFC0] text-sm sm:text-base">
                {home.cta.subtitle}
              </p>
            </div>
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-[#163A50] group-hover:bg-[#49D3C7] transition-colors">
              <ArrowRight className="w-6 h-6 text-[#49D3C7] group-hover:text-[#071A2B] group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        </div>

        {/* Database Info */}
        <div
          className={`mt-10 transition-all duration-700 delay-700 ${isVisible ?"opacity-100" : "opacity-0"}`}
        >
          <p className="text-sm text-[#7295A7]">{home.blurb}</p>
        </div>
      </div>

      <BusinessContextModal
        open={contextOpen}
        onClose={() => setContextOpen(false)}
        labels={home.businessContext}
        markdown={businessContext}
      />
    </section>
  )
}
