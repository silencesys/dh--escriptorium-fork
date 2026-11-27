<template>
    <EscrPage
        class="escr-project-dashboard"
        :breadcrumbs="breadcrumbs"
        :sidebar-actions="sidebarActions"
        sidebar-title="Project"
        :loading="loading"
    >
        <template #page-content>
            <div class="escr-project">
                <!-- title, project actions and what the project is -->
                <header class="escr-detail-header">
                    <div class="escr-detail-title">
                        <h1>{{ projectName }}</h1>
                        <div class="escr-detail-actions">
                            <EscrButton
                                label="Share"
                                color="outline-text"
                                :on-click="openShareModal"
                                :disabled="loading"
                            >
                                <template #button-icon>
                                    <ShareIcon />
                                </template>
                            </EscrButton>
                            <EscrButton
                                label="Edit"
                                color="outline-text"
                                :on-click="openEditModal"
                                :disabled="loading"
                            >
                                <template #button-icon>
                                    <EditIcon />
                                </template>
                            </EscrButton>
                            <VerticalMenu
                                :is-open="projectMenuOpen"
                                :close-menu="closeProjectMenu"
                                :open-menu="openProjectMenu"
                                :disabled="loading"
                                :items="projectMenuItems"
                            />
                        </div>
                    </div>
                    <EscrTags
                        v-if="tags && tags.length"
                        class="escr-detail-tags"
                        :tags="tags"
                        :wrap="true"
                    />
                    <!-- what the project is, grouped: people, content, dates -->
                    <dl class="escr-details">
                        <div class="escr-detail-group">
                            <div v-if="owner">
                                <dt>Owner</dt>
                                <dd>{{ owner }}</dd>
                            </div>
                            <div>
                                <dt>Shared with</dt>
                                <dd>
                                    <button
                                        type="button"
                                        class="escr-detail-link"
                                        :disabled="loading"
                                        @click="openShareModal"
                                    >
                                        {{ sharing }}
                                    </button>
                                </dd>
                            </div>
                        </div>
                        <div class="escr-detail-group">
                            <div>
                                <dt>Default ontology</dt>
                                <dd>{{ ontologySummary }}</dd>
                            </div>
                            <div>
                                <dt>Guidelines</dt>
                                <dd v-if="guidelines">
                                    <a
                                        :href="guidelines"
                                        class="escr-detail-link"
                                        target="_blank"
                                        rel="noopener"
                                    >
                                        {{ guidelinesLabel }}
                                        <ExternalIcon />
                                    </a>
                                </dd>
                                <dd
                                    v-else
                                    class="escr-detail-empty"
                                >
                                    None
                                </dd>
                            </div>
                        </div>
                        <div class="escr-detail-group">
                            <div v-if="createdAt">
                                <dt>Created</dt>
                                <dd>{{ formatDate(createdAt) }}</dd>
                            </div>
                            <div v-if="updatedAt">
                                <dt>Updated</dt>
                                <dd>{{ formatDate(updatedAt) }}</dd>
                            </div>
                        </div>
                    </dl>
                </header>
                <!-- Documents list -->
                <section class="escr-detail-section escr-documents-list">
                    <div class="escr-card-header">
                        <h2>
                            Documents
                            <span
                                v-if="documentsCount !== null"
                                class="escr-count"
                            >{{ documentsCount }}</span>
                        </h2>
                        <div class="escr-card-actions">
                            <FilterSet
                                :disabled="loading"
                                :tags="documentTags"
                                :on-filter="onFilterDocuments"
                                search-placeholder="Search documents..."
                            />
                            <select
                                v-if="viewMode === 'grid'"
                                class="escr-grid-sort"
                                aria-label="Sort documents"
                                :disabled="loading"
                                :value="sortValue"
                                @change="onSortChange"
                            >
                                <option
                                    v-if="!sortValue"
                                    value=""
                                >
                                    Default order
                                </option>
                                <option
                                    v-for="option in sortOptions"
                                    :key="option.value"
                                    :value="option.value"
                                >
                                    {{ option.label }}
                                </option>
                            </select>
                            <SegmentedButtonGroup
                                color="secondary"
                                name="documents-display-mode"
                                class="escr-view-switch"
                                :options="viewModeOptions(GridIcon, ListIcon)"
                                :on-change-selection="setViewMode"
                            />
                            <EscrButton
                                label="New document"
                                :on-click="openCreateDocumentModal"
                                :disabled="loading || createDocumentModalOpen"
                            >
                                <template #button-icon>
                                    <PlusIcon />
                                </template>
                            </EscrButton>
                        </div>
                    </div>
                    <div
                        v-if="documents.length"
                        class="table-container"
                    >
                        <ul
                            v-if="viewMode === 'grid'"
                            class="escr-card-grid"
                        >
                            <GridCard
                                v-for="document in documents"
                                :key="document.pk"
                                :href="document.href"
                                :title="document.name"
                                :covers="covers[document.pk] || []"
                                :placeholder-icon="ManuscriptIcon"
                                :tags="document.tags.tags"
                            >
                                <template #meta>
                                    {{ plural(document.parts_count, "image") }}
                                    · {{ formatDate(document.updated_at) }}
                                </template>
                                <template #actions>
                                    <EscrButton
                                        v-tooltip.bottom="'Images'"
                                        size="small"
                                        color="text"
                                        :on-click="() => navigateToImages(document)"
                                        :disabled="loading"
                                        aria-label="Document images"
                                    >
                                        <template #button-icon>
                                            <ImagesIcon />
                                        </template>
                                    </EscrButton>
                                    <EscrButton
                                        v-tooltip.bottom="'Delete'"
                                        size="small"
                                        color="text"
                                        :on-click="() => openDeleteDocumentModal(document)"
                                        :disabled="loading"
                                        aria-label="Delete document"
                                    >
                                        <template #button-icon>
                                            <TrashIcon />
                                        </template>
                                    </EscrButton>
                                </template>
                            </GridCard>
                        </ul>
                        <EscrTable
                            v-else
                            item-key="pk"
                            :headers="headers"
                            :items="documents"
                            :on-sort="sortDocuments"
                            :disabled="loading"
                            :linkable="true"
                        >
                            <template #actions="{ item }">
                                <EscrButton
                                    v-tooltip.bottom="'Images'"
                                    size="small"
                                    color="text"
                                    :on-click="() => navigateToImages(item)"
                                    :disabled="loading"
                                    aria-label="Document images"
                                >
                                    <template #button-icon>
                                        <ImagesIcon />
                                    </template>
                                </EscrButton>
                                <EscrButton
                                    v-tooltip.bottom="'Delete'"
                                    size="small"
                                    color="text"
                                    :on-click="() => openDeleteDocumentModal(item)"
                                    :disabled="loading"
                                    aria-label="Delete document"
                                >
                                    <template #button-icon>
                                        <TrashIcon />
                                    </template>
                                </EscrButton>
                            </template>
                        </EscrTable>
                        <EscrButton
                            v-if="nextPage"
                            label="Load more"
                            class="escr-load-more-btn"
                            color="outline-primary"
                            size="small"
                            :disabled="loading"
                            :on-click="async () => await fetchNextPage()"
                        />
                    </div>
                    <EscrLoader
                        v-else
                        :loading="loading"
                        no-data-message="There are no documents to display."
                    />
                </section>
                <!-- ontology import (from the project menu) -->
                <input
                    ref="ontologyInput"
                    type="file"
                    accept=".json,.yaml,.yml"
                    class="sr-only"
                    tabindex="-1"
                    aria-hidden="true"
                    @change="onOntologyFileChange"
                >
                <EditProjectModal
                    v-if="editModalOpen"
                    :disabled="loading"
                    :fonts="fonts"
                    :on-cancel="closeEditModal"
                    :on-create-tag="createNewProjectTag"
                    :on-save="saveProject"
                    :tags="allProjectTags"
                />
                <EditDocumentModal
                    v-if="createDocumentModalOpen"
                    :disabled="loading"
                    :fonts="fonts"
                    :new-document="true"
                    :on-cancel="closeCreateDocumentModal"
                    :on-create-tag="createNewDocumentTag"
                    :on-save="createNewDocument"
                    :scripts="scripts"
                    :tags="documentTags"
                />
                <ConfirmModal
                    v-if="clearOntologyModalOpen"
                    body-text="Are you sure you want to clear this project's default ontology?"
                    confirm-verb="Clear"
                    title="Clear Default Ontology"
                    :cannot-undo="true"
                    :disabled="loading"
                    :on-cancel="() => (clearOntologyModalOpen = false)"
                    :on-confirm="onConfirmClearOntology"
                />
                <!-- delete project modal -->
                <ConfirmModal
                    v-if="deleteModalOpen"
                    body-text="Are you sure you want to delete this project?"
                    confirm-verb="Delete"
                    title="Delete Project"
                    :cannot-undo="true"
                    :disabled="loading"
                    :on-cancel="closeDeleteModal"
                    :on-confirm="deleteProject"
                />
                <!-- delete document modal -->
                <ConfirmModal
                    v-if="deleteDocumentModalOpen"
                    :body-text="`Are you sure you want to delete the document ${
                        (documentToDelete && documentToDelete.name) || ''
                    }?`"
                    confirm-verb="Delete"
                    :title="`Delete ${(documentToDelete && documentToDelete.name) || 'Document'}`"
                    :cannot-undo="true"
                    :disabled="loading"
                    :on-cancel="closeDeleteDocumentModal"
                    :on-confirm="deleteDocument"
                />
                <!-- share project modal -->
                <ShareModal
                    v-if="shareModalOpen"
                    :groups="groups"
                    :disabled="loading"
                    :on-cancel="closeShareModal"
                    :on-submit="share"
                    :shared-users="sharedWithUsers"
                />
            </div>
        </template>
    </EscrPage>
</template>
<script>
import {
    Download, Eraser, ExternalLink, Pencil, Trash2, Upload, UserPlus,
} from "lucide";
import { mapActions, mapState } from "vuex";
import ConfirmModal from "../../components/ConfirmModal/ConfirmModal.vue";
import EditDocumentModal from "../../components/EditDocumentModal/EditDocumentModal.vue";
import EditProjectModal from "../../components/EditProjectModal/EditProjectModal.vue";
import EscrButton from "../../components/Button/Button.vue";
import EscrLoader from "../../components/Loader/Loader.vue";
import EscrPage from "../Page/Page.vue";
import EscrTable from "../../components/Table/Table.vue";
import EscrTags from "../../components/Tags/Tags.vue";
import FilterSet from "../../components/FilterSet/FilterSet.vue";
import GridCard from "../../components/GridCard/GridCard.vue";
import viewMode from "../../components/GridCard/viewMode";
import {
    GridIcon,
    ImagesIcon,
    ListIcon,
    ManuscriptIcon,
    PlusIcon,
    TrashIcon,
} from "../../components/Icons/Lucide/icons";
import PeopleIcon from "../../components/Icons/PeopleIcon/PeopleIcon.vue";
import SearchIcon from "../../components/Icons/SearchIcon/SearchIcon.vue";
import SearchPanel from "../../components/SearchPanel/SearchPanel.vue";
import ShareModal from "../../components/SharePanel/ShareModal.vue";
import SharePanel from "../../components/SharePanel/SharePanel.vue";
import SegmentedButtonGroup from "../../components/SegmentedButtonGroup/SegmentedButtonGroup.vue";
import VerticalMenu from "../../components/VerticalMenu/VerticalMenu.vue";
import lucideIcon from "../../components/Icons/Lucide/lucideIcon";
import "../../components/Common/Card.css"
import "../../components/Common/DetailHeader.css";
import "./Project.css";

const ShareIcon = lucideIcon(UserPlus);
const EditIcon = lucideIcon(Pencil);
const ExternalIcon = lucideIcon(ExternalLink);
const ImportIcon = lucideIcon(Upload);
const ExportIcon = lucideIcon(Download);
const ClearIcon = lucideIcon(Eraser);
const DeleteIcon = lucideIcon(Trash2);

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

export default {
    name: "EscrProjectDashboard",
    components: {
        ConfirmModal,
        EditDocumentModal,
        EditIcon,
        EditProjectModal,
        EscrButton,
        EscrLoader,
        EscrPage,
        EscrTable,
        EscrTags,
        ExternalIcon,
        FilterSet,
        GridCard,
        ImagesIcon,
        PlusIcon,
        SegmentedButtonGroup,
        ShareIcon,
        ShareModal,
        TrashIcon,
        VerticalMenu,
    },
    mixins: [viewMode("documents", "documents")],
    props: {
        /**
         * The primary key/id of the current project.
         */
        id: {
            type: Number,
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
            clearOntologyModalOpen: false,
            GridIcon,
            ListIcon,
            ManuscriptIcon,
        };
    },
    computed: {
        ...mapState({
            allProjectTags: (state) => state.projects.tags,
            createDocumentModalOpen: (state) => state.project.createDocumentModalOpen,
            deleteModalOpen: (state) => state.project.deleteModalOpen,
            deleteDocumentModalOpen: (state) => state.project.deleteDocumentModalOpen,
            createdAt: (state) => state.project.createdAt,
            documents: (state) => state.project.documents,
            documentsSortState: (state) => state.project.sortState,
            documentsCount: (state) => state.project.documentsCount,
            documentTags: (state) => state.project.documentTags,
            documentToDelete: (state) => state.project.documentToDelete,
            editModalOpen: (state) => state.project.editModalOpen,
            groups: (state) => state.user.groups,
            guidelines: (state) => state.project.guidelines,
            loading: (state) => state.project.loading,
            nextPage: (state) => state.project.nextPage,
            ontologyConfig: (state) => state.project.ontologyConfig,
            owner: (state) => state.project.owner,
            projectName: (state) => state.project.name,
            projectId: (state) => state.project.id,
            projectMenuOpen: (state) => state.project.menuOpen,
            scripts: (state) => state.project.scripts,
            fonts: (state) => state.project.fonts,
            shareModalOpen: (state) => state.project.shareModalOpen,
            sharedWithUsers: (state) => state.project.sharedWithUsers,
            sharedWithGroups: (state) => state.project.sharedWithGroups,
            tags: (state) => state.project.tags,
            updatedAt: (state) => state.project.updatedAt,
        }),
        /**
         * Links and titles for the breadcrumbs above the page.
         */
        breadcrumbs() {
            return [
                { title: "My Projects", href: "/projects" },
                { title: this.projectName || "Loading..." }
            ];
        },
        /**
         * Table headers for the document list in the project dashboard.
         */
        /**
         * The orders the grid offers (the table sorts by its headers).
         */
        sortOptions() {
            return [
                { value: "updated_at:-1", label: "Recently updated" },
                { value: "name:1", label: "Name" },
                { value: "parts_count:-1", label: "Most images" },
            ];
        },
        sortValue() {
            const { field, direction } = this.documentsSortState || {};
            return field && direction ? `${field}:${direction}` : "";
        },
        headers() {
            return [
                { label: "Name", value: "name", sortable: true },
                { label: "Tags", value: "tags", component: EscrTags },
                { label: "Images", value: "parts_count", sortable: true },
                {
                    label: "Updated",
                    value: "updated_at",
                    sortable: true,
                    format: (val) => this.formatDate(val),
                },
            ];
        },
        /**
         * Who the project is shared with, besides its owner.
         */
        sharing() {
            const users = this.sharedWithUsers?.length;
            const groups = this.sharedWithGroups?.length;
            const parts = [];
            if (users) parts.push(plural(users, "user"));
            if (groups) parts.push(plural(groups, "group"));
            return parts.length ? parts.join(", ") : "Not shared";
        },
        /**
         * The guidelines link, shown by its host (the whole address if it
         * isn't one).
         */
        guidelinesLabel() {
            try {
                return new URL(this.guidelines).host || this.guidelines;
            } catch {
                return this.guidelines;
            }
        },
        /**
         * What the project's default ontology holds, in a few words.
         */
        ontologySummary() {
            const config = this.ontologyConfig;
            if (!config) return "Instance defaults";
            const counts = [
                ["region type", config.region_types],
                ["line type", config.line_types],
                ["part type", config.part_types],
                ["annotation component", config.annotation_components],
                ["taxonomy", config.taxonomy],
            ]
                .filter(([, list]) => list?.length)
                .map(([label, list]) => (label === "taxonomy"
                    ? `${list.length} ${list.length === 1 ? "taxonomy" : "taxonomies"}`
                    : plural(list.length, label)));
            return counts.length ? counts.join(", ") : "Empty ontology";
        },
        /**
         * The project menu: default ontology, then deleting the project.
         */
        projectMenuItems() {
            return [
                {
                    icon: ImportIcon,
                    key: "import-ontology",
                    label: "Import ontology",
                    onClick: this.onClickImportOntology,
                },
                ...(this.ontologyConfig
                    ? [{
                        icon: ExportIcon,
                        key: "export-ontology",
                        label: "Export ontology",
                        onClick: this.onClickExportOntology,
                    }, {
                        icon: ClearIcon,
                        key: "clear-ontology",
                        label: "Clear ontology",
                        onClick: this.onClickClearOntology,
                    }]
                    : []),
                {
                    icon: DeleteIcon,
                    class: "new-section",
                    key: "delete",
                    label: "Delete project",
                    onClick: this.openDeleteModal,
                },
            ];
        },
        /**
         * Sidebar quick actions for the project dashboard.
         */
        sidebarActions() {
            let actions = [
                {
                    data: {
                        disabled: this.loading,
                        users: this.sharedWithUsers,
                        groups: this.sharedWithGroups,
                        openShareModal: this.openShareModal,
                    },
                    icon: PeopleIcon,
                    key: "share",
                    label: "Groups & Users",
                    panel: SharePanel,
                },
            ];
            // if search is enabled on the instance, add search as first item
            if (!this.searchDisabled) {
                actions.unshift({
                    data: {
                        disabled: this.loading,
                        projectId: this.projectId,
                        searchScope: "Project",
                    },
                    icon: SearchIcon,
                    key: "search",
                    label: "Search Project",
                    panel: SearchPanel,
                });
            }
            return actions;
        },
    },
    watch: {
        documents: "showCovers",
        viewMode: "showCovers",
    },
    /**
     * On load, fetch basic details about the project.
     */
    async created() {
        this.setLoading(true);
        this.setId(this.id);
        try {
            await this.fetchProject();
            await this.fetchGroups();
        } catch (error) {
            this.addError(error);
        }
        this.setLoading(false);
    },
    methods: {
        plural,
        showCovers() {
            if (this.viewMode === "grid") {
                this.loadCovers(this.documents.map((document) => document.pk));
            }
        },
        onSortChange(event) {
            const [field, direction] = event.target.value.split(":");
            this.sortDocuments({ field, direction: Number(direction) });
        },
        ...mapActions("project", [
            "clearOntology",
            "closeCreateDocumentModal",
            "closeDeleteModal",
            "closeDeleteDocumentModal",
            "closeEditModal",
            "closeProjectMenu",
            "closeShareModal",
            "createNewDocumentTag",
            "createNewDocument",
            "createNewProjectTag",
            "deleteDocument",
            "deleteProject",
            "exportOntology",
            "fetchNextPage",
            "fetchProject",
            "fetchProjectDocuments",
            "importOntology",
            "openCreateDocumentModal",
            "openDeleteModal",
            "openDeleteDocumentModal",
            "openEditModal",
            "openProjectMenu",
            "openShareModal",
            "searchProject",
            "saveProject",
            "setDocumentToDelete",
            "setId",
            "setLoading",
            "share",
            "sortDocuments",
        ]),
        ...mapActions("projects", ["fetchAllProjectTags"]),
        ...mapActions("user", ["fetchGroups"]),
        ...mapActions("alerts", ["addError"]),
        async onFilterDocuments() {
            this.setLoading(true);
            try {
                await this.fetchProjectDocuments();
            } catch (error) {
                this.addError(error);
            }
            this.setLoading(false);
        },
        formatDate(value) {
            return new Date(value).toLocaleDateString(
                undefined,
                { year: "numeric", month: "short", day: "numeric" },
            );
        },
        onClickImportOntology() {
            this.closeProjectMenu();
            this.$refs.ontologyInput.click();
        },
        async onOntologyFileChange(e) {
            const file = e.target.files[0];
            e.target.value = "";
            if (file) await this.importOntology(file);
        },
        onClickExportOntology() {
            this.closeProjectMenu();
            this.exportOntology();
        },
        onClickClearOntology() {
            this.closeProjectMenu();
            this.clearOntologyModalOpen = true;
        },
        async onConfirmClearOntology() {
            await this.clearOntology();
            this.clearOntologyModalOpen = false;
        },
        navigateToImages(item) {
            if (item?.pk) {
                window.location = `/document/${item.pk}/images`;
            } else {
                this.addError({ message: "Error navigating to the images page." });
            }
        },
    },
}
</script>
