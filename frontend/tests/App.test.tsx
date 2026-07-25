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
const finding = {
  id: 'da8ac937-0d30-4ced-98d6-a5c595a73cd7',
  source: 'synthetic-scanner',
  external_id: 'AVEN-DEMO-001',
  asset_identifier: 'lab-web-01',
  title: 'Outdated demonstration web component',
  severity: 'high',
  cvss_score: 8.1,
  cve: null,
  description: 'Synthetic scanner output.',
  remediation: 'Test and deploy the supported update.',
  status: 'open',
  exception_reason: null,
  first_seen_at: '2026-07-22T10:00:00Z',
  last_seen_at: '2026-07-24T10:00:00Z',
}
const investigation = {
  id: 'fe3e704d-069c-4cc8-aa84-f00a725250ff',
  title: 'Review lab web exposure',
  summary: 'Confirm the finding and document the approved remediation path.',
  severity: 'high',
  status: 'open',
  owner_id: '4d94896d-2c52-4966-8d4c-f6fb4f60f133',
  resolution: null,
  created_at: '2026-07-24T10:00:00Z',
  updated_at: '2026-07-24T10:00:00Z',
}
const investigationDetail = {
  ...investigation,
  links: [
    {
      id: 'bd719ec4-29a5-4033-b5aa-a91c148bf14e',
      entity_type: 'finding',
      entity_id: finding.id,
      label: finding.title,
      created_at: investigation.created_at,
    },
  ],
  comments: [
    {
      id: '3ad8dbcc-14aa-43ef-8674-393815ec8109',
      author_id: investigation.owner_id,
      body: 'Synthetic case created for testing.',
      created_at: investigation.created_at,
    },
  ],
  audit: [
    {
      id: '02658298-e255-47c7-a4f2-1e09f7994be9',
      actor_id: investigation.owner_id,
      action: 'investigation.created',
      details: { synthetic: true },
      created_at: investigation.created_at,
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
    if (url.endsWith('/events/overview'))
      return response({ total: 2, by_severity: { high: 1, informational: 1 } })
    if (url.includes('/alerts?'))
      return response({ items: [alert], page: 1, page_size: 12, total: 1 })
    if (url.endsWith('/rules')) return response([rule])
    if (url.includes('/findings?'))
      return response({ items: [finding], page: 1, page_size: 12, total: 1 })
    if (url.includes('/findings/') && url.endsWith('/status'))
      return response({ ...finding, status: 'resolved' })
    if (url.includes('/investigations?'))
      return response({ items: [investigation], page: 1, page_size: 12, total: 1 })
    if (url.endsWith('/investigations')) return response(investigation, true, 201)
    if (url.includes('/investigations/') && url.endsWith('/links')) return response({}, true, 201)
    if (url.includes('/investigations/') && url.endsWith('/comments'))
      return response({}, true, 201)
    if (url.includes('/investigations/')) return response(investigationDetail)
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
    const eventButton = await screen.findByTestId(`event-${event.id}`)
    expect(eventButton).toBeInTheDocument()
    expect(screen.getAllByText('Repeated authentication failures').length).toBeGreaterThan(0)
    expect(screen.getByText(/Three authentication failure events/)).toBeInTheDocument()
    expect(screen.getAllByText('informational').length).toBeGreaterThanOrEqual(2)

    await user.click(eventButton)
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

  it('reviews findings and accountable investigation history', async () => {
    sessionStorage.setItem('avenward_session', 'existing-token')
    const fetchMock = workspaceFetch()
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()
    render(<App />)

    const caseButton = await screen.findByRole('button', { name: /Review lab web exposure/ })
    await user.click(caseButton)
    expect(await screen.findByText('Linked evidence')).toBeInTheDocument()
    expect(screen.getByText('investigation.created', { exact: false })).toBeInTheDocument()
    expect(screen.getByText('Synthetic case created for testing.')).toBeInTheDocument()

    await user.type(screen.getByLabelText('Add analyst note'), 'Validated by the test analyst.')
    await user.click(screen.getByRole('button', { name: 'Add note' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/investigations/${investigation.id}/comments`),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
    await user.click(screen.getByRole('button', { name: 'Start work' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/investigations/${investigation.id}`),
        expect.objectContaining({ method: 'PATCH' }),
      ),
    )
    await user.type(screen.getByLabelText('Resolution'), 'Synthetic update completed safely.')
    await user.click(screen.getByRole('button', { name: 'Resolve with record' }))

    const findingButton = screen.getByRole('button', {
      name: /Outdated demonstration web component/,
    })
    await user.click(findingButton)
    expect(screen.getByText('Synthetic demonstration')).toBeInTheDocument()
    expect(screen.getByText('AVEN-DEMO-001')).toBeInTheDocument()
    expect(screen.getByText('Test and deploy the supported update.')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Imported scanner content is displayed as untrusted evidence and never executed.',
      ),
    ).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Mark resolved' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining(`/findings/${finding.id}/status`),
        expect.objectContaining({ method: 'PATCH' }),
      ),
    )
    await user.click(screen.getByRole('button', { name: 'Open investigation' }))
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/investigations'),
        expect.objectContaining({ method: 'POST' }),
      ),
    )
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
    await user.click(screen.getByRole('button', { name: 'Previous' }))
    expect(await screen.findByText(/Page 1/)).toBeInTheDocument()

    const findingsNavigation = screen.getByRole('link', { name: 'Findings' })
    await user.click(findingsNavigation)
    expect(findingsNavigation).toHaveClass('nav-active')

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
