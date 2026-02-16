import Clapperboard from "lucide-svelte/icons/clapperboard";
import ImageMinus from "lucide-svelte/icons/image-minus";
import ArrowRightLeft from "lucide-svelte/icons/arrow-right-left";
import FileVideo from "lucide-svelte/icons/file-video";
import Film from "lucide-svelte/icons/film";
import FileDown from "lucide-svelte/icons/file-down";
import Scissors from "lucide-svelte/icons/scissors";
import AudioLines from "lucide-svelte/icons/audio-lines";
import Minimize from "lucide-svelte/icons/minimize";
import Stamp from "lucide-svelte/icons/stamp";
import FileText from "lucide-svelte/icons/file-text";
import Camera from "lucide-svelte/icons/camera";
import Cpu from "lucide-svelte/icons/cpu";
import Merge from "lucide-svelte/icons/merge";
import SplitSquareHorizontal from "lucide-svelte/icons/columns-2";
import FileArchive from "lucide-svelte/icons/file-archive";
import RotateCw from "lucide-svelte/icons/rotate-cw";
import Lock from "lucide-svelte/icons/lock";
import Unlock from "lucide-svelte/icons/unlock";
import Hash from "lucide-svelte/icons/hash";
import Droplets from "lucide-svelte/icons/droplets";
import FileOutput from "lucide-svelte/icons/file-output";
import ImagePlus from "lucide-svelte/icons/image-plus";
import Disc from "lucide-svelte/icons/disc";
import Timer from "lucide-svelte/icons/timer";
import type { ComponentType } from "svelte";

const icons: Record<string, ComponentType> = {
  "video-bg-remove": Clapperboard,
  "image-bg-remove": ImageMinus,
  "image-convert": ArrowRightLeft,
  "video-convert": FileVideo,
  "video-to-gif": Film,
  "image-compress": FileDown,
  "video-trim": Scissors,
  "audio-extract": AudioLines,
  "video-compress": Minimize,
  "image-watermark": Stamp,
  "pdf-to-image": FileText,
  "video-thumbnail": Camera,
  "pdf-merge": Merge,
  "pdf-split": SplitSquareHorizontal,
  "pdf-compress": FileArchive,
  "pdf-rotate": RotateCw,
  "pdf-protect": Lock,
  "pdf-unlock": Unlock,
  "pdf-page-numbers": Hash,
  "pdf-watermark": Droplets,
  "pdf-extract-text": FileOutput,
  "image-to-pdf": ImagePlus,
  "audio-convert": Disc,
  "audio-trim": Timer,
};

export function getProcessorIcon(processorId: string): ComponentType {
  return icons[processorId] ?? Cpu;
}
