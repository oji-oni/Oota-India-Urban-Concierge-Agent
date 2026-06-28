"""
Oota India Urban Concierge — Database Seed Script
Creates the SQLite schema and populates seed data from city modules.
"""
from __future__ import annotations

import importlib
import logging
import os
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

# ── Schema DDL ─────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cities (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 TEXT    NOT NULL,
    slug                 TEXT    NOT NULL UNIQUE,
    state                TEXT    NOT NULL,
    lat                  REAL    NOT NULL,
    lng                  REAL    NOT NULL,
    timezone             TEXT    NOT NULL DEFAULT 'Asia/Kolkata',
    transit_system_name  TEXT
);

CREATE TABLE IF NOT EXISTS neighborhoods (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id                   INTEGER NOT NULL REFERENCES cities(id),
    name                      TEXT    NOT NULL,
    lat                       REAL    NOT NULL,
    lng                       REAL    NOT NULL,
    nearest_transit_station_id INTEGER REFERENCES transit_stations(id),
    vibe                      TEXT
);

CREATE TABLE IF NOT EXISTS transit_stations (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id                INTEGER NOT NULL REFERENCES cities(id),
    name                   TEXT    NOT NULL,
    system                 TEXT    NOT NULL,
    line_name              TEXT,
    line_color             TEXT,
    sequence_order         INTEGER,
    lat                    REAL,
    lng                    REAL,
    is_interchange         INTEGER NOT NULL DEFAULT 0,
    platform_walk_delay_mins INTEGER NOT NULL DEFAULT 2
);

CREATE TABLE IF NOT EXISTS points_of_interest (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id                     INTEGER NOT NULL REFERENCES cities(id),
    name                        TEXT    NOT NULL,
    neighborhood_id             INTEGER REFERENCES neighborhoods(id),
    category                    TEXT    NOT NULL,
    lat                         REAL,
    lng                         REAL,
    rating                      REAL,
    opens_at                    TEXT,
    closes_at                   TEXT,
    typical_entry_wait_mins     INTEGER DEFAULT 0,
    typical_order_to_serve_mins INTEGER DEFAULT 0,
    typical_darshana_wait_mins  INTEGER DEFAULT 0,
    dress_code                  TEXT,
    instructions                TEXT,
    atmosphere_tags             TEXT,
    price_range                 TEXT,
    dietary_tags                TEXT,
    capacity                    INTEGER
);

CREATE TABLE IF NOT EXISTS mall_shops (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    mall_id      INTEGER NOT NULL REFERENCES points_of_interest(id),
    shop_name    TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    floor        TEXT,
    building_wing TEXT
);

CREATE TABLE IF NOT EXISTS movies (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id            INTEGER NOT NULL REFERENCES cities(id),
    cinema_id          INTEGER REFERENCES points_of_interest(id),
    movie_name         TEXT    NOT NULL,
    genre              TEXT,
    language           TEXT    NOT NULL DEFAULT 'Hindi',
    showtimes          TEXT,
    ticket_price_range TEXT,
    duration_mins      INTEGER,
    critic_rating      REAL
);

CREATE TABLE IF NOT EXISTS active_itineraries (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           TEXT    NOT NULL,
    city_id           INTEGER NOT NULL REFERENCES cities(id),
    destination_poi_id INTEGER REFERENCES points_of_interest(id),
    meeting_time      TEXT,
    departure_time    TEXT,
    origin_area       TEXT,
    status            TEXT    NOT NULL DEFAULT 'planned'
);

CREATE TABLE IF NOT EXISTS transit_routes (
    from_station_id INTEGER NOT NULL REFERENCES transit_stations(id),
    to_station_id   INTEGER NOT NULL REFERENCES transit_stations(id),
    travel_time_mins INTEGER NOT NULL,
    interchanges    TEXT,
    PRIMARY KEY (from_station_id, to_station_id)
);

CREATE TABLE IF NOT EXISTS metro_fares (
    from_station_id INTEGER NOT NULL REFERENCES transit_stations(id),
    to_station_id   INTEGER NOT NULL REFERENCES transit_stations(id),
    fare_rupees     INTEGER NOT NULL,
    PRIMARY KEY (from_station_id, to_station_id)
);

CREATE TABLE IF NOT EXISTS shared_expenses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_id        INTEGER NOT NULL REFERENCES active_itineraries(id),
    payer_user_id       TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    total_amount_rupees REAL    NOT NULL,
    split_type          TEXT    NOT NULL DEFAULT 'equal',
    split_data          TEXT
);

CREATE TABLE IF NOT EXISTS user_budgets (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              TEXT    NOT NULL,
    monthly_limit_rupees REAL    NOT NULL DEFAULT 5000.0,
    active_spent_rupees  REAL    NOT NULL DEFAULT 0.0,
    month_year           TEXT    NOT NULL,
    UNIQUE(user_id, month_year)
);

CREATE TABLE IF NOT EXISTS local_document_index (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name  TEXT    NOT NULL,
    file_path  TEXT    NOT NULL UNIQUE,
    checksum   TEXT,
    indexed_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS traffic_rules (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id          INTEGER NOT NULL REFERENCES cities(id),
    route_name       TEXT    NOT NULL,
    peak_start       TEXT    NOT NULL,
    peak_end         TEXT    NOT NULL,
    congestion_factor REAL   NOT NULL DEFAULT 1.0,
    avoidance_note   TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id         INTEGER NOT NULL REFERENCES cities(id),
    name            TEXT    NOT NULL,
    venue_id        INTEGER REFERENCES points_of_interest(id),
    neighborhood_id INTEGER REFERENCES neighborhoods(id),
    date            TEXT,
    time            TEXT,
    type            TEXT,
    price           TEXT
);

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id                   INTEGER NOT NULL REFERENCES cities(id),
    hour_of_day               INTEGER NOT NULL,
    condition                 TEXT    NOT NULL,
    temp_celsius              REAL    NOT NULL,
    uv_index                  INTEGER NOT NULL DEFAULT 0,
    humidity                  INTEGER NOT NULL DEFAULT 60,
    precipitation_probability INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS skill_usage_log (
    skill_name     TEXT    NOT NULL,
    invoked_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    success        INTEGER NOT NULL DEFAULT 1,
    tool_call_count INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memory_metadata (
    chroma_id    TEXT    PRIMARY KEY,
    category     TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    last_accessed TEXT,
    access_count INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL DEFAULT 'active'
);
"""

# ── City module registry ────────────────────────────────────────────────────────

CITY_MODULES = [
    "data.cities.bengaluru",
    "data.cities.mumbai",
    "data.cities.delhi",
    "data.cities.chennai",
    "data.cities.hyderabad",
    "data.cities.kolkata",
    "data.cities.pune",
]


# ── Core helpers ───────────────────────────────────────────────────────────────

def get_db_path() -> Path:
    """Return resolved path to the SQLite database."""
    raw = os.getenv("SQLITE_DB_PATH", "./data/oota.db")
    return Path(raw).resolve()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-keys enabled."""
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Execute all CREATE TABLE IF NOT EXISTS statements."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    log.info("Schema created / verified.")


def seed_all_cities(conn: sqlite3.Connection) -> None:
    """Import each city module and call its seed_city(conn) function."""
    for module_name in CITY_MODULES:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "seed_city"):
                module.seed_city(conn)
                log.info("Seeded city from %s", module_name)
            else:
                log.warning("Module %s has no seed_city() function", module_name)
        except ImportError as exc:
            log.warning("Could not import %s: %s", module_name, exc)
        except Exception as exc:  # noqa: BLE001
            log.error("Error seeding %s: %s", module_name, exc)


def run_seed(force: bool = False) -> None:
    """
    Create schema and seed all cities.

    Args:
        force: If True, drop and recreate all tables before seeding.
    """
    db_path = get_db_path()
    log.info("Database path: %s", db_path)

    with get_connection(db_path) as conn:
        if force:
            log.warning("Force mode: dropping all tables...")
            # Drop tables in reverse dependency order
            tables = [
                "memory_metadata", "skill_usage_log", "weather_forecasts",
                "events", "traffic_rules", "local_document_index",
                "user_budgets", "shared_expenses", "metro_fares",
                "transit_routes", "active_itineraries", "movies",
                "mall_shops", "points_of_interest", "transit_stations",
                "neighborhoods", "cities",
            ]
            for tbl in tables:
                conn.execute(f"DROP TABLE IF EXISTS {tbl}")
            conn.commit()

        create_schema(conn)
        seed_all_cities(conn)
        log.info("Database seeding complete.")


if __name__ == "__main__":
    import sys
    # Add root folder to python path
    root_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root_dir))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
    force_flag = "--force" in sys.argv
    run_seed(force=force_flag)
    print("\n[OK] Oota database seeded successfully.")
