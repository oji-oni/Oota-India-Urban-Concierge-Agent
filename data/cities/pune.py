"""
Pune city seed data for Oota India Urban Concierge.
"""
from __future__ import annotations

import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    """Insert all Pune data."""
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Pune", "pune", "Maharashtra", 18.5204, 73.8567, "Asia/Kolkata", "Pune Metro"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'pune'")
    city_id = cur.fetchone()[0]

    neighborhoods = [
        ("Koregaon Park",  18.5362, 73.8930, "Upscale residential, restaurants, bars, green lanes, Osho Ashram"),
        ("Kothrud",        18.5074, 73.8077, "Residential suburb, highly populated, traditional Maharashtrian cultural feel"),
        ("Viman Nagar",    18.5679, 73.9143, "IT parks, close to airport, malls, students, cafes"),
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
        ("PCMC",           18.6229, 73.8021, False, 2),
        ("Bhosari",        18.6083, 73.8118, False, 2),
        ("Khadki",         18.5615, 73.8322, False, 2),
        ("Shivajinagar",   18.5317, 73.8499, True,  3),
        ("Civil Court",    18.5273, 73.8541, True,  4),
        ("District Court", 18.5262, 73.8567, True,  4),
        ("Vanaz",          18.5074, 73.8055, False, 2),
        ("Anand Nagar",    18.5115, 73.8156, False, 2),
        ("Nal Stop",       18.5126, 73.8327, False, 2),
        ("Garware College", 18.5165, 73.8415, False, 2),
        ("Ramwadi",        18.5618, 73.9212, False, 2),
    ]
    for seq, (name, lat, lng, is_ichange, delay) in enumerate(metro_stations, 1):
        cur.execute(
            "INSERT OR IGNORE INTO transit_stations (city_id, name, system, line_name, line_color, sequence_order, lat, lng, is_interchange, platform_walk_delay_mins) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (city_id, name, "Pune Metro", "Purple Line", "#9C27B0", seq, lat, lng, int(is_ichange), delay),
        )
    conn.commit()

    pois = [
        {
            "name": "German Bakery",
            "neighborhood": "Koregaon Park",
            "category": "restaurant",
            "lat": 18.5361, "lng": 73.8932,
            "rating": 4.3,
            "opens_at": "08:00", "closes_at": "23:00",
            "typical_order_to_serve_mins": 15,
            "atmosphere_tags": "cafe,bakery,iconic,lively",
            "price_range": "₹₹",
            "dietary_tags": "veg,non-veg",
            "instructions": "Famous for Kheema Pav, Mango Cheesecake, and outdoor cafe vibe.",
        },
        {
            "name": "Dagdusheth Halwai Ganpati Temple",
            "neighborhood": "Kothrud",
            "category": "temple",
            "lat": 18.5162, "lng": 73.8562,
            "rating": 4.9,
            "opens_at": "06:00", "closes_at": "23:00",
            "typical_darshana_wait_mins": 30,
            "dress_code": "Traditional attire recommended; no shorts",
            "atmosphere_tags": "sacred,crowded,beautiful-idol,historic",
            "instructions": "One of the most famous Ganpati temples in India. The idol is adorned with gold ornaments.",
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
