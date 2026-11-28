<template>
    <!--
        On the image itself (inside its zoom container, so it pans and zooms
        with it) while a task runs on it:
        - segmenting: a scanner lamp passes down the page and returns;
        - transcribing: the image's own lines light up one after the other,
          in reading order, as if being read.
        Only transforms and opacity are animated; the script runs once per line.
    -->
    <div
        v-if="running"
        :class="['escr-part-scan', `is-${mode}`, `is-${runningStatus}`]"
        aria-hidden="true"
    >
        <div class="escr-part-scan-veil" />
        <div
            v-if="mode === 'scan'"
            class="escr-part-scan-lamp"
        />
        <template v-else>
            <svg
                class="escr-part-scan-lines"
                :viewBox="`0 0 ${width} ${height}`"
                preserveAspectRatio="none"
            >
                <polygon
                    v-for="(shape, index) in shapes"
                    :key="shape.pk"
                    :points="shape.points"
                    :class="{ read: index < current }"
                />
            </svg>
            <div
                v-if="head"
                :key="`${cycle}-${current}`"
                class="escr-part-scan-head"
                :style="head.box"
                @animationend="next"
            >
                <div
                    :class="['escr-part-scan-glow', { rtl }]"
                    :style="{ animationDuration: `${head.duration}ms` }"
                />
            </div>
        </template>
    </div>
</template>
<script>
import { mapGetters, mapState } from "vuex";
import "./PartTaskScan.css";

// time to read a line as wide as the page, and the shortest a line takes (ms)
const PAGE_WIDTH_TIME = 1400;
const MIN_LINE_TIME = 450;
// a pause on the last line before reading again from the top
const LOOP_PAUSE = 900;

export default {
    name: "EscrPartTaskScan",
    data() {
        return {
            current: 0,
            // counts the passes, so a page of one line is read again too
            cycle: 0,
            restartTimer: null,
        };
    },
    computed: {
        ...mapGetters("partTasks", ["running", "runningStatus"]),
        ...mapState({
            lines: (state) => state.lines.all,
            size: (state) => state.parts.image.size,
            textDirection: (state) => state.document.mainTextDirection,
        }),
        width() {
            return (this.size && this.size[0]) || 1;
        },
        height() {
            return (this.size && this.size[1]) || 1;
        },
        rtl() {
            return typeof this.textDirection === "string" && this.textDirection.endsWith("rl");
        },
        /**
         * The lines' outlines (their masks, or a band around the baseline), in
         * reading order, in image pixels.
         */
        shapes() {
            const pad = this.height * 0.008;
            return [...this.lines]
                .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                .map((line) => {
                    let polygon = line.mask && line.mask.length > 2 ? line.mask : null;
                    if (!polygon && line.baseline && line.baseline.length > 1) {
                        const top = line.baseline.map(([x, y]) => [x, y - pad * 3]);
                        const bottom = line.baseline.map(([x, y]) => [x, y + pad]).reverse();
                        polygon = [...top, ...bottom];
                    }
                    if (!polygon) return null;
                    const xs = polygon.map((p) => p[0]);
                    const ys = polygon.map((p) => p[1]);
                    return {
                        pk: line.pk,
                        polygon,
                        points: polygon.map((p) => p.join(",")).join(" "),
                        x: Math.min(...xs),
                        y: Math.min(...ys),
                        w: Math.max(...xs) - Math.min(...xs) || 1,
                        h: Math.max(...ys) - Math.min(...ys) || 1,
                    };
                })
                .filter(Boolean);
        },
        /** Transcribing an image with lines reads them; anything else scans. */
        mode() {
            return this.running === "transcribe" && this.shapes.length ? "read" : "scan";
        },
        /**
         * The line being read: its box (in % of the image), clipped to its
         * outline, and how long it takes.
         */
        head() {
            const shape = this.shapes[this.current];
            if (!shape) return null;
            const pct = (value, of) => `${(value / of) * 100}%`;
            const clip = shape.polygon
                .map(([x, y]) => `${pct(x - shape.x, shape.w)} ${pct(y - shape.y, shape.h)}`)
                .join(", ");
            // queued: nothing is being read yet, so go slower
            const pace = this.runningStatus === "pending" ? 1.8 : 1;
            return {
                box: {
                    left: pct(shape.x, this.width),
                    top: pct(shape.y, this.height),
                    width: pct(shape.w, this.width),
                    height: pct(shape.h, this.height),
                    clipPath: `polygon(${clip})`,
                },
                duration: Math.round(
                    Math.max(MIN_LINE_TIME, (shape.w / this.width) * PAGE_WIDTH_TIME) * pace,
                ),
            };
        },
    },
    watch: {
        running() {
            this.restart();
        },
        shapes() {
            if (this.current >= this.shapes.length) this.restart();
        },
    },
    beforeDestroy() {
        clearTimeout(this.restartTimer);
    },
    methods: {
        next() {
            if (this.current < this.shapes.length - 1) {
                this.current += 1;
                return;
            }
            // the page is read: hold it a moment, then start again from the top
            clearTimeout(this.restartTimer);
            this.restartTimer = setTimeout(() => this.restart(), LOOP_PAUSE);
        },
        restart() {
            clearTimeout(this.restartTimer);
            this.current = 0;
            this.cycle += 1;
        },
    },
};
</script>
