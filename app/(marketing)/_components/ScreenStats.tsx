"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { achievementStats } from "@/data/achievement-stats"

export default function ScreenStats() {
  const sectionRef = useRef<HTMLElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true)
        }
      },
      { threshold: 0.2 }
    )

    if (sectionRef.current) {
      observer.observe(sectionRef.current)
    }

    return () => observer.disconnect()
  }, [])

  return (
    <section
      ref={sectionRef}
      className="min-h-screen flex flex-col justify-center border-t-4 border-black dark:border-white py-16"
    >
      {/* Section Title */}
      <div className="px-4 sm:px-6 lg:px-8 mb-12">
        <h2
          className={`font-display text-[10vw] sm:text-[6vw] text-black dark:text-white transition-all duration-700 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          ACHIEVEMENTS
        </h2>
      </div>

      {/* Horizontal Scroll Container */}
      <div className="overflow-x-auto scrollbar-hide">
        <div className="flex gap-0 px-4 sm:px-6 lg:px-8 min-w-max">
          {achievementStats.map((stat, index) => {
            const isClickable = stat.href && stat.href.trim() !== ""

            const cardContent = (
              <div className="flex flex-col justify-center items-center h-full">
                {/* Huge Number */}
                <div className="font-display text-[20vw] sm:text-[12vw] md:text-[10vw] leading-none mb-4">
                  {stat.number}
                </div>
                {/* Description */}
                <div className="font-display text-2xl sm:text-3xl text-gray-600 dark:text-gray-400 uppercase tracking-wider text-center">
                  {stat.description}
                </div>
              </div>
            )

            const cardClass = `
              w-[80vw] sm:w-[50vw] md:w-[40vw] h-[50vh] sm:h-[60vh]
              border-4 border-black dark:border-white
              flex items-center justify-center
              transition-all duration-500
              ${isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"}
            `

            if (isClickable) {
              return (
                <Link
                  key={index}
                  href={stat.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`${cardClass} hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black cursor-pointer group`}
                  style={{ transitionDelay: `${index * 100}ms` }}
                >
                  <div className="flex flex-col justify-center items-center h-full">
                    <div className="font-display text-[20vw] sm:text-[12vw] md:text-[10vw] leading-none mb-4 group-hover:text-accent transition-colors">
                      {stat.number}
                    </div>
                    <div className="font-display text-2xl sm:text-3xl text-gray-600 dark:text-gray-400 group-hover:text-current uppercase tracking-wider text-center transition-colors">
                      {stat.description}
                    </div>
                  </div>
                </Link>
              )
            }

            return (
              <div
                key={index}
                className={cardClass}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                {cardContent}
              </div>
            )
          })}
        </div>
      </div>

      {/* Scroll Hint */}
      <div className="px-4 sm:px-6 lg:px-8 mt-8">
        <p
          className={`font-display text-sm text-gray-500 dark:text-gray-500 uppercase tracking-widest transition-all duration-700 delay-300 ${
            isVisible ? "opacity-100" : "opacity-0"
          }`}
        >
          ← SWIPE TO EXPLORE →
        </p>
      </div>
    </section>
  )
}
