<template>
    <div :class="classes">
        <WarningIcon
            v-if="color === 'danger' || color === 'warning'"
        />
        <InfoFilledIcon
            v-else-if="color === 'secondary'"
        />
        <span>{{ message }}</span>
    </div>
</template>
<script>
import { InfoFilledIcon, WarningIcon } from "../Icons/Lucide/icons";
import "./Alert.css";

export default {
    name: "EscrAlert",
    components: { InfoFilledIcon, WarningIcon },
    props: {
        color: {
            type: String,
            required: true,
            validator(value) {
                return ["secondary", "warning", "danger"].includes(value);
            },
        },
        message: {
            type: String,
            required: true,
        },
    },
    computed: {
        classes() {
            return {
                "escr-alert": true,
                [`escr-alert--${this.color}`]: true,
            };
        },
    },
}
</script>
