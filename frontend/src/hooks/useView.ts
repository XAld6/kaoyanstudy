import { useEffect, useState } from "react";

export type View = "today" | "plan" | "progress" | "coach" | "settings";

export const VIEW_STORAGE_KEY = "kaoyan-study-console:view:v1";
export const VALID_VIEWS: View[] = ["today", "plan", "progress", "coach", "settings"];

export function loadSavedView(): View {
  try {
    const saved = sessionStorage.getItem(VIEW_STORAGE_KEY);
    if (saved && VALID_VIEWS.includes(saved as View)) return saved as View;
  } catch {
    // sessionStorage may be unavailable
  }
  return "today";
}

export function saveViewToStorage(view: View): void {
  try {
    sessionStorage.setItem(VIEW_STORAGE_KEY, view);
  } catch {
    // ignore write failures
  }
}

export function useView(): [View, React.Dispatch<React.SetStateAction<View>>] {
  const [view, setView] = useState<View>(() => loadSavedView());

  useEffect(() => {
    saveViewToStorage(view);
  }, [view]);

  return [view, setView];
}
