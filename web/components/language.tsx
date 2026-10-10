"use client";

import { LOCALES, type Locale } from "@/lib/dictionary";
import { useLocale, useT } from "@/lib/i18n";

/** EN / ES, mirroring the appearance toggle beside it. */
export function LanguageToggle() {
  const { locale, setLocale } = useLocale();
  const t = useT();

  return (
    <div className="flex items-center gap-1" role="group" aria-label={t("lang.group")}>
      {LOCALES.map((option: Locale) => (
        <button
          key={option}
          type="button"
          className="btn btn-quiet px-2 py-1 text-[11px] uppercase"
          aria-pressed={locale === option}
          onClick={() => setLocale(option)}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
