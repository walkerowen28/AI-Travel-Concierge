"""Load the demo user, catalog, and one upcoming stay.

Run after migrations:

    uv run python -m app.seed
"""

from datetime import date, timedelta

from sqlalchemy import func, select, text

from app.db import SessionLocal
from app.models import Property, Reservation, ReservationStatus, User

DEMO_EMAIL = "alex@example.com"

PROPERTIES: list[dict] = [
    {
        "title": "Rainey Street Loft",
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80",
        "city": "Austin",
        "price_per_night": 189,
        "max_guests": 2,
        "lat": 30.258,
        "lng": -97.738,
        "amenities": ["wifi", "workspace", "ac"],
        "description": "A quiet one-bedroom loft a few blocks from Rainey Street, with a desk and blackout curtains.",
        "house_rules": "No parties. Quiet hours 10pm-8am. No smoking.",
        "nearby": [
            {"name": "Banger's", "kind": "restaurant", "blurb": "Sausage hall and beer garden, a short walk east."},
            {"name": "Lady Bird Lake trail", "kind": "activity", "blurb": "Easy waterfront walk and rental kayaks."},
        ],
    },
    {
        "title": "East Austin Bungalow",
        "image_url": "https://images.unsplash.com/photo-1560448204-603b3fc33ddc?auto=format&fit=crop&w=1200&q=80",
        "city": "Austin",
        "price_per_night": 240,
        "max_guests": 4,
        "lat": 30.262,
        "lng": -97.717,
        "amenities": ["wifi", "kitchen", "parking", "washer"],
        "description": "A 1920s bungalow with a fenced yard, full kitchen, and room for four.",
        "house_rules": "Shoes off inside. Dogs allowed in the yard only.",
        "nearby": [
            {"name": "Veracruz All Natural", "kind": "restaurant", "blurb": "Breakfast tacos on the east side."},
            {"name": "Boggy Creek Farm", "kind": "activity", "blurb": "Morning farm stand a few minutes away."},
        ],
    },
    {
        "title": "Zilker Garden Studio",
        "image_url": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1200&q=80",
        "city": "Austin",
        "price_per_night": 165,
        "max_guests": 2,
        "lat": 30.264,
        "lng": -97.772,
        "amenities": ["wifi", "ac", "bike"],
        "description": "A garden studio near Zilker with a bicycle and a small patio.",
        "house_rules": "No smoking. Checkout by 11am.",
        "nearby": [
            {"name": "Barton Springs", "kind": "activity", "blurb": "Spring-fed pool in Zilker Park."},
            {"name": "Uchi", "kind": "restaurant", "blurb": "Reservation-only sushi, book ahead."},
        ],
    },
    {
        "title": "Alberta Arts Apartment",
        "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1200&q=80",
        "city": "Portland",
        "price_per_night": 155,
        "max_guests": 2,
        "lat": 45.559,
        "lng": -122.646,
        "amenities": ["wifi", "kitchen", "workspace"],
        "description": "A bright apartment above Alberta Street with a work desk and a record player.",
        "house_rules": "No parties. Street parking only.",
        "nearby": [
            {"name": "Pine State Biscuits", "kind": "restaurant", "blurb": "Busy breakfast spot; go early."},
            {"name": "Alberta Park", "kind": "activity", "blurb": "Neighborhood park for a quiet morning walk."},
        ],
    },
    {
        "title": "Hawthorne House",
        "image_url": "https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80",
        "city": "Portland",
        "price_per_night": 210,
        "max_guests": 5,
        "lat": 45.512,
        "lng": -122.621,
        "amenities": ["wifi", "kitchen", "washer", "parking"],
        "description": "A family house near Hawthorne with three bedrooms and a porch.",
        "house_rules": "No smoking. Quiet after 9pm. Kids welcome.",
        "nearby": [
            {"name": "Screen Door", "kind": "restaurant", "blurb": "Southern brunch with a wait on weekends."},
            {"name": "Mt Tabor Park", "kind": "activity", "blurb": "Short hike to a city viewpoint."},
        ],
    },
    {
        "title": "Pearl District Studio",
        "image_url": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1200&q=80",
        "city": "Portland",
        "price_per_night": 198,
        "max_guests": 2,
        "lat": 45.529,
        "lng": -122.685,
        "amenities": ["wifi", "gym", "ac"],
        "description": "A compact studio in the Pearl with a gym downstairs and coffee on the corner.",
        "house_rules": "Building quiet hours 10pm-7am. No smoking.",
        "nearby": [
            {"name": "Tasty n Alder", "kind": "restaurant", "blurb": "Wood-fired brunch downtown."},
            {"name": "Powell's Books", "kind": "activity", "blurb": "The city-block bookstore."},
        ],
    },
    {
        "title": "Alfama Overlook",
        "image_url": "https://images.unsplash.com/photo-1523217582562-09d0def993a6?auto=format&fit=crop&w=1200&q=80",
        "city": "Lisbon",
        "price_per_night": 175,
        "max_guests": 3,
        "lat": 38.713,
        "lng": -9.130,
        "amenities": ["wifi", "kitchen", "view"],
        "description": "A tiled apartment with a river view and a steep walk down to the river.",
        "house_rules": "Stairs only, no elevator. Quiet after 10pm.",
        "nearby": [
            {"name": "Tasca do Chico", "kind": "restaurant", "blurb": "Fado and small plates in the evenings."},
            {"name": "Miradouro da Senhora do Monte", "kind": "activity", "blurb": "Sunset viewpoint a short climb away."},
        ],
    },
    {
        "title": "Principe Real Flat",
        "image_url": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80",
        "city": "Lisbon",
        "price_per_night": 220,
        "max_guests": 4,
        "lat": 38.716,
        "lng": -9.149,
        "amenities": ["wifi", "washer", "workspace", "ac"],
        "description": "A two-bedroom flat near the garden, good for a longer stay with a desk.",
        "house_rules": "No shoes in the bedrooms. Recycling is required.",
        "nearby": [
            {"name": "Cervejaria Ribadouro", "kind": "restaurant", "blurb": "Classic seafood grill nearby."},
            {"name": "Botanical Garden", "kind": "activity", "blurb": "Shady walks a few blocks downhill."},
        ],
    },
    {
        "title": "Baixa Studio",
        "image_url": "https://images.unsplash.com/photo-1501183638710-841dd1904471?auto=format&fit=crop&w=1200&q=80",
        "city": "Lisbon",
        "price_per_night": 140,
        "max_guests": 2,
        "lat": 38.711,
        "lng": -9.138,
        "amenities": ["wifi", "ac"],
        "description": "A small studio between Rossio and the river, noisy on weekends.",
        "house_rules": "No parties. Checkout by 10am.",
        "nearby": [
            {"name": "Time Out Market", "kind": "restaurant", "blurb": "Many counters, best at lunch before the crowd."},
            {"name": "Tram 28 stop", "kind": "activity", "blurb": "The tourist tram; walk the route if the queue is long."},
        ],
    },
    {
        "title": "Yanaka Lane House",
        "image_url": "https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80",
        "city": "Tokyo",
        "price_per_night": 160,
        "max_guests": 3,
        "lat": 35.727,
        "lng": 139.767,
        "amenities": ["wifi", "kitchen", "washer"],
        "description": "A narrow house in Yanaka with a tatami room and a small kitchen.",
        "house_rules": "Remove shoes at the door. No strong perfume. Quiet after 9pm.",
        "nearby": [
            {"name": "Yanaka Ginza", "kind": "activity", "blurb": "A shopping street for snacks and wandering."},
            {"name": "Nezu Cafe", "kind": "restaurant", "blurb": "A small lunch counter; cash is easiest."},
        ],
    },
    {
        "title": "Shimokitazawa Apartment",
        "image_url": "https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80",
        "city": "Tokyo",
        "price_per_night": 145,
        "max_guests": 2,
        "lat": 35.661,
        "lng": 139.668,
        "amenities": ["wifi", "workspace"],
        "description": "A one-room apartment near the record shops, with a fold-down desk.",
        "house_rules": "No guests beyond the booking. Trash sorting is posted on the fridge.",
        "nearby": [
            {"name": "Flash Disc Ranch", "kind": "activity", "blurb": "Used records around the corner."},
            {"name": "Shirube", "kind": "restaurant", "blurb": "Izakaya with a line after 7pm."},
        ],
    },
    {
        "title": "Asakusa Family Room",
        "image_url": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
        "city": "Tokyo",
        "price_per_night": 210,
        "max_guests": 5,
        "lat": 35.714,
        "lng": 139.797,
        "amenities": ["wifi", "kitchen", "washer", "ac"],
        "description": "A larger apartment a few minutes from Senso-ji, with two bedrooms.",
        "house_rules": "No smoking. Leave shoes in the genkan.",
        "nearby": [
            {"name": "Senso-ji", "kind": "activity", "blurb": "Go at opening to avoid the main crush."},
            {"name": "Asakusa Imahan", "kind": "restaurant", "blurb": "Sukiyaki for a sit-down dinner."},
        ],
    },
    {
        "title": "RiNo Loft",
        "image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
        "city": "Denver",
        "price_per_night": 175,
        "max_guests": 2,
        "lat": 39.768,
        "lng": -104.980,
        "amenities": ["wifi", "workspace", "ac"],
        "description": "An industrial loft in RiNo with a long desk and afternoon sun.",
        "house_rules": "No parties. Street parking can fill on weekends.",
        "nearby": [
            {"name": "Denver Central Market", "kind": "restaurant", "blurb": "Several counters for lunch."},
            {"name": "RiNo Art District walls", "kind": "activity", "blurb": "A short mural walk."},
        ],
    },
    {
        "title": "Highland Cottage",
        "image_url": "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
        "city": "Denver",
        "price_per_night": 230,
        "max_guests": 4,
        "lat": 39.762,
        "lng": -105.012,
        "amenities": ["wifi", "kitchen", "parking", "washer"],
        "description": "A cottage in Highland with a driveway and a full kitchen.",
        "house_rules": "No smoking. Quiet after 10pm.",
        "nearby": [
            {"name": "Little Man Ice Cream", "kind": "restaurant", "blurb": "The milk-can stand; expect a line."},
            {"name": "Highland trail", "kind": "activity", "blurb": "An easy walk toward the river."},
        ],
    },
    {
        "title": "Capitol Hill Room",
        "image_url": "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80",
        "city": "Denver",
        "price_per_night": 120,
        "max_guests": 2,
        "lat": 39.733,
        "lng": -104.979,
        "amenities": ["wifi"],
        "description": "A simple room in a shared building near the capitol, best for a short stay.",
        "house_rules": "Shared hallway. No cooking after 9pm. No parties.",
        "nearby": [
            {"name": "Civic Center Park", "kind": "activity", "blurb": "A flat walk to the capitol lawn."},
            {"name": "Hop Alley", "kind": "restaurant", "blurb": "Chinese-American plates a few blocks away."},
        ],
    },
    {
        "title": "Logan Square Flat",
        "image_url": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=80",
        "city": "Chicago",
        "price_per_night": 168,
        "max_guests": 3,
        "lat": 41.923,
        "lng": -87.709,
        "amenities": ["wifi", "kitchen", "workspace"],
        "description": "A flat a block off the boulevard, with a desk and a pull-out sofa.",
        "house_rules": "No smoking. Street cleaning signs are enforceable.",
        "nearby": [
            {"name": "Longman & Eagle", "kind": "restaurant", "blurb": "Brunch and whiskey; no reservations."},
            {"name": "Logan Square monument", "kind": "activity", "blurb": "A loop around the boulevard."},
        ],
    },
    {
        "title": "Wicker Park Walk-up",
        "image_url": "https://images.unsplash.com/photo-1600047509358-9dc75507daeb?auto=format&fit=crop&w=1200&q=80",
        "city": "Chicago",
        "price_per_night": 195,
        "max_guests": 4,
        "lat": 41.910,
        "lng": -87.677,
        "amenities": ["wifi", "kitchen", "washer"],
        "description": "A second-floor walk-up with two bedrooms and a noisy street on weekends.",
        "house_rules": "No parties. Quiet hours start at 10pm on weeknights.",
        "nearby": [
            {"name": "Big Star", "kind": "restaurant", "blurb": "Tacos and a patio; busy after 6."},
            {"name": "606 trail", "kind": "activity", "blurb": "The elevated path starts nearby."},
        ],
    },
    {
        "title": "Lincoln Park Greystone",
        "image_url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=1200&q=80",
        "city": "Chicago",
        "price_per_night": 260,
        "max_guests": 6,
        "lat": 41.925,
        "lng": -87.649,
        "amenities": ["wifi", "kitchen", "parking", "washer", "ac"],
        "description": "A greystone a short walk from the park, with a garage spot and room for six.",
        "house_rules": "No smoking. One parking spot only. No parties.",
        "nearby": [
            {"name": "Lincoln Park Zoo", "kind": "activity", "blurb": "Free admission; go in the morning."},
            {"name": "Cafe Ba-Ba-Reeba", "kind": "restaurant", "blurb": "Tapas for a group dinner."},
        ],
    },
    {
        "title": "Montford Cabin",
        "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=1200&q=80",
        "city": "Asheville",
        "price_per_night": 185,
        "max_guests": 4,
        "lat": 35.596,
        "lng": -82.556,
        "amenities": ["wifi", "kitchen", "fireplace", "parking"],
        "description": "A small cabin in Montford with a wood stove and a gravel drive.",
        "house_rules": "No fireworks. Lock the gate. Quiet after 9pm.",
        "nearby": [
            {"name": "White Duck Taco", "kind": "restaurant", "blurb": "Casual tacos in the River Arts District."},
            {"name": "River Arts District", "kind": "activity", "blurb": "Studios are open most afternoons."},
        ],
    },
    {
        "title": "Downtown Asheville Loft",
        "image_url": "https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80",
        "city": "Asheville",
        "price_per_night": 205,
        "max_guests": 2,
        "lat": 35.595,
        "lng": -82.551,
        "amenities": ["wifi", "ac", "workspace"],
        "description": "A downtown loft above a shop, with a desk and weekend street noise.",
        "house_rules": "No smoking. No balcony parties.",
        "nearby": [
            {"name": "Cucina 24", "kind": "restaurant", "blurb": "Book dinner; the dining room is small."},
            {"name": "Pack Square", "kind": "activity", "blurb": "The city center for an evening walk."},
        ],
    },
    {
        "title": "West Asheville Cottage",
        "image_url": "https://images.unsplash.com/photo-1560184897-ae75f418493e?auto=format&fit=crop&w=1200&q=80",
        "city": "Asheville",
        "price_per_night": 150,
        "max_guests": 3,
        "lat": 35.582,
        "lng": -82.579,
        "amenities": ["wifi", "kitchen", "parking", "washer"],
        "description": "A cottage west of the river with a porch and a washer.",
        "house_rules": "Dogs must be leashed. No smoking indoors.",
        "nearby": [
            {"name": "Sunny Point Cafe", "kind": "restaurant", "blurb": "Breakfast with a patio wait."},
            {"name": "Carrier Park", "kind": "activity", "blurb": "A flat river path for a run."},
        ],
    },
    {
        "title": "Fremont Apartment",
        "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80",
        "city": "Seattle",
        "price_per_night": 172,
        "max_guests": 2,
        "lat": 47.651,
        "lng": -122.350,
        "amenities": ["wifi", "kitchen"],
        "description": "An apartment under the bridge, with a kitchen and a view of the ship canal.",
        "house_rules": "No smoking. Building door code is in the check-in note.",
        "nearby": [
            {"name": "Paseo", "kind": "restaurant", "blurb": "Caribbean sandwiches; they sell out."},
            {"name": "Gas Works Park", "kind": "activity", "blurb": "A short walk to the park hill."},
        ],
    },
    {
        "title": "Ballard House",
        "image_url": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80",
        "city": "Seattle",
        "price_per_night": 240,
        "max_guests": 5,
        "lat": 47.668,
        "lng": -122.384,
        "amenities": ["wifi", "kitchen", "washer", "parking"],
        "description": "A house in Ballard with a driveway, a yard, and room for five.",
        "house_rules": "No parties. Quiet after 10pm. One parking spot.",
        "nearby": [
            {"name": "The Walrus and the Carpenter", "kind": "restaurant", "blurb": "Oysters; the line starts before opening."},
            {"name": "Ballard Locks", "kind": "activity", "blurb": "Watch boats pass in the afternoon."},
        ],
    },
    {
        "title": "Capitol Hill Studio",
        "image_url": "https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=1200&q=80",
        "city": "Seattle",
        "price_per_night": 158,
        "max_guests": 2,
        "lat": 47.623,
        "lng": -122.321,
        "amenities": ["wifi", "workspace"],
        "description": "A studio on Capitol Hill with a desk and nightlife outside on weekends.",
        "house_rules": "No parties. Earplugs are in the drawer.",
        "nearby": [
            {"name": "Volunteer Park", "kind": "activity", "blurb": "A climb to the water tower viewpoint."},
            {"name": "Stateside", "kind": "restaurant", "blurb": "Vietnamese dinner a few blocks away."},
        ],
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count()).select_from(Property))
        if existing:
            by_title = {row["title"]: row["image_url"] for row in PROPERTIES}
            updated = 0
            for prop in db.scalars(select(Property)):
                wanted = by_title.get(prop.title)
                if wanted and prop.image_url != wanted:
                    prop.image_url = wanted
                    updated += 1
            db.commit()
            print(
                f"Catalog already has {existing} properties; "
                f"updated image_url on {updated}."
            )
            return

        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(id=1, name="Alex Guest", email=DEMO_EMAIL)
            db.add(user)
            db.flush()
            db.execute(
                text("SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT MAX(id) FROM users))")
            )

        properties = [Property(**row) for row in PROPERTIES]
        db.add_all(properties)
        db.flush()

        stay = properties[0]
        today = date.today()
        db.add(
            Reservation(
                user_id=user.id,
                property_id=stay.id,
                check_in=today + timedelta(days=14),
                check_out=today + timedelta(days=18),
                guests=2,
                status=ReservationStatus.CONFIRMED,
            )
        )
        db.commit()
        print(f"Seeded user {user.email}, {len(properties)} properties, and 1 reservation.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
