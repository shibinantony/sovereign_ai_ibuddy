export function readStoredValue(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeStoredValue(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Storage can be unavailable in hardened or private browser contexts.
  }
}

export function removeStoredValue(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // The application remains usable without persisted browser preferences.
  }
}
