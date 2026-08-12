"use client"

import Link from "next/link"
import { achievementStats } from "@/data/achievement-stats"

export default function StatsSection() {
  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8 border-t-4 border-black dark:border-white">
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <h2 className="font-display text-display-md text-black dark:text-white mb-12">
          ACHIEVEMENTS
        </h2>

        {/* Stats Grid - Bold Style */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-0">
          {achievementStats.map((stat, index) => {
            const IconComponent = stat.icon
            const isClickable = stat.href && stat.href.trim() !== ""
            const isLast = index === achievementStats.length - 1

            const cardContent = (
              <div className="text-center py-12">
                {/* Big Number */}
                <div className="font-display text-6xl sm:text-7xl lg:text-8xl text-black dark:text-white mb-2">
                  {stat.number}
                </div>
                {/* Description */}
                <div className="font-display text-xl sm:text-2xl text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                  {stat.description}
                </div>
              </div>
            )

            const borderClass = isLast
              ? "border-4 border-black dark:border-white"
              : "border-4 border-r-0 sm:border-r-0 border-black dark:border-white"

            if (isClickable) {
              return (
                <Link
                  key={index}
                  href={stat.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${borderClass} hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-colors cursor-pointer group`}
                >
                  <div className="text-center py-12">
                    <div className="font-display text-6xl sm:text-7xl lg:text-8xl group-hover:text-accent transition-colors mb-2">
                      {stat.number}
                    </div>
                    <div className="font-display text-xl sm:text-2xl text-gray-600 dark:text-gray-400 group-hover:text-current uppercase tracking-wider transition-colors">
                      {stat.description}
                    </div>
                  </div>
                </Link>
              )
            }

            return (
              <div
                key={index}
                className={borderClass}
              >
                {cardContent}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
