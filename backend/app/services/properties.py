from datetime import date
from difflib import get_close_matches

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


def find_properties_by_name(
    db: Session,
    name: str,
    *,
    city: str | None = None,
    limit: int = 5,
) -> list[Property]:
    """Match a property title the way a guest types it: case-insensitive, partial, or misspelled."""
    stmt = select(Property)
    if city:
        stmt = stmt.where(Property.city.ilike(city))
    candidates = list(db.scalars(stmt))
    wanted = " ".join(name.lower().split())
    if not wanted:
        return []

    exact = [prop for prop in candidates if prop.title.lower() == wanted]
    if exact:
        return exact
    partial = [prop for prop in candidates if wanted in prop.title.lower()]
    if partial:
        return partial[:limit]

    by_title = {prop.title.lower(): prop for prop in candidates}
    close = get_close_matches(wanted, list(by_title), n=limit, cutoff=0.6)
    return [by_title[title] for title in close]
