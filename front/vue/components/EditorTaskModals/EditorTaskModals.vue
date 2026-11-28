<template>
    <!-- segmenting or transcribing the image open in the editor (new UI) -->
    <div class="escr-editor-task-modals">
        <SegmentModal
            v-if="modal === 'segment'"
            :models="segmentationModels"
            :disabled="submitting"
            :on-cancel="closeModal"
            :on-submit="submitSegment"
            scope="Image"
        />
        <TranscribeModal
            v-if="modal === 'transcribe'"
            :models="recognitionModels"
            :transcriptions="transcriptions"
            :disabled="submitting"
            :on-cancel="closeModal"
            :on-submit="submitTranscribe"
            scope="Image"
        />
        <ConfirmModal
            v-if="modal === 'overwrite'"
            :body-text="'Are you sure you want to continue? Re-segmenting will delete ' +
                'any existing transcriptions.'"
            title="Overwrite Existing Segmentation and Transcriptions"
            confirm-verb="Continue"
            :cannot-undo="true"
            :disabled="submitting"
            :on-cancel="() => setModal('segment')"
            :on-confirm="submitSegment"
        />
    </div>
</template>
<script>
import { mapActions, mapMutations, mapState } from "vuex";
import ConfirmModal from "../ConfirmModal/ConfirmModal.vue";
import SegmentModal from "../SegmentModal/SegmentModal.vue";
import TranscribeModal from "../TranscribeModal/TranscribeModal.vue";

export default {
    name: "EscrEditorTaskModals",
    components: {
        ConfirmModal,
        SegmentModal,
        TranscribeModal,
    },
    computed: {
        ...mapState({
            modal: (state) => state.partTasks.modal,
            submitting: (state) => state.partTasks.submitting,
            recognitionModels: (state) => state.user.recognitionModels,
            segmentationModels: (state) => state.user.segmentationModels,
            transcriptions: (state) => state.transcriptions.all,
        }),
    },
    methods: {
        ...mapActions("partTasks", ["closeModal", "submitSegment", "submitTranscribe"]),
        ...mapMutations("partTasks", ["setModal"]),
    },
};
</script>
