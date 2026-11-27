import { Image as ImageIcon, ScanText, Table2, TextAlignStart, Type } from "lucide";
import lucideIcon from "../Icons/Lucide/lucideIcon";

/** Editor panel types, in menu order: what they're called and their icon. */
export default [
    { type: "segmentation", label: "Segmentation", icon: lucideIcon(ScanText) },
    { type: "visualisation", label: "Transcription", icon: lucideIcon(Type) },
    { type: "diplomatic", label: "Text / Line Ordering", icon: lucideIcon(TextAlignStart) },
    { type: "source", label: "Image Annotation", icon: lucideIcon(ImageIcon) },
    { type: "elements", label: "Overview", icon: lucideIcon(Table2) },
];
