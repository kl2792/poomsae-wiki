import { getForm, getAllFormIds } from "@/lib/data";
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

  return <FormDetail form={form} />;
}
