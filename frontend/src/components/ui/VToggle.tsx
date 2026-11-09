"use client"

import { useTheme } from "next-themes"

export function VThemeToggle() {
  const { theme, resolvedTheme, setTheme } = useTheme()

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark")
  }

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="w-8 h-8 rounded bg-primary flex items-center justify-center text-primary-foreground font-bold transition-all hover:scale-105 active:scale-95">
      V
    </button>
  )
}
