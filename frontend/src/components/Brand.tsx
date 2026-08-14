interface BrandProps {
  compact?: boolean
}

export function Brand({ compact = false }: BrandProps) {
  return (
    <div className="brand" aria-label="Sovereign AI iBuddy home">
      <span className="brand-mark" aria-hidden="true">
        <span className="brand-mark-core" />
      </span>
      {!compact && (
        <span className="brand-wordmark">
          Sovereign AI <span>iBuddy</span>
        </span>
      )}
    </div>
  )
}
