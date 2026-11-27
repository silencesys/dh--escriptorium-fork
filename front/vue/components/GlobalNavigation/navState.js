import Vue from "vue";

/*
 * Collapsed state of the global navigation, shared by the navigation and the
 * page actions it hosts (EscrSidebar), and kept across pages in localStorage.
 * The class on <html> narrows --nav-width, so the page and the top bar follow.
 */
const STORAGE_KEY = "escr-nav-collapsed";

const read = () => {
    try {
        return localStorage.getItem(STORAGE_KEY) === "true";
    } catch {
        return false;
    }
};

const applyClass = (collapsed) => {
    document.documentElement.classList.toggle("escr-nav-collapsed", collapsed);
};

export const navState = Vue.observable({ collapsed: read() });

// applied as soon as the bundle runs, so the page doesn't jump once the nav mounts
applyClass(navState.collapsed);

export function setNavCollapsed(collapsed) {
    navState.collapsed = collapsed;
    applyClass(collapsed);
    try {
        localStorage.setItem(STORAGE_KEY, String(collapsed));
    } catch {
        // private mode: the state just won't persist
    }
    // panels that size themselves on window resize (editor canvases) follow the new
    // width; createEvent because paper.js installs its own global `Event` in the editor
    const resize = document.createEvent("Event");
    resize.initEvent("resize", false, false);
    window.dispatchEvent(resize);
}
