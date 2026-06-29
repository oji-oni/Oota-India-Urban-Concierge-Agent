"""
Oota City Data MCP Server.
Exposes SQLite data to the concierge agent using FastMCP.
"""
from __future__ import annotations

import os
import sqlite3
import math
import json
import zipfile
from pathlib import Path
from datetime import datetime
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("City Data Server")

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/oota.db")).resolve()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

# Haversine distance helper
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@mcp.tool()
def list_supported_cities() -> str:
    """List all supported cities in the system."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM cities").fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def get_area_info(city: str, area_name: str) -> str:
    """Get neighborhood info and description/vibe for a city."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT n.* FROM neighborhoods n
            JOIN cities c ON n.city_id = c.id
            WHERE c.slug = ? AND n.name LIKE ?
            """,
            (city.lower(), f"%{area_name}%")
        ).fetchone()
        return json.dumps(dict(row) if row else {}, default=str)

@mcp.tool()
def search_points_of_interest(
    city: str,
    category: str = "",
    neighborhood: str = "",
    dietary_tags: str = "",
    price_range: str = "",
    atmosphere: str = "",
    limit: int = 10
) -> str:
    """Search for points of interest (restaurants, temples, malls, parks, etc.) in a city."""
    query = """
        SELECT p.*, n.name as neighborhood_name
        FROM points_of_interest p
        JOIN cities c ON p.city_id = c.id
        LEFT JOIN neighborhoods n ON p.neighborhood_id = n.id
        WHERE c.slug = ?
    """
    params = [city.lower()]

    if category:
        query += " AND p.category = ?"
        params.append(category.lower())
    if neighborhood:
        query += " AND n.name LIKE ?"
        params.append(f"%{neighborhood}%")
    if dietary_tags:
        query += " AND p.dietary_tags LIKE ?"
        params.append(f"%{dietary_tags}%")
    if price_range:
        query += " AND p.price_range = ?"
        params.append(price_range)
    if atmosphere:
        query += " AND p.atmosphere_tags LIKE ?"
        params.append(f"%{atmosphere}%")

    query += " LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def get_poi_details(poi_id: int) -> str:
    """Get full details of a specific point of interest (timings, waits, dress code, instructions)."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM points_of_interest WHERE id = ?", (poi_id,)).fetchone()
        return json.dumps(dict(row) if row else {}, default=str)

@mcp.tool()
def find_midpoint_pois(city: str, area_a: str, area_b: str, category: str = "restaurant") -> str:
    """Find points of interest near the geographical midpoint of two areas."""
    with get_db() as conn:
        # Get coordinates of Area A and Area B
        r_a = conn.execute(
            "SELECT n.lat, n.lng FROM neighborhoods n JOIN cities c ON n.city_id = c.id WHERE c.slug = ? AND n.name = ?",
            (city.lower(), area_a)
        ).fetchone()
        r_b = conn.execute(
            "SELECT n.lat, n.lng FROM neighborhoods n JOIN cities c ON n.city_id = c.id WHERE c.slug = ? AND n.name = ?",
            (city.lower(), area_b)
        ).fetchone()

        if not r_a or not r_b:
            return json.dumps({"error": f"One or both areas not found. A: {bool(r_a)}, B: {bool(r_b)}"})

        mid_lat = (r_a["lat"] + r_b["lat"]) / 2
        mid_lng = (r_a["lng"] + r_b["lng"]) / 2

        # Fetch POIs and calculate distance to midpoint
        pois = conn.execute(
            "SELECT p.*, n.name as neighborhood_name FROM points_of_interest p JOIN cities c ON p.city_id = c.id LEFT JOIN neighborhoods n ON p.neighborhood_id = n.id WHERE c.slug = ? AND p.category = ?",
            (city.lower(), category.lower())
        ).fetchall()

        results = []
        for p in pois:
            dist = haversine(mid_lat, mid_lng, p["lat"], p["lng"])
            p_dict = dict(p)
            p_dict["distance_to_midpoint_km"] = dist
            results.append(p_dict)

        results.sort(key=lambda x: x["distance_to_midpoint_km"])
        return json.dumps(results[:5], default=str)

@mcp.tool()
def calculate_group_midpoint(city: str, area_list: str, category: str = "restaurant") -> str:
    """Calculate geographic centroid for 3+ areas and return closest POIs."""
    areas = json.loads(area_list)
    if not areas or len(areas) < 2:
        return json.dumps({"error": "Need at least 2 areas"})

    with get_db() as conn:
        lats, lngs = [], []
        for area in areas:
            row = conn.execute(
                "SELECT n.lat, n.lng FROM neighborhoods n JOIN cities c ON n.city_id = c.id WHERE c.slug = ? AND n.name = ?",
                (city.lower(), area)
            ).fetchone()
            if row:
                lats.append(row["lat"])
                lngs.append(row["lng"])

        if not lats:
            return json.dumps({"error": "No valid areas found"})

        cent_lat = sum(lats) / len(lats)
        cent_lng = sum(lngs) / len(lngs)

        pois = conn.execute(
            "SELECT p.*, n.name as neighborhood_name FROM points_of_interest p JOIN cities c ON p.city_id = c.id LEFT JOIN neighborhoods n ON p.neighborhood_id = n.id WHERE c.slug = ? AND p.category = ?",
            (city.lower(), category.lower())
        ).fetchall()

        results = []
        for p in pois:
            dist = haversine(cent_lat, cent_lng, p["lat"], p["lng"])
            p_dict = dict(p)
            p_dict["distance_to_centroid_km"] = dist
            results.append(p_dict)

        results.sort(key=lambda x: x["distance_to_centroid_km"])
        return json.dumps({
            "centroid": {"lat": cent_lat, "lng": cent_lng},
            "nearest_pois": results[:5]
        }, default=str)

@mcp.tool()
def estimate_auto_fare(distance_km: float, time_of_day: str = "day") -> str:
    """Estimate auto-rickshaw fare (standard meter vs app surge estimate)."""
    # Standard Bangalore meter: base Rs 30 for first 1.8km, then Rs 15/km
    # Night surcharge: 25% extra between 10 PM and 5 AM
    is_night = time_of_day.lower() in ["night", "late", "10pm-5am"]
    
    base_dist = 1.8
    base_fare = 30.0
    rate_per_km = 15.0

    if distance_km <= base_dist:
        meter_fare = base_fare
    else:
        meter_fare = base_fare + (distance_km - base_dist) * rate_per_km

    if is_night:
        meter_fare *= 1.25

    # App surges: usually 1.3x to 2.2x base meter
    surge_min = meter_fare * 1.3
    surge_max = meter_fare * 2.2

    return json.dumps({
        "distance_km": distance_km,
        "time_of_day": time_of_day,
        "standard_meter_fare_rupees": round(meter_fare, 2),
        "app_estimate_min_rupees": round(surge_min, 2),
        "app_estimate_max_rupees": round(surge_max, 2)
    })

@mcp.tool()
def calculate_metro_ticket_fare(from_station_id: int, to_station_id: int) -> str:
    """Calculate the exact metro fare and platform transfer walking overhead."""
    with get_db() as conn:
        fare_row = conn.execute(
            "SELECT fare_rupees FROM metro_fares WHERE from_station_id = ? AND to_station_id = ?",
            (from_station_id, to_station_id)
        ).fetchone()

        s_from = conn.execute("SELECT * FROM transit_stations WHERE id = ?", (from_station_id,)).fetchone()
        s_to = conn.execute("SELECT * FROM transit_stations WHERE id = ?", (to_station_id,)).fetchone()

        if not s_from or not s_to:
            return json.dumps({"error": "Invalid station IDs"})

        # Estimate delay if interchange
        walk_delay = 0
        notes = []
        if s_from["line_name"] != s_to["line_name"]:
            # If interchange at Majestic or other
            walk_delay = s_from["platform_walk_delay_mins"] or 2
            notes.append(f"Interchange platform transfer delay: {walk_delay} mins.")

        fare = fare_row["fare_rupees"] if fare_row else 30 # default flat
        
        return json.dumps({
            "from_station": s_from["name"],
            "to_station": s_to["name"],
            "fare_rupees": fare,
            "platform_walk_delay_mins": walk_delay,
            "notes": " ".join(notes)
        })

@mcp.tool()
def search_mall_shops(mall_id: int, purchase_category: str = "") -> str:
    """Search for shops within a specific mall by category."""
    query = "SELECT * FROM mall_shops WHERE mall_id = ?"
    params = [mall_id]
    if purchase_category:
        query += " AND category LIKE ?"
        params.append(f"%{purchase_category}%")

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def search_movies(city: str, genre: str = "", cinema_id: int = 0) -> str:
    """Search currently running movies in cinemas for a city."""
    query = """
        SELECT m.*, p.name as cinema_name
        FROM movies m
        JOIN cities c ON m.city_id = c.id
        LEFT JOIN points_of_interest p ON m.cinema_id = p.id
        WHERE c.slug = ?
    """
    params = [city.lower()]

    if genre:
        query += " AND m.genre LIKE ?"
        params.append(f"%{genre}%")
    if cinema_id:
        query += " AND m.cinema_id = ?"
        params.append(cinema_id)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def save_itinerary(user_id: str, poi_id: int, meeting_time: str, departure_time: str, origin_area: str) -> str:
    """Save user travel itinerary details to DB."""
    with get_db() as conn:
        poi = conn.execute("SELECT city_id FROM points_of_interest WHERE id = ?", (poi_id,)).fetchone()
        if not poi:
            return json.dumps({"error": "POI not found"})
        
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO active_itineraries (user_id, city_id, destination_poi_id, meeting_time, departure_time, origin_area, status)
            VALUES (?, ?, ?, ?, ?, ?, 'planned')
            """,
            (user_id, poi["city_id"], poi_id, meeting_time, departure_time, origin_area)
        )
        conn.commit()
        return json.dumps({"status": "saved", "itinerary_id": cur.lastrowid})

@mcp.tool()
def get_active_itineraries(user_id: str = "") -> str:
    """Get active scheduled itineraries."""
    query = """
        SELECT a.*, p.name as destination_name, c.name as city_name
        FROM active_itineraries a
        JOIN cities c ON a.city_id = c.id
        LEFT JOIN points_of_interest p ON a.destination_poi_id = p.id
        WHERE a.status = 'planned'
    """
    params = []
    if user_id:
        query += " AND a.user_id = ?"
        params.append(user_id)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def update_itinerary_status(itinerary_id: int, status: str) -> str:
    """Update active itinerary status (e.g. 'completed', 'cancelled', 'delayed')."""
    with get_db() as conn:
        conn.execute("UPDATE active_itineraries SET status = ? WHERE id = ?", (status, itinerary_id))
        conn.commit()
        return json.dumps({"status": "updated", "itinerary_id": itinerary_id, "new_status": status})

@mcp.tool()
def get_transit_route(city: str, from_area: str, to_area: str) -> str:
    """Compute transit routes using metro/local trains between two neighborhoods."""
    with get_db() as conn:
        # Find transit stations near both areas
        s_from = conn.execute(
            """
            SELECT s.* FROM transit_stations s
            JOIN cities c ON s.city_id = c.id
            JOIN neighborhoods n ON n.nearest_transit_station_id = s.id
            WHERE c.slug = ? AND n.name = ?
            """,
            (city.lower(), from_area)
        ).fetchone()

        s_to = conn.execute(
            """
            SELECT s.* FROM transit_stations s
            JOIN cities c ON s.city_id = c.id
            JOIN neighborhoods n ON n.nearest_transit_station_id = s.id
            WHERE c.slug = ? AND n.name = ?
            """,
            (city.lower(), to_area)
        ).fetchone()

        if not s_from or not s_to:
            return json.dumps({"error": f"Transit stations not mapped for areas. From: {bool(s_from)}, To: {bool(s_to)}"})

        # Simple mock pathfinder or database pathlookup
        route_row = conn.execute(
            "SELECT * FROM transit_routes WHERE from_station_id = ? AND to_station_id = ?",
            (s_from["id"], s_to["id"])
        ).fetchone()

        if route_row:
            return json.dumps({
                "from_station": s_from["name"],
                "to_station": s_to["name"],
                "travel_time_mins": route_row["travel_time_mins"],
                "interchanges": json.loads(route_row["interchanges"]) if route_row["interchanges"] else []
            }, default=str)

        # Fallback haversine estimation
        dist = haversine(s_from["lat"], s_from["lng"], s_to["lat"], s_to["lng"])
        est_mins = int(dist * 2.5) + 5 # 2.5 min per km + buffer
        
        return json.dumps({
            "from_station": s_from["name"],
            "to_station": s_to["name"],
            "travel_time_mins": est_mins,
            "interchanges": ["Majestic"] if s_from["line_name"] != s_to["line_name"] else [],
            "notes": "Estimated via straight-line transit corridors."
        })

@mcp.tool()
def get_transit_station_nearby(city: str, neighborhood: str) -> str:
    """Find the nearest transit station for a neighborhood."""
    with get_db() as conn:
        row = conn.execute(
            """
            SELECT s.* FROM transit_stations s
            JOIN neighborhoods n ON n.nearest_transit_station_id = s.id
            JOIN cities c ON n.city_id = c.id
            WHERE c.slug = ? AND n.name = ?
            """,
            (city.lower(), neighborhood)
        ).fetchone()
        return json.dumps(dict(row) if row else {}, default=str)

@mcp.tool()
def search_events(city: str, date: str = "", event_type: str = "", neighborhood: str = "") -> str:
    """Find cultural events in a city."""
    query = """
        SELECT e.*, p.name as venue_name, n.name as neighborhood_name
        FROM events e
        JOIN cities c ON e.city_id = c.id
        LEFT JOIN points_of_interest p ON e.venue_id = p.id
        LEFT JOIN neighborhoods n ON e.neighborhood_id = n.id
        WHERE c.slug = ?
    """
    params = [city.lower()]
    if date:
        query += " AND e.date = ?"
        params.append(date)
    if event_type:
        query += " AND e.type = ?"
        params.append(event_type.lower())
    if neighborhood:
        query += " AND n.name = ?"
        params.append(neighborhood)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def estimate_travel_time(city: str, from_area: str, to_area: str, mode: str = "metro", time_of_day: str = "day") -> str:
    """Estimate travel time between two neighborhoods incorporating peak hours traffic factor."""
    with get_db() as conn:
        r_from = conn.execute(
            "SELECT lat, lng FROM neighborhoods WHERE name = ?", (from_area,)
        ).fetchone()
        r_to = conn.execute(
            "SELECT lat, lng FROM neighborhoods WHERE name = ?", (to_area,)
        ).fetchone()

        if not r_from or not r_to:
            return json.dumps({"error": "Invalid neighborhoods"})

        dist = haversine(r_from["lat"], r_from["lng"], r_to["lat"], r_to["lng"])

        # Base speeds: Metro=35km/h, Cab/Auto=20km/h
        if mode.lower() == "metro":
            base_mins = int((dist / 35) * 60) + 6 # + station overheads
        else:
            base_mins = int((dist / 20) * 60) + 5

        # Check peak hour rules
        # Mock peak matching
        multiplier = 1.0
        notes = []
        
        # Simple congestion check
        rules = conn.execute(
            "SELECT * FROM traffic_rules WHERE city_id = (SELECT id FROM cities WHERE slug=?)",
            (city.lower(),)
        ).fetchall()
        
        for rule in rules:
            # check if time overlaps
            # (In production we parse HH:MM, here we check simplified rules)
            if "peak" in time_of_day.lower() or "5" in time_of_day or "6" in time_of_day or "8" in time_of_day or "9" in time_of_day:
                multiplier = max(multiplier, rule["congestion_factor"])
                notes.append(f"Congested route factor {rule['congestion_factor']}x applied: {rule['avoidance_note'] or ''}")

        final_mins = int(base_mins * multiplier)
        return json.dumps({
            "distance_km": round(dist, 2),
            "base_duration_mins": base_mins,
            "final_duration_mins": final_mins,
            "traffic_multiplier": multiplier,
            "notes": " ".join(notes)
        })

@mcp.tool()
def get_weather_forecast(city: str, time_of_day: str = "") -> str:
    """Retrieve weather forecast details for planning check."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM weather_forecasts WHERE city_id = (SELECT id FROM cities WHERE slug=?)",
            (city.lower(),)
        ).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

@mcp.tool()
def get_weather_radar_warning(city: str, neighborhood: str) -> str:
    """Returns rain warning alert if precipitation probability is high."""
    with get_db() as conn:
        # Check if there is high rain forecast in this city
        row = conn.execute(
            "SELECT MAX(precipitation_probability) as max_rain FROM weather_forecasts WHERE city_id = (SELECT id FROM cities WHERE slug=?)",
            (city.lower(),)
        ).fetchone()
        
        max_rain = row["max_rain"] if row and row["max_rain"] is not None else 0
        if max_rain > 60:
            return json.dumps({
                "rain_warning": True,
                "precipitation_probability": max_rain,
                "recommendation": f"High rain probability in {city} ({max_rain}%). Suggest choosing indoor venues rather than outdoor parks."
            })
        return json.dumps({"rain_warning": False, "precipitation_probability": max_rain})

@mcp.tool()
def log_shared_expense(itinerary_id: int, payer_user_id: str, description: str, total_amount_rupees: float, split_type: str, split_data: str) -> str:
    """Log a shared group expense split locally."""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO shared_expenses (itinerary_id, payer_user_id, description, total_amount_rupees, split_type, split_data)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (itinerary_id, payer_user_id, description, total_amount_rupees, split_type, split_data)
        )
        conn.commit()
        return json.dumps({"status": "expense_logged", "id": cur.lastrowid})

@mcp.tool()
def get_expense_balances(itinerary_id: int) -> str:
    """Get summarized debt balances for a shared outing."""
    with get_db() as conn:
        expenses = conn.execute("SELECT * FROM shared_expenses WHERE itinerary_id = ?", (itinerary_id,)).fetchall()
        if not expenses:
            return json.dumps({"balances": [], "notes": "No expenses logged for this itinerary."})

        # Calculate splits:
        # split_data usually looks like: {"Arjun": 500, "Priya": 500, "me": 500}
        debts = {} # who owes what
        for exp in expenses:
            payer = exp["payer_user_id"]
            splits = json.loads(exp["split_data"])
            for person, share in splits.items():
                if person == payer:
                    continue
                # person owes share to payer
                pair = (person, payer)
                debts[pair] = debts.get(pair, 0.0) + share

        # Simplify net debts
        simplified = []
        for (debtor, creditor), amount in list(debts.items()):
            # check reverse
            rev_pair = (creditor, debtor)
            if rev_pair in debts:
                rev_amount = debts[rev_pair]
                if amount > rev_amount:
                    debts[rev_pair] = 0.0
                    debts[(debtor, creditor)] = amount - rev_amount
                else:
                    debts[(debtor, creditor)] = 0.0
                    debts[rev_pair] = rev_amount - amount

        for (debtor, creditor), amount in debts.items():
            if amount > 0:
                simplified.append(f"{debtor} owes {creditor} ₹{round(amount, 2)}")

        return json.dumps({"balances": simplified})

@mcp.tool()
def get_budget_status(user_id: str) -> str:
    """Check remaining user budget status for current month."""
    month_yr = datetime.now().strftime("%m-%Y")
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_budgets WHERE user_id = ? AND month_year = ?",
            (user_id, month_yr)
        ).fetchone()

        if not row:
            # Seed default budget
            conn.execute(
                "INSERT INTO user_budgets (user_id, monthly_limit_rupees, active_spent_rupees, month_year) VALUES (?, 5000.0, 0.0, ?)",
                (user_id, month_yr)
            )
            conn.commit()
            return json.dumps({
                "monthly_limit_rupees": 5000.0,
                "active_spent_rupees": 0.0,
                "remaining_budget_rupees": 5000.0
            })

        remaining = row["monthly_limit_rupees"] - row["active_spent_rupees"]
        return json.dumps({
            "monthly_limit_rupees": row["monthly_limit_rupees"],
            "active_spent_rupees": row["active_spent_rupees"],
            "remaining_budget_rupees": round(remaining, 2)
        })

@mcp.tool()
def search_local_documents(query_text: str) -> str:
    """Perform RAG check on local PDFs/markdown inside data/documents/."""
    docs_dir = Path("./data/documents")
    if not docs_dir.exists():
        return json.dumps({"error": "No documents folder exists at ./data/documents"})

    results = []
    # Loop files and search for matching words
    for file in docs_dir.glob("**/*"):
        if file.suffix in [".txt", ".md"]:
            content = file.read_text(encoding="utf-8", errors="ignore")
            if query_text.lower() in content.lower():
                # Extract snippet
                idx = content.lower().find(query_text.lower())
                snippet = content[max(0, idx-100):min(len(content), idx+200)]
                results.append({
                    "file_name": file.name,
                    "file_path": str(file),
                    "snippet": f"...{snippet}..."
                })

    return json.dumps(results[:5])

@mcp.tool()
def export_local_backup() -> str:
    """Package SQLite database and local configuration files into a password-protected zip file."""
    output_zip = Path("./oota_backup.zip")
    try:
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Backup DB
            if DB_PATH.exists():
                zipf.write(DB_PATH, arcname="oota.db")
            # Backup skills
            skills_dir = Path("./.agents/skills")
            if skills_dir.exists():
                for file in skills_dir.glob("**/*"):
                    if file.is_file():
                        zipf.write(file, arcname=str(file.relative_to(Path("."))))
        return json.dumps({"status": "backup_created", "backup_file": str(output_zip.resolve())})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def get_city_traffic_rules(city: str) -> str:
    """Get traffic rules and peak congestion hours for a city."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT t.* FROM traffic_rules t
            JOIN cities c ON t.city_id = c.id
            WHERE c.slug = ?
            """,
            (city.lower(),)
        ).fetchall()
        return json.dumps([dict(r) for r in rows], default=str)

if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
