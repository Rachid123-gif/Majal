"use client";

import { createContext, useCallback, useContext, useEffect, useSyncExternalStore } from "react";
import ar from "./ar.json";
import fr from "./fr.json";

export type Locale = "fr" | "ar";
type Dictionary = typeof fr;

const dictionaries: Record<Locale, Dictionary> = { fr, ar };
const STORAGE_KEY = "majal.locale";

type LocaleContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string>) => string;
};

const LocaleContext = createContext<LocaleContextValue | null>(null);

function lookup(dictionary: Dictionary, key: string): string {
  let node: unknown = dictionary;
  for (const part of key.split(".")) {
    if (typeof node !== "object" || node === null) return key;
    node = (node as Record<string, unknown>)[part];
  }
  return typeof node === "string" ? node : key;
}

function readStoredLocale(): Locale | null {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === "fr" || stored === "ar" ? stored : null;
  } catch {
    return null;
  }
}

// The chosen language lives in localStorage; when storage is unavailable (private window)
// it is kept in memory for the session.
let memoryLocale: Locale = "fr";
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

const getSnapshot = (): Locale => readStoredLocale() ?? memoryLocale;
const getServerSnapshot = (): Locale => "fr";

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const locale = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      memoryLocale = next;
    }
    listeners.forEach((listener) => listener());
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string>) => {
      let text = lookup(dictionaries[locale], key);
      for (const [name, value] of Object.entries(params ?? {})) {
        text = text.replace(`{${name}}`, value);
      }
      return text;
    },
    [locale],
  );

  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>{children}</LocaleContext.Provider>
  );
}

export function useLocale(): LocaleContextValue {
  const value = useContext(LocaleContext);
  if (!value) throw new Error("useLocale must be used inside <LocaleProvider>");
  return value;
}
