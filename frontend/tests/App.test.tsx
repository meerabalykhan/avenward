import { act, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from '../src/App'
import { checkApi } from '../src/api'

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('Avenward foundation shell', () => {
  it('explains the release honestly and renders the core principles', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ status: 'ok' }) }),
    )

    render(<App />)

    expect(screen.getByRole('heading', { name: /see the signal/i })).toBeInTheDocument()
    expect(screen.getByText(/no live monitoring data is shown yet/i)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Observe' })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Foundation connected')).toBeInTheDocument())
  })

  it('shows an honest unavailable state when the backend cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))

    render(<App />)

    await waitFor(() => expect(screen.getByText('Backend unavailable')).toBeInTheDocument())
  })

  it('shows unavailable when the health endpoint returns a non-success response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))

    render(<App />)

    await waitFor(() => expect(screen.getByText('Backend unavailable')).toBeInTheDocument())
  })

  it('ignores an expected request cancellation during unmount', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((_url: string, init: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => {
            reject(new DOMException('Request cancelled', 'AbortError'))
          })
        })
      }),
    )
    const { unmount } = render(<App />)

    await act(async () => {
      unmount()
      await Promise.resolve()
    })

    expect(fetch).toHaveBeenCalledOnce()
  })

  it('treats a non-success health response as unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))

    await expect(checkApi(new AbortController().signal)).resolves.toBe(false)
  })

  it('treats an unexpected health payload as unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ status: 'unknown' }) }),
    )

    await expect(checkApi(new AbortController().signal)).resolves.toBe(false)
  })
})
