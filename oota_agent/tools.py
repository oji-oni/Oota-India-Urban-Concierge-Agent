"""
Custom tools for Oota Concierge Agent.
"""
from __future__ import annotations

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import chromadb
from cryptography.fernet import Fernet

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/oota.db")).resolve()
CHROMA_DIR = Path(os.getenv("CHROMA_DATA_DIR", "./data/chroma")).resolve()

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def get_chroma_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))

# ── 1. Save Preference ────────────────────────────────────────────────────────
def save_preference(key: str, value: str, city: str = "") -> str:
    """
    Save user preference to local Chroma vector database for future semantic recall.
    
    Args:
        key: The key or category of the preference (e.g. 'diet', 'speed')
        value: The detailed preference text (e.g. 'prefers pure veg, avoids mushrooms')
        city: Optional city filter to associate with the preference
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection("user_preferences")
    
    doc_id = f"pref_{hashlib.md5(f'{key}:{value}'.encode()).hexdigest()}"
    metadata = {"key": key, "city": city, "created_at": datetime.now().isoformat()}
    
    collection.upsert(
        documents=[value],
        metadatas=[metadata],
        ids=[doc_id]
    )
    
    # Track in SQLite memory_metadata
    conn = get_db_conn()
    try:
        conn.execute(
            """
            INSERT INTO memory_metadata (chroma_id, category, last_accessed, access_count, status)
            VALUES (?, ?, ?, 1, 'active')
            ON CONFLICT(chroma_id) DO UPDATE SET
                last_accessed = excluded.last_accessed,
                access_count = access_count + 1
            """,
            (doc_id, key, datetime.now().isoformat())
        )
        conn.commit()
    finally:
        conn.close()
        
    return json.dumps({"status": "saved", "chroma_id": doc_id, "category": key})

# ── 2. Recall Preferences ─────────────────────────────────────────────────────
def recall_preferences(query: str) -> str:
    """
    Perform a semantic search over saved user preferences.
    
    Args:
        query: Search query (e.g. 'what food does Priya like?')
    """
    client = get_chroma_client()
    collection = client.get_or_create_collection("user_preferences")
    
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    
    parsed = []
    if results and "documents" in results and results["documents"]:
        for doc, meta, doc_id in zip(results["documents"][0], results["metadatas"][0], results["ids"][0]):
            parsed.append({
                "id": doc_id,
                "preference": doc,
                "metadata": meta
            })
            # Update last_accessed in SQLite
            conn = get_db_conn()
            try:
                conn.execute(
                    "UPDATE memory_metadata SET last_accessed = ?, access_count = access_count + 1 WHERE chroma_id = ?",
                    (datetime.now().isoformat(), doc_id)
                )
                conn.commit()
            finally:
                conn.close()
                
    return json.dumps(parsed)

# ── 3. Calculate Departure Time ───────────────────────────────────────────────
def calculate_departure_time(meeting_time_str: str, transit_mins: int, entry_wait_mins: int = 0) -> str:
    """
    Calculate the exact time the user needs to leave their location, factoring in transit, entry wait, and a 15-minute buffer.
    
    Args:
        meeting_time_str: Target time in format 'HH:MM' (24-hour clock)
        transit_mins: Duration of travel/commute in minutes
        entry_wait_mins: Time spent entering venue or darshana wait in minutes
    """
    try:
        t = datetime.strptime(meeting_time_str, "%H:%M")
    except ValueError:
        # Try full ISO parser
        try:
            t = datetime.fromisoformat(meeting_time_str)
        except ValueError:
            return json.dumps({"error": "Invalid time format. Please use HH:MM."})
            
    total_subtract = transit_mins + entry_wait_mins + 15  # 15 min buffer
    departure_t = t - timedelta(minutes=total_subtract)
    
    return json.dumps({
        "target_meeting_time": meeting_time_str,
        "transit_duration_mins": transit_mins,
        "venue_entry_wait_mins": entry_wait_mins,
        "buffer_mins": 15,
        "total_overhead_mins": total_subtract,
        "departure_time": departure_t.strftime("%H:%M"),
        "notes": f"Please leave by {departure_t.strftime('%I:%M %p')} to account for {transit_mins}m travel, {entry_wait_mins}m wait, and a 15m safety buffer."
    })

# ── 4. Check Weather Recommendation ──────────────────────────────────────────
def check_weather_recommendation(city: str, area: str = "", time_of_day: str = "day") -> str:
    """
    Check local weather forecast and return recommended items (umbrella, sunscreen, clothing style).
    
    Args:
        city: City slug (e.g. 'bengaluru')
        area: Optional neighborhood name
        time_of_day: e.g. 'morning', 'afternoon', 'evening'
    """
    # Fetch from SQLite weather_forecasts
    conn = get_db_conn()
    try:
        row = conn.execute(
            """
            SELECT wf.* FROM weather_forecasts wf
            JOIN cities c ON wf.city_id = c.id
            WHERE c.slug = ?
            ORDER BY ABS(wf.hour_of_day - 12) LIMIT 1
            """,
            (city.lower(),)
        ).fetchone()
    finally:
        conn.close()
        
        if not row:
            return json.dumps({
                "city": city,
                "condition": "Pleasant",
                "temp_celsius": 24.0,
                "recommendations": "Wear comfortable casuals. Carry sunglasses."
            })
            
        temp = row["temp_celsius"]
        condition = row["condition"]
        uv = row["uv_index"]
        precip = row["precipitation_probability"]
        
        recs = []
        if precip > 50:
            recs.append("☔ Carry an umbrella/raincoat. High probability of rain.")
        if uv > 6:
            recs.append("☀️ High UV Index. Apply sunscreen and wear sunglasses.")
        if temp > 32:
            recs.append("👕 Wear light, breathable cotton clothing.")
        elif temp < 20:
            recs.append("🧥 Keep a light jacket or sweater handy.")
        else:
            recs.append("👟 Standard comfortable walking attire.")
            
        return json.dumps({
            "city": city,
            "condition": condition,
            "temp_celsius": temp,
            "precipitation_probability": precip,
            "uv_index": uv,
            "recommendations": " ".join(recs)
        })

# ── 5. Execute Hybrid Routing ─────────────────────────────────────────────────
def execute_hybrid_routing(query_type: str, message: str) -> str:
    """
    Decide whether to route queries to a local Ollama instance (simple ledger/status checks) or Gemini (complex planning).
    
    Args:
        query_type: Categorization of query ('status', 'split', 'planning')
        message: Raw user query
    """
    simple_keywords = ["status", "split", "ledger", "balance", "export", "backup"]
    is_simple = any(k in message.lower() for k in simple_keywords) or query_type in ["status", "split"]
    
    if is_simple:
        return json.dumps({
            "route": "ollama",
            "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "model": "llama3.2",
            "reason": "Simple status, backup, or split ledger transaction requested. Routed to local LLM to conserve cloud API tokens."
        })
    return json.dumps({
        "route": "gemini",
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "reason": "Complex spatial, midpoint, or multi-stage itinerary query. Routed to cloud Gemini for optimal planning quality."
    })

# ── 6. Manage Vault Encryption ────────────────────────────────────────────────
def manage_vault_encryption(action: str = "status") -> str:
    """
    Secure the local SQLite database at rest using Fernet encryption.
    
    Args:
        action: Actions: 'status' (check encryption state), 'encrypt' (secure DB), 'decrypt' (unsecure DB for local use)
    """
    key_file = Path(".vault.key")
    db_file = Path(DB_PATH)
    enc_file = Path(str(DB_PATH) + ".enc")
    
    if action == "status":
        return json.dumps({
            "vault_active": enc_file.exists(),
            "local_db_raw_exists": db_file.exists(),
            "key_present": key_file.exists()
        })
        
    if action == "encrypt":
        if not db_file.exists():
            return json.dumps({"error": "No raw SQLite DB file found to encrypt."})
            
        if not key_file.exists():
            key = Fernet.generate_key()
            key_file.write_bytes(key)
        else:
            key = key_file.read_bytes()
            
        f = Fernet(key)
        raw_data = db_file.read_bytes()
        enc_data = f.encrypt(raw_data)
        enc_file.write_bytes(enc_data)
        db_file.unlink() # Delete unencrypted
        return json.dumps({"status": "database encrypted", "vault_active": True})
        
    if action == "decrypt":
        if not enc_file.exists():
            return json.dumps({"status": "no encrypted database found", "vault_active": False})
            
        if not key_file.exists():
            return json.dumps({"error": "Encryption key missing (.vault.key). Decryption failed."})
            
        key = key_file.read_bytes()
        f = Fernet(key)
        enc_data = enc_file.read_bytes()
        raw_data = f.decrypt(enc_data)
        db_file.write_bytes(raw_data)
        enc_file.unlink() # Delete encrypted
        return json.dumps({"status": "database decrypted", "vault_active": False})
        
    return json.dumps({"error": "Invalid action. Use 'status', 'encrypt', or 'decrypt'."})

# ── 7. Run Document Indexer (RAG) ─────────────────────────────────────────────
def run_document_indexer(documents_dir: str = "./data/documents") -> str:
    """
    Index local PDF and text/markdown files into the Chroma vector store for RAG custom itineraries.
    
    Args:
        documents_dir: Directory containing documents
    """
    doc_path = Path(documents_dir)
    if not doc_path.exists():
        doc_path.mkdir(parents=True, exist_ok=True)
        return json.dumps({"status": "created_directory", "files_indexed": 0, "message": "Placed stubs. Add custom text/markdown guides."})
        
    client = get_chroma_client()
    collection = client.get_or_create_collection("local_documents")
    
    files_indexed = 0
    # Walk and read
    for file in doc_path.glob("**/*"):
        if file.suffix in [".txt", ".md"] and file.is_file():
            content = file.read_text(encoding="utf-8", errors="ignore")
            # Chunking by 800 chars (~150 words)
            chunks = [content[i:i+800] for i in range(0, len(content), 600)]
            
            for idx, chunk in enumerate(chunks):
                chunk_id = f"doc_{hashlib.md5(f'{file.name}:{idx}'.encode()).hexdigest()}"
                collection.upsert(
                    documents=[chunk],
                    metadatas=[{"file_name": file.name, "chunk": idx, "indexed_at": datetime.now().isoformat()}],
                    ids=[chunk_id]
                )
                
            # Log in SQLite local_document_index
            file_checksum = hashlib.md5(content.encode()).hexdigest()
            conn = get_db_conn()
            try:
                conn.execute(
                    """
                    INSERT INTO local_document_index (file_name, file_path, checksum, indexed_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        checksum = excluded.checksum,
                        indexed_at = excluded.indexed_at
                    """,
                    (file.name, str(file.resolve()), file_checksum, datetime.now().isoformat())
                )
                conn.commit()
            finally:
                conn.close()
            files_indexed += 1
            
    return json.dumps({"status": "indexing_completed", "files_indexed": files_indexed})

# ── 8. Generate Dating Plan ───────────────────────────────────────────────────
def generate_dating_plan(city: str, budget: str = "medium", vibe: str = "romantic", time_of_day: str = "evening") -> str:
    """
    Suggest cozy romantic dates combining twilight/sunset views, couple seating, and premium dining.
    
    Args:
        city: City slug (e.g. 'bengaluru')
        budget: 'low', 'medium', or 'high'
        vibe: 'romantic', 'cozy', 'active'
        time_of_day: 'afternoon', 'evening'
    """
    plans = {
        "bengaluru": [
            {"phase": "1. Sunset Walk", "venue": "Lalbagh Botanical Garden / Cubbon Park", "details": "Stroll amidst historic canopy trees before dusk."},
            {"phase": "2. Coffee & Vibe", "venue": "German Bakery / Toit Cafe", "details": "Cozy corner table with nice lighting and ambient acoustics."},
            {"phase": "3. Dinner Date", "venue": "Karavalli (Taj Residency)", "details": "Outdoor courtyard, candle-lit dining under the stars. Excellent coastal seafood."}
        ],
        "mumbai": [
            {"phase": "1. Marine Drive Sunset", "venue": "Marine Drive Promenade", "details": "Walk along the Queen's Necklace watching the sunset over the Arabian Sea."},
            {"phase": "2. Dinner at Leopold", "venue": "Leopold Cafe (Colaba)", "details": "Vibrant, iconic heritage atmosphere, shared bites and drafts."}
        ]
    }
    
    city_plan = plans.get(city.lower(), [
        {"phase": "1. Walk & Chat", "venue": "Local Scenic Park", "details": "Relaxing walk to set the mood."},
        {"phase": "2. Dining", "venue": "Top-rated romantic restaurant", "details": "Fine-dine cuisine with nice ambiance."}
    ])
    
    return json.dumps({
        "city": city,
        "budget": budget,
        "vibe": vibe,
        "time_of_day": time_of_day,
        "itinerary": city_plan
    })

# ── 9. Collect Post-Event Feedback ────────────────────────────────────────────
def collect_post_event_feedback(itinerary_id: int, rating: int, notes: str = "") -> str:
    """
    Request feedback on a completed outing and store qualitative reviews in Chroma memory for future adjustments.
    
    Args:
        itinerary_id: ID of the active itinerary
        rating: Rating from 1 to 5 stars
        notes: Text notes/comments from the user
    """
    conn = get_db_conn()
    try:
        # Fetch itinerary
        itinerary = conn.execute(
            """
            SELECT a.*, p.name as destination_name
            FROM active_itineraries a
            JOIN points_of_interest p ON a.destination_poi_id = p.id
            WHERE a.id = ?
            """,
            (itinerary_id,)
        ).fetchone()
        
        if not itinerary:
            return json.dumps({"error": "Itinerary not found"})
            
        # Update status in DB
        conn.execute("UPDATE active_itineraries SET status = 'completed' WHERE id = ?", (itinerary_id,))
        conn.commit()
    finally:
        conn.close()
        
    # Save feedback into Chroma
    client = get_chroma_client()
    collection = client.get_or_create_collection("feedback_logs")
    
    doc_id = f"fb_{itinerary_id}"
    feedback_text = f"Outing to {itinerary['destination_name']}. Rating: {rating}/5 stars. Comments: {notes}"
    
    collection.upsert(
        documents=[feedback_text],
        metadatas=[{
            "itinerary_id": itinerary_id,
            "rating": rating,
            "venue": itinerary['destination_name'],
            "timestamp": datetime.now().isoformat()
        }],
        ids=[doc_id]
    )
    
    return json.dumps({"status": "feedback_saved", "itinerary_id": itinerary_id, "rating": rating})

# ── 10. Execute Travel Workflow ───────────────────────────────────────────────
async def execute_travel_workflow(city: str, areas: list[str], tool_context: Any) -> str:
    """
    Execute a structured ADK Workflow graph to calculate geographic midpoints and check rain/budget safety constraints.
    
    Args:
        city: The city slug (e.g. 'bengaluru')
        areas: List of neighborhood area names to include in calculations
        tool_context: Injected ADK ToolContext instance
    """
    from oota_agent.workflow import travel_workflow
    node_input = {"city": city, "areas": areas}
    
    # Run the workflow through the async generator
    async for _ in travel_workflow.run(ctx=tool_context, node_input=node_input):
        pass
        
    return json.dumps(tool_context.output)

