import fs from "fs";
import path from "path";

export interface Tip {
  text: string;
  timestamp: number;
  timestamp_end?: number;
}

export interface Technique {
  key: string;
  name: { en: string; ko: string; romanized: string };
  category: string;
  video_timestamp: number;
  video_timestamp_end?: number;
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

const DAT_DIR = path.join(process.cwd(), "..", "dat");
const FORMS_DIR = path.join(DAT_DIR, "forms");



export function getAllForms(): FormData[] {
  if (!fs.existsSync(FORMS_DIR)) return [];
  const files = fs.readdirSync(FORMS_DIR).filter((f) => f.endsWith(".json"));
  return files
    .map((f) => {
      const raw = fs.readFileSync(path.join(FORMS_DIR, f), "utf-8");
      return JSON.parse(raw) as FormData;
    })
    // SYNC: this sort order must match scripts/build_techniques.py load_forms()
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
  if (!/^[a-z0-9-]+$/.test(formId)) return null;
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

// --- Centralized technique database ---

export interface WikiTechniqueTip {
  text: string;
  timestamp?: number;
  video_id?: string;
}

export interface WikiTechniqueSource {
  form_id: string;
  form_name: string;
  video_id: string;
  timestamp: number;
  timestamp_end?: number;
}

export interface WikiTechnique {
  key: string;
  name: { en: string; ko: string; romanized: string };
  category: string;
  source: WikiTechniqueSource;
  tips: WikiTechniqueTip[];
  used_in: string[];
}

const TECHNIQUES_FILE = path.join(DAT_DIR, "techniques.json");

/** Module-level cache: read and parse techniques.json once. */
let _techniquesCache: Record<string, WikiTechnique> | null = null;
function loadTechniquesFile(): Record<string, WikiTechnique> | null {
  if (_techniquesCache !== null) return _techniquesCache;
  if (!fs.existsSync(TECHNIQUES_FILE)) return null;
  const raw = fs.readFileSync(TECHNIQUES_FILE, "utf-8");
  _techniquesCache = JSON.parse(raw) as Record<string, WikiTechnique>;
  return _techniquesCache;
}

export function getAllTechniques(): WikiTechnique[] {
  const data = loadTechniquesFile();
  if (!data) return [];
  return Object.values(data).sort((a, b) =>
    a.name.en.localeCompare(b.name.en)
  );
}

export function getAllTechniqueKeys(): string[] {
  const data = loadTechniquesFile();
  if (!data) return [];
  return Object.keys(data);
}

export function getTechniqueByKey(key: string): WikiTechnique | null {
  const data = loadTechniquesFile();
  if (!data) return null;
  return data[key] ?? null;
}
