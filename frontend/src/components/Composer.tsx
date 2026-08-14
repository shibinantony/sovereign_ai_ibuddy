import { FormEvent, KeyboardEvent, useEffect, useRef } from 'react'
import { ChevronDown, Globe2, Send, Sparkles, Square, WifiOff } from 'lucide-react'
import type { SearchMode } from '../types'

interface ComposerProps {
  value: string
  mode: SearchMode
  streaming: boolean
  offlineMode: boolean
  webSearchReady: boolean
  searchProvider: string
  maxLength: number
  disabled?: boolean
  onChange: (value: string) => void
  onModeChange: (mode: SearchMode) => void
  onSubmit: () => void
  onStop: () => void
}

const modeIcon = {
  auto: Sparkles,
  web: Globe2,
  off: WifiOff,
}

export function Composer({
  value,
  mode,
  streaming,
  offlineMode,
  webSearchReady,
  searchProvider,
  maxLength,
  disabled,
  onChange,
  onModeChange,
  onSubmit,
  onStop,
}: ComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const ModeIcon = modeIcon[mode]
  const webSearchEnabled = !offlineMode && webSearchReady
  const modeHelp = offlineMode
    ? 'Strict offline mode is active. Generation stays on this device and external search is blocked.'
    : !webSearchReady
      ? 'Web search is unavailable. Generation follows the configured model backend.'
      : mode === 'auto'
        ? 'Auto search can send the query to the configured search provider when freshness or verification is needed.'
        : mode === 'web'
          ? `Web search sends the query to ${searchProvider}; generation follows the configured model backend.`
          : 'No web search suppresses retrieval for this message; generation follows the configured model backend.'

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = '0px'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 176)}px`
  }, [value])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (value.trim() && !streaming && !disabled) onSubmit()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      if (value.trim() && !streaming && !disabled) onSubmit()
    }
  }

  return (
    <div className="composer-wrap">
      <form className="composer" onSubmit={submit}>
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          maxLength={maxLength}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask iBuddy anything…"
          aria-label="Message iBuddy"
          disabled={disabled}
        />
        <div className="composer-toolbar">
          <label
            className={`mode-select ${webSearchEnabled ? '' : 'is-local-only'}`}
            title={modeHelp}
          >
            <ModeIcon size={15} aria-hidden="true" />
            <span className="sr-only">Search mode</span>
            <select
              value={mode}
              aria-describedby="search-mode-help"
              onChange={(event) => onModeChange(event.target.value as SearchMode)}
            >
              <option value="off">No web search</option>
              <option value="auto" disabled={!webSearchEnabled}>Auto search</option>
              <option value="web" disabled={!webSearchEnabled}>Search web</option>
            </select>
            <ChevronDown size={13} aria-hidden="true" />
            <span className="sr-only" id="search-mode-help">{modeHelp}</span>
          </label>
          <div className="composer-submit">
            <span
              className={`character-count ${value.length === maxLength ? 'is-limit' : ''}`}
              aria-label={`${value.length.toLocaleString()} of ${maxLength.toLocaleString()} characters used`}
            >
              {value.length.toLocaleString()} / {maxLength.toLocaleString()}
            </span>
            {streaming ? (
              <button className="send-button stop-button" type="button" onClick={onStop} aria-label="Stop response">
                <Square size={13} fill="currentColor" />
              </button>
            ) : (
              <button className="send-button" type="submit" disabled={!value.trim() || disabled} aria-label="Send message">
                <Send size={17} />
              </button>
            )}
          </div>
        </div>
      </form>
      <p className="composer-note">{modeHelp}</p>
    </div>
  )
}
