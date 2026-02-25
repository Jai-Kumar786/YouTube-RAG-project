// ─── API Request / Response types (mirrors FastAPI Pydantic models) ───

export interface IngestRequest {
  youtube_url: string;
}

export interface IngestResponse {
  message: string;
  video_id: string;
  chunks_created: number;
  title: string;
  suggested_questions: string[];
}

export interface AskRequest {
  question: string;
  video_id?: string;
}

export interface AskResponse {
  answer: string;
  sources: string[];
}

export interface HealthResponse {
  status: string;
  database: string;
  message: string;
}

export interface DeleteResponse {
  message: string;
  deleted_count: number;
}

// ─── Generic API result wrapper (never throws — components check .error) ───

export interface ApiResult<T> {
  data?: T;
  error?: string;
}

// ─── UI State types ───

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  timestamp: Date;
  isLoading?: boolean;
}

export interface IngestedVideo {
  video_id: string;
  title: string;
  chunks_created: number;
  suggested_questions: string[];
  ingested_at: Date;
}
