# Copyright 2022 - Dario Cruz https://xtendoo.es/
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Proveedor",
    )
    license = fields.Char(
        string="Matrícula",
        required=False,
        allow_none=False,
    )
    ip_number = fields.Char(
        string="Nº IP",
        required=False,
        allow_none=False,
    )
    upload_date = fields.Date(
        string="Fecha de carga",
        required=False,
        allow_none=False,
    )
    download_date = fields.Date(
        string="Fecha de descarga",
        required=False,
        allow_none=False,
    )
    is_purchase_order_created = fields.Boolean(
        compute= "_compute_purchase_order_created",
        store=True,
    )

    @api.depends("state")
    def _compute_purchase_order_created(self):
        self.is_purchase_order_created = False
        for order in self:
            if self.env["purchase.order"].search([("origin", "=", order.name,)]):
                order.is_purchase_order_created = True

    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for order in self.filtered(lambda order: order.supplier_id):
            if not order.is_purchase_order_created:
                order._create_purchase_order(order)
        return result

    def _create_purchase_order(self, order):
        values = order._purchase_prepare_order_values(order)
        purchase_order = self.env["purchase.order"].create(values)
        purchase_order.button_confirm()

        for line in order.order_line:
            line_values = order._purchase_prepare_line_order_values(purchase_order, line)
            purchase_order.env["purchase.order.line"].create(line_values)
        return purchase_order

    def _purchase_prepare_order_values(self, order):
        self.ensure_one()
        date_order = datetime.datetime.now()
        return {
            "partner_id": order.supplier_id.id,
            "company_id": self.company_id.id,
            # "currency_id": order.supplier_id.property_purchase_currency_id.id
            "origin": order.name,
            "payment_term_id": order.payment_term_id.id,
            "date_order": date_order,
            "license" : order.license,
            "ip_number": order.ip_number,
            "upload_date": order.upload_date,
            "download_date": order.download_date
        }

    def _purchase_prepare_line_order_values(self, purchase_order, line):
        self.ensure_one()
        # compute quantity from SO line UoM
        product_quantity = line.product_uom_qty
        purchase_qty_uom = line.product_uom._compute_quantity(
            product_quantity, line.product_id.uom_po_id
        )
        price_unit = 0.0
        date_planned = datetime.datetime.now()
        return {
            "name": "[%s] %s" % (line.product_id.default_code, line.name)
            if line.product_id.default_code
            else line.name,
            "product_qty": purchase_qty_uom,
            "product_id": line.product_id.id,
            "product_uom": line.product_id.uom_po_id.id,
            "price_unit": price_unit,
            "date_planned": date_planned,
            "taxes_id": None,
            "order_id": purchase_order.id,
            "sale_line_id": line.id,
        }
