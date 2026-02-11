# Deployment Plan

Guide for deploying Vimix as a public web application.

## Current limitations (local-only)

- Job state is in-memory (lost on restart)
- Files stored on local disk
- No concurrency limits or rate limiting
- No auth or user isolation

## Architecture for production

```
Vercel / Cloudflare Pages          (frontend, free)
    ↓ HTTPS
Railway / Fly.io                   (FastAPI in Docker, ~$5-20/mo)
    ↓
Redis                              (job queue + state persistence)
    ↓
Modal / Replicate / RunPod         (GPU workers, pay-per-use)
    ↓
Cloudflare R2 / AWS S3             (file storage)
```

## Deployment options by scale

### Small scale (up to ~50 concurrent users)

Single VPS or container running both frontend and backend.

| Component | Option | Cost |
|-----------|--------|------|
| Frontend | Vercel (free tier) | $0 |
| Backend | Railway or Fly.io (Docker) | $5-20/mo |
| Storage | Local disk or R2 free tier | $0 |

Good enough to launch, validate the product, and get early users.

### Medium scale (hundreds of users)

Separate frontend from backend. Add a job queue and external storage.

| Component | Option | Cost |
|-----------|--------|------|
| Frontend | Vercel | $0-20/mo |
| Backend API | Railway / Fly.io (2+ instances) | $20-50/mo |
| Job queue | Redis (Upstash free tier or Railway) | $0-10/mo |
| Storage | Cloudflare R2 | ~$0.015/GB/mo |

### Large scale (GPU processing, fast results)

Offload heavy processing to GPU workers for 10-50x speedup.

| Component | Option | Cost |
|-----------|--------|------|
| Frontend | Vercel | $0-20/mo |
| Backend API | Fly.io | $20-50/mo |
| GPU workers | Modal (A10G GPU) | ~$0.0011/sec |
| Job queue | Redis | $0-10/mo |
| Storage | Cloudflare R2 / S3 | ~$0.015/GB/mo |

A job that takes 15 sec on CPU takes ~1 sec on GPU. Modal charges only while the function runs.

## Code changes required

### 1. Dockerize the backend

Create `services/processor/Dockerfile`:
- Base image: `python:3.11-slim`
- Install system deps: `ffmpeg`, `libwebp-dev` (for img2webp)
- Install Python deps from `requirements.txt`
- Expose port 8787
- Run with `uvicorn`

### 2. Replace in-memory job manager with Redis

Current: `app/services/job_manager.py` uses a Python dict.

Change to:
- Use Redis for job state (hash per job)
- Use Redis pub/sub or streams for SSE progress events
- Jobs survive server restarts and can be shared across instances
- Libraries: `redis[hiredis]` or `arq` (async Redis job queue)

### 3. Replace local file storage with S3/R2

Current: `app/services/file_manager.py` writes to local `uploads/` and `jobs/` dirs.

Change to:
- Upload files to R2/S3 bucket
- Generate presigned URLs for result downloads (avoids proxying large files)
- Add TTL-based cleanup (auto-delete files after 24h)
- Library: `boto3` (works with both S3 and R2)

### 4. Add a processing queue

Current: `asyncio.create_task()` runs jobs in the same process.

Change to:
- Use `arq` (lightweight async Redis queue) or Celery
- Limit concurrent jobs per worker
- Support multiple worker instances
- Retry failed jobs automatically

### 5. Add rate limiting and file size limits

- Max upload size (e.g., 100MB) via FastAPI middleware
- Rate limiting per IP (e.g., 5 jobs/hour for anonymous users)
- Library: `slowapi` for FastAPI rate limiting

### 6. Optional: GPU workers with Modal

For the heaviest processing (rembg), offload to Modal:

```python
# Pseudocode for Modal integration
import modal

app = modal.App("Vimix")
image = modal.Image.debian_slim().pip_install("rembg", "onnxruntime-gpu", "Pillow")

@app.function(image=image, gpu="A10G")
def remove_bg_gpu(frame_bytes: bytes, model: str) -> bytes:
    from rembg import remove, new_session
    session = new_session(model)
    return remove(frame_bytes, session=session)
```

The FastAPI backend would call this function instead of running rembg locally. Modal handles cold starts, scaling, and GPU allocation.

## Environment variables for production

```env
# Frontend
PUBLIC_API_URL=https://api.Vimix.app

# Backend
CORS_ORIGINS=https://Vimix.app
REDIS_URL=redis://...
S3_BUCKET=Vimix-files
S3_ENDPOINT=https://....r2.cloudflarestorage.com
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
MAX_UPLOAD_MB=100
```

## Deployment checklist

- [ ] Create Dockerfile for backend
- [ ] Set up Redis for job state + queue
- [ ] Migrate file storage to R2/S3
- [ ] Add upload size limits
- [ ] Add rate limiting
- [ ] Configure CORS for production domain
- [ ] Set up CI/CD (GitHub Actions → deploy on push)
- [ ] Add health check endpoint monitoring
- [ ] Set up file cleanup cron (delete files older than 24h)
- [ ] Optional: integrate Modal for GPU processing
