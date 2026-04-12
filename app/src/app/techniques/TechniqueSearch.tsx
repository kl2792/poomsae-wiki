"use client";

import { useState, useCallback, useRef, useEffect } from "react";

interface TechniqueSearchItem {
  key: string;
  en: string;
  ko: string;
  romanized: string;
  category: string;
  used_in: string[];
  hasVideo: boolean;
}

interface Props {
  techniques: TechniqueSearchItem[];
  totalCount: number;
  categories: string[];
  categoryLabels: Record<string, string>;
  formIds: string[];
  formShort: Record<string, string>;
}

function readUrlFilters(): { q: string; categories: Set<string>; forms: Set<string> } {
  if (typeof window === "undefined") return { q: "", categories: new Set(), forms: new Set() };
  const params = new URLSearchParams(window.location.search);
  const q = params.get("q") || "";
  const cats = params.get("category");
  const forms = params.get("form");
  return {
    q,
    categories: cats ? new Set(cats.split(",").filter(Boolean)) : new Set(),
    forms: forms ? new Set(forms.split(",").filter(Boolean)) : new Set(),
  };
}

function writeUrlFilters(q: string, categories: Set<string>, forms: Set<string>) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (categories.size > 0) params.set("category", Array.from(categories).join(","));
  if (forms.size > 0) params.set("form", Array.from(forms).join(","));
  const qs = params.toString();
  const url = window.location.pathname + (qs ? "?" + qs : "");
  window.history.replaceState(window.history.state, "", url);
}

export default function TechniqueSearch({
  techniques,
  totalCount,
  categories,
  categoryLabels,
  formIds,
  formShort,
}: Props) {
  const initial = readUrlFilters();
  const [query, setQuery] = useState(initial.q);
  const [activeCategories, setActiveCategories] = useState<Set<string>>(initial.categories);
  const [activeForms, setActiveForms] = useState<Set<string>>(initial.forms);
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const [visibleCount, setVisibleCount] = useState(totalCount);
  const [showNoVideoOnly, setShowNoVideoOnly] = useState(false);
  const rafRef = useRef<number>(0);

  const applyFilters = useCallback(
    (q: string, cats: Set<string>, forms: Set<string>, noVideoOnly: boolean = false) => {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        const lower = q.toLowerCase().trim();
        const hasCatFilter = cats.size > 0;
        const hasFormFilter = forms.size > 0;
        const hasSearch = lower.length > 0;

        // Build matching keys
        let matchingKeys: Set<string> | null = null;
        if (hasSearch || hasCatFilter || hasFormFilter || noVideoOnly) {
          matchingKeys = new Set(
            techniques
              .filter((t) => {
                if (
                  hasCatFilter &&
                  !cats.has(t.category)
                )
                  return false;
                if (noVideoOnly && t.hasVideo) return false;
                if (
                  hasFormFilter &&
                  !t.used_in.some((f) => forms.has(f))
                )
                  return false;
                if (hasSearch) {
                  return (
                    t.en.toLowerCase().includes(lower) ||
                    t.romanized.toLowerCase().includes(lower) ||
                    t.ko.includes(q)
                  );
                }
                return true;
              })
              .map((t) => t.key)
          );
        }

        // Show/hide technique rows
        let count = 0;
        const rows =
          document.querySelectorAll<HTMLElement>("[data-technique]");
        rows.forEach((row) => {
          const key = row.getAttribute("data-technique") || "";
          const visible = matchingKeys ? matchingKeys.has(key) : true;
          row.style.display = visible ? "" : "none";
          if (visible) count++;
        });

        // Show/hide category sections
        document
          .querySelectorAll<HTMLElement>("[data-category]")
          .forEach((section) => {
            const cat = section.getAttribute("data-category") || "";
            // If category filter is active and this category isn't selected, hide
            if (hasCatFilter && !cats.has(cat)) {
              section.style.display = "none";
              return;
            }
            const visibleRows = section.querySelectorAll<HTMLElement>(
              '[data-technique]:not([style*="display: none"])'
            );
            section.style.display = visibleRows.length > 0 ? "" : "none";
          });

        setVisibleCount(count);
      });
    },
    [techniques]
  );

  // Initial render: wire up collapse triggers
  useEffect(() => {
    const triggers =
      document.querySelectorAll<HTMLElement>("[data-collapse-trigger]");
    const handlers: Array<[HTMLElement, () => void]> = [];

    triggers.forEach((trigger) => {
      const cat = trigger.getAttribute("data-collapse-trigger") || "";
      const handler = () => {
        setCollapsed((prev) => {
          const next = new Set(prev);
          if (next.has(cat)) {
            next.delete(cat);
          } else {
            next.add(cat);
          }
          return next;
        });
      };
      trigger.addEventListener("click", handler);
      handlers.push([trigger, handler]);
    });

    return () => {
      handlers.forEach(([el, handler]) =>
        el.removeEventListener("click", handler)
      );
    };
  }, []);

  // Sync collapse state to DOM
  useEffect(() => {
    categories.forEach((cat) => {
      const body = document.querySelector<HTMLElement>(
        `[data-collapse-body="${cat}"]`
      );
      const chevron = document.querySelector<HTMLElement>(
        `[data-chevron="${cat}"]`
      );
      if (body) {
        body.style.display = collapsed.has(cat) ? "none" : "";
      }
      if (chevron) {
        chevron.style.transform = collapsed.has(cat)
          ? "rotate(-90deg)"
          : "";
      }
    });
  }, [collapsed, categories]);

  // Apply URL-sourced filters on mount
  useEffect(() => {
    if (initial.q || initial.categories.size > 0 || initial.forms.size > 0) {
      applyFilters(initial.q, initial.categories, initial.forms, showNoVideoOnly);
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleCategory(cat: string) {
    setActiveCategories((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      applyFilters(query, next, activeForms, showNoVideoOnly);
      writeUrlFilters(query, next, activeForms);
      return next;
    });
  }

  function toggleForm(formId: string) {
    setActiveForms((prev) => {
      const next = new Set(prev);
      if (next.has(formId)) next.delete(formId);
      else next.add(formId);
      applyFilters(query, activeCategories, next, showNoVideoOnly);
      writeUrlFilters(query, activeCategories, next);
      return next;
    });
  }

  function clearFilters() {
    setActiveCategories(new Set());
    setActiveForms(new Set());
    setQuery("");
    applyFilters("", new Set(), new Set(), false);
    writeUrlFilters("", new Set(), new Set());
  }

  function handleSearch(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setQuery(q);
    applyFilters(q, activeCategories, activeForms, showNoVideoOnly);
    writeUrlFilters(q, activeCategories, activeForms);
  }

  // --- Drag-to-select state (refs to avoid stale closures) ---
  const isDragging = useRef(false);
  const dragAction = useRef<"select" | "deselect">("select");
  const dragTarget = useRef<"category" | "form">("category");

  function handlePillPointerDown(
    kind: "category" | "form",
    id: string,
    isActive: boolean,
  ) {
    isDragging.current = true;
    dragTarget.current = kind;
    dragAction.current = isActive ? "deselect" : "select";
    // Toggle the clicked pill
    if (kind === "category") toggleCategory(id);
    else toggleForm(id);
  }

  function handlePillPointerEnter(
    kind: "category" | "form",
    id: string,
    isActive: boolean,
  ) {
    if (!isDragging.current || dragTarget.current !== kind) return;
    const shouldBeActive = dragAction.current === "select";
    if (isActive === shouldBeActive) return; // already in desired state
    if (kind === "category") toggleCategory(id);
    else toggleForm(id);
  }

  useEffect(() => {
    const onPointerUp = () => {
      isDragging.current = false;
    };
    document.addEventListener("pointerup", onPointerUp);
    return () => document.removeEventListener("pointerup", onPointerUp);
  }, []);

  const hasFilters =
    activeCategories.size > 0 || activeForms.size > 0 || query.length > 0;

  return (
    <div className="mb-6 space-y-3">
      {/* Search bar */}
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        aria-label="Search techniques"
        placeholder="Search techniques..."
        className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300"
      />

      {/* Category filter pills */}
      <div className="flex flex-wrap gap-1.5 items-center">
        <span className="text-xs font-medium text-gray-500 self-center mr-1">
          Category
        </span>
        {categories.map((cat) => (
          <button
            key={cat}
            onPointerDown={(e) => {
              e.preventDefault();
              handlePillPointerDown("category", cat, activeCategories.has(cat));
            }}
            onPointerEnter={() =>
              handlePillPointerEnter("category", cat, activeCategories.has(cat))
            }
            className={`text-xs font-medium px-3 py-1 rounded-full border transition-all cursor-pointer select-none touch-none ${
              activeCategories.has(cat)
                ? "bg-gray-800 text-white border-gray-800 shadow-sm"
                : "bg-white text-gray-600 border-gray-300 hover:border-gray-500 hover:bg-gray-50"
            }`}
          >
            {categoryLabels[cat] || cat}
          </button>
        ))}
      </div>

      {/* Form filter pills — two rows: Taegeuk (TG1–TG8) then Dan forms */}
      <div className="flex gap-1.5 items-start">
        <span className="text-xs font-medium text-gray-500 mr-1 pt-1">
          Form
        </span>
        <div className="flex flex-col gap-1.5">
          <div className="flex flex-wrap gap-1.5">
            {formIds.filter((id) => id.startsWith("taegeuk-")).map((formId) => (
              <button
                key={formId}
                onPointerDown={(e) => {
                  e.preventDefault();
                  handlePillPointerDown("form", formId, activeForms.has(formId));
                }}
                onPointerEnter={() =>
                  handlePillPointerEnter("form", formId, activeForms.has(formId))
                }
                className={`text-xs font-medium px-3 py-1 rounded-full border transition-all cursor-pointer select-none touch-none ${
                  activeForms.has(formId)
                    ? "bg-gray-800 text-white border-gray-800 shadow-sm"
                    : "bg-white text-gray-600 border-gray-300 hover:border-gray-500 hover:bg-gray-50"
                }`}
              >
                {formShort[formId] || formId}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {formIds.filter((id) => !id.startsWith("taegeuk-")).map((formId) => (
              <button
                key={formId}
                onPointerDown={(e) => {
                  e.preventDefault();
                  handlePillPointerDown("form", formId, activeForms.has(formId));
                }}
                onPointerEnter={() =>
                  handlePillPointerEnter("form", formId, activeForms.has(formId))
                }
                className={`text-xs font-medium px-3 py-1 rounded-full border transition-all cursor-pointer select-none touch-none ${
                  activeForms.has(formId)
                    ? "bg-gray-800 text-white border-gray-800 shadow-sm"
                    : "bg-white text-gray-600 border-gray-300 hover:border-gray-500 hover:bg-gray-50"
                }`}
              >
                {formShort[formId] || formId}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Debug: no-video filter + count + clear */}
      <div className="flex items-center gap-3 text-sm text-gray-500">
        <button
          onClick={() => {
            const next = !showNoVideoOnly;
            setShowNoVideoOnly(next);
            applyFilters(query, activeCategories, activeForms, next);
          }}
          className={`text-xs px-2.5 py-1 rounded-full border font-medium transition-colors ${
            showNoVideoOnly
              ? "bg-red-50 border-red-200 text-red-600"
              : "bg-white border-gray-200 text-gray-500 hover:border-gray-300"
          }`}
        >
          {showNoVideoOnly ? "Showing: no video only" : "No video"}
        </button>
        <span>
          {hasFilters || showNoVideoOnly
            ? `Showing ${visibleCount} of ${totalCount} techniques`
            : `${totalCount} techniques`}
        </span>
        {(hasFilters || showNoVideoOnly) && (
          <button
            onClick={() => { setShowNoVideoOnly(false); clearFilters(); }}
            className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
