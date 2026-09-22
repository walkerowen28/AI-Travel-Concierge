import { Link } from 'react-router-dom'
import type { Property } from '../api/types'

type Props = {
  property: Property
}

export function PropertyCard({ property }: Props) {
  return (
    <Link to={`/properties/${property.id}`} className="property-card">
      <img
        className="property-image"
        src={property.image_url}
        alt={property.title}
        loading="lazy"
      />
      <div className="card-meta">
        <span>{property.city}</span>
        <span>Up to {property.max_guests} guests</span>
      </div>
      <h2>{property.title}</h2>
      <p>{property.description}</p>
      <p className="price">
        ${property.price_per_night}
        <span> / night</span>
      </p>
    </Link>
  )
}
