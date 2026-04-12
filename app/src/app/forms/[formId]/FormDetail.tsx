"use client";

import { useState, useCallback, useEffect, useMemo } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import type { FormData, SequenceStep, Technique, WikiTechnique } from "@/lib/data";
import { formatTime } from "@/lib/format";
import { formDisplayName } from "@/lib/constants";
import VideoPlayer from "@/components/VideoPlayer";
import SequenceList from "@/components/SequenceList";
import TechniqueList from "@/components/TechniqueList";

type Tab = "sequence" | "techniques";
type SidebarView = "list" | "detail";

interface FormDetailProps {
  form: FormData;
  wikiTechniques?: Record<string, WikiTechnique>;
}

// --- SidebarDetail: extracted from the inline sidebarDetailContent blob ---

interface SidebarDetailProps {
  currentTech: Technique;
  displayActiveStep: SequenceStep | null;
  form: FormData;
  wikiTechniques: Record<string, WikiTechnique>;
  hasPrev: boolean;
  hasNext: boolean;
  isLooping: boolean;
  onBack: () => void;
  onWatchPerformance: () => void;
  onWatchBreakdown: () => void;
  onStepNav: (direction: -1 | 1) => void;
  onToggleLoop: () => void;
  onSeek: (start: number, end?: number) => void;
}

function SidebarDetail({
  currentTech,
  displayActiveStep,
  form,
  wikiTechniques,
  hasPrev,
  hasNext,
  isLooping,
  onBack,
  onWatchPerformance,
  onWatchBreakdown,
  onStepNav,
  onToggleLoop,
  onSeek,
}: SidebarDetailProps) {
  const wiki = wikiTechniques[currentTech.key];
  const wikiSource = wiki?.source;
  const sourceIsThisForm = wikiSource?.form_id === form.id;
  const hasLocalBreakdown = currentTech.video_timestamp > 0;
  const hasBreakdown = hasLocalBreakdown || (wikiSource && wikiSource.timestamp > 0);

  const tips = wiki && wiki.tips.length > 0 ? wiki.tips : currentTech.tips ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Back button */}
      <button
        onClick={onBack}
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
          <h2 className="text-base font-semibold text-gray-900 break-words">{currentTech.name.en}</h2>
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
            <div className="flex gap-2">
              <button
                onClick={onWatchPerformance}
                className="flex-1 text-xs px-2.5 py-2 rounded bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors text-left"
              >
                &#9654; Watch this move
              </button>
              <button
                onClick={onToggleLoop}
                className={`text-xs px-2.5 py-2 rounded transition-colors shrink-0 ${
                  isLooping
                    ? "bg-blue-600 text-white"
                    : "bg-blue-50 text-blue-700 hover:bg-blue-100"
                }`}
                title={isLooping ? "Stop looping" : "Loop this move"}
              >
                &#128257; Loop
              </button>
            </div>
            {hasBreakdown && (sourceIsThisForm || hasLocalBreakdown) ? (
              <button
                onClick={onWatchBreakdown}
                className="w-full text-xs px-2.5 py-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors text-left"
              >
                &#128214; See technique breakdown
              </button>
            ) : wikiSource && wikiSource.timestamp > 0 ? (
              <Link
                href={`/forms/${wikiSource.form_id}?t=${wikiSource.timestamp}`}
                className="w-full text-xs px-2.5 py-2 rounded bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors block text-left"
              >
                &#128214; See breakdown ({wikiSource.form_name})
              </Link>
            ) : null}
          </div>
        )}

        {/* Used in (from wiki) */}
        {wiki?.used_in && wiki.used_in.length > 1 && (
          <div className="mb-3">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
              Also in
            </p>
            <div className="flex flex-wrap gap-1">
              {wiki.used_in
                .filter((fid: string) => fid !== form.id)
                .map((fid: string) => (
                  <Link
                    key={fid}
                    href={`/forms/${fid}`}
                    className="text-[11px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-700 transition-colors"
                  >
                    {formDisplayName(fid)}
                  </Link>
                ))}
            </div>
          </div>
        )}

        {/* Tips — prefer wiki tips (richer, merged from all forms) */}
        {tips.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
              Tips
            </p>
            {tips.map((tip: { text: string; timestamp?: number; video_id?: string; source?: string } | string, i: number) => {
              const text = typeof tip === "string" ? tip : tip.text;
              const ts = typeof tip === "string" ? null : (tip as { timestamp?: number }).timestamp ?? null;
              const nextTip = tips[i + 1];
              const nextTs = nextTip && typeof nextTip !== "string" ? (nextTip as { timestamp?: number }).timestamp ?? null : null;
              const endTs = nextTs ?? (displayActiveStep ? displayActiveStep.timestamp_end : undefined);
              const tipVideoId = typeof tip !== "string" ? (tip as { video_id?: string }).video_id : undefined;
              const tipSource = typeof tip !== "string" ? (tip as { source?: string }).source : undefined;
              const isCaption = tipSource === "caption";
              const canSeek = ts != null && (!tipVideoId || tipVideoId === form.video_id);
              const tipClass = `block w-full text-left text-sm pl-3 border-l-2 ${isCaption ? "text-gray-400 border-gray-200" : "text-gray-700 border-blue-200"}`;
              const prefix = isCaption ? "🎤 " : "";
              return canSeek ? (
                <button
                  key={i}
                  onClick={() => { if (ts) onSeek(ts, endTs ?? undefined); }}
                  className={`${tipClass} hover:text-blue-600 hover:border-blue-400 cursor-pointer flex items-start gap-2`}
                >
                  {ts && <span className="text-[10px] text-gray-400 font-mono whitespace-nowrap mt-0.5 shrink-0 w-8">{formatTime(ts)}</span>}
                  <span>{prefix}{text}</span>
                </button>
              ) : (
                <p key={i} className={tipClass}>
                  {prefix}{text}
                </p>
              );
            })}
          </div>
        )}
      </div>

      {/* Prev / Next navigation at bottom */}
      {displayActiveStep && (
        <div className="flex border-t border-gray-200">
          <button
            onClick={() => onStepNav(-1)}
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
            onClick={() => onStepNav(1)}
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
  );
}

// --- Main FormDetail component ---

export default function FormDetail({ form, wikiTechniques = {} }: FormDetailProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Read initial state from URL params
  const initialTab = (searchParams.get("tab") === "techniques" ? "techniques" : "sequence") as Tab;
  const initialStepNum = searchParams.get("step") ? parseInt(searchParams.get("step")!, 10) : null;
  const initialMode = searchParams.get("mode") === "flow" ? false : true; // flow = autoPause off
  const initialT = searchParams.get("t") ? parseFloat(searchParams.get("t")!) : undefined;

  const [tab, setTab] = useState<Tab>(initialTab);
  const [activeStep, setActiveStep] = useState<SequenceStep | null>(null);
  const [activeTechnique, setActiveTechnique] = useState<Technique | null>(null);
  const [videoStart, setVideoStart] = useState<number | undefined>(
    initialT && !isNaN(initialT) && initialT > 0 ? initialT : undefined
  );
  const [videoEnd, setVideoEnd] = useState<number | undefined>();
  const [currentVideoTime, setCurrentVideoTime] = useState<number>(0);
  const [userClicked, setUserClicked] = useState(false);
  const [autoPause, setAutoPause] = useState(initialMode);
  const [isPlaying, setIsPlaying] = useState(false);
  const [sidebarView, setSidebarView] = useState<SidebarView>("list");
  const [isLooping, setIsLooping] = useState(false);

  // Update URL params without navigation
  const updateUrl = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());
      for (const [key, value] of Object.entries(updates)) {
        if (value === null) {
          params.delete(key);
        } else {
          params.set(key, value);
        }
      }
      const qs = params.toString();
      router.replace(pathname + (qs ? "?" + qs : ""), { scroll: false });
    },
    [searchParams, router, pathname]
  );

  const techMap = useMemo(
    () => new Map(form.techniques.map((t) => [t.key, t])),
    [form.techniques]
  );

  // Initialize step from URL on mount
  useEffect(() => {
    if (initialStepNum == null || isNaN(initialStepNum)) return;
    const step = form.sequence.find((s) => s.step === initialStepNum);
    if (step) {
      setActiveStep(step);
      setActiveTechnique(techMap.get(step.technique) ?? null);
      setUserClicked(true);
      setSidebarView("detail");
      setVideoStart(step.timestamp);
      setVideoEnd(step.timestamp_end);
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      setIsLooping(false);

      // If clicking the next sequential step, just resume — don't seek
      const isNextStep = prevStep && step.step === prevStep.step + 1;
      if (!isNextStep) {
        setVideoStart(step.timestamp);
      }

      updateUrl({ step: String(step.step), t: null });
    },
    [techMap, activeStep, updateUrl]
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
    const wiki = wikiTechniques[activeTechnique.key];
    // If wiki source is this form, seek locally; otherwise use the form's own timestamp
    if (wiki && wiki.source.form_id === form.id) {
      setVideoStart(wiki.source.timestamp);
    } else if (activeTechnique.video_timestamp > 0) {
      setVideoStart(activeTechnique.video_timestamp);
    }
    setVideoEnd(undefined);
  }, [activeTechnique, wikiTechniques, form.id]);

  const handleWatchPerformance = useCallback(() => {
    if (!activeStep) return;
    setVideoStart(activeStep.timestamp);
    setVideoEnd(activeStep.timestamp_end);
  }, [activeStep]);

  const handleBackToList = useCallback(() => {
    setSidebarView("list");
    updateUrl({ step: null });
  }, [updateUrl]);

  const handleTabSwitch = useCallback((newTab: Tab) => {
    setTab(newTab);
    updateUrl({ tab: newTab === "sequence" ? null : newTab });
  }, [updateUrl]);

  const handleModeToggle = useCallback(() => {
    setAutoPause((v) => {
      const next = !v;
      updateUrl({ mode: next ? null : "flow" });
      return next;
    });
  }, [updateUrl]);

  const handleStepNav = useCallback((direction: -1 | 1) => {
    if (!activeStep) return;
    const idx = form.sequence.findIndex((s) => s.step === activeStep.step);
    const targetIdx = idx + direction;
    if (targetIdx < 0 || targetIdx >= form.sequence.length) return;
    handleStepClick(form.sequence[targetIdx]);
  }, [activeStep, form.sequence, handleStepClick]);

  const handleToggleLoop = useCallback(() => {
    setIsLooping((prev) => {
      const next = !prev;
      if (next) handleWatchPerformance();
      return next;
    });
  }, [handleWatchPerformance]);

  const handleSeek = useCallback((start: number, end?: number) => {
    setVideoStart(start);
    setVideoEnd(end);
  }, []);

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

  /* Sidebar list view — tabs, controls, scrollable list */
  const sidebarListContent = (
    <div className="flex flex-col h-full">
      {/* Tabs + autopause toggle */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => handleTabSwitch("sequence")}
          className={`flex-1 px-3 py-2 text-xs font-medium uppercase tracking-wide transition-colors ${
            tab === "sequence"
              ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50/50"
              : "text-gray-500 hover:text-gray-700"
          }`}
        >
          Sequence ({form.sequence.length})
        </button>
        <button
          onClick={() => handleTabSwitch("techniques")}
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
            onClick={handleModeToggle}
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
            techMap={techMap}
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
            loop={isLooping}
            onTimeUpdate={handleTimeUpdate}
            onPlayingChange={setIsPlaying}
          />
        </div>

        {/* Sidebar — mobile: fills remaining space; desktop: 3/12 left column */}
        <div className="flex-1 md:col-span-3 md:order-1 flex flex-col min-h-0">
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden flex flex-col min-h-0 flex-1">
            {sidebarView === "detail" && currentTech ? (
              <SidebarDetail
                currentTech={currentTech}
                displayActiveStep={displayActiveStep}
                form={form}
                wikiTechniques={wikiTechniques}
                hasPrev={hasPrev}
                hasNext={hasNext}
                isLooping={isLooping}
                onBack={handleBackToList}
                onWatchPerformance={handleWatchPerformance}
                onWatchBreakdown={handleWatchBreakdown}
                onStepNav={handleStepNav}
                onToggleLoop={handleToggleLoop}
                onSeek={handleSeek}
              />
            ) : (
              sidebarListContent
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
