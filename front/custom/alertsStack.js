/*
 * Django's notifications (#alerts-container) and the Vue toasts share the
 * bottom-right corner (custom/alerts.css): the height of the notifications,
 * as --escr-alerts-height on <html>, lifts the toasts above them.
 */
export default function stackAlerts() {
    const container = document.getElementById("alerts-container");
    if (!container || !window.ResizeObserver) return;
    const root = document.documentElement;
    new ResizeObserver(() => {
        root.style.setProperty("--escr-alerts-height", `${container.offsetHeight}px`);
    }).observe(container);
}
