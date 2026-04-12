import { getForm, getAllFormIds, getAllTechniques, type WikiTechnique } from "@/lib/data";
import { notFound } from "next/navigation";
import FormDetail from "./FormDetail";

export async function generateStaticParams() {
  return getAllFormIds().map((id) => ({ formId: id }));
}

export default async function FormPage({
  params,
}: {
  params: Promise<{ formId: string }>;
}) {
  const { formId } = await params;
  const form = getForm(formId);
  if (!form) notFound();

  // Build wiki technique lookup keyed by form technique key.
  // Forms use mixed key schemes (numbered "01", slugs "arae-makki"), so
  // match through case-insensitive English name.
  const allWiki = getAllTechniques();
  const wikiByName = new Map<string, WikiTechnique>();
  for (const wt of allWiki) {
    wikiByName.set(wt.name.en.toLowerCase(), wt);
  }

  const wikiTechniques: Record<string, WikiTechnique> = {};
  for (const tech of form.techniques) {
    const match = wikiByName.get(tech.name.en.toLowerCase());
    if (match) {
      wikiTechniques[tech.key] = match;
    }
  }

  return <FormDetail form={form} wikiTechniques={wikiTechniques} />;
}
