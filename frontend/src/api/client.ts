import type {
  BookReservationInput,
  Issue,
  Property,
  PropertyFilters,
  Reservation,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const body = (await response.json()) as { detail?: string | { msg?: string }[] }
      if (typeof body.detail === 'string') {
        detail = body.detail
      } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
        detail = body.detail[0].msg
      }
    } catch {
      // keep default message
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

function toQuery(filters: PropertyFilters): string {
  const params = new URLSearchParams()
  if (filters.city?.trim()) params.set('city', filters.city.trim())
  if (filters.max_price != null && !Number.isNaN(filters.max_price)) {
    params.set('max_price', String(filters.max_price))
  }
  if (filters.guests != null && !Number.isNaN(filters.guests)) {
    params.set('guests', String(filters.guests))
  }
  if (filters.check_in) params.set('check_in', filters.check_in)
  if (filters.check_out) params.set('check_out', filters.check_out)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function listProperties(filters: PropertyFilters = {}): Promise<Property[]> {
  return request<Property[]>(`/api/properties${toQuery(filters)}`)
}

export function getProperty(id: number): Promise<Property> {
  return request<Property>(`/api/properties/${id}`)
}

export function listReservations(): Promise<Reservation[]> {
  return request<Reservation[]>('/api/reservations')
}

export function bookReservation(input: BookReservationInput): Promise<Reservation> {
  return request<Reservation>('/api/reservations', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function cancelReservation(id: number): Promise<Reservation> {
  return request<Reservation>(`/api/reservations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action: 'cancel' }),
  })
}

export function extendReservation(id: number, check_out: string): Promise<Reservation> {
  return request<Reservation>(`/api/reservations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ action: 'extend', check_out }),
  })
}

export function reportIssue(id: number, description: string): Promise<Issue> {
  return request<Issue>(`/api/reservations/${id}/issues`, {
    method: 'POST',
    body: JSON.stringify({ description }),
  })
}
