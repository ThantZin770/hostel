import { Component, onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useBus, useOwnedDialogs, useService } from "@web/core/utils/hooks";
import { SearchPanel } from "@web/search/search_panel/search_panel";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";

const CENTRAL_DEMAND_PLANNING_VIEW = "central_demand_planning";
const PRODUCT_FIELD_NAME = "product_id";
const PRODUCT_RESULT_LIMIT = 9;
const PRODUCT_VISIBLE_OPTIONS = 8;

let nextProductFilterId = 1;

function getEmptyDashboardValues() {
    return {
        pending: 0,
        approved: 0,
        late: 0,
        rfq_created: 0,
        rejected: 0,
        requested_qty: 0,
        approved_qty: 0,
    };
}

function getEmptyDashboardData() {
    return {
        global: getEmptyDashboardValues(),
        my: getEmptyDashboardValues(),
    };
}

class CentralDemandPlanningDashboardData {
    constructor(orm, getDomain) {
        this.orm = orm;
        this.getDomain = getDomain;
    }

    load() {
        return this.orm.call(
            "purchase.demand.plan.line",
            "retrieve_central_demand_planning_dashboard",
            [this.getDomain()]
        );
    }

    hasPersonalScope(data) {
        return JSON.stringify(data.global) !== JSON.stringify(data.my);
    }
}

class CentralDemandPlanningProductFilter {
    constructor({ addDialog, orm, searchModel, state }) {
        this.addDialog = addDialog;
        this.orm = orm;
        this.searchModel = searchModel;
        this.state = state;
    }

    get activeIds() {
        return this.activeQuery.map((queryElem) => queryElem.autocompleteValue.value);
    }

    get activeQuery() {
        const searchItem = this.searchItem;
        if (!searchItem) {
            return [];
        }
        return this.searchModel.query
            .filter(
                (queryElem) =>
                    queryElem.searchItemId === searchItem.id &&
                    queryElem.autocompleteValue?.operator === "="
            )
            .filter((queryElem) => queryElem.autocompleteValue);
    }

    get autocompleteProps() {
        return {
            autoSelect: true,
            class: "mt-1",
            inputDebounceDelay: 250,
            placeholder: _t("+ Add Products"),
            resetOnSelect: true,
            searchOnInputClick: false,
            sources: [
                {
                    placeholder: _t("Loading..."),
                    options: (request) => this.loadSource(request),
                    optionSlot: "option",
                },
            ],
            value: "",
        };
    }

    get hasSearchItem() {
        return Boolean(this.searchItem);
    }

    get isAllActive() {
        return this.state.filters.length && this.state.filters.every((filter) => filter.active);
    }

    get resModel() {
        return this.searchModel.searchViewFields[PRODUCT_FIELD_NAME]?.relation || "product.product";
    }

    get searchItem() {
        return this.searchModel.getSearchItems(
            (item) => item.type === "field" && item.fieldName === PRODUCT_FIELD_NAME
        )[0];
    }

    get sortedFilters() {
        return [...this.state.filters].sort((a, b) =>
            a.label.localeCompare(b.label, undefined, {
                ignorePunctuation: true,
                numeric: true,
                sensitivity: "base",
            })
        );
    }

    async loadSource(request) {
        const records = await this.orm.call(this.resModel, "name_search", [], {
            context: this.searchModel.globalContext,
            domain: [["id", "not in", this.state.filters.map((filter) => filter.value)]],
            limit: PRODUCT_RESULT_LIMIT,
            name: request.trim(),
            operator: "ilike",
        });

        const options = records.slice(0, PRODUCT_VISIBLE_OPTIONS).map(([id, label]) => ({
            data: { id },
            label,
            onSelect: () => this.select(id, label),
        }));
        if (records.length > PRODUCT_VISIBLE_OPTIONS) {
            options.push({
                label: _t("Search More..."),
                onSelect: () => this.openSearchMore(request.trim()),
            });
        }
        if (!records.length) {
            options.push({
                cssClass: "o_m2o_no_result",
                label: _t("No records"),
            });
        }
        return options;
    }

    async openSearchMore(request) {
        const domain = [["id", "not in", this.state.filters.map((filter) => filter.value)]];
        const dynamicFilters = [];
        if (request.length) {
            const nameGets = await this.orm.call(this.resModel, "name_search", [], {
                context: this.searchModel.globalContext,
                domain,
                name: request,
                operator: "ilike",
            });
            dynamicFilters.push({
                description: _t("Quick search: %s", request),
                domain: [["id", "in", nameGets.map((nameGet) => nameGet[0])]],
            });
        }
        this.addDialog(SelectCreateDialog, {
            context: this.searchModel.globalContext,
            domain,
            dynamicFilters,
            multiSelect: true,
            noCreate: true,
            onSelected: (resIds) => this.selectMany(resIds),
            resModel: this.resModel,
            title: _t("Search: Products"),
        });
    }

    remove(filter) {
        this.state.filters = this.state.filters.filter((item) => item.value !== filter.value);
        this.removeFromDomain(filter.value);
    }

    removeFromDomain(productId, notify = true) {
        const searchItem = this.searchItem;
        if (!searchItem) {
            return;
        }
        this.searchModel.query = this.searchModel.query.filter(
            (queryElem) =>
                queryElem.searchItemId !== searchItem.id ||
                queryElem.autocompleteValue?.value !== productId
        );
        if (notify) {
            this.notify();
        }
    }

    select(id, label) {
        const searchItem = this.searchItem;
        if (!searchItem) {
            return;
        }
        this.upsertFilter(id, label);
        this.searchModel.addAutoCompletionValues(searchItem.id, {
            label,
            operator: "=",
            value: id,
        });
        this.sync();
    }

    async selectMany(resIds) {
        const products = await this.orm.call(
            this.resModel,
            "read",
            [resIds, ["display_name"]],
            { context: this.searchModel.globalContext }
        );
        for (const product of products) {
            this.select(product.id, product.display_name);
        }
    }

    sync() {
        const activeIds = new Set(this.activeIds);
        for (const queryElem of this.activeQuery) {
            const { label, value } = queryElem.autocompleteValue;
            this.upsertFilter(value, label);
        }
        for (const filter of this.state.filters) {
            filter.active = activeIds.has(filter.value);
        }
    }

    toggleAll(checked) {
        if (checked) {
            for (const filter of this.state.filters) {
                this.select(filter.value, filter.label);
            }
            return;
        }
        for (const filter of this.state.filters) {
            this.removeFromDomain(filter.value, false);
            filter.active = false;
        }
        this.notify();
    }

    toggleFilter(filter, checked) {
        if (checked) {
            this.select(filter.value, filter.label);
        } else {
            this.removeFromDomain(filter.value);
            filter.active = false;
        }
    }

    upsertFilter(id, label) {
        const filter = this.state.filters.find((item) => item.value === id);
        if (filter) {
            filter.active = true;
            filter.label = label;
            return filter;
        }
        this.state.filters.push({
            active: true,
            label,
            value: id,
        });
    }

    notify() {
        // Odoo exposes addAutoCompletionValues, but not removal of one autocomplete value.
        if (this.searchModel._notify) {
            this.searchModel._notify();
        } else {
            this.searchModel.search();
        }
    }
}

export class CentralDemandPlanningDashboard extends Component {
    static template = "purchase_demand_planning_central.CentralDemandPlanningDashboard";
    static props = { list: { type: Object, optional: true } };

    setup() {
        const orm = useService("orm");
        this.dashboardService = new CentralDemandPlanningDashboardData(orm, () =>
            this.getDashboardDomain()
        );
        this.state = useState({
            data: getEmptyDashboardData(),
            multiuser: false,
        });
        this.dashboardRequestId = 0;

        onWillStart(() => this.updateDashboardState());
        onWillUpdateProps(() => this.updateDashboardState());
        if (this.env.searchModel) {
            useBus(this.env.searchModel, "update", () => this.updateDashboardState());
        }
    }

    get dashboard() {
        return this.state.data;
    }

    get multiuser() {
        return this.state.multiuser;
    }

    getDashboardDomain() {
        return this.env.searchModel?.domain || this.props.list?.domain || [];
    }

    async updateDashboardState() {
        const requestId = ++this.dashboardRequestId;
        const data = await this.dashboardService.load();
        if (requestId !== this.dashboardRequestId) {
            return;
        }
        this.state.data = data;
        this.state.multiuser = this.dashboardService.hasPersonalScope(data);
    }

    setSearchContext(ev) {
        const filters = ev.currentTarget.getAttribute("filter_name").split(",");
        const searchItems = this.env.searchModel.getSearchItems((item) =>
            filters.includes(item.name)
        );
        this.env.searchModel.query = [];
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }

    formatQty(value) {
        return new Intl.NumberFormat(undefined, {
            maximumFractionDigits: 2,
        }).format(value || 0);
    }
}

export class CentralDemandPlanningListController extends ListController {
    static template = "purchase_demand_planning_central.CentralDemandPlanningListView";
    static components = {
        ...ListController.components,
        CentralDemandPlanningDashboard,
    };
}

export class CentralDemandPlanningSearchPanel extends SearchPanel {
    static template = "purchase_demand_planning_central.CentralDemandPlanningSearchPanel";
    static components = {
        ...SearchPanel.components,
        AutoComplete,
    };

    setup() {
        super.setup();
        const productState = useState({
            collapsed: false,
            filters: [],
        });
        this.productState = productState;
        this.productFilter = new CentralDemandPlanningProductFilter({
            addDialog: useOwnedDialogs(),
            orm: useService("orm"),
            searchModel: this.env.searchModel,
            state: productState,
        });
        useBus(this.env.searchModel, "update", () => this.productFilter.sync());
    }

    get hasProductSearchItem() {
        return this.productFilter.hasSearchItem;
    }

    get isAllProductsActive() {
        return this.productFilter.isAllActive;
    }

    get nextProductFilterId() {
        nextProductFilterId += 1;
        return nextProductFilterId;
    }

    get productAutoCompleteProps() {
        return this.productFilter.autocompleteProps;
    }

    get productFilters() {
        return this.productFilter.sortedFilters;
    }

    onAllProductInputChange(ev) {
        this.productFilter.toggleAll(ev.target.checked);
    }

    onProductFilterInputChange(filter, ev) {
        this.productFilter.toggleFilter(filter, ev.target.checked);
    }

    onProductFilterRemove(filter) {
        this.productFilter.remove(filter);
    }

    toggleProductSection() {
        this.productState.collapsed = !this.productState.collapsed;
    }
}

export const centralDemandPlanningView = {
    ...listView,
    Controller: CentralDemandPlanningListController,
    SearchPanel: CentralDemandPlanningSearchPanel,
};

registry.category("views").add(CENTRAL_DEMAND_PLANNING_VIEW, centralDemandPlanningView);
