export type NearbySpot = {
  name: string
  kind: string
  blurb: string
}

export type Property = {
  id: number
  title: string
  description: string
  city: string
  price_per_night: number
  max_guests: number
  amenities: string[]
  house_rules: string
  image_url: string
  lat: number
  lng: number
  nearby: NearbySpot[]
}

export type PropertyFilters = {
  city?: string
  max_price?: number
  guests?: number
  check_in?: string
  check_out?: string
}

export type Reservation = {
  id: number
  property_id: number
  property_title: string
  city: string
  check_in: string
  check_out: string
  guests: number
  status: string
}

export type BookReservationInput = {
  property_id: number
  check_in: string
  check_out: string
  guests: number
}

export type Issue = {
  id: number
  reservation_id: number
  description: string
  status: string
}
