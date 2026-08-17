/** @odoo-module **/

// Shared cookie-based theme logic. Kept framework-free (no Owl import)
// so it can be reused from any bundle - backend systray today, a
// public-page widget later - without pulling in backend-only deps.
//
// Two cookies, deliberately separate:
// - "color_scheme": Odoo's OWN cookie (web/views/webclient_templates.xml
//   reads it server-side to pick the light or dark asset bundle before
//   any of our JS ever runs). We only ever set/clear it, never invent
//   new values Odoo doesn't already understand.
// - "bpro_theme_pref": OUR record of what the user actually chose -
//   "light", "dark", or "auto". Needed because "auto" has no native
//   Odoo concept; without remembering the user meant "auto" (not
//   "light"), we couldn't tell the two apart on the next page load.

const PREF_COOKIE = "bpro_theme_pref";
const SCHEME_COOKIE = "color_scheme";

function readCookie(name) {
    const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : null;
}

function writeCookie(name, value, days = 365) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function systemPrefersDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function getThemePref() {
    return readCookie(PREF_COOKIE) || "auto";
}

/**
 * Applies `mode` ("light" | "dark" | "auto"), reloading only if the
 * resulting light/dark bundle actually needs to change - switching
 * from "auto" to "light" when the system is already light, for
 * instance, shouldn't force a pointless reload.
 */
export function setThemePref(mode) {
    writeCookie(PREF_COOKIE, mode);
    const wantDark = mode === "auto" ? systemPrefersDark() : mode === "dark";
    const currentlyDark = readCookie(SCHEME_COOKIE) === "dark";
    if (wantDark === currentlyDark) {
        return;
    }
    writeCookie(SCHEME_COOKIE, wantDark ? "dark" : "light");
    window.location.reload();
}

/**
 * Call once per page load, but only after the page has actually
 * settled (e.g. deferred via setTimeout from a component's onMounted,
 * never at module top-level) - it can call window.location.reload(),
 * and doing that mid-mount takes the whole app down with it, not just
 * whatever called this. Confirmed the hard way, in a real browser.
 *
 * If the user's preference is "auto" and the OS preference has
 * drifted from what the last-rendered page assumed (e.g. first visit
 * ever, or the OS theme changed since the cookie was last set),
 * reconciles the cookie and reloads once. Also wires a live listener
 * so an OS theme change while "auto" is active takes effect without
 * the user having to do anything.
 */
export function reconcileAutoTheme() {
    if (getThemePref() !== "auto") {
        return;
    }
    const wantDark = systemPrefersDark();
    const currentlyDark = readCookie(SCHEME_COOKIE) === "dark";
    if (wantDark !== currentlyDark) {
        writeCookie(SCHEME_COOKIE, wantDark ? "dark" : "light");
        window.location.reload();
        return;
    }
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
            if (getThemePref() === "auto") {
                setThemePref("auto");
            }
        });
    }
}

export function isDarkActive() {
    return readCookie(SCHEME_COOKIE) === "dark";
}

/**
 * Odoo's own `color_scheme` cookie correctly picks the light/dark
 * asset bundle server-side (confirmed by reading
 * web/views/webclient_templates.xml), but loading the dark bundle
 * alone doesn't actually repaint the page - confirmed the hard way,
 * in a real browser: with the dark bundle genuinely loaded and the
 * cookie genuinely set, the body background stayed light
 * (rgb(248,249,250), not the dark value Odoo's own SCSS defines).
 * Root cause: Bootstrap 5.3's dark variables only activate under a
 * `[data-bs-theme="dark"]` selector, and nothing in Odoo 18
 * Community's own bundle sets that attribute. This does - safe to
 * call at module top-level (unlike reconcileAutoTheme/setThemePref,
 * it only ever sets a DOM attribute, never reloads).
 */
export function applyBsTheme() {
    const el = document.documentElement;
    if (isDarkActive()) {
        el.setAttribute("data-bs-theme", "dark");
    } else {
        el.removeAttribute("data-bs-theme");
    }
}

applyBsTheme();
