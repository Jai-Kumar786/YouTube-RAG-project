"use client";

import { useState, useCallback } from "react";
import Header from "@/components/Header";
import IngestPanel from "@/components/IngestPanel";
import ChatPanel from "@/components/ChatPanel";
import { clearAllVideos } from "@/lib/api";
import type { IngestedVideo } from "@/types";

export default function Home() {
  const [ingestedVideos, setIngestedVideos] = useState<IngestedVideo[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  // Pending question to auto-submit in ChatPanel
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);

  const handleVideoIngested = (video: IngestedVideo) => {
    setIngestedVideos((prev) => {
      const exists = prev.some((v) => v.video_id === video.video_id);
      if (exists) {
        return prev.map((v) => (v.video_id === video.video_id ? video : v));
      }
      return [...prev, video];
    });
    // Auto-select the newly ingested video
    setSelectedVideoId(video.video_id);
  };

  const handleClearAll = async () => {
    const result = await clearAllVideos();
    if (!result.error) {
      setIngestedVideos([]);
      setSelectedVideoId(null);
    }
    return result;
  };

  const handleSelectVideo = (videoId: string) => {
    // Toggle: click again to deselect
    setSelectedVideoId((prev) => (prev === videoId ? null : videoId));
  };

  // Called when a suggested question pill is clicked
  const handleAskQuestion = useCallback((videoId: string, question: string) => {
    setSelectedVideoId(videoId);
    setPendingQuestion(question);
  }, []);

  // Called by ChatPanel after it consumes the pending question
  const handlePendingConsumed = useCallback(() => {
    setPendingQuestion(null);
  }, []);

  // Find the selected video's title for the banner
  const selectedVideoTitle = ingestedVideos.find(
    (v) => v.video_id === selectedVideoId
  )?.title ?? null;

  return (
    <div className="app-container">
      <Header />

      <main
        className={`main-grid ${ingestedVideos.length > 0 ? "collapsed" : ""}`}
      >
        <IngestPanel
          ingestedVideos={ingestedVideos}
          onVideoIngested={handleVideoIngested}
          onClearAll={handleClearAll}
          selectedVideoId={selectedVideoId}
          onSelectVideo={handleSelectVideo}
          onAskQuestion={handleAskQuestion}
        />
        <ChatPanel
          hasIngestedVideos={ingestedVideos.length > 0}
          selectedVideoId={selectedVideoId}
          selectedVideoTitle={selectedVideoTitle}
          pendingQuestion={pendingQuestion}
          onPendingConsumed={handlePendingConsumed}
        />
      </main>
    </div>
  );
}
