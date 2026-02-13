let _apiBaseUrl: string | null = null;

/** True when running inside the Tauri desktop shell. */
export function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/**
 * Detect the API base URL.
 * - Desktop (Tauri): ask Rust for the sidecar port via IPC.
 * - Web: use the env variable or default 8787.
 */
export async function initApiUrl(): Promise<string> {
  if (_apiBaseUrl) return _apiBaseUrl;

  if (isTauri()) {
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      const port = await invoke<number>("get_api_port");
      _apiBaseUrl = `http://127.0.0.1:${port}`;
    } catch {
      // Fallback if IPC fails
      _apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8787";
    }
  } else {
    _apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8787";
  }

  return _apiBaseUrl!;
}

function API_URL(): string {
  return _apiBaseUrl || import.meta.env.VITE_API_URL || "http://localhost:8787";
}

/**
 * Wait until the backend API responds to /health.
 * Used by the loading screen to know when the sidecar is ready.
 */
export async function waitForBackend(maxAttempts = 60): Promise<void> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const res = await fetch(`${API_URL()}/health`);
      if (res.ok) return;
    } catch {
      // Backend not up yet
    }
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error("Backend did not start in time");
}

export interface OptionChoice {
  value: string;
  label: string;
}

export interface OptionSchema {
  id: string;
  label: string;
  type: "number" | "select" | "text";
  default: number | string;
  min?: number;
  max?: number;
  step?: number;
  choices?: OptionChoice[];
  showWhen?: Record<string, string | string[]>;
}

export interface Processor {
  id: string;
  label: string;
  description: string;
  accepted_extensions: string[];
  options_schema: OptionSchema[];
}

export interface Job {
  id: string;
  processor_id: string;
  original_filename: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  message: string;
  result_extension: string;
  error: string | null;
  created_at: string;
}

export interface ProgressEvent {
  status: string;
  progress: number;
  message: string;
}

export interface Batch {
  id: string;
  job_ids: string[];
  processor_id: string;
  created_at: string;
}

export interface BatchWithJobs extends Batch {
  jobs: Job[];
}

export async function fetchProcessors(): Promise<Processor[]> {
  const res = await fetch(`${API_URL()}/processors`);
  if (!res.ok) throw new Error("Failed to fetch processors");
  return res.json();
}

export async function createJob(
  processorId: string,
  file: File,
  options: Record<string, unknown> = {},
): Promise<Job> {
  const form = new FormData();
  form.append("processor_id", processorId);
  form.append("file", file);
  form.append("options", JSON.stringify(options));

  const res = await fetch(`${API_URL()}/jobs`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function fetchJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_URL()}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export function subscribeProgress(
  jobId: string,
  onEvent: (e: ProgressEvent) => void,
  onDone: () => void,
): () => void {
  const es = new EventSource(`${API_URL()}/jobs/${jobId}/progress`);

  es.onmessage = (msg) => {
    const data: ProgressEvent = JSON.parse(msg.data);
    onEvent(data);
    if (data.status === "completed" || data.status === "failed") {
      es.close();
      onDone();
    }
  };

  es.onerror = () => {
    es.close();
    onDone();
  };

  return () => es.close();
}

export async function createBatch(
  processorId: string,
  files: File[],
  options: Record<string, unknown> = {},
): Promise<Batch> {
  const form = new FormData();
  form.append("processor_id", processorId);
  for (const file of files) {
    form.append("files", file);
  }
  form.append("options", JSON.stringify(options));

  const res = await fetch(`${API_URL()}/jobs/batch`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function fetchBatch(batchId: string): Promise<BatchWithJobs> {
  const res = await fetch(`${API_URL()}/jobs/batch/${batchId}`);
  if (!res.ok) throw new Error("Batch not found");
  return res.json();
}

export function getResultUrl(jobId: string): string {
  return `${API_URL()}/jobs/${jobId}/result`;
}
