from __future__ import annotations

from datetime import date

from agents import RunContextWrapper, function_tool

from app.agent.context import ConciergeContext
from app.errors import AppError
from app.services import properties as property_service
from app.services import reservations as reservation_service


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _err(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return f"Error: {exc.message}"
    return f"Error: {exc}"


@function_tool
def search_properties(
    ctx: RunContextWrapper[ConciergeContext],
    city: str | None = None,
    max_price: int | None = None,
    guests: int | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
) -> str:
    """Search stays by city, max nightly price, guests, and optional dates (YYYY-MM-DD)."""
    try:
        rows = property_service.search_properties(
            ctx.context.db,
            city=city,
            max_price=max_price,
            guests=guests,
            check_in=_parse_date(check_in),
            check_out=_parse_date(check_out),
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace(
        "search_properties",
        f"city={city!r} max_price={max_price} guests={guests} results={len(rows)}",
    )
    if not rows:
        return "No properties matched those filters."

    lines = []
    for prop in rows[:12]:
        lines.append(
            f"#{prop.id} {prop.title} — {prop.city}, ${prop.price_per_night}/night, "
            f"up to {prop.max_guests} guests"
        )
    return "\n".join(lines)


@function_tool
def get_property(
    ctx: RunContextWrapper[ConciergeContext],
    name: str | None = None,
    city: str | None = None,
    property_id: int | None = None,
) -> str:
    """Get full details for one property, including house rules and nearby spots.

    Prefer `name` (the property title as the guest wrote it; typos are fine), optionally
    narrowed by `city`. Only pass `property_id` if it appeared in a tool result this turn.
    """
    db = ctx.context.db
    if name:
        matches = property_service.find_properties_by_name(db, name, city=city)
        ctx.context.trace(
            "get_property", f"name={name!r} city={city!r} matches={len(matches)}"
        )
        if not matches:
            return f"No property named {name!r} was found. Use search_properties to list stays."
        if len(matches) > 1:
            options = "\n".join(f"#{prop.id} {prop.title} — {prop.city}" for prop in matches)
            return f"Several properties match {name!r}; ask the guest which one:\n{options}"
        return _format_property(matches[0])

    if property_id is None:
        return "Error: provide the property name (preferred) or a property_id."
    prop = property_service.get_property(db, property_id)
    ctx.context.trace("get_property", f"property_id={property_id}")
    if prop is None:
        return f"Property {property_id} was not found."
    return _format_property(prop)


def _format_property(prop) -> str:
    nearby = "; ".join(
        f"{spot.get('name')} ({spot.get('kind')}): {spot.get('blurb')}"
        for spot in (prop.nearby or [])
    )
    amenities = ", ".join(prop.amenities or [])
    return (
        f"#{prop.id} {prop.title}\n"
        f"City: {prop.city}\n"
        f"Price: ${prop.price_per_night}/night\n"
        f"Max guests: {prop.max_guests}\n"
        f"Amenities: {amenities}\n"
        f"Description: {prop.description}\n"
        f"House rules: {prop.house_rules}\n"
        f"Nearby: {nearby or 'none listed'}"
    )


@function_tool
def list_reservations(ctx: RunContextWrapper[ConciergeContext]) -> str:
    """List the demo guest's reservations (confirmed and cancelled)."""
    try:
        rows = reservation_service.list_reservations(ctx.context.db)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("list_reservations", f"count={len(rows)}")
    if not rows:
        return "The guest has no reservations yet."

    lines = []
    for row in rows:
        lines.append(
            f"Reservation #{row.id}: {row.property_title} in {row.city}, "
            f"{row.check_in} → {row.check_out}, {row.guests} guests, status={row.status}"
        )
    return "\n".join(lines)


@function_tool
def get_house_rules(
    ctx: RunContextWrapper[ConciergeContext],
    reservation_id: int | None = None,
) -> str:
    """Get house rules for a reservation. Uses chat context reservation_id when omitted."""
    rid = reservation_id if reservation_id is not None else ctx.context.reservation_id
    if rid is None:
        return "Error: reservation_id is required (pass it or open chat from a reservation)."
    try:
        reservation = reservation_service.list_reservations(ctx.context.db)
        match = next((row for row in reservation if row.id == rid), None)
        if match is None:
            return f"Reservation {rid} was not found."
        prop = property_service.get_property(ctx.context.db, match.property_id)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("get_house_rules", f"reservation_id={rid}")
    if prop is None:
        return "Property for that reservation was not found."
    return f"House rules for {prop.title}: {prop.house_rules}"


@function_tool
def suggest_nearby(
    ctx: RunContextWrapper[ConciergeContext],
    reservation_id: int | None = None,
    property_id: int | None = None,
) -> str:
    """Suggest nearby restaurants and activities from seeded property data."""
    pid = property_id
    rid = reservation_id if reservation_id is not None else ctx.context.reservation_id
    try:
        if pid is None and rid is not None:
            rows = reservation_service.list_reservations(ctx.context.db)
            match = next((row for row in rows if row.id == rid), None)
            if match is None:
                return f"Reservation {rid} was not found."
            pid = match.property_id
        if pid is None:
            return "Error: provide property_id or reservation_id (or chat with reservation context)."
        prop = property_service.get_property(ctx.context.db, pid)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("suggest_nearby", f"property_id={pid} reservation_id={rid}")
    if prop is None:
        return f"Property {pid} was not found."
    if not prop.nearby:
        return f"No nearby suggestions are seeded for {prop.title}."
    lines = [f"Nearby for {prop.title}:"]
    for spot in prop.nearby:
        lines.append(f"- {spot.get('name')} ({spot.get('kind')}): {spot.get('blurb')}")
    return "\n".join(lines)


@function_tool
def book_reservation(
    ctx: RunContextWrapper[ConciergeContext],
    property_id: int,
    check_in: str,
    check_out: str,
    guests: int = 1,
) -> str:
    """Book a stay for the demo guest. Dates must be YYYY-MM-DD."""
    try:
        row = reservation_service.book_reservation(
            ctx.context.db,
            property_id=property_id,
            check_in=date.fromisoformat(check_in),
            check_out=date.fromisoformat(check_out),
            guests=guests,
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("book_reservation", f"reservation_id={row.id} property_id={property_id}")
    return (
        f"Booked reservation #{row.id}: {row.property_title} in {row.city}, "
        f"{row.check_in} → {row.check_out}, {row.guests} guests."
    )


@function_tool
def extend_stay(
    ctx: RunContextWrapper[ConciergeContext],
    new_check_out: str,
    reservation_id: int | None = None,
) -> str:
    """Extend a confirmed reservation to a later check-out date (YYYY-MM-DD)."""
    rid = reservation_id if reservation_id is not None else ctx.context.reservation_id
    if rid is None:
        return "Error: reservation_id is required."
    try:
        row = reservation_service.update_reservation(
            ctx.context.db,
            rid,
            action="extend",
            check_out=date.fromisoformat(new_check_out),
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("extend_stay", f"reservation_id={rid} check_out={new_check_out}")
    return (
        f"Extended reservation #{row.id} for {row.property_title}: "
        f"now {row.check_in} → {row.check_out}."
    )


@function_tool
def cancel_reservation(
    ctx: RunContextWrapper[ConciergeContext],
    reservation_id: int | None = None,
) -> str:
    """Cancel a confirmed reservation for the demo guest."""
    rid = reservation_id if reservation_id is not None else ctx.context.reservation_id
    if rid is None:
        return "Error: reservation_id is required."
    try:
        row = reservation_service.update_reservation(
            ctx.context.db,
            rid,
            action="cancel",
        )
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("cancel_reservation", f"reservation_id={rid}")
    return f"Cancelled reservation #{row.id} ({row.property_title})."


@function_tool
def report_issue(
    ctx: RunContextWrapper[ConciergeContext],
    description: str,
    reservation_id: int | None = None,
) -> str:
    """File an issue against a confirmed reservation."""
    rid = reservation_id if reservation_id is not None else ctx.context.reservation_id
    if rid is None:
        return "Error: reservation_id is required."
    try:
        issue = reservation_service.report_issue(ctx.context.db, rid, description)
    except Exception as exc:  # noqa: BLE001
        return _err(exc)

    ctx.context.trace("report_issue", f"reservation_id={rid} issue_id={issue.id}")
    return f"Opened issue #{issue.id} on reservation #{rid}: {issue.description}"


ALL_TOOLS = [
    search_properties,
    get_property,
    list_reservations,
    get_house_rules,
    suggest_nearby,
    book_reservation,
    extend_stay,
    cancel_reservation,
    report_issue,
]
