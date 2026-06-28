"""
Bengaluru city seed data for Oota India Urban Concierge.
Real data: neighborhoods, POIs, metro stations, traffic rules, weather.
"""
from __future__ import annotations

import json
import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    """Insert all Bengaluru data. Idempotent — safe to run multiple times."""
    cur = conn.cursor()

    # ── City record ────────────────────────────────────────────────────────────
    cur.execute(
        """
        INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("Bengaluru", "bengaluru", "Karnataka", 12.9716, 77.5946, "Asia/Kolkata", "Namma Metro"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'bengaluru'")
    city_id = cur.fetchone()[0]

    # ── Neighborhoods ──────────────────────────────────────────────────────────
    neighborhoods = [
        ("Koramangala",   12.9352, 77.6244, "Young, hip, startup culture, lots of cafes and restaurants"),
        ("Indiranagar",   12.9784, 77.6408, "Trendy, tree-lined streets, craft beer, brunch spots"),
        ("Malleshwaram",  13.0035, 77.5685, "Old Bengaluru, traditional market, filter coffee culture"),
        ("Whitefield",    12.9698, 77.7499, "IT corridor, malls, expat community, modern infrastructure"),
        ("HSR Layout",    12.9116, 77.6370, "Residential, clean streets, family-friendly, rising food scene"),
        ("Jayanagar",     12.9299, 77.5838, "Heritage neighbourhood, South Indian food, quiet lanes"),
        ("BTM Layout",    12.9165, 77.6101, "Busy, affordable, student-heavy, street food paradise"),
        ("MG Road",       12.9756, 77.6063, "Commercial hub, metro connectivity, shopping and nightlife"),
        ("Cubbon Park",   12.9763, 77.5929, "Green lung of the city, colonial buildings, joggers"),
        ("Basavanagudi",  12.9425, 77.5731, "Old city charm, Bull Temple, authentic Karnataka food"),
        ("Rajajinagar",   12.9980, 77.5540, "Residential, ISKCON temple, traditional market"),
        ("Electronic City", 12.8399, 77.6770, "IT hub, Infosys campus, affordable housing"),
    ]
    nbhd_ids: dict[str, int] = {}
    for name, lat, lng, vibe in neighborhoods:
        cur.execute(
            """
            INSERT OR IGNORE INTO neighborhoods (city_id, name, lat, lng, vibe)
            VALUES (?, ?, ?, ?, ?)
            """,
            (city_id, name, lat, lng, vibe),
        )
    conn.commit()
    for name, *_ in neighborhoods:
        cur.execute(
            "SELECT id FROM neighborhoods WHERE city_id = ? AND name = ?",
            (city_id, name),
        )
        row = cur.fetchone()
        if row:
            nbhd_ids[name] = row[0]

    # ── Transit stations ───────────────────────────────────────────────────────
    # Purple Line: Baiyappanahalli → Mysuru Road (east-west)
    purple_line = [
        ("Baiyappanahalli",       12.9920, 77.6605, False, 2),
        ("Swami Vivekananda Road",12.9902, 77.6514, False, 2),
        ("Indiranagar",           12.9784, 77.6414, False, 2),
        ("Halasuru",              12.9766, 77.6290, False, 2),
        ("Trinity",               12.9731, 77.6189, False, 2),
        ("MG Road",               12.9755, 77.6100, False, 2),
        ("Cubbon Park",           12.9763, 77.5968, False, 2),
        ("Vidhana Soudha",        12.9793, 77.5904, False, 2),
        ("Sir M Visvesvaraya",    12.9771, 77.5841, False, 2),
        ("Majestic (KSR City)",   12.9766, 77.5713, True,  6),  # interchange
        ("City Railway Station",  12.9769, 77.5646, False, 2),
        ("Magadi Road",           12.9700, 77.5506, False, 2),
        ("Hosahalli",             12.9625, 77.5390, False, 2),
        ("Vijayanagar",           12.9640, 77.5238, False, 2),
        ("Attiguppe",             12.9619, 77.5119, False, 2),
        ("Deepanjali Nagar",      12.9616, 77.4985, False, 2),
        ("Mysuru Road",           12.9552, 77.4849, False, 2),
    ]
    # Green Line: Nagasandra → Silk Board (north-south)
    green_line = [
        ("Nagasandra",            13.0623, 77.5127, False, 2),
        ("Dasarahalli",           13.0497, 77.5135, False, 2),
        ("Jalahalli",             13.0383, 77.5126, False, 2),
        ("Peenya Industry",       13.0275, 77.5128, False, 2),
        ("Peenya",                13.0224, 77.5139, False, 2),
        ("Goraguntepalya",        13.0151, 77.5219, False, 2),
        ("Yeshwanthpur",          13.0226, 77.5389, False, 2),
        ("Sandal Soap Factory",   13.0093, 77.5474, False, 2),
        ("Mahalakshmi",           13.0006, 77.5528, False, 2),
        ("Rajajinagar",           13.0017, 77.5554, False, 2),
        ("Mahakavi Kuvempu Road", 12.9980, 77.5589, False, 2),
        ("Srirampura",            12.9943, 77.5659, False, 2),
        ("Mantri Square Sampige", 12.9942, 77.5683, False, 2),
        ("Majestic (KSR City)",   12.9766, 77.5713, True,  6),  # same interchange
        ("Chickpete",             12.9681, 77.5750, False, 2),
        ("Krishna Rajendra Market",12.9613, 77.5760, False, 2),
        ("National College",      12.9538, 77.5777, False, 2),
        ("Lalbagh",               12.9484, 77.5791, False, 2),
        ("South End Circle",      12.9399, 77.5822, False, 2),
        ("Jayanagar",             12.9299, 77.5838, False, 2),
        ("Rashtreeya Vidyalaya Road",12.9227, 77.5861, False, 2),
        ("Banashankari",          12.9244, 77.5475, False, 2),
        ("JP Nagar",              12.9091, 77.5851, False, 2),
        ("Yelachenahalli",        12.8946, 77.5844, False, 2),
        ("Konanakunte Cross",     12.8841, 77.5844, False, 2),
        ("Doddakallasandra",      12.8741, 77.5845, False, 2),
        ("Vajarahalli",           12.8644, 77.5861, False, 2),
        ("Thalaghattapura",       12.8552, 77.5869, False, 2),
        ("Silk Board",            12.9172, 77.6227, False, 2),
    ]

    station_ids: dict[str, int] = {}

    def insert_stations(stations: list, system: str, line_name: str, line_color: str) -> None:
        for seq, (name, lat, lng, is_ichange, delay) in enumerate(stations, start=1):
            cur.execute(
                """
                SELECT id FROM transit_stations
                WHERE city_id = ? AND name = ? AND line_name = ?
                """,
                (city_id, name, line_name),
            )
            row = cur.fetchone()
            if row:
                station_ids[f"{line_name}:{name}"] = row[0]
                continue
            cur.execute(
                """
                INSERT INTO transit_stations
                    (city_id, name, system, line_name, line_color, sequence_order,
                     lat, lng, is_interchange, platform_walk_delay_mins)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (city_id, name, system, line_name, line_color, seq,
                 lat, lng, int(is_ichange), delay),
            )
            station_ids[f"{line_name}:{name}"] = cur.lastrowid
        conn.commit()

    insert_stations(purple_line, "Namma Metro", "Purple Line", "#7B1FA2")
    insert_stations(green_line, "Namma Metro", "Green Line", "#388E3C")

    # Seed metro fares (distance-slab based, Bengaluru BMRCL tariff)
    # Slab: 0-2 km → ₹10, 2-4 km → ₹15, 4-6 km → ₹20, 6-10 km → ₹25, 10-15 km → ₹30, 15-20 km → ₹35, >20 km → ₹40
    # We insert representative fares for common journeys
    common_fares = [
        ("Purple Line:MG Road",       "Purple Line:Indiranagar",        15),
        ("Purple Line:MG Road",       "Purple Line:Majestic (KSR City)",10),
        ("Purple Line:Baiyappanahalli","Purple Line:Majestic (KSR City)",30),
        ("Purple Line:Majestic (KSR City)","Purple Line:Mysuru Road",   35),
        ("Green Line:Rajajinagar",    "Green Line:Majestic (KSR City)", 10),
        ("Green Line:Majestic (KSR City)","Green Line:Jayanagar",        20),
        ("Green Line:Majestic (KSR City)","Green Line:Silk Board",       30),
        ("Green Line:Nagasandra",     "Green Line:Majestic (KSR City)", 35),
    ]
    for from_key, to_key, fare in common_fares:
        from_id = station_ids.get(from_key)
        to_id   = station_ids.get(to_key)
        if from_id and to_id:
            cur.execute(
                "INSERT OR IGNORE INTO metro_fares (from_station_id, to_station_id, fare_rupees) VALUES (?, ?, ?)",
                (from_id, to_id, fare),
            )
    conn.commit()

    # ── Points of Interest ─────────────────────────────────────────────────────
    pois = [
        # --- Restaurants ---
        {
            "name": "Toit Brewpub",
            "neighborhood": "Indiranagar",
            "category": "restaurant",
            "lat": 12.9756, "lng": 77.6413,
            "rating": 4.5,
            "opens_at": "12:00", "closes_at": "23:00",
            "typical_order_to_serve_mins": 15,
            "atmosphere_tags": "craft beer,lively,rooftop,pub",
            "price_range": "₹₹₹",
            "dietary_tags": "non-veg,veg-options",
            "capacity": 250,
            "instructions": "Weekends get packed after 7pm; arrive early or book table.",
        },
        {
            "name": "CTR / Sri Sagar (Central Tiffin Room)",
            "neighborhood": "Malleshwaram",
            "category": "restaurant",
            "lat": 13.0037, "lng": 77.5687,
            "rating": 4.7,
            "opens_at": "07:30", "closes_at": "21:30",
            "typical_order_to_serve_mins": 10,
            "atmosphere_tags": "iconic,heritage,old-school,breakfast",
            "price_range": "₹",
            "dietary_tags": "pure-veg",
            "capacity": 60,
            "dress_code": "Casual",
            "instructions": "Famous for benne masala dosa. Queue starts early on weekends. Cash only.",
        },
        {
            "name": "Vidyarthi Bhavan",
            "neighborhood": "Basavanagudi",
            "category": "restaurant",
            "lat": 12.9398, "lng": 77.5728,
            "rating": 4.6,
            "opens_at": "06:30",
            "closes_at": "20:30",
            "typical_order_to_serve_mins": 8,
            "atmosphere_tags": "legacy,breakfast,South-Indian,no-frills",
            "price_range": "₹",
            "dietary_tags": "pure-veg",
            "capacity": 80,
            "instructions": "Closed 11:30–15:30. Only dosa and vada. Queue guaranteed on weekends. Since 1943.",
        },
        {
            "name": "Meghana Foods",
            "neighborhood": "Koramangala",
            "category": "restaurant",
            "lat": 12.9356, "lng": 77.6202,
            "rating": 4.4,
            "opens_at": "11:30", "closes_at": "23:00",
            "typical_order_to_serve_mins": 20,
            "atmosphere_tags": "biryani,casual,noisy,popular",
            "price_range": "₹₹",
            "dietary_tags": "non-veg,halal",
            "capacity": 120,
            "instructions": "Famous for Andhra chicken biryani. Long waits on weekends; takeaway faster.",
        },
        {
            "name": "Karavalli",
            "neighborhood": "MG Road",
            "category": "restaurant",
            "lat": 12.9760, "lng": 77.6101,
            "rating": 4.6,
            "opens_at": "12:30", "closes_at": "23:00",
            "typical_order_to_serve_mins": 25,
            "atmosphere_tags": "fine-dining,coastal,romantic,heritage-property",
            "price_range": "₹₹₹₹",
            "dietary_tags": "non-veg,seafood-specialty",
            "capacity": 80,
            "instructions": "Located inside Taj Gateway Hotel. Reservations recommended. Coastal Karnataka and Chettinad cuisine.",
        },
        # --- Temples ---
        {
            "name": "ISKCON Temple Bengaluru",
            "neighborhood": "Rajajinagar",
            "category": "temple",
            "lat": 12.9987, "lng": 77.5540,
            "rating": 4.8,
            "opens_at": "04:15", "closes_at": "21:00",
            "typical_darshana_wait_mins": 60,
            "dress_code": "Traditional Indian attire preferred; no sleeveless, shorts, or short skirts",
            "instructions": "Ekadashi and festival days: waits can reach 3+ hours. Photography not allowed inside sanctum.",
            "atmosphere_tags": "spiritual,grand,bhajan,crowded-on-ekadashi",
            "dietary_tags": "pure-veg",
        },
        {
            "name": "Bull Temple (Dodda Basavana Gudi)",
            "neighborhood": "Basavanagudi",
            "category": "temple",
            "lat": 12.9425, "lng": 77.5717,
            "rating": 4.5,
            "opens_at": "06:00", "closes_at": "20:00",
            "typical_darshana_wait_mins": 20,
            "dress_code": "No shorts or sleeveless attire",
            "instructions": "One of the oldest temples in Bengaluru. Monolithic bull (Nandi) is 4.5m high. Kadalekai Parishe groundnut fair in Nov.",
            "atmosphere_tags": "historic,peaceful,Dravidian-architecture",
        },
        {
            "name": "Dodda Ganapathi Temple",
            "neighborhood": "Basavanagudi",
            "category": "temple",
            "lat": 12.9410, "lng": 77.5718,
            "rating": 4.4,
            "opens_at": "06:00", "closes_at": "21:00",
            "typical_darshana_wait_mins": 15,
            "dress_code": "Traditional attire preferred",
            "instructions": "Closes 13:00–17:00. Massive Ganapathi idol made of butter and sugar. Near Bull Temple.",
            "atmosphere_tags": "historic,compact,traditional",
        },
        # --- Malls ---
        {
            "name": "Phoenix MarketCity Bengaluru",
            "neighborhood": "Whitefield",
            "category": "mall",
            "lat": 12.9959, "lng": 77.6971,
            "rating": 4.3,
            "opens_at": "11:00", "closes_at": "22:00",
            "typical_entry_wait_mins": 5,
            "atmosphere_tags": "premium,large,multiplex,food-court",
            "price_range": "₹₹₹",
            "instructions": "4 floors, 250+ stores, PVR multiplex, Arcade. Parking available basement B1-B3. BMTC buses from Whitefield station.",
        },
        {
            "name": "Orion Mall",
            "neighborhood": "Rajajinagar",
            "category": "mall",
            "lat": 13.0121, "lng": 77.5547,
            "rating": 4.3,
            "opens_at": "11:00", "closes_at": "22:00",
            "typical_entry_wait_mins": 3,
            "atmosphere_tags": "family,cinema,food-court,shopping",
            "price_range": "₹₹₹",
            "instructions": "Cinepolis multiplex on top floor. Metro: Rajajinagar station (Green Line). Ample parking.",
        },
        {
            "name": "Forum Mall Koramangala",
            "neighborhood": "Koramangala",
            "category": "mall",
            "lat": 12.9345, "lng": 77.6100,
            "rating": 4.2,
            "opens_at": "11:00", "closes_at": "22:00",
            "typical_entry_wait_mins": 5,
            "atmosphere_tags": "central-Koramangala,lifestyle,casual",
            "price_range": "₹₹",
            "instructions": "Shoppers Stop anchor store. Cafes on ground floor. Best reached by auto from Koramangala 4th Block.",
        },
        # --- Parks ---
        {
            "name": "Cubbon Park",
            "neighborhood": "Cubbon Park",
            "category": "park",
            "lat": 12.9763, "lng": 77.5929,
            "rating": 4.7,
            "opens_at": "06:00", "closes_at": "18:00",
            "typical_entry_wait_mins": 0,
            "atmosphere_tags": "green,joggers,heritage-buildings,families",
            "price_range": "free",
            "instructions": "240 acres of lawns and trees. Vehicles not allowed inside on Sundays. Home to Karnataka High Court and Attara Kacheri.",
        },
        {
            "name": "Lalbagh Botanical Garden",
            "neighborhood": "Basavanagudi",
            "category": "park",
            "lat": 12.9507, "lng": 77.5848,
            "rating": 4.6,
            "opens_at": "06:00", "closes_at": "19:00",
            "typical_entry_wait_mins": 5,
            "atmosphere_tags": "botanical,glass-house,lakes,heritage",
            "price_range": "₹",
            "instructions": "Entry: ₹20 adults, ₹10 children. Famous glass-house flower show in Jan and Aug. Oldest botanical garden in India (1760).",
        },
        # --- Cinema ---
        {
            "name": "PVR Forum Koramangala",
            "neighborhood": "Koramangala",
            "category": "cinema",
            "lat": 12.9343, "lng": 77.6103,
            "rating": 4.1,
            "opens_at": "10:00", "closes_at": "23:30",
            "price_range": "₹₹",
            "instructions": "Inside Forum Mall. 8 screens. IMAX screen available. Online booking on PVR app.",
        },
        {
            "name": "INOX Garuda Mall MG Road",
            "neighborhood": "MG Road",
            "category": "cinema",
            "lat": 12.9768, "lng": 77.6115,
            "rating": 4.2,
            "opens_at": "10:00", "closes_at": "23:30",
            "price_range": "₹₹",
            "instructions": "6 screens. Metro: MG Road station (Purple Line) — 3 min walk.",
        },
        {
            "name": "Cinepolis Orion Mall",
            "neighborhood": "Rajajinagar",
            "category": "cinema",
            "lat": 13.0119, "lng": 77.5549,
            "rating": 4.1,
            "opens_at": "10:00", "closes_at": "23:30",
            "price_range": "₹₹",
            "instructions": "8 screens on top floor of Orion Mall. Metro: Rajajinagar (Green Line).",
        },
        {
            "name": "PVR Phoenix MarketCity",
            "neighborhood": "Whitefield",
            "category": "cinema",
            "lat": 12.9958, "lng": 77.6972,
            "rating": 4.3,
            "opens_at": "10:00", "closes_at": "00:00",
            "price_range": "₹₹₹",
            "instructions": "11 screens including Gold and IMAX. Best multiplex experience in Whitefield.",
        },
    ]

    poi_ids: dict[str, int] = {}
    for p in pois:
        nbhd_name = p.get("neighborhood", "")
        nbhd_id   = nbhd_ids.get(nbhd_name)
        cur.execute(
            """
            INSERT OR IGNORE INTO points_of_interest
                (city_id, name, neighborhood_id, category, lat, lng, rating,
                 opens_at, closes_at, typical_entry_wait_mins,
                 typical_order_to_serve_mins, typical_darshana_wait_mins,
                 dress_code, instructions, atmosphere_tags, price_range,
                 dietary_tags, capacity)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                city_id,
                p["name"],
                nbhd_id,
                p["category"],
                p.get("lat"),  p.get("lng"),
                p.get("rating"),
                p.get("opens_at"),  p.get("closes_at"),
                p.get("typical_entry_wait_mins", 0),
                p.get("typical_order_to_serve_mins", 0),
                p.get("typical_darshana_wait_mins", 0),
                p.get("dress_code"),
                p.get("instructions"),
                p.get("atmosphere_tags"),
                p.get("price_range"),
                p.get("dietary_tags"),
                p.get("capacity"),
            ),
        )
        poi_ids[p["name"]] = cur.lastrowid
    conn.commit()

    # Refresh poi_ids in case rows already existed
    for p in pois:
        if p["name"] not in poi_ids or poi_ids[p["name"]] == 0:
            cur.execute(
                "SELECT id FROM points_of_interest WHERE city_id = ? AND name = ?",
                (city_id, p["name"]),
            )
            row = cur.fetchone()
            if row:
                poi_ids[p["name"]] = row[0]

    # ── Mall Shops — Phoenix MarketCity ────────────────────────────────────────
    mall_id = poi_ids.get("Phoenix MarketCity Bengaluru")
    if mall_id:
        shops = [
            ("Zara",           "Fashion",     "2",  "East Wing"),
            ("H&M",            "Fashion",     "1",  "Central"),
            ("Starbucks",      "Cafe",         "G",  "Main Atrium"),
            ("Croma",          "Electronics",  "1",  "West Wing"),
            ("Lifestyle",      "Department",   "1",  "North Wing"),
            ("Nike",           "Sportswear",   "2",  "East Wing"),
            ("Adidas",         "Sportswear",   "2",  "East Wing"),
            ("The Body Shop",  "Beauty",        "G",  "Main Atrium"),
            ("BookMyShow",     "Entertainment","3",  "PVR Level"),
            ("Food Court",     "Food",          "3",  "Top Floor"),
        ]
        for shop_name, cat, floor, wing in shops:
            cur.execute(
                """
                INSERT OR IGNORE INTO mall_shops (mall_id, shop_name, category, floor, building_wing)
                VALUES (?, ?, ?, ?, ?)
                """,
                (mall_id, shop_name, cat, floor, wing),
            )
        conn.commit()

    # ── Traffic rules ──────────────────────────────────────────────────────────
    traffic = [
        ("Outer Ring Road (ORR)",     "08:00", "10:00", 2.5,
         "Avoid ORR during morning rush. Use HAL Old Airport Road or Sarjapur Road alternate."),
        ("Outer Ring Road (ORR)",     "17:00", "19:30", 2.5,
         "Evening peak equally bad. Metro from Marathahalli to Majestic if applicable."),
        ("Silk Board Junction",        "07:30", "10:00", 3.0,
         "Worst bottleneck in Bengaluru. Leave by 07:00 or after 10:30. Flyover provides partial relief."),
        ("Silk Board Junction",        "17:00", "20:00", 3.0,
         "Avoid completely. Use Sarjapur Road directly to Electronic City or NICE Road."),
        ("KR Puram Bridge",            "08:00", "10:00", 2.2,
         "Only bridge over Outer Ring Road near Whitefield. Use Tin Factory route as alternate."),
        ("Hebbal Flyover",             "08:00", "10:30", 2.0,
         "North Bengaluru bottleneck. Airport-bound traffic. Allow extra 20 min."),
        ("Hosur Road (Electronic City)","17:30","20:00", 2.3,
         "IT crowd exodus. Elevated tollway faster but costs ₹50. Signal-free option."),
        ("MG Road / Brigade Road",     "18:00", "21:00", 1.8,
         "Weekend evenings very congested. Metro to MG Road station recommended."),
    ]
    for route, peak_start, peak_end, factor, note in traffic:
        cur.execute(
            """
            INSERT OR IGNORE INTO traffic_rules
                (city_id, route_name, peak_start, peak_end, congestion_factor, avoidance_note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (city_id, route, peak_start, peak_end, factor, note),
        )
    conn.commit()

    # ── Weather forecasts (typical June–September monsoon season) ──────────────
    weather = [
        (0,  "Clear",    22, 0, 78, 10),
        (3,  "Clear",    21, 0, 80, 5),
        (6,  "Partly Cloudy", 23, 2, 76, 20),
        (9,  "Mostly Cloudy", 26, 6, 70, 40),
        (11, "Partly Cloudy", 28, 8, 65, 30),
        (13, "Thunderstorm", 27, 7, 75, 75),
        (15, "Heavy Rain",   25, 4, 85, 90),
        (17, "Drizzle",      24, 2, 88, 65),
        (19, "Partly Cloudy",23, 1, 82, 40),
        (21, "Clear",        22, 0, 79, 15),
    ]
    for hour, cond, temp, uv, humid, precip in weather:
        cur.execute(
            """
            INSERT OR IGNORE INTO weather_forecasts
                (city_id, hour_of_day, condition, temp_celsius,
                 uv_index, humidity, precipitation_probability)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (city_id, hour, cond, temp, uv, humid, precip),
        )
    conn.commit()
