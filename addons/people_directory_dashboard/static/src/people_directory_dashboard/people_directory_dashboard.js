import { Component, onWillStart, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { KeepLast } from "@web/core/utils/concurrency";
import { useService } from "@web/core/utils/hooks";

const DEFAULT_FILTERS = {
    category: "all",
    demographic: "all",
    subtype: "all",
    state_id: "all",
    township_id: "all",
    status: "all",
    search: "",
};

const EMPTY_DATA = {
    domain: [],
    kpis: [],
    categories: [],
    employee_bars: [],
    region_rows: [],
    breakdowns: [],
    location_rows: [],
    recent_profiles: [],
    options: {
        categories: [],
        statuses: [],
        subtypes: {},
        states: [],
        townships: [],
    },
};

export class PeopleDirectoryDashboard extends Component {
    static template = "people_directory_dashboard.PeopleDirectoryDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.keepLast = new KeepLast();
        this.searchTimer = null;
        this.state = useState({
            loading: true,
            filters: { ...DEFAULT_FILTERS },
            data: { ...EMPTY_DATA },
            drawerOpen: false,
            drawerTitle: _t("Details"),
            drawerRows: [],
            drawerDomain: [],
            donutShowLabels: false,
            donutHoverKey: null,
        });

        onWillStart(() => this.loadDashboard());
    }

    get subtypeOptions() {
        const category = this.state.filters.category;
        const subtypes = this.state.data.options.subtypes[category] || [];
        return [{ value: "all", label: _t("All Types") }, ...subtypes];
    }

    get demographicOptions() {
        return [
            { value: "all", label: _t("All Demographics") },
            { value: "gender", label: _t("Gender") },
            { value: "age_group", label: _t("Age Group") },
            { value: "nationality", label: _t("Nationality") },
            { value: "blood_group", label: _t("Blood Group") },
        ];
    }

    get demographicRows() {
        return this.state.data.demographic_rows || [];
    }

    get donutStyle() {
        const slices = this.donutSlices;
        const total = slices.reduce((sum, slice) => sum + slice.count, 0);
        if (!total) {
            return "background:var(--pdd-chart-empty)";
        }
        const gradients = slices.map((slice) => `${slice.color} ${slice.start}% ${slice.end}%`);
        return `background:conic-gradient(${gradients.join(",")})`;
    }

    get donutSlices() {
        const categories = this.state.data.categories.filter((category) => category.count);
        const total = categories.reduce((sum, category) => sum + category.count, 0);
        if (!total) {
            return [];
        }
        let cursor = 0;
        return categories.map((category) => {
            const start = cursor;
            cursor += (category.count / total) * 100;
            return {
                ...category,
                start,
                end: cursor,
                mid: start + (cursor - start) / 2,
                label_text: `${category.label} ${this._slicePercent(category.count, total)}%`,
            };
        });
    }

    get donutHoverLabels() {
        if (!this.state.donutShowLabels) {
            return [];
        }
        if (!this.state.donutHoverKey) {
            return [];
        }
        const slices = this.donutSlices;
        if (!slices.length) {
            return [];
        }
        const hoveredSlice = slices.find((slice) => slice.key === this.state.donutHoverKey);
        if (!hoveredSlice) {
            return [];
        }

        const boxSize = 240;
        const center = boxSize / 2;
        const labelRadius = 108;
        const labelWidth = 138;
        const labelHeight = 24;
        const minLeft = 6;
        const maxLeft = boxSize - labelWidth - 6;
        const minTop = 6;
        const maxTop = boxSize - labelHeight - 6;

        const angle = ((hoveredSlice.mid / 100) * Math.PI * 2) - Math.PI / 2;
        const rightSide = Math.cos(angle) >= 0;
        const rawLeft = center + Math.cos(angle) * labelRadius + (rightSide ? 8 : -(labelWidth + 8));
        const rawTop = center + Math.sin(angle) * labelRadius - labelHeight / 2;
        const left = Math.max(minLeft, Math.min(maxLeft, rawLeft));
        const top = Math.max(minTop, Math.min(maxTop, rawTop));

        return [
            {
                key: hoveredSlice.key,
                color: hoveredSlice.color,
                text: hoveredSlice.label_text,
                active: true,
                sideClass: rightSide ? "o_pdd_donut_hint_right" : "o_pdd_donut_hint_left",
                style: `left:${left}px;top:${top}px;`,
            },
        ];
    }

    async loadDashboard() {
        this.state.loading = true;
        try {
            this.state.data = await this.keepLast.add(
                this.orm.call("res.profile", "get_people_directory_dashboard", [
                    { ...this.state.filters },
                ])
            );
        } finally {
            this.state.loading = false;
        }
    }

    async onFilterChange(fieldName, ev) {
        this.state.filters[fieldName] = ev.target.value;
        if (fieldName === "category") {
            this.state.filters.subtype = "all";
        }
        if (fieldName === "state_id") {
            this.state.filters.township_id = "all";
        }
        await this.loadDashboard();
    }

    onSearchInput(ev) {
        this.state.filters.search = ev.target.value;
        browser.clearTimeout(this.searchTimer);
        this.searchTimer = browser.setTimeout(() => this.loadDashboard(), 300);
    }

    refresh() {
        return this.loadDashboard();
    }

    openDrawer(title, rows, domain) {
        this.state.drawerTitle = title;
        this.state.drawerRows = rows || [];
        this.state.drawerDomain = domain || this.state.data.domain;
        this.state.drawerOpen = true;
    }

    closeDrawer() {
        this.state.drawerOpen = false;
    }

    onDonutEnter(ev) {
        this.state.donutShowLabels = true;
        this.onDonutMove(ev);
    }

    onDonutMove(ev) {
        const hovered = this._hoveredDonutSlice(ev);
        this.state.donutHoverKey = hovered ? hovered.key : null;
    }

    onDonutLeave() {
        this.state.donutShowLabels = false;
        this.state.donutHoverKey = null;
    }

    openProfiles(domain = this.state.data.domain, name = _t("Profiles")) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: "res.profile",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain,
        });
    }

    saveFilter() {
        this.openDrawer(_t("Saved Filter Preview"), this.state.data.categories, this.state.data.domain);
    }

    openProfile(profileId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: _t("Profile"),
            res_model: "res.profile",
            res_id: profileId,
            views: [[false, "form"]],
        });
    }

    formatNumber(value) {
        return new Intl.NumberFormat().format(value || 0);
    }

    barStyle(row) {
        const height = row.count ? Math.max(row.percent, 6) : 2;
        return `height:${height}%`;
    }

    fillStyle(row) {
        const width = row.count ? Math.max(row.percent, 3) : 0;
        return `width:${width}%;background:${row.color}`;
    }

    _hoveredDonutSlice(ev) {
        const slices = this.donutSlices;
        if (!slices.length) {
            return null;
        }

        const rect = ev.currentTarget.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const x = ev.clientX - centerX;
        const y = ev.clientY - centerY;
        const distance = Math.hypot(x, y);
        const donutInset = 25;
        const outerRadius = (Math.min(rect.width, rect.height) / 2) - donutInset;
        const innerRadius = outerRadius * 0.6;

        if (distance < innerRadius || distance > outerRadius) {
            return null;
        }

        const angleDeg = (Math.atan2(y, x) * 180) / Math.PI;
        const normalized = (angleDeg + 450) % 360;
        const percentage = (normalized / 360) * 100;
        return slices.find((slice) => percentage >= slice.start && percentage < slice.end) || null;
    }

    _slicePercent(value, total) {
        return total ? ((value / total) * 100).toFixed(1) : "0.0";
    }
}

registry.category("actions").add("people_directory_dashboard.dashboard", PeopleDirectoryDashboard);
