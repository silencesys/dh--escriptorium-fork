<template>
    <div class="escr-train-form">
        <div
            class="escr-form-field escr-model-type"
            role="group"
            aria-label="Model type"
        >
            <span
                class="escr-field-label"
                aria-hidden="true"
            >
                Type
            </span>
            <EscrSegmentedButtonGroup
                name="model-type-toggle"
                :disabled="isSubmitting"
                :options="modelTypeOptions"
                :on-change-selection="onChangeModelType"
            />
        </div>
        <EscrTextField
            class="escr-model-name"
            label="Name"
            placeholder="Name your new model..."
            :disabled="form.override || isSubmitting"
            :value="form.model_name"
            :on-input="onInputName"
            :invalid="dirty && !isValid"
            :errors="
                dirty && !isValid
                    ? ['A name is required unless overwriting']
                    : []
            "
            required
        />
        <div class="escr-base-model-group">
            <EscrAutocompleteField
                :key="modelType"
                class="escr-base-model"
                label="Base model"
                placeholder="None, train from scratch"
                :disabled="isSubmitting"
                :option-groups="modelOptionGroups"
                :on-change="onChangeBaseModel"
            />
            <p class="escr-train-hint">
                Pick a model to fine-tune, or leave empty to train a new one.
            </p>
            <label
                class="escr-overwrite"
                :class="{ 'escr-overwrite--disabled': !form.model || isSubmitting }"
            >
                <input
                    type="checkbox"
                    :disabled="!form.model || isSubmitting"
                    :checked="form.override"
                    aria-describedby="overwrite-help"
                    @change="onChangeOverride"
                >
                <span>Overwrite the base model</span>
            </label>
            <span
                id="overwrite-help"
                class="sr-only"
            >
                You must be the owner of the base model to overwrite its file.
            </span>
        </div>
        <!-- epochs, learning rate, ...: only on servers with our training API -->
        <EscrTrainingSettings
            v-model="options"
            :model-type="modelType"
            :has-base-model="!!form.model"
            :disabled="isSubmitting"
            :errors="optionErrors"
        />
        <!-- what will happen, or what is still missing, then the button -->
        <div class="escr-train-footer">
            <p
                class="escr-train-message"
                :class="{ 'escr-train-message--error': blocker }"
                role="alert"
                aria-live="polite"
            >
                {{ blocker || summary }}
            </p>
            <EscrButton
                class="escr-train-btn"
                color="primary"
                :label="isSubmitting ? 'Starting…' : 'Start training'"
                :disabled="
                    !isValid ||
                        isSubmitting ||
                        !currentCollection.id ||
                        !currentCollection.items ||
                        currentCollection.items.length === 0
                "
                :on-click="submitTraining"
            />
        </div>
    </div>
</template>

<script>
import { mapActions, mapState } from "vuex";
import EscrAutocompleteField from "../../components/AutocompleteDropdown/AutocompleteField.vue";
import EscrButton from "../../components/Button/Button.vue";
// eslint-disable-next-line max-len
import EscrSegmentedButtonGroup from "../../components/SegmentedButtonGroup/SegmentedButtonGroup.vue";
import EscrTextField from "../../components/TextField/TextField.vue";
import EscrTrainingSettings from "../TrainingSettings/TrainingSettings.vue";
import { trainCollectionWithOptions } from "../../../src/api/customTraining";
import "./TrainForm.css";

export default {
    components: {
        EscrAutocompleteField,
        EscrButton,
        EscrSegmentedButtonGroup,
        EscrTextField,
        EscrTrainingSettings,
    },
    data() {
        return {
            dirty: false,
            isSubmitting: false,
            modelType: "recognizer",
            // training settings; empty trains with kraken's defaults
            options: {},
            optionErrors: {},
            form: {
                model_name: "",
                model: null,
                override: false,
            },
        };
    },
    computed: {
        ...mapState("user", ["recognitionModels", "segmentationModels"]),
        ...mapState("collection", {
            currentCollection: (state) => state.currentCollection,
            isCollectionDirty: (state) => state.dirty,
        }),
        isValid() {
            // Require either a new name or an override of an existing model
            return (
                this.form.model_name || (this.form.model && this.form.override)
            );
        },
        modelOptionGroups() {
            const models =
                this.modelType === "recognizer"
                    ? this.recognitionModels
                    : this.segmentationModels;

            const yourModels = [];
            const sharedModels = [];
            const publicModels = [];

            models.forEach((m) => {
                const option = {
                    label: m.name,
                    value: m.pk,
                    selected:
                        this.form.model != null &&
                        this.form.model.toString() === m.pk.toString(),
                };
                if (m.rights === "owner") {
                    yourModels.push(option);
                } else if (m.rights === "public") {
                    publicModels.push(option);
                } else {
                    sharedModels.push(option);
                }
            });

            const groups = [];
            if (yourModels.length > 0) {
                groups.push({ label: "Your Models", options: yourModels });
            }
            if (sharedModels.length > 0) {
                groups.push({ label: "Shared Models", options: sharedModels });
            }
            if (publicModels.length > 0) {
                groups.push({ label: "Public Models", options: publicModels });
            }
            return groups;
        },
        /**
         * What still stands in the way of training, if anything
         */
        blocker() {
            const items = this.currentCollection.items || [];
            if (items.length === 0) {
                return this.dirty
                    ? "Select images to train on first."
                    : "";
            }
            if (!this.currentCollection.id) {
                return "Save the selection as a collection to train on it.";
            }
            return "";
        },
        /**
         * What the training will run on
         */
        summary() {
            const n = (this.currentCollection.items || []).length;
            if (!n) return "Select the images to train on.";
            const images = `${n} ${n === 1 ? "image" : "images"}`;
            const name = this.currentCollection.name || "the collection";
            return this.isCollectionDirty
                ? `Trains on the saved version of ${name}.`
                : `Trains on ${images} from ${name}.`;
        },
        modelTypeOptions() {
            return [
                {
                    label: "Recognition",
                    value: "recognizer",
                    selected: this.modelType === "recognizer",
                },
                {
                    label: "Segmentation",
                    value: "segmenter",
                    selected: this.modelType === "segmenter",
                },
            ];
        },
    },
    mounted() {
        this.fetchRecognizeModels();
        this.fetchSegmentModels();
    },
    methods: {
        ...mapActions("user", ["fetchRecognizeModels", "fetchSegmentModels"]),
        /**
         * Submit model training payload to the backend
         */
        async submitTraining() {
            if (this.isCollectionDirty) {
                const confirmProceed = window.confirm(
                    "You have unsaved changes in your collection. " +
                        "If you start training now, these changes will not be reflected " +
                        "in the training data. Are you sure you want to proceed without saving?",
                );
                if (!confirmProceed) {
                    return;
                }
            }
            this.isSubmitting = true;
            try {
                // rm null/empty values from payload so API doesn't reject them
                const payload = {};
                if (this.form.model_name) {
                    payload.model_name = this.form.model_name;
                }
                if (this.form.model) {
                    payload.model = this.form.model;
                }
                if (this.form.override) {
                    payload.override = this.form.override;
                }

                this.optionErrors = {};
                if (Object.keys(this.options).length) {
                    // our endpoint: upstream's training, with the settings
                    await trainCollectionWithOptions(
                        this.currentCollection.id,
                        this.modelType,
                        { ...payload, options: this.options },
                    );
                } else {
                    await this.$store.dispatch("collection/trainModel", {
                        modelType: this.modelType,
                        payload,
                    });
                }

                this.$store.dispatch("alerts/add", {
                    color: "success",
                    message: "Training job successfully queued!",
                });
            } catch (error) {
                const optionErrors = error?.response?.data?.options;
                if (optionErrors) {
                    // shown with the settings
                    this.optionErrors = typeof optionErrors === "object"
                        ? optionErrors
                        : { non_field_errors: [String(optionErrors)] };
                } else {
                    this.$store.dispatch("alerts/addError", error);
                }
            } finally {
                this.isSubmitting = false;
            }
        },
        /**
         * Input handler for model type toggle
         */
        onChangeModelType(val) {
            this.modelType = val;
            this.form.model = null;
            this.form.override = false;
        },
        /**
         * Input handler for name text field
         */
        onInputName(e) {
            this.form.model_name = e.target.value;
            this.dirty = true;
        },
        /**
         * Input handler for base model selection
         */
        onChangeBaseModel(e) {
            this.form.model = e.target.value;
            this.dirty = true;
            if (!this.form.model) this.form.override = false;
        },
        /**
         * Input handler for override checkbox
         */
        onChangeOverride(e) {
            this.form.override = e.target.checked;
            this.dirty = true;
            if (this.form.override) {
                this.form.model_name = "";
            }
        },
    },
};
</script>
