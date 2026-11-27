<template>
    <div class="escr-monitoring">
        <!-- filters on the left, applied as they change; the bulk action on the right -->
        <div class="escr-monitoring-toolbar">
            <div
                class="escr-monitoring-filters"
                role="search"
            >
                <div class="escr-monitoring-select">
                    <select
                        v-model="state"
                        aria-label="Task state"
                        @change="reload"
                    >
                        <option value="">
                            All states
                        </option>
                        <option
                            v-for="label in stateLabels"
                            :key="label"
                            :value="label"
                        >
                            {{ label }}
                        </option>
                    </select>
                </div>
                <div
                    v-if="isAdmin"
                    class="escr-monitoring-select"
                >
                    <select
                        v-model="user"
                        aria-label="User"
                        @change="reload"
                    >
                        <option value="">
                            All users
                        </option>
                        <option
                            v-for="[id, name] in sortedUsers"
                            :key="id"
                            :value="id"
                        >
                            {{ name }}
                        </option>
                    </select>
                </div>
                <div class="escr-monitoring-search">
                    <SearchIcon />
                    <input
                        v-model="query"
                        type="search"
                        placeholder="Search documents"
                        aria-label="Document name"
                        @input="search"
                        @keyup.enter="reload"
                    >
                </div>
            </div>
            <EscrButton
                color="outline-text"
                size="small"
                :label="cancelSelectedLabel"
                :disabled="!selected.length"
                :on-click="() => askToCancel(selectedDocuments)"
            >
                <template #button-icon>
                    <BanIcon />
                </template>
            </EscrButton>
        </div>

        <table
            class="table escr-monitoring-table"
            :class="{ 'is-loading': loading }"
        >
            <thead>
                <tr>
                    <th class="escr-monitoring-check">
                        <input
                            type="checkbox"
                            :checked="allSelected"
                            :indeterminate.prop="selected.length > 0 && !allSelected"
                            :disabled="!cancelable.length"
                            aria-label="Select every document with tasks to cancel"
                            @change="toggleAll"
                        >
                    </th>
                    <th>Document</th>
                    <th>Owner</th>
                    <th>Tasks</th>
                    <th>Last task started</th>
                    <th />
                </tr>
            </thead>
            <tbody>
                <tr
                    v-for="document in documents"
                    :key="document.pk"
                >
                    <td class="escr-monitoring-check">
                        <input
                            v-if="isActive(document)"
                            type="checkbox"
                            :checked="selected.includes(document.pk)"
                            :aria-label="`Select ${document.name}`"
                            @change="toggle(document)"
                        >
                    </td>
                    <td class="escr-monitoring-name">
                        <a :href="`/document/${document.pk}/`">{{ document.name }}</a>
                    </td>
                    <td>{{ document.owner }}</td>
                    <td>
                        <ul
                            v-if="stats(document).length"
                            class="escr-monitoring-stats"
                        >
                            <li
                                v-for="stat in stats(document)"
                                :key="stat.label"
                                :class="['escr-state', `escr-state--${stat.key}`]"
                            >
                                <component :is="stat.icon" />
                                {{ stat.count }} {{ stat.label.toLowerCase() }}
                            </li>
                        </ul>
                        <span
                            v-else
                            class="escr-muted"
                        >—</span>
                    </td>
                    <td>
                        <time
                            v-if="document.last_started_task"
                            :datetime="document.last_started_task"
                            :title="formatDate(document.last_started_task)"
                        >{{ fromNow(document.last_started_task) }}</time>
                        <span
                            v-else
                            class="escr-muted"
                        >—</span>
                    </td>
                    <td class="escr-monitoring-actions">
                        <EscrButton
                            v-if="isActive(document)"
                            color="outline-text"
                            size="small"
                            label="Cancel tasks"
                            :on-click="() => askToCancel([document])"
                        />
                    </td>
                </tr>
                <tr v-if="!documents.length && !loading">
                    <td
                        colspan="6"
                        class="escr-monitoring-empty"
                    >
                        {{ emptyMessage }}
                    </td>
                </tr>
            </tbody>
        </table>

        <nav
            v-if="previous || next"
            class="escr-monitoring-pages"
            aria-label="Pages"
        >
            <EscrButton
                color="outline-text"
                size="small"
                label="Previous"
                :disabled="!previous || loading"
                :on-click="() => goTo(page - 1)"
            >
                <template #button-icon>
                    <ChevronLeftIcon />
                </template>
            </EscrButton>
            <span class="escr-monitoring-page">Page {{ page }}</span>
            <EscrButton
                color="outline-text"
                size="small"
                label="Next"
                :disabled="!next || loading"
                :on-click="() => goTo(page + 1)"
            >
                <template #button-icon-right>
                    <ChevronRightIcon />
                </template>
            </EscrButton>
        </nav>

        <EscrModal
            v-if="toCancel.length"
            class="escr-confirm-modal escr-monitoring-modal"
        >
            <template #modal-header>
                <h2 class="confirm-header--danger">
                    <WarningIcon />Cancel tasks
                </h2>
            </template>
            <template #modal-content>
                <p>
                    The queued and running tasks of
                    {{ cancelTarget }}
                    will be stopped:
                </p>
                <ul class="escr-monitoring-modal-list">
                    <li
                        v-for="document in toCancel"
                        :key="document.pk"
                    >
                        <strong>{{ document.name }}</strong>
                        <span class="escr-muted">{{ document.owner }}</span>
                    </li>
                </ul>
            </template>
            <template #modal-actions>
                <EscrButton
                    color="outline-text"
                    label="Keep them"
                    :disabled="canceling"
                    :on-click="() => (toCancel = [])"
                />
                <EscrButton
                    color="danger"
                    :label="canceling ? 'Canceling…' : 'Cancel tasks'"
                    :disabled="canceling"
                    :on-click="cancel"
                />
            </template>
        </EscrModal>
    </div>
</template>

<script>
/*
 * Task Monitoring (/documents/tasks/) in the new UI: documents with their
 * tasks, filtered as the filters change, and the queued and running tasks of
 * one or more documents canceled after a confirmation. The legacy UI keeps
 * DocumentsTasks/List.vue (see src/documentstasks/main.js). Styles:
 * custom/tasks.css, which the new UI loads on Django pages.
 */
import {
    Ban, ChevronLeft, ChevronRight, CircleCheck, CircleDashed, CircleX, LoaderCircle, Search,
} from "lucide";
import EscrButton from "../Button/Button.vue";
import EscrModal from "../Modal/Modal.vue";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import { WarningIcon } from "../Icons/Lucide/icons";

const BanIcon = lucideIcon(Ban);
// the states as the API names them, with how the tasks pages show them
const STATES = {
    Queued: { key: "active", icon: lucideIcon(CircleDashed) },
    Running: { key: "active", icon: lucideIcon(LoaderCircle) },
    Crashed: { key: "failed", icon: lucideIcon(CircleX) },
    Finished: { key: "finished", icon: lucideIcon(CircleCheck) },
    Canceled: { key: "canceled", icon: BanIcon },
};
const ACTIVE = ["Queued", "Running"];
const SEARCH_DELAY = 300;

export default {
    name: "EscrTaskMonitoring",
    components: {
        EscrButton,
        EscrModal,
        BanIcon,
        ChevronLeftIcon: lucideIcon(ChevronLeft),
        ChevronRightIcon: lucideIcon(ChevronRight),
        SearchIcon: lucideIcon(Search),
        WarningIcon,
    },
    props: {
        isAdmin: { type: Boolean, default: false },
        taskStates: { type: Object, default: () => ({}) },
        users: { type: Object, default: () => ({}) },
    },
    data() {
        return {
            state: "",
            user: "",
            query: "",
            page: 1,
            selected: [],
            toCancel: [],
            canceling: false,
            loading: true,
            searchTimer: null,
        };
    },
    computed: {
        response() {
            return this.$store.state.documentsTasks || {};
        },
        documents() {
            return this.response.results || [];
        },
        previous() {
            return this.response.previous;
        },
        next() {
            return this.response.next;
        },
        stateLabels() {
            return Object.values(this.taskStates);
        },
        sortedUsers() {
            return Object.entries(this.users).sort(([, a], [, b]) =>
                a.toLowerCase().localeCompare(b.toLowerCase()));
        },
        cancelable() {
            return this.documents.filter(this.isActive);
        },
        selectedDocuments() {
            return this.cancelable.filter(
                (document) => this.selected.includes(document.pk),
            );
        },
        allSelected() {
            const count = this.cancelable.length;
            return count > 0 && this.selected.length === count;
        },
        filtered() {
            return Boolean(this.state || this.user || this.query);
        },
        cancelSelectedLabel() {
            const count = this.selected.length;
            return count ? `Cancel tasks of ${count} selected` : "Cancel tasks of selected";
        },
        cancelTarget() {
            const count = this.toCancel.length;
            return count === 1 ? "this document" : `the ${count} documents`;
        },
        emptyMessage() {
            return this.filtered
                ? "No documents with tasks match these filters."
                : "No documents with tasks.";
        },
    },
    created() {
        this.fetch();
    },
    beforeDestroy() {
        clearTimeout(this.searchTimer);
    },
    methods: {
        isActive(document) {
            const stats = document.tasks_stats || {};
            return ACTIVE.some((state) => stats[state] > 0);
        },
        stats(document) {
            return Object.entries(document.tasks_stats || {})
                .filter(([, count]) => count > 0)
                .map(([label, count]) => (
                    { label, count, ...(STATES[label] || STATES.Canceled) }
                ));
        },
        toggle(document) {
            this.selected = this.selected.includes(document.pk)
                ? this.selected.filter((pk) => pk !== document.pk)
                : [...this.selected, document.pk];
        },
        toggleAll() {
            this.selected = this.allSelected ? [] : this.cancelable.map((document) => document.pk);
        },
        search() {
            clearTimeout(this.searchTimer);
            this.searchTimer = setTimeout(this.reload, SEARCH_DELAY);
        },
        reload() {
            clearTimeout(this.searchTimer);
            this.page = 1;
            this.fetch();
        },
        goTo(page) {
            this.page = page;
            this.fetch();
        },
        async fetch() {
            const params = { page: this.page };
            if (this.state) params.task_state = this.state;
            if (this.user) params.user_id = this.user;
            if (this.query) params.name = this.query;
            this.loading = true;
            await this.$store.dispatch("fetchDocumentsTasks", params);
            this.loading = false;
            // keep only what is still on the page and still cancelable
            const cancelable = this.cancelable.map((document) => document.pk);
            this.selected = this.selected.filter((pk) => cancelable.includes(pk));
        },
        askToCancel(documents) {
            this.toCancel = documents;
        },
        async cancel() {
            this.canceling = true;
            for (const document of this.toCancel) {
                try {
                    const data = await this.$store.dispatch("cancelDocumentTasks", document.pk);
                    const id = `cancel-${document.pk}-${Date.now()}`;
                    window.Alert.add(id, data.details, "success");
                } catch (err) {
                    const message = err.response?.data?.error || err.message;
                    window.Alert.add(`cancel-${document.pk}-${Date.now()}`, message, "danger");
                }
            }
            this.canceling = false;
            this.toCancel = [];
            this.selected = [];
            this.fetch();
        },
        formatDate(iso) {
            return new Date(iso).toLocaleString(
                undefined, { dateStyle: "medium", timeStyle: "short" },
            );
        },
        fromNow(iso) {
            const seconds = (new Date(iso) - Date.now()) / 1000;
            const units = [
                ["year", 31536000], ["month", 2592000], ["week", 604800],
                ["day", 86400], ["hour", 3600], ["minute", 60],
            ];
            const format = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
            for (const [unit, size] of units) {
                if (Math.abs(seconds) >= size) {
                    return format.format(Math.round(seconds / size), unit);
                }
            }
            return "just now";
        },
    },
};
</script>
