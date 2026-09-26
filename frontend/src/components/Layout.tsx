import { Link, NavLink, Outlet } from 'react-router-dom'
import { ChatPanel } from './ChatPanel'

export function Layout() {
  return (
    <div className="page">
      <header className="header">
        <Link to="/" className="brand">
          AI Travel Concierge
        </Link>
        <nav className="nav">
          <NavLink to="/" end>
            Browse
          </NavLink>
          <NavLink to="/reservations">Reservations</NavLink>
        </nav>
      </header>
      <Outlet />
      <ChatPanel />
    </div>
  )
}
