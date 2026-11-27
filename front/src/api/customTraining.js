import axios from "axios";

/*
 * Training with options: this deployment's own endpoints
 * (app/apps/escr_custom), next to upstream's in collection.js.
 */

// what can be set, the defaults, and the device the server trains on
export const retrieveTrainingInfo = async () =>
    await axios.get("/custom/training/");

// train a model on a collection with options (see TrainingSettings.vue)
export const trainCollectionWithOptions = async (collectionId, modelType, payload) =>
    await axios.post(
        `/custom/collections/${collectionId}/${
            modelType === "segmenter" ? "train_segmenter" : "train_recognizer"
        }/`,
        payload,
    );
