import Link from "next/link";
import { getAllForms } from "@/lib/data";

const BELT_COLORS: Record<string, string> = {
  "8th Geup": "bg-yellow-100 text-yellow-800",
  "7th Geup": "bg-yellow-200 text-yellow-900",
  "6th Geup": "bg-green-100 text-green-800",
  "5th Geup": "bg-green-200 text-green-900",
  "4th Geup": "bg-blue-100 text-blue-800",
  "3rd Geup": "bg-blue-200 text-blue-900",
  "2nd Geup": "bg-red-100 text-red-800",
  "1st Geup": "bg-red-200 text-red-900",
};

export default function Home() {
  const forms = getAllForms();

  const taegeuk = forms.filter((f) => f.id.startsWith("taegeuk"));
  const danForms = forms.filter(
    (f) => !f.id.startsWith("taegeuk") && f.dan !== undefined
  );

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Poomsae Wiki</h1>
        <p className="text-gray-500 mt-1">
          Interactive reference for all official WT/KKW poomsae forms. Click any
          move to see the exact video segment.
        </p>
      </div>

      {forms.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No form data yet.</p>
          <p className="text-sm mt-1">
            Run the OCR pipeline to generate form JSON files in dat/forms/
          </p>
        </div>
      ) : (
        <>
          {taegeuk.length > 0 && (
            <section className="mb-10">
              <h2 className="text-lg font-semibold mb-4 text-gray-700">
                Taegeuk Forms
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {taegeuk.map((form) => (
                  <FormCard key={form.id} form={form} />
                ))}
              </div>
            </section>
          )}

          {danForms.length > 0 && (
            <section>
              <h2 className="text-lg font-semibold mb-4 text-gray-700">
                Dan Forms
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {danForms.map((form) => (
                  <FormCard key={form.id} form={form} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function FormCard({
  form,
}: {
  form: {
    id: string;
    name: { en: string; ko: string };
    belt?: string;
    dan?: number | null;
    total_moves: number;
    sequence?: { step: number }[];
    techniques?: { key: string }[];
    meaning?: { en: string };
  };
}) {
  const beltColor = form.belt
    ? (BELT_COLORS[form.belt] || "bg-gray-800 text-white")
    : "bg-gray-800 text-white";

  const moveCount = form.sequence
    ? form.sequence.filter((s) => s.step > 0).length
    : form.total_moves;
  const techCount = form.techniques?.length;

  return (
    <Link
      href={`/forms/${form.id}`}
      className="block p-4 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <h3 className="font-medium text-sm">{form.name.en}</h3>
      <p className="text-xs text-gray-400 mt-0.5">{form.name.ko}</p>
      <div className="flex items-center gap-2 mt-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${beltColor}`}>
          {form.dan ? `${form.dan}${form.dan === 1 ? "st" : form.dan === 2 ? "nd" : form.dan === 3 ? "rd" : "th"} Dan` : form.belt}
        </span>
        <span className="text-[10px] text-gray-400">
          {moveCount} moves{techCount ? ` / ${techCount} techniques` : ""}
        </span>
      </div>
      {form.meaning && (
        <p className="text-[10px] text-gray-400 mt-1 italic">
          {form.meaning.en}
        </p>
      )}
    </Link>
  );
}
