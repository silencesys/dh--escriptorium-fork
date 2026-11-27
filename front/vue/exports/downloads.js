import Vue from "vue";
import axios from "axios";
import Downloads from "../pages/Downloads/Downloads.vue";
import Exports from "../pages/Exports/Exports.vue";

// Match the auth / CSRF defaults the rest of the app uses. Without these,
// same-origin DELETE / POST calls get rejected as CSRF failures.
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";
axios.defaults.withCredentials = true;

// the new UI has its own My Exports; the legacy UI keeps the list
const page = document.querySelector("#main.escr-vue-enabled") ? Exports : Downloads;

new Vue({
    el: "#vue-downloads",
    render: (h) => h(page),
});
