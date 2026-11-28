<template>
    <!-- over the panels while a task runs on the open image: locks editing and says why
         (the image itself shows the task: PartTaskScan) -->
    <transition name="escr-part-task-fade">
        <div
            v-if="running"
            :class="['escr-part-task-overlay', `is-${runningStatus}`]"
            role="status"
            aria-live="polite"
        >
            <div
                class="escr-part-task-card"
                :style="cardLeft === null ? null : { left: `${cardLeft}px` }"
            >
                <LoaderIcon class="escr-part-task-spinner" />
                <div class="escr-part-task-text">
                    <strong>{{ title }}</strong>
                    <span>{{ detail }}</span>
                </div>
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        color="text"
                        size="small"
                        label="Edit anyway"
                        :on-click="dismiss"
                    />
                    <template #popper>
                        Stop waiting; changes may be lost when it finishes
                    </template>
                </VDropdown>
            </div>
        </div>
    </transition>
</template>
<script>
import { Dropdown as VDropdown } from "floating-vue";
import { LoaderCircle } from "lucide";
import { mapActions, mapGetters } from "vuex";
import EscrButton from "../Button/Button.vue";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import "./EditorTaskOverlay.css";

const LoaderIcon = lucideIcon(LoaderCircle);

// how often to ask for the task's status, in case its websocket events are missed
const POLL_INTERVAL = 20000;

export default {
    name: "EscrEditorTaskOverlay",
    components: {
        EscrButton,
        LoaderIcon,
        VDropdown,
    },
    data() {
        return {
            pollTimer: null,
            // the card's centre, over the image's panel (null: the middle)
            cardLeft: null,
        };
    },
    computed: {
        ...mapGetters("partTasks", ["running", "runningStatus"]),
        title() {
            return this.running === "segment"
                ? "Segmenting this image"
                : "Transcribing this image";
        },
        detail() {
            return this.runningStatus === "pending"
                ? "Queued · editing is paused until it's done"
                : "Editing is paused until it's done";
        },
    },
    watch: {
        running: {
            immediate: true,
            handler(running) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
                if (!running) return;
                this.pollTimer = setInterval(() => this.poll(), POLL_INTERVAL);
                this.$nextTick(this.placeCard);
                // don't leave a line being typed into under the overlay
                const focused = document.activeElement;
                if (focused && focused.closest && focused.closest(".escr-editor-tabcontent")) {
                    focused.blur();
                }
            },
        },
    },
    mounted() {
        window.addEventListener("resize", this.placeCard);
    },
    beforeDestroy() {
        clearInterval(this.pollTimer);
        window.removeEventListener("resize", this.placeCard);
    },
    methods: {
        ...mapActions("partTasks", ["dismiss", "poll"]),
        /** Centre the card over the panel showing the image, if one does. */
        placeCard() {
            if (!this.running || !this.$el || !this.$el.parentElement) return;
            const image = this.$el.parentElement.querySelector("#seg-zoom-container");
            const panel = image && image.closest(".col.panel");
            if (!panel) {
                this.cardLeft = null;
                return;
            }
            const box = this.$el.getBoundingClientRect();
            const rect = panel.getBoundingClientRect();
            this.cardLeft = Math.round(rect.left - box.left + rect.width / 2);
        },
    },
};
</script>
