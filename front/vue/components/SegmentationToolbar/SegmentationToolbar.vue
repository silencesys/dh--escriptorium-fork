<template>
    <EditorToolbar
        panel-type="segmentation"
        :disabled="disabled"
        :panel-index="panelIndex"
    >
        <template #editor-tools-center>
            <div class="escr-editortools-paneltools">
                <!-- change view mode -->
                <SegmentedButtonGroup
                    color="secondary"
                    name="segmentation-view-mode"
                    :disabled="disabled"
                    :options="modeOptions"
                    :on-change-selection="onChangeMode"
                />
                <!-- drawing tools, and actions on the selection -->
                <DetachableToolbar
                    v-if="!toolbarDetached"
                    :disabled="disabled"
                    :display-mode="displayMode"
                    :has-points-selection="hasPointsSelection"
                    :has-selection="hasSelection"
                    :is-drawing="isDrawing"
                    :region-labels-enabled="regionLabelsEnabled"
                    :on-toggle-region-labels="onToggleRegionLabels"
                    :on-change-selection-type="onChangeSelectionType"
                    :on-delete="onDelete"
                    :on-join="onJoin"
                    :on-link="onLink"
                    :on-unlink="onUnlink"
                    :on-reverse="onReverse"
                    :selected-type="selectedType"
                    :selection-is-linked="selectionIsLinked"
                    :selection-is-unlinked="selectionIsUnlinked"
                    :toggle-tool="toggleTool"
                    :toggle-toolbar-detached="toggleToolbarDetached"
                    :tool="tool"
                    :toolbar-detached="false"
                />
                <!-- history and display settings, at the end of the row -->
                <div class="escr-seg-toolbar-end">
                    <VDropdown
                        id="undo"
                        theme="escr-tooltip-small"
                        placement="bottom"
                        :distance="8"
                        :triggers="['hover']"
                    >
                        <EscrButton
                            id="undo-button"
                            aria-label="undo"
                            color="text"
                            :on-click="onUndo"
                            :disabled="disabled || !canUndo"
                        >
                            <template #button-icon>
                                <UndoIcon />
                            </template>
                        </EscrButton>
                        <template #popper>
                            Undo (Ctrl Z)
                        </template>
                    </VDropdown>
                    <VDropdown
                        id="redo"
                        theme="escr-tooltip-small"
                        placement="bottom"
                        :distance="8"
                        :triggers="['hover']"
                    >
                        <EscrButton
                            id="redo-button"
                            aria-label="redo"
                            color="text"
                            :on-click="onRedo"
                            :disabled="disabled || !canRedo"
                        >
                            <template #button-icon>
                                <RedoIcon />
                            </template>
                        </EscrButton>
                        <template #popper>
                            Redo (Ctrl Y)
                        </template>
                    </VDropdown>
                    <VMenu
                        placement="bottom-end"
                        theme="vertical-menu"
                        :distance="8"
                        :triggers="['click']"
                    >
                        <EscrButton
                            color="text"
                            aria-label="Display and ordering options"
                            title="Display and ordering options"
                            :disabled="disabled"
                            :on-click="() => {}"
                        >
                            <template #button-icon>
                                <MoreIcon />
                            </template>
                        </EscrButton>
                        <template #popper>
                            <ul
                                class="escr-vertical-menu escr-seg-options"
                                role="menu"
                            >
                                <li>
                                    <button
                                        type="button"
                                        role="menuitemcheckbox"
                                        :aria-checked="String(lineNumberingEnabled)"
                                        @click="onToggleLineNumbering({
                                            target: { checked: !lineNumberingEnabled },
                                        })"
                                    >
                                        <CheckIcon :class="checkClass(lineNumberingEnabled)" />
                                        <span>Show line numbers</span>
                                        <kbd>N</kbd>
                                    </button>
                                </li>
                                <li v-if="displayMode === 'regions'">
                                    <button
                                        type="button"
                                        role="menuitemcheckbox"
                                        :aria-checked="String(regionLabelsEnabled)"
                                        @click="onToggleRegionLabels"
                                    >
                                        <CheckIcon :class="checkClass(regionLabelsEnabled)" />
                                        <span>Show region labels</span>
                                    </button>
                                </li>
                                <li class="new-section">
                                    <button
                                        type="button"
                                        role="menuitemcheckbox"
                                        :aria-checked="String(autoOrder)"
                                        @click="onToggleAutoOrder"
                                    >
                                        <CheckIcon :class="checkClass(autoOrder)" />
                                        <span>Reorder lines automatically</span>
                                    </button>
                                </li>
                                <li v-if="!autoOrder">
                                    <button
                                        v-close-popper
                                        type="button"
                                        role="menuitem"
                                        @click="onRecalculateOrdering"
                                    >
                                        <ReorderIcon />
                                        <span>Reorder lines now</span>
                                    </button>
                                </li>
                                <li
                                    v-if="!hasMasks && lines.length > 0"
                                    class="new-section"
                                >
                                    <button
                                        v-close-popper
                                        type="button"
                                        role="menuitem"
                                        @click="processLines"
                                    >
                                        <CalculateMasksIcon />
                                        <span>Calculate masks</span>
                                    </button>
                                </li>
                            </ul>
                        </template>
                    </VMenu>
                </div>
            </div>
        </template>
    </EditorToolbar>
</template>

<script>
import { mapState, mapGetters } from "vuex";
import DetachableMixin from "./DetachableMixin.vue";
import DetachableToolbar from "./DetachableToolbar.vue";
import EditorToolbar from "../EditorToolbar/EditorToolbar.vue";
import EscrButton from "../Button/Button.vue";
import SegmentedButtonGroup from "../SegmentedButtonGroup/SegmentedButtonGroup.vue";
import { Dropdown as VDropdown, Menu as VMenu, VClosePopper } from "floating-vue";
import "../VerticalMenu/VerticalMenu.css";
import "./SegmentationToolbar.css";
import {
    ArrowDown01,
    Check,
    Ellipsis,
    LayoutTemplate,
    RectangleHorizontal,
    Redo2,
    ScanLine,
    Spline,
    Undo2,
} from "lucide";
import lucideIcon from "../Icons/Lucide/lucideIcon";

const LinesIcon = lucideIcon(Spline);
const MasksIcon = lucideIcon(RectangleHorizontal);
const RegionsIcon = lucideIcon(LayoutTemplate);
const RedoIcon = lucideIcon(Redo2);
const UndoIcon = lucideIcon(Undo2);
const CheckIcon = lucideIcon(Check);
const MoreIcon = lucideIcon(Ellipsis);
const ReorderIcon = lucideIcon(ArrowDown01);
const CalculateMasksIcon = lucideIcon(ScanLine);

export default {
    name: "EscrSegmentationToolbar",
    components: {
        CalculateMasksIcon,
        CheckIcon,
        DetachableToolbar,
        EditorToolbar,
        EscrButton,
        MoreIcon,
        RedoIcon,
        ReorderIcon,
        SegmentedButtonGroup,
        UndoIcon,
        VDropdown,
        VMenu,
    },
    directives: {
        closePopper: VClosePopper,
    },
    mixins: [DetachableMixin],
    props: {
        /**
         * True if redo is currently possible
         */
        canRedo: {
            type: Boolean,
            required: true,
        },
        /**
         * True if undo is currently possible
         */
        canUndo: {
            type: Boolean,
            required: true,
        },
        /**
         * True if a drawing is currently in progress, in which case the toolbar should
         * not add or remove icons.
         */
        isDrawing: {
            type: Boolean,
            required: true,
        },
        /**
         * True if line numbering is currently toggled on
         */
        lineNumberingEnabled: {
            type: Boolean,
            required: true,
        },
        /**
         * Callback function for changing the display mode
         */
        onChangeMode: {
            type: Function,
            required: true,
        },
        /**
         * Callback function for turning line numbering on and off
         */
        onToggleLineNumbering: {
            type: Function,
            required: true,
        },
        /**
         * Callback function for redo
         */
        onRedo: {
            type: Function,
            required: true,
        },
        /**
         * Callback function for undo
         */
        onUndo: {
            type: Function,
            required: true,
        },
        /**
         * The index of this panel, to allow swapping in EditorToolbar dropdown
         */
        panelIndex: {
            type: Number,
            required: true,
        },
        processLines: {
            type: Function,
            required: true,
        },
        autoOrder: {
            type: Boolean,
            required: true
        },
        onToggleAutoOrder: {
            type: Function,
            required: true
        },
        onRecalculateOrdering: {
            type: Function,
            required: true
        },
        regionLabelsEnabled: {
            type: Boolean,
            required: true,
            default: false,
        },
        onToggleRegionLabels: {
            type: Function,
            required: true,
            default: () => {},
        },

    },
    computed: {
        ...mapState({
            "lines": (state) => state.lines.all,
        }),
        ...mapGetters("lines", ["hasMasks"]),
        /**
         * Get objects for the three modes (lines, regions, masks)
         */
        modeOptions() {
            return [
                {
                    value: "lines",
                    label: LinesIcon,
                    selected: this.displayMode === "lines",
                    tooltip: "Lines mode (L)",
                },
                {
                    value: "masks",
                    label: MasksIcon,
                    selected: this.displayMode === "masks",
                    tooltip: "Masks mode (M)",
                },
                {
                    value: "regions",
                    label: RegionsIcon,
                    selected: this.displayMode === "regions",
                    tooltip: "Regions mode (R)",
                },
            ]
        },
    },
    methods: {
        /** Check mark of a menu option: hidden (but keeping its room) while off */
        checkClass(on) {
            return { "escr-check-off": !on };
        },
    },
}
</script>
