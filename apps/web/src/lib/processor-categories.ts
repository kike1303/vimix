import Video from "lucide-svelte/icons/video";
import ImageIcon from "lucide-svelte/icons/image";
import FileText from "lucide-svelte/icons/file-text";
import Music from "lucide-svelte/icons/music";
import type { ComponentType } from "svelte";
import type { Processor } from "$lib/api";

export interface ProcessorCategory {
  id: string;
  icon: ComponentType;
  prefixes: string[];
}

export const categories: ProcessorCategory[] = [
  { id: "video", icon: Video, prefixes: ["video-"] },
  { id: "image", icon: ImageIcon, prefixes: ["image-"] },
  { id: "pdf", icon: FileText, prefixes: ["pdf-", "image-to-pdf"] },
  { id: "audio", icon: Music, prefixes: ["audio-"] },
];

export function getProcessorsForCategory(
  processors: Processor[],
  categoryId: string,
): Processor[] {
  const cat = categories.find((c) => c.id === categoryId);
  if (!cat) return [];
  return processors.filter((p) =>
    cat.prefixes.some((prefix) => p.id.startsWith(prefix) || p.id === prefix),
  );
}

export function getCategoryForProcessor(processorId: string): string | null {
  for (const cat of categories) {
    if (cat.prefixes.some((prefix) => processorId.startsWith(prefix) || processorId === prefix)) {
      return cat.id;
    }
  }
  return null;
}

export function getCategoryIcon(categoryId: string): ComponentType {
  const cat = categories.find((c) => c.id === categoryId);
  return cat?.icon ?? FileText;
}
