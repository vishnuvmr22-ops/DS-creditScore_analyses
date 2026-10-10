"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  DEFAULT_LOCALE,
  featureLabel,
  isLocale,
  LOCALE_KEY,
  translate,
  type Locale,
  type Vars,
} from "./dictionary";

/**
 * The interface language, held the same way the appearance is: chosen by the
 * operator, remembered in localStorage, and defaulting to English. There is no
 * provider requirement — a component rendered outside one (as in unit tests)
 * resolves against English, so the source-of-truth strings are always reachable.
 */

export const LOCALE_BOOTSTRAP = `
(function () {
  try {
    var saved = localStorage.getItem('${LOCALE_KEY}');
    document.documentElement.lang = (saved === 'en' || saved === 'es') ? saved : '${DEFAULT_LOCALE}';
  } catch (e) {
    document.documentElement.lang = '${DEFAULT_LOCALE}';
  }
})();
`;

interface LocaleState {
  locale: Locale;
  setLocale: (next: Locale) => void;
}

const LocaleContext = createContext<LocaleState | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

  // Read the stored choice after mount so the server and first client render
  // agree (both English); a returning operator's preference is applied next.
  useEffect(() => {
    try {
      const saved = localStorage.getItem(LOCALE_KEY);
      if (isLocale(saved)) setLocaleState(saved);
    } catch {
      // A locked-down browser losing the preference is not worth failing over.
    }
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    try {
      localStorage.setItem(LOCALE_KEY, next);
    } catch {
      // See above — the choice simply won't persist.
    }
  }, []);

  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale]);
  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale(): LocaleState {
  return useContext(LocaleContext) ?? { locale: DEFAULT_LOCALE, setLocale: () => {} };
}

/** The translator bound to the current locale. `t(key, vars?)`. */
export function useT(): (key: string, vars?: Vars) => string {
  const { locale } = useLocale();
  return useCallback((key: string, vars?: Vars) => translate(locale, key, vars), [locale]);
}

/** A feature name in words, in the current locale. */
export function useFeatureLabel(): (name: string) => string {
  const { locale } = useLocale();
  return useCallback((name: string) => featureLabel(locale, name), [locale]);
}
