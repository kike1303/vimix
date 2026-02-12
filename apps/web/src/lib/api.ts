const API_URL = "http://localhost:8787";

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

export async function fetchProcessors(): Promise<Processor[]> {
  const res = await fetch(`${API_URL}/processors`);
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

  const res = await fetch(`${API_URL}/jobs`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function fetchJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export function subscribeProgress(
  jobId: string,
  onEvent: (e: ProgressEvent) => void,
  onDone: () => void,
): () => void {
  const es = new EventSource(`${API_URL}/jobs/${jobId}/progress`);

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

export function getResultUrl(jobId: string): string {
  return `${API_URL}/jobs/${jobId}/result`;
}
