"use client";

import { useState, useCallback, useMemo } from "react";
import type { FormData, SequenceStep, Technique } from "@/lib/data";
import VideoPlayer from "@/components/VideoPlayer";
import SequenceList from "@/components/SequenceList";
import TechniqueList from "@/components/TechniqueList";

type Tab = "sequence" | "techniques";

export default function FormDetail({ form }: { form: FormData }) {
  const [tab, setTab] = useState<Tab>("sequence");
  const [activeStep, setActiveStep] = useState<SequenceStep | null>(null);
  const [activeTechnique, setActiveTechnique] = useState<Technique | null>(null);
  const [videoStart, setVideoStart] = useState<number | undefined>();
  const [videoEnd, setVideoEnd] = useState<number | undefined>();
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0);
  const [userClicked, setUserClicked] = useState(false);

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

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{form.name.en}</h1>
        <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
          <span>{form.name.ko}</span>
          {form.meaning && <span>&middot; {form.meaning.en}</span>}
          {form.belt && <span>&middot; {form.belt}</span>}
          <span>
            &middot; {form.total_moves} moves &middot;{" "}
            {form.techniques.length} techniques
          </span>
        </div>
      </div>

      {/* Main content: list + video */}
      <div className="grid grid-cols-1 md:grid-cols-10 gap-6">
        {/* Video (7/10 width on desktop, appears second in DOM but visually right) */}
        <div className="md:col-span-7 md:order-2">
          <VideoPlayer
            videoId={form.video_id}
            startTime={videoStart}
            endTime={videoEnd}
            onTimeUpdate={handleTimeUpdate}
          />

          {/* Active item details */}
          {currentTech && (
            <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
              <div className="flex items-center gap-2 mb-2">
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
                  <button
                    onClick={handleWatchBreakdown}
                    className="text-xs px-2.5 py-1.5 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
                  >
                    See technique breakdown
                  </button>
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
          )}
        </div>

        {/* Sidebar (3/10 width on desktop, scrollable, appears first/left) */}
        <div className="md:col-span-3 md:order-1">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {/* Tabs */}
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
            </div>

            <div className="max-h-[70vh] overflow-y-auto">
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

          {/* Quick links to video sections */}
          {form.sections?.repeat && (
            <div className="mt-3 text-sm">
              <span className="text-gray-400">Jump to: </span>
              <button
                onClick={() => {
                  setActiveStep(null);
                  setActiveTechnique(null);
                  setVideoStart(form.sections!.repeat!.start + 5);
                  setVideoEnd(form.sections!.repeat!.end);
                }}
                className="text-blue-600 hover:underline"
              >
                Full-speed run
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
