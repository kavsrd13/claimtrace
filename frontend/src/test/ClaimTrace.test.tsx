import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { afterEach, describe, expect, it } from 'vitest'
import { CitationBadge, CitationList } from '../components/ClaimTrace'
import type { Citation } from '../api'

afterEach(() => cleanup())

const mockCitation: Citation = {
  source_label: 'Document A, Section 2',
  text: 'The contract was signed on January 1st, 2024.',
  score: 0.92,
}

const mockCitation2: Citation = {
  source_label: 'Document B, Paragraph 3',
  text: 'The agreement takes effect upon signature.',
  score: 0.75,
}

/* ============================================================
   CitationBadge tests
   ============================================================ */
describe('CitationBadge', () => {
  it('renders with correct badge number text', () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('1')
  })

  it('renders badge with correct index', () => {
    render(<CitationBadge citation={mockCitation} index={5} />)
    const badge = screen.getByRole('button', { name: /citation 5/i })
    expect(badge).toHaveTextContent('5')
  })

  it('does not show panel initially', () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens panel on click', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)

    const panel = screen.getByRole('dialog')
    expect(panel).toBeInTheDocument()
    expect(panel).toHaveTextContent(mockCitation.source_label)
    expect(panel).toHaveTextContent(mockCitation.text)
  })

  it('shows score percentage in panel', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)

    expect(screen.getByRole('dialog')).toHaveTextContent('92%')
  })

  it('closes panel on second click', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await userEvent.click(badge)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens panel on Enter key press', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    badge.focus()
    await userEvent.keyboard('{Enter}')

    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('opens panel on Space key press', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    badge.focus()
    await userEvent.keyboard(' ')

    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('closes panel on Escape key press', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('closes panel via close button', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)

    const closeBtn = screen.getByRole('button', { name: /close citation/i })
    await userEvent.click(closeBtn)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('has aria-expanded false when closed', () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    expect(badge).toHaveAttribute('aria-expanded', 'false')
  })

  it('has aria-expanded true when open', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)
    expect(badge).toHaveAttribute('aria-expanded', 'true')
  })

  it('has aria-haspopup dialog attribute', () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    expect(badge).toHaveAttribute('aria-haspopup', 'dialog')
  })

  it('panel has role=dialog and aria-modal=true', async () => {
    render(<CitationBadge citation={mockCitation} index={1} />)
    const badge = screen.getByRole('button', { name: /citation 1/i })
    await userEvent.click(badge)

    const panel = screen.getByRole('dialog')
    expect(panel).toHaveAttribute('aria-modal', 'true')
  })
})

/* ============================================================
   Keyboard navigation between multiple badges
   ============================================================ */
describe('CitationBadge keyboard navigation between multiple badges', () => {
  it('can tab between multiple citation badges', async () => {
    render(
      <div>
        <CitationBadge citation={mockCitation} index={1} />
        <CitationBadge citation={mockCitation2} index={2} />
      </div>,
    )

    const badges = screen.getAllByRole('button', { name: /citation/i })
    expect(badges).toHaveLength(2)

    badges[0].focus()
    expect(document.activeElement).toBe(badges[0])

    await userEvent.tab()
    expect(document.activeElement).toBe(badges[1])
  })

  it('opening one badge does not open another', async () => {
    render(
      <div>
        <CitationBadge citation={mockCitation} index={1} />
        <CitationBadge citation={mockCitation2} index={2} />
      </div>,
    )

    const badges = screen.getAllByRole('button', { name: /citation/i })
    await userEvent.click(badges[0])

    const dialogs = screen.getAllByRole('dialog')
    expect(dialogs).toHaveLength(1)
    expect(dialogs[0]).toHaveTextContent(mockCitation.source_label)
  })

  it('Escape closes only the open panel', async () => {
    render(
      <div>
        <CitationBadge citation={mockCitation} index={1} />
        <CitationBadge citation={mockCitation2} index={2} />
      </div>,
    )

    const badges = screen.getAllByRole('button', { name: /citation/i })
    await userEvent.click(badges[1])
    expect(screen.getByRole('dialog')).toHaveTextContent(mockCitation2.source_label)

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

/* ============================================================
   CitationList tests
   ============================================================ */
describe('CitationList', () => {
  it('renders nothing when citations array is empty', () => {
    const { container } = render(<CitationList citations={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders all citations', () => {
    render(<CitationList citations={[mockCitation, mockCitation2]} />)
    const badges = screen.getAllByRole('button', { name: /citation/i })
    expect(badges).toHaveLength(2)
  })

  it('renders source labels in list', () => {
    render(<CitationList citations={[mockCitation]} />)
    expect(screen.getByText(mockCitation.source_label)).toBeInTheDocument()
  })

  it('renders citation text in list', () => {
    render(<CitationList citations={[mockCitation]} />)
    expect(screen.getByText(mockCitation.text)).toBeInTheDocument()
  })

  it('renders "Sources" title', () => {
    render(<CitationList citations={[mockCitation]} />)
    expect(screen.getByText('Sources')).toBeInTheDocument()
  })

  it('has accessible aria-label on the list wrapper', () => {
    render(<CitationList citations={[mockCitation]} />)
    expect(screen.getByLabelText('Citations')).toBeInTheDocument()
  })
})
