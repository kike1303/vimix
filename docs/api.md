# API Reference

Base URL: `http://localhost:8787`

## Health Check

```
GET /health
```

Response: `{ "status": "ok" }`

---

## Processors

### List Available Processors

```
GET /processors
```

Response:

```json
[
  {
    "id": "video-bg-remove",
    "label": "Video Background Removal",
    "description": "Remove the background from an MP4 video and export an animated WebP with transparency.",
    "accepted_extensions": [".mp4", ".mov", ".webm"]
  }
]
```

---

## Jobs

### Create a Job

```
POST /jobs
Content-Type: multipart/form-data
```

| Field | Type | Description |
|-------|------|-------------|
| `processor_id` | string | Processor ID from `/processors` |
| `file` | file | The file to process |

Response:

```json
{
  "id": "a1b2c3d4e5f6",
  "processor_id": "video-bg-remove",
  "original_filename": "video.mp4",
  "status": "pending",
  "progress": 0,
  "message": "",
  "error": null,
  "created_at": "2025-01-01T00:00:00+00:00"
}
```

### Get Job Status

```
GET /jobs/{job_id}
```

Response: Same shape as create response, with updated status/progress.

**Status values**: `pending` → `processing` → `completed` | `failed`

### Subscribe to Progress (SSE)

```
GET /jobs/{job_id}/progress
Accept: text/event-stream
```

Each event:

```
data: {"status": "processing", "progress": 45.2, "message": "Removing background – frame 47/104"}
```

The stream closes automatically when status is `completed` or `failed`.

### Download Result

```
GET /jobs/{job_id}/result
```

Returns the processed file (e.g., `image/webp`).

Only available when job status is `completed`.
