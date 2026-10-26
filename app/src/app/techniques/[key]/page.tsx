import { getTechniqueByKey, getAllTechniqueKeys } from "@/lib/data";
import type { WikiTechnique } from "@/lib/data";
import { notFound } from "next/navigation";
import TechniqueDetail from "./TechniqueDetail";

// Combo keys contain "+" which Next.js static export decodes as space.
// Encode "+" as "--plus--" in URL paths; reverse on lookup.
const PLUS_TOKEN = "--plus--";
function keyToSlug(key: string): string {
  return key.replace(/\+/g, PLUS_TOKEN);
}
function slugToKey(slug: string): string {
  return slug.replace(new RegExp(PLUS_TOKEN, "g"), "+");
}

export async function generateStaticParams() {
  // Include all techniques (combos + components) so every link resolves
  return getAllTechniqueKeys({ includeDecomposedCombos: true }).map((key) => ({ key: keyToSlug(key) }));
}

export default async function TechniquePage({
  params,
}: {
  params: Promise<{ key: string }>;
}) {
  const { key: slug } = await params;
  const key = slugToKey(slug);
  const technique = getTechniqueByKey(key);
  if (!technique) notFound();

  // Resolve component data for combo techniques
  const componentData: Record<string, WikiTechnique> = {};
  for (const compKey of technique.components ?? []) {
    const comp = getTechniqueByKey(compKey);
    if (comp) componentData[compKey] = comp;
  }

  return <TechniqueDetail technique={technique} componentData={componentData} />;
}
