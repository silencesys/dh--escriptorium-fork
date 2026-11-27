/*
 * Lucide stand-ins for eScriptorium's own icons, under the same names and
 * classes, so a component switches by its import line alone:
 *
 *     import { XIcon } from "../Icons/Lucide/icons";
 *
 * Used by the modals and the form controls in them, so every icon there is
 * drawn in the one outline style (custom/modals.css sizes them).
 */
import {
    Check,
    ChevronDown,
    CircleCheck,
    CircleX,
    CloudUpload,
    FileArchive,
    FileCode,
    FileText,
    Folder,
    Globe,
    Images,
    Info,
    LayoutGrid,
    List,
    Pencil,
    Plus,
    ScrollText,
    ToggleLeft,
    ToggleRight,
    Trash2,
    TriangleAlert,
    X,
} from "lucide";
import lucideIcon from "./lucideIcon";

export const CheckCircleIcon = lucideIcon(CircleCheck, "escr-check-circle-icon");
export const CheckIcon = lucideIcon(Check, "escr-check-icon");
export const ChevronDownIcon = lucideIcon(ChevronDown, "escr-chevron-down-icon");
export const IIIFIcon = lucideIcon(Globe, "escr-iiif-icon");
export const ImagesIcon = lucideIcon(Images, "escr-images-icon");
export const InfoFilledIcon = lucideIcon(Info, "escr-info-icon");
export const InfoOutlineIcon = lucideIcon(Info, "escr-info-outline-icon");
export const METSIcon = lucideIcon(FileArchive, "escr-mets-icon");
export const PDFIcon = lucideIcon(FileText, "escr-pdf-icon");
export const PencilIcon = lucideIcon(Pencil, "escr-pencil-icon");
export const PlusIcon = lucideIcon(Plus, "escr-plus-icon");
export const ToggleOffIcon = lucideIcon(ToggleLeft, "escr-toggle-off");
export const ToggleOnIcon = lucideIcon(ToggleRight, "escr-toggle-on");
export const TrashIcon = lucideIcon(Trash2, "escr-trash-icon");
export const UploadIcon = lucideIcon(CloudUpload, "escr-upload-icon");
export const WarningIcon = lucideIcon(TriangleAlert, "escr-warning-icon");
export const XCircleIcon = lucideIcon(CircleX, "escr-x-circle-icon");
export const XIcon = lucideIcon(X, "escr-x-icon");
export const XMLIcon = lucideIcon(FileCode, "escr-xml-icon");

// the projects and documents grids (GridCard, the grid / list switch)
export const FolderIcon = lucideIcon(Folder, "escr-folder-icon");
export const GridIcon = lucideIcon(LayoutGrid, "escr-grid-icon");
export const ListIcon = lucideIcon(List, "escr-list-icon");
export const ManuscriptIcon = lucideIcon(ScrollText, "escr-manuscript-icon");
