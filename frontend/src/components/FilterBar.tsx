import type { FormEvent } from 'react'
import type { PropertyFilters } from '../api/types'

const CITIES = [
  '',
  'Austin',
  'Portland',
  'Lisbon',
  'Tokyo',
  'Denver',
  'Chicago',
  'Asheville',
  'Seattle',
]

type Props = {
  value: PropertyFilters
  onChange: (next: PropertyFilters) => void
  onSubmit: () => void
}

export function FilterBar({ value, onChange, onSubmit }: Props) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form className="filter-bar" onSubmit={handleSubmit}>
      <label>
        City
        <select
          value={value.city ?? ''}
          onChange={(event) => onChange({ ...value, city: event.target.value || undefined })}
        >
          <option value="">Any city</option>
          {CITIES.filter(Boolean).map((city) => (
            <option key={city} value={city}>
              {city}
            </option>
          ))}
        </select>
      </label>

      <label>
        Max price
        <input
          type="number"
          min={0}
          placeholder="Any"
          value={value.max_price ?? ''}
          onChange={(event) =>
            onChange({
              ...value,
              max_price: event.target.value ? Number(event.target.value) : undefined,
            })
          }
        />
      </label>

      <label>
        Guests
        <input
          type="number"
          min={1}
          placeholder="1+"
          value={value.guests ?? ''}
          onChange={(event) =>
            onChange({
              ...value,
              guests: event.target.value ? Number(event.target.value) : undefined,
            })
          }
        />
      </label>

      <label>
        Check-in
        <input
          type="date"
          value={value.check_in ?? ''}
          onChange={(event) =>
            onChange({ ...value, check_in: event.target.value || undefined })
          }
        />
      </label>

      <label>
        Check-out
        <input
          type="date"
          value={value.check_out ?? ''}
          onChange={(event) =>
            onChange({ ...value, check_out: event.target.value || undefined })
          }
        />
      </label>

      <button type="submit">Search</button>
    </form>
  )
}
