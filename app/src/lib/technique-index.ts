import { getAllForms } from "./data";

export interface TechniqueBreakdown {
  formId: string;
  formName: string;
  videoId: string;
  timestamp: number;
}

/**
 * Build an index mapping each technique key to the first form (in curriculum
 * order) whose video actually explains it (video_timestamp > 0).
 *
 * Curriculum order is defined by getAllForms(): Taegeuk 1-8, then dan forms
 * by rank. This means "first" = the earliest form in the learning sequence.
 */
export function buildTechniqueIndex(): Map<string, TechniqueBreakdown> {
  const index = new Map<string, TechniqueBreakdown>();
  const forms = getAllForms();

  for (const form of forms) {
    for (const tech of form.techniques) {
      if (tech.video_timestamp > 0 && !index.has(tech.key)) {
        index.set(tech.key, {
          formId: form.id,
          formName: form.name.en,
          videoId: form.video_id,
          timestamp: tech.video_timestamp,
        });
      }
    }
  }

  return index;
}

/**
 * Find the first form that has a video breakdown for a given technique.
 * Returns null if no form explains this technique on video.
 */
export function findBreakdown(
  techniqueKey: string,
): TechniqueBreakdown | null {
  const index = buildTechniqueIndex();
  return index.get(techniqueKey) ?? null;
}
