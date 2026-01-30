# Social Media Post Generator (FastAPI)

Lightweight FastAPI service and simple frontend to generate social media posts using AI. Produces text variations and images (video generation planned). Can be used manually via the UI or automated via API/WebSocket for pipelines.

**Features**
- Create text variations (multiple options)
- Generate images for posts (via HuggingFace/Freepik integrations)
- WebSocket-based live progress updates during generation
- UI for manual workflows and form-based creation
- Automation-friendly API for headless usage
- LinkedIn one-click posting is in development
- Video generation: planned for future releases

**Repository layout (high level)**
- `socialmedia_generator/` — FastAPI app and backend code
- `socialmedia_generator/static/` — Frontend assets (HTML, JS, CSS)
- `Dockerfile`, `Dockerfile.fastapi` — container build files

## Prerequisites
- Docker (to build and run the image)
- Optional environment variables for external services (Anthropic, HF, DigitalOcean/DO Spaces, Freepik)

## Build
From the repository root run:

```bash
docker build -t social-media-generator:local .
```

## Run (example)
Run the container with required environment variables mounted and ports forwarded. The example below is PowerShell-style (line-continuation with backticks) — adapt to your shell as needed.

```powershell
docker run `
   -e ANTHROPIC_API_KEY=$env:ANTHROPIC_API_KEY `
   -e HF_TOKEN=$env:HF_TOKEN `
   -e DO_SPACES_KEY=$env:DO_SPACES_KEY `
   -e DO_SPACES_SECRET=$env:DO_SPACES_SECRET `
   -e FREEPIK_API_KEY=$env:FREEPIK_API_KEY `
   -v "$(Get-Location)\computer_use_demo:/home/computeruse/computer_use_demo" `
   -v "$HOME\.anthropic:/home/computeruse/.anthropic" `
   -v //var/run/docker.sock:/var/run/docker.sock `
   -p 8000:8000 `
   -it social-media-generator:local
```

Notes:
- The container exposes port `8000` (FastAPI/uvicorn). After start, open `http://localhost:8000/` to access the frontend (or `http://localhost:8000/static/generator.html`).
- Mounting `~/.anthropic` allows the container to read Anthropic CLI/credentials if you use that method.
- Mounting `computer_use_demo` lets the container operate on your local demo folder (persistent data, file uploads, etc.).

## Environment variables
- `ANTHROPIC_API_KEY` — Anthropic API key (if using Anthropic endpoints)
- `HF_TOKEN` — HuggingFace token (for model/API access)
- `DO_SPACES_KEY` / `DO_SPACES_SECRET` — DigitalOcean Spaces credentials (optional, for storage)
- `FREEPIK_API_KEY` — Freepik API key (optional, for image source)

Additional optional DO Spaces configuration:
- `DO_SPACES_REGION` — Region for DO Spaces (default: `sgp1`)
- `DO_SPACES_ENDPOINT` — Full endpoint URL for your Space (e.g. `https://<bucket>.<region>.digitaloceanspaces.com`). When set the public file URL will be constructed from this value.
- `DO_SPACES_BUCKET` — (optional) Bucket/Space name if you prefer to configure it separately.

If you don't have these services configured, the app can still run but some features (image generation, uploads) will be disabled or will fail until configured.

## How to use
- Manual UI: open `http://localhost:8000/` → fill data sources, choose language/tone and media preferences, then click **Create Post**. The UI connects to the backend via HTTP + WebSocket for progress updates.
- Automation: POST to `/api/posts` with the payload described by the form. The API returns a `post_id` and a WebSocket path for live updates.
- Results: once generation completes, the API returns text variation IDs and media content IDs. Use these IDs to select the desired combination and finalize the post.

## API endpoints (selected)
- `POST /api/posts` — create a post generation request
- `GET /api/posts/{post_id}` — fetch post details
- `WS /api/posts/{post_id}/updates` — WebSocket for live generation updates
- `GET /` — serves `index.html` or JSON API summary when a frontend isn't present

## Frontend
- Files live in `socialmedia_generator/static/`.
- `generator.html` loads `generator.js` from `/static/generator.js` (the app mounts the static folder at `/static`).

## Automation & CI
The service is designed to be automation-friendly:
- Use the API + WebSocket for programmatic generation and progress tracking.
- Persist results to S3/Spaces (if configured) to integrate with pipelines.

## Limitations / TODOs
- One-click LinkedIn posting is in development.
- Video generation is planned for future releases.
- The repository includes a heavier `Dockerfile.fastapi` with desktop/VNC support — the supplied `Dockerfile` was simplified for a server-focused build. If you need the desktop UI/VNC features, use `Dockerfile.fastapi` and the dev compose files.

## Screenshots
Screenshots are available in `docs/screenshots/`. Examples below:

![Generator - form view](docs/screenshots/Screenshot%202026-01-30%20233659.png)

![Generator - creating post](docs/screenshots/Screenshot%202026-01-30%20233707.png)

![Generator - live updates](docs/screenshots/Screenshot%202026-01-30%20233800.png)

![Generator - results](docs/screenshots/Screenshot%202026-01-30%20233940.png)

If you add or rename screenshots, update these links accordingly.

## Troubleshooting
- If `generator.js` fails to load when opening `/`, ensure static files are mounted at `/static` (the server mounts `socialmedia_generator/static` at `/static`).
- Check logs from uvicorn for stack traces when API calls fail.

---