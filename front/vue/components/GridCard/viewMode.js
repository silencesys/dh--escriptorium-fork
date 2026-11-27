import { retrieveCovers } from "../../../src/api/customCovers";

/*
 * A list page shown as cards (the default) or as a table, remembered per
 * page; and the cards' cover images, fetched once per item.
 *
 *     mixins: [viewMode("projects", "projects")],
 *
 * `storageKey` names the choice in localStorage, `kind` the covers asked for
 * (projects or documents); the page calls loadCovers(ids) with what it shows.
 */
export default function viewMode(storageKey, kind) {
    const key = `${storageKey}-display-mode`;
    return {
        data() {
            return {
                covers: {},
                viewMode: localStorage.getItem(key) === "list" ? "list" : "grid",
            };
        },
        methods: {
            setViewMode(mode) {
                localStorage.setItem(key, mode);
                this.viewMode = mode;
            },
            viewModeOptions(GridIcon, ListIcon) {
                return [
                    {
                        value: "grid",
                        label: GridIcon,
                        selected: this.viewMode === "grid",
                        tooltip: "Cards",
                    },
                    {
                        value: "list",
                        label: ListIcon,
                        selected: this.viewMode === "list",
                        tooltip: "List",
                    },
                ];
            },
            async loadCovers(ids) {
                const missing = ids.filter((id) => !(id in this.covers));
                if (!missing.length) return;
                try {
                    const { data } = await retrieveCovers({ [kind]: missing });
                    const found = data?.[kind] || {};
                    const covers = { ...this.covers };
                    missing.forEach((id) => {
                        covers[id] = found[id] || [];
                    });
                    this.covers = covers;
                } catch {
                    // a card without its images is still a card
                }
            },
        },
    };
}

// "1 document", "3 documents"
export const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

// "27 Nov 2026", as the project and document pages write dates
export const shortDate = (value) => new Date(value).toLocaleDateString(
    undefined,
    { year: "numeric", month: "short", day: "numeric" },
);
