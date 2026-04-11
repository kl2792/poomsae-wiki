"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/* eslint-disable @typescript-eslint/no-explicit-any */
declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

interface VideoPlayerProps {
  videoId: string;
  startTime?: number;
  endTime?: number;
  onTimeUpdate?: (time: number) => void;
}

const SPEEDS = [0.25, 0.5, 0.75, 1, 1.25, 1.5];

export default function VideoPlayer({
  videoId,
  startTime,
  endTime,
  onTimeUpdate,
}: VideoPlayerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [ready, setReady] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [playing, setPlaying] = useState(false);

  // Load YouTube IFrame API
  useEffect(() => {
    if (window.YT?.Player) {
      setReady(true);
      return;
    }
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(tag);
    window.onYouTubeIframeAPIReady = () => setReady(true);
  }, []);

  // Create player
  useEffect(() => {
    if (!ready || !containerRef.current) return;
    if (playerRef.current) {
      playerRef.current.destroy();
    }

    playerRef.current = new window.YT.Player(containerRef.current, {
      videoId,
      playerVars: {
        modestbranding: 1,
        rel: 0,
        start: startTime ? Math.floor(startTime) : undefined,
      },
      events: {
        onStateChange: (e: any) => {
          setPlaying(e.data === window.YT.PlayerState.PLAYING);
        },
      },
    });

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [ready, videoId]);

  // Seek when startTime changes
  useEffect(() => {
    if (playerRef.current && startTime !== undefined) {
      playerRef.current.seekTo(startTime, true);
      playerRef.current.playVideo();
    }
  }, [startTime]);

  // Monitor playback to auto-pause at endTime
  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (!playing || endTime === undefined) return;

    intervalRef.current = setInterval(() => {
      if (!playerRef.current) return;
      const current = playerRef.current.getCurrentTime();
      onTimeUpdate?.(current);
      if (current >= endTime) {
        playerRef.current.pauseVideo();
      }
    }, 200);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, endTime, onTimeUpdate]);

  const handleSpeedChange = useCallback((newSpeed: number) => {
    setSpeed(newSpeed);
    playerRef.current?.setPlaybackRate(newSpeed);
  }, []);

  const seekTo = useCallback((time: number) => {
    playerRef.current?.seekTo(time, true);
    playerRef.current?.playVideo();
  }, []);

  return (
    <div className="space-y-2">
      {/* Video embed */}
      <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
        <div ref={containerRef} className="absolute inset-0" />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500 text-xs">Speed:</span>
        {SPEEDS.map((s) => (
          <button
            key={s}
            onClick={() => handleSpeedChange(s)}
            className={`px-2 py-0.5 rounded text-xs font-mono ${
              speed === s
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {s}x
          </button>
        ))}
      </div>
    </div>
  );
}
