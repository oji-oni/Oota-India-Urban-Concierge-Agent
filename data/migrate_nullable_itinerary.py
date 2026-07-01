"""
Migrate shared_expenses.itinerary_id to allow NULL
so expenses can be logged without a pre-existing itinerary.
"""
import sqlite3, pathlib

db = pathlib.Path("data/oota.db")
conn = sqlite3.connect(str(db))
conn.execute("PRAGMA foreign_keys = OFF")
conn.execute("BEGIN")

# Re-create the table without the NOT NULL constraint on itinerary_id
conn.execute("""
CREATE TABLE IF NOT EXISTS shared_expenses_new (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    itinerary_id        INTEGER REFERENCES active_itineraries(id),
    payer_user_id       TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    total_amount_rupees REAL    NOT NULL,
    split_type          TEXT    NOT NULL DEFAULT 'equal',
    split_data          TEXT
)
""")

# Copy existing rows (should be 0 right now, but safe to do anyway)
conn.execute("""
INSERT INTO shared_expenses_new
SELECT id, itinerary_id, payer_user_id, description, total_amount_rupees, split_type, split_data
FROM shared_expenses
""")

conn.execute("DROP TABLE shared_expenses")
conn.execute("ALTER TABLE shared_expenses_new RENAME TO shared_expenses")
conn.execute("COMMIT")
conn.execute("PRAGMA foreign_keys = ON")
conn.close()
print("Migration complete: itinerary_id is now nullable in shared_expenses")
