import {
    createTranscriptionLayer,
    retrieveDocumentPart,
    segmentDocument,
    transcribeDocument,
} from "../../api";
import { retrieveDocument } from "../api";

/*
 * Segmenting and transcribing the image open in the editor (new UI).
 *
 * The image's own `workflow` (parts store) says whether a task is running on
 * it: while one is, the editor is locked. The server reports progress on the
 * document's websocket ("part:workflow" events, handled here); when a task
 * ends the image's lines, or its new transcription, are reloaded.
 */

// statuses of a task that hasn't ended yet
const RUNNING = ["pending", "ongoing"];
// the tasks the editor starts and waits for
const PROCESSES = ["segment", "transcribe"];
const LABELS = { segment: "Segmentation", transcribe: "Transcription" };
// the text directions the segmenter takes (the segment modal's options)
const TEXT_DIRECTIONS = ["horizontal-lr", "horizontal-rl", "vertical-lr", "vertical-rl"];

export const initialState = () => ({
    // the open modal: "segment", "transcribe", or "overwrite" (confirming a re-segmentation)
    modal: null,
    submitting: false,
    // the layer each transcription task writes to, by image pk: shown when it's done
    layers: {},
});

export const getters = {
    /**
     * The task running on the open image ("segment" or "transcribe"), or null.
     */
    running(state, getters, rootState) {
        const workflow = rootState.parts.workflow || {};
        return PROCESSES.find((process) => RUNNING.includes(workflow[process])) || null;
    },
    /**
     * Its status: "pending" (queued) or "ongoing".
     */
    runningStatus(state, getters, rootState) {
        return getters.running ? rootState.parts.workflow[getters.running] : null;
    },
};

export const mutations = {
    setModal(state, modal) {
        state.modal = modal;
    },
    setSubmitting(state, submitting) {
        state.submitting = submitting;
    },
    setLayer(state, { part, layer }) {
        state.layers = { ...state.layers, [part]: layer };
    },
    clearLayer(state, part) {
        const layers = { ...state.layers };
        delete layers[part];
        state.layers = layers;
    },
};

/** Set one task's status on the open image's workflow. */
const setStatus = (commit, rootState, process, status) => {
    commit(
        "parts/load",
        { workflow: { ...(rootState.parts.workflow || {}), [process]: status } },
        { root: true },
    );
};

export const actions = {
    /**
     * Open the segment or transcribe modal, with its models loaded.
     */
    async openModal({ commit, dispatch, rootState }, kind) {
        commit("setModal", kind);
        commit("document/setBlockShortcuts", true, { root: true });
        const form = rootState.forms[kind];
        if (kind === "segment") {
            // start from lines and regions, in the document's text direction
            if (!form.include.length) {
                commit(
                    "forms/setFieldValue",
                    { form: "segment", field: "include", value: ["lines", "regions"] },
                    { root: true },
                );
            }
            if (!TEXT_DIRECTIONS.includes(form.textDirection)) {
                // the script's direction, else the document's ("ltr" or "rtl")
                const { mainTextDirection, defaultTextDirection } = rootState.document;
                const value = TEXT_DIRECTIONS.includes(mainTextDirection)
                    ? mainTextDirection
                    : (defaultTextDirection === "rtl" ? "horizontal-rl" : "horizontal-lr");
                commit(
                    "forms/setFieldValue",
                    { form: "segment", field: "textDirection", value },
                    { root: true },
                );
            }
        }
        try {
            if (kind === "segment" && !rootState.user.segmentationModels.length) {
                await dispatch("user/fetchSegmentModels", null, { root: true });
            } else if (kind === "transcribe" && !rootState.user.recognitionModels.length) {
                await dispatch("user/fetchRecognizeModels", null, { root: true });
            }
        } catch (error) {
            dispatch("alerts/addError", error, { root: true });
        }
    },
    closeModal({ commit }) {
        commit("setModal", null);
        commit("document/setBlockShortcuts", false, { root: true });
    },
    /**
     * Queue the segmentation of the open image. With "overwrite" checked, asks
     * first (the modal moves to "overwrite"), then runs once confirmed.
     */
    async submitSegment({ state, commit, dispatch, rootState }) {
        const form = rootState.forms.segment;
        if (form.overwrite && state.modal !== "overwrite") {
            commit("setModal", "overwrite");
            return;
        }
        const part = rootState.parts.pk;
        commit("setSubmitting", true);
        try {
            await segmentDocument({
                documentId: rootState.document.id,
                parts: [part],
                steps: form.include.length === 2 ? "both" : form.include[0],
                model: form.model || undefined,
                override: form.overwrite,
                textDirection: form.textDirection,
            });
            // the server says nothing until a worker takes it: show it queued now
            if (rootState.parts.pk === part) {
                setStatus(commit, rootState, "segment", "pending");
            }
            dispatch("closeModal");
            dispatch(
                "alerts/add",
                { color: "success", message: "Segmentation queued" },
                { root: true },
            );
        } catch (error) {
            dispatch("alerts/addError", error, { root: true });
        } finally {
            commit("setSubmitting", false);
        }
    },
    /**
     * Queue the transcription of the open image into the chosen layer (made
     * if it's new).
     */
    async submitTranscribe({ commit, dispatch, rootState }) {
        const form = rootState.forms.transcribe;
        const documentId = rootState.document.id;
        const part = rootState.parts.pk;
        commit("setSubmitting", true);
        try {
            const { data: layer } = await createTranscriptionLayer({
                documentId,
                layerName: form.layerName,
            });
            await transcribeDocument({
                documentId,
                model: form.model,
                transcription: layer.pk,
                parts: [part],
            });
            // a new layer is listed now; it fills in when the task is done
            const all = rootState.transcriptions.all;
            if (!all.find((t) => t.pk === layer.pk)) {
                commit("transcriptions/set", [...all, layer], { root: true });
                commit(
                    "forms/setFieldValue",
                    {
                        form: "transcriptionManagement",
                        field: "transcriptions",
                        value: [
                            ...rootState.forms.transcriptionManagement.transcriptions,
                            layer,
                        ],
                    },
                    { root: true },
                );
            }
            commit("setLayer", { part, layer: layer.pk });
            if (rootState.parts.pk === part) {
                setStatus(commit, rootState, "transcribe", "pending");
            }
            dispatch("closeModal");
            dispatch(
                "alerts/add",
                { color: "success", message: "Transcription queued" },
                { root: true },
            );
        } catch (error) {
            dispatch("alerts/addError", error, { root: true });
        } finally {
            commit("setSubmitting", false);
        }
    },
    /**
     * A "part:workflow" event from the document's websocket.
     */
    async handleWorkflowEvent({ commit, dispatch, rootState }, { id, process, status, reason }) {
        if (!PROCESSES.includes(process) || String(id) !== String(rootState.parts.pk)) return;
        const wasRunning = RUNNING.includes((rootState.parts.workflow || {})[process]);
        if (RUNNING.includes(status)) {
            setStatus(commit, rootState, process, status);
        } else if (status === "done") {
            // each task reports "done" twice (for the image, then for itself): reload once
            if (wasRunning) await dispatch("reload", process);
        } else {
            // error or canceled; a failing task also sends its own message
            setStatus(commit, rootState, process, status);
            if (wasRunning && reason) {
                dispatch(
                    "alerts/add",
                    { color: "alert", message: `${LABELS[process]} stopped: ${reason}` },
                    { root: true },
                );
            }
        }
    },
    /**
     * Ask the server for the running task's status, in case its events were
     * missed (e.g. the websocket dropped).
     */
    async poll({ dispatch, getters, rootState }) {
        const process = getters.running;
        const part = rootState.parts.pk;
        if (!process || !part) return;
        try {
            const { data } = await retrieveDocumentPart(rootState.document.id, part);
            const status = data.workflow && data.workflow[process];
            if (RUNNING.includes(status)) return;
            await dispatch("handleWorkflowEvent", {
                id: part,
                process,
                // a finished task's report isn't listed: no status means it's done
                status: status === "error" || status === "canceled" ? status : "done",
            });
        } catch (error) {
            // try again at the next poll
        }
    },
    /**
     * Unlock the image without waiting for its task (e.g. one stuck in the queue).
     */
    dismiss({ commit, getters, rootState }) {
        if (getters.running) setStatus(commit, rootState, getters.running, "dismissed");
    },
    /**
     * Show what a finished task made: the new lines and regions, or the new
     * transcription.
     */
    async reload({ state, commit, dispatch, rootState }, process) {
        const part = rootState.parts.pk;
        setStatus(commit, rootState, process, "done");
        if (process === "segment") {
            // as after a rotation: drop the image's elements, then fetch them anew
            // (this also clears the segmentation undo history)
            commit("regions/reset", {}, { root: true });
            commit("lines/reset", {}, { root: true });
            commit("imageAnnotations/reset", {}, { root: true });
            commit("textAnnotations/reset", {}, { root: true });
            commit("parts/reset", {}, { root: true });
            try {
                await dispatch("parts/fetchPart", { pk: part }, { root: true });
                // the task reports "done" before its report is closed, so the
                // image may still say it's running
                setStatus(commit, rootState, process, "done");
                await dispatch(
                    "transcriptions/getCurrentContent",
                    rootState.transcriptions.selectedTranscription,
                    { root: true },
                );
                await dispatch("transcriptions/getComparisonContent", {}, { root: true });
            } catch (error) {
                dispatch("alerts/addError", error, { root: true });
            }
            return;
        }

        const layer = state.layers[part];
        commit("clearLayer", part);
        const selected = rootState.transcriptions.selectedTranscription;
        try {
            if (!layer) {
                // queued elsewhere (or before a reload): its layer may be new here
                const { data } = await retrieveDocument(rootState.document.id);
                commit("transcriptions/set", data.transcriptions, { root: true });
            }
            if (layer && String(layer) !== String(selected)) {
                // show the new transcription (selecting it loads its text)
                commit("transcriptions/setSelectedTranscription", layer, { root: true });
            } else {
                await dispatch("transcriptions/getCurrentContent", selected, { root: true });
            }
            if (layer && rootState.transcriptions.comparedTranscriptions.includes(layer)) {
                await dispatch("transcriptions/fetchContent", layer, { root: true });
            }
        } catch (error) {
            dispatch("alerts/addError", error, { root: true });
        }
    },
};

export default {
    namespaced: true,
    state: initialState,
    getters,
    mutations,
    actions,
};
