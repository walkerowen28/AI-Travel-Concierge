from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import NotFoundError, ValidationError
from app.schemas import PropertyOut
from app.services.properties import get_property, search_properties

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyOut])
def list_properties(
    city: str | None = None,
    max_price: int | None = Query(default=None, ge=0),
    guests: int | None = Query(default=None, ge=1),
    check_in: date | None = None,
    check_out: date | None = None,
    db: Session = Depends(get_db),
) -> list[PropertyOut]:
    if (check_in is None) != (check_out is None):
        raise ValidationError("check_in and check_out must be provided together")
    if check_in is not None and check_out is not None and check_out <= check_in:
        raise ValidationError("check_out must be after check_in")
    return search_properties(
        db,
        city=city,
        max_price=max_price,
        guests=guests,
        check_in=check_in,
        check_out=check_out,
    )


@router.get("/{property_id}", response_model=PropertyOut)
def read_property(property_id: int, db: Session = Depends(get_db)) -> PropertyOut:
    prop = get_property(db, property_id)
    if prop is None:
        raise NotFoundError("Property not found")
    return prop
