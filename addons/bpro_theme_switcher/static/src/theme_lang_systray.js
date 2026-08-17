/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { getThemePref, setThemePref, reconcileAutoTheme } from "./theme_utils";

const THEME_OPTIONS = [
    { value: "light", label: _t("Day"), icon: "fa-sun-o" },
    { value: "dark", label: _t("Night"), icon: "fa-moon-o" },
    { value: "auto", label: _t("Auto"), icon: "fa-adjust" },
];

export class ThemeLangSystray extends Component {
    static template = "bpro_theme_switcher.ThemeLangSystray";
    static components = { Dropdown, DropdownItem };
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            themePref: getThemePref(),
            languages: [],
            currentLang: user.context.lang,
        });
        onWillStart(async () => {
            this.state.languages = await this.orm.searchRead(
                "res.lang",
                [["active", "=", true]],
                ["code", "name"]
            );
        });
        // Deferred with setTimeout, and only after this component (a
        // systray item, mounted as part of the webclient's own tree)
        // has actually mounted - calling this at module top-level
        // instead broke the webclient outright: a reload triggered
        // mid-mount, before Owl's App.mount() had even resolved,
        // threw "Cannot mount component: the target is not a valid
        // DOM element" and took the whole app down with it, not just
        // this component. Confirmed by reproducing it in a real
        // browser before shipping this fix.
        onMounted(() => setTimeout(() => reconcileAutoTheme(), 0));
    }

    get themeOptions() {
        return THEME_OPTIONS;
    }

    onSelectTheme(value) {
        this.state.themePref = value;
        setThemePref(value);
    }

    async onSelectLang(code) {
        if (code === this.state.currentLang) {
            return;
        }
        await this.orm.write("res.users", [user.userId], { lang: code });
        window.location.reload();
    }
}

export const themeLangSystrayItem = {
    Component: ThemeLangSystray,
};

registry.category("systray").add("bpro.theme_lang_systray", themeLangSystrayItem, { sequence: 1 });
