"""
Mumbai city seed data for Oota India Urban Concierge.
"""
from __future__ import annotations
import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Mumbai", "mumbai", "Maharashtra", 19.0760, 72.8777, "Asia/Kolkata", "Mumbai Local + Metro"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'mumbai'")
    city_id = cur.fetchone()[0]

    neighborhoods = [
        ("Bandra",         19.0544, 72.8402, "Trendy, Queen of Suburbs, cafes, sea link, Bollywood"),
        ("Andheri",        19.1136, 72.8697, "Massive suburb, IT companies, film studios, nightlife"),
        ("Dadar",          19.0178, 72.8478, "Central suburb, Marathi culture, flower market, well-connected"),
        ("Colaba",         18.9067, 72.9162, "Historic South Mumbai, Gateway of India, cafes, budget stays"),
        ("Juhu",           19.1075, 72.8263, "Beach suburb, Bollywood bungalows, chaat, sea facing"),
        ("Lower Parel",    18.9979, 72.8303, "Corporate hub, mills redeveloped to malls, upscale dining"),
        ("BKC",            19.0548, 72.8651, "Bandra-Kurla Complex, financial district, consulates"),
        ("Kurla",          19.0726, 72.8826, "Transport hub, LBS Marg, Asia's largest slum Dharavi nearby"),
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

    # Local train stations — Western Line (Churchgate to Dahanu Road)
    western_line = [
        ("Churchgate",     18.9352, 72.8263, False, 2),
        ("Marine Lines",   18.9410, 72.8250, False, 2),
        ("Charni Road",    18.9484, 72.8223, False, 2),
        ("Grant Road",     18.9608, 72.8174, False, 2),
        ("Mumbai Central",18.9710, 72.8197, True,  4),
        ("Mahalakshmi",   18.9826, 72.8237, False, 2),
        ("Lower Parel",   18.9960, 72.8296, False, 2),
        ("Elphinstone Road",19.0062,72.8350, False, 2),
        ("Dadar",         19.0178, 72.8430, True,  5),
        ("Matunga Road",  19.0285, 72.8454, False, 2),
        ("Mahim Junction",19.0423, 72.8383, True,  3),
        ("Bandra",        19.0544, 72.8392, False, 2),
        ("Khar Road",     19.0698, 72.8370, False, 2),
        ("Santa Cruz",    19.0819, 72.8374, False, 2),
        ("Vile Parle",    19.0972, 72.8454, False, 2),
        ("Andheri",       19.1136, 72.8490, True,  4),
        ("Jogeshwari",    19.1316, 72.8497, False, 2),
        ("Goregaon",      19.1527, 72.8496, False, 2),
        ("Malad",         19.1873, 72.8484, False, 2),
        ("Borivali",      19.2319, 72.8547, False, 2),
    ]
    # Central Line (CST to Kasara / Panvel)
    central_line = [
        ("Chhatrapati Shivaji Maharaj Terminus", 18.9398, 72.8355, True, 5),
        ("Masjid",        18.9468, 72.8386, False, 2),
        ("Sandhurst Road",18.9553, 72.8415, False, 2),
        ("Byculla",       18.9737, 72.8371, False, 2),
        ("Chinchpokli",   18.9790, 72.8322, False, 2),
        ("Currey Road",   18.9867, 72.8266, False, 2),
        ("Parel",         18.9949, 72.8244, False, 2),
        ("Dadar Central", 19.0180, 72.8440, True,  5),
        ("Sion",          19.0393, 72.8618, False, 2),
        ("Kurla",         19.0726, 72.8797, True,  4),
        ("Vidyavihar",    19.0884, 72.8913, False, 2),
        ("Ghatkopar",     19.0858, 72.9081, True,  3),
        ("Vikhroli",      19.1040, 72.9289, False, 2),
        ("Kanjurmarg",    19.1204, 72.9418, False, 2),
        ("Bhandup",       19.1432, 72.9424, False, 2),
        ("Mulund",        19.1764, 72.9573, False, 2),
    ]

    station_ids: dict[str, int] = {}
    for line_stations, line_name, color in [
        (western_line, "Western Line", "#1565C0"),
        (central_line, "Central Line", "#B71C1C"),
    ]:
        for seq, (name, lat, lng, is_ichange, delay) in enumerate(line_stations, 1):
            cur.execute(
                "SELECT id FROM transit_stations WHERE city_id = ? AND name = ? AND line_name = ?",
                (city_id, name, line_name),
            )
            row = cur.fetchone()
            if row:
                station_ids[f"{line_name}:{name}"] = row[0]
                continue
            cur.execute(
                "INSERT INTO transit_stations (city_id, name, system, line_name, line_color, sequence_order, lat, lng, is_interchange, platform_walk_delay_mins) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (city_id, name, "Mumbai Local", line_name, color, seq, lat, lng, int(is_ichange), delay),
            )
            station_ids[f"{line_name}:{name}"] = cur.lastrowid
    conn.commit()

    pois = [
        {"name": "Leopold Cafe", "neighborhood": "Colaba", "category": "restaurant",
         "lat": 18.9231, "lng": 72.8315, "rating": 4.1,
         "opens_at": "07:30", "closes_at": "00:30",
         "typical_order_to_serve_mins": 20,
         "atmosphere_tags": "iconic,tourist-spot,historic,beer-garden",
         "price_range": "₹₹", "dietary_tags": "non-veg",
         "instructions": "Legendary cafe since 1871. Survived 26/11 attacks. Multi-cuisine, cold beer, lively."},
        {"name": "Britannia & Co", "neighborhood": "Colaba", "category": "restaurant",
         "lat": 18.9305, "lng": 72.8351, "rating": 4.5,
         "opens_at": "11:30", "closes_at": "16:30",
         "typical_order_to_serve_mins": 15,
         "atmosphere_tags": "Parsi-food,heritage,old-world,lunch-only",
         "price_range": "₹₹", "dietary_tags": "non-veg",
         "instructions": "Parsi cafe since 1923. Lunch only; closed Sunday. Berry Pulav is a must. Owned by 90-year-old Boman Kohinoor."},
        {"name": "Trishna", "neighborhood": "Colaba", "category": "restaurant",
         "lat": 18.9296, "lng": 72.8319, "rating": 4.5,
         "opens_at": "12:00", "closes_at": "23:30",
         "typical_order_to_serve_mins": 30,
         "atmosphere_tags": "seafood,fine-dining,Kala-Ghoda,iconic",
         "price_range": "₹₹₹₹", "dietary_tags": "non-veg,seafood-specialty",
         "instructions": "Famous for butter garlic crab and bombil fry. Reservations essential on weekends."},
        {"name": "Siddhivinayak Temple", "neighborhood": "Dadar", "category": "temple",
         "lat": 19.0173, "lng": 72.8302, "rating": 4.7,
         "opens_at": "05:30", "closes_at": "22:00",
         "typical_darshana_wait_mins": 120,
         "dress_code": "Modest attire; no shorts or sleeveless",
         "atmosphere_tags": "powerful,Ganesha,spiritual,always-crowded",
         "instructions": "One of the richest temples in India. Tuesdays: 3–4 hour waits. Online darshan booking saves time. No mobile phones in sanctum."},
        {"name": "Elephanta Caves", "neighborhood": "Colaba", "category": "heritage",
         "lat": 18.9635, "lng": 72.9315, "rating": 4.4,
         "opens_at": "09:00", "closes_at": "17:30",
         "typical_entry_wait_mins": 20,
         "price_range": "₹₹",
         "atmosphere_tags": "UNESCO,cave-temples,ferry,island",
         "instructions": "Ferry from Gateway of India: ₹200 return. Closed Mondays. 120+ stone steps to caves. Take lunch/water."},
        {"name": "Juhu Chowpatty Beach", "neighborhood": "Juhu", "category": "beach",
         "lat": 19.1009, "lng": 72.8260, "rating": 4.1,
         "opens_at": "05:00", "closes_at": "23:00",
         "typical_entry_wait_mins": 0,
         "price_range": "free",
         "atmosphere_tags": "beach,chaat,sunset,families,casual",
         "instructions": "Best at sunset. Famous for pani puri, bhel puri, vada pav stalls. Not for swimming. Polluted water."},
        {"name": "PVR ICON BKC", "neighborhood": "BKC", "category": "cinema",
         "lat": 19.0632, "lng": 72.8676, "rating": 4.4,
         "opens_at": "10:00", "closes_at": "00:00",
         "price_range": "₹₹₹",
         "instructions": "Premium multiplex with recliner seats. 8 screens. Fine dining options inside."},
        {"name": "R City Mall Ghatkopar", "neighborhood": "Kurla", "category": "mall",
         "lat": 19.0879, "lng": 72.9086, "rating": 4.2,
         "opens_at": "11:00", "closes_at": "22:00",
         "price_range": "₹₹",
         "atmosphere_tags": "family,central-suburban,cinema,food-court",
         "instructions": "Metro: Ghatkopar station Line 1. 200+ stores, Multiplex on top floor."},
        {"name": "Gateway of India", "neighborhood": "Colaba", "category": "monument",
         "lat": 18.9220, "lng": 72.8347, "rating": 4.5,
         "opens_at": "00:00", "closes_at": "23:59",
         "typical_entry_wait_mins": 5,
         "price_range": "free",
         "atmosphere_tags": "iconic,heritage,waterfront,tourist,photo-spot",
         "instructions": "Arch monument built in 1924. Open 24/7. Taj Mahal Palace Hotel next door. Ferries to Elephanta from here."},
        {"name": "Haji Ali Dargah", "neighborhood": "Lower Parel", "category": "dargah",
         "lat": 18.9827, "lng": 72.8090, "rating": 4.6,
         "opens_at": "05:30", "closes_at": "22:00",
         "typical_darshana_wait_mins": 30,
         "dress_code": "Covered head required; modest clothing",
         "atmosphere_tags": "spiritual,sea-causeway,iconic,qawwali-evenings",
         "instructions": "Accessible via causeway — only during low tide. Check tide timings before visiting. Qawwali every Thursday evening."},
    ]
    for p in pois:
        nbhd_id = nbhd_ids.get(p.get("neighborhood", ""))
        cur.execute(
            "INSERT OR IGNORE INTO points_of_interest (city_id, name, neighborhood_id, category, lat, lng, rating, opens_at, closes_at, typical_entry_wait_mins, typical_order_to_serve_mins, typical_darshana_wait_mins, dress_code, instructions, atmosphere_tags, price_range, dietary_tags, capacity) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (city_id, p["name"], nbhd_id, p["category"], p.get("lat"), p.get("lng"), p.get("rating"), p.get("opens_at"), p.get("closes_at"), p.get("typical_entry_wait_mins", 0), p.get("typical_order_to_serve_mins", 0), p.get("typical_darshana_wait_mins", 0), p.get("dress_code"), p.get("instructions"), p.get("atmosphere_tags"), p.get("price_range"), p.get("dietary_tags"), p.get("capacity")),
        )
    conn.commit()

    traffic = [
        ("Western Express Highway",  "08:00", "10:30", 2.3, "Andheri–Bandra bottleneck. Metro Line 1 (Ghatkopar–Versova) is faster."),
        ("Eastern Express Highway",  "08:00", "10:00", 2.0, "CST–Sion–Kurla corridor. Central line train much faster."),
        ("Bandra-Worli Sea Link",    "08:00", "10:00", 1.5, "Toll: ₹105 one-way. Saves 20–30 min vs Mahim Causeway."),
        ("Mahim Causeway",           "17:30", "20:00", 2.5, "Avoid peak hours. Sea Link costs more but saves time."),
        ("Sion–Panvel Highway",      "17:30", "20:00", 2.2, "Harbour line train faster during evenings."),
    ]
    for route, ps, pe, cf, note in traffic:
        cur.execute(
            "INSERT OR IGNORE INTO traffic_rules (city_id, route_name, peak_start, peak_end, congestion_factor, avoidance_note) VALUES (?, ?, ?, ?, ?, ?)",
            (city_id, route, ps, pe, cf, note),
        )
    conn.commit()

    weather = [
        (0,  "Humid",          28, 0, 85, 20),
        (3,  "Clear",          27, 0, 88, 10),
        (6,  "Partly Cloudy",  28, 2, 82, 25),
        (9,  "Cloudy",         30, 6, 78, 50),
        (12, "Heavy Rain",     29, 4, 90, 85),
        (15, "Thunderstorm",   28, 3, 92, 90),
        (17, "Drizzle",        28, 2, 88, 70),
        (19, "Partly Cloudy", 28, 1, 84, 40),
        (21, "Cloudy",         28, 0, 86, 30),
        (23, "Clear",          27, 0, 84, 15),
    ]
    for hour, cond, temp, uv, humid, precip in weather:
        cur.execute(
            "INSERT OR IGNORE INTO weather_forecasts (city_id, hour_of_day, condition, temp_celsius, uv_index, humidity, precipitation_probability) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (city_id, hour, cond, temp, uv, humid, precip),
        )
    conn.commit()
