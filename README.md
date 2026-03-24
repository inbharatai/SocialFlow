<div align="center">

<br/>

<!-- Capsule Render Hero Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,12,22&height=200&section=header&text=SocialFlow&fontSize=70&fontAlignY=35&desc=AI-Powered%20Social%20Media%20Automation&descAlignY=55&descSize=20&fontColor=ffffff&animation=fadeIn" width="100%"/>

<br/>

<!-- Animated Typing SVG -->
<a href="https://github.com/inbharatai/SocialFlow">
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=7C3AED&center=true&vCenter=true&repeat=true&width=750&height=45&lines=Generate+%26+Publish+to+12+Platforms;OpenAI+%7C+Anthropic+%7C+Gemini+%7C+HeyGen+%7C+Ollama;Choose+Your+AI+Provider+%E2%80%A2+Free+Tiers+Available;Local-Only+%E2%80%A2+Encrypted+%E2%80%A2+Fully+Automated" alt="Typing SVG" />
</a>

<br/><br/>

<!-- Built with Claude Code -->
[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.ai/claude-code)

<br/>

<!-- Badge Row -->
[![Version](https://img.shields.io/badge/v2.0.0-7C3AED?style=for-the-badge&label=version)](https://github.com/inbharatai/SocialFlow/releases)
[![Build](https://img.shields.io/badge/passing-5B21B6?style=for-the-badge&logo=github-actions&logoColor=white&label=build)]()
[![License](https://img.shields.io/badge/MIT-000080?style=for-the-badge&label=license)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-7C3AED?style=for-the-badge)](https://github.com/inbharatai/SocialFlow/pulls)

<br/>

<!-- Tech badges (flat) -->
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![GPT-4o](https://img.shields.io/badge/GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_Haiku-6B4FBB?style=flat-square&logo=anthropic&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_2.0_Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![DALL-E 3](https://img.shields.io/badge/DALL--E_3-412991?style=flat-square&logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)

<br/>

[**Get Started**](#quick-start) &nbsp;&middot;&nbsp; [**AI Providers**](#ai-providers) &nbsp;&middot;&nbsp; [**Features**](#features) &nbsp;&middot;&nbsp; [**Architecture**](#architecture) &nbsp;&middot;&nbsp; [**API Docs**](#api-reference) &nbsp;&middot;&nbsp; [**Contributing**](#contributing)

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## What is SocialFlow?

**SocialFlow** is an AI-powered social media automation engine that generates and publishes content to **12 platforms** — LinkedIn, Instagram, X, Facebook, Reddit, Medium, Substack, Discord, beehiiv, MailerLite, Brevo, and HeyGen — all from your local machine. It combines **OpenAI GPT-4o**, **Anthropic Claude**, **Google Gemini**, or **local Ollama models** for content generation, **HeyGen** for AI video production, **post-publish analytics**, and **Playwright** for browser-based publishing — with AES-256 encrypted credentials and zero cloud dependencies.

<div align="center">

> *"Generate, schedule, and publish — without handing your credentials to a third party."*

</div>

Now with **multi-provider AI support** — pick the model that fits your budget. Gemini and Claude offer free tiers, so you can start generating content at **zero cost**.

> [!IMPORTANT]
> **When used with [OpenClaw AI CMO](https://github.com/inbharatai/OpenClaw-AI-CMO), no paid API keys are needed.** OpenClaw generates all content locally using Ollama + open-source models. SocialFlow then handles publishing only — which uses browser automation, not APIs. The API keys below are only required if you use SocialFlow **standalone** for content generation.

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## AI Providers

<div align="center">

SocialFlow lets you choose your AI text provider from **Settings** — switch at any time with no code changes. Video generation always uses HeyGen.

<br/>

<table>
<tr>
<th align="center">Provider</th>
<th align="center">Model</th>
<th align="center">Tier</th>
<th align="center">Best For</th>
<th align="center">Get Key</th>
</tr>
<tr>
<td align="center">
  <img src="https://img.shields.io/badge/OpenAI-412991?style=flat-square&logo=openai&logoColor=white" />
</td>
<td align="center"><b>GPT-4o</b></td>
<td align="center"><img src="https://img.shields.io/badge/Paid-f59e0b?style=flat-square" /></td>
<td>Maximum quality &amp; instruction following</td>
<td><a href="https://platform.openai.com/api-keys">platform.openai.com</a></td>
</tr>
<tr>
<td align="center">
  <img src="https://img.shields.io/badge/Anthropic-6B4FBB?style=flat-square&logo=anthropic&logoColor=white" />
</td>
<td align="center"><b>Claude Haiku</b></td>
<td align="center"><img src="https://img.shields.io/badge/Free_Trial-8b5cf6?style=flat-square" /></td>
<td>Fast, creative &amp; cost-efficient</td>
<td><a href="https://console.anthropic.com">console.anthropic.com</a></td>
</tr>
<tr>
<td align="center">
  <img src="https://img.shields.io/badge/Google-4285F4?style=flat-square&logo=google&logoColor=white" />
</td>
<td align="center"><b>Gemini 2.0 Flash</b></td>
<td align="center"><img src="https://img.shields.io/badge/Free_Tier-10b981?style=flat-square" /></td>
<td>Generous free quota, great to start</td>
<td><a href="https://aistudio.google.com/app/apikey">aistudio.google.com</a></td>
</tr>
</table>

<br/>

```
Settings  →  🤖 AI Text Provider  →  Select card  →  Paste API key  →  Save
```

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## At a Glance

<div align="center">

<table>
<tr>
<td align="center"><h3>53+</h3><sub>API Endpoints</sub></td>
<td align="center"><h3>12</h3><sub>Platforms</sub></td>
<td align="center"><h3>3</h3><sub>AI Providers</sub></td>
<td align="center"><h3>10+</h3><sub>Content Types</sub></td>
<td align="center"><h3>AES-256</h3><sub>Encryption</sub></td>
<td align="center"><h3>100%</h3><sub>Local</sub></td>
</tr>
</table>

<br/>

**v2.0 Released** &nbsp;&middot;&nbsp; **12 Platforms** &nbsp;&middot;&nbsp; **HeyGen Video** &nbsp;&middot;&nbsp; **Analytics Engine** &nbsp;&middot;&nbsp; **OpenClaw Bridge** &nbsp;&middot;&nbsp; **Visual Content**

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Features

<details>
<summary><b>Full Feature List (click to expand)</b></summary>

<br/>

| Feature | Description | Key Details |
|:--------|:------------|:------------|
| **Multi-Provider AI** | Choose OpenAI, Anthropic, or Gemini for text generation | Switch providers from the Settings UI — free tiers available |
| **AI Content Generation** | Generate posts, carousels, reel scripts, and threads | Platform-specific tone and formatting for LinkedIn, Instagram, and X |
| **AI Image Generation** | Create social media visuals with DALL-E 3 | Automatic carousel image sets, post thumbnails, custom prompts |
| **AI Video Generation** | Text-to-video, image-to-video, and avatar videos via HeyGen | Lip sync, talking avatars, reel-ready vertical video |
| **Browser Automation** | Publish directly to LinkedIn, Instagram, and X via Playwright | Session persistence — no repeated logins; headless or visible mode |
| **Post Scheduling** | Schedule posts for future publishing with APScheduler | Cron-like scheduling, queue management, automatic retry |
| **Encrypted Credentials** | AES-256 encryption for all stored platform credentials | Keys never leave your machine; encrypted at rest |
| **Session Persistence** | Browser sessions saved locally — log in once, publish forever | No re-authentication needed between runs |
| **React Dashboard** | Single HTML React frontend for managing everything | Content preview, account management, publish controls |
| **Multi-Format Content** | Posts, carousels, reels, threads, and image posts | Each format optimized for its target platform |
| **Local-Only** | Everything runs on your machine — no cloud, no SaaS | Your data, your credentials, your control |

</details>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Architecture

**Key design decisions:**

| Decision | Reason |
|:---------|:-------|
| **Multi-Provider AI** | Users pick their provider; swap between OpenAI, Anthropic, Gemini without code changes |
| **Playwright over APIs** | No official publish APIs for most platforms — browser automation is the reliable path |
| **AES-256 Encryption** | Platform credentials encrypted at rest — never stored in plain text |
| **Session Persistence** | Browser state saved between runs so users authenticate once |
| **Single HTML Frontend** | Zero build step — one React file served by FastAPI, no Node.js needed |
| **SQLite Storage** | Simple, portable, zero-config database for posts, accounts, and schedules |
| **APScheduler** | In-process job scheduling — no external queue or worker infrastructure needed |

<br/>

<details>
<summary><b>Project Structure (click to expand)</b></summary>

<br/>

```
SocialFlow/
│
├── backend/
│   ├── main.py                     # FastAPI app, 53+ endpoints, multi-provider AI
│   ├── automation.py               # LinkedIn, Instagram, X browser automation
│   ├── automation_extended.py      # Facebook, Reddit, Medium, Substack, Discord, Email, HeyGen
│   ├── heygen_adapter.py           # HeyGen native video adapter + 6-state job machine
│   ├── heygen_routes.py            # HeyGen API endpoints (15+ routes)
│   ├── asset_inventory.py          # Content asset tracking + distribution queue
│   ├── analytics_store.py          # Post-publish performance analytics (SQLite)
│   ├── visual_content_routes.py    # Visual brief generation API
│   ├── openclaw_bridge.py          # OpenClaw AI CMO integration bridge
│   ├── requirements.txt            # Python dependencies
│   └── .env.example                # Environment template
│
├── frontend/
│   └── index.html                  # Single-page React dashboard
│
├── sessions/                       # Playwright browser sessions (gitignored)
├── uploads/                        # Uploaded media files (auto-created)
├── start.sh                        # Linux/macOS launcher
├── start.bat                       # Windows launcher
└── README.md
```

</details>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Quick Start

> [!TIP]
> **Prerequisites:** Python 3.10+ &middot; At least one AI API key (Gemini has a free tier) &middot; A Chromium-based browser (Playwright installs its own)

### One-Command Setup

<table>
<tr>
<td width="50%">

**macOS / Linux**
```bash
git clone https://github.com/inbharatai/SocialFlow.git
cd SocialFlow
chmod +x start.sh && ./start.sh
```

</td>
<td width="50%">

**Windows**
```powershell
git clone https://github.com/inbharatai/SocialFlow.git
cd SocialFlow
.\start.bat
```

</td>
</tr>
</table>

<details>
<summary><b>Manual Setup (click to expand)</b></summary>

<br/>

```bash
# 1. Clone
git clone https://github.com/inbharatai/SocialFlow.git && cd SocialFlow

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 3. Environment — add at least one AI provider key
cp .env.example .env
```

</details>

### Run

```bash
# Start the server (serves both API and frontend)
cd backend && uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

<div align="center">

| | URL | Description |
|---|---|---|
| Dashboard | [`http://localhost:8000`](http://localhost:8000) | **React Dashboard** |
| Swagger | [`http://localhost:8000/docs`](http://localhost:8000/docs) | **Interactive API Docs** |
| Health | [`http://localhost:8000/api/health`](http://localhost:8000/api/health) | **Health Check** |

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Tech Stack

<div align="center">

### Backend
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![APScheduler](https://img.shields.io/badge/APScheduler-FF6F00?style=for-the-badge)

### AI — Text Generation (choose one)
![GPT-4o](https://img.shields.io/badge/GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![Claude Haiku](https://img.shields.io/badge/Claude_Haiku-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)
![Gemini Flash](https://img.shields.io/badge/Gemini_2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)

### AI — Images & Video
![DALL-E 3](https://img.shields.io/badge/DALL--E_3-412991?style=for-the-badge&logo=openai&logoColor=white)
![HeyGen](https://img.shields.io/badge/HeyGen_AI-FF4444?style=for-the-badge)

### Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

### Security
![AES-256](https://img.shields.io/badge/AES--256-000000?style=for-the-badge&logo=letsencrypt&logoColor=white)

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Supported Platforms

<div align="center">

<table>
<tr>
<td align="center"><b>Platform</b></td>
<td align="center"><b>Content Types</b></td>
<td align="center"><b>Automation</b></td>
</tr>
<tr><td><b>LinkedIn</b></td><td>Posts, Carousels, Video</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Instagram</b></td><td>Posts, Carousels, Reels</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>X (Twitter)</b></td><td>Tweets, Threads, Video</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Facebook</b></td><td>Posts, Images, Links</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Reddit</b></td><td>Posts, Links, Comments</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Medium</b></td><td>Articles, Stories</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Substack</b></td><td>Newsletters, Posts</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Discord</b></td><td>Announcements, Updates</td><td>Webhook API</td></tr>
<tr><td><b>HeyGen</b></td><td>Avatar Videos, Talking Head</td><td>Browser Automation, Job Tracking</td></tr>
<tr><td><b>beehiiv</b></td><td>Email Newsletters</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>MailerLite</b></td><td>Email Campaigns</td><td>Login, Publish, Session Persist</td></tr>
<tr><td><b>Brevo</b></td><td>Email Marketing</td><td>Login, Publish, Session Persist</td></tr>
</table>

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## API Reference

> [!NOTE]
> Full interactive API docs at [`/docs`](http://localhost:8000/docs) (Swagger UI) when running locally.

<details>
<summary><b>20+ Endpoints (click to expand)</b></summary>

<br/>

| Domain | Endpoint | Method | Description |
|:-------|:---------|:-------|:------------|
| **Health** | `/api/health` | GET | Server health check |
| **Config** | `/api/config` | GET | Current config — provider status, active AI provider |
| | `/api/config` | POST | Update API keys and active AI provider |
| **Accounts** | `/api/accounts` | GET | List all platform accounts |
| | `/api/accounts` | POST | Add a new platform account |
| | `/api/accounts/{id}` | PUT | Update account details |
| | `/api/accounts/{id}` | DELETE | Remove an account |
| | `/api/accounts/{id}/login` | POST | Browser login to platform |
| | `/api/accounts/{id}/check` | GET | Check session validity |
| **Generate** | `/api/generate` | POST | AI content generation (active provider) |
| | `/api/generate-carousel` | POST | Generate carousel with DALL-E 3 images |
| **Video** | `/api/generate-video` | POST | HeyGen text-to-video or image-to-video |
| | `/api/video-status/{task_id}` | GET | Check video generation status |
| | `/api/generate-reel` | POST | Generate reel script + video combo |
| | `/api/generate-avatar` | POST | Talking avatar video |
| | `/api/generate-avatar-with-script` | POST | AI script + talking avatar |
| | `/api/upload-avatar-photo` | POST | Upload avatar reference photo |
| | `/api/upload-audio` | POST | Upload audio for lip sync |
| **Posts** | `/api/posts` | GET | List all posts |
| | `/api/posts` | POST | Create a new post |
| | `/api/posts/{id}` | PUT | Update a post |
| | `/api/posts/{id}` | DELETE | Delete a post |
| | `/api/posts/{id}/publish` | POST | Publish post via browser automation |
| **Upload** | `/api/upload` | POST | Upload media files |

</details>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Security

<div align="center">

| | Layer | Details |
|:--:|:------|:--------|
| 1 | **AES-256 Credential Encryption** | All platform passwords encrypted at rest with AES-256 |
| 2 | **Local-Only Architecture** | No cloud servers, no third-party credential storage |
| 3 | **Session Isolation** | Each platform session stored in its own browser context |
| 4 | **No Credential Transmission** | Passwords decrypted only at publish time, never sent to external APIs |
| 5 | **CORS Protection** | Strict origin allowlist on all API endpoints |
| 6 | **Gitignored Secrets** | Sessions, `.env`, and database excluded from version control |

</div>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Environment Variables

<details>
<summary><b>Configuration Reference (click to expand)</b></summary>

<br/>

| Variable | Required | Default | Description |
|:---------|:--------:|:--------|:------------|
| `AI_PROVIDER` | No | `openai` | Active text AI provider: `openai` \| `anthropic` \| `gemini` |
| `OPENAI_API_KEY` | If using OpenAI | — | GPT-4o content generation + DALL-E 3 image generation |
| `ANTHROPIC_API_KEY` | If using Anthropic | — | Claude Haiku content generation (free trial credits on sign-up) |
| `GEMINI_API_KEY` | If using Gemini | — | Gemini 2.0 Flash content generation (generous free tier) |
| `HEYGEN_PASSWORD` | For video features | — | HeyGen video generation (text-to-video, avatars, lip sync) |
| `HEADLESS` | No | `false` | Set to `true` to run Playwright browsers in headless mode |

> [!IMPORTANT]
> **At least one text AI key is required** for content generation. We recommend starting with Gemini (free tier) or Anthropic (free trial credits).
>
> **Without `HEYGEN_PASSWORD`:** Video generation endpoints will return errors. All other features work normally.

</details>

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## Contributing

<div align="center">

**We welcome contributions!** Whether it is a bug fix, new platform integration, or feature improvement.

</div>

<br/>

1. **Fork** the repository
2. **Branch** — `git checkout -b feature/amazing-feature`
3. **Commit** — `git commit -m 'Add amazing feature'`
4. **Push** — `git push origin feature/amazing-feature`
5. **Open** a Pull Request

> [!NOTE]
> **Project conventions:** AES-256 for all credential storage &middot; Playwright for all browser automation &middot; AI calls through the provider dispatcher in `main.py` &middot; SQLite for persistence &middot; Test with `/docs` before submitting

<br/>

<img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&customColorList=2,12,22&height=2&section=header" width="100%"/>

<br/>

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

<br/>

---

<div align="center">

<br/>

**Built by [INBharat AI](https://github.com/inbharatai) · [info@inbharat.ai](mailto:info@inbharat.ai)**

*Generate, schedule, and publish to 12 platforms — all from your local machine*

`#SocialFlow` · `#AIMarketing` · `#OpenSource` · `#SocialMediaAutomation` · `#HeyGen` · `#ContentOps` · `#SoloBuilder` · `#LocalAI` · `#BuildInPublic`

<br/>

[![Star this repo](https://img.shields.io/github/stars/inbharatai/SocialFlow?style=for-the-badge&logo=github&label=Star%20SocialFlow&color=7C3AED)](https://github.com/inbharatai/SocialFlow)

<br/>

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![GPT-4o](https://img.shields.io/badge/GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)
![Claude](https://img.shields.io/badge/Claude_Haiku-6B4FBB?style=flat-square&logo=anthropic&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![DALL-E 3](https://img.shields.io/badge/DALL--E_3-412991?style=flat-square&logo=openai&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)

<sub>If SocialFlow helped you, give it a star — it means the world to us!</sub>

<br/>

[![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-6B4FBB?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.ai/claude-code)

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,12,22&height=100&section=footer" width="100%"/>
