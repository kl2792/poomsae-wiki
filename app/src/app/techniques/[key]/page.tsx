import { getTechniqueByKey, getAllTechniqueKeys, getAllForms } from "@/lib/data";
import { notFound } from "next/navigation";
import TechniqueDetail from "./TechniqueDetail";

export async function generateStaticParams() {
  return getAllTechniqueKeys().map((key) => ({ key }));
}

export default async function TechniquePage({
  params,
}: {
  params: Promise<{ key: string }>;
}) {
  const { key } = await params;
  const technique = getTechniqueByKey(key);
  if (!technique) notFound();

  // Build form name lookup for "used in" badges
  const forms = getAllForms();
  const formNameMap: Record<string, string> = {};
  for (const f of forms) {
    formNameMap[f.id] = f.name.en;
  }

  return <TechniqueDetail technique={technique} formNameMap={formNameMap} />;
}
