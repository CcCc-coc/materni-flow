/**
 * The full-page spinner Next.js shows while a route segment loads.
 *
 * One component behind both `loading.tsx` files. They were two near-identical
 * 40-line copies differing only in the word under the spinner, which is exactly
 * the shape that drifts: a colour changed on one page and not the other.
 *
 * Colours come from the Tailwind theme rather than literals so the whole thing
 * follows a palette change.
 */
export function LoadingScreen({ label }: { label: string }) {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="flex flex-col items-center gap-8">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-secondary/20 border-t-secondary animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-secondary to-highlight animate-pulse" />
          </div>
        </div>

        <div className="flex flex-col items-center gap-2">
          <p className="font-display text-xl text-primary animate-pulse">{label}</p>
          <div className="flex gap-1">
            {[0, 150, 300].map((delay) => (
              <span
                key={delay}
                className="w-2 h-2 bg-secondary rounded-full animate-bounce"
                style={{ animationDelay: `${delay}ms` }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
