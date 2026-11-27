<template>
    <div
        :class="{ 'escr-toolbar': true, [`escr-${panelType}-toolbar`]: true }"
    >
        <div class="escr-editortools-switcher">
            <VMenu
                placement="bottom-start"
                theme="vertical-menu"
                :distance="8"
                :shown="panelMenuOpen"
                :triggers="[]"
                :auto-hide="true"
                @apply-hide="closePanelMenu"
            >
                <EscrButton
                    :disabled="disabled"
                    :on-click="openPanelMenu"
                    color="text-alt"
                    :aria-label="`${panel.label} panel: change panel`"
                >
                    <template #button-icon>
                        <component :is="panel.icon" />
                    </template>
                    <template #button-icon-right>
                        <ChevronDownIcon />
                    </template>
                </EscrButton>
                <template #popper>
                    <ul class="escr-vertical-menu">
                        <li
                            v-for="option in panels"
                            :key="option.type"
                        >
                            <button
                                type="button"
                                @mousedown="() => onSwitchPanel({
                                    index: panelIndex, panel: option.type
                                })"
                            >
                                <component :is="option.icon" />
                                <span>{{ option.label }}</span>
                            </button>
                        </li>
                    </ul>
                </template>
            </VMenu>
        </div>
        <!-- panel tools scroll sideways when they don't fit; the scrollbar is hidden and
             an anchor (over a soft fade) shows each direction that can still scroll -->
        <div class="escr-toolbar-tools">
            <div
                ref="scroller"
                class="escr-toolbar-scroller"
                @scroll.passive="updateScrollAnchors"
                @wheel="onToolsWheel"
            >
                <slot name="editor-tools-center" />
            </div>
            <button
                v-if="canScrollStart"
                type="button"
                class="escr-toolbar-anchor escr-toolbar-anchor-start"
                tabindex="-1"
                aria-label="Scroll tools back"
                @mousedown.prevent
                @click="scrollTools(-1)"
            >
                <ChevronLeftIcon />
            </button>
            <button
                v-if="canScrollEnd"
                type="button"
                class="escr-toolbar-anchor escr-toolbar-anchor-end"
                tabindex="-1"
                aria-label="Scroll tools forward"
                @mousedown.prevent
                @click="scrollTools(1)"
            >
                <ChevronRightIcon />
            </button>
        </div>
        <div
            v-if="editorPanels.length > 1 && !disabled"
            class="escr-editortools-close"
        >
            <VDropdown
                class="escr-editortools-close"
                theme="escr-tooltip-small"
                placement="bottom"
                :distance="8"
                :triggers="['hover']"
            >
                <button
                    :aria-label="`Close ${panelName} panel`"
                    type="button"
                    @mousedown="() => removeEditorPanel(panelType)"
                >
                    <RemovePanelIcon />
                </button>
                <template #popper>
                    Close {{ panelName }} panel
                </template>
            </VDropdown>
        </div>
    </div>
</template>
<script>
import { ChevronDown, ChevronLeft, ChevronRight, X } from "lucide";
import EscrButton from "../Button/Button.vue";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import PANELS from "./panels";
import { Dropdown as VDropdown, Menu as VMenu } from "floating-vue";
import { mapActions, mapState } from "vuex";
import "./EditorToolbar.css";

const ChevronDownIcon = lucideIcon(ChevronDown);
const ChevronLeftIcon = lucideIcon(ChevronLeft);
const ChevronRightIcon = lucideIcon(ChevronRight);
const RemovePanelIcon = lucideIcon(X);

export default {
    name: "EscrEditorToolbar",
    components: {
        ChevronDownIcon,
        ChevronLeftIcon,
        ChevronRightIcon,
        EscrButton,
        RemovePanelIcon,
        VDropdown,
        VMenu,
    },
    props: {
        /**
         * True if all buttons and tools should be disabled
         */
        disabled: {
            type: Boolean,
            required: true,
        },
        /**
         * The index of this panel, to allow swapping panels
         */
        panelIndex: {
            type: Number,
            required: true,
        },
        /**
         * The type of panel this toolbar is for
         */
        panelType: {
            type: String,
            required: true,
        },
    },
    data() {
        return {
            panelMenuOpen: false,
            panels: PANELS,
            canScrollStart: false,
            canScrollEnd: false,
        }
    },
    mounted() {
        // the tools' width changes with the panel width and with the tools shown (modes)
        this.resizeObserver = new ResizeObserver(() => this.updateScrollAnchors());
        this.resizeObserver.observe(this.$refs.scroller);
        for (const child of this.$refs.scroller.children) this.resizeObserver.observe(child);
        this.updateScrollAnchors();
    },
    beforeDestroy() {
        this.resizeObserver?.disconnect();
    },
    computed: {
        ...mapState({
            editorPanels: (state) => state.document.editorPanels,
        }),
        panel() {
            return PANELS.find((p) => p.type === this.panelType) || { label: "", icon: null };
        },
        panelName() {
            return this.panel.label;
        },
    },
    methods: {
        ...mapActions("document", ["removeEditorPanel", "switchEditorPanel"]),
        closePanelMenu() {
            this.panelMenuOpen = false;
        },
        onSwitchPanel({ index, panel }) {
            this.switchEditorPanel({ index, panel });
            this.closePanelMenu();
        },
        openPanelMenu() {
            this.panelMenuOpen = true;
        },
        updateScrollAnchors() {
            const el = this.$refs.scroller;
            if (!el) return;
            const max = el.scrollWidth - el.clientWidth;
            this.canScrollStart = el.scrollLeft > 1;
            this.canScrollEnd = el.scrollLeft < max - 1;
        },
        onToolsWheel(event) {
            // a vertical mouse wheel scrolls the tools sideways (trackpads scroll natively)
            const el = this.$refs.scroller;
            if (el.scrollWidth <= el.clientWidth) return;
            if (Math.abs(event.deltaY) <= Math.abs(event.deltaX)) return;
            const lineHeight = event.deltaMode === 1 ? 32 : 1;
            el.scrollLeft += event.deltaY * lineHeight;
            event.preventDefault();
        },
        scrollTools(direction) {
            const el = this.$refs.scroller;
            el.scrollBy({ left: direction * el.clientWidth * 0.7, behavior: "smooth" });
        },
    },
}
</script>
