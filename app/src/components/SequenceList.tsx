"use client";

import { useEffect, useRef } from "react";
import type { SequenceStep, Technique } from "@/lib/data";
import { formatTime } from "@/lib/format";

interface SequenceListProps {
  sequence: SequenceStep[];
  techMap: Map<string, Technique>;
  activeStep: number | null;
  onStepClick: (step: SequenceStep) => void;
}

export default function SequenceList({
  sequence,
  techMap,
  activeStep,
  onStepClick,
}: SequenceListProps) {
  const activeRef = useRef<HTMLButtonElement>(null);

  // Auto-scroll to active step when it changes
  useEffect(() => {
    if (activeStep == null || !activeRef.current) return;
    activeRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [activeStep]);

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
            ref={isActive ? activeRef : undefined}
            onClick={() => onStepClick(step)}
            className={`w-full text-left px-2 py-2.5 min-h-[44px] flex items-center gap-2 transition-colors ${
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
              <div className="flex items-start gap-1.5">
                <span
                  className={`text-[12px] font-medium ${
                    isActive ? "text-blue-900" : "text-gray-900"
                  }`}
                >
                  {step.side ? `${abbreviateSide(step.side)} ${displayName}` : displayName}
                </span>
                {step.kihap && (
                  <span className="text-[9px] bg-red-100 text-red-700 px-1 py-0.5 rounded font-medium uppercase shrink-0">
                    Kihap
                  </span>
                )}
              </div>
              <span className="text-[10px] text-gray-400">
                {tech?.name.romanized}{tech?.name.ko ? ` · ${tech.name.ko}` : ""}
                {step.direction && step.direction !== "forward" && ` · ${formatDirection(step.direction)}`}
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

function abbreviateSide(side: string): string {
  if (side === "left") return "L";
  if (side === "right") return "R";
  return side.charAt(0).toUpperCase() + side.slice(1);
}

function formatDirection(dir: string): string {
  const map: Record<string, string> = {
    "left-90": "\u21b0 Turn left",
    "right-90": "\u21b1 Turn right",
    "left-180": "\u21b0 Turn left 180\u00b0",
    "right-180": "\u21b1 Turn right 180\u00b0",
    "back": "\u21b6 Turn around",
  };
  return map[dir] ?? dir;
}
