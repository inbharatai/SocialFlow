"""
SocialFlow Asset Inventory — Content & Media Tracking System

Tracks all generated assets (videos, images, text) across the pipeline.
Think of this as SocialFlow's content library / DAM (Digital Asset Manager).

Every generated piece — whether from HeyGen, AI text, carousel, or manual upload —
gets registered here with metadata for reuse, routing, and auditing.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


DATABASE_PATH = "socialflow.db"


def init_asset_tables():
    """Create asset inventory tables if they don't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    # Core asset inventory
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT UNIQUE NOT NULL,
        asset_type TEXT NOT NULL,
        source TEXT NOT NULL,
        title TEXT,
        description TEXT,
        file_path TEXT,
        file_url TEXT,
        file_size INTEGER,
        duration_seconds INTEGER,
        aspect_ratio TEXT,
        campaign TEXT,
        topic TEXT,
        tags TEXT,
        metadata TEXT,
        state TEXT DEFAULT 'available',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Content queue — platform-specific distribution items
    c.execute('''CREATE TABLE IF NOT EXISTS content_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        queue_id TEXT UNIQUE NOT NULL,
        asset_id TEXT,
        platform TEXT NOT NULL,
        content_type TEXT NOT NULL,
        caption TEXT,
        hashtags TEXT,
        copy_text TEXT,
        media_paths TEXT,
        scheduled_time DATETIME,
        state TEXT DEFAULT 'pending',
        campaign TEXT,
        approval_level TEXT,
        source_job_id TEXT,
        error TEXT,
        published_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
    )''')

    # Campaign grouping
    c.execute('''CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        start_date DATE,
        end_date DATE,
        state TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    conn.commit()
    conn.close()


# ─── ASSET CRUD ───────────────────────────────────────────────

def register_asset(
    asset_type: str,
    source: str,
    title: str = "",
    description: str = "",
    file_path: str = None,
    file_url: str = None,
    file_size: int = None,
    duration_seconds: int = None,
    aspect_ratio: str = None,
    campaign: str = "",
    topic: str = "",
    tags: List[str] = None,
    metadata: dict = None
) -> dict:
    """Register a new asset in the inventory"""
    asset_id = f"asset-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{os.urandom(3).hex()}"

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''INSERT INTO assets
        (asset_id, asset_type, source, title, description, file_path, file_url,
         file_size, duration_seconds, aspect_ratio, campaign, topic, tags, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            asset_id, asset_type, source, title, description,
            file_path, file_url, file_size, duration_seconds, aspect_ratio,
            campaign, topic,
            json.dumps(tags or []),
            json.dumps(metadata or {})
        )
    )

    conn.commit()
    conn.close()

    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "source": source,
        "title": title
    }


def get_asset(asset_id: str) -> Optional[dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM assets WHERE asset_id = ?", (asset_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def list_assets(
    asset_type: str = None,
    source: str = None,
    campaign: str = None,
    limit: int = 50
) -> List[dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM assets WHERE 1=1"
    params = []

    if asset_type:
        query += " AND asset_type = ?"
        params.append(asset_type)
    if source:
        query += " AND source = ?"
        params.append(source)
    if campaign:
        query += " AND campaign = ?"
        params.append(campaign)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ─── CONTENT QUEUE CRUD ──────────────────────────────────────

def queue_content(
    platform: str,
    content_type: str,
    caption: str = "",
    hashtags: str = "",
    copy_text: str = "",
    media_paths: List[str] = None,
    asset_id: str = None,
    scheduled_time: str = None,
    campaign: str = "",
    approval_level: str = None,
    source_job_id: str = None
) -> dict:
    """Add content to the distribution queue"""
    queue_id = f"q-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{platform[:3]}-{os.urandom(2).hex()}"

    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    c.execute('''INSERT INTO content_queue
        (queue_id, asset_id, platform, content_type, caption, hashtags, copy_text,
         media_paths, scheduled_time, campaign, approval_level, source_job_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            queue_id, asset_id, platform, content_type, caption, hashtags, copy_text,
            json.dumps(media_paths or []),
            scheduled_time, campaign, approval_level, source_job_id
        )
    )

    conn.commit()
    conn.close()

    return {"queue_id": queue_id, "platform": platform, "state": "pending"}


def list_queue(
    platform: str = None,
    state: str = None,
    campaign: str = None,
    limit: int = 50
) -> List[dict]:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM content_queue WHERE 1=1"
    params = []

    if platform:
        query += " AND platform = ?"
        params.append(platform)
    if state:
        query += " AND state = ?"
        params.append(state)
    if campaign:
        query += " AND campaign = ?"
        params.append(campaign)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_queue_state(queue_id: str, new_state: str, error: str = None) -> bool:
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()

    updates = ["state = ?", "updated_at = ?"]
    params = [new_state, datetime.now().isoformat()]

    if error:
        updates.append("error = ?")
        params.append(error)

    if new_state == "published":
        updates.append("published_at = ?")
        params.append(datetime.now().isoformat())

    params.append(queue_id)
    c.execute(f"UPDATE content_queue SET {', '.join(updates)} WHERE queue_id = ?", params)

    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


# Initialize tables on import
init_asset_tables()
