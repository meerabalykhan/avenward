import { useEffect, useState, type FormEvent } from 'react'

import {
  getEvents,
  getMe,
  getOverview,
  importFile,
  login,
  previewFile,
  type EventPage,
  type EventRecord,
  type Overview,
  type User,
} from './api'

const EMPTY_PAGE: EventPage = { items: [], page: 1, page_size: 12, total: 0 }
const severityOrder = ['critical', 'high', 'medium', 'low', 'informational']

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
        <p className="eyebrow">Event explorer · 0.1.0</p>
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
  const [selected, setSelected] = useState<EventRecord | null>(null)
  const [query, setQuery] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)
  const [error, setError] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<{ count: number; sample: EventRecord[] } | null>(null)

  async function load(activeToken = token, activePage = page) {
    try {
      const [identity, summary, result] = await Promise.all([
        getMe(activeToken),
        getOverview(activeToken),
        getEvents(activeToken, query, severity, activePage),
      ])
      setUser(identity)
      setOverview(summary)
      setEvents(result)
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

  function acceptToken(value: string) {
    sessionStorage.setItem('avenward_session', value)
    setToken(value)
  }

  function signOut() {
    sessionStorage.removeItem('avenward_session')
    setToken('')
    setUser(null)
    setSelected(null)
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
          <a className="nav-active" href="#overview">
            Overview
          </a>
          <a href="#events">Events</a>
          <a href="#import">Import</a>
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
          {severityOrder.slice(0, 4).map((level) => (
            <article key={level}>
              <span>{level}</span>
              <strong>{overview.by_severity[level] ?? 0}</strong>
            </article>
          ))}
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
