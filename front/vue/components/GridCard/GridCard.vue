<template>
    <li class="escr-grid-card">
        <div
            class="escr-grid-card-cover"
            aria-hidden="true"
        >
            <img
                v-for="src in covers"
                :key="src"
                :src="src"
                alt=""
                loading="lazy"
                decoding="async"
            >
            <component
                :is="placeholderIcon"
                v-if="!covers.length"
                class="escr-grid-card-placeholder"
            />
        </div>
        <div class="escr-grid-card-body">
            <h3 class="escr-grid-card-title">
                <!-- the link covers the card (custom/lists.css) -->
                <a
                    :href="href"
                    class="escr-grid-card-link"
                >{{ title }}</a>
            </h3>
            <p class="escr-grid-card-meta">
                <slot name="meta" />
            </p>
            <EscrTags
                v-if="tags.length"
                :tags="tags"
            />
        </div>
        <div
            v-if="$slots.actions"
            class="escr-grid-card-actions"
        >
            <slot name="actions" />
        </div>
    </li>
</template>
<script>
import EscrTags from "../Tags/Tags.vue";

/*
 * A project or a document as a card of a grid (ul.escr-card-grid): its
 * cover images, or a placeholder icon, its name linking to it, a line about
 * it, its tags, and actions shown on hover or focus. Styles: custom/lists.css.
 */
export default {
    name: "EscrGridCard",
    components: { EscrTags },
    props: {
        /**
         * Up to a few image URLs, shown side by side as the cover.
         */
        covers: {
            type: Array,
            default: () => [],
        },
        href: {
            type: String,
            required: true,
        },
        /**
         * Icon component shown on a card without images.
         */
        placeholderIcon: {
            type: [Object, Function],
            required: true,
        },
        /**
         * Tags as EscrTags takes them ({ pk, name, color | variant }).
         */
        tags: {
            type: Array,
            default: () => [],
        },
        title: {
            type: String,
            required: true,
        },
    },
};
</script>
