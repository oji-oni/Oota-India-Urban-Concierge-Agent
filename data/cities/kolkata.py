"""
Kolkata city seed data for Oota India Urban Concierge.
"""
from __future__ import annotations

import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    """Insert all Kolkata data."""
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Kolkata", "kolkata", "West Bengal", 22.5726, 88.3639, "Asia/Kolkata", "Kolkata Metro"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'kolkata'")
    city_id = cur.fetchone()[0]

    neighborhoods = [
        ("Park Street",    22.5486, 88.3516, "High-end dining, pubs, colonial buildings, bustling nightlife"),
        ("Salt Lake",      22.5804, 88.4217, "IT hub, planned sectors, quiet residential, malls, lakes"),
        ("Gariahat",       22.5186, 88.3687, "Traditional shopping district, saree shops, fish market, street food"),
    ]
    nbhd_ids = {}
    for name, lat, lng, vibe in neighborhoods:
        cur.execute(
            "INSERT OR IGNORE INTO neighborhoods (city_id, name, lat, lng, vibe) VALUES (?, ?, ?, ?, ?)",
            (city_id, name, lat, lng, vibe),
        )
    conn.commit()
    for name, *_ in neighborhoods:
        cur.execute("SELECT id FROM neighborhoods WHERE city_id = ? AND name = ?", (city_id, name))
        row = cur.fetchone()
        if row:
            nbhd_ids[name] = row[0]

    metro_stations = [
        ("Kavi Subhash",   22.4735, 88.3846, False, 2),
        ("Mahanayak Uttam Kumar", 22.4842, 88.3475, False, 2),
        ("Kalighat",       22.5188, 88.3472, False, 2),
        ("Jatin Das Park", 22.5255, 88.3474, False, 2),
        ("Rabindra Sadan", 22.5417, 88.3468, False, 2),
        ("Maidan",         22.5487, 88.3469, False, 2),
        ("Park Street",    22.5539, 88.3496, True,  3),
        ("Esplanade",      22.5646, 88.3516, True,  4),
        ("Central",        22.5719, 88.3585, False, 2),
        ("Shambazar",      22.5986, 88.3762, False, 2),
        ("Dum Dum",        22.6224, 88.3789, True,  3),
    ]
    for seq, (name, lat, lng, is_ichange, delay) in enumerate(metro_stations, 1):
        cur.execute(
            "INSERT OR IGNORE INTO transit_stations (city_id, name, system, line_name, line_color, sequence_order, lat, lng, is_interchange, platform_walk_delay_mins) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (city_id, name, "Kolkata Metro", "Blue Line", "#3F51B5", seq, lat, lng, int(is_ichange), delay),
        )
    conn.commit()

    pois = [
        {
            "name": "Mocambo",
            "neighborhood": "Park Street",
            "category": "restaurant",
            "lat": 22.5512, "lng": 88.3524,
            "rating": 4.5,
            "opens_at": "11:15", "closes_at": "23:00",
            "typical_order_to_serve_mins": 15,
            "atmosphere_tags": "continental,heritage,vintage,non-veg",
            "price_range": "₹₹₹",
            "dietary_tags": "non-veg",
            "instructions": "Famous for Devilled Crab, Fish A La Mocambo, and vintage decor.",
        },
        {
            "name": "Dakshineswar Kali Temple",
            "neighborhood": "Park Street",
            "category": "temple",
            "lat": 22.6550, "lng": 88.3575,
            "rating": 4.8,
            "opens_at": "06:00", "closes_at": "20:30",
            "typical_darshana_wait_mins": 45,
            "dress_code": "Modest traditional attire; no shorts",
            "atmosphere_tags": "sacred,riverbank,peaceful,historical",
            "instructions": "Situated on the banks of Hooghly River. Traditional 9-spire temple architecture.",
        }
    ]
    for poi in pois:
        nbhd_id = nbhd_ids.get(poi["neighborhood"])
        cur.execute(
            """
            INSERT OR IGNORE INTO points_of_interest (city_id, name, neighborhood_id, category, lat, lng, rating, opens_at, closes_at, typical_order_to_serve_mins, typical_darshana_wait_mins, dress_code, atmosphere_tags, price_range, dietary_tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (city_id, poi["name"], nbhd_id, poi["category"], poi["lat"], poi["lng"], poi["rating"], poi["opens_at"], poi["closes_at"], poi.get("typical_order_to_serve_mins", 0), poi.get("typical_darshana_wait_mins", 0), poi.get("dress_code"), poi.get("atmosphere_tags"), poi.get("price_range"), poi.get("dietary_tags")),
        )
    conn.commit()
