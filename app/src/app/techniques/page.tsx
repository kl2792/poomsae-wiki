import Link from "next/link";
import { getAllTechniques, getAllForms } from "@/lib/data";
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

const CATEGORY_COLORS: Record<string, string> = {
  block: "bg-blue-100 text-blue-800",
  strike: "bg-red-100 text-red-800",
  kick: "bg-orange-100 text-orange-800",
  stance: "bg-green-100 text-green-800",
  ready: "bg-gray-100 text-gray-700",
  technique: "bg-purple-100 text-purple-800",
};

export default function TechniquesPage() {
  const techniques = getAllTechniques();
  const forms = getAllForms();
  const formNameMap: Record<string, string> = {};
  for (const f of forms) {
    formNameMap[f.id] = f.name.en;
  }

  // Group by category
  const grouped: Record<string, WikiTechnique[]> = {};
  for (const t of techniques) {
    const cat = t.category;
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(t);
  }

  const orderedCategories = CATEGORY_ORDER.filter((c) => grouped[c]);

  // Build serializable data for client search component
  const searchData = techniques.map((t) => ({
    key: t.key,
    en: t.name.en,
    ko: t.name.ko,
    romanized: t.name.romanized,
    category: t.category,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Techniques</h1>
        <p className="text-gray-500 mt-1">
          {techniques.length} unique techniques across {forms.length} forms.
          Grouped by category.
        </p>
      </div>

      <TechniqueSearch techniques={searchData} />

      {orderedCategories.map((cat) => (
        <section key={cat} id={cat} className="mb-8">
          <h2 className="text-xl font-semibold mb-3 text-gray-700 sticky top-14 bg-gray-50 py-2 z-10">
            {CATEGORY_LABELS[cat] || cat}{" "}
            <span className="text-sm font-normal text-gray-400">
              ({grouped[cat].length})
            </span>
          </h2>
          <div className="grid gap-2">
            {grouped[cat].map((t) => (
              <TechniqueRow
                key={t.key}
                technique={t}
                formNameMap={formNameMap}
                categoryColor={CATEGORY_COLORS[cat] || "bg-gray-100 text-gray-700"}
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
  formNameMap,
  categoryColor,
}: {
  technique: WikiTechnique;
  formNameMap: Record<string, string>;
  categoryColor: string;
}) {
  const hasSource = t.source.timestamp > 0;
  const sourceUrl = hasSource
    ? `/forms/${t.source.form_id}?t=${t.source.timestamp}`
    : `/forms/${t.source.form_id}`;

  return (
    <div
      data-technique={t.key}
      className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-200 transition-colors"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <Link href={sourceUrl} className="font-medium text-sm hover:text-blue-600">
            {t.name.en}
          </Link>
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${categoryColor}`}>
            {t.category}
          </span>
          {t.tips.length > 0 && (
            <span className="text-[10px] text-gray-400">
              {t.tips.length} tip{t.tips.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 mt-0.5">
          {t.name.romanized}
          <span className="ml-2 text-gray-400">{t.name.ko}</span>
        </p>
      </div>
      <div className="flex flex-wrap gap-1">
        {t.used_in.map((formId) => (
          <Link
            key={formId}
            href={`/forms/${formId}`}
            className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-700 whitespace-nowrap"
          >
            {formNameMap[formId] || formId}
          </Link>
        ))}
      </div>
    </div>
  );
}
