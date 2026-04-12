"use client";

import type { Technique } from "@/lib/data";
import { CATEGORY_COLORS } from "@/lib/constants";

interface TechniqueListProps {
  techniques: Technique[];
  occurrences: Map<string, number>;
  activeTechnique: string | null;
  onTechniqueClick: (technique: Technique) => void;
}

export default function TechniqueList({
  techniques,
  occurrences,
  activeTechnique,
  onTechniqueClick,
}: TechniqueListProps) {
  return (
    <div className="divide-y divide-gray-100">
      {techniques.map((tech) => {
        const isActive = activeTechnique === tech.key;
        const count = occurrences.get(tech.key) ?? 0;
        const catColor = CATEGORY_COLORS[tech.category] ?? "bg-gray-100 text-gray-600";

        return (
          <button
            key={tech.key}
            onClick={() => onTechniqueClick(tech)}
            className={`w-full text-left px-3 py-2.5 flex items-start gap-3 transition-colors ${
              isActive
                ? "bg-blue-50 border-l-2 border-blue-600"
                : "hover:bg-gray-50 border-l-2 border-transparent"
            }`}
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-medium truncate ${
                    isActive ? "text-blue-900" : "text-gray-900"
                  }`}
                >
                  {tech.name.en}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${catColor}`}>
                  {tech.category}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                {tech.name.romanized && (
                  <span className="text-[11px] text-gray-400">{tech.name.romanized}</span>
                )}
                <span className="text-[11px] text-gray-300">{tech.name.ko}</span>
              </div>
            </div>

            <span className="text-xs text-gray-400 shrink-0 pt-0.5">
              {count}x
            </span>
          </button>
        );
      })}
    </div>
  );
}
