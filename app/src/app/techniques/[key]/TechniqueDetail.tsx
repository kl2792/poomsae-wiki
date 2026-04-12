"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import type { WikiTechnique } from "@/lib/data";
import { categoryTheme, formDisplayName } from "@/lib/constants";
import { formatTime } from "@/lib/format";
import VideoPlayer from "@/components/VideoPlayer";

interface TechniqueDetailProps {
  technique: WikiTechnique;
}

export default function TechniqueDetail({
  technique: t,
}: TechniqueDetailProps) {
  const hasVideo = t.source.timestamp > 0;
  const [videoStart, setVideoStart] = useState<number | undefined>(
    hasVideo ? t.source.timestamp : undefined
  );
  const [videoEnd, setVideoEnd] = useState<number | undefined>(
    t.source.timestamp_end
  );

  const handleTipClick = useCallback(
    (timestamp: number) => {
      setVideoStart(timestamp);
      setVideoEnd(undefined);
    },
    []
  );

  const categoryColor = categoryTheme(t.category).badge;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Back link */}
      <Link
        href="/techniques"
        className="text-sm text-gray-500 hover:text-gray-700 mb-4 inline-block"
      >
        &larr; All techniques
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl md:text-3xl font-bold">{t.name.en}</h1>
          <span
            className={`text-xs px-2 py-0.5 rounded font-medium ${categoryColor}`}
          >
            {t.category}
          </span>
        </div>
        <p className="text-gray-500">
          {t.name.romanized}
          <span className="ml-2 text-gray-400">{t.name.ko}</span>
        </p>
      </div>

      {/* Main content: video + details */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Video */}
        <div className="lg:w-[60%] flex-shrink-0">
          {hasVideo ? (
            <VideoPlayer
              videoId={t.source.video_id}
              startTime={videoStart}
              endTime={videoEnd}
              autoPause={false}
            />
          ) : (
            <div className="w-full aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 text-sm">
              No video breakdown available
            </div>
          )}
          {hasVideo && (
            <p className="text-xs text-gray-400 mt-2">
              From{" "}
              <Link
                href={`/forms/${t.source.form_id}`}
                className="underline hover:text-gray-600"
              >
                {t.source.form_name}
              </Link>
              {" "}at {formatTime(t.source.timestamp)}
            </p>
          )}
        </div>

        {/* Details sidebar */}
        <div className="flex-1 space-y-6">
          {/* Tips */}
          {t.tips.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-2">Tips</h2>
              <ul className="space-y-2">
                {t.tips.map((tip, i) => {
                  const hasTimestamp =
                    tip.timestamp !== undefined && tip.timestamp > 0;
                  return (
                    <li key={i} className="flex gap-2 text-sm">
                      {hasTimestamp ? (
                        <button
                          onClick={() => handleTipClick(tip.timestamp!)}
                          className="text-blue-600 hover:text-blue-800 font-mono text-xs whitespace-nowrap mt-0.5"
                        >
                          {formatTime(tip.timestamp!)}
                        </button>
                      ) : (
                        <span className="text-gray-300 font-mono text-xs whitespace-nowrap mt-0.5">
                          --:--
                        </span>
                      )}
                      <span className="text-gray-700">{tip.text}</span>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Used in */}
          {t.used_in.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-2">
                Used in
              </h2>
              <div className="flex flex-wrap gap-2">
                {t.used_in.map((formId) => (
                  <Link
                    key={formId}
                    href={`/forms/${formId}`}
                    className="text-xs px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-700"
                  >
                    {formDisplayName(formId)}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
