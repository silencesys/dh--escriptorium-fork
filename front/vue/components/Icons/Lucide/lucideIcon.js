import "./Lucide.css";

/*
 * Lucide icons (https://lucide.dev, ISC license) as Vue components.
 *
 *     import { ZoomIn } from "lucide";
 *     import lucideIcon from "../Icons/Lucide/lucideIcon";
 *     const ZoomInIcon = lucideIcon(ZoomIn);
 *
 * Icons are drawn with strokes in the current text colour; size them with CSS
 * (width/height) like any other icon.
 */
const ATTRS = {
    xmlns: "http://www.w3.org/2000/svg",
    width: 18,
    height: 18,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": 1.75,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "aria-hidden": "true",
    focusable: "false",
};

export default function lucideIcon(iconNode, className) {
    return {
        functional: true,
        render(h, { data }) {
            return h(
                "svg",
                {
                    ...data,
                    staticClass: ["escr-icon", className, data.staticClass]
                        .filter(Boolean).join(" "),
                    attrs: { ...ATTRS, ...data.attrs },
                },
                iconNode.map(([tag, attrs]) => h(tag, { attrs })),
            );
        },
    };
}
