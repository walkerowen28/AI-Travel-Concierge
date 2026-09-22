import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, bookReservation, getProperty } from '../api/client'

export function PropertyDetailPage() {
  const { id } = useParams()
  const propertyId = Number(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [guests, setGuests] = useState(1)
  const [formError, setFormError] = useState<string | null>(null)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['property', propertyId],
    queryFn: () => getProperty(propertyId),
    enabled: Number.isFinite(propertyId) && propertyId > 0,
  })

  const bookMutation = useMutation({
    mutationFn: bookReservation,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['reservations'] })
      await queryClient.invalidateQueries({ queryKey: ['properties'] })
      navigate('/reservations')
    },
    onError: (err: unknown) => {
      setFormError(err instanceof ApiError ? err.message : 'Could not book this stay.')
    },
  })

  function onBook(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    if (!checkIn || !checkOut) {
      setFormError('Choose check-in and check-out dates.')
      return
    }
    bookMutation.mutate({
      property_id: propertyId,
      check_in: checkIn,
      check_out: checkOut,
      guests,
    })
  }

  if (!Number.isFinite(propertyId) || propertyId <= 0) {
    return <p className="status-bad">Invalid property id.</p>
  }

  if (isLoading) return <p>Loading stay…</p>
  if (isError || !data) {
    return (
      <p className="status-bad">
        {error instanceof ApiError ? error.message : 'Property not found.'}{' '}
        <Link to="/">Back to browse</Link>
      </p>
    )
  }

  return (
    <section className="detail">
      <img
        className="detail-image"
        src={data.image_url}
        alt={data.title}
      />
      <p className="eyebrow">{data.city}</p>
      <h1>{data.title}</h1>
      <p className="lede">{data.description}</p>
      <p className="price">
        ${data.price_per_night}
        <span> / night · up to {data.max_guests} guests</span>
      </p>

      <div className="detail-grid">
        <div>
          <h2>Amenities</h2>
          <ul className="chip-list">
            {data.amenities.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <h2>House rules</h2>
          <p>{data.house_rules}</p>

          <h2>Nearby</h2>
          <ul className="nearby-list">
            {data.nearby.map((spot) => (
              <li key={`${spot.kind}-${spot.name}`}>
                <strong>{spot.name}</strong>
                <span className="muted"> · {spot.kind}</span>
                <p>{spot.blurb}</p>
              </li>
            ))}
          </ul>
        </div>

        <form className="book-form" onSubmit={onBook}>
          <h2>Book this stay</h2>
          <label>
            Check-in
            <input
              type="date"
              value={checkIn}
              onChange={(event) => setCheckIn(event.target.value)}
              required
            />
          </label>
          <label>
            Check-out
            <input
              type="date"
              value={checkOut}
              onChange={(event) => setCheckOut(event.target.value)}
              required
            />
          </label>
          <label>
            Guests
            <input
              type="number"
              min={1}
              max={data.max_guests}
              value={guests}
              onChange={(event) => setGuests(Number(event.target.value))}
              required
            />
          </label>
          {formError && <p className="status-bad">{formError}</p>}
          <button type="submit" disabled={bookMutation.isPending}>
            {bookMutation.isPending ? 'Booking…' : 'Book reservation'}
          </button>
        </form>
      </div>
    </section>
  )
}
