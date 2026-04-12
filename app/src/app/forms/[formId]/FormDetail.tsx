"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import type { FormData, SequenceStep, Technique } from "@/lib/data";
import VideoPlayer from "@/components/VideoPlayer";
import SequenceList from "@/components/SequenceList";
import TechniqueList from "@/components/TechniqueList";

export interface CrossRef {
  formId: string;
  formName: string;
  timestamp: number;
}

type Tab = "sequence" | "techniques";

interface FormDetailProps {
  form: FormData;
  crossRefs?: Record<string, CrossRef>;
}

export default function FormDetail({ form, crossRefs = {} }: FormDetailProps) {
  const [tab, setTab] = useState<Tab>("sequence");
  const [activeStep, setActiveStep] = useState<SequenceStep | null>(null);
  const [activeTechnique, setActiveTechnique] = useState<Technique | null>(null);
  const [videoStart, setVideoStart] = useState<number | undefined>();
  const [videoEnd, setVideoEnd] = useState<number | undefined>();
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0);
  const [userClicked, setUserClicked] = useState(false);
  const [autoPause, setAutoPause] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);

  // Handle ?t= query param from cross-reference links
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const t = params.get("t");
    if (t) {
      const seconds = parseFloat(t);
      if (!isNaN(seconds) && seconds > 0) {
        setVideoStart(seconds);
      }
    }
  }, []);

  const techMap = useMemo(
    () => new Map(form.techniques.map((t) => [t.key, t])),
    [form.techniques]
  );

  const occurrences = useMemo(() => {
    const counts = new Map<string, number>();
    for (const s of form.sequence) {
      counts.set(s.technique, (counts.get(s.technique) ?? 0) + 1);
    }
    return counts;
  }, [form.sequence]);

  // Auto-highlight: find which step matches current video time
  const trackedStep = useMemo(() => {
    if (userClicked) return null; // don't override user selection
    return form.sequence.find(
      (s) => currentVideoTime >= s.timestamp && currentVideoTime < s.timestamp_end
    ) ?? null;
  }, [currentVideoTime, form.sequence, userClicked]);

  // The displayed active step: user-clicked takes priority, else auto-tracked
  const displayActiveStep = userClicked ? activeStep : (trackedStep ?? activeStep);

  const handleTimeUpdate = useCallback((time: number) => {
    setCurrentVideoTime(time);
    // Clear user click after video moves past the clicked segment
    if (userClicked && activeStep && time >= activeStep.timestamp_end) {
      setUserClicked(false);
    }
  }, [userClicked, activeStep]);

  const handleStepClick = useCallback(
    (step: SequenceStep) => {
      const prevStep = activeStep;
      setActiveStep(step);
      setActiveTechnique(techMap.get(step.technique) ?? null);
      setVideoEnd(step.timestamp_end);
      setUserClicked(true);

      // If clicking the next sequential step, just resume — don't seek
      const isNextStep = prevStep && step.step === prevStep.step + 1;
      if (!isNextStep) {
        setVideoStart(step.timestamp);
      }
    },
    [techMap, activeStep]
  );

  const handleTechniqueClick = useCallback((tech: Technique) => {
    setActiveTechnique(tech);
    setActiveStep(null);
    setVideoStart(tech.video_timestamp);
    setVideoEnd(undefined);
    setUserClicked(true);
  }, []);

  const handleWatchBreakdown = useCallback(() => {
    if (!activeTechnique) return;
    setVideoStart(activeTechnique.video_timestamp);
    setVideoEnd(undefined);
  }, [activeTechnique]);

  const handleWatchPerformance = useCallback(() => {
    if (!activeStep) return;
    setVideoStart(activeStep.timestamp);
    setVideoEnd(activeStep.timestamp_end);
  }, [activeStep]);

  // Resolve the technique for the displayed active step
  const currentTech = displayActiveStep
    ? techMap.get(displayActiveStep.technique)
    : activeTechnique;

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  /* Shared technique detail panel — rendered in two places (mobile vs desktop) */
  const techniqueDetail = currentTech ? (
    <div className="p-3 md:p-4 bg-white rounded-lg border border-gray-200">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {activeStep && (
          <span className="text-xs font-mono text-gray-400">
            Step {activeStep.step}
          </span>
        )}
        <h2 className="font-semibold">{currentTech.name.en}</h2>
        <span className="text-xs text-gray-400">
          {currentTech.name.ko}
        </span>
        {activeStep?.kihap && (
          <span className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium">
            KIHAP
          </span>
        )}
      </div>

      {activeStep &&
        activeStep.direction &&
        activeStep.direction !== "forward" && (
          <p className="text-sm text-gray-600 mb-2">
            Direction: {activeStep.direction}
          </p>
        )}

      {/* Action buttons when a sequence step is selected */}
      {activeStep && (
        <div className="flex gap-2 mb-3">
          <button
            onClick={handleWatchPerformance}
            className="text-xs px-2.5 py-1.5 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
          >
            Watch this move
          </button>
          {currentTech?.video_timestamp ? (
            <button
              onClick={handleWatchBreakdown}
              className="text-xs px-2.5 py-1.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
            >
              See technique breakdown
            </button>
          ) : crossRefs[currentTech.key] ? (
            <a
              href={`/poomsae-wiki/forms/${crossRefs[currentTech.key].formId}?t=${crossRefs[currentTech.key].timestamp}`}
              className="text-xs px-2.5 py-1.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors inline-block"
            >
              See breakdown ({crossRefs[currentTech.key].formName})
            </a>
          ) : null}
        </div>
      )}

      {currentTech.tips.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
            Tips
          </p>
          {currentTech.tips.map((tip, i) => {
            const text = typeof tip === "string" ? tip : tip.text;
            const ts = typeof tip === "string" ? null : tip.timestamp;
            // End = next tip's start, or technique's end
            const nextTip = currentTech.tips[i + 1];
            const nextTs = nextTip && typeof nextTip !== "string" ? nextTip.timestamp : null;
            const endTs = nextTs ?? (activeStep ? activeStep.timestamp_end : undefined);
            return (
              <button
                key={i}
                onClick={() => {
                  if (ts) {
                    setVideoStart(ts);
                    setVideoEnd(endTs ?? undefined);
                  }
                }}
                className={`block w-full text-left text-sm text-gray-700 pl-3 border-l-2 border-blue-200 ${ts ? "hover:text-blue-600 hover:border-blue-400 cursor-pointer" : ""}`}
              >
                {text}
                {ts && <span className="text-[10px] text-gray-400 ml-2">{formatTime(ts)}</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  ) : null;

  return (
    <div className="h-[100dvh] flex flex-col overflow-hidden max-w-6xl mx-auto px-3 md:px-4 py-2 md:py-4">
      {/* Header */}
      <div className="mb-2 md:mb-4 flex-none">
        <h1 className="text-lg md:text-2xl font-bold">{form.name.en}</h1>
        <div className="flex items-center gap-2 md:gap-3 mt-0.5 md:mt-1 text-xs md:text-sm text-gray-500 flex-wrap">
          <span>{form.name.ko}</span>
          {form.meaning && <span>&middot; {form.meaning.en}</span>}
          {form.belt && <span>&middot; {form.belt}</span>}
          <span>
            &middot; {form.total_moves} moves &middot;{" "}
            {form.techniques.length} techniques
          </span>
        </div>
      </div>

      {/* Main content — mobile: flex col; desktop: grid sidebar-left video-right */}
      <div className="flex flex-col md:grid md:grid-cols-10 md:gap-6 flex-1 min-h-0 gap-2">

        {/* Video — mobile: capped height; desktop: scrollable column */}
        <div className="flex-none md:flex-1 md:col-span-6 md:order-2 md:overflow-y-auto max-h-[35vh] md:max-h-none">
          <VideoPlayer
            videoId={form.video_id}
            startTime={videoStart}
            endTime={videoEnd}
            autoPause={autoPause}
            onTimeUpdate={handleTimeUpdate}
            onPlayingChange={setIsPlaying}
          />

          {/* Technique detail: desktop only (inside video column) */}
          <div className="hidden md:block mt-4">
            {techniqueDetail}
          </div>
        </div>

        {/* Technique detail: mobile only (between video and sidebar) */}
        {techniqueDetail && (
          <div className="flex-none md:hidden">
            {techniqueDetail}
          </div>
        )}

        {/* Sidebar — mobile: fills remaining space; desktop: 3/10 left column */}
        <div className="flex-1 md:col-span-4 md:order-1 flex flex-col min-h-0">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col min-h-0 flex-1">
            {/* Tabs + autopause toggle */}
            <div className="flex border-b border-gray-200">
              <button
                onClick={() => setTab("sequence")}
                className={`flex-1 px-3 py-2 text-xs font-medium uppercase tracking-wide transition-colors ${
                  tab === "sequence"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50/50"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Sequence ({form.sequence.length})
              </button>
              <button
                onClick={() => setTab("techniques")}
                className={`flex-1 px-3 py-2 text-xs font-medium uppercase tracking-wide transition-colors ${
                  tab === "techniques"
                    ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50/50"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                Techniques ({form.techniques.length})
              </button>
              <div className="flex items-center gap-1 self-center mr-1">
                {form.sections?.repeat && (
                  <button
                    onClick={() => {
                      setActiveStep(null);
                      setActiveTechnique(null);
                      setVideoStart(form.sections!.repeat!.start + 5);
                      setVideoEnd(form.sections!.repeat!.end);
                    }}
                    className="px-2 py-1.5 text-[11px] font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors whitespace-nowrap"
                  >
                    ▶ Full run
                  </button>
                )}
                <button
                  onClick={() => setAutoPause((v) => !v)}
                  className={`group relative px-2.5 py-1.5 text-[11px] font-medium rounded-md transition-all whitespace-nowrap border ${
                    autoPause
                      ? `border-blue-200 bg-blue-50 text-blue-700 ${isPlaying ? "ring-1 ring-blue-300 animate-pulse" : ""}`
                      : `border-green-200 bg-green-50 text-green-700 ${isPlaying ? "ring-1 ring-green-300" : ""}`
                  }`}
                >
                  {autoPause ? "⏸ Step" : "▶ Flow"}
                  <span className="absolute hidden group-hover:block bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 text-[10px] text-white bg-gray-800 rounded whitespace-nowrap z-10">
                    {autoPause ? "Pauses after each move" : "Plays through, sidebar tracks"}
                  </span>
                </button>
              </div>
            </div>

            <div className="overflow-y-auto flex-1 min-h-0">
              {tab === "sequence" ? (
                <SequenceList
                  sequence={form.sequence}
                  techniques={form.techniques}
                  activeStep={displayActiveStep?.step ?? null}
                  onStepClick={handleStepClick}
                />
              ) : (
                <TechniqueList
                  techniques={form.techniques}
                  occurrences={occurrences}
                  activeTechnique={activeTechnique?.key ?? null}
                  onTechniqueClick={handleTechniqueClick}
                />
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
