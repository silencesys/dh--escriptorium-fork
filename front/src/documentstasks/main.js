import Vue from "vue";
import store from "./index.js";
import DocumentsTasks from "../../vue/components/DocumentsTasks/List.vue";
import TaskMonitoring from "../../vue/components/TaskMonitoring/TaskMonitoring.vue";

// the new UI has its own Task Monitoring; the legacy UI keeps the list
const newUI = Boolean(document.querySelector("#main.escr-vue-enabled"));

export var docstasksVM = new Vue({
    el: "#documents_tasks",
    store,
    components: {
        documentstasks: newUI ? TaskMonitoring : DocumentsTasks,
    },
});
