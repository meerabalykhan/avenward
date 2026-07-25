import { useEffect, useState, type FormEvent } from 'react'

import {
  addInvestigationComment,
  changeAlertStatus,
  changeFindingStatus,
  createInvestigation,
  getAlertDetail,
  getAlerts,
  getEvents,
  getFindings,
  getInvestigationDetail,
  getInvestigations,
  getMe,
  getOverview,
  getRules,
  importFile,
  linkInvestigationEvidence,
  login,
  previewFile,
  updateInvestigation,
  type AlertPage,
  type AlertDetail,
  type EventPage,
  type EventRecord,
  type FindingPage,
  type FindingRecord,
  type InvestigationDetail,
  type InvestigationPage,
  type Overview,
  type RuleRecord,
  type User,
} from './api'

const EMPTY_PAGE: EventPage = { items: [], page: 1, page_size: 12, total: 0 }
const EMPTY_ALERTS: AlertPage = { items: [], page: 1, page_size: 12, total: 0 }
const EMPTY_FINDINGS: FindingPage = { items: [], page: 1, page_size: 12, total: 0 }
const EMPTY_INVESTIGATIONS: InvestigationPage = { items: [], page: 1, page_size: 12, total: 0 }
const severityOrder = ['critical', 'high', 'medium', 'low', 'informational']
const navigationSections = [
  ['overview', 'Overview'],
  ['events', 'Events'],
  ['alerts', 'Alerts'],
  ['investigations', 'Investigations'],
  ['findings', 'Findings'],
  ['rules', 'Rules'],
  ['import', 'Import'],
] as const

function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState('analyst@example.com')
  const [password, setPassword] = useState('avenward-demo-only')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const session = await login(email, password)
      onLogin(session.token)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Sign-in failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-shell">
      <section className="login-copy">
        <a className="brand" href="#top">
          <span className="brand-mark">A</span>
          <span>Avenward</span>
        </a>
        <p className="eyebrow">Investigation workspace · 0.3.0</p>
        <h1>
          Evidence,
          <br />
          <span>made legible.</span>
        </h1>
        <p>
          Explore normalized, synthetic security activity with its source, time, confidence, and
          limitations intact.
        </p>
      </section>
      <form
        className="login-card"
        onSubmit={(event) => {
          void submit(event)
        }}
      >
        <p className="eyebrow">Local demonstration</p>
        <h2>Enter the workspace</h2>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={12}
          />
        </label>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <button className="primary-action" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="fine-print">
          Synthetic data only. Do not expose this development build publicly.
        </p>
      </form>
    </main>
  )
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('avenward_session') ?? '')
  const [user, setUser] = useState<User | null>(null)
  const [overview, setOverview] = useState<Overview>({ total: 0, by_severity: {} })
  const [events, setEvents] = useState<EventPage>(EMPTY_PAGE)
  const [alerts, setAlerts] = useState<AlertPage>(EMPTY_ALERTS)
  const [rules, setRules] = useState<RuleRecord[]>([])
  const [findings, setFindings] = useState<FindingPage>(EMPTY_FINDINGS)
  const [investigations, setInvestigations] = useState<InvestigationPage>(EMPTY_INVESTIGATIONS)
  const [selectedFinding, setSelectedFinding] = useState<FindingRecord | null>(null)
  const [selectedInvestigation, setSelectedInvestigation] = useState<InvestigationDetail | null>(
    null,
  )
  const [selectedAlert, setSelectedAlert] = useState<AlertDetail | null>(null)
  const [selected, setSelected] = useState<EventRecord | null>(null)
  const [query, setQuery] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<{ count: number; sample: EventRecord[] } | null>(null)
  const [comment, setComment] = useState('')
  const [resolution, setResolution] = useState('')
  const [activeSection, setActiveSection] = useState(() =>
    window.location.hash ? window.location.hash.slice(1) : 'overview',
  )

  async function load(activeToken = token, activePage = page) {
    try {
      const [
        identity,
        summary,
        result,
        alertResult,
        ruleResult,
        findingResult,
        investigationResult,
      ] = await Promise.all([
        getMe(activeToken),
        getOverview(activeToken),
        getEvents(activeToken, query, severity, activePage),
        getAlerts(activeToken),
        getRules(activeToken),
        getFindings(activeToken),
        getInvestigations(activeToken),
      ])
      setUser(identity)
      setOverview(summary)
      setEvents(result)
      setAlerts(alertResult)
      setRules(ruleResult)
      setFindings(findingResult)
      setInvestigations(investigationResult)
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Workspace could not be loaded')
    }
  }

  useEffect(() => {
    // Loading is asynchronous; state changes occur after the external API responds.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (token) void load()
  }, [token, page, severity]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const syncSection = () => setActiveSection(window.location.hash.slice(1) || 'overview')
    window.addEventListener('hashchange', syncSection)
    return () => window.removeEventListener('hashchange', syncSection)
  }, [])

  function acceptToken(value: string) {
    sessionStorage.setItem('avenward_session', value)
    setToken(value)
  }

  function signOut() {
    sessionStorage.removeItem('avenward_session')
    setToken('')
    setUser(null)
    setSelected(null)
    setSelectedAlert(null)
    setSelectedFinding(null)
    setSelectedInvestigation(null)
  }

  if (!token) return <Login onLogin={acceptToken} />

  return (
    <div className="workspace-shell">
      <aside className="sidebar">
        <a className="brand" href="#top">
          <span className="brand-mark">A</span>
          <span>Avenward</span>
        </a>
        <nav aria-label="Primary">
          {navigationSections.map(([section, label]) => (
            <a
              className={activeSection === section ? 'nav-active' : undefined}
              href={`#${section}`}
              key={section}
              onClick={() => setActiveSection(section)}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="identity">
          <strong>{user?.display_name ?? 'Loading…'}</strong>
          <span>{user?.organization}</span>
          <button onClick={signOut}>Sign out</button>
        </div>
      </aside>
      <main className="workspace" id="top">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Operational workspace</p>
            <h1>Event explorer</h1>
          </div>
          <span className="live-badge">Synthetic evidence</span>
        </header>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <section id="overview" className="metric-grid" aria-label="Event overview">
          <article>
            <span>Normalized events</span>
            <strong>{overview.total}</strong>
          </article>
          {severityOrder.map((level) => (
            <article key={level}>
              <span>{level}</span>
              <strong>{overview.by_severity[level] ?? 0}</strong>
            </article>
          ))}
          <article>
            <span>Open alerts</span>
            <strong>{alerts.items.filter((alert) => alert.status === 'open').length}</strong>
          </article>
          <article>
            <span>Open investigations</span>
            <strong>
              {investigations.items.filter((item) => item.status !== 'resolved').length}
            </strong>
          </article>
          <article>
            <span>Open findings</span>
            <strong>{findings.items.filter((item) => item.status === 'open').length}</strong>
          </article>
        </section>
        <section className="panel" id="alerts">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Evidence-backed detections</p>
              <h2>Alerts</h2>
            </div>
            <span className="panel-note">{alerts.total} deduplicated alerts</span>
          </div>
          <div className="event-layout">
            <div className="event-list">
              {alerts.items.length ? (
                alerts.items.map((alert) => (
                  <button
                    className={`event-row ${selectedAlert?.id === alert.id ? 'selected' : ''}`}
                    key={alert.id}
                    onClick={() =>
                      void getAlertDetail(token, alert.id)
                        .then(setSelectedAlert)
                        .catch((reason: Error) => setError(reason.message))
                    }
                  >
                    <span className={`severity-dot severity-${alert.severity}`} />
                    <span>
                      <strong>{alert.title}</strong>
                      <small>
                        {alert.group_key} · {alert.event_count} evidence events
                      </small>
                    </span>
                    <b>{alert.status}</b>
                  </button>
                ))
              ) : (
                <p className="empty-state empty-list">
                  No rules have reached their thresholds yet.
                </p>
              )}
            </div>
            <aside className="event-detail">
              {selectedAlert ? (
                <>
                  <p className="eyebrow">Alert rationale</p>
                  <h3>{selectedAlert.title}</h3>
                  <dl>
                    <dt>Status</dt>
                    <dd>{selectedAlert.status}</dd>
                    <dt>Group</dt>
                    <dd>{selectedAlert.group_key}</dd>
                    <dt>Evidence</dt>
                    <dd>{selectedAlert.event_count} events</dd>
                    <dt>Rule</dt>
                    <dd>
                      {selectedAlert.rule.name} · version {selectedAlert.rule_version}
                    </dd>
                  </dl>
                  <p>{selectedAlert.summary}</p>
                  <div className="alert-evidence">
                    <strong>Supporting evidence</strong>
                    {selectedAlert.evidence.map((item) => (
                      <span key={item.id}>
                        {item.title} · {item.source} · {new Date(item.observed_at).toLocaleString()}
                      </span>
                    ))}
                  </div>
                  <div className="alert-actions">
                    {(['open', 'acknowledged', 'resolved'] as const).map((state) => (
                      <button
                        key={state}
                        disabled={selectedAlert.status === state}
                        onClick={() =>
                          void changeAlertStatus(token, selectedAlert.id, state)
                            .then(async (updated) => {
                              setSelectedAlert((current) =>
                                current ? { ...current, ...updated } : current,
                              )
                              await load()
                            })
                            .catch((reason: Error) => setError(reason.message))
                        }
                      >
                        Mark {state}
                      </button>
                    ))}
                  </div>
                  <small>Alert state changes never alter or delete the underlying evidence.</small>
                </>
              ) : (
                <p className="empty-state">Select an alert to inspect why it exists.</p>
              )}
            </aside>
          </div>
        </section>
        <section className="panel" id="investigations">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Accountable casework</p>
              <h2>Investigations</h2>
            </div>
            <span className="panel-note">{investigations.total} cases · append-only history</span>
          </div>
          <div className="event-layout case-layout">
            <div className="event-list">
              {investigations.items.map((item) => (
                <button
                  className={`event-row ${selectedInvestigation?.id === item.id ? 'selected' : ''}`}
                  key={item.id}
                  onClick={() =>
                    void getInvestigationDetail(token, item.id)
                      .then((detail) => {
                        setSelectedInvestigation(detail)
                        setResolution(detail.resolution ?? '')
                      })
                      .catch((reason: Error) => setError(reason.message))
                  }
                >
                  <span className={`severity-dot severity-${item.severity}`} />
                  <span>
                    <strong>{item.title}</strong>
                    <small>
                      {item.status.replace('_', ' ')} · updated{' '}
                      {new Date(item.updated_at).toLocaleString()}
                    </small>
                  </span>
                  <b>{item.severity}</b>
                </button>
              ))}
            </div>
            <aside className="event-detail case-detail">
              {selectedInvestigation ? (
                <>
                  <p className="eyebrow">Investigation record</p>
                  <h3>{selectedInvestigation.title}</h3>
                  <p>{selectedInvestigation.summary}</p>
                  <dl>
                    <dt>Status</dt>
                    <dd>{selectedInvestigation.status.replace('_', ' ')}</dd>
                    <dt>Evidence</dt>
                    <dd>{selectedInvestigation.links.length} linked records</dd>
                    <dt>Comments</dt>
                    <dd>{selectedInvestigation.comments.length}</dd>
                  </dl>
                  <div className="case-timeline">
                    <strong>Linked evidence</strong>
                    {selectedInvestigation.links.map((link) => (
                      <span key={link.id}>
                        {link.entity_type} · {link.label}
                      </span>
                    ))}
                    <strong>Analyst notes</strong>
                    {selectedInvestigation.comments.map((item) => (
                      <span key={item.id}>{item.body}</span>
                    ))}
                    <strong>Audit history</strong>
                    <small>
                      {selectedInvestigation.audit.length} append-only entries · latest five shown
                    </small>
                    {selectedInvestigation.audit.slice(-5).map((item) => (
                      <span key={item.id}>
                        {item.action} · {new Date(item.created_at).toLocaleString()}
                      </span>
                    ))}
                    {selectedInvestigation.resolution && (
                      <>
                        <strong>Resolution record</strong>
                        <span className="resolution-record">
                          {selectedInvestigation.resolution}
                        </span>
                      </>
                    )}
                  </div>
                  {selectedInvestigation.status !== 'resolved' && (
                    <>
                      <form
                        className="case-form"
                        onSubmit={(event) => {
                          event.preventDefault()
                          if (!comment.trim()) return
                          void addInvestigationComment(token, selectedInvestigation.id, comment)
                            .then(async () => {
                              setComment('')
                              setSelectedInvestigation(
                                await getInvestigationDetail(token, selectedInvestigation.id),
                              )
                            })
                            .catch((reason: Error) => setError(reason.message))
                        }}
                      >
                        <label>
                          Add analyst note
                          <textarea
                            value={comment}
                            onChange={(event) => setComment(event.target.value)}
                          />
                        </label>
                        <button disabled={!comment.trim()}>Add note</button>
                      </form>
                      <div className="case-form">
                        <label>
                          Resolution
                          <textarea
                            value={resolution}
                            onChange={(event) => setResolution(event.target.value)}
                          />
                        </label>
                        <div className="alert-actions">
                          <button
                            disabled={selectedInvestigation.status === 'in_progress'}
                            onClick={() =>
                              void updateInvestigation(token, selectedInvestigation.id, {
                                status: 'in_progress',
                              })
                                .then(async () => {
                                  setSelectedInvestigation(
                                    await getInvestigationDetail(token, selectedInvestigation.id),
                                  )
                                  await load()
                                })
                                .catch((reason: Error) => setError(reason.message))
                            }
                          >
                            Start work
                          </button>
                          <button
                            disabled={!resolution.trim()}
                            onClick={() =>
                              void updateInvestigation(token, selectedInvestigation.id, {
                                status: 'resolved',
                                resolution,
                              })
                                .then(async () => {
                                  setSelectedInvestigation(
                                    await getInvestigationDetail(token, selectedInvestigation.id),
                                  )
                                  await load()
                                })
                                .catch((reason: Error) => setError(reason.message))
                            }
                          >
                            Resolve with record
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </>
              ) : (
                <p className="empty-state">
                  Select an investigation to review its complete timeline.
                </p>
              )}
            </aside>
          </div>
        </section>
        <section className="panel" id="findings">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Imported scanner evidence</p>
              <h2>Vulnerability findings</h2>
            </div>
            <span className="panel-note">Findings are not proof of compromise</span>
          </div>
          <div className="event-layout finding-layout">
            <div className="event-list">
              {findings.items.map((item) => (
                <button
                  className={`event-row ${selectedFinding?.id === item.id ? 'selected' : ''}`}
                  key={item.id}
                  onClick={() => setSelectedFinding(item)}
                >
                  <span className={`severity-dot severity-${item.severity}`} />
                  <span>
                    <strong>{item.title}</strong>
                    <small>
                      {item.asset_identifier} · {item.cve ?? item.external_id}
                    </small>
                  </span>
                  <b>{item.status}</b>
                </button>
              ))}
            </div>
            <aside className="event-detail">
              {selectedFinding ? (
                <>
                  <div className="detail-kicker">
                    <p className="eyebrow">Finding detail</p>
                    <span className="synthetic-label">Synthetic demonstration</span>
                  </div>
                  <h3>{selectedFinding.title}</h3>
                  <dl>
                    <dt>Asset</dt>
                    <dd>{selectedFinding.asset_identifier}</dd>
                    <dt>Source</dt>
                    <dd>{selectedFinding.source}</dd>
                    <dt>Reference</dt>
                    <dd>{selectedFinding.cve ?? selectedFinding.external_id}</dd>
                    <dt>CVSS</dt>
                    <dd>{selectedFinding.cvss_score ?? 'Not supplied'}</dd>
                    <dt>Status</dt>
                    <dd>{selectedFinding.status}</dd>
                  </dl>
                  <p>{selectedFinding.description}</p>
                  <strong>Remediation guidance</strong>
                  <p>{selectedFinding.remediation}</p>
                  <div className="alert-actions">
                    <button
                      onClick={() =>
                        void createInvestigation(token, {
                          title: `Review ${selectedFinding.title}`,
                          summary: `Validate the imported finding on ${selectedFinding.asset_identifier} and document the approved response.`,
                          severity: selectedFinding.severity,
                        })
                          .then(async (created) => {
                            await linkInvestigationEvidence(
                              token,
                              created.id,
                              'finding',
                              selectedFinding.id,
                            )
                            await load()
                            setSelectedInvestigation(
                              await getInvestigationDetail(token, created.id),
                            )
                          })
                          .catch((reason: Error) => setError(reason.message))
                      }
                    >
                      Open investigation
                    </button>
                    <button
                      disabled={selectedFinding.status === 'resolved'}
                      onClick={() =>
                        void changeFindingStatus(token, selectedFinding.id, 'resolved')
                          .then(async (updated) => {
                            setSelectedFinding(updated)
                            await load()
                          })
                          .catch((reason: Error) => setError(reason.message))
                      }
                    >
                      Mark resolved
                    </button>
                  </div>
                  <small>
                    Imported scanner content is displayed as untrusted evidence and never executed.
                  </small>
                </>
              ) : (
                <p className="empty-state">
                  Select a finding to inspect its affected asset and guidance.
                </p>
              )}
            </aside>
          </div>
        </section>
        <section className="panel rules-panel" id="rules">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Versioned policy</p>
              <h2>Detection rules</h2>
            </div>
            <span className="panel-note">Data-only · no executable expressions</span>
          </div>
          <div className="rule-grid">
            {rules.map((rule) => (
              <article key={rule.id}>
                <span className={`severity-label severity-text-${rule.severity}`}>
                  {rule.severity}
                </span>
                <h3>{rule.name}</h3>
                <p>{rule.description}</p>
                <small>
                  v{rule.version} · threshold {rule.definition.threshold} ·{' '}
                  {Math.round(rule.definition.window_seconds / 60)} minute window
                </small>
              </article>
            ))}
          </div>
        </section>
        <section className="panel" id="events">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Evidence stream</p>
              <h2>Recent activity</h2>
            </div>
            <form
              className="filters"
              onSubmit={(e) => {
                e.preventDefault()
                setPage(1)
                void load(token, 1)
              }}
            >
              <input
                aria-label="Search events"
                placeholder="Search title, actor, target"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <select
                aria-label="Filter severity"
                value={severity}
                onChange={(e) => {
                  setSeverity(e.target.value)
                  setPage(1)
                }}
              >
                <option value="">All severities</option>
                {severityOrder.map((level) => (
                  <option key={level}>{level}</option>
                ))}
              </select>
              <button>Search</button>
            </form>
          </div>
          <div className="event-layout">
            <div className="event-list">
              {events.items.map((item) => (
                <button
                  className={`event-row ${selected?.id === item.id ? 'selected' : ''}`}
                  data-testid={`event-${item.id}`}
                  key={item.id}
                  onClick={() => setSelected(item)}
                >
                  <span className={`severity-dot severity-${item.severity}`} />
                  <span>
                    <strong>{item.title}</strong>
                    <small>
                      {item.source} · {new Date(item.observed_at).toLocaleString()}
                    </small>
                  </span>
                  <b>{item.confidence}%</b>
                </button>
              ))}
            </div>
            <aside className="event-detail">
              {selected ? (
                <>
                  <p className="eyebrow">Event detail</p>
                  <h3>{selected.title}</h3>
                  <dl>
                    <dt>Source</dt>
                    <dd>{selected.source}</dd>
                    <dt>Observed</dt>
                    <dd>{new Date(selected.observed_at).toLocaleString()}</dd>
                    <dt>Confidence</dt>
                    <dd>{selected.confidence}%</dd>
                    <dt>Actor</dt>
                    <dd>{selected.actor ?? 'Not supplied'}</dd>
                    <dt>Target</dt>
                    <dd>{selected.target ?? 'Not supplied'}</dd>
                  </dl>
                  <p>{selected.summary}</p>
                  <small>
                    Confidence reflects supplied evidence quality; it is not an AI verdict.
                  </small>
                </>
              ) : (
                <p className="empty-state">Select an event to inspect its context.</p>
              )}
            </aside>
          </div>
          <div className="pagination">
            <button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>
              Previous
            </button>
            <span>
              Page {page} · {events.total} events
            </span>
            <button
              disabled={page * events.page_size >= events.total}
              onClick={() => setPage((value) => value + 1)}
            >
              Next
            </button>
          </div>
        </section>
        <section className="panel import-panel" id="import">
          <div>
            <p className="eyebrow">Controlled ingestion</p>
            <h2>Preview before import</h2>
            <p>
              UTF-8 CSV, JSON, or JSONL. Maximum 2 MB and 5,000 events. Files are parsed as data and
              never executed.
            </p>
          </div>
          <div className="import-controls">
            <input
              aria-label="Choose event file"
              type="file"
              accept=".csv,.json,.jsonl"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null)
                setPreview(null)
              }}
            />
            <button
              disabled={!file}
              onClick={() =>
                file &&
                void previewFile(token, file)
                  .then(setPreview)
                  .catch((reason: Error) => setError(reason.message))
              }
            >
              Preview
            </button>
            {preview && (
              <div className="preview-result">
                <strong>{preview.count} valid events</strong>
                <span>{preview.sample.length} shown in the safe preview</span>
                <button
                  className="primary-action"
                  onClick={() =>
                    file &&
                    void importFile(token, file)
                      .then(async () => {
                        setPreview(null)
                        setFile(null)
                        await load()
                      })
                      .catch((reason: Error) => setError(reason.message))
                  }
                >
                  Confirm import
                </button>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
