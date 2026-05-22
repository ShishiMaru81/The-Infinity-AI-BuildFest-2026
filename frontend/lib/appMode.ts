const STORAGE_KEY = "guardianai_app_mode";

export type AppMode = "test" | "real";

export function getAppMode(): AppMode {
  if (typeof window === "undefined") return "test";
  const v = localStorage.getItem(STORAGE_KEY);
  return v === "real" ? "real" : "test";
}

export function setAppMode(mode: AppMode): void {
  localStorage.setItem(STORAGE_KEY, mode);
}

export function initAppModeDefault(): void {
  if (typeof window === "undefined") return;
  if (!localStorage.getItem(STORAGE_KEY)) {
    localStorage.setItem(STORAGE_KEY, "test");
  }
}
