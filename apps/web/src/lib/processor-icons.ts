import Clapperboard from "lucide-svelte/icons/clapperboard";
import ImageMinus from "lucide-svelte/icons/image-minus";
import ArrowRightLeft from "lucide-svelte/icons/arrow-right-left";
import FileVideo from "lucide-svelte/icons/file-video";
import Film from "lucide-svelte/icons/film";
import FileDown from "lucide-svelte/icons/file-down";
import Cpu from "lucide-svelte/icons/cpu";
import type { ComponentType } from "svelte";

const icons: Record<string, ComponentType> = {
  "video-bg-remove": Clapperboard,
  "image-bg-remove": ImageMinus,
  "image-convert": ArrowRightLeft,
  "video-convert": FileVideo,
  "video-to-gif": Film,
  "image-compress": FileDown,
};

export function getProcessorIcon(processorId: string): ComponentType {
  return icons[processorId] ?? Cpu;
}
