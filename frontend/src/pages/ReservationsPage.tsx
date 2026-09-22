import { useQuery } from '@tanstack/react-query'
import { ApiError, listReservations } from '../api/client'
import { ReservationCard } from '../components/ReservationCard'

export function ReservationsPage() {
  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: ['reservations'],
    queryFn: listReservations,
  })

  return (
    <section>
      <div className="hero">
        <h1>My reservations</h1>
        <p className="lede">
          Stays for the demo guest. Cancel, extend, or report an issue on confirmed bookings.
        </p>
      </div>

      {isLoading && <p>Loading reservations…</p>}
      {isError && (
        <p className="status-bad">
          {error instanceof ApiError ? error.message : 'Could not load reservations.'}
        </p>
      )}
      {data && (
        <>
          <p className="result-count">
            {data.length} reservation{data.length === 1 ? '' : 's'}
            {isFetching ? ' · refreshing…' : ''}
          </p>
          <div className="stack">
            {data.map((reservation) => (
              <ReservationCard key={reservation.id} reservation={reservation} />
            ))}
          </div>
          {data.length === 0 && (
            <p className="lede">No reservations yet. Book something from Browse.</p>
          )}
        </>
      )}
    </section>
  )
}
