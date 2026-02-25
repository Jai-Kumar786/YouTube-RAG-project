"use client";

import {
    useState,
    useRef,
    useEffect,
    useCallback,
    type FormEvent,
    type KeyboardEvent,
} from "react";
import { askQuestion } from "@/lib/api";
import type { ChatMessage } from "@/types";

interface ChatPanelProps {
    hasIngestedVideos: boolean;
    selectedVideoId: string | null;
    selectedVideoTitle: string | null;
    pendingQuestion: string | null;
    onPendingConsumed: () => void;
}

let messageIdCounter = 0;
function nextId() {
    return `msg-${++messageIdCounter}-${Date.now()}`;
}

export default function ChatPanel({
    hasIngestedVideos,
    selectedVideoId,
    selectedVideoTitle,
    pendingQuestion,
    onPendingConsumed,
}: ChatPanelProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const canSend = input.trim().length > 0 && !loading && hasIngestedVideos;

    const submitQuestion = useCallback(async (question: string) => {
        if (!question.trim() || loading) return;

        const userMsg: ChatMessage = {
            id: nextId(),
            role: "user",
            content: question,
            timestamp: new Date(),
        };

        const placeholderMsg: ChatMessage = {
            id: nextId(),
            role: "assistant",
            content: "",
            timestamp: new Date(),
            isLoading: true,
        };

        setMessages((prev) => [...prev, userMsg, placeholderMsg]);
        setInput("");
        setLoading(true);

        const result = await askQuestion(question, selectedVideoId ?? undefined);

        setMessages((prev) => {
            const updated = [...prev];
            const idx = updated.findIndex((m) => m.id === placeholderMsg.id);
            if (idx !== -1) {
                updated[idx] = {
                    ...updated[idx],
                    content: result.data?.answer ?? result.error ?? "Unknown error occurred.",
                    sources: result.data?.sources,
                    isLoading: false,
                };
            }
            return updated;
        });

        setLoading(false);
        inputRef.current?.focus();
    }, [loading, selectedVideoId]);

    // Auto-submit pending question from suggested questions
    useEffect(() => {
        if (pendingQuestion && !loading) {
            submitQuestion(pendingQuestion);
            onPendingConsumed();
        }
    }, [pendingQuestion, loading, submitQuestion, onPendingConsumed]);

    async function handleSend(e?: FormEvent) {
        e?.preventDefault();
        const question = input.trim();
        if (!question || loading) return;
        submitQuestion(question);
    }

    function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
        if (e.key === "Enter" && !e.shiftKey && canSend) {
            e.preventDefault();
            handleSend();
        }
    }

    function formatTime(date: Date) {
        return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    // Display name for the banner
    const displayName = selectedVideoTitle ?? selectedVideoId ?? "All videos";

    return (
        <section className="glass-card chat-panel" aria-label="Chat with AI">
            {/* Active video banner */}
            {hasIngestedVideos && (
                <div className={`active-video-banner ${selectedVideoId ? "filtered" : ""}`}>
                    {selectedVideoId ? (
                        <>🎯 Showing results from: <strong>{displayName}</strong></>
                    ) : (
                        <>📹 Showing results from: <strong>All videos</strong></>
                    )}
                </div>
            )}

            {/* Messages area */}
            {messages.length === 0 ? (
                <div className="chat-empty">
                    <span className="chat-empty-icon">💬</span>
                    <p className="chat-empty-title">
                        {hasIngestedVideos
                            ? "Ask anything about your videos!"
                            : "Ingest a YouTube video first"}
                    </p>
                    <p className="chat-empty-subtitle">
                        {hasIngestedVideos
                            ? selectedVideoId
                                ? `Questions will be answered using "${displayName}" only. Or click a 💡 suggested question!`
                                : "Your questions will be answered using all ingested video transcripts."
                            : "Process a video using the panel on the left, then come back here to ask questions."}
                    </p>
                </div>
            ) : (
                <div className="chat-messages" role="log" aria-live="polite">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`message message-${msg.role}`}
                        >
                            <div className="message-bubble">
                                {msg.isLoading ? (
                                    <div className="typing-dots">
                                        <span />
                                        <span />
                                        <span />
                                    </div>
                                ) : (
                                    msg.content
                                )}
                            </div>
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="message-sources">
                                    {msg.sources.map((s) => (
                                        <span className="source-pill" key={s}>
                                            📹 {s}
                                        </span>
                                    ))}
                                </div>
                            )}
                            <span className="message-time">{formatTime(msg.timestamp)}</span>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>
            )}

            {/* Input bar */}
            <form className="chat-input-bar" onSubmit={handleSend}>
                <input
                    ref={inputRef}
                    className="input-field"
                    type="text"
                    placeholder={
                        hasIngestedVideos
                            ? selectedVideoId
                                ? `Ask about "${displayName}"…`
                                : "Ask a question about the video…"
                            : "Ingest a video first…"
                    }
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={!hasIngestedVideos || loading}
                    aria-label="Question input"
                />
                <button
                    type="submit"
                    className="btn-primary btn-send"
                    disabled={!canSend}
                    aria-label="Send question"
                >
                    ➤
                </button>
            </form>
        </section>
    );
}
