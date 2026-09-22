import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { BrowsePage } from './pages/BrowsePage'
import { PropertyDetailPage } from './pages/PropertyDetailPage'
import { ReservationsPage } from './pages/ReservationsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<BrowsePage />} />
          <Route path="/properties/:id" element={<PropertyDetailPage />} />
          <Route path="/reservations" element={<ReservationsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
