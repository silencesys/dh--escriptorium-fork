<template>
    <EscrPage class="escr-projects-list">
        <template #page-content>
            <div class="escr-card escr-card-table">
                <div class="escr-card-padding escr-card-header">
                    <h1>Projects</h1>
                    <div class="escr-card-actions">
                        <FilterSet
                            :disabled="loading"
                            :tags="tags"
                            :on-filter="async () => await fetchProjects()"
                            search-placeholder="Search projects..."
                        />
                        <select
                            v-if="viewMode === 'grid'"
                            class="escr-grid-sort"
                            aria-label="Sort projects"
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
                            name="projects-display-mode"
                            class="escr-view-switch"
                            :options="viewModeOptions(GridIcon, ListIcon)"
                            :on-change-selection="setViewMode"
                        />
                        <EscrButton
                            label="Create New"
                            :on-click="openCreateModal"
                            :disabled="loading || createModalOpen"
                        >
                            <template #button-icon>
                                <PlusIcon />
                            </template>
                        </EscrButton>
                        <NewProjectModal
                            v-if="createModalOpen"
                            :disabled="loading"
                            :fonts="fonts"
                            :new-project="true"
                            :on-save="createNewProject"
                            :on-cancel="closeCreateModal"
                            :on-create-tag="createNewProjectTag"
                            :tags="tags"
                        />
                    </div>
                </div>
                <EscrModal
                    v-if="deleteModalOpen"
                    class="escr-delete-project"
                >
                    <template #modal-content>
                        <h2>Delete Project "{{ projectToDelete.name }}"</h2>
                        <p>
                            Are you sure you want to delete this project?
                            This action cannot be undone.
                        </p>
                    </template>
                    <template #modal-actions>
                        <EscrButton
                            color="outline-primary"
                            label="Cancel"
                            :disabled="loading"
                            :on-click="() => closeDeleteModal()"
                        />
                        <EscrButton
                            color="danger"
                            label="Delete"
                            :disabled="loading"
                            :on-click="() => deleteProject()"
                        />
                    </template>
                </EscrModal>
                <div
                    v-if="projects.length"
                    class="table-container"
                >
                    <ul
                        v-if="viewMode === 'grid'"
                        class="escr-card-grid"
                    >
                        <GridCard
                            v-for="project in projects"
                            :key="project.slug"
                            :href="project.href"
                            :title="project.name"
                            :covers="covers[project.id] || []"
                            :placeholder-icon="FolderIcon"
                            :tags="project.tags.tags"
                        >
                            <template #meta>
                                {{ plural(project.documents_count, "document") }}
                                · {{ project.owner }} · {{ shortDate(project.updated_at) }}
                            </template>
                            <template #actions>
                                <EscrButton
                                    v-tooltip.bottom="'Delete'"
                                    size="small"
                                    color="text"
                                    :on-click="() => openDeleteModal(project)"
                                    :disabled="loading"
                                    aria-label="Delete project"
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
                        :items="projects"
                        item-key="slug"
                        :headers="headers"
                        :on-sort="sortProjects"
                        :disabled="loading"
                        :linkable="true"
                    >
                        <template #actions="{ item }">
                            <EscrButton
                                v-tooltip.bottom="'Delete'"
                                size="small"
                                color="text"
                                :on-click="() => openDeleteModal(item)"
                                :disabled="loading"
                                aria-label="Delete project"
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
                    no-data-message="There are no projects to display."
                />
            </div>
        </template>
    </EscrPage>
</template>
<script>
import { mapActions, mapState } from "vuex";
import EscrButton from "../../components/Button/Button.vue";
import EscrLoader from "../../components/Loader/Loader.vue";
import EscrModal from "../../components/Modal/Modal.vue";
import EscrPage from "../Page/Page.vue";
import EscrTable from "../../components/Table/Table.vue";
import EscrTags from "../../components/Tags/Tags.vue";
import FilterSet from "../../components/FilterSet/FilterSet.vue";
import GridCard from "../../components/GridCard/GridCard.vue";
import viewMode, { plural, shortDate } from "../../components/GridCard/viewMode";
import {
    FolderIcon,
    GridIcon,
    ListIcon,
    PlusIcon,
    TrashIcon,
} from "../../components/Icons/Lucide/icons";
import SegmentedButtonGroup from "../../components/SegmentedButtonGroup/SegmentedButtonGroup.vue";
import NewProjectModal from "../../components/EditProjectModal/EditProjectModal.vue";
import "../../components/Common/Card.css"
import "./ProjectsList.css";

export default {
    name: "EscrProjectsListPage",
    components: {
        EscrButton,
        EscrLoader,
        EscrModal,
        EscrPage,
        EscrTable,
        // eslint-disable-next-line vue/no-unused-components
        EscrTags,
        FilterSet,
        GridCard,
        NewProjectModal,
        PlusIcon,
        SegmentedButtonGroup,
        TrashIcon,
    },
    mixins: [viewMode("projects", "projects")],
    data() {
        return { FolderIcon, GridIcon, ListIcon };
    },
    computed: {
        ...mapState({
            createModalOpen: (state) => state.projects.createModalOpen,
            deleteModalOpen: (state) => state.projects.deleteModalOpen,
            fonts: (state) => state.projects.fonts,
            loading: (state) => state.projects.loading,
            nextPage: (state) => state.projects.nextPage,
            projects: (state) => state.projects.projects,
            projectToDelete: (state) => state.projects.projectToDelete,
            sortState: (state) => state.projects.sortState,
            tags: (state) => state.projects.tags,
        }),
        /**
         * The orders the grid offers (the table sorts by its headers).
         */
        sortOptions() {
            return [
                { value: "updated_at:-1", label: "Recently updated" },
                { value: "name:1", label: "Name" },
                { value: "documents_count:-1", label: "Most documents" },
                { value: "owner:1", label: "Owner" },
            ];
        },
        sortValue() {
            const { field, direction } = this.sortState || {};
            return field && direction ? `${field}:${direction}` : "";
        },
        headers() {
            return [
                { label: "Name", value: "name", sortable: true },
                { label: "Project Tags", value: "tags", component: EscrTags },
                { label: "# of Documents", value: "documents_count", sortable: true  },
                { label: "Owner", value: "owner", sortable: true  },
                {
                    label: "Last Update",
                    value: "updated_at",
                    sortable: true,
                    format: (val) => new Date(val).toLocaleDateString(
                        undefined,
                        { year: "numeric", month: "long", day: "numeric" },
                    ),
                },
            ];
        },
    },
    watch: {
        projects: "showCovers",
        viewMode: "showCovers",
    },
    async created() {
        try {
            await this.fetchCurrentUser();
            await this.fetchProjects();
            await this.fetchAllProjectTags();
            await this.fetchFonts();
        } catch (error) {
            this.addError(error);
        }
    },
    methods: {
        plural,
        shortDate,
        showCovers() {
            if (this.viewMode === "grid") {
                this.loadCovers(this.projects.map((project) => project.id));
            }
        },
        onSortChange(event) {
            const [field, direction] = event.target.value.split(":");
            this.sortProjects({ field, direction: Number(direction) });
        },
        ...mapActions("projects", [
            "closeCreateModal",
            "closeDeleteModal",
            "createNewProject",
            "createNewProjectTag",
            "deleteProject",
            "fetchAllProjectTags",
            "fetchFonts",
            "fetchProjects",
            "fetchNextPage",
            "openCreateModal",
            "openDeleteModal",
            "sortProjects",
        ]),
        ...mapActions("alerts", ["addError"]),
        ...mapActions("user", ["fetchCurrentUser"]),
    },
};
</script>
