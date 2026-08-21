import { Link } from 'react-router-dom'

export function PlaceholderPage({ title }: { title: string }) {
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
        <h1>{title}</h1>
        <p className="lede">Coming in Block 2.</p>
      </section>
    </main>
  )
}
