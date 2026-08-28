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
    <section className="min-h-screen flex flex-col justify-center pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-white dark:bg-primary">
      <div className="max-w-4xl mx-auto w-full">
        {/* Title */}
        <div
          className={`transition-all duration-700 delay-100 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8"}`}
        >
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-tight mb-4">
            <span className="text-primary dark:text-white">{home.headline.prefix}</span>
            <span className="text-blue-600 dark:text-blue-400">{home.headline.accent}</span>
          </h1>

          <p className="text-xl sm:text-2xl text-slate-500 dark:text-slate-400 mb-4">
            {home.tagline}
          </p>

          <div className="w-20 h-1.5 bg-amber-500 rounded mb-10" />
        </div>

        {/* Description */}
        <div
          className={`transition-all duration-700 delay-300 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 mb-5 leading-relaxed max-w-3xl">
            {home.description}
          </p>

          {/* One paragraph cannot carry a whole business domain; this opens the
              two or three screens that can. */}
          <button
            type="button"
            onClick={() => setContextOpen(true)}
            className="group inline-flex items-center gap-2 mb-10 px-4 py-2 rounded-full text-sm font-medium bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer"
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
                className={`transition-all duration-500 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
              />
            ))}
          </div>

          {/* Tech Stack Tags */}
          <div className="flex flex-wrap gap-2 mb-10">
            {home.techStack.map((tech) => (
              <span
                key={tech}
                className="px-4 py-1.5 text-sm rounded-full bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* CTA Button */}
        <div
          className={`transition-all duration-700 delay-500 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <Link
            href="/chat"
            className="group flex items-center justify-between w-full p-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition-all duration-200 cursor-pointer"
          >
            <div>
              <h3 className="font-display text-2xl sm:text-3xl text-primary dark:text-white mb-1">
                {home.cta.title}
              </h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm sm:text-base">
                {home.cta.subtitle}
              </p>
            </div>
            <div className="flex items-center justify-center w-14 h-14 rounded-full bg-slate-100 dark:bg-slate-700 group-hover:bg-blue-600 transition-colors">
              <ArrowRight className="w-6 h-6 text-slate-400 group-hover:text-white group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        </div>

        {/* Database Info */}
        <div
          className={`mt-10 transition-all duration-700 delay-700 ${isVisible ? "opacity-100" : "opacity-0"}`}
        >
          <p className="text-sm text-slate-400 dark:text-slate-500">{home.blurb}</p>
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
