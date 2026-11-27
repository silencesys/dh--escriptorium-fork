<template>
    <div class="escr-toolbar escr-editor-global-toolbar">
        <!-- the element being edited: title, paging, its tools -->
        <div class="escr-editortoolbar-section">
            <slot name="start" />
        </div>

        <!-- view tools, shared by all panels; then adding panels -->
        <div class="escr-editortoolbar-section">
            <VDropdown
                theme="escr-tooltip-small"
                placement="bottom"
                :disabled="disabled"
                :distance="8"
                :triggers="['hover']"
            >
                <ToggleButton
                    id="escr-toggle-select"
                    color="text"
                    :checked="tool === 'select'"
                    :disabled="disabled"
                    :on-change="() => toggleTool('select')"
                >
                    <template #button-icon>
                        <CursorSelectIcon />
                    </template>
                </ToggleButton>
                <template #popper>
                    Select (S)
                </template>
            </VDropdown>
            <VDropdown
                theme="escr-tooltip-small"
                placement="bottom"
                :disabled="disabled"
                :distance="8"
                :triggers="['hover']"
            >
                <ToggleButton
                    id="escr-toggle-pan"
                    color="text"
                    :checked="tool === 'pan'"
                    :disabled="disabled"
                    :on-change="() => toggleTool('pan')"
                >
                    <template #button-icon>
                        <CursorPanIcon />
                    </template>
                </ToggleButton>
                <template #popper>
                    Pan (P)
                </template>
            </VDropdown>
            <div class="new-section with-separator">
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        aria-label="Zoom in"
                        color="text"
                        :on-click="onZoomIn"
                        :disabled="disabled"
                    >
                        <template #button-icon>
                            <ZoomInIcon />
                        </template>
                    </EscrButton>
                    <template #popper>
                        Zoom in (Ctrl +)
                    </template>
                </VDropdown>
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        aria-label="Zoom out"
                        color="text"
                        :on-click="onZoomOut"
                        :disabled="disabled"
                    >
                        <template #button-icon>
                            <ZoomOutIcon />
                        </template>
                    </EscrButton>
                    <template #popper>
                        Zoom out (Ctrl -)
                    </template>
                </VDropdown>
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        aria-label="Reset zoom"
                        color="text"
                        :on-click="onZoomReset"
                        :disabled="disabled"
                    >
                        <template #button-icon>
                            <ZoomResetIcon />
                        </template>
                    </EscrButton>
                    <template #popper>
                        Reset zoom (Ctrl 0)
                    </template>
                </VDropdown>
            </div>
            <div class="new-section with-separator">
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        aria-label="Rotate Counterclockwise"
                        color="text"
                        :on-click="() => onRotate(270)"
                        :disabled="disabled"
                    >
                        <template #button-icon>
                            <RotateCCWIcon />
                        </template>
                    </EscrButton>
                    <template #popper>
                        Rotate Counterclockwise (Ctrl ,)
                    </template>
                </VDropdown>
                <VDropdown
                    theme="escr-tooltip-small"
                    placement="bottom"
                    :distance="8"
                    :triggers="['hover']"
                >
                    <EscrButton
                        aria-label="Rotate Clockwise"
                        color="text"
                        :on-click="() => onRotate(90)"
                        :disabled="disabled"
                    >
                        <template #button-icon>
                            <RotateCWIcon />
                        </template>
                    </EscrButton>
                    <template #popper>
                        Rotate Clockwise (Ctrl .)
                    </template>
                </VDropdown>
            </div>
        </div>

        <!-- panels (at most three) -->
        <div
            v-if="editorPanels.length < 3"
            class="escr-editortoolbar-section new-section with-separator"
        >
            <VDropdown
                placement="bottom-end"
                theme="vertical-menu"
                :shown="addPanelMenuOpen"
                :triggers="[]"
                :auto-hide="true"
                @apply-hide="closeAddPanelMenu"
            >
                <EscrButton
                    :disabled="disabled"
                    :on-click="openAddPanelMenu"
                    color="text"
                    aria-label="Add panel"
                    title="Add panel"
                >
                    <template #button-icon>
                        <AddPanelIcon />
                    </template>
                </EscrButton>
                <template #popper>
                    <ul class="escr-vertical-menu">
                        <li
                            v-for="option in panelsToAdd"
                            :key="option.type"
                        >
                            <button
                                type="button"
                                @mousedown="onAddEditorPanel(option.type)"
                            >
                                <component :is="option.icon" />
                                <span>{{ option.label }}</span>
                            </button>
                        </li>
                    </ul>
                </template>
            </VDropdown>
        </div>
    </div>
</template>
<script>
import { mapActions, mapState } from "vuex";
import {
    Hand, Maximize, MousePointer2, PanelRightOpen,
    RotateCcwSquare, RotateCwSquare, ZoomIn, ZoomOut,
} from "lucide";
import EscrButton from "../Button/Button.vue";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import PANELS from "../EditorToolbar/panels";
import ToggleButton from "../ToggleButton/ToggleButton.vue";
import { Dropdown as VDropdown } from "floating-vue";
import "./EditorGlobalToolbar.css";

const AddPanelIcon = lucideIcon(PanelRightOpen);
const CursorPanIcon = lucideIcon(Hand);
const CursorSelectIcon = lucideIcon(MousePointer2);
const RotateCCWIcon = lucideIcon(RotateCcwSquare);
const RotateCWIcon = lucideIcon(RotateCwSquare);
const ZoomInIcon = lucideIcon(ZoomIn);
const ZoomOutIcon = lucideIcon(ZoomOut);
const ZoomResetIcon = lucideIcon(Maximize);

export default {
    name: "EscrEditorGlobalToolbar",
    components: {
        AddPanelIcon,
        CursorPanIcon,
        CursorSelectIcon,
        EscrButton,
        RotateCCWIcon,
        RotateCWIcon,
        ToggleButton,
        VDropdown,
        ZoomInIcon,
        ZoomOutIcon,
        ZoomResetIcon,
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
         * Callback function to rotate
         */
        onRotate: {
            type: Function,
            required: true,
        },
        /**
         * Callback function to zoom in
         */
        onZoomIn: {
            type: Function,
            required: true,
        },
        /**
         * Callback function to zoom out
         */
        onZoomOut: {
            type: Function,
            required: true,
        },
        /**
         * Callback function to reset zoom
         */
        onZoomReset: {
            type: Function,
            required: true,
        },
        /**
         * Callback function to toggle one of the toggleable tools (pan, select)
         */
        toggleTool: {
            type: Function,
            required: true,
        },
        /**
         * Currently selected tool
         */
        tool: {
            type: String,
            required: true,
        },
    },
    data() {
        return {
            addPanelMenuOpen: false,
        }
    },
    computed: {
        ...mapState({ editorPanels: (state) => state.document.editorPanels }),
        panelsToAdd() {
            return PANELS.filter((panel) => !this.editorPanels.includes(panel.type));
        },
    },
    methods: {
        ...mapActions("document", ["addEditorPanel"]),
        /**
         * Callback to close the add panel menu
         */
        closeAddPanelMenu() {
            this.addPanelMenuOpen = false;
        },
        /**
         * Callback to open the add panel menu
         */
        openAddPanelMenu() {
            this.addPanelMenuOpen = true;
        },
        /**
         * Callback to add a panel and close the menu
         */
        onAddEditorPanel(panelType) {
            this.closeAddPanelMenu();
            this.addEditorPanel(panelType);
        }
    }
}
</script>
