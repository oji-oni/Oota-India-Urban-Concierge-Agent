"""
Oota Memory Curator Sub-agent.
Performs periodic audits (Active -> Stale -> Archived) on SQLite preferences and Chroma vector indexes.
"""
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import chromadb

DB_PATH = Path(os.getenv("SQLITE_DB_PATH", "./data/oota.db")).resolve()
CHROMA_DIR = Path(os.getenv("CHROMA_DATA_DIR", "./data/chroma")).resolve()
SKILLS_DIR = Path("./.agents/skills/auto")

def get_chroma_client():
    return chromadb.PersistentClient(path=str(CHROMA_DIR))

def run_curator_cleanup() -> dict:
    """
    Scans memory metadata and archives stale records without deleting them.
    Active -> Stale (30 days unused) -> Archived (90 days unused).
    """
    now = datetime.now()
    stale_threshold = now - timedelta(days=30)
    archive_threshold = now - timedelta(days=90)
    
    stale_count = 0
    archived_count = 0
    skills_archived = 0
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # 1. Fetch memory entries
        rows = cur.execute("SELECT * FROM memory_metadata").fetchall()
        chroma_client = get_chroma_client()
        pref_collection = chroma_client.get_collection("user_preferences")
        
        # Get or create archive collection
        archive_collection = chroma_client.get_or_create_collection("user_preferences_archive")
        
        for row in rows:
            chroma_id = row["chroma_id"]
            last_acc_str = row["last_accessed"]
            status = row["status"]
            
            if not last_acc_str:
                last_acc = now
            else:
                try:
                    last_acc = datetime.fromisoformat(last_acc_str)
                except ValueError:
                    last_acc = now
                    
            # Check thresholds
            if last_acc < archive_threshold and status != "archived":
                # Move from primary to archive collection in Chroma
                try:
                    doc = pref_collection.get(ids=[chroma_id])
                    if doc and doc["documents"]:
                        archive_collection.upsert(
                            ids=doc["ids"],
                            documents=doc["documents"],
                            metadatas=doc["metadatas"]
                        )
                        pref_collection.delete(ids=[chroma_id])
                except Exception:
                    pass
                    
                cur.execute("UPDATE memory_metadata SET status = 'archived' WHERE chroma_id = ?", (chroma_id,))
                archived_count += 1
            elif last_acc < stale_threshold and status == "active":
                cur.execute("UPDATE memory_metadata SET status = 'stale' WHERE chroma_id = ?", (chroma_id,))
                stale_count += 1
                
        # 2. Curate auto-generated skills
        if SKILLS_DIR.exists():
            archive_skills_dir = Path("./.agents/skills/.archive")
            archive_skills_dir.mkdir(parents=True, exist_ok=True)
            
            for file in SKILLS_DIR.glob("*.md"):
                # If modification time > 30 days ago, move to archive
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime < stale_threshold:
                    dest = archive_skills_dir / file.name
                    file.rename(dest)
                    skills_archived += 1
                    
        conn.commit()
        conn.close()
        
    except Exception as e:
        return {"error": str(e)}
        
    return {
        "status": "success",
        "stale_marked": stale_count,
        "archived_marked": archived_count,
        "skills_archived": skills_archived
    }
