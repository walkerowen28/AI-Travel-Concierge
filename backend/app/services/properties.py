from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Property, Reservation, ReservationStatus


def search_properties(
    db: Session,
    *,
    city: str | None = None,
    max_price: int | None = None,
    guests: int | None = None,
    check_in: date | None = None,
    check_out: date | None = None,
) -> list[Property]:
    stmt = select(Property)
    if city:
        stmt = stmt.where(Property.city.ilike(city))
    if max_price is not None:
        stmt = stmt.where(Property.price_per_night <= max_price)
    if guests is not None:
        stmt = stmt.where(Property.max_guests >= guests)
    if check_in is not None and check_out is not None:
        busy = select(Reservation.property_id).where(
            Reservation.status == ReservationStatus.CONFIRMED,
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        )
        stmt = stmt.where(Property.id.not_in(busy))
    return list(db.scalars(stmt.order_by(Property.city, Property.title)))


def get_property(db: Session, property_id: int) -> Property | None:
    return db.get(Property, property_id)
