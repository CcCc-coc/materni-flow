"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowRight, BarChart3, Shield, AlertTriangle, Users } from "lucide-react"

export default function Hero() {
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    setIsVisible(true)
  }, [])

  const capabilities = [
    { icon: BarChart3, label: "Risk Pricing Analysis" },
    { icon: Shield, label: "Portfolio Concentration" },
    { icon: AlertTriangle, label: "Early Warning Signals" },
    { icon: Users, label: "Customer Lifecycle Value" },
  ]

  return (
    <section className="min-h-screen flex flex-col justify-center pt-24 pb-12 px-4 sm:px-6 lg:px-8 bg-white dark:bg-[#0A1628]">
      <div className="max-w-4xl mx-auto w-full">
        {/* Title */}
        <div
          className={`transition-all duration-700 delay-100 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8"}`}
        >
          <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl leading-tight mb-4">
            <span className="text-[#0A1628] dark:text-white">SMB Lending </span>
            <span className="text-blue-600 dark:text-blue-400">Lens</span>
          </h1>

          <p className="text-xl sm:text-2xl text-slate-500 dark:text-slate-400 mb-4">
            Fintech Lending Analytics Agent
          </p>

          <div className="w-20 h-1.5 bg-amber-500 rounded mb-10" />
        </div>

        {/* Description */}
        <div
          className={`transition-all duration-700 delay-300 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 mb-10 leading-relaxed max-w-3xl">
            An AI agent that helps fintech lending teams analyze loan portfolios through
            natural conversation. Query risk metrics, identify mispriced segments, detect
            early warning signals, and surface actionable insights from your lending data.
          </p>

          {/* Capability Cards - Bluevine Style */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            {capabilities.map((cap, index) => (
              <div
                key={cap.label}
                className={`p-5 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 transition-all duration-500 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
                style={{ transitionDelay: `${400 + index * 100}ms` }}
              >
                <cap.icon className="w-6 h-6 text-blue-600 dark:text-blue-400 mb-3" />
                <p className="text-sm font-medium text-[#0A1628] dark:text-white">{cap.label}</p>
              </div>
            ))}
          </div>

          {/* Tech Stack Tags */}
          <div className="flex flex-wrap gap-2 mb-10">
            {["Strands SDK", "AWS Bedrock", "PostgreSQL", "Next.js"].map((tech) => (
              <span
                key={tech}
                className="px-4 py-1.5 text-sm rounded-full bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700"
              >
                {tech}
              </span>
            ))}
          </div>
        </div>

        {/* CTA Button - Bluevine Style */}
        <div
          className={`transition-all duration-700 delay-500 ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}
        >
          <Link
            href="/chat"
            className="group flex items-center justify-between w-full p-6 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl hover:border-blue-500 dark:hover:border-blue-400 hover:shadow-lg transition-all duration-200 cursor-pointer"
          >
            <div>
              <h3 className="font-display text-2xl sm:text-3xl text-[#0A1628] dark:text-white mb-1">
                Start Analyzing
              </h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm sm:text-base">
                Ask questions about your lending portfolio in plain English
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
          <p className="text-sm text-slate-400 dark:text-slate-500">
            Analyzing Pacific Bridge Lending data: 10 tables, ~52,500 records covering applications, loans, payments, and defaults
          </p>
        </div>
      </div>
    </section>
  )
}
