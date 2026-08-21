import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getHealth } from '../api/client'

export function HomePage() {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 10_000,
  })

  return (
    <main className="page">
      <header className="header">
        <p className="brand">AI Travel Concierge</p>
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/reservations">Reservations</Link>
        </nav>
      </header>

      <section className="hero">
        <h1>Stack health</h1>
        <p className="lede">
          Block 0 smoke check: UI → Vite proxy → FastAPI → Postgres.
        </p>

        <div className="health-panel" aria-live="polite">
          {isLoading && <p>Checking API…</p>}
          {isError && (
            <p className="status-bad">
              Could not reach API: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          )}
          {data && (
            <dl className="health-grid">
              <div>
                <dt>API status</dt>
                <dd className={data.status === 'ok' ? 'status-ok' : 'status-warn'}>
                  {data.status}
                </dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd className={data.database === 'up' ? 'status-ok' : 'status-bad'}>
                  {data.database}
                </dd>
              </div>
            </dl>
          )}
          <button type="button" onClick={() => void refetch()} disabled={isFetching}>
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </button>
        </div>
      </section>
    </main>
  )
}
