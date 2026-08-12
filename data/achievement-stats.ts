import { FaPython } from "react-icons/fa"
import { PenTool, Sparkles } from "lucide-react"
import { AchievementStat } from "@/types"

export const achievementStats: AchievementStat[] = [
  {
    number: "10+",
    description: "Open Source Python Libraries",
    color: "text-primary",
    borderColor: "border-primary",
    glowColor: "shadow-primary/20",
    icon: FaPython,
    href: "https://pypi.org/user/example/",
  },
  {
    number: "100+",
    description: "Tech Blogs",
    color: "text-secondary",
    borderColor: "border-secondary",
    glowColor: "shadow-secondary/20",
    icon: PenTool,
    href: "https://johndoe.me/blogs",
  },
  {
    number: "5",
    description: "Production Ready AI Applications",
    color: "text-secondary",
    borderColor: "border-secondary",
    glowColor: "shadow-secondary/20",
    icon: Sparkles,
    href: "https://johndoe.me/portfolio",
  },
]
