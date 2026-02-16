import { browser } from "$app/environment";

const STORAGE_KEY = "vimix-favorites";

function load(): string[] {
  if (!browser) return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore corrupt data
  }
  return [];
}

function save(ids: string[]) {
  if (!browser) return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

export const favoriteIds: string[] = $state(load());

export function toggleFavorite(id: string) {
  const idx = favoriteIds.indexOf(id);
  if (idx >= 0) {
    favoriteIds.splice(idx, 1);
  } else {
    favoriteIds.push(id);
  }
  save([...favoriteIds]);
}

export function isFavorite(id: string): boolean {
  return favoriteIds.includes(id);
}
