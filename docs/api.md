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
    "description": "Remove the background from a video and export with transparency.",
    "accepted_extensions": [".mp4", ".mov", ".webm"],
    "options_schema": [
      {
        "id": "fps",
        "label": "Frames per second",
        "type": "number",
        "default": 15,
        "min": 1,
        "max": 60,
        "step": 1
      },
      {
        "id": "model",
        "label": "AI model",
        "type": "select",
        "default": "u2netp",
        "choices": [
          { "value": "u2netp", "label": "Fast (u2netp)" },
          { "value": "u2net", "label": "Quality (u2net)" },
          { "value": "isnet-general-use", "label": "ISNet" }
        ]
      }
    ]
  }
]
```

Each processor includes an `options_schema` array that describes available options. The frontend uses this to auto-render UI controls.

### Option schema fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique option identifier |
| `label` | string | Display name (fallback if no i18n key) |
| `type` | `"number"` \| `"select"` \| `"text"` | Control type |
| `default` | number \| string | Default value |
| `min`, `max`, `step` | number | For `number` type only |
| `choices` | array | For `select` type: `[{ "value", "label" }]` |
| `showWhen` | object | Conditional visibility: `{ "other_option_id": "value" }` or `{ "id": ["val1", "val2"] }` |

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
| `options` | string (JSON) | Optional: JSON-encoded options matching the processor's schema |

Response:

```json
{
  "id": "a1b2c3d4e5f6",
  "processor_id": "video-bg-remove",
  "original_filename": "video.mp4",
  "status": "pending",
  "progress": 0,
  "message": "",
  "result_extension": "",
  "error": null,
  "created_at": "2025-01-01T00:00:00+00:00"
}
```

### Get Job Status

```
GET /jobs/{job_id}
```

Response: Same shape as create response, with updated status/progress/result_extension.

**Status values**: `pending` → `processing` → `completed` | `failed`

The `result_extension` field (e.g. `.webp`, `.png`, `.mp4`) is populated when the job completes.

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

Returns the processed file with the correct `Content-Type` and `Content-Disposition` headers.

Supported result types: `image/webp`, `image/png`, `image/jpeg`, `image/gif`, `image/bmp`, `image/tiff`, `video/mp4`, `video/quicktime`, `video/webm`, `application/zip`, `audio/mpeg`, `audio/aac`, `audio/wav`, `audio/flac`, `audio/ogg`.

Only available when job status is `completed`.
