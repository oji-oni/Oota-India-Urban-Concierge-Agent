"""
Delhi city seed data for Oota India Urban Concierge.
"""
from __future__ import annotations
import sqlite3


def seed_city(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO cities (name, slug, state, lat, lng, timezone, transit_system_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("Delhi", "delhi", "Delhi", 28.6139, 77.2090, "Asia/Kolkata", "Delhi Metro"),
    )
    conn.commit()
    cur.execute("SELECT id FROM cities WHERE slug = 'delhi'")
    city_id = cur.fetchone()[0]

    neighborhoods = [
        ("Connaught Place",  28.6315, 77.2167, "Colonial-era commercial hub, circular market, fine dining"),
        ("Lajpat Nagar",     28.5672, 77.2371, "South Delhi, market for fabrics, street food, middle-class vibe"),
        ("Karol Bagh",       28.6509, 77.1907, "Dense market, bridal shopping, backpacker hotels, mix of everything"),
        ("Hauz Khas",        28.5535, 77.2065, "Upscale, village-turned-trendy, lake view, boutiques, nightlife"),
        ("Chandni Chowk",    28.6562, 77.2306, "Oldest market in India, street food paradise, Mughal heritage"),
        ("Vasant Kunj",      28.5209, 77.1577, "South-west Delhi, malls, residential, expat-friendly"),
        ("Saket",            28.5244, 77.2175, "Planned suburb, Select City Walk mall, PVR cinemas"),
        ("Nehru Place",      28.5491, 77.2506, "IT market, electronics hub, South-East Delhi"),
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

    # Yellow Line: Samaypur Badli → HUDA City Centre (via Connaught Place)
    yellow_line = [
        ("Samaypur Badli",         28.7452, 77.1277, False, 2),
        ("Rohini Sector 18, 19",   28.7287, 77.1320, False, 2),
        ("Haiderpur Badli Mor",    28.7201, 77.1518, False, 2),
        ("Jahangirpuri",           28.7133, 77.1641, False, 2),
        ("Adarsh Nagar",           28.7058, 77.1724, False, 2),
        ("Azadpur",                28.7019, 77.1777, True,  3),
        ("Model Town",             28.6964, 77.1967, False, 2),
        ("GTB Nagar",              28.6976, 77.2066, False, 2),
        ("Vishwa Vidyalaya",       28.6913, 77.2103, False, 2),
        ("Vidhan Sabha",           28.6837, 77.2068, False, 2),
        ("Civil Lines",            28.6762, 77.2144, False, 2),
        ("Kashmere Gate",          28.6672, 77.2282, True,  4),
        ("Chandni Chowk",          28.6565, 77.2303, False, 2),
        ("Chawri Bazar",           28.6487, 77.2285, False, 2),
        ("New Delhi",              28.6415, 77.2200, True,  5),
        ("Rajiv Chowk (CP)",       28.6328, 77.2197, True,  6),
        ("Patel Chowk",            28.6240, 77.2139, False, 2),
        ("Central Secretariat",    28.6152, 77.2115, True,  4),
        ("Udyog Bhawan",           28.6105, 77.2134, False, 2),
        ("Lok Kalyan Marg",        28.5990, 77.2063, False, 2),
        ("Jor Bagh",               28.5897, 77.2101, False, 2),
        ("INA",                    28.5791, 77.2092, True,  3),
        ("AIIMS",                  28.5664, 77.2100, False, 2),
        ("Green Park",             28.5583, 77.2095, False, 2),
        ("Hauz Khas",              28.5436, 77.2066, True,  3),
        ("Malviya Nagar",          28.5306, 77.2073, False, 2),
        ("Saket",                  28.5219, 77.2078, False, 2),
        ("Qutub Minar",            28.5128, 77.1849, False, 2),
        ("Chhattarpur",            28.5005, 77.1714, False, 2),
        ("Sultanpur",              28.4869, 77.1557, False, 2),
        ("Ghitorni",               28.4742, 77.1454, False, 2),
        ("Arjan Garh",             28.4571, 77.1265, False, 2),
        ("Guru Dronacharya",       28.4462, 77.1097, False, 2),
        ("Sikanderpur",            28.4342, 77.0960, False, 2),
        ("MG Road Gurgaon",        28.4226, 77.0853, False, 2),
        ("IFFCO Chowk",            28.4131, 77.0739, False, 2),
        ("HUDA City Centre",       28.4595, 77.0740, False, 2),
    ]
    # Blue Line: Dwarka Sector 21 → Vaishali / Noida City Centre
    blue_line = [
        ("Dwarka Sector 21",  28.5526, 77.0583, True,  4),
        ("Dwarka Sector 8",   28.5666, 77.0723, False, 2),
        ("Dwarka Sector 9",   28.5888, 77.0728, False, 2),
        ("Dwarka Sector 10",  28.5983, 77.0750, False, 2),
        ("Dwarka Sector 11",  28.6065, 77.0743, False, 2),
        ("Dwarka Sector 12",  28.6133, 77.0711, False, 2),
        ("Dwarka Sector 13",  28.6188, 77.0681, False, 2),
        ("Dwarka Sector 14",  28.6243, 77.0659, False, 2),
        ("Dwarka",            28.6271, 77.0599, False, 2),
        ("Dwarka Mor",        28.6332, 77.0634, False, 2),
        ("Nawada",            28.6387, 77.0760, False, 2),
        ("Uttam Nagar West",  28.6437, 77.0851, False, 2),
        ("Uttam Nagar East",  28.6480, 77.0972, False, 2),
        ("Janakpuri West",    28.6291, 77.0883, False, 2),
        ("Janakpuri East",    28.6316, 77.1023, False, 2),
        ("Tilak Nagar",       28.6327, 77.1153, False, 2),
        ("Subhash Nagar",     28.6366, 77.1268, False, 2),
        ("Tagore Garden",     28.6399, 77.1372, False, 2),
        ("Rajouri Garden",    28.6456, 77.1466, True,  3),
        ("Ramesh Nagar",      28.6501, 77.1571, False, 2),
        ("Moti Nagar",        28.6549, 77.1657, False, 2),
        ("Kirti Nagar",       28.6566, 77.1736, True,  3),
        ("Shadipur",          28.6533, 77.1822, False, 2),
        ("Patel Nagar",       28.6536, 77.1894, False, 2),
        ("Rajendra Place",    28.6542, 77.1984, False, 2),
        ("Karol Bagh",        28.6514, 77.1908, False, 2),
        ("Jhandewalan",       28.6444, 77.1990, False, 2),
        ("Ramakrishna Ashram Marg",28.6385,77.2078, False, 2),
        ("Rajiv Chowk",       28.6328, 77.2197, True,  6),
        ("Barakhamba Road",   28.6285, 77.2272, False, 2),
        ("Mandi House",       28.6244, 77.2340, True,  3),
        ("Pragati Maidan",    28.6183, 77.2448, False, 2),
        ("Indraprastha",      28.6139, 77.2534, False, 2),
        ("Yamuna Bank",       28.6233, 77.2687, True,  3),
        ("Laxmi Nagar",       28.6318, 77.2783, False, 2),
        ("Nirman Vihar",      28.6408, 77.2877, False, 2),
        ("Preet Vihar",       28.6456, 77.2955, False, 2),
        ("Karkarduma",        28.6502, 77.3045, False, 2),
        ("Anand Vihar ISBT",  28.6474, 77.3155, True,  4),
        ("Vaishali",          28.6455, 77.3378, False, 2),
    ]

    station_ids: dict[str, int] = {}
    for line_stations, line_name, color, system in [
        (yellow_line, "Yellow Line", "#F9A825", "Delhi Metro"),
        (blue_line,   "Blue Line",   "#1565C0", "Delhi Metro"),
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
                (city_id, name, system, line_name, color, seq, lat, lng, int(is_ichange), delay),
            )
            station_ids[f"{line_name}:{name}"] = cur.lastrowid
    conn.commit()

    pois = [
        {"name": "Paranthe Wali Gali", "neighborhood": "Chandni Chowk", "category": "restaurant",
         "lat": 28.6558, "lng": 77.2302, "rating": 4.3,
         "opens_at": "08:00", "closes_at": "22:00",
         "typical_order_to_serve_mins": 10,
         "atmosphere_tags": "street-food,heritage,stuffed-parathas,old-Delhi",
         "price_range": "₹", "dietary_tags": "veg",
         "instructions": "Famous lane with multiple shops selling 20+ varieties of stuffed paranthas since 1870s. Best visited morning."},
        {"name": "Bukhara ITC Maurya", "neighborhood": "Connaught Place", "category": "restaurant",
         "lat": 28.5990, "lng": 77.1711, "rating": 4.7,
         "opens_at": "12:30", "closes_at": "23:45",
         "typical_order_to_serve_mins": 30,
         "atmosphere_tags": "fine-dining,NWFP-cuisine,world-famous,leather-bib",
         "price_range": "₹₹₹₹", "dietary_tags": "non-veg",
         "instructions": "Dal Bukhara slow-cooked for 18 hours. World's 50 Best Restaurants listed. Reservations mandatory. Smart casual dress code."},
        {"name": "Saravana Bhavan Connaught Place", "neighborhood": "Connaught Place", "category": "restaurant",
         "lat": 28.6343, "lng": 77.2206, "rating": 4.2,
         "opens_at": "08:00", "closes_at": "23:00",
         "typical_order_to_serve_mins": 15,
         "atmosphere_tags": "South-Indian,vegetarian,reliable,chain",
         "price_range": "₹₹", "dietary_tags": "pure-veg",
         "instructions": "Reliable South Indian food in North India. Idli-dosa-vada. Good for vegetarians."},
        {"name": "Akshardham Temple", "neighborhood": "Connaught Place", "category": "temple",
         "lat": 28.6127, "lng": 77.2773, "rating": 4.8,
         "opens_at": "09:30", "closes_at": "18:00",
         "typical_darshana_wait_mins": 80,
         "typical_entry_wait_mins": 30,
         "dress_code": "No shorts, sleeveless, or revealing clothing; covers provided at gate",
         "atmosphere_tags": "grand,UNESCO-nominated,musical-fountain,exhibitions",
         "instructions": "No electronic devices inside. Security check takes 20–30 min. Musical fountain show at 7:30pm and 8:30pm. Allow 3–4 hours."},
        {"name": "India Gate", "neighborhood": "Connaught Place", "category": "monument",
         "lat": 28.6129, "lng": 77.2295, "rating": 4.6,
         "opens_at": "00:00", "closes_at": "23:59",
         "typical_entry_wait_mins": 0,
         "price_range": "free",
         "atmosphere_tags": "iconic,war-memorial,lawn,picnic,heritage",
         "instructions": "Best at sunset or illuminated at night. Republic Day parade starts here. Rajpath lawns: great for picnics."},
        {"name": "Qutub Minar", "neighborhood": "Hauz Khas", "category": "heritage",
         "lat": 28.5245, "lng": 77.1855, "rating": 4.5,
         "opens_at": "07:00", "closes_at": "17:00",
         "typical_entry_wait_mins": 15,
         "price_range": "₹₹",
         "atmosphere_tags": "UNESCO,Mughal,historic,73m-minaret",
         "instructions": "Entry: ₹40 Indians, ₹600 foreigners. No climbing permitted. Nearest metro: Qutub Minar (Yellow Line)."},
        {"name": "Select City Walk Mall", "neighborhood": "Saket", "category": "mall",
         "lat": 28.5278, "lng": 77.2195, "rating": 4.4,
         "opens_at": "11:00", "closes_at": "22:00",
         "price_range": "₹₹₹",
         "atmosphere_tags": "premium,open-air,South-Delhi,food-court,cinema",
         "instructions": "One of Delhi's best malls. Metro: Saket (Yellow Line). PVR Cinemas on top floor. Upscale brands."},
        {"name": "DLF Promenade Vasant Kunj", "neighborhood": "Vasant Kunj", "category": "mall",
         "lat": 28.5180, "lng": 77.1590, "rating": 4.3,
         "opens_at": "11:00", "closes_at": "22:00",
         "price_range": "₹₹₹",
         "atmosphere_tags": "premium,luxury-brands,anchor-Zara,food-options",
         "instructions": "Premium mall in South-West Delhi. No direct metro; cab/auto from Dwarka Sector 21 or Saket."},
        {"name": "Jama Masjid", "neighborhood": "Chandni Chowk", "category": "mosque",
         "lat": 28.6507, "lng": 77.2334, "rating": 4.6,
         "opens_at": "07:00", "closes_at": "21:30",
         "typical_entry_wait_mins": 10,
         "dress_code": "Conservative clothing; head covering for women; remove shoes",
         "atmosphere_tags": "Mughal,largest-mosque-India,historic,photo-spot",
         "price_range": "free",
         "instructions": "Closed during prayer times (5 prayers daily). Minarets open for viewing for ₹100. Great city views from top."},
        {"name": "Dilli Haat INA", "neighborhood": "Lajpat Nagar", "category": "market",
         "lat": 28.5800, "lng": 77.2098, "rating": 4.2,
         "opens_at": "10:30", "closes_at": "22:00",
         "price_range": "₹₹",
         "atmosphere_tags": "craft,culture,regional-food,handloom,open-air",
         "instructions": "Entry: ₹30 adults. Rotating stalls from different Indian states. Good for handicrafts and regional food."},
    ]
    for p in pois:
        nbhd_id = nbhd_ids.get(p.get("neighborhood", ""))
        cur.execute(
            "INSERT OR IGNORE INTO points_of_interest (city_id, name, neighborhood_id, category, lat, lng, rating, opens_at, closes_at, typical_entry_wait_mins, typical_order_to_serve_mins, typical_darshana_wait_mins, dress_code, instructions, atmosphere_tags, price_range, dietary_tags, capacity) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (city_id, p["name"], nbhd_id, p["category"], p.get("lat"), p.get("lng"), p.get("rating"), p.get("opens_at"), p.get("closes_at"), p.get("typical_entry_wait_mins", 0), p.get("typical_order_to_serve_mins", 0), p.get("typical_darshana_wait_mins", 0), p.get("dress_code"), p.get("instructions"), p.get("atmosphere_tags"), p.get("price_range"), p.get("dietary_tags"), p.get("capacity")),
        )
    conn.commit()

    traffic = [
        ("NH-48 (Delhi-Gurgaon Expressway)", "08:00", "10:30", 2.8, "Mahipalpur to Sheetla Mata worst. Metro Yellow Line from HUDA City Centre is faster."),
        ("Ring Road",                        "08:30", "10:00", 2.2, "ITO and Ashram crossings peak. Allow extra 30 min."),
        ("Lal Bahadur Shastri Marg",         "17:00", "20:00", 2.0, "Return traffic from Connaught Place. Metro recommended."),
        ("NH-44 (Delhi-Chandigarh)",         "08:00", "10:00", 2.3, "Mukarba Chowk flyover helps. GTK Depot junction is bottleneck."),
        ("Chandni Chowk Main Road",          "10:00", "20:00", 2.0, "No cars allowed in core area on certain days. Use Metro to Chandni Chowk."),
    ]
    for route, ps, pe, cf, note in traffic:
        cur.execute(
            "INSERT OR IGNORE INTO traffic_rules (city_id, route_name, peak_start, peak_end, congestion_factor, avoidance_note) VALUES (?, ?, ?, ?, ?, ?)",
            (city_id, route, ps, pe, cf, note),
        )
    conn.commit()

    weather = [
        (0,  "Clear",        28, 0, 55, 5),
        (3,  "Clear",        26, 0, 58, 5),
        (6,  "Hazy",         29, 3, 60, 10),
        (9,  "Partly Cloudy",35, 7, 45, 15),
        (12, "Hot & Sunny",  40, 10,35, 5),
        (14, "Hot & Sunny",  42, 10,32, 5),
        (16, "Partly Cloudy",40, 8, 38, 15),
        (18, "Cloudy",       36, 4, 48, 30),
        (20, "Clear",        32, 1, 55, 10),
        (22, "Clear",        29, 0, 57, 5),
    ]
    for hour, cond, temp, uv, humid, precip in weather:
        cur.execute(
            "INSERT OR IGNORE INTO weather_forecasts (city_id, hour_of_day, condition, temp_celsius, uv_index, humidity, precipitation_probability) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (city_id, hour, cond, temp, uv, humid, precip),
        )
    conn.commit()
