/*
 * Keyboard reading of the column charts of Django pages (data-escr-chart,
 * e.g. My Tasks): the chart is one tab stop, the arrow keys (and Home / End)
 * move between its columns, and a focused column shows its tooltip like a
 * hovered one (custom/tasks.css).
 */
const STEPS = { ArrowLeft: -1, ArrowRight: 1 };

export default function enhanceCharts(root = document) {
    root.querySelectorAll("[data-escr-chart]").forEach((chart) => {
        chart.addEventListener("keydown", (event) => {
            const columns = Array.from(chart.children);
            const current = columns.indexOf(document.activeElement);
            if (current < 0) return;
            let next;
            if (event.key in STEPS) next = current + STEPS[event.key];
            else if (event.key === "Home") next = 0;
            else if (event.key === "End") next = columns.length - 1;
            else return;
            event.preventDefault();
            next = Math.max(0, Math.min(columns.length - 1, next));
            columns[current].tabIndex = -1;
            columns[next].tabIndex = 0;
            columns[next].focus();
        });
    });
}
