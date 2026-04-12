/** Per-category theme classes: badge (pill), border (section accent), bg (section strip). */
export const CATEGORY_THEME: Record<string, { badge: string; border: string; bg: string }> = {
  block:     { badge: "bg-blue-100 text-blue-800",     border: "border-blue-400",   bg: "bg-blue-50" },
  strike:    { badge: "bg-red-100 text-red-800",       border: "border-red-400",    bg: "bg-red-50" },
  kick:      { badge: "bg-orange-100 text-orange-800", border: "border-orange-400", bg: "bg-orange-50" },
  stance:    { badge: "bg-green-100 text-green-800",   border: "border-green-400",  bg: "bg-green-50" },
  ready:     { badge: "bg-gray-100 text-gray-700",     border: "border-gray-400",   bg: "bg-gray-50" },
  technique: { badge: "bg-purple-100 text-purple-800", border: "border-purple-400", bg: "bg-purple-50" },
};

const DEFAULT_THEME = { badge: "bg-gray-100 text-gray-700", border: "border-gray-400", bg: "bg-gray-50" };

/** Look up category theme with fallback. */
export function categoryTheme(cat: string) {
  return CATEGORY_THEME[cat] ?? DEFAULT_THEME;
}

/** Canonical display names for all forms. Keyed by form ID. */
export const FORM_DISPLAY: Record<string, string> = {
  "taegeuk-1": "Taegeuk Il Jang",
  "taegeuk-2": "Taegeuk Ee Jang",
  "taegeuk-3": "Taegeuk Sam Jang",
  "taegeuk-4": "Taegeuk Sa Jang",
  "taegeuk-5": "Taegeuk Oh Jang",
  "taegeuk-6": "Taegeuk Yuk Jang",
  "taegeuk-7": "Taegeuk Chil Jang",
  "taegeuk-8": "Taegeuk Pal Jang",
  koryo: "Koryo",
  keumgang: "Keumgang",
  taebaek: "Taebaek",
  pyeongwon: "Pyeongwon",
  sipjin: "Sipjin",
  jitae: "Jitae",
  chonkwon: "Chonkwon",
  hansu: "Hansu",
  ilyeo: "Ilyeo",
};

/** Short abbreviations for filter pills and tags. */
export const FORM_SHORT: Record<string, string> = {
  "taegeuk-1": "TG1",
  "taegeuk-2": "TG2",
  "taegeuk-3": "TG3",
  "taegeuk-4": "TG4",
  "taegeuk-5": "TG5",
  "taegeuk-6": "TG6",
  "taegeuk-7": "TG7",
  "taegeuk-8": "TG8",
  koryo: "Koryo",
  keumgang: "Keumgang",
  taebaek: "Taebaek",
  pyeongwon: "Pyeongwon",
  sipjin: "Sipjin",
  jitae: "Jitae",
  chonkwon: "Chonkwon",
  hansu: "Hansu",
  ilyeo: "Ilyeo",
};

/** Title-case a form ID as fallback display name (e.g. "taegeuk-1" → "Taegeuk 1"). */
export function formDisplayName(formId: string): string {
  return FORM_DISPLAY[formId] ?? formId.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
