import type {
    ApiResult,
    IngestResponse,
    AskResponse,
    HealthResponse,
    DeleteResponse,
} from "@/types";

const API_BASE =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ─── Helper: wraps fetch in the ApiResult<T> contract ───

async function apiFetch<T>(
    path: string,
    options?: RequestInit
): Promise<ApiResult<T>> {
    try {
        const res = await fetch(`${API_BASE}${path}`, {
            headers: { "Content-Type": "application/json" },
            ...options,
        });

        const body = await res.json();

        if (!res.ok) {
            // FastAPI returns { detail: "..." } for HTTPException
            const detail =
                typeof body?.detail === "string"
                    ? body.detail
                    : "Something went wrong on the server.";

            if (res.status === 400) return { error: detail }; // validation
            if (res.status === 404) return { error: detail }; // not found
            return { error: `Server error: ${detail}` };      // 500+
        }

        return { data: body as T };
    } catch {
        return { error: "Cannot reach the server. Is the backend running?" };
    }
}

// ─── Public API functions ───

export async function ingestVideo(url: string): Promise<ApiResult<IngestResponse>> {
    return apiFetch<IngestResponse>("/ingest", {
        method: "POST",
        body: JSON.stringify({ youtube_url: url }),
    });
}

export async function askQuestion(question: string, videoId?: string): Promise<ApiResult<AskResponse>> {
    return apiFetch<AskResponse>("/ask", {
        method: "POST",
        body: JSON.stringify({ question, ...(videoId && { video_id: videoId }) }),
    });
}

export async function checkHealth(): Promise<ApiResult<HealthResponse>> {
    return apiFetch<HealthResponse>("/health");
}

export async function clearAllVideos(): Promise<ApiResult<DeleteResponse>> {
    return apiFetch<DeleteResponse>("/videos", {
        method: "DELETE",
    });
}
