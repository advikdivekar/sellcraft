import type { PhotoAnalysis, CopyOutput, CreativeSettings, GenerationJob, ProductInput, ProviderStatus, Tone } from "./types";

export class ApiError extends Error {
  constructor(public code: string, message: string, public retryable = false, public fields?: { field: string; message: string }[]) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, init);
  } catch {
    throw new ApiError("network", "Can't reach the SellCraft server. Check your connection and that the backend is running.", true);
  }
  if (!res.ok) {
    let body: { error?: { code: string; message: string; retryable?: boolean; fields?: { field: string; message: string }[] } } = {};
    try { body = await res.json(); } catch { /* non-JSON error */ }
    const e = body.error;
    throw new ApiError(e?.code ?? "http_" + res.status, e?.message ?? `Request failed (${res.status}).`, e?.retryable ?? res.status >= 500, e?.fields);
  }
  return res.json() as Promise<T>;
}

const json = (method: string, body: unknown): RequestInit => ({
  method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});

export const api = {
  status: () => request<ProviderStatus>("/api/providers/status"),
  upload: (file: Blob, name: string) => {
    const fd = new FormData();
    fd.append("file", file, name);
    return request<{ asset_id: string; width: number; height: number }>("/api/uploads", { method: "POST", body: fd });
  },
  analyze: (assetId: string) => request<PhotoAnalysis>(`/api/uploads/${assetId}/analyze`, { method: "POST" }),
  createJob: (product: ProductInput, settings: CreativeSettings) =>
    request<GenerationJob>("/api/generations", json("POST", { product, settings })),
  getJob: (id: string) => request<GenerationJob>(`/api/generations/${id}`),
  saveCopy: (id: string, copy: CopyOutput) => request<GenerationJob>(`/api/generations/${id}/copy`, json("PATCH", copy)),
  regenerate: (id: string, body: { section?: string | null; tone?: Tone | null; instructions?: string | null }) =>
    request<GenerationJob>(`/api/generations/${id}/regenerate-copy`, json("POST", body)),
  reassemble: (id: string) => request<GenerationJob>(`/api/generations/${id}/reassemble`, { method: "POST" }),
  retry: (id: string) => request<GenerationJob>(`/api/generations/${id}/retry`, { method: "POST" }),
  assetUrl: (jobId: string, assetId: string) => `/api/generations/${jobId}/assets/${assetId}`,
};
