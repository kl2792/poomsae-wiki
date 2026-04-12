import { getForm, getAllFormIds } from "@/lib/data";
import { buildTechniqueIndex } from "@/lib/technique-index";
import type { CrossRef } from "./FormDetail";
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

  // Build cross-references for techniques that lack a breakdown in this form's video.
  const index = buildTechniqueIndex();
  const crossRefs: Record<string, CrossRef> = {};
  for (const tech of form.techniques) {
    if (tech.video_timestamp === 0) {
      const entry = index.get(tech.key);
      if (entry && entry.formId !== form.id) {
        crossRefs[tech.key] = {
          formId: entry.formId,
          formName: entry.formName,
          timestamp: entry.timestamp,
        };
      }
    }
  }

  return <FormDetail form={form} crossRefs={crossRefs} />;
}
