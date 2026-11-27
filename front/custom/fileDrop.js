/*
 * Drop zones for the file fields of Django forms in the new UI (for now the
 * model upload), without touching their templates: the native file input
 * stays where it is and covers the zone invisibly (custom/forms.css), so
 * clicking, dropping a file, validation and the page's own change handlers
 * all keep working natively. This only adds the zone's text and state.
 */

const FIELDS = [
    {
        input: 'form[action$="/models/new/"] input[type="file"]',
        accept: [".mlmodel", ".safetensors"],
        prompt: "Drop a model file here, or click to browse",
        // the page fills this from the file name: undo that for a refused file
        nameField: 'input[name="name"]',
    },
];

const formatSize = (bytes) => {
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) {
        size /= 1024;
        unit += 1;
    }
    return `${size.toFixed(unit ? 1 : 0)} ${units[unit]}`;
};

function enhance(input, { accept, prompt, nameField }) {
    const zone = input.parentElement;
    if (!zone || zone.classList.contains("escr-file-drop")) return;
    zone.classList.add("escr-file-drop");
    input.setAttribute("accept", accept.join(","));

    const text = document.createElement("div");
    text.className = "escr-file-drop-text";
    text.setAttribute("aria-hidden", "true");
    text.innerHTML = `
        <span class="escr-file-drop-icon"></span>
        <span class="escr-file-drop-title"></span>
        <span class="escr-file-drop-hint"></span>`;
    zone.appendChild(text);
    const title = text.querySelector(".escr-file-drop-title");
    const hint = text.querySelector(".escr-file-drop-hint");

    const render = (error) => {
        const file = input.files && input.files[0];
        zone.classList.toggle("escr-file-drop--filled", Boolean(file));
        zone.classList.toggle("escr-file-drop--error", Boolean(error));
        title.textContent = file ? file.name : prompt;
        hint.textContent = error
            || (file ? `${formatSize(file.size)} · click or drop to replace` : accept.join(" or "));
    };

    input.addEventListener("change", () => {
        const file = input.files && input.files[0];
        const ok = !file || accept.some((ext) => file.name.toLowerCase().endsWith(ext));
        if (!ok) {
            // dropping skips the picker's filter: refuse other files right here
            input.value = "";
            const name = nameField && input.form?.querySelector(nameField);
            if (name && name.value === file.name.replace(/\.[^.]+$/, "")) name.value = "";
            render(`${file.name} is not a model file (${accept.join(" or ")})`);
            return;
        }
        render();
    });
    // highlight while a file is dragged over the zone
    ["dragenter", "dragover"].forEach((type) => input.addEventListener(type, () => {
        zone.classList.add("escr-file-drop--over");
    }));
    ["dragleave", "drop"].forEach((type) => input.addEventListener(type, () => {
        zone.classList.remove("escr-file-drop--over");
    }));

    // large files take a while: say so on the submit button
    const form = input.form;
    const button = form?.querySelector('button[type="submit"]');
    if (button) {
        const label = button.textContent;
        form.addEventListener("submit", () => {
            button.classList.add("escr-submitting");
            button.textContent = "Uploading…";
        });
        // coming back to the page from history restores the button
        window.addEventListener("pageshow", () => {
            button.classList.remove("escr-submitting");
            button.textContent = label;
        });
    }

    render();
}

export default function enhanceFileDrops() {
    FIELDS.forEach((field) => {
        document.querySelectorAll(field.input).forEach((input) => enhance(input, field));
    });
}
