import { useEffect, useState } from 'react'
import { readStoredValue, writeStoredValue } from '../lib/storage'

export type Theme = 'light' | 'dark'

function getInitialTheme(): Theme {
  const saved = readStoredValue('ibuddy-theme')
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
    writeStoredValue('ibuddy-theme', theme)
    const themeMeta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
    themeMeta?.setAttribute('content', theme === 'dark' ? '#111310' : '#f7f8f5')
  }, [theme])

  return {
    theme,
    toggleTheme: () => setTheme((current) => (current === 'light' ? 'dark' : 'light')),
  }
}
