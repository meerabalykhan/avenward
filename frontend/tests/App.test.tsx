import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '../src/App'

const event = {
  id: '43f1b6cb-3475-4c76-bc65-1e0bd6ff58b7',
  source: 'identity',
  category: 'authentication',
  severity: 'high',
  title: 'Repeated authentication failure',
  actor: 'demo-user-1',
  target: 'lab-asset-2',
  observed_at: '2026-07-23T10:00:00Z',
  confidence: 87,
  summary: 'Synthetic evidence for testing.',
}
const alert = {
  id: '9b287670-67e5-4c3a-af18-7ea0731cc7ab',
  status: 'open',
  severity: 'high',
  title: 'Repeated authentication failures',
  summary: 'Rule matched three events for demo-user-1.',
  group_key: 'demo-user-1',
  rule_version: 1,
  event_count: 3,
  first_seen_at: '2026-07-23T09:50:00Z',
  last_seen_at: '2026-07-23T10:00:00Z',
}
const rule = {
  id: '621994f5-7db0-474a-8ab4-c0446e6950ae',
  slug: 'repeated-authentication-failure',
  name: 'Repeated authentication failures',
  description: 'Three authentication failure events for one actor within 15 minutes.',
  version: 1,
  enabled: true,
  severity: 'high',
  definition: { threshold: 3, window_seconds: 900, group_by: 'actor' },
}
const alertDetail = {
  ...alert,
  rule,
  evidence: [
    {
      id: event.id,
      title: event.title,
      source: event.source,
      observed_at: event.observed_at,
    },
  ],
}

function response(data: unknown, ok = true, status = 200) {
  return Promise.resolve({ ok, status, json: () => Promise.resolve(data) })
}

function workspaceFetch() {
  return vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
    if (url.endsWith('/auth/login')) return response({ token: 'session-token', user: {} })
    if (url.endsWith('/auth/me'))
      return response({
        email: 'analyst@example.com',
        display_name: 'Demo Analyst',
        role: 'admin',
        organization: 'Avenward Lab',
      })
    if (url.endsWith('/events/overview')) return response({ total: 1, by_severity: { high: 1 } })
    if (url.includes('/alerts?'))
      return response({ items: [alert], page: 1, page_size: 12, total: 1 })
    if (url.endsWith('/rules')) return response([rule])
    if (url.includes('/alerts/') && url.endsWith('/status'))
      return response({ ...alert, status: 'acknowledged' })
    if (url.includes('/alerts/')) return response(alertDetail)
    if (url.includes('/events?'))
      return response({ items: [event], page: 1, page_size: 12, total: 13 })
    if (url.endsWith('/events/preview')) return response({ count: 1, sample: [event] })
    if (url.endsWith('/events/import')) return response({ imported: 1 }, true, 201)
    return response({}, false, 404)
  })
}

afterEach(() => {
  sessionStorage.clear()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('Avenward event explorer', () => {
  it('signs in and presents tenant-scoped synthetic evidence', async () => {
    vi.stubGlobal('fetch', workspaceFetch())
    const user = userEvent.setup()
    render(<App />)

    expect(screen.getByRole('heading', { name: /evidence,\s*made legible/i })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    await screen.findByRole('heading', { name: 'Event explorer' })
    expect(await screen.findByText('Demo Analyst')).toBeInTheDocument()
    expect(screen.getByText('Repeated authentication failure')).toBeInTheDocument()
    expect(screen.getAllByText('Repeated authentication failures').length).toBeGreaterThan(0)
    expect(screen.getByText(/Three authentication failure events/)).toBeInTheDocument()

    await user.click(screen.getByText('Repeated authentication failure'))
    expect(screen.getByText('Synthetic evidence for testing.')).toBeInTheDocument()
    expect(screen.getByText(/not an AI verdict/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('explains and acknowledges a deduplicated alert without changing evidence', async () => {
    sessionStorage.setItem('avenward_session', 'existing-token')
    const fetchMock = workspaceFetch()
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    render(<App />)

    const alertButtons = await screen.findAllByRole('button', {
      name: /Repeated authentication failures/,
    })
    await user.click(alertButtons[0]!)
    expect(screen.getByText('Rule matched three events for demo-user-1.')).toBeInTheDocument()
    expect(screen.getByText('Supporting evidence')).toBeInTheDocument()
    expect(screen.getByText(/never alter or delete the underlying evidence/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Mark acknowledged' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/alerts/9b287670-67e5-4c3a-af18-7ea0731cc7ab/status'),
        expect.objectContaining({ method: 'PATCH' }),
      ),
    )
  })

  it('shows a safe authentication failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => response({ detail: 'Invalid email or password' }, false, 401)),
    )
    const user = userEvent.setup()
    render(<App />)
    await user.clear(screen.getByLabelText('Email'))
    await user.type(screen.getByLabelText('Email'), 'wrong@example.com')
    await user.clear(screen.getByLabelText('Password'))
    await user.type(screen.getByLabelText('Password'), 'incorrect-demo-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password')
  })

  it('searches, filters, paginates, previews, and confirms an import', async () => {
    sessionStorage.setItem('avenward_session', 'existing-token')
    const fetchMock = workspaceFetch()
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Repeated authentication failure')

    await user.type(screen.getByLabelText('Search events'), 'authentication')
    await user.click(screen.getByRole('button', { name: 'Search' }))
    await user.selectOptions(screen.getByLabelText('Filter severity'), 'high')
    expect(fetchMock).toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByText(/Page 2/)).toBeInTheDocument()

    const file = new File([JSON.stringify(event)], 'events.json', { type: 'application/json' })
    fireEvent.change(screen.getByLabelText('Choose event file'), { target: { files: [file] } })
    await user.click(screen.getByRole('button', { name: 'Preview' }))
    expect(await screen.findByText('1 valid events')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Confirm import' }))
    await waitFor(() => expect(screen.queryByText('1 valid events')).not.toBeInTheDocument())
  })

  it('reports workspace loading and file preview errors', async () => {
    sessionStorage.setItem('avenward_session', 'expired-token')
    vi.stubGlobal(
      'fetch',
      vi.fn(() => response({ detail: 'Session is invalid or expired' }, false, 401)),
    )
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Session is invalid or expired')
  })
})
