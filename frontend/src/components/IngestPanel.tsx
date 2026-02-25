"use client";

import { useState, type FormEvent } from "react";
import { ingestVideo } from "@/lib/api";
import type { IngestedVideo, ApiResult, DeleteResponse } from "@/types";

interface IngestPanelProps {
    ingestedVideos: IngestedVideo[];
    onVideoIngested: (video: IngestedVideo) => void;
    onClearAll: () => Promise<ApiResult<DeleteResponse>>;
    selectedVideoId: string | null;
    onSelectVideo: (videoId: string) => void;
    onAskQuestion: (videoId: string, question: string) => void;
}

// Validates youtube.com/watch?v=... and youtu.be/... formats
function isValidYouTubeUrl(url: string): boolean {
    try {
        const parsed = new URL(url);
        if (
            parsed.hostname === "youtu.be" &&
            parsed.pathname.length > 1
        ) {
            return true;
        }
        if (
            (parsed.hostname === "www.youtube.com" ||
                parsed.hostname === "youtube.com") &&
            parsed.pathname === "/watch" &&
            parsed.searchParams.has("v")
        ) {
            return true;
        }
        return false;
    } catch {
        return false;
    }
}

export default function IngestPanel({
    ingestedVideos,
    onVideoIngested,
    onClearAll,
    selectedVideoId,
    onSelectVideo,
    onAskQuestion,
}: IngestPanelProps) {
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [clearing, setClearing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [collapsed, setCollapsed] = useState(false);

    const canSubmit = url.trim().length > 0 && !loading;

    async function handleSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setSuccess(null);

        if (!isValidYouTubeUrl(url)) {
            setError(
                "Please enter a valid YouTube URL (youtube.com/watch?v=... or youtu.be/...)"
            );
            return;
        }

        setLoading(true);

        const result = await ingestVideo(url);

        setLoading(false);

        if (result.error) {
            setError(result.error);
            return;
        }

        if (result.data) {
            const { video_id, chunks_created, message, title, suggested_questions } = result.data;

            if (chunks_created === 0) {
                setSuccess(message);
            } else {
                setSuccess(
                    `✓ Ingested "${title}" (${chunks_created} chunks)`
                );
                onVideoIngested({
                    video_id,
                    title,
                    chunks_created,
                    suggested_questions,
                    ingested_at: new Date(),
                });
            }
            setUrl("");
        }
    }

    async function handleClearAll() {
        if (!confirm("Delete ALL stored video chunks? This cannot be undone.")) return;
        setClearing(true);
        setError(null);
        setSuccess(null);
        const result = await onClearAll();
        setClearing(false);
        if (result.error) {
            setError(result.error);
        } else {
            setSuccess(result.data?.message ?? "All videos cleared.");
        }
    }

    return (
        <section className="glass-card ingest-panel" aria-label="Video ingestion">
            <div className="panel-header">
                <h2 className="panel-title">
                    <span className="panel-icon">📥</span> Ingest Video
                </h2>
                {ingestedVideos.length > 0 && (
                    <button
                        className="collapse-toggle"
                        onClick={() => setCollapsed(!collapsed)}
                        aria-label={collapsed ? "Expand ingest form" : "Collapse ingest form"}
                    >
                        {collapsed ? "▼ Expand" : "▲ Collapse"}
                    </button>
                )}
            </div>

            {!collapsed && (
                <form className="ingest-form" onSubmit={handleSubmit}>
                    <input
                        className="input-field"
                        type="url"
                        placeholder="Paste a YouTube URL…"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        disabled={loading}
                        aria-label="YouTube video URL"
                    />
                    <button
                        type="submit"
                        className="btn-primary"
                        disabled={!canSubmit}
                        aria-label="Process video"
                    >
                        {loading ? (
                            <>
                                <span className="spinner spinner-sm" /> Processing…
                            </>
                        ) : (
                            "Process Video"
                        )}
                    </button>

                    {loading && (
                        <p className="duration-notice">
                            ⏳ This may take a minute for long videos…
                        </p>
                    )}

                    {error && (
                        <div className="alert alert-error" role="alert">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="alert alert-success" role="status">
                            {success}
                        </div>
                    )}
                </form>
            )}

            {/* Ingested Videos list */}
            {ingestedVideos.length > 0 && (
                <div className="video-list">
                    <span className="video-list-title">
                        Ingested Videos ({ingestedVideos.length})
                    </span>
                    {ingestedVideos.map((v) => (
                        <div key={v.video_id} className="video-card">
                            <div
                                className={`video-item video-item-selectable ${selectedVideoId === v.video_id ? "selected" : ""}`}
                                onClick={() => onSelectVideo(v.video_id)}
                                role="button"
                                tabIndex={0}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" || e.key === " ") onSelectVideo(v.video_id);
                                }}
                                aria-pressed={selectedVideoId === v.video_id}
                                aria-label={`Filter by ${v.title}`}
                            >
                                <div className="video-item-info">
                                    <span className="video-item-title">
                                        {selectedVideoId === v.video_id && "🎯 "}{v.title}
                                    </span>
                                    <span className="video-item-meta">
                                        {v.video_id} · {v.chunks_created} chunks
                                    </span>
                                </div>
                            </div>
                            {/* Suggested questions */}
                            {v.suggested_questions.length > 0 && (
                                <div className="suggested-questions">
                                    {v.suggested_questions.map((q, i) => (
                                        <button
                                            key={i}
                                            className="suggested-question"
                                            onClick={() => onAskQuestion(v.video_id, q)}
                                            aria-label={`Ask: ${q}`}
                                        >
                                            💡 {q}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                    <button
                        className="btn-danger"
                        onClick={handleClearAll}
                        disabled={clearing}
                        aria-label="Clear all ingested videos"
                    >
                        {clearing ? "Clearing…" : "🗑️ Clear All Videos"}
                    </button>
                </div>
            )}
        </section>
    );
}
