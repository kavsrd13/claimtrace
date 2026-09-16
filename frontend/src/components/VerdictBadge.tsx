import React from 'react'
import type { ClaimItem } from '../api'

export const VERDICT_LABELS: Record<ClaimItem['verdict'], string> = {
  agree: '✅ Agree',
  disagree: '❌ Disagree',
  only_in_a: '📘 Only in A',
  only_in_b: '📙 Only in B',
}

interface VerdictBadgeProps {
  verdict: ClaimItem['verdict']
}

/**
 * Accessible status badge for document claim analysis verdicts.
 * Renders high-contrast label with emoji icon and semantic aria-label.
 */
export function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const label = VERDICT_LABELS[verdict] || verdict
  return (
    <span
      className={`verdict-badge verdict-${verdict}`}
      role="status"
      aria-label={`Claim verdict: ${verdict}`}
    >
      {label}
    </span>
  )
}

export default VerdictBadge
