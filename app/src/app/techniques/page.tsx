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

import { CATEGORY_COLORS } from "@/lib/constants";

/** Short display name for form filter pills and row tags. */
const FORM_SHORT: Record<string, string> = {
  "taegeuk-1": "TG1",
  "taegeuk-2": "TG2",
  "taegeuk-3": "TG3",
  "taegeuk-4": "TG4",
  "taegeuk-5": "TG5",
  "taegeuk-6": "TG6",
  "taegeuk-7": "TG7",
  "taegeuk-8": "TG8",
  koryo: "Koryo",
  keumgang: "Keumgang",
  taebaek: "Taebaek",
  pyeongwon: "Pyeongwon",
  sipjin: "Sipjin",
  jitae: "Jitae",
  chonkwon: "Chonkwon",
  hansu: "Hansu",
  ilyeo: "Ilyeo",
};

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
          className="mb-6"
        >
          <button
            data-collapse-trigger={cat}
            className="w-full flex items-center justify-between py-2 px-1 text-left sticky top-14 bg-gray-50 z-10 cursor-pointer select-none"
          >
            <span className="text-lg font-semibold text-gray-700">
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
              className="w-5 h-5 text-gray-400 transition-transform"
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
          <div data-collapse-body={cat} className="grid gap-0.5">
            {grouped[cat].map((t) => (
              <TechniqueRow
                key={t.key}
                technique={t}
                categoryColor={
                  CATEGORY_COLORS[cat] || "bg-gray-100 text-gray-700"
                }
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
}: {
  technique: WikiTechnique;
  categoryColor: string;
}) {
  return (
    <Link
      href={`/techniques/${t.key}`}
      data-technique={t.key}
      data-forms={t.used_in.join(",")}
      className="flex items-center gap-3 px-3 py-2 rounded hover:bg-blue-50 transition-colors group"
    >
      {/* Name block */}
      <div className="flex-1 min-w-0 flex items-baseline gap-2 overflow-hidden">
        <span className="font-medium text-sm text-gray-900 whitespace-nowrap">
          {t.name.en}
        </span>
        <span className="text-xs text-gray-400 truncate">
          {t.name.romanized} · {t.name.ko}
        </span>
      </div>

      {/* Category pill */}
      <span
        className={`hidden sm:inline text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${categoryColor}`}
      >
        {t.category}
      </span>

      {/* Form tags */}
      <div className="hidden md:flex gap-1 shrink-0">
        {t.used_in.map((formId) => (
          <span
            key={formId}
            className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 whitespace-nowrap"
          >
            {FORM_SHORT[formId] || formId}
          </span>
        ))}
      </div>

      {/* Arrow */}
      <svg
        className="w-4 h-4 text-gray-300 group-hover:text-blue-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
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
