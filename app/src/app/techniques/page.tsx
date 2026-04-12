import Link from "next/link";
import { getAllTechniques } from "@/lib/data";
import type { WikiTechnique } from "@/lib/data";
import TechniqueSearch from "./TechniqueSearch";

const CATEGORY_ORDER = [
  "block",
  "strike",
  "kick",
  "stance",
  "ready",
  "technique",
];

const CATEGORY_LABELS: Record<string, string> = {
  block: "Blocks",
  strike: "Strikes",
  kick: "Kicks",
  stance: "Stances",
  ready: "Ready Positions",
  technique: "Other Techniques",
};

import { categoryTheme, FORM_SHORT } from "@/lib/constants";

export default function TechniquesPage() {
  const techniques = getAllTechniques();

  // Group by category
  const grouped: Record<string, WikiTechnique[]> = {};
  for (const t of techniques) {
    const cat = t.category;
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(t);
  }

  const orderedCategories = CATEGORY_ORDER.filter((c) => grouped[c]);

  // Collect all form IDs that appear in any technique
  const allFormIds = Array.from(
    new Set(techniques.flatMap((t) => t.used_in))
  ).sort((a, b) => {
    const order = Object.keys(FORM_SHORT);
    return order.indexOf(a) - order.indexOf(b);
  });

  // Build serializable data for client search component
  const searchData = techniques.map((t) => ({
    key: t.key,
    en: t.name.en,
    ko: t.name.ko,
    romanized: t.name.romanized,
    category: t.category,
    used_in: t.used_in,
    hasVideo: t.source.timestamp > 0,
  }));

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-4">
        <h1 className="text-3xl font-bold">Techniques</h1>
      </div>

      <TechniqueSearch
        techniques={searchData}
        totalCount={techniques.length}
        categories={orderedCategories}
        categoryLabels={CATEGORY_LABELS}
        formIds={allFormIds}
        formShort={FORM_SHORT}
      />

      {orderedCategories.map((cat) => (
        <section
          key={cat}
          data-category={cat}
          className="mb-8"
        >
          <button
            data-collapse-trigger={cat}
            className={`w-full flex items-center justify-between py-2.5 px-3 text-left sticky top-14 z-10 cursor-pointer select-none border-l-4 rounded-r-sm ${categoryTheme(cat).border} ${categoryTheme(cat).bg}`}
          >
            <span className="text-lg font-semibold text-gray-800">
              {CATEGORY_LABELS[cat] || cat}{" "}
              <span
                className="text-sm font-normal text-gray-400"
                data-category-count={cat}
              >
                ({grouped[cat].length})
              </span>
            </span>
            <svg
              data-chevron={cat}
              className="w-5 h-5 text-gray-500 transition-transform"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          <div data-collapse-body={cat} className="divide-y divide-gray-100">
            {grouped[cat].map((t, i) => (
              <TechniqueRow
                key={t.key}
                technique={t}
                categoryColor={
                  categoryTheme(cat).badge
                }
                even={i % 2 === 0}
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function TechniqueRow({
  technique: t,
  categoryColor,
  even,
}: {
  technique: WikiTechnique;
  categoryColor: string;
  even: boolean;
}) {
  const tipCount = t.tips.length;

  return (
    <Link
      href={`/techniques/${t.key}`}
      data-technique={t.key}
      data-forms={t.used_in.join(",")}
      className={`flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors group ${even ? "bg-white" : "bg-gray-50/50"}`}
    >
      {/* Name block */}
      <div className="flex-1 min-w-0 flex items-baseline gap-2 overflow-hidden">
        <span className="font-semibold text-sm text-gray-900 whitespace-nowrap">
          {t.name.en}
        </span>
        <span className="text-xs text-gray-400 truncate">
          {t.name.romanized} · {t.name.ko}
        </span>
      </div>

      {/* Tip count badge */}
      {tipCount > 0 && (
        <span className="text-[11px] font-medium px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 shrink-0">
          {tipCount} {tipCount === 1 ? "tip" : "tips"}
        </span>
      )}

      {/* Video status debug badge */}
      {t.source.timestamp === 0 ? (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-red-50 text-red-400 shrink-0" data-has-video="false">
          no video
        </span>
      ) : (
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-400 shrink-0 hidden" data-has-video="true">
          has video
        </span>
      )}

      {/* Category pill */}
      <span
        className={`hidden sm:inline text-[11px] px-2 py-0.5 rounded-full font-medium shrink-0 ${categoryColor}`}
      >
        {t.category}
      </span>

      {/* Form tags */}
      <div className="hidden md:flex gap-1 shrink-0">
        {t.used_in.map((formId) => (
          <span
            key={formId}
            className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium whitespace-nowrap"
          >
            {FORM_SHORT[formId] || formId}
          </span>
        ))}
      </div>

      {/* Arrow */}
      <svg
        className="w-4 h-4 text-gray-400 group-hover:text-blue-500 shrink-0 transition-colors"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9 5l7 7-7 7"
        />
      </svg>
    </Link>
  );
}
