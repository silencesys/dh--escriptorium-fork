<template>
    <div
        v-if="info && info.available"
        class="escr-training-settings"
    >
        <h2
            id="escr-settings-title"
            class="escr-settings-title"
        >
            Settings
        </h2>
        <div
            class="escr-form-field"
            role="group"
            aria-labelledby="escr-settings-title"
        >
            <div class="escr-settings-mode">
                <button
                    v-for="m in modes"
                    :key="m.value"
                    type="button"
                    :class="{ active: mode === m.value }"
                    :aria-pressed="mode === m.value ? 'true' : 'false'"
                    :disabled="disabled"
                    @click="mode = m.value"
                >
                    {{ m.label }}
                </button>
            </div>
            <p class="escr-train-hint">
                {{ summary }}
            </p>
        </div>

        <!-- every setting, in groups; empty fields keep the default shown in
             them. In each group the larger controls come first. -->
        <div
            v-if="mode === 'custom'"
            class="escr-settings-groups"
        >
            <fieldset
                v-if="isRecognition && !hasBaseModel"
                class="escr-settings-group"
            >
                <legend>Architecture</legend>
                <div class="escr-settings-grid">
                    <label class="escr-setting escr-setting--wide">
                        <span class="sr-only">Architecture</span>
                        <select
                            v-model="fields.architecture"
                            :disabled="disabled"
                        >
                            <option value="">VGSL (kraken's classic)</option>
                            <option value="ppocrv6">PP-OCRv6</option>
                        </select>
                    </label>
                    <label
                        v-if="fields.architecture === 'ppocrv6'"
                        class="escr-setting escr-setting--wide"
                    >
                        <span>Model size</span>
                        <select
                            v-model="fields.variant"
                            :disabled="disabled"
                        >
                            <option value="">Default ({{ defaults.variant || "small" }})</option>
                            <option value="tiny">Tiny</option>
                            <option value="small">Small</option>
                            <option value="medium">Medium</option>
                        </select>
                    </label>
                </div>
            </fieldset>

            <fieldset class="escr-settings-group">
                <legend>Optimization</legend>
                <div class="escr-settings-grid">
                    <label class="escr-setting escr-setting--wide">
                        <span>Schedule</span>
                        <select
                            v-model="fields.schedule"
                            :disabled="disabled"
                        >
                            <option value="">
                                Default ({{ scheduleLabel(defaults.schedule) }})
                            </option>
                            <option
                                v-for="sched in info.choices.schedule"
                                :key="sched"
                                :value="sched"
                            >
                                {{ scheduleLabel(sched) }}
                            </option>
                        </select>
                    </label>
                    <label class="escr-setting">
                        <span>Rate</span>
                        <select
                            v-model="fields.lratePreset"
                            :disabled="disabled"
                        >
                            <option value="">Default ({{ formatRate(defaults.lrate) }})</option>
                            <option
                                v-for="rate in learningRates"
                                :key="rate"
                                :value="rate"
                            >
                                {{ rate }}
                            </option>
                            <option value="custom">Custom…</option>
                        </select>
                    </label>
                    <label class="escr-setting">
                        <span>Warmup (steps)</span>
                        <input
                            v-model="fields.warmup"
                            type="number"
                            min="0"
                            :placeholder="placeholder('warmup')"
                            :disabled="disabled"
                        >
                    </label>
                    <label
                        v-if="isRecognition"
                        class="escr-setting"
                    >
                        <span>Batch size</span>
                        <input
                            v-model="fields.batch_size"
                            type="number"
                            min="1"
                            :max="batchSizeLimit"
                            :placeholder="placeholder('batch_size')"
                            :disabled="disabled"
                            :class="{ invalid: invalid.includes('batch_size') }"
                        >
                    </label>
                    <label
                        v-if="fields.lratePreset === 'custom'"
                        class="escr-setting escr-setting--wide"
                    >
                        <span>Custom rate</span>
                        <input
                            v-model.trim="fields.lrate"
                            type="text"
                            inputmode="decimal"
                            placeholder="e.g. 3e-4 or 0.0003"
                            :class="{ invalid: invalid.includes('lrate') }"
                            :disabled="disabled"
                        >
                    </label>
                    <label
                        v-for="p in scheduleParams"
                        :key="p.key"
                        class="escr-setting"
                    >
                        <span>{{ p.label }}</span>
                        <input
                            v-model.trim="fields[p.key]"
                            type="text"
                            inputmode="decimal"
                            :placeholder="placeholder(p.key)"
                            :class="{ invalid: invalid.includes(p.key) }"
                            :disabled="disabled"
                        >
                    </label>
                </div>
            </fieldset>

            <fieldset class="escr-settings-group">
                <legend>Length</legend>
                <div class="escr-settings-grid">
                    <label class="escr-setting">
                        <span>Max epochs</span>
                        <input
                            v-model="fields.epochs"
                            type="number"
                            min="1"
                            :placeholder="placeholder('epochs')"
                            :disabled="disabled"
                        >
                    </label>
                    <label class="escr-setting">
                        <span>Min epochs</span>
                        <input
                            v-model="fields.min_epochs"
                            type="number"
                            min="0"
                            :placeholder="placeholder('min_epochs')"
                            :disabled="disabled"
                        >
                    </label>
                    <label class="escr-setting escr-setting--check">
                        <input
                            v-model="fields.stopEarly"
                            type="checkbox"
                            :disabled="disabled"
                        >
                        <span>Stop early</span>
                    </label>
                    <label class="escr-setting">
                        <span>Patience (epochs)</span>
                        <input
                            v-model="fields.lag"
                            type="number"
                            min="1"
                            :placeholder="placeholder('lag')"
                            :disabled="disabled || !fields.stopEarly"
                        >
                    </label>
                </div>
            </fieldset>

            <fieldset class="escr-settings-group">
                <legend>Data</legend>
                <div class="escr-settings-grid">
                    <label class="escr-setting escr-setting--wide">
                        <span>Unicode normalization</span>
                        <select
                            v-model="fields.normalization"
                            :disabled="disabled"
                        >
                            <option value="">None</option>
                            <option
                                v-for="n in info.choices.normalization"
                                :key="n"
                                :value="n"
                            >
                                {{ n }}
                            </option>
                        </select>
                    </label>
                    <label class="escr-setting escr-setting--check escr-setting--wide">
                        <input
                            v-model="fields.augment"
                            type="checkbox"
                            :disabled="disabled"
                        >
                        <span>Augment images (helps with little training data)</span>
                    </label>
                </div>
            </fieldset>

            <fieldset class="escr-settings-group">
                <legend>Advanced</legend>
                <div class="escr-settings-grid">
                    <label class="escr-setting escr-setting--wide">
                        <span>Other kraken settings</span>
                        <textarea
                            v-model="fields.extra"
                            rows="3"
                            spellcheck="false"
                            placeholder="--sched-patience 10"
                            :disabled="disabled"
                        />
                    </label>
                    <label
                        v-if="isRecognition && hasBaseModel"
                        class="escr-setting escr-setting--wide"
                    >
                        <span>Train only the last layer first (steps)</span>
                        <input
                            v-model="fields.freeze_backbone"
                            type="number"
                            min="0"
                            placeholder="0, train every layer"
                            :disabled="disabled"
                        >
                    </label>
                </div>
            </fieldset>
        </div>

        <ul
            v-if="errorList.length"
            class="escr-settings-errors"
            role="alert"
        >
            <li
                v-for="e in errorList"
                :key="e"
            >
                {{ e }}
            </li>
        </ul>
    </div>
</template>

<script>
import { retrieveTrainingInfo } from "../../../src/api/customTraining";
import "./TrainingSettings.css";

const SCHEDULE_LABELS = {
    constant: "Constant",
    cosine: "Cosine",
    reduceonplateau: "Reduce on plateau",
    "1cycle": "One cycle",
    exponential: "Exponential",
    step: "Step",
};
// the settings each schedule uses
const SCHEDULE_PARAMS = {
    reduceonplateau: [
        { key: "rop_patience", label: "Reduce after (epochs)" },
        { key: "rop_factor", label: "Reduce by factor" },
    ],
    step: [
        { key: "step_size", label: "Step every (epochs)" },
        { key: "gamma", label: "Decay factor" },
    ],
    exponential: [{ key: "gamma", label: "Decay factor" }],
    cosine: [
        { key: "cos_t_max", label: "Reach the end at (epoch)" },
        { key: "cos_min_lr", label: "Final learning rate" },
    ],
};
// "Faster": fewer epochs and an earlier stop, for servers without a GPU
const FASTER = {
    recognition: { epochs: 30, lag: 5 },
    segmentation: { epochs: 20, lag: 5 },
};
// common learning rates, from fast to careful (fine-tuning)
const LEARNING_RATES = ["1e-2", "5e-3", "1e-3", "5e-4", "3e-4", "2e-4", "1e-4", "5e-5", "1e-5"];
const NUMBER_FIELDS = [
    "epochs", "min_epochs", "lag", "lrate", "warmup", "freeze_backbone", "batch_size",
    "rop_patience", "rop_factor", "step_size", "gamma", "cos_t_max", "cos_min_lr",
];

export default {
    name: "EscrTrainingSettings",
    props: {
        /**
         * Options as sent to the API: empty for kraken's defaults
         */
        value: {
            type: Object,
            default: () => ({}),
        },
        /**
         * "recognizer" or "segmenter"
         */
        modelType: {
            type: String,
            required: true,
        },
        /**
         * Whether a base model is picked (fine-tuning)
         */
        hasBaseModel: {
            type: Boolean,
            default: false,
        },
        disabled: {
            type: Boolean,
            default: false,
        },
        /**
         * The server's complaints about the options, by setting
         */
        errors: {
            type: Object,
            default: () => ({}),
        },
    },
    data() {
        return {
            info: null,
            mode: "default",
            fields: {
                epochs: "",
                min_epochs: "",
                stopEarly: true,
                lag: "",
                lrate: "",
                lratePreset: "",
                warmup: "",
                schedule: "",
                rop_patience: "",
                rop_factor: "",
                step_size: "",
                gamma: "",
                cos_t_max: "",
                cos_min_lr: "",
                freeze_backbone: "",
                batch_size: "",
                architecture: "",
                variant: "",
                augment: false,
                normalization: "",
                extra: "",
            },
        };
    },
    computed: {
        isRecognition() {
            return this.modelType !== "segmenter";
        },
        job() {
            return this.isRecognition ? "recognition" : "segmentation";
        },
        learningRates() {
            return LEARNING_RATES;
        },
        /**
         * The largest batch size this server lets a training choose
         */
        batchSizeLimit() {
            return this.info?.limits?.batch_size || null;
        },
        /**
         * Typed numbers that aren't numbers ("5e-", "abc")
         */
        invalid() {
            return NUMBER_FIELDS.filter((key) => {
                const value = this.fields[key];
                return value !== "" && value !== null && !Number.isFinite(Number(value));
            });
        },
        modes() {
            return [
                { label: "Default", value: "default" },
                { label: "Faster", value: "faster" },
                { label: "Custom", value: "custom" },
            ];
        },
        /**
         * What a training without options uses, for the architecture trained
         */
        defaults() {
            if (!this.info) return {};
            const byArch = this.info.defaults[this.job] || {};
            const arch = this.isRecognition
                ? (!this.hasBaseModel && this.fields.architecture) || "vgsl"
                : "blla";
            return byArch[arch] || Object.values(byArch)[0] || {};
        },
        scheduleParams() {
            return SCHEDULE_PARAMS[this.fields.schedule || this.defaults.schedule] || [];
        },
        /**
         * The options for the API: only what differs from the defaults
         */
        options() {
            if (this.mode === "default") return {};
            if (this.mode === "faster") {
                const options = { ...FASTER[this.job] };
                // fine-tuning: train the new last layer alone for a while
                if (this.isRecognition && this.hasBaseModel) options.freeze_backbone = 1000;
                return options;
            }
            const f = this.fields;
            const options = {};
            const usable = new Set([
                "epochs", "min_epochs", "warmup",
                ...this.scheduleParams.map((p) => p.key),
            ]);
            if (f.stopEarly) usable.add("lag");
            if (this.isRecognition && this.hasBaseModel) usable.add("freeze_backbone");
            if (this.isRecognition) usable.add("batch_size");
            NUMBER_FIELDS.forEach((key) => {
                const value = Number(f[key]);
                if (usable.has(key) && f[key] !== "" && f[key] !== null && Number.isFinite(value)) {
                    options[key] = value;
                }
            });
            // the learning rate: a common one, or a typed one
            delete options.lrate;
            if (f.lratePreset === "custom") {
                const rate = Number(f.lrate);
                if (f.lrate !== "" && Number.isFinite(rate)) options.lrate = rate;
            } else if (f.lratePreset) {
                options.lrate = Number(f.lratePreset);
            }
            const quit = f.stopEarly ? "early" : "fixed";
            if (quit !== this.defaults.quit) options.quit = quit;
            if (f.schedule) options.schedule = f.schedule;
            if (f.augment) options.augment = true;
            if (f.normalization) options.normalization = f.normalization;
            if (this.isRecognition && !this.hasBaseModel && f.architecture) {
                options.architecture = f.architecture;
            }
            const extra = this.parseExtra(f.extra);
            if (options.architecture === "ppocrv6" && f.variant) extra.variant = f.variant;
            if (Object.keys(extra).length) options.extra = extra;
            return options;
        },
        /**
         * In words, what the chosen settings do
         */
        summary() {
            const d = this.defaults;
            const o = { ...d, ...this.options, ...(this.options.extra || {}) };
            const parts = [`Up to ${o.epochs} epochs`];
            if (o.quit === "early") {
                parts.push(`stops after ${o.lag} without improvement`);
            }
            if (this.isRecognition && o.batch_size) {
                parts.push(`in batches of ${o.batch_size} lines`);
            }
            let text = parts.join(", ") + ".";
            if (this.mode === "faster" && this.options.freeze_backbone) {
                text += " Starts by training only the base model's last layer.";
            }
            if (this.mode !== "faster" && this.info?.device === "cpu") {
                text += " This server trains on its CPU: Faster finishes sooner.";
            }
            return text;
        },
        errorList() {
            const list = this.invalid.map((key) => `${key}: not a number (use 0.0005 or 5e-4).`);
            const walk = (errors, prefix) => {
                Object.entries(errors || {}).forEach(([key, value]) => {
                    if (Array.isArray(value)) {
                        const label = key === "non_field_errors" ? "" : `${key}: `;
                        list.push(`${prefix}${label}${value.join(" ")}`);
                    } else if (value && typeof value === "object") {
                        walk(value, `${prefix}${key}.`);
                    } else {
                        list.push(`${prefix}${key}: ${value}`);
                    }
                });
            };
            walk(this.errors, "");
            return list;
        },
    },
    watch: {
        options: {
            deep: true,
            immediate: true,
            handler(options) {
                this.$emit("input", options);
            },
        },
        defaults(defaults) {
            this.fields.stopEarly = defaults.quit === "early";
        },
    },
    async mounted() {
        try {
            const { data } = await retrieveTrainingInfo();
            this.info = data;
            // without a GPU, the shorter run is the better start
            if (data.available && data.device === "cpu") this.mode = "faster";
        } catch (error) {
            // our endpoints missing: train the upstream way, without settings
            this.info = null;
        }
    },
    methods: {
        placeholder(key) {
            const value = this.defaults[key];
            return value === undefined || value === null || value === -1 ? "" : String(value);
        },
        /**
         * 0.0005 as 5e-4, the way learning rates are usually written
         */
        formatRate(rate) {
            if (rate === undefined || rate === null) return "";
            return rate < 0.01 ? Number(rate).toExponential() : String(rate);
        },
        scheduleLabel(schedule) {
            return SCHEDULE_LABELS[schedule] || schedule;
        },
        /**
         * "name = value" lines, or ketos options ("--sched-patience 10
         * --augment"), to an object; the server maps ketos's names
         */
        parseExtra(text) {
            const extra = {};
            (text || "").split(/\n|,/).forEach((line) => {
                const trimmed = line.trim();
                if (trimmed.startsWith("-")) {
                    const tokens = trimmed.split(/\s+/);
                    tokens.forEach((token, i) => {
                        if (!token.startsWith("-")) return;
                        const next = tokens[i + 1];
                        const [key, inline] = token.replace(/^-+/, "").split("=");
                        extra[key] = inline !== undefined
                            ? inline
                            : next && !next.startsWith("-") ? next : "";
                    });
                    return;
                }
                const match = trimmed.match(/^([A-Za-z_][\w-]*)\s*[=:]\s*(.*)$/);
                if (match) extra[match[1]] = match[2].trim();
            });
            return extra;
        },
    },
};
</script>
