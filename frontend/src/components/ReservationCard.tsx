import { useState, type FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ApiError,
  cancelReservation,
  extendReservation,
  reportIssue,
} from '../api/client'
import type { Reservation } from '../api/types'

type Props = {
  reservation: Reservation
}

export function ReservationCard({ reservation }: Props) {
  const queryClient = useQueryClient()
  const [extendDate, setExtendDate] = useState('')
  const [issueText, setIssueText] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const isConfirmed = reservation.status === 'confirmed'

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['reservations'] })
  }

  const cancelMutation = useMutation({
    mutationFn: () => cancelReservation(reservation.id),
    onSuccess: async () => {
      setError(null)
      setMessage('Reservation cancelled.')
      await invalidate()
    },
    onError: (err: unknown) => {
      setMessage(null)
      setError(err instanceof ApiError ? err.message : 'Could not cancel.')
    },
  })

  const extendMutation = useMutation({
    mutationFn: (checkOut: string) => extendReservation(reservation.id, checkOut),
    onSuccess: async () => {
      setError(null)
      setMessage('Stay extended.')
      setExtendDate('')
      await invalidate()
    },
    onError: (err: unknown) => {
      setMessage(null)
      setError(err instanceof ApiError ? err.message : 'Could not extend.')
    },
  })

  const issueMutation = useMutation({
    mutationFn: (description: string) => reportIssue(reservation.id, description),
    onSuccess: async () => {
      setError(null)
      setMessage('Issue reported.')
      setIssueText('')
      await invalidate()
    },
    onError: (err: unknown) => {
      setMessage(null)
      setError(err instanceof ApiError ? err.message : 'Could not report issue.')
    },
  })

  function onExtend(event: FormEvent) {
    event.preventDefault()
    if (!extendDate) {
      setError('Pick a new check-out date.')
      return
    }
    extendMutation.mutate(extendDate)
  }

  function onIssue(event: FormEvent) {
    event.preventDefault()
    if (!issueText.trim()) {
      setError('Describe the issue.')
      return
    }
    issueMutation.mutate(issueText.trim())
  }

  return (
    <article className="reservation-card">
      <div className="card-meta">
        <span>{reservation.city}</span>
        <span className={isConfirmed ? 'status-ok' : 'status-warn'}>
          {reservation.status}
        </span>
      </div>
      <h2>{reservation.property_title}</h2>
      <p>
        {reservation.check_in} → {reservation.check_out} · {reservation.guests} guests
      </p>

      {isConfirmed && (
        <div className="reservation-actions">
          <button
            type="button"
            className="button-secondary"
            disabled={cancelMutation.isPending}
            onClick={() => {
              if (window.confirm('Cancel this reservation?')) {
                cancelMutation.mutate()
              }
            }}
          >
            Cancel
          </button>

          <form className="inline-form" onSubmit={onExtend}>
            <label>
              Extend to
              <input
                type="date"
                min={reservation.check_out}
                value={extendDate}
                onChange={(event) => setExtendDate(event.target.value)}
              />
            </label>
            <button type="submit" disabled={extendMutation.isPending}>
              Extend
            </button>
          </form>

          <form className="inline-form issue-form" onSubmit={onIssue}>
            <label>
              Report issue
              <input
                type="text"
                placeholder="What went wrong?"
                value={issueText}
                onChange={(event) => setIssueText(event.target.value)}
              />
            </label>
            <button type="submit" disabled={issueMutation.isPending}>
              Report
            </button>
          </form>
        </div>
      )}

      {message && <p className="status-ok">{message}</p>}
      {error && <p className="status-bad">{error}</p>}
    </article>
  )
}
