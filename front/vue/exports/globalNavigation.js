import Vue from "vue";
import store from "../store";
import GlobalNavigation from "../components/GlobalNavigation/GlobalNavigation.vue";
import baseSettings from "../components/GlobalNavigation/baseSettings";
import "../index.css";
// for the Vue buttons and modals of Django pages (e.g. Task Monitoring),
// whose own bundles only load their scripts
import "../components/Button/Button.css";
import "../components/Modal/Modal.css";
import "../components/ConfirmModal/ConfirmModal.css";
import "../../custom/index.css";
import enhanceFileDrops from "../../custom/fileDrop";
import enhanceCharts from "../../custom/charts";
import measureScrollbars from "../../custom/scrollbars";

/*
 * Standalone navigation for pages rendered by Django. Vue pages built on
 * EscrPage render the navigation themselves (with their breadcrumbs and
 * actions), so wait until their scripts have run and only mount if none did.
 */
function mount() {
    enhanceFileDrops();
    enhanceCharts();
    measureScrollbars();
    const el = document.getElementById("vue-global-nav");
    if (!el) return;
    if (document.querySelector(".escr-global-nav")) {
        el.remove();
        return;
    }
    new Vue({
        el,
        store,
        components: {
            "global-navigation": GlobalNavigation,
        },
    });
}

/*
 * Signed-in users of the new UI land on their projects instead of the home page
 * (this bundle only loads for them; custom/overrides.css keeps the home page
 * hidden meanwhile, so it doesn't flash).
 */
if (window.location.pathname === "/" && baseSettings.isAuthenticated) {
    window.location.replace("/projects/");
} else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
} else {
    mount();
}
