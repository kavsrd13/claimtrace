import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, expect, it } from 'vitest'
import { VerdictBadge } from '../components/VerdictBadge'

describe('VerdictBadge Component', () => {
  it('renders agree verdict with green badge and checkmark', () => {
    render(<VerdictBadge verdict="agree" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveTextContent('Agree')
    expect(badge).toHaveClass('verdict-agree')
    expect(badge).toHaveAttribute('aria-label', 'Claim verdict: agree')
  })

  it('renders disagree verdict with red badge and crossmark', () => {
    render(<VerdictBadge verdict="disagree" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveTextContent('Disagree')
    expect(badge).toHaveClass('verdict-disagree')
    expect(badge).toHaveAttribute('aria-label', 'Claim verdict: disagree')
  })

  it('renders only_in_a verdict with blue badge', () => {
    render(<VerdictBadge verdict="only_in_a" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveTextContent('Only in A')
    expect(badge).toHaveClass('verdict-only_in_a')
  })

  it('renders only_in_b verdict with orange badge', () => {
    render(<VerdictBadge verdict="only_in_b" />)
    const badge = screen.getByRole('status')
    expect(badge).toHaveTextContent('Only in B')
    expect(badge).toHaveClass('verdict-only_in_b')
  })
})
