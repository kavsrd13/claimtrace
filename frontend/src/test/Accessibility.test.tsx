import { render, screen } from '@testing-library/react'
import React from 'react'
import { describe, expect, it } from 'vitest'
import App from '../App'

describe('Accessibility Landmarks & Features', () => {
  it('renders a skip to main content link targeting #main-content', () => {
    render(<App />)
    const skipLink = screen.getByRole('link', { name: /skip to main content/i })
    expect(skipLink).toBeInTheDocument()
    expect(skipLink).toHaveAttribute('href', '#main-content')
    expect(skipLink).toHaveClass('skip-link')
  })

  it('renders an ARIA live region for screen reader announcements', () => {
    render(<App />)
    const liveRegion = screen.getByRole('status')
    expect(liveRegion).toBeInTheDocument()
    expect(liveRegion).toHaveAttribute('aria-live', 'polite')
    expect(liveRegion).toHaveClass('sr-only')
  })

  it('renders a main landmark with id main-content', () => {
    render(<App />)
    const mainElement = screen.getByRole('main')
    expect(mainElement).toBeInTheDocument()
    expect(mainElement).toHaveAttribute('id', 'main-content')
  })
})
