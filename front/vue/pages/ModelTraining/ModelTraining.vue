<template>
    <EscrPage class="escr-model-training">
        <template #page-content>
            <div class="escr-training">
                <header class="escr-training-header">
                    <h1>Model training</h1>
                    <EscrTabs
                        v-model="activeTab"
                        :tabs="trainingDataTabs"
                    />
                </header>
                <div class="escr-training-body">
                    <!-- the training data: browse to pick images, or review the selection -->
                    <div class="escr-training-data">
                        <div
                            v-show="activeTab === 'browse'"
                            id="panel-browse"
                            class="escr-tab-panel"
                            role="tabpanel"
                            aria-labelledby="tab-browse"
                            tabindex="0"
                        >
                            <h2 class="sr-only">
                                Browse
                            </h2>
                            <EscriptoriumBrowser
                                v-if="escrBrowserLoaded"
                                :preselected-project="preselectedProject"
                                :preselected-document="preselectedDocument"
                            />
                            <div
                                v-else
                                class="escr-spinner escr-spinner--secondary"
                                role="status"
                            >
                                <span class="sr-only">Loading browser...</span>
                            </div>
                        </div>
                        <div
                            v-show="activeTab === 'selected'"
                            id="panel-selected"
                            class="escr-tab-panel escr-selected-parts"
                            role="tabpanel"
                            aria-labelledby="tab-selected"
                            tabindex="0"
                        >
                            <h2 class="sr-only">
                                Selected images
                            </h2>
                            <div
                                v-if="isLoadingCollection"
                                class="escr-spinner escr-spinner--secondary"
                                role="status"
                            >
                                <span class="sr-only">Loading collection...</span>
                            </div>
                            <SelectedDocuments v-else-if="collectionItems.length" />
                            <div
                                v-else
                                class="escr-training-empty"
                            >
                                <p>No images selected yet.</p>
                                <p class="escr-training-empty-hint">
                                    Load a saved collection, or pick images to train on.
                                </p>
                                <EscrButton
                                    label="Browse images"
                                    color="outline-text"
                                    :on-click="() => activeTab = 'browse'"
                                />
                            </div>
                        </div>
                    </div>
                    <!-- what to train on and what to train, in order, ending
                         with the start button -->
                    <aside class="escr-training-panel">
                        <section class="escr-training-step">
                            <h2>Training data</h2>
                            <ManageCollectionForm
                                @loaded="activeTab = 'selected'"
                                @new-started="activeTab = 'browse'"
                            />
                        </section>
                        <section class="escr-training-step escr-training-step--model">
                            <h2>Model</h2>
                            <TrainForm />
                        </section>
                    </aside>
                </div>
            </div>
        </template>
    </EscrPage>
</template>
<script>
import { mapActions, mapState } from "vuex";
import EscrPage from "../Page/Page.vue";
import EscrButton from "../../components/Button/Button.vue";
import EscrTabs from "../../components/Tabs/Tabs.vue";
import EscriptoriumBrowser from "../../components/EscriptoriumBrowser/EscriptoriumBrowser.vue";
import ManageCollectionForm from "../../components/ManageCollectionForm/ManageCollectionForm.vue";
import SelectedDocuments from "../../components/EscriptoriumBrowser/SelectedDocuments.vue";
import TrainForm from "../../components/TrainForm/TrainForm.vue";
import "../../components/Common/Card.css";
import "./ModelTraining.css";

export default {
    name: "EscrModelTrainingPage",
    components: {
        EscrButton,
        EscrPage,
        EscrTabs,
        EscriptoriumBrowser,
        ManageCollectionForm,
        SelectedDocuments,
        TrainForm,
    },
    props: {
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
            activeTab: "browse",
            preselectedProject: null,
            preselectedDocument: null,
            escrBrowserLoaded: false,
        };
    },
    computed: {
        ...mapState("collection", {
            collectionItems: (state) => state.currentCollection.items,
            isLoadingCollection: (state) => state.loading,
            isDirty: (state) => state.dirty,
        }),
        /**
         * tabs for training data management, with parts count as badges
         */
        trainingDataTabs() {
            return [
                { label: "Browse", value: "browse" },
                {
                    label: "Selected",
                    value: "selected",
                    badge: this.collectionItems.length
                },
            ];
        }
    },
    async mounted() {
        // fetch all collections
        await this.$store.dispatch("collection/fetchCollections");

        // grab preselected parts/project/doc data from session storage
        const preselected = sessionStorage.getItem("escr-training-data");
        if (preselected) {
            // load parts and document from preselected
            const data = JSON.parse(preselected);
            this.preselectedProject = data.project;
            this.preselectedDocument = data.document;
            await this.loadCollection(null);
            await this.$store.dispatch("collection/addSelectedParts", {
                document: this.preselectedDocument,
                partPks: data.selectedParts,
                partsOverride: data.parts,
            });
            // remove the keys from session storage
            sessionStorage.removeItem("escr-training-data");
            this.activeTab = "selected";
        } else if (this.collectionItems.length > 0) {
            this.activeTab = "selected";
        }
        this.escrBrowserLoaded = true;

        // add beforeunload event handler to show "unsaved changes" prompt
        window.addEventListener("beforeunload", this.handleBeforeUnload);
    },
    beforeDestroy() {
        // clean up beforeunload listener
        window.removeEventListener("beforeunload", this.handleBeforeUnload);
    },
    methods: {
        ...mapActions("collection", ["loadCollection"]),
        /**
         * Intercept browser navigation/close if there are unsaved changes
         */
        handleBeforeUnload(event) {
            if (this.isDirty) {
                event.preventDefault();
                // Chrome requires returnValue to trigger the warning prompt
                event.returnValue = "";
            }
        },
    },
};
</script>
