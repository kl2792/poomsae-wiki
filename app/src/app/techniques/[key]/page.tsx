import { getTechniqueByKey, getAllTechniqueKeys } from "@/lib/data";
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

  return <TechniqueDetail technique={technique} />;
}
