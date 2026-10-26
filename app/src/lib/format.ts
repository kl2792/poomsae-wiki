/** Whether a wiki technique has real content worth linking to. */
export function hasWikiContent(t: { source: { timestamp: number }; tips: unknown[]; used_in: string[] }): boolean {
  return t.source.timestamp > 0 || t.tips.length > 0 || t.used_in.length > 0;
}

/** Format seconds as m:ss. */
export function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Return English ordinal suffix for a number (1st, 2nd, 3rd, 11th, 12th, 13th, 21st, ...). */
export function ordinal(n: number): string {
  const mod100 = n % 100;
  if (mod100 >= 11 && mod100 <= 13) return "th";
  const mod10 = n % 10;
  if (mod10 === 1) return "st";
  if (mod10 === 2) return "nd";
  if (mod10 === 3) return "rd";
  return "th";
}
