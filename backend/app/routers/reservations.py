from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    BookReservationRequest,
    IssueCreate,
    IssueOut,
    ReservationOut,
    ReservationPatch,
)
from app.services.reservations import (
    book_reservation,
    list_reservations,
    report_issue,
    update_reservation,
)

router = APIRouter(tags=["reservations"])


@router.get("/reservations", response_model=list[ReservationOut])
def get_reservations(db: Session = Depends(get_db)) -> list[ReservationOut]:
    return list_reservations(db)


@router.post("/reservations", response_model=ReservationOut, status_code=201)
def create_reservation(
    body: BookReservationRequest,
    db: Session = Depends(get_db),
) -> ReservationOut:
    return book_reservation(
        db,
        property_id=body.property_id,
        check_in=body.check_in,
        check_out=body.check_out,
        guests=body.guests,
    )


@router.patch("/reservations/{reservation_id}", response_model=ReservationOut)
def patch_reservation(
    reservation_id: int,
    body: ReservationPatch,
    db: Session = Depends(get_db),
) -> ReservationOut:
    return update_reservation(
        db,
        reservation_id,
        action=body.action,
        check_out=body.check_out,
    )


@router.post(
    "/reservations/{reservation_id}/issues",
    response_model=IssueOut,
    status_code=201,
)
def create_issue(
    reservation_id: int,
    body: IssueCreate,
    db: Session = Depends(get_db),
) -> IssueOut:
    return report_issue(db, reservation_id, body.description)
