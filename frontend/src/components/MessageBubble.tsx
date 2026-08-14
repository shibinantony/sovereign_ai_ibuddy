import { useState } from 'react'
import { AlertCircle, Check, Clipboard, ExternalLink, Sparkles, Square, UserRound } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../types'

interface MessageBubbleProps {
  message: Message
}

function formatMessageTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime()) || date.getTime() === 0) return ''
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const copy = async () => {
    try {
      const bibliography = message.sources.length
        ? `\n\nSources:\n${message.sources
            .map((source, index) => `[${index + 1}] ${source.title}: ${source.url}`)
            .join('\n')}`
        : ''
      await navigator.clipboard.writeText(`${message.content}${bibliography}`)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1600)
    } catch {
      setCopied(false)
    }
  }

  return (
    <article className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-avatar" aria-hidden="true">
        {isUser ? <UserRound size={16} /> : <Sparkles size={16} />}
      </div>
      <div className="message-body">
        <div className="message-heading">
          <strong>{isUser ? 'You' : 'iBuddy'}</strong>
          <span>{formatMessageTime(message.created_at)}</span>
        </div>
        <div className="message-content">
          {message.content ? (
            isUser ? (
              <p>{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noreferrer">
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )
          ) : message.pending ? (
            <span className="thinking" aria-label="iBuddy is thinking">
              <i /> <i /> <i />
            </span>
          ) : null}
          {message.pending && message.content && <span className="stream-caret" aria-hidden="true" />}
        </div>

        {!isUser && message.responseState && (
          <div
            className={`response-state response-state-${message.responseState}`}
            role={message.responseState === 'error' ? 'alert' : 'status'}
          >
            {message.responseState === 'error' ? (
              <AlertCircle size={13} aria-hidden="true" />
            ) : (
              <Square size={10} fill="currentColor" aria-hidden="true" />
            )}
            <span>
              {message.responseState === 'error'
                ? 'Incomplete response — generation ended unexpectedly.'
                : message.content
                  ? 'Response stopped — partial content may be incomplete.'
                  : 'Response stopped before any text was generated.'}
            </span>
          </div>
        )}

        {!!message.sources.length && (
          <div className="sources-block">
            <div className="sources-heading">
              <span>Sources</span>
              <small>{message.sources.length}</small>
            </div>
            <div className="source-grid">
              {message.sources.map((source, index) => (
                <a
                  id={`source-${message.id}-${index + 1}`}
                  className="source-card"
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Source ${index + 1}: ${source.title || source.domain || 'Source'}`}
                  key={`${source.url}-${index}`}
                >
                  <span className="source-number">{index + 1}</span>
                  <span className="source-copy">
                    <strong>{source.title || source.domain || 'Source'}</strong>
                    {source.snippet && <span>{source.snippet}</span>}
                    <small>{source.domain}</small>
                  </span>
                  <ExternalLink size={14} aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>
        )}

        {message.content && (
          <div className="message-actions">
            <button type="button" onClick={copy} aria-label={copied ? 'Copied response' : 'Copy response'}>
              {copied ? <Check size={14} /> : <Clipboard size={14} />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        )}
      </div>
    </article>
  )
}
