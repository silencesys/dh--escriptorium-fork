/*
 * The width of a scrollbar in this browser, as custom/scrollbars.css draws
 * it (0 where scrollbars overlay the content, as with macOS defaults), as
 * --escr-scrollbar-thin on <html>.
 * Scrolling modal content (custom/modals.css) reserves that gutter and takes
 * it off its right padding, so its fields end on the same line as the
 * header and the actions, scrollbar or not.
 */
export default function measureScrollbars() {
    const probe = document.createElement("div");
    // no scrollbar-width of its own: the probe gets the page's scrollbar style
    probe.style.cssText = "position:absolute;top:-999px;width:100px;height:50px;"
        + "overflow-y:scroll";
    document.body.appendChild(probe);
    const width = probe.offsetWidth - probe.clientWidth;
    probe.remove();
    document.documentElement.style.setProperty("--escr-scrollbar-thin", `${width}px`);
}
