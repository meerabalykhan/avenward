import { useEffect, useState, type CSSProperties } from 'react'

import { checkApi } from './api'

type ApiState = 'checking' | 'connected' | 'unavailable'

const pillars = [
  {
    number: '01',
    title: 'Observe',
    text: 'Bring authorized security events and infrastructure signals into one coherent view.',
  },
  {
    number: '02',
    title: 'Understand',
    text: 'Connect detections to evidence, confidence, time ranges, and explicit data limitations.',
  },
  {
    number: '03',
    title: 'Investigate',
    text: 'Move deliberately from an unusual signal to an alert, incident, and accountable record.',
  },
]

function App() {
  const [apiState, setApiState] = useState<ApiState>('checking')

  useEffect(() => {
    const controller = new AbortController()
    void checkApi(controller.signal)
      .then((connected) => setApiState(connected ? 'connected' : 'unavailable'))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        setApiState('unavailable')
      })
    return () => controller.abort()
  }, [])

  return (
    <div className="site-shell">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Avenward home">
          <span className="brand-mark" aria-hidden="true">
            A
          </span>
          <span>Avenward</span>
        </a>
        <div className="header-status" role="status" aria-live="polite">
          <span className={`status-dot status-dot--${apiState}`} aria-hidden="true" />
          {apiState === 'checking' && 'Checking foundation'}
          {apiState === 'connected' && 'Foundation connected'}
          {apiState === 'unavailable' && 'Backend unavailable'}
        </div>
      </header>

      <main id="main-content">
        <section className="hero" id="top" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow">Security and operations, composed</p>
            <h1 id="hero-title">
              See the signal.
              <span>Keep the context.</span>
            </h1>
            <p className="hero-summary">
              Avenward is an open, self-hosted workspace for turning authorized operational data
              into evidence-led understanding—without theatrical dashboards or invented certainty.
            </p>
            <div className="hero-actions">
              <a className="primary-action" href="#foundation">
                Explore the foundation
              </a>
              <a className="text-action" href="/api/v1/version">
                Foundation version <span aria-hidden="true">↗</span>
              </a>
            </div>
          </div>

          <div className="signal-card" aria-label="Illustrative signal summary">
            <div className="signal-card__header">
              <span>Evidence posture</span>
              <span className="demo-label">Illustrative</span>
            </div>
            <div className="signal-score">
              <span className="signal-score__value">Calm</span>
              <span className="signal-score__label">by design</span>
            </div>
            <div className="signal-lines" aria-hidden="true">
              <span style={{ '--line': '78%' } as CSSProperties} />
              <span style={{ '--line': '52%' } as CSSProperties} />
              <span style={{ '--line': '66%' } as CSSProperties} />
              <span style={{ '--line': '39%' } as CSSProperties} />
              <span style={{ '--line': '61%' } as CSSProperties} />
            </div>
            <p>
              Future findings will show their source, time range, confidence, and limitations—not
              just a dramatic severity color.
            </p>
          </div>
        </section>

        <section className="foundation" id="foundation" aria-labelledby="foundation-title">
          <div>
            <p className="eyebrow">Version 0.0.1</p>
            <h2 id="foundation-title">A trustworthy beginning.</h2>
          </div>
          <p>
            This release establishes the application boundary, health surface, development stack,
            quality checks, and security decisions. No live monitoring data is shown yet.
          </p>
        </section>

        <section className="pillars" aria-label="Avenward workflow principles">
          {pillars.map((pillar) => (
            <article className="pillar" key={pillar.number}>
              <span>{pillar.number}</span>
              <h3>{pillar.title}</h3>
              <p>{pillar.text}</p>
            </article>
          ))}
        </section>
      </main>

      <footer>
        <span>Avenward · pre-release foundation</span>
        <span>Clarity across security and operations.</span>
      </footer>
    </div>
  )
}

export default App
