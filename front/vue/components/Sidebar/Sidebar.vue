<template>
    <!-- page actions, rendered inside the global navigation by EscrPage -->
    <nav
        class="escr-sidebar"
        :aria-label="title || 'page actions'"
    >
        <span
            v-if="title"
            class="escr-sidebar-title"
            aria-hidden="true"
        >{{ title }}</span>
        <ul>
            <li
                v-for="action in actions"
                :key="action.key"
            >
                <!-- each action expands its panel inline, like Tasks; with the
                     navigation collapsed, the panel opens beside the rail instead -->
                <VMenu
                    placement="right-start"
                    theme="vertical-menu"
                    :distance="12"
                    :triggers="['click']"
                    :disabled="!collapsed"
                >
                    <button
                        v-tooltip="{
                            content: action.label,
                            placement: 'right',
                            theme: 'escr-tooltip-small',
                            distance: 12,
                            triggers: ['hover'],
                            disabled: !collapsed,
                        }"
                        :class="classes(action.key)"
                        :disabled="loading"
                        :aria-label="actionLabel(action)"
                        :aria-expanded="isOpen(action.key) ? 'true' : 'false'"
                        :aria-controls="`escr-action-${action.key}`"
                        @click="() => onActionClick(action.key)"
                    >
                        <component
                            :is="action.icon"
                            v-if="action.icon"
                        />
                        <span>{{ action.label }}</span>
                        <ChevronDownIcon
                            :class="{
                                'escr-nav-chevron': true,
                                'escr-nav-chevron--open': isOpen(action.key),
                            }"
                        />
                    </button>
                    <template #popper>
                        <div class="escr-nav-flyout">
                            <p class="escr-nav-flyout-title">
                                {{ action.label }}
                            </p>
                            <div class="escr-selected-action">
                                <component
                                    :is="action.panel"
                                    class="escr-action-panel"
                                    :data="action.data"
                                />
                            </div>
                        </div>
                    </template>
                </VMenu>
                <div
                    v-if="isOpen(action.key)"
                    :id="`escr-action-${action.key}`"
                    class="escr-nav-submenu escr-selected-action"
                >
                    <component
                        :is="action.panel"
                        class="escr-action-panel"
                        :data="action.data"
                    />
                </div>
            </li>
        </ul>
    </nav>
</template>
<script>
import { Menu as VMenu, VTooltip } from "floating-vue";
import { mapActions, mapState } from "vuex";
import ChevronDownIcon from "../Icons/ChevronDownIcon/ChevronDownIcon.vue";
import { navState } from "../GlobalNavigation/navState";
import "./Sidebar.css";

export default {
    name: "EscrSidebar",
    components: { ChevronDownIcon, VMenu },
    directives: { tooltip: VTooltip },
    props: {
        /**
         * A list of sidebar items, each of which should have a unique key (string),
         * a label (string), a panel (component), and optionally an icon (component)
         * and data (object).
         */
        actions: {
            type: Array,
            required: true,
            validator(value) {
                return Array.isArray(value) && value.every(
                    (v) => [
                        "key", "label", "panel",
                    ].every((prop) => Object.hasOwn(v, prop))
                );
            }
        },
        /**
         * A boolean indicating whether or not loading is occurring.
         */
        loading: {
            type: Boolean,
            default: false,
        },
        /**
         * Short heading for the actions, naming what they belong to (e.g. "Project").
         */
        title: {
            type: String,
            default: "",
        },
    },
    computed: {
        ...mapState({
            selectedKey: (state) => state.sidebar.selectedAction,
        }),
        collapsed() {
            return navState.collapsed;
        },
    },
    methods: {
        ...mapActions("sidebar",
            [
                "toggleAction",
            ],
        ),
        /** Whether an action's panel is shown inline (only in the full-width navigation). */
        isOpen(key) {
            return this.selectedKey === key && !this.collapsed;
        },
        actionLabel(action) {
            return `${this.isOpen(action.key) ? "Close" : "Open"} the ${action.label} panel`;
        },
        onActionClick(key) {
            // collapsed, the click opens the panel's menu instead
            if (!this.collapsed) this.toggleAction(key);
        },
        classes(key) {
            return {
                "escr-sidebar-button": true,
                "escr-nav-group-toggle": true,
                "escr-sidebar-button--selected": this.isOpen(key),
            }
        },
    }
}
</script>
