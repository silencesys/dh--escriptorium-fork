<template>
    <nav class="escr-global-nav">
        <a
            href="/"
            class="escr-nav-logo"
            aria-label="eScriptorium"
        >
            <EscrLogo />
        </a>
        <div class="escr-upper-navgroup">
            <VMenu
                v-if="isAuthenticated && !searchDisabled"
                placement="right-start"
                theme="vertical-menu"
                :triggers="['click']"
            >
                <button
                    v-if="isAuthenticated && !searchDisabled"
                    v-tooltip="navTip('Search')"
                    href="/search/"
                    aria-label="global search"
                    class="escr-global-search"
                    :class="{
                        'escr-globalnav-icon': true,
                        'escr-globalnav-icon-active': ['/search/', '/find-replace/'].some(
                            (page) => location.href.endsWith(page)
                        ),
                    }"
                >
                    <SearchLargeIcon />
                    <span>Search</span>
                </button>

                <template #popper>
                    <ul class="escr-vertical-menu escr-tasks-menu">
                        <li>
                            <a href="/search/">
                                <span>Search</span>
                            </a>
                        </li>
                        <li>
                            <a href="/find-replace/">
                                <span>Find and Replace</span>
                            </a>
                        </li>
                    </ul>
                </template>
            </VMenu>
            <a
                v-if="isAuthenticated"
                v-tooltip="navTip('Projects')"
                href="/projects/"
                aria-label="projects list"
                :class="{
                    'escr-globalnav-icon': true,
                    'escr-globalnav-icon-active': location.href.endsWith('/projects/'),
                }"
            >
                <HomeIcon />
                <span>Projects</span>
            </a>
            <a
                v-if="isAuthenticated"
                v-tooltip="navTip('Models')"
                href="/models/"
                aria-label="models list"
                :class="{
                    'escr-globalnav-icon': true,
                    'escr-globalnav-icon-active': location.href.endsWith('/models/'),
                }"
            >
                <ModelsIcon />
                <span>Models</span>
            </a>
            <a
                v-if="isAuthenticated && canTrain"
                v-tooltip="navTip('Training')"
                href="/training/"
                aria-label="training page"
                :class="{
                    'escr-globalnav-icon': true,
                    'escr-globalnav-icon-active': location.href.endsWith('/training/'),
                }"
            >
                <TrainIcon />
                <span>Training</span>
            </a>
            <div
                v-if="isAuthenticated"
                class="escr-nav-group"
            >
                <!-- collapsed, the group opens as a menu beside the rail -->
                <VMenu
                    placement="right-start"
                    theme="vertical-menu"
                    :distance="12"
                    :triggers="['click']"
                    :disabled="!collapsed"
                >
                    <button
                        v-tooltip="navTip('Tasks')"
                        type="button"
                        aria-controls="escr-nav-tasks"
                        :aria-expanded="tasksExpanded ? 'true' : 'false'"
                        :class="{
                            'escr-globalnav-icon': true,
                            'escr-nav-group-toggle': true,
                            'escr-globalnav-icon-active': !tasksExpanded && tasksPages.some(
                                (item) => isCurrent(item.href)
                            ),
                        }"
                        @click="toggleTasks"
                    >
                        <TasksIcon />
                        <span>Tasks</span>
                        <ChevronDownIcon
                            :class="{
                                'escr-nav-chevron': true,
                                'escr-nav-chevron--open': tasksOpen,
                            }"
                        />
                    </button>
                    <template #popper>
                        <p class="escr-nav-flyout-title">
                            Tasks
                        </p>
                        <ul class="escr-vertical-menu escr-tasks-menu">
                            <li
                                v-for="item in tasksPages"
                                :key="item.href"
                            >
                                <a
                                    :href="item.href"
                                    :aria-current="isCurrent(item.href) ? 'page' : null"
                                    :class="{ preselected: isCurrent(item.href) }"
                                >
                                    <span>{{ item.label }}</span>
                                </a>
                            </li>
                        </ul>
                    </template>
                </VMenu>
                <ul
                    v-show="tasksExpanded"
                    id="escr-nav-tasks"
                    class="escr-nav-submenu"
                >
                    <li
                        v-for="item in tasksPages"
                        :key="item.href"
                    >
                        <a
                            :href="item.href"
                            :aria-current="isCurrent(item.href) ? 'page' : null"
                            :class="{
                                'escr-globalnav-icon': true,
                                'escr-globalnav-icon-active': isCurrent(item.href),
                            }"
                        >
                            <span>{{ item.label }}</span>
                        </a>
                    </li>
                </ul>
            </div>
            <a
                v-if="isAuthenticated"
                v-tooltip="navTip('Teams')"
                href="/profile/teams/"
                aria-label="teams page"
                :class="{
                    'escr-globalnav-icon': true,
                    'escr-globalnav-icon-active': location.href.endsWith('/profile/teams/'),
                }"
            >
                <PeopleIcon />
                <span>Teams</span>
            </a>
            <!-- actions of the current page (EscrPage passes its EscrSidebar) -->
            <div
                v-if="$scopedSlots.contextual"
                class="escr-contextual-navgroup"
            >
                <slot name="contextual" />
            </div>
        </div>
        <button
            v-tooltip="navTip('Expand sidebar')"
            type="button"
            class="escr-globalnav-icon escr-nav-collapse"
            :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
            :aria-expanded="collapsed ? 'false' : 'true'"
            @click="toggleCollapsed"
        >
            <PanelLeftOpenIcon v-if="collapsed" />
            <PanelLeftCloseIcon v-else />
            <span>Collapse sidebar</span>
        </button>
        <!--
            Top bar, on one line with the logo: the page's breadcrumbs (passed
            by EscrPage) or, when the page has none, its title; the profile
            menu on the right.
        -->
        <header class="escr-topbar">
            <slot name="crumbs">
                <ul class="escr-breadcrumbs">
                    <li class="escr-first-crumb">
                        <span>{{ pageTitle }}</span>
                    </li>
                </ul>
            </slot>
            <EscrThemeSwitch />
            <VMenu
                v-if="isAuthenticated"
                placement="bottom-end"
                theme="vertical-menu"
                :triggers="['click']"
            >
                <button
                    aria-label="expand user profile menu"
                    :class="{
                        'escr-profile-button': true,
                        'escr-profile-button--active': profilePages.some(
                            (page) => location.href.endsWith(page)
                        ),
                    }"
                    type="button"
                >
                    <span
                        class="escr-avatar"
                        aria-hidden="true"
                    >{{ initials }}</span>
                </button>
                <template #popper>
                    <ul class="escr-vertical-menu">
                        <li>
                            <a href="/profile/">
                                <span>Profile Settings</span>
                            </a>
                        </li>
                        <li>
                            <a href="/password_change/">
                                <span>Change Password</span>
                            </a>
                        </li>
                        <li v-if="canInvite">
                            <a href="/invite/">
                                <span>Invite Users</span>
                            </a>
                        </li>
                        <li
                            v-if="isStaff"
                            class="new-section"
                        >
                            <a href="/quotas/instance/">
                                <span>Leaderboard</span>
                            </a>
                        </li>
                        <li v-if="isStaff">
                            <a href="/admin/">
                                <span>Site Administration</span>
                            </a>
                        </li>
                        <li class="new-section">
                            <a href="/logout/">
                                <span>Logout</span>
                            </a>
                        </li>
                    </ul>
                </template>
            </VMenu>
            <a
                v-else
                href="/login"
                aria-label="sign in"
                class="escr-profile-signin"
            >
                <ProfileIcon />
                <span>Sign in</span>
            </a>
        </header>
    </nav>
</template>
<script>
import { Menu as VMenu, VTooltip } from "floating-vue";
import { PanelLeftClose, PanelLeftOpen } from "lucide";
import ChevronDownIcon from "../Icons/ChevronDownIcon/ChevronDownIcon.vue";
import EscrLogo from "../Icons/EscrLogo/EscrLogo.vue";
import HomeIcon from "../Icons/HomeIcon/HomeIcon.vue";
import ModelsIcon from "../Icons/ModelsIcon/ModelsIcon.vue";
import PeopleIcon from "../Icons/PeopleIcon/PeopleIcon.vue";
import ProfileIcon from "../Icons/ProfileIcon/ProfileIcon.vue";
import SearchLargeIcon from "../Icons/SearchLargeIcon/SearchLargeIcon.vue";
import TasksIcon from "../Icons/TasksIcon/TasksIcon.vue";
import TrainIcon from "../Icons/TrainIcon/TrainIcon.vue";
import lucideIcon from "../Icons/Lucide/lucideIcon";
import EscrThemeSwitch from "../ThemeSwitch/ThemeSwitch.vue";
import "../Breadcrumbs/Breadcrumbs.css";
import "../VerticalMenu/VerticalMenu.css";
import "./GlobalNavigation.css";
import { mapActions, mapState } from "vuex";
import baseSettings from "./baseSettings";
import { navState, setNavCollapsed } from "./navState";

const TASKS_OPEN_KEY = "escr-nav-tasks-open";
const PanelLeftCloseIcon = lucideIcon(PanelLeftClose);
const PanelLeftOpenIcon = lucideIcon(PanelLeftOpen);

export default {
    name: "EscrGlobalNavigation",
    components: {
        ChevronDownIcon,
        EscrLogo,
        EscrThemeSwitch,
        HomeIcon,
        ModelsIcon,
        PanelLeftCloseIcon,
        PanelLeftOpenIcon,
        PeopleIcon,
        ProfileIcon,
        SearchLargeIcon,
        TasksIcon,
        TrainIcon,
        VMenu,
    },
    directives: {
        tooltip: VTooltip,
    },
    props: {
        // both default to what the base template says (see baseSettings.js)
        isAuthenticated: {
            type: Boolean,
            default: () => baseSettings.isAuthenticated,
        },
        searchDisabled: {
            type: Boolean,
            default: () => baseSettings.searchDisabled,
        },
    },
    data() {
        return {
            pageTitle: "",
            tasksOpen: false,
            tasksPages: [
                { href: "/quotas/", label: "My Tasks" },
                { href: "/downloads/", label: "My Exports" },
                { href: "/documents/tasks/", label: "Task Monitoring" },
            ],
        };
    },
    computed: {
        ...mapState({
            canInvite: (state) => state.user.canInvite,
            canTrain: (state) => state.user.canTrain,
            isStaff: (state) => state.user.isStaff,
            firstName: (state) => state.user.firstName,
            username: (state) => state.user.username,
        }),
        /** True when the navigation is narrowed to its icons. */
        collapsed() {
            return navState.collapsed;
        },
        /** The Tasks pages are listed inline only in the full-width navigation. */
        tasksExpanded() {
            return this.tasksOpen && !this.collapsed;
        },
        /** First letter of the name, for the profile avatar. */
        initials() {
            const name = (this.firstName || this.username || "").trim();
            return name ? name.slice(0, 1).toUpperCase() : "·";
        },
        location() {
            // helper to access window object from within template
            return window.location;
        },
        profilePages() {
            // pages that will trigger the "profile" button to be in the active state
            return ["/profile/", "/password_change/", "/invite/", "/quotas/instance/"];
        },
    },
    mounted() {
        this.pageTitle = this.getPageTitle();
        // open the Tasks group on its own pages, otherwise as the user left it
        this.tasksOpen = this.tasksPages.some((item) => this.isCurrent(item.href))
            || localStorage.getItem(TASKS_OPEN_KEY) === "true";
        if (this.isAuthenticated) {
            this.fetchCurrentUser();
        }
    },
    methods: {
        ...mapActions("user", [
            "fetchCurrentUser",
        ]),
        /**
         * Crumb for pages without breadcrumbs: the page's <title> ("eScriptorium - X"),
         * or its first heading when the template kept the default title.
         */
        isCurrent(href) {
            return window.location.pathname === href;
        },
        toggleTasks() {
            // collapsed, the click opens the Tasks menu instead
            if (this.collapsed) return;
            this.tasksOpen = !this.tasksOpen;
            localStorage.setItem(TASKS_OPEN_KEY, String(this.tasksOpen));
        },
        toggleCollapsed() {
            setNavCollapsed(!this.collapsed);
        },
        /** Label beside an icon-only row, shown while the navigation is collapsed. */
        navTip(content) {
            return {
                content,
                placement: "right",
                theme: "escr-tooltip-small",
                distance: 12,
                // hover only: after a click the focused row shouldn't keep its label up
                triggers: ["hover"],
                disabled: !this.collapsed,
            };
        },
        getPageTitle() {
            const title = document.title.replace(/^\s*eScriptorium\s*-\s*/, "").trim();
            if (title && title !== "Digital Library") return title;
            const heading = document.querySelector("#main h1, #main h2");
            return (heading && heading.textContent.trim()) || title || "eScriptorium";
        }
    }
}
</script>
