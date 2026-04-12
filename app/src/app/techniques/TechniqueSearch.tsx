"use client";

import { useState } from "react";

interface TechniqueSearchItem {
  key: string;
  en: string;
  ko: string;
  romanized: string;
  category: string;
}

export default function TechniqueSearch({
  techniques,
}: {
  techniques: TechniqueSearchItem[];
}) {
  const [query, setQuery] = useState("");

  // When the user types, hide non-matching technique rows via DOM
  // This avoids re-rendering the entire server-rendered list
  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setQuery(q);

    const lower = q.toLowerCase().trim();
    const rows = document.querySelectorAll<HTMLElement>("[data-technique]");

    if (!lower) {
      // Show all
      rows.forEach((row) => (row.style.display = ""));
      document
        .querySelectorAll<HTMLElement>("section[id]")
        .forEach((s) => (s.style.display = ""));
      return;
    }

    const matchingKeys = new Set(
      techniques
        .filter(
          (t) =>
            t.en.toLowerCase().includes(lower) ||
            t.romanized.toLowerCase().includes(lower) ||
            t.ko.includes(q) ||
            t.category.toLowerCase().includes(lower)
        )
        .map((t) => t.key)
    );

    rows.forEach((row) => {
      const key = row.getAttribute("data-technique") || "";
      row.style.display = matchingKeys.has(key) ? "" : "none";
    });

    // Hide empty category sections
    document.querySelectorAll<HTMLElement>("section[id]").forEach((section) => {
      const visibleRows = section.querySelectorAll<HTMLElement>(
        '[data-technique]:not([style*="display: none"])'
      );
      section.style.display = visibleRows.length > 0 ? "" : "none";
    });
  }

  return (
    <div className="mb-6">
      <input
        type="text"
        value={query}
        onChange={handleChange}
        placeholder="Search techniques (English, Korean, or romanized)..."
        className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300"
      />
    </div>
  );
}
