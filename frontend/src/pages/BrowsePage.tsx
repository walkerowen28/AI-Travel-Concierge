import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ApiError, listProperties } from '../api/client'
import type { PropertyFilters } from '../api/types'
import { FilterBar } from '../components/FilterBar'
import { PropertyCard } from '../components/PropertyCard'

export function BrowsePage() {
  const [draft, setDraft] = useState<PropertyFilters>({})
  const [filters, setFilters] = useState<PropertyFilters>({})

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: ['properties', filters],
    queryFn: () => listProperties(filters),
  })

  return (
    <section>
      <div className="hero">
        <h1>Find a stay</h1>
        <p className="lede">
          Browse the seed catalog by city, price, guests, and dates. Booking uses the demo guest.
        </p>
      </div>

      <FilterBar value={draft} onChange={setDraft} onSubmit={() => setFilters(draft)} />

      {isLoading && <p>Loading properties…</p>}
      {isError && (
        <p className="status-bad">
          {error instanceof ApiError ? error.message : 'Could not load properties.'}
        </p>
      )}
      {data && (
        <>
          <p className="result-count">
            {data.length} stay{data.length === 1 ? '' : 's'}
            {isFetching ? ' · refreshing…' : ''}
          </p>
          <div className="card-grid">
            {data.map((property) => (
              <PropertyCard key={property.id} property={property} />
            ))}
          </div>
          {data.length === 0 && (
            <p className="lede">No stays matched those filters. Try clearing dates or raising the price.</p>
          )}
        </>
      )}
    </section>
  )
}
