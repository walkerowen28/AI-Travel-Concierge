import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { PlaceholderPage } from './pages/PlaceholderPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/properties/:id"
          element={<PlaceholderPage title="Property detail" />}
        />
        <Route
          path="/reservations"
          element={<PlaceholderPage title="My reservations" />}
        />
      </Routes>
    </BrowserRouter>
  )
}
