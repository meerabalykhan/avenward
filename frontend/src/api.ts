export type EventRecord = {
  id: string
  source: string
  category: string
  severity: string
  title: string
  actor: string | null
  target: string | null
  observed_at: string
  confidence: number
  summary: string
}

export type EventPage = { items: EventRecord[]; page: number; page_size: number; total: number }
export type Overview = { total: number; by_severity: Record<string, number> }
export type User = { email: string; display_name: string; role: string; organization: string }

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (init?.body && !(init.body instanceof FormData))
    headers.set('Content-Type', 'application/json')
  const response = await fetch(`/api/v1${path}`, { ...init, headers })
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function login(email: string, password: string) {
  return request<{ token: string; user: Omit<User, 'organization'> }>('/auth/login', undefined, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export const getMe = (token: string) => request<User>('/auth/me', token)
export const getOverview = (token: string) => request<Overview>('/events/overview', token)
export const getEvents = (token: string, query: string, severity: string, page: number) => {
  const params = new URLSearchParams({ page: String(page), page_size: '12' })
  if (query) params.set('q', query)
  if (severity) params.set('severity', severity)
  return request<EventPage>(`/events?${params}`, token)
}
export const previewFile = (token: string, file: File) => {
  const body = new FormData()
  body.set('upload', file)
  return request<{ count: number; sample: EventRecord[] }>('/events/preview', token, {
    method: 'POST',
    body,
  })
}
export const importFile = (token: string, file: File) => {
  const body = new FormData()
  body.set('upload', file)
  return request<{ imported: number }>('/events/import', token, { method: 'POST', body })
}
