"use client"

import { useEffect, useRef } from "react"
import { X } from "lucide-react"
import { site } from "@/config/site"
import { MermaidBlock } from "@/components/chat/blocks/MermaidBlock"

/**
 * The long-form business explainer, as a dismissable overlay.
 *
 * The home page can carry a headline and one paragraph. It cannot carry a whole
 * business domain, and a reader who does not already know the industry has no
 * way to tell what the agent's answers are *for*. This holds the two or three
 * screens that close that gap, without spending a route on it or pushing the
 * call to action below the fold.
 *
 * Dismissal is deliberately generous: the close button, the backdrop, and
 * Escape all work. Clicking *inside* the panel does not close it — that reads
 * as an obvious idea until you try to scroll a long document and it vanishes
 * under you.
 *
 * All copy comes from `config/site.ts`, so swapping the dataset rewrites this
 * without touching the component.
 */
export default function BusinessContextModal({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  const panelRef = useRef<HTMLDivElement>(null)

  // Escape closes, and the page behind must not scroll while the overlay is up.
  useEffect(() => {
    if (!open) return

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKeyDown)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = "hidden"

    // Move focus into the panel so Escape and the scroll keys land here rather
    // than on whatever was focused on the page underneath.
    panelRef.current?.focus()

    return () => {
      document.removeEventListener("keydown", onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [open, onClose])

  if (!open) return null

  const { businessContext } = site

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-[#0A1628]/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="business-context-title"
        tabIndex={-1}
        // The backdrop closes on click, so a click that starts inside the panel
        // must not bubble up to it.
        onClick={(event) => event.stopPropagation()}
        className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-2xl outline-none"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-5 right-5 z-10 flex items-center justify-center w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 hover:text-[#0A1628] dark:hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="overflow-y-auto px-6 sm:px-10 py-8 sm:py-10">
          <h2
            id="business-context-title"
            className="font-display text-3xl sm:text-4xl text-[#0A1628] dark:text-white mb-3 pr-12"
          >
            {businessContext.title}
          </h2>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
            {businessContext.subtitle}
          </p>

          <div className="w-16 h-1.5 bg-amber-500 rounded mt-7" />

          {businessContext.sections.map((section) => (
            <section key={section.heading} className="mt-10">
              <h3 className="font-display text-xl sm:text-2xl text-[#0A1628] dark:text-white mb-3">
                {section.heading}
              </h3>

              {section.paragraphs.map((paragraph) => (
                <p
                  key={paragraph}
                  className="text-slate-600 dark:text-slate-300 leading-relaxed mb-3"
                >
                  {paragraph}
                </p>
              ))}

              {section.bullets && (
                <dl className="mt-4 space-y-4">
                  {section.bullets.map((bullet) => (
                    <div
                      key={bullet.term}
                      className="pl-4 border-l-2 border-slate-200 dark:border-slate-700 hover:border-amber-500 transition-colors"
                    >
                      <dt className="font-medium text-[#0A1628] dark:text-white mb-1">
                        {bullet.term}
                      </dt>
                      <dd className="text-slate-600 dark:text-slate-300 leading-relaxed">
                        {bullet.detail}
                      </dd>
                    </div>
                  ))}
                </dl>
              )}

              {/* Reuses the chat renderer, which already lazy-loads the ~1MB
                  mermaid bundle and runs it at securityLevel "strict". */}
              {section.mermaid && (
                <div className="my-5">
                  <MermaidBlock source={section.mermaid} language="mermaid" />
                </div>
              )}

              {section.closingParagraphs?.map((paragraph) => (
                <p
                  key={paragraph}
                  className="text-slate-600 dark:text-slate-300 leading-relaxed mt-4"
                >
                  {paragraph}
                </p>
              ))}
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
