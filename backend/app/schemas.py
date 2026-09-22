from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class NearbySpot(BaseModel):
    name: str
    kind: str
    blurb: str


class PropertyOut(BaseModel):
    id: int
    title: str
    description: str
    city: str
    price_per_night: int
    max_guests: int
    amenities: list[str]
    house_rules: str
    image_url: str
    lat: float
    lng: float
    nearby: list[NearbySpot]

    model_config = {"from_attributes": True}


class BookReservationRequest(BaseModel):
    property_id: int
    check_in: date
    check_out: date
    guests: int = Field(ge=1)


class ReservationPatch(BaseModel):
    action: Literal["cancel", "extend"]
    check_out: date | None = None

    @model_validator(mode="after")
    def extend_requires_checkout(self) -> "ReservationPatch":
        if self.action == "extend" and self.check_out is None:
            raise ValueError("check_out is required to extend a stay")
        return self


class ReservationOut(BaseModel):
    id: int
    property_id: int
    property_title: str
    city: str
    check_in: date
    check_out: date
    guests: int
    status: str


class IssueCreate(BaseModel):
    description: str = Field(min_length=1, max_length=2000)


class IssueOut(BaseModel):
    id: int
    reservation_id: int
    description: str
    status: str

    model_config = {"from_attributes": True}
