"""
SocialFlow - Main Server
AI-powered social media automation with browser-based posting
"""

import os
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from cryptography.fernet import Fernet

from automation import get_automation, LinkedInAutomation, InstagramAutomation, TwitterAutomation

# ============== CONFIG ==============
DATABASE_PATH = "socialflow.db"
UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)
SESSIONS_DIR = Path("sessions")
SESSIONS_DIR.mkdir(exist_ok=True)

# Encryption for credentials
def get_or_create_key():
    key_file = Path(".secret_key")
    if key_file.exists():
        return key_file.read_bytes()
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    return key

FERNET = Fernet(get_or_create_key())

def encrypt(text: str) -> str:
    return FERNET.encrypt(text.encode()).decode()

def decrypt(text: str) -> str:
    return FERNET.decrypt(text.encode()).decode()

# Load config
def load_config():
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "KLING_API_KEY": os.getenv("KLING_API_KEY", ""),
        "HEADLESS": os.getenv("HEADLESS", "false").lower() == "true"
    }

CONFIG = load_config()

# ============== DATABASE ==============
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    
    # Posts table
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        content_type TEXT NOT NULL,
        content TEXT NOT NULL,
        media_paths TEXT,
        scheduled_time DATETIME,
        status TEXT DEFAULT 'draft',
        post_id TEXT,
        error_message TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        published_at DATETIME
    )''')
    
    # Accounts table (encrypted credentials)
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        password_encrypted TEXT NOT NULL,
        is_logged_in INTEGER DEFAULT 0,
        last_login DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Content templates
    c.execute('''CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        platform TEXT NOT NULL,
        content_type TEXT NOT NULL,
        prompt_template TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============== MODELS ==============
class AccountCreate(BaseModel):
    platform: str
    username: str
    password: str

class ContentRequest(BaseModel):
    topic: str
    platform: str
    content_type: str  # post, carousel, reel, thread
    slides: Optional[int] = 5
    custom_instructions: Optional[str] = None


class CarouselRequest(BaseModel):
    topic: str
    slides: int = 5
    style: str = "modern"  # modern, minimal, bold, colorful
    platform: str = "instagram"  # instagram, linkedin
    custom_instructions: Optional[str] = None


class VideoRequest(BaseModel):
    prompt: str
    video_type: str = "text_to_video"  # text_to_video, image_to_video
    image_url: Optional[str] = None  # Required for image_to_video
    duration: int = 5  # 5 or 10 seconds
    aspect_ratio: str = "9:16"  # 9:16 (vertical/reel), 16:9 (horizontal), 1:1 (square)
    mode: str = "std"  # std or pro
    platform: str = "instagram"  # instagram, tiktok, youtube


class ReelRequest(BaseModel):
    topic: str
    style: str = "engaging"  # engaging, educational, funny, dramatic
    duration: int = 5
    platform: str = "instagram"
    custom_instructions: Optional[str] = None


class AvatarRequest(BaseModel):
    image_url: Optional[str] = None  # URL to your photo
    image_path: Optional[str] = None  # Or local path
    text: Optional[str] = None  # Script to speak (uses TTS)
    audio_url: Optional[str] = None  # Or provide your own audio
    voice_id: str = "en_female_1"  # TTS voice
    prompt: str = "speaking naturally with a friendly, professional expression"
    mode: str = "std"  # std or pro


class AvatarScriptRequest(BaseModel):
    topic: str
    duration: int = 30  # seconds of speech
    tone: str = "professional"  # professional, casual, enthusiastic, educational
    platform: str = "instagram"
    custom_instructions: Optional[str] = None

class PostCreate(BaseModel):
    platform: str
    content_type: str
    content: str
    media_paths: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None

class PostUpdate(BaseModel):
    content: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    status: Optional[str] = None

# ============== AI CONTENT GENERATION (OpenAI) ==============
async def generate_content_ai(prompt: str) -> str:
    """Generate content using OpenAI GPT-4"""
    if not CONFIG["OPENAI_API_KEY"]:
        raise HTTPException(
            status_code=400, 
            detail="OpenAI API key not configured. Add OPENAI_API_KEY to your .env file. Get your key at https://platform.openai.com/api-keys"
        )
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert social media content creator. Create engaging, viral-worthy content optimized for each platform. Be creative, authentic, and focus on value."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.8
            },
            timeout=60.0
        )
        
        if response.status_code != 200:
            error_detail = response.text
            if "invalid_api_key" in error_detail:
                raise HTTPException(status_code=401, detail="Invalid OpenAI API key. Check your key at https://platform.openai.com/api-keys")
            if "insufficient_quota" in error_detail:
                raise HTTPException(status_code=402, detail="No OpenAI credits. Add payment method at https://platform.openai.com/account/billing")
            raise HTTPException(status_code=response.status_code, detail=error_detail)
        
        return response.json()["choices"][0]["message"]["content"]


async def generate_image_dalle(prompt: str, size: str = "1024x1024") -> str:
    """Generate image using DALL-E 3"""
    if not CONFIG["OPENAI_API_KEY"]:
        raise HTTPException(status_code=400, detail="OpenAI API key not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {CONFIG['OPENAI_API_KEY']}",
                "Content-Type": "application/json"
            },
            json={
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": "standard"
            },
            timeout=120.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()["data"][0]["url"]


async def download_image(url: str, filename: str) -> str:
    """Download image from URL and save locally"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=60.0)
        filepath = UPLOADS_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return str(filepath)


# ============== KLING AI VIDEO GENERATION ==============
class KlingAI:
    """Kling AI video generation integration"""
    
    # Using official Kling API endpoint
    BASE_URL = "https://api.klingai.com/v1"
    
    @staticmethod
    async def generate_video_from_text(
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "9:16",  # Vertical for reels
        mode: str = "std"  # std or pro
    ) -> dict:
        """Generate video from text prompt"""
        if not CONFIG["KLING_API_KEY"]:
            raise HTTPException(status_code=400, detail="Kling API key not configured. Add KLING_API_KEY to .env")
        
        async with httpx.AsyncClient() as client:
            # Create video generation task
            response = await client.post(
                f"{KlingAI.BASE_URL}/videos/text2video",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": prompt,
                    "duration": duration,
                    "aspect_ratio": aspect_ratio,
                    "mode": mode
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
    
    @staticmethod
    async def generate_video_from_image(
        image_url: str,
        prompt: str,
        duration: int = 5,
        mode: str = "std"
    ) -> dict:
        """Generate video from image + prompt"""
        if not CONFIG["KLING_API_KEY"]:
            raise HTTPException(status_code=400, detail="Kling API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{KlingAI.BASE_URL}/videos/image2video",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json={
                    "image_url": image_url,
                    "prompt": prompt,
                    "duration": duration,
                    "mode": mode
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
    
    @staticmethod
    async def check_task_status(task_id: str) -> dict:
        """Check video generation task status"""
        if not CONFIG["KLING_API_KEY"]:
            raise HTTPException(status_code=400, detail="Kling API key not configured")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{KlingAI.BASE_URL}/videos/tasks/{task_id}",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
    
    @staticmethod
    async def wait_for_video(task_id: str, max_wait: int = 300) -> dict:
        """Poll until video is ready (max 5 minutes)"""
        import asyncio
        
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds < max_wait:
            result = await KlingAI.check_task_status(task_id)
            status = result.get("status", "").lower()
            
            if status == "completed":
                return result
            elif status in ["failed", "error"]:
                raise HTTPException(status_code=500, detail=f"Video generation failed: {result}")
            
            # Wait 5 seconds before polling again
            await asyncio.sleep(5)
        
        raise HTTPException(status_code=408, detail="Video generation timed out")
    
    @staticmethod
    async def generate_avatar_video(
        image_url: str,
        audio_url: str = None,
        text: str = None,
        voice_id: str = "en_female_1",
        prompt: str = "speaking naturally with a friendly expression",
        mode: str = "std"
    ) -> dict:
        """Generate talking avatar video from photo + audio/text"""
        if not CONFIG["KLING_API_KEY"]:
            raise HTTPException(status_code=400, detail="Kling API key not configured")
        
        async with httpx.AsyncClient() as client:
            payload = {
                "image_url": image_url,
                "prompt": prompt,
                "mode": mode
            }
            
            # Either use provided audio or generate from text
            if audio_url:
                payload["audio_url"] = audio_url
            elif text:
                payload["text"] = text
                payload["voice_id"] = voice_id
            else:
                raise HTTPException(status_code=400, detail="Either audio_url or text is required")
            
            response = await client.post(
                f"{KlingAI.BASE_URL}/videos/avatar",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()
    
    @staticmethod
    async def generate_lip_sync(
        video_url: str,
        audio_url: str = None,
        text: str = None,
        voice_id: str = "en_female_1"
    ) -> dict:
        """Add lip sync to existing video"""
        if not CONFIG["KLING_API_KEY"]:
            raise HTTPException(status_code=400, detail="Kling API key not configured")
        
        async with httpx.AsyncClient() as client:
            payload = {"video_url": video_url}
            
            if audio_url:
                payload["audio_url"] = audio_url
            elif text:
                payload["text"] = text
                payload["voice_id"] = voice_id
            
            response = await client.post(
                f"{KlingAI.BASE_URL}/videos/lip-sync",
                headers={
                    "Authorization": f"Bearer {CONFIG['KLING_API_KEY']}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return response.json()

# ============== SCHEDULER ==============
scheduler = AsyncIOScheduler()

async def publish_scheduled_post(post_id: int):
    """Publish a scheduled post using browser automation"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = dict(c.fetchone())
    
    c.execute("SELECT * FROM accounts WHERE platform = ?", (post["platform"],))
    account_row = c.fetchone()
    
    if not account_row:
        c.execute("UPDATE posts SET status = 'failed', error_message = 'No account connected' WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        return
    
    account = dict(account_row)
    
    try:
        # Get automation instance
        auto = get_automation(post["platform"], headless=CONFIG["HEADLESS"])
        
        # Parse media paths
        media_paths = json.loads(post["media_paths"]) if post["media_paths"] else None
        
        # Post content
        result = await auto.post(post["content"], media_paths)
        
        if result["success"]:
            c.execute(
                "UPDATE posts SET status = 'published', published_at = ? WHERE id = ?",
                (datetime.now().isoformat(), post_id)
            )
        else:
            c.execute(
                "UPDATE posts SET status = 'failed', error_message = ? WHERE id = ?",
                (result["message"], post_id)
            )
    except Exception as e:
        c.execute(
            "UPDATE posts SET status = 'failed', error_message = ? WHERE id = ?",
            (str(e), post_id)
        )
    
    conn.commit()
    conn.close()

# ============== APP SETUP ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.start()
    
    # Reschedule pending posts
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, scheduled_time FROM posts WHERE status = 'scheduled' AND scheduled_time > ?",
              (datetime.now().isoformat(),))
    for row in c.fetchall():
        post_id, scheduled_time = row
        scheduler.add_job(
            publish_scheduled_post,
            DateTrigger(run_date=datetime.fromisoformat(scheduled_time)),
            args=[post_id],
            id=f"post_{post_id}",
            replace_existing=True
        )
    conn.close()
    
    yield
    scheduler.shutdown()

app = FastAPI(title="SocialFlow", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============== API ROUTES ==============

@app.get("/")
async def serve_frontend():
    return FileResponse("../frontend/index.html")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# --- Accounts ---
@app.get("/api/accounts")
async def get_accounts():
    """Get all connected accounts (without passwords)"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, platform, username, is_logged_in, last_login FROM accounts")
    accounts = [dict(row) for row in c.fetchall()]
    conn.close()
    return {"accounts": accounts}

@app.post("/api/accounts")
async def add_account(account: AccountCreate):
    """Add account credentials"""
    conn = get_db()
    c = conn.cursor()
    
    # Encrypt password
    encrypted_pw = encrypt(account.password)
    
    c.execute(
        """INSERT OR REPLACE INTO accounts (platform, username, password_encrypted, is_logged_in)
           VALUES (?, ?, ?, 0)""",
        (account.platform.lower(), account.username, encrypted_pw)
    )
    conn.commit()
    conn.close()
    
    return {"success": True, "message": f"Account added for {account.platform}"}

@app.post("/api/accounts/{platform}/login")
async def login_account(platform: str):
    """Login to a platform using saved credentials"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM accounts WHERE platform = ?", (platform.lower(),))
    row = c.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = dict(row)
    password = decrypt(account["password_encrypted"])
    
    try:
        auto = get_automation(platform, headless=False)  # Always visible for login
        result = await auto.login(account["username"], password)
        await auto.close()
        
        if result["success"]:
            c.execute(
                "UPDATE accounts SET is_logged_in = 1, last_login = ? WHERE platform = ?",
                (datetime.now().isoformat(), platform.lower())
            )
            conn.commit()
        
        conn.close()
        return result
        
    except Exception as e:
        conn.close()
        return {"success": False, "message": str(e)}

@app.post("/api/accounts/{platform}/check")
async def check_login_status(platform: str):
    """Check if still logged in to a platform"""
    try:
        auto = get_automation(platform, headless=True)
        is_logged_in = await auto.check_login()
        await auto.close()
        
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE accounts SET is_logged_in = ? WHERE platform = ?",
                  (1 if is_logged_in else 0, platform.lower()))
        conn.commit()
        conn.close()
        
        return {"logged_in": is_logged_in}
    except Exception as e:
        return {"logged_in": False, "error": str(e)}

@app.delete("/api/accounts/{platform}")
async def delete_account(platform: str):
    """Delete account and session"""
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM accounts WHERE platform = ?", (platform.lower(),))
    conn.commit()
    conn.close()
    
    # Delete session file
    session_file = SESSIONS_DIR / f"{platform.lower()}_session.json"
    if session_file.exists():
        session_file.unlink()
    
    return {"deleted": True}

# --- Content Generation ---
@app.post("/api/generate")
async def generate_content(request: ContentRequest):
    """Generate AI content"""
    
    # Build prompt based on platform and content type
    platform_tips = {
        "linkedin": "Professional tone, thought leadership, industry insights. Use line breaks for readability. Include 3-5 relevant hashtags at the end.",
        "instagram": "Casual, engaging, visual-first. Use emojis strategically. Include 20-30 hashtags in a comment or at the end.",
        "twitter": "Concise, punchy, conversation-starting. Max 280 characters for single tweets. Use threads for longer content."
    }
    
    content_formats = {
        "post": f"Create a single engaging {request.platform} post",
        "carousel": f"Create a {request.slides}-slide carousel. For EACH slide provide:\n- **Slide N:** [Headline]\n- Content (2-3 short sentences)\n- Visual suggestion",
        "reel": "Create a 30-60 second video script with:\n- Hook (first 3 sec)\n- Main points (3-5 quick tips)\n- CTA\n- Caption\n- Hashtags\n- Audio/music suggestion",
        "thread": "Create a Twitter/X thread with 5-8 tweets. Number each tweet. First tweet is the hook. Last tweet is the CTA."
    }
    
    prompt = f"""{content_formats.get(request.content_type, 'Create a post')} about: {request.topic}

Platform: {request.platform.upper()}
Tips: {platform_tips.get(request.platform.lower(), '')}

{request.custom_instructions or ''}

Make it engaging, authentic, and optimized for maximum reach."""

    content = await generate_content_ai(prompt)
    
    return {
        "content": content,
        "platform": request.platform,
        "content_type": request.content_type,
        "generated_at": datetime.now().isoformat()
    }


# --- Carousel Generation ---
@app.post("/api/generate-carousel")
async def generate_carousel(request: CarouselRequest):
    """Generate a complete carousel with AI images and text"""
    
    # Step 1: Generate slide content with GPT-4
    content_prompt = f"""Create a {request.slides}-slide carousel for {request.platform} about: {request.topic}

For EACH slide, provide in this exact JSON format:
{{
    "slides": [
        {{
            "slide_number": 1,
            "headline": "Catchy headline (max 6 words)",
            "body": "Supporting text (1-2 short sentences)",
            "image_prompt": "Detailed image description for AI generation - describe visual style, colors, elements"
        }}
    ],
    "caption": "Instagram/LinkedIn caption with hashtags"
}}

Slide 1 = Hook/Title slide (attention grabbing)
Last slide = CTA (follow, like, save, etc.)
Style: {request.style}

{request.custom_instructions or ''}

Return ONLY valid JSON, no other text."""

    content_response = await generate_content_ai(content_prompt)
    
    # Parse the JSON response
    try:
        # Clean up response - remove markdown code blocks if present
        clean_response = content_response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        clean_response = clean_response.strip()
        
        carousel_data = json.loads(clean_response)
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response", "raw": content_response}
    
    # Step 2: Generate images for each slide
    generated_images = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for i, slide in enumerate(carousel_data.get("slides", [])):
        image_prompt = slide.get("image_prompt", request.topic)
        
        # Enhance prompt for better carousel images
        enhanced_prompt = f"""Create a clean, professional social media carousel slide image.
Style: {request.style}, modern, eye-catching
Content hint: {image_prompt}
Requirements: 
- Bold, readable text area (leave space for overlay text)
- Vibrant but not cluttered
- Instagram/LinkedIn optimized (square format works best)
- Professional, high-quality look
Do NOT include any text in the image."""

        try:
            image_url = await generate_image_dalle(enhanced_prompt, "1024x1024")
            filename = f"carousel_{timestamp}_slide_{i+1}.png"
            local_path = await download_image(image_url, filename)
            
            generated_images.append({
                "slide_number": i + 1,
                "headline": slide.get("headline", ""),
                "body": slide.get("body", ""),
                "image_path": local_path,
                "image_url": f"/uploads/{filename}"
            })
        except Exception as e:
            generated_images.append({
                "slide_number": i + 1,
                "headline": slide.get("headline", ""),
                "body": slide.get("body", ""),
                "error": str(e)
            })
    
    return {
        "success": True,
        "carousel": {
            "topic": request.topic,
            "platform": request.platform,
            "style": request.style,
            "slides": generated_images,
            "caption": carousel_data.get("caption", ""),
            "generated_at": datetime.now().isoformat()
        }
    }


# --- Video Generation (Kling AI) ---
@app.post("/api/generate-video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Generate video using Kling AI"""
    
    try:
        if request.video_type == "image_to_video":
            if not request.image_url:
                raise HTTPException(status_code=400, detail="image_url is required for image_to_video")
            result = await KlingAI.generate_video_from_image(
                image_url=request.image_url,
                prompt=request.prompt,
                duration=request.duration,
                mode=request.mode
            )
        else:
            result = await KlingAI.generate_video_from_text(
                prompt=request.prompt,
                duration=request.duration,
                aspect_ratio=request.aspect_ratio,
                mode=request.mode
            )
        
        return {
            "success": True,
            "task_id": result.get("task_id"),
            "status": "processing",
            "message": "Video generation started. Use /api/video-status/{task_id} to check progress."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/video-status/{task_id}")
async def check_video_status(task_id: str):
    """Check video generation status"""
    try:
        result = await KlingAI.check_task_status(task_id)
        return {
            "success": True,
            "task_id": task_id,
            "status": result.get("status"),
            "video_url": result.get("video_url") or result.get("output", {}).get("video_url"),
            "data": result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/generate-reel")
async def generate_reel(request: ReelRequest):
    """Generate a complete reel: script + video"""
    
    # Step 1: Generate script with GPT-4
    script_prompt = f"""Create a viral {request.duration}-second reel script about: {request.topic}

Style: {request.style}
Platform: {request.platform}

Provide in JSON format:
{{
    "hook": "First 2-3 seconds - attention grabber (max 10 words)",
    "main_content": "Main message - quick, punchy points",
    "cta": "Call to action at the end",
    "video_prompt": "Detailed visual description for AI video generation - describe scene, movement, style, mood",
    "caption": "Post caption with emojis and hashtags",
    "audio_suggestion": "Type of music/sound that would fit"
}}

{request.custom_instructions or ''}

Make it engaging and optimized for {request.platform}. Return ONLY valid JSON."""

    try:
        script_response = await generate_content_ai(script_prompt)
        
        # Parse JSON
        clean_response = script_response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        clean_response = clean_response.strip()
        
        script_data = json.loads(clean_response)
        
        # Step 2: Generate video with Kling AI
        video_prompt = script_data.get("video_prompt", request.topic)
        
        # Enhance for reel format
        enhanced_video_prompt = f"""{video_prompt}
Style: Vertical video (9:16), dynamic, engaging for social media reels.
Movement: Smooth camera movements, eye-catching transitions.
Quality: High quality, vibrant colors, professional look."""

        video_result = await KlingAI.generate_video_from_text(
            prompt=enhanced_video_prompt,
            duration=request.duration,
            aspect_ratio="9:16",  # Vertical for reels
            mode="std"
        )
        
        return {
            "success": True,
            "reel": {
                "topic": request.topic,
                "platform": request.platform,
                "script": script_data,
                "video_task_id": video_result.get("task_id"),
                "video_status": "processing",
                "generated_at": datetime.now().isoformat()
            }
        }
        
    except json.JSONDecodeError:
        return {"success": False, "error": "Failed to parse script", "raw": script_response}
    except Exception as e:
        return {"success": False, "error": str(e)}


# --- Avatar Video Generation ---
@app.post("/api/generate-avatar")
async def generate_avatar(request: AvatarRequest):
    """Generate talking avatar video from your photo"""
    
    try:
        # Determine image URL
        image_url = request.image_url
        if request.image_path and not image_url:
            # If local path provided, we need to serve it or upload
            # For now, assume it's a URL or will be converted
            image_url = request.image_path
        
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url or image_path is required")
        
        result = await KlingAI.generate_avatar_video(
            image_url=image_url,
            audio_url=request.audio_url,
            text=request.text,
            voice_id=request.voice_id,
            prompt=request.prompt,
            mode=request.mode
        )
        
        return {
            "success": True,
            "task_id": result.get("task_id"),
            "status": "processing",
            "message": "Avatar video generation started"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/generate-avatar-with-script")
async def generate_avatar_with_script(request: AvatarScriptRequest):
    """Generate script + create avatar video"""
    
    # Step 1: Generate script with GPT-4
    script_prompt = f"""Write a {request.duration}-second speaking script about: {request.topic}

Tone: {request.tone}
Platform: {request.platform}

Requirements:
- Natural, conversational speech
- About {request.duration * 2} words (average speaking pace)
- Engaging opening hook
- Clear main message
- Call to action at the end

{request.custom_instructions or ''}

Return ONLY the script text that will be spoken. No formatting, no stage directions, just the words to be said."""

    try:
        script = await generate_content_ai(script_prompt)
        
        return {
            "success": True,
            "script": script.strip(),
            "word_count": len(script.split()),
            "estimated_duration": len(script.split()) / 2,  # ~2 words per second
            "message": "Script generated. Upload your photo and use /api/generate-avatar to create the video."
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/upload-avatar-photo")
async def upload_avatar_photo(file: UploadFile = File(...)):
    """Upload photo for avatar generation"""
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, WebP images allowed")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"avatar_{timestamp}_{file.filename}"
    filepath = UPLOADS_DIR / filename
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "success": True,
        "filename": filename,
        "path": str(filepath),
        "url": f"/uploads/{filename}",
        "full_url": f"http://localhost:8000/uploads/{filename}"
    }


@app.post("/api/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio for avatar/lip-sync"""
    
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/x-wav", "audio/ogg"]
    # Be more permissive with audio types
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_{timestamp}_{file.filename}"
    filepath = UPLOADS_DIR / filename
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {
        "success": True,
        "filename": filename,
        "path": str(filepath),
        "url": f"/uploads/{filename}",
        "full_url": f"http://localhost:8000/uploads/{filename}"
    }

# --- Posts CRUD ---
@app.get("/api/posts")
async def get_posts(status: Optional[str] = None, platform: Optional[str] = None):
    conn = get_db()
    c = conn.cursor()
    
    query = "SELECT * FROM posts WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if platform:
        query += " AND platform = ?"
        params.append(platform)
    
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    
    posts = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return {"posts": posts}

@app.post("/api/posts")
async def create_post(post: PostCreate):
    conn = get_db()
    c = conn.cursor()
    
    status = "scheduled" if post.scheduled_time else "draft"
    
    c.execute(
        """INSERT INTO posts (platform, content_type, content, media_paths, scheduled_time, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            post.platform,
            post.content_type,
            post.content,
            json.dumps(post.media_paths) if post.media_paths else None,
            post.scheduled_time.isoformat() if post.scheduled_time else None,
            status
        )
    )
    
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    
    if post.scheduled_time and post.scheduled_time > datetime.now():
        scheduler.add_job(
            publish_scheduled_post,
            DateTrigger(run_date=post.scheduled_time),
            args=[post_id],
            id=f"post_{post_id}",
            replace_existing=True
        )
    
    return {"id": post_id, "status": status}

@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, update: PostUpdate):
    conn = get_db()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if update.content is not None:
        updates.append("content = ?")
        params.append(update.content)
    if update.scheduled_time is not None:
        updates.append("scheduled_time = ?")
        params.append(update.scheduled_time.isoformat())
        updates.append("status = 'scheduled'")
    if update.status is not None:
        updates.append("status = ?")
        params.append(update.status)
    
    if updates:
        params.append(post_id)
        c.execute(f"UPDATE posts SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    
    conn.close()
    return {"updated": True}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    
    try:
        scheduler.remove_job(f"post_{post_id}")
    except Exception:
        pass
    
    return {"deleted": True}

@app.post("/api/posts/{post_id}/publish")
async def publish_now(post_id: int, background_tasks: BackgroundTasks):
    """Publish a post immediately"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE posts SET status = 'publishing' WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    
    background_tasks.add_task(publish_scheduled_post, post_id)
    return {"message": "Publishing started"}

# --- File Upload ---
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload media file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = UPLOADS_DIR / filename
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    return {"filename": filename, "path": str(filepath)}

# --- Config ---
@app.get("/api/config")
async def get_config():
    return {
        "openai_configured": bool(CONFIG["OPENAI_API_KEY"]),
        "kling_configured": bool(CONFIG["KLING_API_KEY"]),
        "headless_mode": CONFIG["HEADLESS"]
    }

class ConfigUpdate(BaseModel):
    OPENAI_API_KEY: Optional[str] = None
    KLING_API_KEY: Optional[str] = None
    HEADLESS: Optional[bool] = None

@app.post("/api/config")
async def update_config(new_config: ConfigUpdate):
    global CONFIG
    for key, value in new_config.model_dump(exclude_none=True).items():
        CONFIG[key] = value
        os.environ[key] = str(value)
    return {"updated": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
