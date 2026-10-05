from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    dispatch_note_ids = fields.One2many(
        "dispatch.note",
        "purchase_order_id",
        domain=[("type", "=", "purchase")],
    )
    dispatch_note_count = fields.Integer(compute="_compute_dispatch_note_count")

    def action_view_dispatch_note_ids(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase_dispatch_note.action_purchase_dispatch_note"
        )
        action["domain"] = [
            ("type", "=", "purchase"),
            ("id", "in", self.dispatch_note_ids.ids),
        ]
        action["context"] = {
            "default_type": "purchase",
            "default_purchase_order_id": self.id,
        }
        return action

    @api.depends("dispatch_note_ids")
    def _compute_dispatch_note_count(self):
        for order in self:
            order.dispatch_note_count = len(order.dispatch_note_ids)

    def action_dispatch_note(self):
        view = self.env.ref("purchase_dispatch_note.purchase_dispatch_note_view_form")
        return {
            "name": f"{self.name}'s Dispatch Note",
            "type": "ir.actions.act_window",
            "res_model": "dispatch.note",
            "view_mode": "form",
            "views": [(view.id, "form")],
            "target": "new",
            "context": {
                "default_type": "purchase",
                "default_note_type": "plan" if self.state != "purchase" else "late",
                "default_purchase_order_id": self.id,
            },
        }

    def _get_dispatch_notes_for_picking(self):
        self.ensure_one()
        return self.dispatch_note_ids.filtered(
            lambda note: (
                note.type == "purchase"
                and note.state == "confirm"
                and any(
                    line.product_id
                    and line.product_id.type == "consu"
                    and line.quantity > 0
                    for line in note.line_ids
                )
            )
        )

    def _update_dispatch_note_stock_move_vals(self, vals, note):
        if note.delivery_date:
            delivery_date = fields.Datetime.to_datetime(note.delivery_date)
            vals["date"] = delivery_date
            vals["date_deadline"] = delivery_date
        return vals

    def _prepare_dispatch_note_stock_move_vals(
        self, purchase_line, picking, quantity, uom, note
    ):
        if uom.compare(quantity, 0.0) <= 0:
            return []
        vals = purchase_line._prepare_stock_move_vals(
            picking,
            purchase_line._get_stock_move_price_unit(),
            quantity,
            uom,
        )
        return [self._update_dispatch_note_stock_move_vals(vals, note)]

    def _create_dispatch_note_stock_moves(self, note, picking):
        self.ensure_one()
        StockMove = self.env["stock.move"]
        moves = StockMove
        for note_line in note.line_ids.filtered(lambda line: line.product_id):
            if note_line.product_id.type != "consu":
                continue
            source_uom = note_line.uom_id or note_line.product_id.uom_id
            remaining_note_qty = note_line.quantity
            if source_uom.compare(remaining_note_qty, 0.0) <= 0:
                continue

            purchase_lines = self.order_line.filtered(
                lambda line: (
                    not line.display_type and line.product_id == note_line.product_id
                )
            )
            for purchase_line in sorted(
                purchase_lines, key=lambda line: (line.sequence, line.id)
            ):
                requested_line_uom_qty = source_uom._compute_quantity(
                    remaining_note_qty,
                    purchase_line.product_uom_id,
                    rounding_method="HALF-UP",
                )
                available_qty = (
                    purchase_line.product_qty - purchase_line._get_qty_procurement()
                )
                if purchase_line.product_uom_id.compare(available_qty, 0.0) <= 0:
                    continue
                qty_to_create_line_uom = min(requested_line_uom_qty, available_qty)
                if (
                    purchase_line.product_uom_id.compare(qty_to_create_line_uom, 0.0)
                    <= 0
                ):
                    continue
                qty_to_create = purchase_line.product_uom_id._compute_quantity(
                    qty_to_create_line_uom,
                    source_uom,
                    rounding_method="HALF-UP",
                )

                vals_list = self._prepare_dispatch_note_stock_move_vals(
                    purchase_line, picking, qty_to_create, source_uom, note
                )
                if not vals_list:
                    continue

                created_qty = 0.0
                for vals in vals_list:
                    move_uom = self.env["uom.uom"].browse(vals["product_uom"])
                    created_qty += move_uom._compute_quantity(
                        vals["product_uom_qty"],
                        source_uom,
                        rounding_method="HALF-UP",
                    )
                moves |= StockMove.create(vals_list)
                remaining_note_qty -= created_qty
                if source_uom.compare(remaining_note_qty, 0.0) <= 0:
                    break

        return moves

    def _confirm_dispatch_note_picking(self, order, picking, moves):
        moves = moves.filtered(lambda move: move.state not in ("done", "cancel"))
        moves = moves._action_confirm()
        seq = 0
        for move in sorted(moves, key=lambda move: move.date):
            seq += 5
            move.sequence = seq
        moves._action_assign()
        forward_pickings = self.env["stock.picking"]._get_impacted_pickings(moves)
        (picking | forward_pickings).action_confirm()
        picking.message_post_with_source(
            "mail.message_origin_link",
            render_values={"self": picking, "origin": order},
            subtype_xmlid="mail.mt_note",
        )

    def _create_dispatch_note_receipt(self, note):
        self.ensure_one()
        note.ensure_one()
        if (
            note.type != "purchase"
            or note.state != "confirm"
            or note.purchase_order_id.id != self.id
            or self.state != "purchase"
        ):
            return self.env["stock.picking"]

        existing_pickings = note.picking_ids.filtered(
            lambda picking: picking.state != "cancel"
        )
        if existing_pickings:
            return existing_pickings

        order = self.with_company(self.company_id)
        picking_vals = order._prepare_picking()
        picking_vals["dispatch_note_id"] = note.id
        picking = (
            order.env["stock.picking"].with_user(SUPERUSER_ID).create(picking_vals)
        )

        moves = order._create_dispatch_note_stock_moves(note, picking)
        if not moves:
            picking.unlink()
            return self.env["stock.picking"]

        order._confirm_dispatch_note_picking(order, picking, moves)
        return picking

    def _create_picking(self):
        orders_without_dispatch_notes = self.filtered(
            lambda order: not order.dispatch_note_ids
        )
        if orders_without_dispatch_notes:
            super(PurchaseOrder, orders_without_dispatch_notes)._create_picking()

        for order in (self - orders_without_dispatch_notes).filtered(
            lambda po: po.state == "purchase"
        ):
            if any(product.type == "consu" for product in order.order_line.product_id):
                for note in order._get_dispatch_notes_for_picking():
                    order._create_dispatch_note_receipt(note)
        return True

    state = fields.Selection(selection_add=[("confirm", "Confirmed"), ("purchase",)])

    def action_virtual_confirm(self):
        for order in self:
            order.state = "confirm"

    def button_confirm(self):
        for order in self:
            if order.state not in ["draft", "sent", "confirm"]:
                continue
            error_msg = order._confirmation_error_message()
            if error_msg:
                raise UserError(error_msg)
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({"state": "to approve"})
        return True
