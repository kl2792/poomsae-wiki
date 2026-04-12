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
type SidebarView = "list" | "detail";

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
  const [sidebarView, setSidebarView] = useState<SidebarView>("list");

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
      setSidebarView("detail");

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
    setSidebarView("detail");
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

  const handleBackToList = useCallback(() => {
    setSidebarView("list");
  }, []);

  const handlePrevStep = useCallback(() => {
    if (!activeStep) return;
    const idx = form.sequence.findIndex((s) => s.step === activeStep.step);
    if (idx > 0) {
      const prev = form.sequence[idx - 1];
      setActiveStep(prev);
      setActiveTechnique(techMap.get(prev.technique) ?? null);
      setVideoStart(prev.timestamp);
      setVideoEnd(prev.timestamp_end);
      setUserClicked(true);
    }
  }, [activeStep, form.sequence, techMap]);

  const handleNextStep = useCallback(() => {
    if (!activeStep) return;
    const idx = form.sequence.findIndex((s) => s.step === activeStep.step);
    if (idx < form.sequence.length - 1) {
      const next = form.sequence[idx + 1];
      setActiveStep(next);
      setActiveTechnique(techMap.get(next.technique) ?? null);
      setVideoStart(next.timestamp);
      setVideoEnd(next.timestamp_end);
      setUserClicked(true);
    }
  }, [activeStep, form.sequence, techMap]);

  // Resolve the technique for the displayed active step
  const currentTech = displayActiveStep
    ? techMap.get(displayActiveStep.technique)
    : activeTechnique;

  // For prev/next: determine if buttons should be disabled
  const activeIdx = activeStep
    ? form.sequence.findIndex((s) => s.step === activeStep.step)
    : -1;
  const hasPrev = activeIdx > 0;
  const hasNext = activeIdx >= 0 && activeIdx < form.sequence.length - 1;

  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  /* Sidebar detail view — shown when a step/technique is selected */
  const sidebarDetailContent = currentTech ? (
    <div className="flex flex-col h-full">
      {/* Back button */}
      <button
        onClick={handleBackToList}
        className="flex items-center gap-1 px-3 py-2 text-xs text-gray-500 hover:text-gray-700 border-b border-gray-200 transition-colors"
      >
        <span>&#8592;</span> Back to list
      </button>

      {/* Scrollable detail content */}
      <div className="overflow-y-auto flex-1 min-h-0 p-3">
        {/* Step number + technique name */}
        <div className="mb-3">
          {displayActiveStep && (
            <span className="text-[11px] font-mono text-gray-400 block mb-0.5">
              Step {displayActiveStep.step}
            </span>
          )}
          <h2 className="text-base font-semibold text-gray-900">{currentTech.name.en}</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {currentTech.name.romanized}
            {currentTech.name.ko ? ` \u00b7 ${currentTech.name.ko}` : ""}
          </p>
        </div>

        {/* Direction */}
        {displayActiveStep &&
          displayActiveStep.direction &&
          displayActiveStep.direction !== "forward" && (
            <p className="text-sm text-gray-600 mb-2">
              Direction: {displayActiveStep.direction}
            </p>
          )}

        {/* Kihap badge */}
        {displayActiveStep?.kihap && (
          <span className="inline-block text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium mb-3">
            KIHAP
          </span>
        )}

        {/* Action buttons */}
        {displayActiveStep && (
          <div className="flex flex-col gap-2 mb-4">
            <button
              onClick={handleWatchPerformance}
              className="w-full text-xs px-2.5 py-2 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors text-left"
            >
              &#9654; Watch this move
            </button>
            {currentTech?.video_timestamp ? (
              <button
                onClick={handleWatchBreakdown}
                className="w-full text-xs px-2.5 py-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors text-left"
              >
                &#128214; See technique breakdown
              </button>
            ) : crossRefs[currentTech.key] ? (
              <a
                href={`/poomsae-wiki/forms/${crossRefs[currentTech.key].formId}?t=${crossRefs[currentTech.key].timestamp}`}
                className="w-full text-xs px-2.5 py-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors block text-left"
              >
                &#128214; See breakdown ({crossRefs[currentTech.key].formName})
              </a>
            ) : null}
          </div>
        )}

        {/* Tips */}
        {currentTech.tips.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Tips
            </p>
            {currentTech.tips.map((tip, i) => {
              const text = typeof tip === "string" ? tip : tip.text;
              const ts = typeof tip === "string" ? null : tip.timestamp;
              const nextTip = currentTech.tips[i + 1];
              const nextTs = nextTip && typeof nextTip !== "string" ? nextTip.timestamp : null;
              const endTs = nextTs ?? (displayActiveStep ? displayActiveStep.timestamp_end : undefined);
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

      {/* Prev / Next navigation at bottom */}
      {displayActiveStep && (
        <div className="flex border-t border-gray-200">
          <button
            onClick={handlePrevStep}
            disabled={!hasPrev}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
              hasPrev
                ? "text-gray-700 hover:bg-gray-50"
                : "text-gray-300 cursor-not-allowed"
            }`}
          >
            &#9664; Prev
          </button>
          <div className="w-px bg-gray-200" />
          <button
            onClick={handleNextStep}
            disabled={!hasNext}
            className={`flex-1 px-3 py-2 text-xs font-medium transition-colors ${
              hasNext
                ? "text-gray-700 hover:bg-gray-50"
                : "text-gray-300 cursor-not-allowed"
            }`}
          >
            Next &#9654;
          </button>
        </div>
      )}
    </div>
  ) : null;

  /* Sidebar list view — tabs, controls, scrollable list */
  const sidebarListContent = (
    <div className="flex flex-col h-full">
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
                setSidebarView("list");
                setVideoStart(form.sections!.repeat!.start + 5);
                setVideoEnd(form.sections!.repeat!.end);
              }}
              className="px-2 py-1.5 text-[11px] font-medium text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors whitespace-nowrap"
            >
              &#9654; Full run
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
            {autoPause ? "\u23f8 Step" : "\u25b6 Flow"}
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
  );

  return (
    <div className="h-[100dvh] flex flex-col overflow-hidden max-w-[1600px] mx-auto px-3 md:px-4 py-2 md:py-4">
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
      <div className="flex flex-col md:grid md:grid-cols-12 md:gap-4 flex-1 min-h-0 gap-2">

        {/* Video — mobile: capped height; desktop: fills right column */}
        <div className="flex-none md:flex-1 md:col-span-9 md:order-2 md:flex md:flex-col max-h-[35vh] md:max-h-none">
          <VideoPlayer
            videoId={form.video_id}
            startTime={videoStart}
            endTime={videoEnd}
            autoPause={autoPause}
            onTimeUpdate={handleTimeUpdate}
            onPlayingChange={setIsPlaying}
          />
        </div>

        {/* Sidebar — mobile: fills remaining space; desktop: 3/12 left column */}
        <div className="flex-1 md:col-span-3 md:order-1 flex flex-col min-h-0">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col min-h-0 flex-1">
            {sidebarView === "detail" && sidebarDetailContent
              ? sidebarDetailContent
              : sidebarListContent}
          </div>
        </div>
      </div>
    </div>
  );
}
