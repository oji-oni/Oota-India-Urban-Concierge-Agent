"""
Chennai city seed data for Oota India Urban Concierge.
Stub: 5 POIs + MRTS / Chennai Metro stations.
"""
from __future__ import annotations

import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    """Insert all Chennai data. Idempotent — safe to run multiple times."""
    cur = conn.cursor()

    # ── City record ─────────────────────────────────────────────────────────
    cur.execute(
        """
        INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Chennai", "chennai", "Tamil Nadu", 13.0827, 80.2707, "Asia/Kolkata", "Chennai Metro + MRTS"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'chennai'")
    city_id = cur.fetchone()[0]

    # ── Neighborhoods ────────────────────────────────────────────────────────
    neighborhoods = [
        ("T. Nagar",       13.0418, 80.2341, "Shopping hub, Pondy Bazaar, gold jewellery, dense market"),
        ("Mylapore",       13.0333, 80.2686, "Cultural heart of Chennai, Kapaleeshwarar Temple, sabha season"),
        ("Adyar",          13.0067, 80.2567, "Residential, beach access, upscale eateries, Besant Nagar nearby"),
        ("Anna Nagar",     13.0878, 80.2099, "Planned suburb, wide roads, middle-class residential, Parks"),
        ("Egmore",         13.0785, 80.2613, "Central Chennai, museums, government offices, budget hotels"),
        ("Velachery",      12.9815, 80.2180, "IT corridor suburb, Phoenix Mall, good metro connectivity"),
        ("Guindy",         13.0067, 80.2206, "Industrial area, TIDEL Park, Chennai airport nearby"),
    ]
    nbhd_ids: dict[str, int] = {}
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

    # ── Transit stations — Chennai Metro Blue Line (Airport ↔ Wimco Nagar) ──
    blue_line = [
        ("Chennai International Airport",  12.9941, 80.1709, True,  4),
        ("Meenambakkam",                    12.9968, 80.1793, False, 2),
        ("Alandur",                         13.0005, 80.1999, True,  3),
        ("St. Thomas Mount",               13.0024, 80.2063, False, 2),
        ("Guindy",                          13.0074, 80.2195, False, 2),
        ("Little Mount",                    13.0131, 80.2219, False, 2),
        ("Saidapet",                        13.0192, 80.2230, False, 2),
        ("CMBT (Koyambedu)",               13.0694, 80.1941, True,  4),
        ("Arumbakkam",                      13.0724, 80.2041, False, 2),
        ("Vadapalani",                      13.0503, 80.2126, False, 2),
        ("Ashok Nagar",                     13.0347, 80.2147, False, 2),
        ("Ekkattuthangal",                  13.0242, 80.2209, False, 2),
    ]
    # MRTS (Mass Rapid Transit System) — Beach to Velachery
    mrts_line = [
        ("Chennai Beach",   13.1048, 80.2886, True,  3),
        ("Fort",            13.0954, 80.2822, False, 2),
        ("Park Town",       13.0832, 80.2764, False, 2),
        ("Egmore",          13.0785, 80.2626, True,  3),
        ("Chetpet",         13.0714, 80.2520, False, 2),
        ("Nungambakkam",    13.0608, 80.2434, False, 2),
        ("Kodambakkam",     13.0515, 80.2251, False, 2),
        ("Mambalam",        13.0376, 80.2178, False, 2),
        ("Saidapet",        13.0175, 80.2222, False, 2),
        ("Guindy",          13.0067, 80.2206, False, 2),
        ("St. Thomas Mount",13.0024, 80.2063, False, 2),
        ("Velachery",       12.9819, 80.2201, False, 2),
    ]

    for line_stations, line_name, color, system in [
        (blue_line,  "Blue Line",   "#1565C0", "Chennai Metro"),
        (mrts_line,  "MRTS Line",   "#EF6C00", "MRTS"),
    ]:
        for seq, (name, lat, lng, is_ichange, delay) in enumerate(line_stations, 1):
            cur.execute(
                "SELECT id FROM transit_stations WHERE city_id = ? AND name = ? AND line_name = ?",
                (city_id, name, line_name),
            )
            if cur.fetchone():
                continue
            cur.execute(
                "INSERT INTO transit_stations (city_id, name, system, line_name, line_color, sequence_order, lat, lng, is_interchange, platform_walk_delay_mins) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (city_id, name, system, line_name, color, seq, lat, lng, int(is_ichange), delay),
            )
    conn.commit()

    # ── Points of Interest ───────────────────────────────────────────────────
    pois = [
        {
            "name": "Kapaleeshwarar Temple",
            "neighborhood": "Mylapore",
            "category": "temple",
            "lat": 13.0332, "lng": 80.2697,
            "rating": 4.7,
            "opens_at": "05:45", "closes_at": "21:30",
            "typical_darshana_wait_mins": 30,
            "dress_code": "Traditional attire; men must remove shirt for sanctum entry",
            "atmosphere_tags": "Dravidian,gopuram,historic,flowers,fragrant",
            "instructions": "Closes 12:00–16:00. Dedicated to Lord Shiva. Brahmotsavam festival in April spectacular.",
        },
        {
            "name": "Saravana Bhavan (Egmore)",
            "neighborhood": "Egmore",
            "category": "restaurant",
            "lat": 13.0780, "lng": 80.2631,
            "rating": 4.4,
            "opens_at": "07:00", "closes_at": "23:00",
            "typical_order_to_serve_mins": 12,
            "atmosphere_tags": "South-Indian,vegetarian,iconic,global-chain",
            "price_range": "₹₹",
            "dietary_tags": "pure-veg",
            "instructions": "Chennai is the origin of this global chain. Idli and filter coffee in the morning is unmissable.",
        },
        {
            "name": "Marina Beach",
            "neighborhood": "Mylapore",
            "category": "beach",
            "lat": 13.0569, "lng": 80.2823,
            "rating": 4.5,
            "opens_at": "00:00", "closes_at": "23:59",
            "typical_entry_wait_mins": 0,
            "price_range": "free",
            "atmosphere_tags": "world-famous,long-beach,sunset,bhajji-stalls",
            "instructions": "Second longest urban beach in the world (13 km). Not for swimming — dangerous currents. Best at dawn/dusk.",
        },
        {
            "name": "Anjappar Chettinad Restaurant",
            "neighborhood": "Anna Nagar",
            "category": "restaurant",
            "lat": 13.0858, "lng": 80.2106,
            "rating": 4.3,
            "opens_at": "11:00", "closes_at": "23:00",
            "typical_order_to_serve_mins": 20,
            "atmosphere_tags": "Chettinad,spicy,South-Indian,non-veg",
            "price_range": "₹₹",
            "dietary_tags": "non-veg",
            "instructions": "Famous for Chettinad chicken and pepper dishes. Authentic Tamil Nadu cuisine.",
        },
        {
            "name": "Phoenix MarketCity Chennai",
            "neighborhood": "Velachery",
            "category": "mall",
            "lat": 12.9943, "lng": 80.2183,
            "rating": 4.3,
            "opens_at": "11:00", "closes_at": "22:00",
            "typical_entry_wait_mins": 5,
            "atmosphere_tags": "premium,multiplex,food-court,family",
            "price_range": "₹₹₹",
            "instructions": "Metro: Velachery station. 4 floors, 200+ stores. PVR cinemas on top floor.",
        },
    ]
    for p in pois:
        nbhd_id = nbhd_ids.get(p.get("neighborhood", ""))
        cur.execute(
            "INSERT OR IGNORE INTO points_of_interest (city_id, name, neighborhood_id, category, lat, lng, rating, opens_at, closes_at, typical_entry_wait_mins, typical_order_to_serve_mins, typical_darshana_wait_mins, dress_code, instructions, atmosphere_tags, price_range, dietary_tags, capacity) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (city_id, p["name"], nbhd_id, p["category"], p.get("lat"), p.get("lng"), p.get("rating"), p.get("opens_at"), p.get("closes_at"), p.get("typical_entry_wait_mins", 0), p.get("typical_order_to_serve_mins", 0), p.get("typical_darshana_wait_mins", 0), p.get("dress_code"), p.get("instructions"), p.get("atmosphere_tags"), p.get("price_range"), p.get("dietary_tags"), p.get("capacity")),
        )
    conn.commit()

    # ── Traffic rules ────────────────────────────────────────────────────────
    traffic = [
        ("GST Road (NH-48)",     "08:00", "10:00", 2.3, "Airport to Guindy corridor. Metro Blue Line faster."),
        ("Anna Salai (MT Road)",  "08:30", "10:00", 2.0, "Central artery. MRTS from Park Town recommended."),
        ("OMR (Old Mahabalipuram Road)", "17:30", "20:00", 2.5, "IT employees return peak. Velachery metro hub."),
    ]
    for route, ps, pe, cf, note in traffic:
        cur.execute(
            "INSERT OR IGNORE INTO traffic_rules (city_id, route_name, peak_start, peak_end, congestion_factor, avoidance_note) VALUES (?, ?, ?, ?, ?, ?)",
            (city_id, route, ps, pe, cf, note),
        )
    conn.commit()

    # ── Weather (coastal; relatively stable temperatures) ────────────────────
    weather = [
        (0,  "Humid",        28, 0, 80, 15),
        (6,  "Partly Cloudy",29, 3, 76, 20),
        (9,  "Hot & Sunny",  34, 7, 65, 10),
        (12, "Hot & Sunny",  38, 10,55, 5),
        (15, "Hot & Sunny",  37, 9, 58, 10),
        (18, "Partly Cloudy",33, 4, 65, 25),
        (20, "Clear",        30, 1, 72, 15),
        (22, "Clear",        28, 0, 77, 10),
    ]
    for hour, cond, temp, uv, humid, precip in weather:
        cur.execute(
            "INSERT OR IGNORE INTO weather_forecasts (city_id, hour_of_day, condition, temp_celsius, uv_index, humidity, precipitation_probability) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (city_id, hour, cond, temp, uv, humid, precip),
        )
    conn.commit()
