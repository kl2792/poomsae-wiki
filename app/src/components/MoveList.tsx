"use client";

import type { Move } from "@/lib/data";

interface MoveListProps {
  moves: Move[];
  activeMove: number | null;
  onMoveClick: (move: Move) => void;
}

export default function MoveList({
  moves,
  activeMove,
  onMoveClick,
}: MoveListProps) {
  return (
    <div className="divide-y divide-gray-100">
      {moves.map((move) => {
        const isActive = activeMove === move.number;
        return (
          <button
            key={move.number}
            onClick={() => onMoveClick(move)}
            className={`w-full text-left px-3 py-2.5 flex items-start gap-3 transition-colors ${
              isActive
                ? "bg-blue-50 border-l-2 border-blue-600"
                : "hover:bg-gray-50 border-l-2 border-transparent"
            }`}
          >
            {/* Move number */}
            <span
              className={`text-xs font-mono w-6 pt-0.5 shrink-0 ${
                isActive ? "text-blue-600 font-bold" : "text-gray-400"
              }`}
            >
              {move.number === 0 ? "--" : String(move.number).padStart(2, "0")}
            </span>

            {/* Move info */}
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-medium truncate ${
                    isActive ? "text-blue-900" : "text-gray-900"
                  }`}
                >
                  {move.technique_id
                    .replace(/-/g, " ")
                    .replace(/\b\w/g, (c) => c.toUpperCase())}
                </span>
                {move.kihap && (
                  <span className="text-[10px] bg-red-100 text-red-700 px-1.5 py-0.5 rounded font-medium uppercase">
                    Kihap
                  </span>
                )}
              </div>
              {move.direction && move.direction !== "forward" && (
                <span className="text-xs text-gray-500">{move.direction}</span>
              )}
            </div>

            {/* Timestamp */}
            <span className="text-[11px] text-gray-400 font-mono shrink-0 pt-0.5">
              {formatTime(move.timestamp_start)}
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
