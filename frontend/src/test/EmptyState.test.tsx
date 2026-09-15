import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import EmptyState from '../components/EmptyState'

afterEach(() => cleanup())

describe('EmptyState', () => {
  it('renders the title', () => {
    render(<EmptyState title="Nothing here yet" />)
    expect(screen.getByText('Nothing here yet')).toBeInTheDocument()
  })

  it('renders default icon when no icon prop is provided', () => {
    render(<EmptyState title="Empty" />)
    // The default icon is 📂
    expect(screen.getByText('📂')).toBeInTheDocument()
  })

  it('renders a custom icon', () => {
    render(<EmptyState icon="🚀" title="Empty" />)
    expect(screen.getByText('🚀')).toBeInTheDocument()
  })

  it('renders description when provided', () => {
    render(
      <EmptyState
        title="Empty"
        description="No documents have been uploaded yet."
      />,
    )
    expect(
      screen.getByText('No documents have been uploaded yet.'),
    ).toBeInTheDocument()
  })

  it('does not render description when not provided', () => {
    render(<EmptyState title="Empty" />)
    // There should be no <p> element with description text
    const paragraphs = document.querySelectorAll('p')
    expect(paragraphs.length).toBe(0)
  })

  it('renders action button when action prop is provided', () => {
    const onClick = vi.fn()
    render(
      <EmptyState
        title="Empty"
        action={{ label: 'Upload Now', onClick }}
      />,
    )
    const btn = screen.getByRole('button', { name: 'Upload Now' })
    expect(btn).toBeInTheDocument()
  })

  it('does not render action button when action prop is not provided', () => {
    render(<EmptyState title="Empty" />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onClick when action button is clicked', async () => {
    const onClick = vi.fn()
    render(
      <EmptyState
        title="Empty"
        action={{ label: 'Upload Now', onClick }}
      />,
    )
    const btn = screen.getByRole('button', { name: 'Upload Now' })
    await userEvent.click(btn)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('has role=status for accessibility', () => {
    render(<EmptyState title="Nothing" />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renders all parts together', () => {
    const onClick = vi.fn()
    render(
      <EmptyState
        icon="📄"
        title="No Documents"
        description="Upload a file to get started."
        action={{ label: 'Upload', onClick }}
      />,
    )
    expect(screen.getByText('📄')).toBeInTheDocument()
    expect(screen.getByText('No Documents')).toBeInTheDocument()
    expect(screen.getByText('Upload a file to get started.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Upload' })).toBeInTheDocument()
  })

  it('renders title as an h2 element', () => {
    render(<EmptyState title="My Title" />)
    const heading = screen.getByRole('heading', { level: 2, name: 'My Title' })
    expect(heading).toBeInTheDocument()
  })
})
