"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { checkHealth } from "@/lib/api";

type Status = "checking" | "connected" | "disconnected";

export default function HealthBadge() {
    const [status, setStatus] = useState<Status>("checking");
    const mountedRef = useRef(true);

    const runCheck = useCallback(async () => {
        const result = await checkHealth();
        if (mountedRef.current) {
            setStatus(result.data?.status === "healthy" ? "connected" : "disconnected");
        }
    }, []);

    useEffect(() => {
        mountedRef.current = true;
        // Initial check + polling
        const timer = setTimeout(() => { runCheck(); }, 0);
        const id = setInterval(runCheck, 30_000);
        return () => {
            mountedRef.current = false;
            clearTimeout(timer);
            clearInterval(id);
        };
    }, [runCheck]);

    const label =
        status === "checking"
            ? "Checking…"
            : status === "connected"
                ? "Backend Connected"
                : "Backend Offline";

    return (
        <div className="health-badge" role="status" aria-live="polite">
            <span className={`status-dot ${status}`} />
            <span>{label}</span>
            {status === "disconnected" && (
                <button
                    className="health-badge-retry"
                    onClick={() => {
                        setStatus("checking");
                        runCheck();
                    }}
                    aria-label="Retry backend connection"
                >
                    Retry
                </button>
            )}
        </div>
    );
}
