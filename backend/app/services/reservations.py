from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.constants import DEMO_USER_ID
from app.errors import ConflictError, NotFoundError, ValidationError
from app.models import Issue, IssueStatus, Property, Reservation, ReservationStatus, User
from app.schemas import ReservationOut


def _reservation_out(reservation: Reservation) -> ReservationOut:
    return ReservationOut(
        id=reservation.id,
        property_id=reservation.property_id,
        property_title=reservation.property.title,
        city=reservation.property.city,
        check_in=reservation.check_in,
        check_out=reservation.check_out,
        guests=reservation.guests,
        status=reservation.status,
    )


def _get_demo_user(db: Session) -> User:
    user = db.get(User, DEMO_USER_ID)
    if user is None:
        raise NotFoundError("Demo user is not seeded")
    return user


def _get_reservation(db: Session, reservation_id: int) -> Reservation:
    reservation = db.scalar(
        select(Reservation)
        .options(joinedload(Reservation.property))
        .where(
            Reservation.id == reservation_id,
            Reservation.user_id == DEMO_USER_ID,
        )
    )
    if reservation is None:
        raise NotFoundError("Reservation not found")
    return reservation


def _validate_stay(prop: Property, check_in: date, check_out: date, guests: int) -> None:
    if check_out <= check_in:
        raise ValidationError("check_out must be after check_in")
    if guests > prop.max_guests:
        raise ValidationError(f"This stay allows at most {prop.max_guests} guests")


def _assert_available(
    db: Session,
    property_id: int,
    check_in: date,
    check_out: date,
    *,
    exclude_reservation_id: int | None = None,
) -> None:
    stmt = select(Reservation.id).where(
        Reservation.property_id == property_id,
        Reservation.status == ReservationStatus.CONFIRMED,
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    )
    if exclude_reservation_id is not None:
        stmt = stmt.where(Reservation.id != exclude_reservation_id)
    if db.scalar(stmt.limit(1)) is not None:
        raise ConflictError("Those dates are already booked")


def book_reservation(
    db: Session,
    *,
    property_id: int,
    check_in: date,
    check_out: date,
    guests: int,
) -> ReservationOut:
    prop = db.get(Property, property_id)
    if prop is None:
        raise NotFoundError("Property not found")
    _get_demo_user(db)
    _validate_stay(prop, check_in, check_out, guests)
    _assert_available(db, property_id, check_in, check_out)

    reservation = Reservation(
        user_id=DEMO_USER_ID,
        property_id=property_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        status=ReservationStatus.CONFIRMED,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    reservation.property = prop
    return _reservation_out(reservation)


def list_reservations(db: Session) -> list[ReservationOut]:
    rows = db.scalars(
        select(Reservation)
        .options(joinedload(Reservation.property))
        .where(Reservation.user_id == DEMO_USER_ID)
        .order_by(Reservation.check_in.desc())
    )
    return [_reservation_out(row) for row in rows]


def update_reservation(
    db: Session,
    reservation_id: int,
    *,
    action: str,
    check_out: date | None = None,
) -> ReservationOut:
    reservation = _get_reservation(db, reservation_id)
    if reservation.status != ReservationStatus.CONFIRMED:
        raise ConflictError("Only a confirmed reservation can be changed")

    if action == "cancel":
        reservation.status = ReservationStatus.CANCELLED
    elif action == "extend":
        if check_out is None or check_out <= reservation.check_out:
            raise ValidationError("check_out must be after the current checkout")
        _assert_available(
            db,
            reservation.property_id,
            reservation.check_in,
            check_out,
            exclude_reservation_id=reservation.id,
        )
        reservation.check_out = check_out
    else:
        raise ValidationError("Unknown action")

    db.commit()
    db.refresh(reservation)
    return _reservation_out(reservation)


def report_issue(db: Session, reservation_id: int, description: str) -> Issue:
    reservation = _get_reservation(db, reservation_id)
    if reservation.status != ReservationStatus.CONFIRMED:
        raise ConflictError("Cannot report an issue on a cancelled reservation")
    issue = Issue(
        reservation_id=reservation.id,
        description=description,
        status=IssueStatus.OPEN,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue
