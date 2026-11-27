<template>
    <EscrPage
        class="escr-document-dashboard"
        :breadcrumbs="breadcrumbs"
        :sidebar-actions="sidebarActions"
        sidebar-title="Document"
        :loading="loading && loading.document"
    >
        <template #page-content>
            <div class="escr-document">
                <div class="escr-document-main">
                    <!-- title, document actions and what the document is -->
                    <header class="escr-detail-header">
                        <div class="escr-detail-title">
                            <h1 :title="documentName">
                                {{ documentName }}
                            </h1>
                            <div class="escr-detail-actions">
                                <EscrButton
                                    label="Share"
                                    color="outline-text"
                                    :on-click="openShareModal"
                                    :disabled="loading && loading.document"
                                >
                                    <template #button-icon>
                                        <ShareIcon />
                                    </template>
                                </EscrButton>
                                <EscrButton
                                    label="Edit"
                                    color="outline-text"
                                    :on-click="openEditModal"
                                    :disabled="(loading && loading.document) || editModalOpen"
                                >
                                    <template #button-icon>
                                        <EditIcon />
                                    </template>
                                </EscrButton>
                                <VerticalMenu
                                    :is-open="documentMenuOpen"
                                    :close-menu="closeDocumentMenu"
                                    :open-menu="openDocumentMenu"
                                    :disabled="(loading && loading.document) || deleteModalOpen"
                                    :items="documentMenuItems"
                                />
                            </div>
                        </div>
                        <EscrTags
                            v-if="tags && tags.length"
                            class="escr-detail-tags"
                            :tags="tags"
                            wrap
                        />
                        <!-- grouped: where it lives and who sees it, its text, dates -->
                        <dl class="escr-details">
                            <div class="escr-detail-group">
                                <div v-if="projectName">
                                    <dt>Project</dt>
                                    <dd>
                                        <a
                                            :href="`/project/${projectSlug}/`"
                                            class="escr-detail-link"
                                        >{{ projectName }}</a>
                                    </dd>
                                </div>
                                <div>
                                    <dt>Shared with</dt>
                                    <dd>
                                        <button
                                            type="button"
                                            class="escr-detail-link"
                                            :disabled="loading && loading.document"
                                            @click="openShareModal"
                                        >
                                            {{ sharing }}
                                        </button>
                                    </dd>
                                </div>
                            </div>
                            <div class="escr-detail-group">
                                <div>
                                    <dt>Main script</dt>
                                    <dd :class="{ 'escr-detail-empty': !mainScript }">
                                        {{ mainScript || "None" }}
                                    </dd>
                                </div>
                                <div v-if="readDirection">
                                    <dt>Reading direction</dt>
                                    <dd>{{ readDirectionLabel }}</dd>
                                </div>
                            </div>
                            <div class="escr-detail-group">
                                <div v-if="createdAt">
                                    <dt>Created</dt>
                                    <dd>{{ formatDate(createdAt) }}</dd>
                                </div>
                                <div v-if="lastModified">
                                    <dt>Updated</dt>
                                    <dd>{{ formatDate(lastModified) }}</dd>
                                </div>
                            </div>
                        </dl>
                    </header>

                    <!-- recent images -->
                    <section class="escr-detail-section escr-document-images">
                        <div class="escr-card-header">
                            <h2>Recent images</h2>
                            <div class="escr-card-actions">
                                <EscrButton
                                    label="All images"
                                    size="small"
                                    color="outline-text"
                                    :on-click="() => navigateToImages()"
                                    :disabled="loading && loading.parts"
                                >
                                    <template #button-icon-right>
                                        <ArrowIcon />
                                    </template>
                                </EscrButton>
                            </div>
                        </div>
                        <div
                            v-if="parts.length"
                            class="table-container"
                        >
                            <EscrTable
                                :items="parts"
                                :headers="partsHeaders"
                                item-key="pk"
                                linkable
                            />
                        </div>
                        <EscrLoader
                            v-else
                            :loading="loading && loading.parts"
                            no-data-message="There are no images to display."
                        />
                    </section>

                    <!-- recent tasks -->
                    <section class="escr-detail-section escr-document-tasks">
                        <div class="escr-card-header">
                            <h2>Tasks</h2>
                            <div class="escr-card-actions">
                                <EscrButton
                                    label="All tasks"
                                    size="small"
                                    color="outline-text"
                                    :on-click="() => navigateToTasks()"
                                    :disabled="loading && loading.tasks"
                                >
                                    <template #button-icon-right>
                                        <ArrowIcon />
                                    </template>
                                </EscrButton>
                            </div>
                        </div>
                        <TaskDashboard v-if="tasks.length" />
                        <EscrLoader
                            v-else
                            :loading="loading && loading.tasks"
                            no-data-message="There are no tasks to display."
                        />
                    </section>
                </div>

                <!-- statistics: tiles, characters and ontology -->
                <aside class="escr-document-stats">
                    <div class="escr-document-stats-header">
                        <h2>Statistics</h2>
                        <label class="escr-document-stats-view">
                            <span>Transcription</span>
                            <EscrDropdown
                                :options="transcriptionLevels"
                                :on-change="selectTranscription"
                            />
                        </label>
                    </div>
                    <dl class="escr-stat-tiles">
                        <div
                            v-for="stat in stats"
                            :key="stat.label"
                            class="escr-stat-tile"
                        >
                            <dt>{{ stat.label }}</dt>
                            <dd :class="{ 'escr-stat-tile-empty': stat.empty }">
                                {{ stat.value }}
                            </dd>
                        </div>
                    </dl>
                    <CharactersCard
                        class="escr-document-characters"
                        compact
                        :loading="charactersLoading"
                        :on-view="() => openCharactersModal"
                        :on-sort-characters="sortCharacters"
                        :sort="charactersSort && charactersSort.field"
                        :items="characters"
                    />
                    <OntologyCard
                        class="escr-document-ontology"
                        context="Document"
                        compact
                        :loading="loading && loading.document"
                    />
                </aside>
                <EditDocumentModal
                    v-if="editModalOpen"
                    :disabled="loading && loading.document"
                    :fonts="fonts"
                    :new-document="false"
                    :on-cancel="closeEditModal"
                    :on-create-tag="createNewDocumentTag"
                    :on-save="saveDocument"
                    :scripts="scripts"
                    :tags="allDocumentTags"
                />
                <!-- delete document modal -->
                <ConfirmModal
                    v-if="deleteModalOpen"
                    body-text="Are you sure you want to delete this document?"
                    confirm-verb="Delete"
                    title="Delete Document"
                    :cannot-undo="true"
                    :disabled="loading && loading.document"
                    :on-cancel="closeDeleteModal"
                    :on-confirm="deleteDocument"
                />
                <!-- share document modal -->
                <ShareModal
                    v-if="shareModalOpen"
                    :groups="groups"
                    :disabled="loading && loading.document"
                    :on-cancel="closeShareModal"
                    :on-submit="shareDocument"
                    :shared-users="sharedWithUsers"
                />
                <!-- import images modal -->
                <ImportModal
                    v-if="taskModalOpen && taskModalOpen.import"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('import')"
                    :on-submit="handleSubmitImport"
                />
                <!-- cancel image uploads modal -->
                <ConfirmModal
                    v-if="taskModalOpen && taskModalOpen.imageCancelWarning"
                    :body-text="'Uploads are still in progress. Are you sure you want ' +
                        'to cancel? Incomplete uploads may be lost.'"
                    title="Cancel Upload In Progress"
                    cancel-verb="No"
                    confirm-verb="Yes, cancel"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('imageCancelWarning')"
                    :on-confirm="confirmImageCancelWarning"
                    :cannot-undo="false"
                />
                <!-- segment document modal -->
                <SegmentModal
                    v-if="taskModalOpen && taskModalOpen.segment"
                    :models="segmentationModels"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('segment')"
                    :on-submit="handleSubmitSegmentation"
                    scope="Document"
                />
                <!-- transcribe document modal -->
                <TranscribeModal
                    v-if="taskModalOpen && taskModalOpen.transcribe"
                    :models="recognitionModels"
                    :transcriptions="transcriptions"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('transcribe')"
                    :on-submit="handleSubmitTranscribe"
                    scope="Document"
                />
                <!-- overwrite segmentation modal -->
                <ConfirmModal
                    v-if="taskModalOpen && taskModalOpen.overwriteWarning"
                    :body-text="'Are you sure you want to continue? Re-segmenting will delete ' +
                        'any existing transcriptions.'"
                    title="Overwrite Existing Segmentation and Transcriptions"
                    confirm-verb="Continue"
                    :disabled="loading && loading.document"
                    :cannot-undo="true"
                    :on-cancel="() => closeTaskModal('overwriteWarning')"
                    :on-confirm="confirmOverwriteWarning"
                />
                <!-- align document modal -->
                <AlignModal
                    v-if="taskModalOpen && taskModalOpen.align"
                    :transcriptions="transcriptions"
                    :region-types="regionTypes"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('align')"
                    :on-submit="handleSubmitAlign"
                    :textual-witnesses="textualWitnesses"
                    scope="Document"
                />
                <!-- export document modal -->
                <ExportModal
                    v-if="taskModalOpen && taskModalOpen.export"
                    :markdown-enabled="markdownEnabled"
                    :tei-enabled="teiEnabled"
                    :transcriptions="transcriptions"
                    :region-types="regionTypes"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('export')"
                    :on-submit="handleSubmitExport"
                    scope="Document"
                />
                <!-- download archive modal -->
                <DownloadArchiveModal
                    v-if="taskModalOpen && taskModalOpen.downloadArchive"
                    :disabled="loading && loading.document"
                    :on-cancel="() => closeTaskModal('downloadArchive')"
                    :on-submit="handleSubmitDownloadArchive"
                    scope="Document"
                />
                <!-- cancel task modal -->
                <ConfirmModal
                    v-if="taskModalOpen && taskModalOpen.cancelWarning"
                    :body-text="'Are you sure you want to cancel this task?'"
                    title="Cancel Task"
                    confirm-verb="Yes"
                    cancel-verb="No"
                    :cannot-undo="false"
                    :disabled="loading && loading.tasks"
                    :on-cancel="() => closeTaskModal('cancelWarning')"
                    :on-confirm="() => cancelTask({ documentId: id })"
                />
            </div>
        </template>
    </EscrPage>
</template>
<script>
import { ArrowRight, Pencil, Trash2, UserPlus } from "lucide";
import ReconnectingWebSocket from "reconnectingwebsocket";
import { mapActions, mapState } from "vuex";
import AlignModal from "../../components/AlignModal/AlignModal.vue";
import DownloadArchiveModal from "../../components/DownloadArchiveModal/DownloadArchiveModal.vue";
import ExportModal from "../../components/ExportModal/ExportModal.vue";
import CharactersCard from "../../components/CharactersCard/CharactersCard.vue";
import ConfirmModal from "../../components/ConfirmModal/ConfirmModal.vue";
import EditDocumentModal from "../../components/EditDocumentModal/EditDocumentModal.vue";
import EscrButton from "../../components/Button/Button.vue";
import EscrDropdown from "../../components/Dropdown/Dropdown.vue";
import EscrLoader from "../../components/Loader/Loader.vue";
import EscrPage from "../Page/Page.vue";
import EscrTags from "../../components/Tags/Tags.vue";
import EscrTable from "../../components/Table/Table.vue";
import ImportModal from "../../components/ImportModal/ImportModal.vue";
import ModelsIcon from "../../components/Icons/ModelsIcon/ModelsIcon.vue";
import ModelsPanel from "../../components/ModelsPanel/ModelsPanel.vue";
import OntologyCard from "../../components/OntologyCard/OntologyCard.vue";
import PeopleIcon from "../../components/Icons/PeopleIcon/PeopleIcon.vue";
import QuickActionsPanel from "../../components/QuickActionsPanel/QuickActionsPanel.vue";
import SearchIcon from "../../components/Icons/SearchIcon/SearchIcon.vue";
import SearchPanel from "../../components/SearchPanel/SearchPanel.vue";
import SegmentModal from "../../components/SegmentModal/SegmentModal.vue";
import ShareModal from "../../components/SharePanel/ShareModal.vue";
import SharePanel from "../../components/SharePanel/SharePanel.vue";
import TaskDashboard from "./TaskDashboard.vue";
import ToolsIcon from "../../components/Icons/ToolsIcon/ToolsIcon.vue";
import TranscribeModal from "../../components/TranscribeModal/TranscribeModal.vue";
import VerticalMenu from "../../components/VerticalMenu/VerticalMenu.vue";
import lucideIcon from "../../components/Icons/Lucide/lucideIcon";
import "../../components/Common/Card.css"
import "../../components/Common/DetailHeader.css";
import "./Document.css";

const ArrowIcon = lucideIcon(ArrowRight);
const EditIcon = lucideIcon(Pencil);
const ShareIcon = lucideIcon(UserPlus);
const DeleteIcon = lucideIcon(Trash2);

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;
const READ_DIRECTIONS = { ltr: "Left to right", rtl: "Right to left" };

export default {
    name: "EscrDocumentDashboard",
    components: {
        AlignModal,
        ArrowIcon,
        CharactersCard,
        ConfirmModal,
        DownloadArchiveModal,
        EditDocumentModal,
        EditIcon,
        EscrButton,
        EscrDropdown,
        EscrLoader,
        EscrPage,
        EscrTable,
        EscrTags,
        ExportModal,
        ImportModal,
        // eslint-disable-next-line vue/no-unused-components
        ModelsIcon,
        // eslint-disable-next-line vue/no-unused-components
        ModelsPanel,
        OntologyCard,
        // eslint-disable-next-line vue/no-unused-components
        PeopleIcon,
        // eslint-disable-next-line vue/no-unused-components
        QuickActionsPanel,
        // eslint-disable-next-line vue/no-unused-components
        SearchIcon,
        // eslint-disable-next-line vue/no-unused-components
        SearchPanel,
        SegmentModal,
        ShareIcon,
        ShareModal,
        // eslint-disable-next-line vue/no-unused-components
        SharePanel,
        TaskDashboard,
        // eslint-disable-next-line vue/no-unused-components
        ToolsIcon,
        TranscribeModal,
        VerticalMenu,
    },
    props: {
        /**
         * The primary key/id of the current document.
         */
        id: {
            type: Number,
            required: true,
        },
        /**
         * Whether or not OpenITI Markdown export is enabled on the current instance.
         */
        markdownEnabled: {
            type: Boolean,
            required: true,
        },
        /**
         * Whether or not OpenITI TEI XML export is enabled on the current instance.
         */
        teiEnabled: {
            type: Boolean,
            required: true,
        },
        /**
         * Whether or not search is disabled on the current instance.
         */
        searchDisabled: {
            type: Boolean,
            required: true,
        },
    },
    data() {
        return {
            msgSocket: undefined,
        };
    },
    computed: {
        ...mapState({
            effectiveTranscriptionFont: (state) => state.document.effectiveTranscriptionFont,
            allDocumentTags: (state) => state.project.documentTags,
            charCount: (state) => state.transcription.characterCount,
            createdAt: (state) => state.document.createdAt,
            characters: (state) => state.characters.characters,
            charactersLoading: (state) => state.characters.loading,
            charactersSort: (state) => state.characters.sortState,
            documentMenuOpen: (state) => state.document.menuOpen,
            documentMetadata: (state) => state.document.metadata,
            documentName: (state) => state.document.name,
            deleteModalOpen: (state) => state.document.deleteModalOpen,
            editModalOpen: (state) => state.document.editModalOpen,
            groups: (state) => state.user.groups,
            lastModified: (state) => state.document.lastModified,
            lineCount: (state) => state.transcription.lineCount,
            loading: (state) => state.document.loading,
            mainScript: (state) => state.document.mainScript,
            models: (state) => state.document.models,
            nextPage: (state) => state.document.nextPage,
            parts: (state) => state.document.parts,
            partsCount: (state) => state.document.partsCount,
            projectId: (state) => state.document.projectId,
            projectName: (state) => state.document.projectName,
            projectSlug: (state) => state.document.projectSlug,
            readDirection: (state) => state.document.readDirection,
            recognitionModels: (state) => state.user.recognitionModels,
            regionTypes: (state) => state.document.regionTypes,
            segmentationModels: (state) => state.user.segmentationModels,
            selectedTranscription: (state) => state.transcription.selectedTranscription,
            scripts: (state) => state.project.scripts,
            fonts: (state) => state.project.fonts,
            sharedWithUsers: (state) => state.document.sharedWithUsers,
            sharedWithGroups: (state) => state.document.sharedWithGroups,
            shareModalOpen: (state) => state.document.shareModalOpen,
            tags: (state) => state.document.tags,
            tagsModalOpen: (state) => state.document.tagsModalOpen,
            taskModalOpen: (state) => state.tasks.modalOpen,
            tasks: (state) => state.document.tasks,
            textualWitnesses: (state) => state.document.textualWitnesses,
            transcriptionLoading: (state) => state.transcription.loading,
            transcriptions: (state) => state.document.transcriptions,
        }),
        /**
         * Links and titles for the breadcrumbs above the page.
         */
        breadcrumbs() {
            let docBreadcrumbs = [{ title: "Loading..." }];
            if (this.projectName && this.projectSlug && this.documentName) {
                docBreadcrumbs = [
                    {
                        title: this.projectName,
                        href: `/project/${this.projectSlug}`
                    },
                    { title: this.documentName }
                ];
            }
            return [
                { title: "My Projects", href: "/projects" },
                ...docBreadcrumbs,
            ];
        },
        /**
         * The document menu (editing and sharing are buttons beside it).
         */
        documentMenuItems() {
            return [
                {
                    icon: DeleteIcon,
                    key: "delete",
                    label: "Delete document",
                    onClick: this.openDeleteModal,
                },
            ];
        },
        /**
         * Headers for the parts (images) table.
         */
        partsHeaders() {
            return [
                { label: "Name", value: "title", image: "thumbnail" },
                {
                    label: "Updated",
                    value: "updated_at",
                    format: (val) => this.formatDate(val),
                },
            ];
        },
        /**
         * Who the document is shared with.
         */
        sharing() {
            const users = this.sharedWithUsers?.length;
            const groups = this.sharedWithGroups?.length;
            const parts = [];
            if (users) parts.push(plural(users, "user"));
            if (groups) parts.push(plural(groups, "group"));
            return parts.length ? parts.join(", ") : "Not shared";
        },
        readDirectionLabel() {
            return READ_DIRECTIONS[this.readDirection] || this.readDirection;
        },
        /**
         * The statistics tiles: images of the document, then lines, characters
         * and confidence of the selected transcription.
         */
        stats() {
            const counting = this.transcriptionLoading?.characterCount;
            const count = (value, loading) => {
                if (loading) return { value: "…", empty: true };
                return value ? { value: value.toLocaleString() } : { value: "–", empty: true };
            };
            const confidence = this.transcriptionConfidence;
            return [
                { label: "Images", ...count(this.partsCount, this.loading?.document) },
                { label: "Lines", ...count(this.lineCount, counting) },
                { label: "Characters", ...count(this.charCount, counting) },
                {
                    label: "Confidence",
                    value: confidence || "–",
                    empty: !confidence,
                },
            ];
        },
        /**
         * Sidebar quick actions for the document dashboard.
         */
        sidebarActions() {
            let actions = [
                {
                    data: {
                        disabled: this.loading?.document,
                        scope: "Document",
                    },
                    icon: ToolsIcon,
                    key: "tasks",
                    label: "Quick Actions",
                    panel: QuickActionsPanel,
                },
                {
                    data: {
                        disabled: this.loading?.document,
                        users: this.sharedWithUsers,
                        groups: this.sharedWithGroups,
                        openShareModal: this.openShareModal,
                    },
                    icon: PeopleIcon,
                    key: "share",
                    label: "Groups & Users",
                    panel: SharePanel,
                },
                {
                    data: {
                        loading: this.loading?.document || this.loading?.models,
                        models: this.models,
                    },
                    icon: ModelsIcon,
                    key: "models",
                    label: "Document Models",
                    panel: ModelsPanel,
                }
            ];
            // if search is enabled on the instance, add search as first item
            if (!this.searchDisabled) {
                actions.unshift({
                    data: {
                        disabled: this.loading?.document,
                        searchScope: "Document",
                        projectId: this.projectId,
                        documentId: this.id,
                    },
                    icon: SearchIcon,
                    key: "search",
                    label: "Search Document",
                    panel: SearchPanel,
                });
            }
            return actions
        },
        transcriptionConfidence() {
            const confidence = this.transcriptions?.find(
                (transcription) => transcription.pk === this.selectedTranscription
            )?.avg_confidence;
            return confidence ? `${Math.round(confidence * 100)}%` : "";
        },
        transcriptionLevels() {
            return this.transcriptions.map((transcription) => ({
                value: transcription.pk,
                selected: transcription.pk === this.selectedTranscription,
                label: transcription.name,
            }));
        },
    },
    watch: {
        effectiveTranscriptionFont(font) {
            this.applyTranscriptionFont(font);
        },
    },
    /**
     * On load, fetch basic details about the document.
     */
    async created() {
        this.setId(this.id);
        // join document websocket room
        const msg = `{"type": "join-room", "object_cls": "document", "object_pk": ${this.id}}`;
        const scheme = location.protocol === "https:" ? "wss:" : "ws:";
        const msgSocket = new ReconnectingWebSocket(`${scheme}//${window.location.host}/ws/notif/`);
        msgSocket.maxReconnectAttempts = 3;
        msgSocket.addEventListener("open", function() {
            msgSocket.send(msg);
        });
        // handle document-related websocket events
        msgSocket.addEventListener("message", this.websocketTaskListener);
        try {
            await this.fetchGroups();
            await this.fetchDocument();
        } catch (error) {
            this.setLoading({ key: "document", loading: false });
            this.addError(error);
        }
    },
    methods: {
        ...mapActions("document", [
            "changeSelectedTranscription",
            "closeDeleteModal",
            "closeDocumentMenu",
            "closeEditModal",
            "closeShareModal",
            "confirmImageCancelWarning",
            "confirmOverwriteWarning",
            "deleteDocument",
            "fetchDocument",
            "fetchDocumentTasks",
            "fetchDocumentTasksThrottled",
            "handleImportDone",
            "handleSubmitAlign",
            "handleSubmitDownloadArchive",
            "handleSubmitExport",
            "handleSubmitImport",
            "handleSubmitSegmentation",
            "handleSubmitTranscribe",
            "openCharactersModal",
            "openDeleteModal",
            "openDocumentMenu",
            "openEditModal",
            "openShareModal",
            "openTagsModal",
            "saveDocument",
            "selectTranscription",
            "setId",
            "setLoading",
            "shareDocument",
            "sortCharacters",
            "viewTasks",
        ]),
        ...mapActions("alerts", ["addError"]),
        ...mapActions("project", ["createNewDocumentTag"]),
        ...mapActions("user", ["fetchGroups"]),
        ...mapActions("tasks", {
            cancelTask: "cancel",
            closeTaskModal: "closeModal",
        }),
        formatDate(value) {
            return new Date(value).toLocaleDateString(
                undefined,
                { year: "numeric", month: "short", day: "numeric" },
            );
        },
        navigateToImages() {
            if (this.id) {
                window.location = `/document/${this.id}/images`;
            } else {
                this.addError({ message: "Error navigating to the images page." });
            }
        },
        navigateToTasks() {
            window.location = "/quotas/";
        },
        selectTranscription(e) {
            this.changeSelectedTranscription(parseInt(e.target.value, 10));
        },
        applyTranscriptionFont(font) {
            const styleId = "escr-transcription-font-face";
            let styleEl = document.getElementById(styleId);
            if (font && font.url) {
                if (!styleEl) {
                    styleEl = document.createElement("style");
                    styleEl.id = styleId;
                    document.head.appendChild(styleEl);
                }
                const pct = (value) => `${Math.round(value * 100)}%`;
                const descriptors = [`size-adjust: ${pct(font.size_adjust ?? 1)}`];
                if (font.ascent_override) {
                    descriptors.push(`ascent-override: ${pct(font.ascent_override)}`);
                }
                if (font.descent_override) {
                    descriptors.push(`descent-override: ${pct(font.descent_override)}`);
                }
                styleEl.textContent = `@font-face {
                    font-family: "escr-transcription-font";
                    src: url("${font.url}");
                    ${descriptors.join("; ")};
                }`;
                this.$el.style.setProperty(
                    "--transcription-font-family",
                    `"escr-transcription-font", "Noto Sans", "Resized Arabic", sans-serif`,
                );
                if (font.line_height) {
                    this.$el.style.setProperty(
                        "--transcription-font-line-height",
                        `${font.line_height}em`,
                    );
                } else {
                    this.$el.style.removeProperty("--transcription-font-line-height");
                }
            } else {
                if (styleEl) styleEl.textContent = "";
                this.$el.style.removeProperty("--transcription-font-family");
                this.$el.style.removeProperty("--transcription-font-line-height");
            }
        },
        async websocketTaskListener(e) {
            const data = JSON.parse(e.data);
            // handle task-related events
            const taskEvents = [
                "export:", "import:", "part:mask", "part:workflow", "training:"
            ];
            if (
                data.type === "event" && taskEvents.some((task) => data.name.startsWith(task))
            ) {
                // these may be frequent, so throttle
                this.fetchDocumentTasksThrottled();

                if (data.name === "import:done") {
                    this.handleImportDone();
                }
            }
        }
    },
}
</script>
