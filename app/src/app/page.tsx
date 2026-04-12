import Link from "next/link";
import { getAllForms } from "@/lib/data";
import { ordinal } from "@/lib/format";

const BELT_COLORS: Record<string, string> = {
  "8th Geup": "bg-white text-gray-700 border border-gray-300",              // white
  "7th Geup": "bg-gradient-to-r from-yellow-300 to-green-400 text-green-900", // yellow-green
  "6th Geup": "bg-green-500 text-white",                                  // green
  "5th Geup": "bg-gradient-to-r from-green-500 to-blue-500 text-white",   // green-blue
  "4th Geup": "bg-blue-600 text-white",                                   // blue
  "3rd Geup": "bg-gradient-to-r from-blue-600 to-red-600 text-white",     // blue-red
  "2nd Geup": "bg-red-600 text-white",                                    // red
  "1st Geup": "bg-gradient-to-r from-red-600 to-gray-900 text-white",     // red-black
};

export default function Home() {
  const forms = getAllForms();

  const taegeuk = forms.filter((f) => f.id.startsWith("taegeuk"));
  const danForms = forms.filter(
    (f) => !f.id.startsWith("taegeuk") && f.dan !== undefined
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Poomsae Wiki</h1>
        <p className="text-gray-500 mt-1">
          Interactive reference for all official WT/KKW poomsae forms. Click any
          form to start learning.
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
          <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
            {/* Taegeuk: 4 rows × 2 cols (2/5 width) */}
            {taegeuk.length > 0 && (
              <section className="md:col-span-2">
                <h2 className="text-lg font-semibold mb-3 text-gray-700">
                  Taegeuk Forms
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  {taegeuk.map((form) => (
                    <FormCard key={form.id} form={form} />
                  ))}
                </div>
              </section>
            )}

            {/* Dan: 3 rows × 3 cols (3/5 width) */}
            {danForms.length > 0 && (
              <section className="md:col-span-3">
                <h2 className="text-lg font-semibold mb-3 text-gray-700">
                  Dan Forms
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {danForms.map((form) => (
                    <FormCard key={form.id} form={form} />
                  ))}
                </div>
            </section>
          )}
          </div>
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
    : form.dan
      ? "bg-gradient-to-r from-gray-800 to-gray-950 text-yellow-300 font-semibold"
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
        <span className={`text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap ${beltColor}${form.dan ? " ring-1 ring-yellow-600/40" : ""}`}>
          {form.dan ? `${form.dan}${ordinal(form.dan)} Dan` : form.belt}
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
