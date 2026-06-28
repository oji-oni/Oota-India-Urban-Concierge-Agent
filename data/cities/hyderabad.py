"""
Hyderabad city seed data for Oota India Urban Concierge.
Stub: 5 POIs + Hyderabad Metro stations.
"""
from __future__ import annotations

import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    """Insert all Hyderabad data. Idempotent — safe to run multiple times."""
    cur = conn.cursor()

    # ── City record ─────────────────────────────────────────────────────────
    cur.execute(
        """
        INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Hyderabad", "hyderabad", "Telangana", 17.3850, 78.4867, "Asia/Kolkata", "Hyderabad Metro Rail"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'hyderabad'")
    city_id = cur.fetchone()[0]

    # ── Neighborhoods ────────────────────────────────────────────────────────
    neighborhoods = [
        ("Banjara Hills",   17.4150, 78.4347, "Upscale residential, embassies, fine dining, boutiques"),
        ("Jubilee Hills",   17.4239, 78.4072, "Premium residential, celebrity homes, restaurants, clubs"),
        ("Hitech City",     17.4498, 78.3812, "IT corridor, CYBERABAD, Mindspace, corporate campus"),
        ("Charminar",       17.3616, 78.4747, "Historic old city, Hyderabadi biryani, bangles, Muslim heritage"),
        ("Secunderabad",    17.4399, 78.4983, "Twin city, railway junction, cantonment, traditional market"),
        ("Madhapur",        17.4478, 78.3915, "IT suburb, pubs, multiplex, young professionals"),
        ("Gachibowli",      17.4401, 78.3489, "IT companies, international stadium, IIIT campus"),
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

    # ── Transit stations — Hyderabad Metro Red Line (Miyapur ↔ LB Nagar) ────
    red_line = [
        ("Miyapur",                17.4970, 78.3528, False, 2),
        ("JNTU College",           17.4937, 78.3597, False, 2),
        ("KPHB Colony",            17.4897, 78.3681, False, 2),
        ("Kukatpally",             17.4853, 78.3807, False, 2),
        ("Balanagar",              17.4794, 78.3918, False, 2),
        ("Moosapet",               17.4751, 78.4032, False, 2),
        ("Bharat Nagar",           17.4712, 78.4137, False, 2),
        ("Erragadda",              17.4655, 78.4265, False, 2),
        ("ESI Hospital",           17.4597, 78.4352, False, 2),
        ("SR Nagar",               17.4534, 78.4451, False, 2),
        ("Ameerpet",               17.4374, 78.4483, True,  5),  # interchange
        ("Punjagutta",             17.4285, 78.4533, False, 2),
        ("Errum Manzil",           17.4208, 78.4551, False, 2),
        ("Khairatabad",            17.4143, 78.4573, False, 2),
        ("Lakdi Ka Pul",           17.4084, 78.4583, False, 2),
        ("Assembly",               17.4022, 78.4625, False, 2),
        ("Nampally",               17.3939, 78.4668, False, 2),
        ("Gandhi Bhavan",          17.3873, 78.4700, False, 2),
        ("Osmania Medical College",17.3809, 78.4730, False, 2),
        ("MJ Market",              17.3770, 78.4767, False, 2),
        ("Malakpet",               17.3700, 78.4917, False, 2),
        ("New Market",             17.3665, 78.5004, False, 2),
        ("Musarambagh",            17.3603, 78.5123, False, 2),
        ("Dilsukhnagar",           17.3688, 78.5272, False, 2),
        ("Chaitanyapuri",          17.3694, 78.5379, False, 2),
        ("Victoria Memorial",      17.3694, 78.5504, False, 2),
        ("LB Nagar",               17.3474, 78.5578, False, 2),
    ]
    # Blue Line: Nagole ↔ Raidurg
    blue_line = [
        ("Nagole",                 17.3934, 78.5711, False, 2),
        ("Uppal",                  17.4004, 78.5590, False, 2),
        ("Stadium",                17.4044, 78.5476, False, 2),
        ("NGRI",                   17.4100, 78.5348, False, 2),
        ("Habsiguda",              17.4140, 78.5229, False, 2),
        ("Tarnaka",                17.4175, 78.5113, False, 2),
        ("Mettuguda",              17.4218, 78.5008, False, 2),
        ("Secunderabad East",      17.4317, 78.4933, False, 2),
        ("Parade Grounds",         17.4369, 78.4826, False, 2),
        ("Secunderabad West",      17.4385, 78.4686, True,  4),
        ("Gandhi Hospital",        17.4379, 78.4603, False, 2),
        ("Musheerabad",            17.4326, 78.4549, False, 2),
        ("RTC X Roads",            17.4283, 78.4502, False, 2),
        ("Chikkadpally",           17.4242, 78.4479, False, 2),
        ("Narayanguda",            17.4193, 78.4466, False, 2),
        ("Sultan Bazar",           17.4095, 78.4648, False, 2),
        ("MG Bus Station",         17.3880, 78.4741, True,  4),
        ("Ameerpet",               17.4374, 78.4483, True,  5),
        ("Yusufguda",              17.4385, 78.4311, False, 2),
        ("Road No 5, Jubilee Hills",17.4315, 78.4208, False, 2),
        ("Jubilee Hills Check Post",17.4259, 78.4083, False, 2),
        ("Peddamma Gudi",          17.4259, 78.3953, False, 2),
        ("Madhapur",               17.4459, 78.3912, False, 2),
        ("Durgam Cheruvu",         17.4483, 78.3789, False, 2),
        ("Hitech City",            17.4498, 78.3808, False, 2),
        ("Raidurg",                17.4281, 78.3586, False, 2),
    ]

    for line_stations, line_name, color in [
        (red_line,  "Red Line",  "#C62828"),
        (blue_line, "Blue Line", "#1565C0"),
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
                (city_id, name, "Hyderabad Metro Rail", line_name, color, seq, lat, lng, int(is_ichange), delay),
            )
    conn.commit()

    # ── Points of Interest ───────────────────────────────────────────────────
    pois = [
        {
            "name": "Charminar",
            "neighborhood": "Charminar",
            "category": "monument",
            "lat": 17.3616, "lng": 78.4747,
            "rating": 4.5,
            "opens_at": "09:30", "closes_at": "17:30",
            "typical_entry_wait_mins": 20,
            "price_range": "₹",
            "atmosphere_tags": "iconic,Mughal,archway,photo-spot,old-city",
            "instructions": "Entry ₹25 Indians, ₹300 foreigners. Closed Fridays. Laad Bazaar for bangles just outside.",
        },
        {
            "name": "Paradise Biryani (Secunderabad)",
            "neighborhood": "Secunderabad",
            "category": "restaurant",
            "lat": 17.4399, "lng": 78.4952,
            "rating": 4.4,
            "opens_at": "11:00", "closes_at": "23:30",
            "typical_order_to_serve_mins": 20,
            "atmosphere_tags": "iconic,biryani,Hyderabadi,legendary,non-veg",
            "price_range": "₹₹",
            "dietary_tags": "non-veg,halal",
            "instructions": "The most famous Hyderabadi biryani restaurant since 1953. Dum biryani cooked in sealed handi. Multiple branches.",
        },
        {
            "name": "Golconda Fort",
            "neighborhood": "Charminar",
            "category": "heritage",
            "lat": 17.3833, "lng": 78.4011,
            "rating": 4.5,
            "opens_at": "08:00", "closes_at": "17:30",
            "typical_entry_wait_mins": 15,
            "price_range": "₹₹",
            "atmosphere_tags": "UNESCO-nominated,Qutb-Shahi,acoustic-marvel,fort",
            "instructions": "Light & Sound Show in evenings (₹130 Hindi, ₹230 English). Clap at the main entrance — heard at the top of the hill!",
        },
        {
            "name": "Chicha's Hyderabadi Restaurant (Banjara Hills)",
            "neighborhood": "Banjara Hills",
            "category": "restaurant",
            "lat": 17.4150, "lng": 78.4340,
            "rating": 4.3,
            "opens_at": "12:00", "closes_at": "23:00",
            "typical_order_to_serve_mins": 25,
            "atmosphere_tags": "Hyderabadi,authentic,haleem,non-veg",
            "price_range": "₹₹",
            "dietary_tags": "non-veg,halal",
            "instructions": "Try the haleem during Ramadan — it's world-famous. Paya and nihari also excellent.",
        },
        {
            "name": "Inorbit Mall Hyderabad (Hitech City)",
            "neighborhood": "Hitech City",
            "category": "mall",
            "lat": 17.4535, "lng": 78.3804,
            "rating": 4.2,
            "opens_at": "11:00", "closes_at": "22:00",
            "typical_entry_wait_mins": 5,
            "atmosphere_tags": "IT-corridor,multiplex,food-court,family",
            "price_range": "₹₹",
            "instructions": "Metro: Hitech City station (Blue Line). Cinepolis multiplex. Good food court with regional options.",
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
        ("ORR (Outer Ring Road)",      "08:00", "10:00", 2.2, "IT workers commute to HITEC City. Metro Blue Line from Ameerpet."),
        ("Rajiv Gandhi International Airport Road", "06:00", "08:30", 2.0, "Early flights. Book cab night before."),
        ("Banjara Hills Road No. 12",  "17:30", "20:00", 2.3, "Evening shopping peak. Many eateries cause parking chaos."),
    ]
    for route, ps, pe, cf, note in traffic:
        cur.execute(
            "INSERT OR IGNORE INTO traffic_rules (city_id, route_name, peak_start, peak_end, congestion_factor, avoidance_note) VALUES (?, ?, ?, ?, ?, ?)",
            (city_id, route, ps, pe, cf, note),
        )
    conn.commit()

    # ── Weather (hot semi-arid; pre-monsoon summer is intense) ───────────────
    weather = [
        (0,  "Clear",        26, 0, 50, 5),
        (6,  "Clear",        28, 4, 48, 10),
        (9,  "Hot & Sunny",  33, 7, 42, 5),
        (12, "Hot & Sunny",  39, 10,35, 5),
        (15, "Partly Cloudy",38, 9, 38, 15),
        (18, "Partly Cloudy",34, 4, 48, 25),
        (20, "Clear",        30, 1, 55, 10),
        (22, "Clear",        27, 0, 52, 5),
    ]
    for hour, cond, temp, uv, humid, precip in weather:
        cur.execute(
            "INSERT OR IGNORE INTO weather_forecasts (city_id, hour_of_day, condition, temp_celsius, uv_index, humidity, precipitation_probability) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (city_id, hour, cond, temp, uv, humid, precip),
        )
    conn.commit()
