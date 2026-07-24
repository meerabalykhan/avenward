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
export type RuleRecord = {
  id: string
  slug: string
  name: string
  description: string
  version: number
  enabled: boolean
  severity: string
  definition: { threshold: number; window_seconds: number; group_by: string | null }
}
export type AlertRecord = {
  id: string
  status: 'open' | 'acknowledged' | 'resolved'
  severity: string
  title: string
  summary: string
  group_key: string
  rule_version: number
  event_count: number
  first_seen_at: string
  last_seen_at: string
}
export type AlertPage = { items: AlertRecord[]; page: number; page_size: number; total: number }
export type AlertDetail = AlertRecord & {
  rule: RuleRecord
  evidence: Array<{ id: string; title: string; source: string; observed_at: string }>
}
export type FindingRecord = {
  id: string
  source: string
  external_id: string
  asset_identifier: string
  title: string
  severity: string
  cvss_score: number | null
  cve: string | null
  description: string
  remediation: string
  status: 'open' | 'accepted' | 'resolved'
  exception_reason: string | null
  first_seen_at: string
  last_seen_at: string
}
export type FindingPage = { items: FindingRecord[]; page: number; page_size: number; total: number }
export type InvestigationRecord = {
  id: string
  title: string
  summary: string
  severity: string
  status: 'open' | 'in_progress' | 'resolved'
  owner_id: string | null
  resolution: string | null
  created_at: string
  updated_at: string
}
export type InvestigationPage = {
  items: InvestigationRecord[]
  page: number
  page_size: number
  total: number
}
export type InvestigationDetail = InvestigationRecord & {
  links: Array<{
    id: string
    entity_type: string
    entity_id: string
    label: string
    created_at: string
  }>
  comments: Array<{ id: string; author_id: string; body: string; created_at: string }>
  audit: Array<{
    id: string
    actor_id: string
    action: string
    details: Record<string, unknown>
    created_at: string
  }>
}

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
export const getRules = (token: string) => request<RuleRecord[]>('/rules', token)
export const getAlerts = (token: string) => request<AlertPage>('/alerts?page=1&page_size=12', token)
export const getAlertDetail = (token: string, alertId: string) =>
  request<AlertDetail>(`/alerts/${alertId}`, token)
export const changeAlertStatus = (token: string, alertId: string, status: AlertRecord['status']) =>
  request<AlertRecord>(`/alerts/${alertId}/status`, token, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
export const getFindings = (token: string) =>
  request<FindingPage>('/findings?page=1&page_size=12', token)
export const changeFindingStatus = (
  token: string,
  findingId: string,
  status: FindingRecord['status'],
  exceptionReason?: string,
) =>
  request<FindingRecord>(`/findings/${findingId}/status`, token, {
    method: 'PATCH',
    body: JSON.stringify({ status, exception_reason: exceptionReason ?? null }),
  })
export const getInvestigations = (token: string) =>
  request<InvestigationPage>('/investigations?page=1&page_size=12', token)
export const getInvestigationDetail = (token: string, investigationId: string) =>
  request<InvestigationDetail>(`/investigations/${investigationId}`, token)
export const createInvestigation = (
  token: string,
  payload: { title: string; summary: string; severity: string },
) =>
  request<InvestigationRecord>('/investigations', token, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
export const linkInvestigationEvidence = (
  token: string,
  investigationId: string,
  entityType: 'alert' | 'event' | 'finding',
  entityId: string,
) =>
  request(`/investigations/${investigationId}/links`, token, {
    method: 'POST',
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  })
export const updateInvestigation = (
  token: string,
  investigationId: string,
  payload: { status: InvestigationRecord['status']; resolution?: string },
) =>
  request<InvestigationRecord>(`/investigations/${investigationId}`, token, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
export const addInvestigationComment = (token: string, investigationId: string, body: string) =>
  request(`/investigations/${investigationId}/comments`, token, {
    method: 'POST',
    body: JSON.stringify({ body }),
  })
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
