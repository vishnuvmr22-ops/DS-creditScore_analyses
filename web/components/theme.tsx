"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";

export type Appearance = "light" | "dark";

export const THEME_KEY = "creditsentinel.appearance";

/**
 * Applied before paint by an inline script in the layout, so there is no flash.
 * Dark is the default appearance; an explicit saved choice always wins.
 */
export const THEME_BOOTSTRAP = `
(function () {
  try {
    var saved = localStorage.getItem('${THEME_KEY}');
    var system = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    document.documentElement.dataset.theme = saved === 'dark' || saved === 'light' ? saved : (saved === 'system' ? system : 'dark');
  } catch (e) {
    document.documentElement.dataset.theme = 'dark';
  }
})();
`;

function readStored(): Appearance {
  const saved = typeof localStorage !== "undefined" ? localStorage.getItem(THEME_KEY) : null;
  return saved === "light" ? "light" : "dark";
}

export function AppearanceToggle() {
  const [appearance, setAppearance] = useState<Appearance>("dark");
  const t = useT();

  useEffect(() => {
    setAppearance(readStored());
  }, []);

  function choose(next: Appearance) {
    setAppearance(next);
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem(THEME_KEY, next);
    } catch {
      // A locked-down browser losing the preference is not worth failing over.
    }
  }

  return (
    <div className="flex items-center gap-1" role="group" aria-label={t("theme.group")}>
      {(["light", "dark"] as const).map((option) => (
        <button
          key={option}
          type="button"
          className="btn btn-quiet px-2 py-1 text-[11px]"
          aria-pressed={appearance === option}
          onClick={() => choose(option)}
        >
          {t(`theme.${option}`)}
        </button>
      ))}
    </div>
  );
}
