"""
SocialFlow HeyGen API Routes — Native Video Generation Endpoints

These endpoints make HeyGen a first-class content generation source inside SocialFlow.
They follow the same FastAPI pattern as existing endpoints.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from heygen_adapter import (
    HeyGenVideoAdapter,
    HeyGenJobState,
    create_heygen_job,
    update_job_state,
    get_job,
    list_jobs,
    get_platform_video_rules,
    generate_platform_variants,
    PLATFORM_VIDEO_RULES
)
from asset_inventory import (
    register_asset,
    get_asset,
    list_assets,
    queue_content,
    list_queue,
    update_queue_state
)

router = APIRouter(prefix="/api/heygen", tags=["HeyGen Video"])


# ─── REQUEST MODELS ──────────────────────────────────────────

class CreateVideoJobRequest(BaseModel):
    script: str
    campaign: str = ""
    topic: str = ""
    platform_targets: Optional[List[str]] = None
    cta: str = ""
    format_hint: str = "vertical"
    duration_target: int = 30


class JobActionRequest(BaseModel):
    job_id: str


class RegisterOutputRequest(BaseModel):
    job_id: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    aspect_ratio: str = "9:16"


class QueueVideoRequest(BaseModel):
    job_id: str
    platforms: Optional[List[str]] = None
    campaign: str = ""


# ─── JOB MANAGEMENT ──────────────────────────────────────────

@router.post("/jobs")
async def create_job(request: CreateVideoJobRequest):
    """Create a new HeyGen video generation job"""
    job = create_heygen_job(
        script=request.script,
        campaign=request.campaign,
        topic=request.topic,
        platform_targets=request.platform_targets or ["instagram", "youtube", "linkedin"],
        cta=request.cta,
        format_hint=request.format_hint,
        duration_target=request.duration_target
    )
    return {"success": True, "job": job}


@router.get("/jobs")
async def get_jobs(state: str = None, limit: int = 50):
    """List HeyGen jobs, optionally filtered by state"""
    jobs = list_jobs(state=state, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/jobs/{job_id}")
async def get_job_details(job_id: str):
    """Get details of a specific job"""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"job": job}


@router.post("/jobs/{job_id}/generate")
async def trigger_generation(job_id: str):
    """
    Trigger video generation for a job.
    Requires HeyGen to be logged in.
    Opens browser, navigates to HeyGen editor, inputs script.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    adapter = HeyGenVideoAdapter(headless=False)
    try:
        result = await adapter.create_video(job_id)
        return result
    finally:
        await adapter.close()


@router.post("/jobs/{job_id}/register-output")
async def register_job_output(job_id: str, request: RegisterOutputRequest):
    """
    Register the output of a completed HeyGen video.
    Call this after the video is downloaded/available from HeyGen.
    Creates an asset in the SocialFlow inventory.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Register as asset
    asset = register_asset(
        asset_type="video",
        source="heygen",
        title=f"HeyGen Video: {job.get('topic', job_id)[:80]}",
        description=job.get("script", "")[:500],
        file_path=request.file_path,
        file_url=request.file_url,
        duration_seconds=request.duration_seconds,
        aspect_ratio=request.aspect_ratio,
        campaign=job.get("campaign", ""),
        topic=job.get("topic", ""),
        tags=["heygen", "video", "generated"],
        metadata={
            "job_id": job_id,
            "format_hint": job.get("format_hint"),
            "platform_targets": job.get("platform_targets", [])
        }
    )

    # Transition job to completed first if still in draft/queued, then to ready
    if job["state"] in (HeyGenJobState.DRAFT, HeyGenJobState.QUEUED):
        update_job_state(job_id, HeyGenJobState.QUEUED, details="Manual output registration")
        update_job_state(job_id, HeyGenJobState.GENERATING, details="Manually marked generating")
        update_job_state(job_id, HeyGenJobState.COMPLETED, details="Manually completed",
                        output_path=request.file_path, output_url=request.file_url)

    if job["state"] in (HeyGenJobState.COMPLETED, HeyGenJobState.FAILED):
        pass  # already completed or failed

    # Now transition to ready_for_distribution
    updated_job = get_job(job_id)
    if updated_job and updated_job["state"] in (HeyGenJobState.COMPLETED, HeyGenJobState.FAILED):
        update_job_state(
            job_id,
            HeyGenJobState.READY,
            details=f"Output registered as {asset['asset_id']}",
            output_path=request.file_path,
            output_url=request.file_url
        )

    return {
        "success": True,
        "asset": asset,
        "job_state": HeyGenJobState.READY,
        "message": "Video registered in asset inventory. Ready for platform distribution."
    }


@router.post("/jobs/{job_id}/distribute")
async def distribute_to_platforms(job_id: str, request: QueueVideoRequest):
    """
    Create platform-specific queue entries for a completed video.
    This routes the video to Instagram, YouTube, LinkedIn, etc.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job["state"] not in (HeyGenJobState.COMPLETED, HeyGenJobState.READY):
        raise HTTPException(
            status_code=400,
            detail=f"Job must be completed or ready. Current state: {job['state']}"
        )

    platforms = request.platforms or job.get("platform_targets", [])
    variants = generate_platform_variants(job)

    queued = []
    for variant in variants:
        if variant["platform"] not in platforms:
            continue

        q = queue_content(
            platform=variant["platform"],
            content_type=variant["format"],
            caption=f"[Draft — needs platform copy] {variant['topic']}",
            copy_text=variant["script"][:500],
            media_paths=[variant["video_path"]] if variant.get("video_path") else [],
            asset_id=None,  # link to asset if registered
            campaign=request.campaign or variant.get("campaign", ""),
            source_job_id=job_id
        )
        queued.append(q)

    return {
        "success": True,
        "job_id": job_id,
        "queued": queued,
        "total_platforms": len(queued),
        "message": f"Video queued for distribution to {len(queued)} platforms"
    }


# ─── PLATFORM RULES ──────────────────────────────────────────

@router.get("/platform-rules")
async def get_all_platform_rules():
    """Get video formatting rules for all platforms"""
    return {"rules": PLATFORM_VIDEO_RULES}


@router.get("/platform-rules/{platform}")
async def get_platform_rules(platform: str):
    """Get video formatting rules for a specific platform"""
    rules = get_platform_video_rules(platform)
    if not rules:
        raise HTTPException(status_code=404, detail=f"No rules for platform: {platform}")
    return {"platform": platform, "rules": rules}


# ─── ASSET INVENTORY ─────────────────────────────────────────

@router.get("/assets")
async def get_assets(
    asset_type: str = None,
    source: str = None,
    campaign: str = None,
    limit: int = 50
):
    """List assets in the inventory"""
    assets = list_assets(asset_type=asset_type, source=source, campaign=campaign, limit=limit)
    return {"assets": assets, "total": len(assets)}


@router.get("/assets/{asset_id}")
async def get_asset_details(asset_id: str):
    """Get details of a specific asset"""
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
    return {"asset": asset}


# ─── CONTENT QUEUE ────────────────────────────────────────────

@router.get("/queue")
async def get_content_queue(
    platform: str = None,
    state: str = None,
    campaign: str = None,
    limit: int = 50
):
    """List content queue items"""
    items = list_queue(platform=platform, state=state, campaign=campaign, limit=limit)
    return {"queue": items, "total": len(items)}


@router.post("/queue/{queue_id}/approve")
async def approve_queue_item(queue_id: str):
    """Approve a queue item for publishing"""
    success = update_queue_state(queue_id, "approved")
    if not success:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return {"success": True, "queue_id": queue_id, "state": "approved"}


@router.post("/queue/{queue_id}/publish")
async def publish_queue_item(queue_id: str):
    """Mark a queue item as published"""
    success = update_queue_state(queue_id, "published")
    if not success:
        raise HTTPException(status_code=404, detail=f"Queue item {queue_id} not found")
    return {"success": True, "queue_id": queue_id, "state": "published"}
