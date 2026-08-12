export default function Loading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* Background Elements - 与其他页面风格一致 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-primary/8 via-primary/4 to-transparent rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-[400px] h-[300px] bg-gradient-radial from-secondary/6 via-secondary/3 to-transparent rounded-full blur-2xl"></div>
      </div>

      {/* Loading Content */}
      <div className="relative flex flex-col items-center gap-8">
        {/* Animated Logo/Spinner */}
        <div className="relative">
          {/* Outer rotating ring */}
          <div className="w-20 h-20 rounded-full border-4 border-primary/20 border-t-primary animate-spin"></div>

          {/* Inner pulsing circle */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary via-secondary to-highlight animate-pulse"></div>
          </div>

          {/* Glow effect */}
          <div className="absolute inset-0 rounded-full bg-primary/20 blur-xl animate-pulse"></div>
        </div>

        {/* Loading Text */}
        <div className="flex flex-col items-center gap-2">
          <p className="text-xl font-semibold bg-gradient-to-r from-primary via-secondary to-highlight bg-clip-text text-transparent animate-pulse">
            Loading
          </p>
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
            <span className="w-2 h-2 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
            <span className="w-2 h-2 bg-highlight rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
          </div>
        </div>
      </div>
    </div>
  )
}
