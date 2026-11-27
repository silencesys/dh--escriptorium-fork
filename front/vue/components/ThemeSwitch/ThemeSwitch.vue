<template>
    <div
        class="escr-theme-switch"
        role="radiogroup"
        aria-label="Colour theme"
    >
        <button
            v-for="option in options"
            :key="option.value"
            type="button"
            role="radio"
            :aria-checked="preference === option.value ? 'true' : 'false'"
            :aria-label="option.label"
            :title="option.label"
            :class="{
                'escr-theme-option': true,
                'escr-theme-option--selected': preference === option.value,
            }"
            @click="setPreference(option.value)"
        >
            <!-- sun -->
            <svg
                v-if="option.value === 'light-mode'"
                viewBox="0 0 24 24"
                aria-hidden="true"
            >
                <circle
                    cx="12"
                    cy="12"
                    r="4"
                />
                <path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4" />
            </svg>
            <!-- moon -->
            <svg
                v-else-if="option.value === 'dark-mode'"
                viewBox="0 0 24 24"
                aria-hidden="true"
            >
                <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
            </svg>
            <!-- monitor -->
            <svg
                v-else
                viewBox="0 0 24 24"
                aria-hidden="true"
            >
                <rect
                    x="3"
                    y="4"
                    width="18"
                    height="12.5"
                    rx="2"
                />
                <path d="M8.5 20h7M12 16.5V20" />
            </svg>
        </button>
    </div>
</template>
<script>
import "./ThemeSwitch.css";

const STORAGE_KEY = "user-theme";
const SYSTEM = "system";
const MODES = ["light-mode", "dark-mode"];

/**
 * Three-state colour theme: light, dark or follow the operating system.
 * The preference is kept in localStorage ("user-theme"); the resolved mode is
 * applied as a light-mode / dark-mode class on <html>.
 */
export default {
    name: "EscrThemeSwitch",
    data() {
        return {
            preference: SYSTEM,
            options: [
                { value: "light-mode", label: "Light theme" },
                { value: "dark-mode", label: "Dark theme" },
                { value: SYSTEM, label: "Use system theme" },
            ],
        };
    },
    created() {
        this.media = window.matchMedia("(prefers-color-scheme: dark)");
        const stored = localStorage.getItem(STORAGE_KEY);
        this.preference = [...MODES, SYSTEM].includes(stored) ? stored : SYSTEM;
        this.apply();
        this.onSystemChange = () => {
            if (this.preference === SYSTEM) this.apply();
        };
        this.media.addEventListener("change", this.onSystemChange);
    },
    beforeDestroy() {
        this.media.removeEventListener("change", this.onSystemChange);
    },
    methods: {
        setPreference(value) {
            this.preference = value;
            localStorage.setItem(STORAGE_KEY, value);
            this.apply();
        },
        apply() {
            const mode = this.preference === SYSTEM
                ? (this.media.matches ? "dark-mode" : "light-mode")
                : this.preference;
            const root = document.documentElement.classList;
            root.remove(...MODES);
            root.add(mode);
        },
    },
};
</script>
