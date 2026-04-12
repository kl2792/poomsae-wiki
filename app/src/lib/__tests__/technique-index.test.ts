import { describe, it, expect } from "vitest";
import { buildTechniqueIndex, findBreakdown } from "../technique-index";

describe("buildTechniqueIndex", () => {
  const index = buildTechniqueIndex();

  it("returns a Map", () => {
    expect(index).toBeInstanceOf(Map);
  });

  it("contains entries from the data", () => {
    // Index should have at least some entries with video_timestamp > 0
    expect(index.size).toBeGreaterThan(5);
  });

  it("has non-empty index", () => {
    expect(index.size).toBeGreaterThan(0);
  });

  it("each entry has required fields", () => {
    for (const [key, entry] of index) {
      expect(entry.formId).toBeTruthy();
      expect(entry.formName).toBeTruthy();
      expect(entry.videoId).toBeTruthy();
      expect(entry.timestamp).toBeGreaterThan(0);
    }
  });

  it("maps to the earliest form in curriculum order", () => {
    // arae-makki is taught in taegeuk-1, so it should map there
    const entry = index.get("arae-makki");
    if (entry) {
      expect(entry.formId).toBe("taegeuk-1");
    }
  });
});

describe("findBreakdown", () => {
  it("returns breakdown for a known technique", () => {
    // Get any key from the index to test with
    const idx = buildTechniqueIndex();
    const firstKey = Array.from(idx.keys())[0];
    if (!firstKey) return; // skip if index empty
    const result = findBreakdown(firstKey);
    expect(result).not.toBeNull();
    expect(result!.formId).toBeTruthy();
    expect(result!.videoId).toBeTruthy();
    expect(result!.timestamp).toBeGreaterThan(0);
  });

  it("returns null for nonexistent technique", () => {
    expect(findBreakdown("nonexistent-technique")).toBeNull();
  });

  it("returns null for empty string", () => {
    expect(findBreakdown("")).toBeNull();
  });
});
