/** @odoo-module **/

// Curated dark theme applied via a plain DOM attribute + localStorage -
// deliberately NOT Odoo's own color_scheme cookie / assets_web_dark
// bundle swap (the previous approach here). That native mechanism only
// covers a handful of widgets in Odoo 18 Community (calendar, file
// viewer, emoji picker) - confirmed directly in a real browser: with
// the dark bundle genuinely loaded and the cookie genuinely set, the
// body background stayed light. This applies our own dark_theme.scss
// against this attribute instead, styling the actual surfaces (forms,
// lists, kanban, dialogs, chatter...) directly - proven first on the
// sibling mepcrm.in product's bpro_ui_prefs module, ported here as-is.
//
// Because switching modes is just a DOM attribute + CSS, not a
// server-rendered bundle choice, there is no reload on toggle and no
// mount-crash hazard from reloading mid-mount (both real problems with
// the cookie-based approach this replaced).

const THEME_KEY = "bpro_hrms_theme_pref"; // "light" | "dark" | "auto"
const darkMedia = window.matchMedia("(prefers-color-scheme: dark)");

function readPref() {
    let value;
    try {
        value = window.localStorage.getItem(THEME_KEY);
    } catch {
        value = null;
    }
    return ["light", "dark", "auto"].includes(value) ? value : "auto";
}

function writePref(mode) {
    try {
        window.localStorage.setItem(THEME_KEY, mode);
    } catch {
        // private browsing - theme still applies for this page's lifetime
    }
}

function applyTheme() {
    const mode = readPref();
    const wantDark = mode === "dark" || (mode === "auto" && darkMedia.matches);
    document.documentElement.setAttribute("data-bpro-theme", wantDark ? "dark" : "light");
}

export function getThemePref() {
    return readPref();
}

export function setThemePref(mode) {
    writePref(mode);
    applyTheme();
}

export function isDarkActive() {
    return document.documentElement.getAttribute("data-bpro-theme") === "dark";
}

// Apply immediately at asset-load time (before the webclient mounts) so
// there is no light flash, and keep "auto" in sync with a live OS
// theme change - safe to call unconditionally here since applyTheme()
// never reloads the page.
applyTheme();
darkMedia.addEventListener("change", () => {
    if (readPref() === "auto") {
        applyTheme();
    }
});
