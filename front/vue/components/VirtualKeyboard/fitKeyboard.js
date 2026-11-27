/**
 * The virtual keyboard (@escriptorium/virtual-keyboard) opens below the field
 * it types into, at the field's left edge. Make it as wide as `widthSource`
 * (the field, or the panel around it) whenever `field` gets focus; the width
 * reaches the keyboard's stylesheet through the --vk-width property.
 */
export function fitKeyboardOnFocus(field, widthSource = field) {
    if (field.vkFitted) return;
    field.vkFitted = true;
    field.addEventListener("focus", () => {
        const width = widthSource.getBoundingClientRect().width;
        document.documentElement.style.setProperty("--vk-width", `${Math.round(width)}px`);
    });
}
