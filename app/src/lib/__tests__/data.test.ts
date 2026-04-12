import { describe, it, expect } from "vitest";
import {
  getAllForms,
  getForm,
  getAllFormIds,
  getTechnique,
  getAllTechniques,
  getTechniqueByKey,
} from "../data";
import type { FormData, WikiTechnique } from "../data";

describe("getAllForms", () => {
  const forms = getAllForms();

  it("returns a non-empty array", () => {
    expect(forms.length).toBeGreaterThan(0);
  });

  it("sorts taegeuk forms first by number", () => {
    const taegeuk = forms.filter((f) => f.id.startsWith("taegeuk-"));
    const numbers = taegeuk.map((f) => {
      const m = f.id.match(/taegeuk-(\d)/);
      return m ? parseInt(m[1]) : 0;
    });
    expect(numbers).toEqual([...numbers].sort((a, b) => a - b));
  });

  it("sorts dan forms after taegeuk by dan rank", () => {
    const taegeukEnd = forms.findLastIndex((f) =>
      f.id.startsWith("taegeuk-")
    );
    const danForms = forms.slice(taegeukEnd + 1);
    const ranks = danForms.map((f) => f.dan ?? 99);
    expect(ranks).toEqual([...ranks].sort((a, b) => a - b));
  });

  it("places all taegeuk forms before dan forms", () => {
    const lastTaegeukIdx = forms.findLastIndex((f) =>
      f.id.startsWith("taegeuk-")
    );
    const firstDanIdx = forms.findIndex((f) => f.dan !== null && f.dan !== undefined);
    // taegeuk forms should be contiguous at the start; first dan after last taegeuk
    expect(firstDanIdx).toBeGreaterThan(lastTaegeukIdx);
  });
});

describe("getForm", () => {
  it("returns valid form data for taegeuk-1", () => {
    const form = getForm("taegeuk-1");
    expect(form).not.toBeNull();
    expect(form!.id).toBe("taegeuk-1");
    expect(form!.name.en).toBe("Taegeuk Il Jang");
    expect(form!.name.ko).toBeTruthy();
  });

  it("returns null for nonexistent form", () => {
    expect(getForm("nonexistent")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(getForm("")).toBeNull();
  });
});

describe("form data structure", () => {
  const forms = getAllForms();

  it("every form has required fields", () => {
    for (const form of forms) {
      expect(form.id).toBeTruthy();
      expect(form.name.en).toBeTruthy();
      expect(form.name.ko).toBeTruthy();
      expect(form.video_id).toBeTruthy();
      expect(form.total_moves).toBeGreaterThan(0);
      expect(form.techniques.length).toBeGreaterThan(0);
      expect(form.sequence.length).toBeGreaterThan(0);
    }
  });

  it("every sequence step references an existing technique", () => {
    for (const form of forms) {
      const techKeys = new Set(form.techniques.map((t) => t.key));
      for (const step of form.sequence) {
        expect(
          techKeys.has(step.technique),
          `Form ${form.id} step ${step.step}: technique "${step.technique}" not in techniques`
        ).toBe(true);
      }
    }
  });

  it("sequence steps are ordered", () => {
    for (const form of forms) {
      const steps = form.sequence.map((s) => s.step);
      expect(steps).toEqual([...steps].sort((a, b) => a - b));
    }
  });

  it("every technique has required name fields", () => {
    for (const form of forms) {
      for (const tech of form.techniques) {
        expect(tech.key).toBeTruthy();
        expect(tech.name.en).toBeTruthy();
        expect(tech.name.ko).toBeTruthy();
        expect(tech.name.romanized).toBeTruthy();
        expect(tech.category).toBeTruthy();
      }
    }
  });
});

describe("getTechnique", () => {
  it("finds a technique by key", () => {
    const form = getForm("taegeuk-1")!;
    const tech = getTechnique(form, form.techniques[0].key);
    expect(tech).toBeDefined();
    expect(tech!.key).toBe(form.techniques[0].key);
  });

  it("returns undefined for nonexistent key", () => {
    const form = getForm("taegeuk-1")!;
    expect(getTechnique(form, "nonexistent")).toBeUndefined();
  });
});

// --- Wiki technique database tests ---

describe("getAllTechniques", () => {
  const techniques = getAllTechniques();

  it("returns a non-empty array", () => {
    expect(techniques.length).toBeGreaterThan(0);
  });

  it("returns more than 100 techniques", () => {
    expect(techniques.length).toBeGreaterThan(100);
  });

  it("returns techniques sorted by English name", () => {
    const names = techniques.map((t) => t.name.en);
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b)));
  });
});

describe("getTechniqueByKey", () => {
  it("returns a valid technique for 'low-block'", () => {
    const tech = getTechniqueByKey("low-block");
    expect(tech).not.toBeNull();
    expect(tech!.key).toBe("low-block");
    expect(tech!.name.en).toBe("Low Block");
    expect(tech!.name.ko).toBeTruthy();
    expect(tech!.name.romanized).toBe("Arae Makgi");
    expect(tech!.category).toBe("block");
  });

  it("returns null for nonexistent key", () => {
    expect(getTechniqueByKey("nonexistent-technique-xyz")).toBeNull();
  });

  it("returns null for empty string key", () => {
    expect(getTechniqueByKey("")).toBeNull();
  });
});

describe("wiki technique data structure", () => {
  const techniques = getAllTechniques();

  it("every technique has required fields: key, name.en, name.ko, name.romanized, category, source", () => {
    for (const tech of techniques) {
      expect(tech.key, `technique missing key`).toBeTruthy();
      expect(tech.name.en, `${tech.key} missing name.en`).toBeTruthy();
      expect(tech.name.ko, `${tech.key} missing name.ko`).toBeTruthy();
      expect(tech.name.romanized, `${tech.key} missing name.romanized`).toBeTruthy();
      expect(tech.category, `${tech.key} missing category`).toBeTruthy();
      expect(tech.source, `${tech.key} missing source`).toBeDefined();
    }
  });

  it("every technique source has form_id and video_id", () => {
    for (const tech of techniques) {
      expect(tech.source.form_id, `${tech.key} source missing form_id`).toBeTruthy();
      expect(tech.source.video_id, `${tech.key} source missing video_id`).toBeTruthy();
      expect(typeof tech.source.timestamp).toBe("number");
    }
  });

  it("every technique has non-empty used_in array", () => {
    for (const tech of techniques) {
      expect(
        tech.used_in.length,
        `${tech.key} has empty used_in`
      ).toBeGreaterThan(0);
    }
  });

  it("no duplicate keys across techniques", () => {
    const keys = techniques.map((t) => t.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("categories are valid values", () => {
    const validCategories = new Set([
      "block", "kick", "strike", "stance", "ready", "technique", "combination",
    ]);
    for (const tech of techniques) {
      expect(
        validCategories.has(tech.category),
        `${tech.key} has invalid category '${tech.category}'`
      ).toBe(true);
    }
  });
});

describe("getAllFormIds", () => {
  it("returns an array of string ids", () => {
    const ids = getAllFormIds();
    expect(ids.length).toBeGreaterThan(0);
    for (const id of ids) {
      expect(typeof id).toBe("string");
      expect(id.length).toBeGreaterThan(0);
    }
  });

  it("matches the ids from getAllForms", () => {
    const ids = new Set(getAllFormIds());
    const formIds = new Set(getAllForms().map((f) => f.id));
    expect(ids).toEqual(formIds);
  });
});
