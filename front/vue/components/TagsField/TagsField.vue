<script>
import { Dropdown as VDropdown } from "floating-vue";
import { CheckIcon, PlusIcon } from "../Icons/Lucide/icons";
import EscrButton from "../Button/Button.vue";
import Tags from "../Tags/Tags.vue";
import TextField from "../TextField/TextField.vue";

import "./TagsField.css";
import { tagVariants } from "../../store/util/color";

export default {
    name: "EscrTagsField",
    props: {
        /**
         * Boolean to disable clicking tags or buttons.
         */
        disabled: {
            type: Boolean,
            required: true,
        },
        /**
         * Callback function for submitting after changing the tags selection
         */
        onChange: {
            type: Function,
            required: true,
        },
        /**
         * Callback function for changing the string in the "Add/search tags" field
         */
        onChangeTagName: {
            type: Function,
            required: true,
        },
        /**
         * Callback function for creating a new tag
         */
        onCreateTag: {
            type: Function,
            required: true,
        },
        /**
         * String currently typed into the "Add/search tags" field
         */
        tagName: {
            type: String,
            required: true,
        },
        /**
         * Array of tag objects to populate the list of all tags, each structured as follows:
         * { pk: Number, name: String, variant: Number }
         */
        tags: {
            type: Array,
            required: true,
        },
        /**
         * Array of numbers, which correspond to selected tag primary keys.
         */
        selectedTags: {
            type: Array,
            required: true,
        },
    },
    computed: {
        filteredTags() {
            return this.tags?.filter(
                (tag) => tag.name?.toLowerCase().includes(this.tagName?.toLowerCase())
            ) || [];
        },
    },
    methods: {
        /**
         * Enter in the search field: pick the tag of that name, or create it in the
         * first colour no tag uses yet (the colour picker stays on the button).
         */
        handleKeydown(event) {
            if (event.key !== "Enter" || event.isComposing) return;
            event.preventDefault();
            const name = this.tagName?.trim();
            if (this.disabled || !name) return;
            const existing = this.tags.find(
                (tag) => tag.name?.toLowerCase() === name.toLowerCase()
            );
            if (existing) {
                if (!this.selectedTags.includes(existing.pk)) {
                    this.onChange({ checked: true, tag: existing });
                }
                this.onChangeTagName({ target: { value: "" } });
                return;
            }
            // the picker's 30 colours, past the first (a neutral grey)
            const used = new Set(this.tags.map((tag) => tag.variant));
            const colours = [...Array(29).keys()].map((n) => n + 2);
            const variant = colours.find((n) => !used.has(n))
                || colours[this.tags.length % colours.length];
            this.onCreateTag(tagVariants[variant - 1]);
        },
        /**
         * Determine which variant class to apply based on props.
         */
        tagClasses: Tags.methods.tagClasses,
        /*
         * Helper method to render the color picker
         */
        renderTagColorPicker(h) {
            return [
                h("div", { class: "escr-create-tag" }, [
                    h(
                        VDropdown,
                        {
                            props: {
                                theme: "tags-dropdown",
                            },
                            scopedSlots: {
                                popper: ({ hide }) => h(
                                    "div",
                                    {
                                        class: "escr-tag-colors",
                                    },
                                    [...Array(30).keys()].map((n) =>
                                        h(
                                            "button",
                                            {
                                                class: `escr-tag--variant-${n+1}`,
                                                domProps: {
                                                    disabled: this.disabled,
                                                },
                                                on: {
                                                    click: () => {
                                                        this.onCreateTag(tagVariants[n]);
                                                        hide();
                                                    }
                                                },
                                            },
                                        )
                                    ),
                                ),
                            }
                        },
                        [
                            this.renderAddTagButton(h),
                        ],
                    ),
                ]),
            ]
        },
        /*
         * Helper method to render an individual tag option
         */
        renderTagOption(h, tag) {
            return [
                h(
                    "input",
                    {
                        class: {
                            "sr-only": true
                        },
                        domProps: {
                            id: `field-tag-${tag.pk}`,
                            disabled: this.disabled,
                            name: `field-tag-${tag.pk}`,
                            type: "checkbox",
                            // ensure initial selections are checked on mount
                            checked: this.selectedTags.includes(tag.pk),
                        },
                        on: {
                            change: (e) => this.onChange({ checked: e.target.checked, tag }),
                        },
                    },
                ),
                h(
                    "label",
                    {
                        class: this.tagClasses(tag.variant),
                        domProps: {
                            htmlFor: `field-tag-${tag.pk}`,
                        },
                    },
                    [
                        h("span", tag.name),
                        h(CheckIcon)
                    ],
                ),
            ];
        },
        /*
         * Helper method to render notice about tags hidden by string filter
         */
        renderFilteredTagNotice(h) {
            const filteredTags = this.filteredTags;
            const hiddenSelectedTagCount = this.tags.filter(
                (tag) =>
                    this.selectedTags.includes(tag.pk) &&
                    !filteredTags.some((t) => t.pk === tag.pk),
            ).length;
            if (filteredTags.length === 0) {
                return h(
                    "div",
                    `No matching tags. ${this.tags.length} tag${this.tags.length !== 1 ? "s" : ""
                    } hidden, including ${hiddenSelectedTagCount} selected.`,
                );
            } else if (filteredTags.length < this.tags.length) {
                const hiddenTagCount = this.tags.length - filteredTags.length;
                return h(
                    "div",
                    `+ ${hiddenTagCount
                    } tag${hiddenTagCount !== 1 ? "s" : ""} hidden, including ${
                        hiddenSelectedTagCount
                    } selected tag${hiddenSelectedTagCount !== 1 ? "s" : ""}`,
                );
            }
            return [];
        },
        /*
         * Helper method to render how picking tags works
         */
        renderTagsHelp(h) {
            if (!this.tags.length) return [];
            return h(
                "span",
                { class: "escr-help-text" },
                "Filled tags with a tick are selected: click a tag to select or deselect it. "
                + "Enter selects or creates the tag you typed.",
            );
        },
        /*
         * Helper method to render the "add tag" button
         */
        renderAddTagButton(h) {
            return h(
                EscrButton,
                {
                    props: {
                        color: "text",
                        label: this.tagName
                            ? `Create a tag "${this.tagName}"`
                            : "Create a tag",
                        disabled: this.disabled || !this.tagName || this.tags.some(
                            (tag) => tag.name === this.tagName
                        ),
                        // color picker will bind to this button, so its onClick can be noop
                        onClick: () => {},
                        size: "small",
                    },
                    scopedSlots: {
                        "button-icon": () => {
                            return h(PlusIcon)
                        },
                    },
                },
            )
        },
    },
    render(h) {
        return h(
            "div",
            { class: "escr-tags-field escr-form-field" },
            [
                h("span", { class: "escr-form-label" }, "Tags"),
                h(
                    TextField,
                    {
                        props: {
                            disabled: this.disabled,
                            label: "Add/search tags",
                            labelVisible: false,
                            onInput: this.onChangeTagName,
                            placeholder: "Add/search tags",
                            value: this.tagName,
                            maxLength: 100,
                        },
                        on: {
                            keydown: this.handleKeydown,
                        },
                    }
                ),
                this.renderTagColorPicker(h),
                h(
                    "div",
                    { class: "escr-tag-field-group" },
                    [...this.filteredTags].sort(
                        (a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase())
                    ).map(
                        (tag) => this.renderTagOption(h, tag)
                    ),
                ),
                this.renderFilteredTagNotice(h),
                this.renderTagsHelp(h),
            ],
        );
    },
}
</script>
