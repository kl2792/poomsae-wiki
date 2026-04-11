import fs from "fs";
import path from "path";

export interface Tip {
  text: string;
  timestamp: number;
}

export interface Technique {
  key: string;
  id: string;
  name: { en: string; ko: string };
  romanized: string;
  category: string;
  video_timestamp: number;
  tips: (Tip | string)[];
}

export interface SequenceStep {
  step: number;
  technique: string; // key into techniques[]
  side: string | null;
  direction: string;
  kihap: boolean;
  timestamp: number;
  timestamp_end: number;
}

export interface FormSections {
  intro?: { start: number; end: number };
  breakdown?: { start: number; end: number };
  repeat?: { start: number; end: number };
  multi_angle?: { start: number; end: number };
  outro?: { start: number; end: number };
}

export interface FormData {
  id: string;
  name: { en: string; ko: string };
  meaning?: { en: string; ko: string };
  belt?: string;
  dan?: number | null;
  total_moves: number;
  diagram?: string;
  video_id: string;
  video_duration_seconds: number;
  sections?: FormSections;
  competition_divisions?: string[];
  techniques: Technique[];
  sequence: SequenceStep[];
}

/** @deprecated Use Technique + SequenceStep instead */
export interface Move {
  number: number;
  technique_id: string;
  stance_id?: string;
  side?: string | null;
  direction: string;
  timestamp_start: number;
  timestamp_end: number;
  kihap: boolean;
  combination_with_next?: boolean;
  tips: string[];
  notes?: string;
}

const FORMS_DIR = path.join(process.cwd(), "..", "dat", "forms");

export function getTechnique(
  form: FormData,
  key: string
): Technique | undefined {
  return form.techniques.find((t) => t.key === key);
}

export function getAllForms(): FormData[] {
  if (!fs.existsSync(FORMS_DIR)) return [];
  const files = fs.readdirSync(FORMS_DIR).filter((f) => f.endsWith(".json"));
  return files
    .map((f) => {
      const raw = fs.readFileSync(path.join(FORMS_DIR, f), "utf-8");
      return JSON.parse(raw) as FormData;
    })
    .sort((a, b) => {
      const aNum = a.id.match(/taegeuk-(\d)/)?.[1];
      const bNum = b.id.match(/taegeuk-(\d)/)?.[1];
      // Taegeuk forms first, sorted by number
      if (aNum && bNum) return parseInt(aNum) - parseInt(bNum);
      if (aNum) return -1;
      if (bNum) return 1;
      // Dan forms sorted by dan rank
      const aDan = a.dan ?? 99;
      const bDan = b.dan ?? 99;
      return aDan - bDan;
    });
}

export function getForm(formId: string): FormData | null {
  const filePath = path.join(FORMS_DIR, `${formId}.json`);
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as FormData;
}

export function getAllFormIds(): string[] {
  if (!fs.existsSync(FORMS_DIR)) return [];
  return fs
    .readdirSync(FORMS_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""));
}
