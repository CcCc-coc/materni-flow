"use client"

import Hero from "./_components/Hero"
import { dataset } from "@/lib/project"

export default function HomePageContent() {
  return (
    <div className="min-h-screen bg-cyan-50 dark:bg-slate-950 text-cyan-900 dark:text-cyan-50 font-body">
      <div className="relative">
        <Hero />

        <footer className="py-8 px-4 sm:px-6 lg:px-8 border-t border-cyan-200 dark:border-cyan-800 bg-white dark:bg-slate-900">
          <div className="max-w-7xl mx-auto text-center">
            <p className="text-sm text-cyan-600 dark:text-cyan-400">
              &copy; {new Date().getFullYear()} {dataset.project.footerName}. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </div>
  )
}
