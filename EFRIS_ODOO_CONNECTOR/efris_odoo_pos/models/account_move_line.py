# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    efris_unit_price = fields.Float(string="EFRIS Unit Price", compute="_compute_efris_unit_price")
    is_efris_product = fields.Boolean('IS EFRIS product',readonly=True)

    def _compute_efris_unit_price(self):
        for rec in self:
            rec.efris_unit_price = False
            if rec.product_id.efris_unit_price:
                rec.write({'is_efris_product': True})
                rec.efris_unit_price = rec.product_id.efris_unit_price
