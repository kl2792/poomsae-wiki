import { describe, it, expect } from "vitest";
import { getAllForms, getForm, getAllFormIds, getTechnique } from "../data";
import type { FormData } from "../data";

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
