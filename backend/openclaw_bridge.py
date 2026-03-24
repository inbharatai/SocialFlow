"""
OpenClaw Bridge — API endpoints for OpenClaw to push approved content to SocialFlow
This is the connector between OpenClaw's content pipeline and SocialFlow's posting engine.

Endpoints:
  POST /api/openclaw/publish    — Push approved content to a platform
  POST /api/openclaw/batch      — Push multiple items at once
  GET  /api/openclaw/status      — Check platform connection status
  GET  /api/openclaw/history     — Recent publish history
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/openclaw", tags=["OpenClaw Bridge"])


class OpenClawPublishRequest(BaseModel):
    """Content from OpenClaw approval pipeline"""
    platform: str           # linkedin, x, facebook, instagram, discord, reddit, medium, substack, heygen, beehiiv, mailerlite, brevo
    content: str            # The post/article text
    content_type: str       # product-update, ai-news, social-post, newsletter, video-brief, etc.
    title: Optional[str] = None         # For Medium, Substack, Reddit
    subtitle: Optional[str] = None      # For Substack
    subreddit: Optional[str] = None     # For Reddit
    image_paths: Optional[List[str]] = None
    approval_level: Optional[str] = None  # L1, L2, L3 — for audit trail
    source_file: Optional[str] = None     # Original file path in OpenClaw
    dry_run: bool = False                 # If true, don't actually post


class BatchPublishRequest(BaseModel):
    items: List[OpenClawPublishRequest]


# History storage
BRIDGE_LOG_PATH = Path("openclaw_bridge_log.json")


def log_bridge_event(event: dict):
    """Append to bridge log file"""
    events = []
    if BRIDGE_LOG_PATH.exists():
        try:
            events = json.loads(BRIDGE_LOG_PATH.read_text())
        except Exception:
            events = []
    events.append(event)
    # Keep last 500 events
    events = events[-500:]
    BRIDGE_LOG_PATH.write_text(json.dumps(events, indent=2))


@router.post("/publish")
async def openclaw_publish(request: OpenClawPublishRequest):
    """
    Receive approved content from OpenClaw and publish to the specified platform.
    This is the main bridge endpoint.
    """
    from automation_extended import get_automation_extended

    timestamp = datetime.now().isoformat()
    platform = request.platform.lower()

    # Validate platform
    supported = ["linkedin", "x", "twitter", "facebook", "instagram", "discord",
                 "reddit", "medium", "substack", "heygen", "beehiiv", "mailerlite", "brevo"]
    if platform not in supported:
        raise HTTPException(status_code=400,
                          detail=f"Unsupported platform: {platform}. Supported: {supported}")

    # Validate content
    if not request.content or len(request.content.strip()) < 5:
        raise HTTPException(status_code=400, detail="Content is too short or empty")

    # Dry run — just validate and return
    if request.dry_run:
        log_bridge_event({
            "timestamp": timestamp,
            "platform": platform,
            "content_type": request.content_type,
            "action": "dry_run",
            "status": "validated",
            "source_file": request.source_file
        })
        return {
            "success": True,
            "action": "dry_run",
            "platform": platform,
            "message": f"Validated for {platform}. Would publish in live mode.",
            "content_preview": request.content[:200]
        }

    # Get Discord webhook from config if needed
    kwargs = {}
    if platform == "discord":
        config_path = Path("discord_webhook.json")
        if config_path.exists():
            discord_config = json.loads(config_path.read_text())
            kwargs["webhook_url"] = discord_config.get("webhook_url", "")
        else:
            raise HTTPException(status_code=400,
                              detail="Discord webhook not configured. Create discord_webhook.json")

    if platform == "substack":
        config_path = Path("substack_config.json")
        if config_path.exists():
            sub_config = json.loads(config_path.read_text())
            kwargs["publication_url"] = sub_config.get("publication_url", "")

    try:
        auto = get_automation_extended(platform, headless=True, **kwargs)

        # Build post kwargs based on platform — only pass params each platform accepts
        post_kwargs = {"content": request.content}
        if request.image_paths:
            post_kwargs["image_paths"] = request.image_paths

        # title only for platforms that accept it
        title_platforms = ("medium", "substack", "reddit", "beehiiv", "mailerlite", "brevo")
        if request.title and platform in title_platforms:
            post_kwargs["title"] = request.title
        if request.subtitle and platform == "substack":
            post_kwargs["subtitle"] = request.subtitle
        if request.subreddit and platform == "reddit":
            post_kwargs["subreddit"] = request.subreddit

        # For email platforms, add subject
        if platform in ("beehiiv", "mailerlite", "brevo") and request.title:
            post_kwargs["subject"] = request.title

        result = await auto.post(**post_kwargs)

        if hasattr(auto, 'close'):
            await auto.close()

        # Log the event
        log_bridge_event({
            "timestamp": timestamp,
            "platform": platform,
            "content_type": request.content_type,
            "approval_level": request.approval_level,
            "action": "publish",
            "status": "success" if result.get("success") else "failed",
            "message": result.get("message", ""),
            "source_file": request.source_file
        })

        return {
            "success": result.get("success", False),
            "platform": platform,
            "message": result.get("message", ""),
            "timestamp": timestamp,
            "source_file": request.source_file
        }

    except Exception as e:
        log_bridge_event({
            "timestamp": timestamp,
            "platform": platform,
            "content_type": request.content_type,
            "action": "publish",
            "status": "error",
            "message": str(e),
            "source_file": request.source_file
        })
        return {
            "success": False,
            "platform": platform,
            "message": f"Error: {str(e)}",
            "timestamp": timestamp
        }


@router.post("/batch")
async def openclaw_batch_publish(request: BatchPublishRequest):
    """Publish multiple items from OpenClaw in sequence"""
    results = []
    for item in request.items:
        result = await openclaw_publish(item)
        results.append(result)
    return {
        "total": len(results),
        "succeeded": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
        "results": results
    }


@router.get("/status")
async def openclaw_platform_status():
    """Check which platforms have saved sessions / are ready to post"""
    from automation_extended import get_automation_extended

    sessions_dir = Path("sessions")
    status = {}

    platforms = ["linkedin", "instagram", "x", "facebook", "reddit",
                 "medium", "substack", "heygen", "beehiiv", "mailerlite", "brevo"]

    for p in platforms:
        session_file = sessions_dir / f"{p}_session.json"
        has_session = session_file.exists()

        status[p] = {
            "has_session": has_session,
            "session_age": None,
            "ready": has_session
        }

        if has_session:
            try:
                session_data = json.loads(session_file.read_text())
                saved_at = session_data.get("saved_at", "")
                status[p]["session_age"] = saved_at
            except Exception:
                pass

    # Discord check
    webhook_config = Path("discord_webhook.json")
    status["discord"] = {
        "has_session": webhook_config.exists(),
        "ready": webhook_config.exists(),
        "type": "webhook"
    }

    return {"platforms": status}


@router.get("/history")
async def openclaw_publish_history(limit: int = 50):
    """Get recent publish history"""
    events = []
    if BRIDGE_LOG_PATH.exists():
        try:
            events = json.loads(BRIDGE_LOG_PATH.read_text())
        except Exception:
            events = []

    # Return most recent first
    return {"events": list(reversed(events[-limit:]))}
