import { BarChart3, BookOpenText, Compass, Lightbulb, Sparkles } from 'lucide-react'

interface EmptyStateProps {
  onPrompt: (prompt: string) => void
  disabled?: boolean
}

const prompts = [
  {
    icon: Compass,
    eyebrow: 'Explore',
    title: 'What changed in AI this week?',
    prompt: 'What are the most important developments in AI from the past week? Cite reliable sources.',
  },
  {
    icon: BarChart3,
    eyebrow: 'Compare',
    title: 'Break down a complex choice',
    prompt: 'Help me compare the strongest options for building a private, local-first AI assistant.',
  },
  {
    icon: BookOpenText,
    eyebrow: 'Understand',
    title: 'Teach me something deeply',
    prompt: 'Explain retrieval-augmented generation from first principles with a concrete example.',
  },
  {
    icon: Lightbulb,
    eyebrow: 'Create',
    title: 'Turn an idea into a plan',
    prompt: 'Turn my rough product idea into a practical one-week validation plan.',
  },
]

export function EmptyState({ onPrompt, disabled }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-orb" aria-hidden="true">
        <Sparkles size={23} />
      </div>
      <p className="empty-kicker">YOUR PRIVATE AI WORKSPACE</p>
      <h1>What are we exploring?</h1>
      <p className="empty-subtitle">
        Work locally by default. Enable approved web retrieval only when current evidence is needed.
      </p>
      <div className="prompt-grid">
        {prompts.map(({ icon: Icon, eyebrow, title, prompt }) => (
          <button type="button" key={title} onClick={() => onPrompt(prompt)} disabled={disabled}>
            <span className="prompt-icon"><Icon size={17} /></span>
            <span>
              <small>{eyebrow}</small>
              <strong>{title}</strong>
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
