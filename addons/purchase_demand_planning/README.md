# Purchase Demand Planning

Technical documentation for the `purchase_demand_planning` Odoo module.
The module defines purchase demand request records and demand lines. It provides the base data model, views, menu entries, access rights, and demand reference sequence used before RFQ processing.

## 2. Dependencies

Declared in `__manifest__.py`:

```python
["demand_planning", "stock", "purchase"]
```

Dependency usage:

| Dependency | Used for |
| --- | --- |
| `demand_planning` | Root Demand Planning menu. |
| `stock` | Picking types, warehouse context, forecast report, stock quantities. |
| `purchase` | RFQ and RFQ line references. |

## 3. Module Structure

```text
purchase_demand_planning/
|-- __init__.py
|-- __manifest__.py
|-- data/
|   `-- sequence.xml
|-- models/
|   |-- __init__.py
|   |-- purchase_demand_plan.py
|   `-- purchase_demand_plan_line.py
|-- security/
|   `-- ir.model.access.csv
`-- views/
    |-- menus.xml
    `-- purchase_demand_plan_views.xml
```

## 4. Data Model

### 4.1 `purchase.demand.plan`

Defined in `models/purchase_demand_plan.py`.

```python
_name = "purchase.demand.plan"
_description = "Purchase Demand Plan"
_inherit = ["mail.thread", "mail.activity.mixin"]
_rec_name = "reference"
_order = "id desc"
```

| Field | Type | Required | Default / Behavior |
| --- | --- | --- | --- |
| `reference` | Char | Yes | Defaults to `New`; replaced by sequence on create. |
| `company_id` | Many2one `res.company` | Yes | Current company. |
| `requester_id` | Many2one `res.users` | No | Current user. |
| `request_date` | Date | No | Today. |
| `note` | Text | No | Manual notes. |
| `picking_type_id` | Many2one `stock.picking.type` | Yes | Default incoming picking type. |
| `state` | Selection | No | Defaults to `draft`. |
| `line_ids` | One2many `purchase.demand.plan.line` | No | Child demand lines. |


### 4.2 `purchase.demand.plan.line`

Defined in `models/purchase_demand_plan_line.py`.

```python
_name = "purchase.demand.plan.line"
_description = "Purchase Demand Plan Line"
```

| Field | Type | Required | Default / Behavior |
| --- | --- | --- | --- |
| `demand_id` | Many2one `purchase.demand.plan` | Yes | Parent demand; cascade delete. |
| `product_id` | Many2one `product.product` | Yes | Requested product. |
| `description` | Char | No | Manual description. |
| `uom_id` | Many2one `uom.uom` | No | Related to `product_id.uom_id`. |
| `qty_available` | Float | No | Related to `product_id.qty_available`. |
| `virtual_available` | Float | No | Related to `product_id.virtual_available`. |
| `free_qty` | Float | No | Related to `product_id.free_qty`. |
| `incoming_qty` | Float | No | Related to `product_id.incoming_qty`. |
| `outgoing_qty` | Float | No | Related to `product_id.outgoing_qty`. |
| `requested_qty` | Float | Yes | Defaults to `1.0`. |
| `approved_qty` | Float | No | Defaults to `0.0`. |
| `rejected_qty` | Float | No | Stored computed field. |
| `forecasted_issue` | Boolean | No | Computed stock warning flag. |
| `is_storable` | Boolean | No | Related to `product_id.is_storable`. |
| `preferred_vendor_id` | Many2one `res.partner` | No | Preferred vendor. |
| `required_date` | Date | No | Expected delivery date. |
| `remark` | Text | No | Manual remark. |
| `state` | Selection | No | Defaults to `pending`. |
| `rfq_ids` | Many2many `purchase.order` | No | Readonly RFQ links. |
| `rfq_line_ids` | Many2many `purchase.order.line` | No | Readonly RFQ line links. |

Line state values:

| Value | Label |
| --- | --- |
| `pending` | Pending |
| `approved` | Approved |
| `rfq_created` | RFQ Created |
| `rejected` | Rejected |

## 5. Technical Business Logic

This section documents implemented model logic only.

### 5.1 Demand Reference Generation

Method: `purchase.demand.plan.create`

Purpose:
- Assign a unique reference from sequence `purchase.demand.plan`.

Configured in `data/sequence.xml`:

```xml
<field name="code">purchase.demand.plan</field>
<field name="prefix">PDR/%(day)s/%(month)s/%(year)s/</field>
<field name="padding">5</field>
```

Execution:
1. On create, check whether the reference is still `New`.
2. Request the next sequence value.
3. Write the generated value into `reference`.
4. Continue with ORM create.

Technical note:
- The current method is declared with `@api.model`. If batch create support is required, refactor it to `@api.model_create_multi`.

### 5.2 Default Incoming Picking Type

Methods:
- `_default_picking_type`
- `_get_picking_type`

Purpose:
- Default `picking_type_id` with an incoming operation type for the current company.

Resolution order:
1. Incoming picking type linked to a warehouse of the company.
2. Generic incoming picking type with no warehouse.
3. Inactive generic incoming picking type with no warehouse.

### 5.3 Header Workflow Methods

Methods:
- `action_submitted`
- `action_bu_approved`

Implemented transitions:

```text
draft -> submitted
submitted -> bu_approved
```

Current implementation:
- `action_submitted` writes `state = "submitted"`.
- `action_bu_approved` writes `state = "bu_approved"`.

Technical note:
- These methods do not enforce group checks, source-state checks, line validation, or quantity validation.

### 5.4 Forecast Warning

Method: `_compute_forecasted_issue`

Trigger:
- Depends on `requested_qty`.

Logic:
1. Resolve warehouse from `line.demand_id.picking_type_id.warehouse_id`.
2. Read `line.product_id.virtual_available` with `warehouse_id` context.
3. Set `forecasted_issue = True` when virtual availability is below zero.
4. Otherwise set `forecasted_issue = False`.

Technical note:
- The compute only depends on `requested_qty`; changes to product, picking type, or stock quantities do not automatically trigger recompute unless Odoo recomputes the field for another reason.

### 5.5 Product Forecast Action

Method: `action_product_forecast_report`

Logic:
1. Ensure one demand line.
2. Call `product_id.action_product_forecast_report()`.
3. Inject `active_id`, `active_model`, and `warehouse_id` into the action context.
4. Return the action.

### 5.6 Rejected Quantity

Method: `_compute_rejected_qty`

Formula:

```python
rejected_qty = requested_qty - approved_qty if approved_qty > 0 else 0
```

Dependencies:
- `requested_qty`
- `approved_qty`

### 5.7 RFQ Traceability Fields

Fields:
- `rfq_ids`
- `rfq_line_ids`

The base module stores these readonly reference links but does not create RFQs itself. RFQ creation and line synchronization are expected to be handled by a downstream extension module.

## 6. Views and Actions

Defined in `views/purchase_demand_plan_views.xml`.

| XML ID | Type | Model | Purpose |
| --- | --- | --- | --- |
| `view_purchase_demand_plan_tree` | List | `purchase.demand.plan` | Demand request overview. |
| `view_purchase_demand_plan_form` | Form | `purchase.demand.plan` | Demand request entry and workflow. |
| `action_purchase_demand_plan` | Window action | `purchase.demand.plan` | Opens list/form views. |

Form components:
- Header buttons: `action_submitted`, `action_bu_approved`.
- Header statusbar: `state`.
- Main fields: requester, company, request date, picking type.
- Notebook page `Lines`: editable `line_ids`.
- Notebook page `Notes`: free text `note`.
- Chatter from `mail.thread` and `mail.activity.mixin`.

Embedded demand line UI:
- Shows product and quantity fields.
- Shows stock-related related fields.
- Displays forecast report buttons based on `forecasted_issue` and `is_storable`.
- Shows RFQ traceability fields as optional hidden fields.

## 7. Menus

Defined in `views/menus.xml`.

| XML ID | Name | Parent | Action |
| --- | --- | --- | --- |
| `menu_purchase_demand_plan` | Purchase Demand Requests | `demand_planning.demand_planning_root` | `action_purchase_demand_plan` |
| `purchase_rfq_category` | Requests for Quotation | `demand_planning.demand_planning_root` | `purchase.purchase_rfq` |
| `replenishment_category` | Replenishment | `demand_planning.demand_planning_root` | `stock.action_orderpoint_replenish` |

## 8. Security

Defined in `security/ir.model.access.csv`.

| Access ID | Model | Group | Read | Write | Create | Delete |
| --- | --- | --- | --- | --- | --- | --- |
| `access_purchase_demand_plan_user` | `purchase.demand.plan` | `base.group_user` | 1 | 1 | 1 | 1 |
| `access_purchase_demand_plan_manager` | `purchase.demand.plan` | `base.group_user` | 1 | 1 | 1 | 1 |
| `access_purchase_demand_plan_line_user` | `purchase.demand.plan.line` | `base.group_user` | 1 | 1 | 1 | 1 |
| `access_purchase_demand_plan_line_manager` | `purchase.demand.plan.line` | `base.group_user` | 1 | 1 | 1 | 1 |

Technical notes:
- No custom groups are defined.
- No record rules are defined.
- The `user` and `manager` access rows currently use the same group and permissions.

## 9. Data Files

| File | Loaded by manifest | Content |
| --- | --- | --- |
| `data/sequence.xml` | Yes | Sequence `purchase.demand.plan`. |
| `security/ir.model.access.csv` | Yes | Access rights for demand models. |
| `views/purchase_demand_plan_views.xml` | Yes | Views and window action. |
| `views/menus.xml` | Yes | Menu entries. |

## 10. Scheduled Actions

No scheduled actions are defined by this module.

## 11. External Integrations

No external APIs or third-party services are used.

Internal Odoo integrations:
- Product forecast report via `product.product.action_product_forecast_report()`.
- Purchase RFQ references through `purchase.order` and `purchase.order.line`.
- Stock picking type and warehouse context from `stock`.

## 12. Installation and Upgrade

Installation:
1. Install required dependencies.
2. Update the Odoo apps list.
3. Install `purchase_demand_planning`.
4. Confirm sequence `purchase.demand.plan` exists.
5. Confirm menu `Demand Planning > Purchase Demand Requests` is visible.

Upgrade checks:
- Run module upgrade after model, view, security, or sequence changes.
- Verify access rights after security changes.
- Verify embedded One2many line editing after view changes.
- Verify forecast action after stock or product model changes.

## 13. Technical Test Checklist

| Scenario | Expected result |
| --- | --- |
| Install module | Models, views, sequence, access rights, and menus load without error. |
| Create demand plan | Reference is generated from sequence. |
| Create demand line | Product is required; requested quantity defaults to `1.0`. |
| Submit demand | Header state becomes `submitted`. |
| BU approve demand | Header state becomes `bu_approved`. |
| Compute rejected quantity | `rejected_qty` updates from requested and approved quantities. |
| Forecast issue check | Negative warehouse forecast sets `forecasted_issue`. |
| Forecast report button | Opens standard product forecast report with warehouse context. |
| RFQ traceability write | `rfq_ids` and `rfq_line_ids` can store multiple linked purchase records. |

## 14. Known Technical Gaps

- No custom security groups separate requester, approver, and purchaser responsibilities.
- No record rules restrict records by requester, company, or role.
- Header workflow methods do not validate source state.
- Approval quantity is not required before approval.
- `forecasted_issue` dependencies are narrow and may not recompute for every stock-relevant change.
- RFQ creation is outside this base module.

## 15. Change Log

| Version | Description |
| --- | --- |
| Initial | Added purchase demand header and line models. |
| Initial | Added demand reference sequence. |
| Initial | Added list/form views and demand planning menus. |
| Initial | Added stock visibility fields and forecast report action on demand lines. |
