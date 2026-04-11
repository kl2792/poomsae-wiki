"use client";

import type { Technique } from "@/lib/data";

interface TechniqueListProps {
  techniques: Technique[];
  occurrences: Map<string, number>;
  activeTechnique: string | null;
  onTechniqueClick: (technique: Technique) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  block: "bg-blue-50 text-blue-700",
  strike: "bg-orange-50 text-orange-700",
  kick: "bg-green-50 text-green-700",
  stance: "bg-gray-100 text-gray-600",
};

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
              <span className="text-xs text-gray-400">{tech.name.ko}</span>
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
