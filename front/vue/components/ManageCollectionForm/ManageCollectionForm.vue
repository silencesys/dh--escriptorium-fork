<template>
    <div class="escr-collection-form">
        <!-- load a saved collection, or start over -->
        <div class="escr-collection-load">
            <EscrDropdownField
                label="Collection"
                :label-visible="true"
                :options="collectionsOptions"
                :on-change="handleLoadCollection"
            />
            <EscrButton
                :disabled="!collectionId"
                label="New"
                color="outline-text"
                :on-click="handleNewCollection"
            >
                <template #button-icon>
                    <PlusIcon />
                </template>
            </EscrButton>
        </div>
        <!-- the current selection: its name, size and whether it is saved -->
        <div class="escr-collection-current">
            <div class="escr-collection-name">
                <button
                    v-if="!isEditingName"
                    type="button"
                    class="escr-collection-name-button"
                    title="Rename the collection"
                    @click="startEditingName"
                >
                    <span>{{ collectionName || "Untitled collection" }}</span>
                    <PencilIcon />
                </button>
                <EscrTextField
                    v-else
                    ref="nameInput"
                    class="escr-collection-name-input"
                    name="virtual-collection-name"
                    label="Collection name"
                    :label-visible="false"
                    placeholder="Name your collection..."
                    :value="collectionName"
                    :on-input="handleNameChange"
                    :on-blur="() => { isEditingName = false; }"
                    :on-keydown="handleNameKeydown"
                    :max-length="512"
                />
            </div>
            <div class="escr-collection-status">
                <span class="escr-collection-stats">
                    {{ imagesLabel }}<template v-if="statusLabel">
                        <span aria-hidden="true">·</span>
                        <span :class="{ 'escr-collection-unsaved': isDirty }">
                            {{ statusLabel }}
                        </span>
                    </template>
                </span>
                <EscrButton
                    label="Save"
                    size="small"
                    :color="isDirty && collectionItems.length ? 'primary' : 'outline-text'"
                    :disabled="
                        isLoadingCollection ||
                            isSavingCollection ||
                            collectionItems.length === 0 ||
                            !isDirty
                    "
                    :on-click="handleSaveCollection"
                />
            </div>
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from "vuex";
import EscrButton from "../../components/Button/Button.vue";
import EscrDropdownField from "../../components/Dropdown/DropdownField.vue";
import EscrTextField from "../../components/TextField/TextField.vue";
import { Pencil, Plus } from "lucide";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import "./ManageCollectionForm.css";

const PencilIcon = lucideIcon(Pencil);
const PlusIcon = lucideIcon(Plus);

export default {
    name: "ManageCollectionForm",
    components: {
        EscrButton,
        EscrDropdownField,
        EscrTextField,
        PencilIcon,
        PlusIcon,
    },
    data() {
        return {
            isEditingName: false,
        };
    },
    computed: {
        ...mapState("collection", {
            collections: (state) => state.collections,
            collectionId: (state) => state.currentCollection.id,
            collectionName: (state) => state.currentCollection.name,
            collectionItems: (state) => state.currentCollection.items,
            isLoadingCollection: (state) => state.loading,
            isSavingCollection: (state) => state.saving,
            isDirty: (state) => state.dirty,
        }),
        /**
         * The user's collections, formatted for the dropdown
         */
        collectionsOptions() {
            return this.collections.map((c) => ({
                value: String(c.id),
                label: c.name,
                selected: c.id === this.collectionId,
            }));
        },
        /**
         * How many images the selection holds
         */
        imagesLabel() {
            const n = this.collectionItems.length;
            return `${n} ${n === 1 ? "image" : "images"}`;
        },
        /**
         * Whether the selection is saved: training needs a saved collection
         */
        statusLabel() {
            if (this.isDirty) return "Unsaved";
            if (this.collectionId) return "Saved";
            return "";
        },
    },
    methods: {
        ...mapActions("collection", ["saveCollection", "loadCollection"]),
        /**
         * Handler for clicking the pencil icon to edit the collection name
         */
        startEditingName() {
            this.isEditingName = true;
            this.$nextTick(() => {
                const input = this.$refs.nameInput?.$el?.querySelector("input");
                if (input) {
                    input.focus();
                }
            });
        },
        /**
         * Update the collection name on state
         */
        handleNameChange(event) {
            this.$store.commit(
                "collection/setCollectionName",
                event.target.value,
            );
        },
        /**
         * Stop editing name on Enter key
         */
        handleNameKeydown(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                this.isEditingName = false;
            }
        },
        /**
         * Persist the collection in the backend
         */
        async handleSaveCollection() {
            // If the user hasn't set a name, default it to "Untitled collection"
            if (!this.collectionName || this.collectionName.trim() === "") {
                this.$store.commit(
                    "collection/setCollectionName",
                    "Untitled collection",
                );
            }
            try {
                await this.saveCollection();
                this.$store.dispatch("alerts/add", {
                    color: "success",
                    message: "Collection saved successfully!",
                });
            } catch (error) {
                this.$store.dispatch("alerts/addError", error);
            }
        },
        /**
         * Load a collection from the backend, prompting user on unsaved
         * changes, and loading the selected parts tab
         */
        handleLoadCollection(event) {
            if (this.isDirty) {
                const confirmDiscard = window.confirm(
                    "You have unsaved changes in your current collection. " +
                    "Are you sure you want to load a new one and discard these changes?"
                );
                if (!confirmDiscard) {
                    return;
                }
            }
            this.loadCollection(event.target.value);
            this.isEditingName = false;
            // send parent to "selected" tab
            this.$emit("loaded");
        },
        /**
         * Reset the collection state to empty, prompting user on unsaved
         * changes, and loading the browse tab
         */
        handleNewCollection() {
            if (this.isDirty) {
                const confirmDiscard = window.confirm(
                    "You have unsaved changes in your current collection. " +
                    "Are you sure you want to start a new one and discard these changes?"
                );
                if (!confirmDiscard) {
                    return;
                }
            }
            this.loadCollection(null);
            this.isEditingName = false;
            // send parent to "browse" tab
            this.$emit("new-started");
        },
    },
};
</script>
