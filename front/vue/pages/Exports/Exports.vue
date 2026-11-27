<template>
    <div class="escr-exports">
        <p class="escr-exports-intro">
            Exports and archives you queue are kept here until they expire.
        </p>

        <p
            v-if="error"
            class="escr-exports-error"
            role="alert"
        >
            Could not load your exports: {{ error }}
        </p>

        <div
            v-else-if="!loading && !items.length"
            class="escr-exports-empty"
        >
            <ArchiveIcon />
            <p>No exports yet</p>
            <p class="escr-exports-empty-hint">
                Export a document from its page, and the file will wait for you here.
            </p>
        </div>

        <table
            v-else
            class="table escr-exports-table"
            :class="{ 'is-loading': loading }"
        >
            <thead>
                <tr>
                    <th>Export</th>
                    <th class="escr-num">
                        Size
                    </th>
                    <th>Created</th>
                    <th>Expires</th>
                    <th class="escr-num">
                        Downloads
                    </th>
                    <th />
                </tr>
            </thead>
            <tbody>
                <tr
                    v-for="item in items"
                    :key="item.fingerprint"
                    :class="{ 'is-expired': item.is_expired }"
                >
                    <td class="escr-exports-label">
                        <span class="escr-exports-type">{{ shortMime(item.mime_type) }}</span>
                        <span class="escr-exports-name">{{ item.label }}</span>
                    </td>
                    <td class="escr-num">
                        {{ formatSize(item.file_size) }}
                    </td>
                    <td>
                        <time
                            :datetime="item.created_at"
                            :title="formatDate(item.created_at)"
                        >{{ formatDay(item.created_at) }}</time>
                    </td>
                    <td>
                        <span
                            v-if="item.is_expired"
                            class="escr-exports-expired"
                        >Expired</span>
                        <time
                            v-else-if="item.expires_at"
                            :datetime="item.expires_at"
                            :title="formatDate(item.expires_at)"
                        >{{ fromNow(item.expires_at) }}</time>
                        <span
                            v-else
                            class="escr-muted"
                        >Never</span>
                    </td>
                    <td class="escr-num">
                        {{ item.accessed_count || 0 }}
                    </td>
                    <td class="escr-exports-actions">
                        <a
                            v-if="!item.is_expired"
                            :href="item.file_url"
                            class="escr-button escr-button--outline-text escr-button--small"
                            download
                        >
                            <DownloadIcon />
                            <span>Download</span>
                        </a>
                        <EscrButton
                            color="text"
                            size="small"
                            class="escr-exports-delete"
                            :aria-label="`Delete ${item.label}`"
                            title="Delete"
                            :on-click="() => (toDelete = item)"
                        >
                            <template #button-icon>
                                <TrashIcon />
                            </template>
                        </EscrButton>
                    </td>
                </tr>
            </tbody>
        </table>

        <nav
            v-if="!error && (previous || next)"
            class="escr-monitoring-pages"
            aria-label="Pages"
        >
            <EscrButton
                color="outline-text"
                size="small"
                label="Previous"
                :disabled="!previous || loading"
                :on-click="() => loadPage(page - 1)"
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
                :on-click="() => loadPage(page + 1)"
            >
                <template #button-icon-right>
                    <ChevronRightIcon />
                </template>
            </EscrButton>
        </nav>

        <EscrConfirmModal
            v-if="toDelete"
            title="Delete export"
            :body-text="`Delete “${toDelete.label}”?`"
            confirm-verb="Delete"
            :disabled="deleting"
            :on-cancel="() => (toDelete = null)"
            :on-confirm="remove"
        />
    </div>
</template>
<script>
/*
 * My Exports (/downloads/) in the new UI: the files of the user's exports,
 * to download until they expire, or to delete. The legacy UI keeps
 * pages/Downloads/Downloads.vue (see vue/exports/downloads.js). Styles:
 * custom/tasks.css, which the new UI loads on Django pages.
 */
import axios from "axios";
import { Archive, ChevronLeft, ChevronRight, Download, Trash2 } from "lucide";
import EscrButton from "../../components/Button/Button.vue";
import EscrConfirmModal from "../../components/ConfirmModal/ConfirmModal.vue";
import lucideIcon from "../../components/Icons/Lucide/lucideIcon";

const MIME_TYPES = {
    "application/zip": "ZIP",
    "application/gzip": "TAR.GZ",
    "application/json": "JSON",
};

export default {
    name: "EscrExports",
    components: {
        EscrButton,
        EscrConfirmModal,
        ArchiveIcon: lucideIcon(Archive),
        ChevronLeftIcon: lucideIcon(ChevronLeft),
        ChevronRightIcon: lucideIcon(ChevronRight),
        DownloadIcon: lucideIcon(Download),
        TrashIcon: lucideIcon(Trash2),
    },
    data() {
        return {
            items: [],
            loading: true,
            error: null,
            page: 1,
            next: null,
            previous: null,
            toDelete: null,
            deleting: false,
        };
    },
    created() {
        this.fetch();
    },
    methods: {
        async fetch() {
            this.loading = true;
            this.error = null;
            try {
                const response = await axios.get("/api/downloads/", {
                    params: { page: this.page },
                });
                this.items = response.data.results || [];
                this.next = response.data.next;
                this.previous = response.data.previous;
            } catch (e) {
                this.error = e.message || String(e);
            } finally {
                this.loading = false;
            }
        },
        loadPage(page) {
            this.page = page;
            this.fetch();
        },
        async remove() {
            const item = this.toDelete;
            this.deleting = true;
            try {
                await axios.delete(`/api/downloads/${item.fingerprint}/`);
                if (this.items.length === 1 && this.page > 1) {
                    this.page -= 1;
                }
                this.fetch();
            } catch (e) {
                this.error = e.message || String(e);
            } finally {
                this.deleting = false;
                this.toDelete = null;
            }
        },
        formatSize(bytes) {
            if (!bytes && bytes !== 0) return "";
            const units = ["B", "KB", "MB", "GB", "TB"];
            let i = 0;
            let n = bytes;
            while (n >= 1024 && i < units.length - 1) {
                n /= 1024;
                i += 1;
            }
            return `${n.toFixed(n >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
        },
        formatDate(iso) {
            return new Date(iso).toLocaleString(
                undefined, { dateStyle: "medium", timeStyle: "short" },
            );
        },
        formatDay(iso) {
            return new Date(iso).toLocaleDateString(undefined, { dateStyle: "medium" });
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
            return "now";
        },
        shortMime(mime) {
            return MIME_TYPES[mime] || (mime || "").split("/").pop().toUpperCase();
        },
    },
};
</script>
