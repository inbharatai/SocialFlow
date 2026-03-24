"""
SocialFlow Visual Content API — Generate visual briefs via API

Provides REST endpoints for generating carousel packs, quote cards,
thumbnails, and creative packs. Uses OpenClaw skill-runner + local LLM.
Results stored in asset inventory.
"""

import os
import subprocess
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from asset_inventory import register_asset, list_assets

router = APIRouter(prefix="/api/visual", tags=["Visual Content"])

PROJECT_ROOT = Path(__file__).parent.parent.parent
VISUAL_SCRIPT = PROJECT_ROOT / "openclaw-engine" / "scripts" / "visual-brief-generator.sh"
BRIEFS_DIR = PROJECT_ROOT / "data" / "image-briefs"


class VisualBriefRequest(BaseModel):
    content: str
    brief_type: str = "carousel"  # carousel, quote-card, thumbnail, story-frames, image-prompt, creative-pack
    platform: str = "instagram"
    campaign: str = ""
    topic: str = ""


class AutoGenerateRequest(BaseModel):
    """Trigger auto-generation from today's approved content"""
    pass


# ─── BRIEF TYPES CATALOG ─────────────────────────────────────

BRIEF_TYPES = {
    "carousel": {
        "name": "Carousel Pack",
        "description": "5-7 slide carousel with design system, per-slide text, and visual direction",
        "platforms": ["instagram", "linkedin"],
        "output_dir": "carousels",
        "skill": "carousel-builder"
    },
    "quote-card": {
        "name": "Quote Card Pack",
        "description": "3-5 shareable quote graphics with style variants",
        "platforms": ["instagram", "linkedin", "x"],
        "output_dir": "quote-cards",
        "skill": "quote-card-generator"
    },
    "thumbnail": {
        "name": "Thumbnail Pack",
        "description": "3 thumbnail options with headline formulas (A/B/C)",
        "platforms": ["youtube", "article", "linkedin"],
        "output_dir": "thumbnails",
        "skill": "thumbnail-generator"
    },
    "story-frames": {
        "name": "Story Frames",
        "description": "3-frame Instagram/LinkedIn story sequence",
        "platforms": ["instagram", "linkedin"],
        "output_dir": "story-frames",
        "skill": "image-brief-generator"
    },
    "image-prompt": {
        "name": "AI Image Prompts",
        "description": "3 detailed prompts for Midjourney/DALL-E/Flux",
        "platforms": ["all"],
        "output_dir": "image-prompts",
        "skill": "image-brief-generator"
    },
    "creative-pack": {
        "name": "Full Creative Pack",
        "description": "Complete visual kit: carousel + quote cards + thumbnails + stories + image prompts + captions",
        "platforms": ["all"],
        "output_dir": "creative-packs",
        "skill": "creative-pack-builder"
    }
}


@router.get("/types")
async def list_brief_types():
    """List all available visual brief types"""
    return {"types": BRIEF_TYPES}


@router.post("/generate")
async def generate_visual_brief(request: VisualBriefRequest):
    """Generate a visual content brief using local LLM"""

    if request.brief_type not in BRIEF_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown brief type: {request.brief_type}. Valid: {list(BRIEF_TYPES.keys())}"
        )

    if not request.content or len(request.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Content too short (min 10 chars)")

    brief_info = BRIEF_TYPES[request.brief_type]

    # Check if script exists
    if not VISUAL_SCRIPT.exists():
        raise HTTPException(status_code=500, detail="visual-brief-generator.sh not found")

    try:
        result = subprocess.run(
            [str(VISUAL_SCRIPT), request.content[:2000], request.brief_type, request.platform],
            capture_output=True, text=True, timeout=180,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0 and result.stdout.strip():
            output_path = result.stdout.strip()

            # Read the generated brief
            brief_content = ""
            if os.path.isfile(output_path):
                with open(output_path) as f:
                    brief_content = f.read()

                # Register in asset inventory
                asset = register_asset(
                    asset_type="visual-brief",
                    source=f"visual-{request.brief_type}",
                    title=f"{brief_info['name']}: {request.topic or request.content[:50]}",
                    description=brief_content[:500],
                    file_path=output_path,
                    campaign=request.campaign,
                    topic=request.topic,
                    tags=["visual", request.brief_type, request.platform],
                    metadata={
                        "brief_type": request.brief_type,
                        "platform": request.platform,
                        "skill": brief_info["skill"]
                    }
                )

                return {
                    "success": True,
                    "brief_type": request.brief_type,
                    "platform": request.platform,
                    "output_path": output_path,
                    "asset": asset,
                    "content_preview": brief_content[:500],
                    "generated_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": True,
                    "brief_type": request.brief_type,
                    "message": "Brief generated but output path not found",
                    "stdout": result.stdout[:500]
                }
        else:
            return {
                "success": False,
                "error": result.stderr[:500] if result.stderr else "Empty output",
                "brief_type": request.brief_type
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Generation timed out (180s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/auto-generate")
async def auto_generate_visuals():
    """Trigger auto-generation of visual briefs from today's approved content"""

    if not VISUAL_SCRIPT.exists():
        raise HTTPException(status_code=500, detail="visual-brief-generator.sh not found")

    try:
        result = subprocess.run(
            [str(VISUAL_SCRIPT), "--auto"],
            capture_output=True, text=True, timeout=600,
            cwd=str(PROJECT_ROOT)
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "errors": result.stderr[:500] if result.stderr else None,
            "generated_at": datetime.now().isoformat()
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Auto-generation timed out (600s limit)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/briefs")
async def list_visual_briefs(brief_type: str = None, limit: int = 50):
    """List generated visual briefs from the asset inventory"""
    source = f"visual-{brief_type}" if brief_type else None
    assets = list_assets(asset_type="visual-brief", source=source, limit=limit)
    return {"briefs": assets, "total": len(assets)}


@router.get("/stats")
async def visual_content_stats():
    """Get visual content generation statistics"""
    stats = {}
    for bt, info in BRIEF_TYPES.items():
        output_dir = BRIEFS_DIR / info["output_dir"]
        count = 0
        if output_dir.exists():
            count = len([f for f in output_dir.iterdir() if f.suffix == '.md' and not f.name.startswith('.')])
        stats[bt] = {
            "name": info["name"],
            "generated": count,
            "output_dir": str(output_dir)
        }

    total = sum(s["generated"] for s in stats.values())
    return {"types": stats, "total_briefs": total}
