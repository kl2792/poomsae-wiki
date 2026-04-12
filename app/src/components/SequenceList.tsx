"use client";

import type { SequenceStep, Technique } from "@/lib/data";

interface SequenceListProps {
  sequence: SequenceStep[];
  techniques: Technique[];
  activeStep: number | null;
  onStepClick: (step: SequenceStep) => void;
}

export default function SequenceList({
  sequence,
  techniques,
  activeStep,
  onStepClick,
}: SequenceListProps) {
  const techMap = new Map(techniques.map((t) => [t.key, t]));

  return (
    <div className="divide-y divide-gray-100">
      {sequence.map((step) => {
        const isActive = activeStep === step.step;
        const tech = techMap.get(step.technique);
        const displayName = tech
          ? tech.name.en
          : step.technique
              .replace(/-/g, " ")
              .replace(/\b\w/g, (c) => c.toUpperCase());

        return (
          <button
            key={step.step}
            onClick={() => onStepClick(step)}
            className={`w-full text-left px-2 py-1.5 flex items-center gap-2 transition-colors ${
              isActive
                ? "bg-blue-50 border-l-2 border-blue-600"
                : "hover:bg-gray-50 border-l-2 border-transparent"
            }`}
          >
            <span
              className={`text-[11px] font-mono w-5 shrink-0 ${
                isActive ? "text-blue-600 font-bold" : "text-gray-400"
              }`}
            >
              {step.step === 0 ? "--" : String(step.step).padStart(2, "0")}
            </span>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span
                  className={`text-[13px] font-medium truncate ${
                    isActive ? "text-blue-900" : "text-gray-900"
                  }`}
                >
                  {step.side ? `${step.side.charAt(0).toUpperCase() + step.side.slice(1)} ${displayName}` : displayName}
                </span>
                {step.kihap && (
                  <span className="text-[9px] bg-red-100 text-red-700 px-1 py-0.5 rounded font-medium uppercase">
                    Kihap
                  </span>
                )}
                {step.direction && step.direction !== "forward" && (
                  <span className="text-[10px] text-gray-400">{formatDirection(step.direction)}</span>
                )}
              </div>
              <span className="text-[10px] text-gray-400">
                {tech?.name.romanized}{tech?.name.ko ? ` · ${tech.name.ko}` : ""}
              </span>
            </div>

            <span className="text-[10px] text-gray-400 font-mono shrink-0">
              {formatTime(step.timestamp)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function formatDirection(dir: string): string {
  const map: Record<string, string> = {
    "left-90": "↰ Turn left",
    "right-90": "↱ Turn right",
    "left-180": "↰ Turn left 180°",
    "right-180": "↱ Turn right 180°",
    "back": "↶ Turn around",
  };
  return map[dir] ?? dir;
}
