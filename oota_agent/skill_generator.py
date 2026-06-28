"""
Oota Skill Generator Sub-agent.
Reflects on successful complex tasks and crystallizes them into reusable SKILL.md guides.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path("./.agents/skills/auto")

def generate_and_save_skill(task_description: str, tools_used: list[str], steps_log: str) -> dict:
    """
    Spawns reflection process to build a new skill procedure when a complex task is completed.
    """
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create safe slug
    safe_slug = "".join([c if c.isalnum() else "-" for c in task_description.lower()[:30]]).strip("-")
    if not safe_slug:
        safe_slug = "custom-task"
        
    skill_file = SKILLS_DIR / f"{safe_slug}.md"
    
    # Simple templates mapping for demo/crystallization
    yaml_frontmatter = f"""---
name: {safe_slug}
description: >
  Auto-crystallized procedure to solve: {task_description}
trigger_patterns:
  - "{safe_slug.replace('-', ' ')}"
  - "{task_description[:20]}"
created_at: "{datetime.now().isoformat()}"
invocation_count: 0
last_invoked: null
source: auto-generated
---

## Crystallized Procedure
1. Receive request matching trigger: "{task_description}"
2. Sequence of tools executed: {', '.join(tools_used)}
3. Detailed execution log reference: {steps_log[:200]}...
4. Verify constraint filters locally without cloud data leakage.

## Privacy Mandate
- Keep location & coordinate variables localized.
- Prevent caching attendee data to external networks.
"""
    skill_file.write_text(yaml_frontmatter, encoding="utf-8")
    
    # Log to SQLite
    db_path = Path(os.getenv("SQLITE_DB_PATH", "./data/oota.db")).resolve()
    try:
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO skill_usage_log (skill_name, success, tool_call_count) VALUES (?, 1, ?)",
                (safe_slug, len(tools_used))
            )
            conn.commit()
    except Exception:
        pass
        
    return {"status": "skill_created", "skill_file": str(skill_file), "name": safe_slug}
