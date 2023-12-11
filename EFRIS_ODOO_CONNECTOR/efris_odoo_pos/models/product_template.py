# -*- coding: utf-8 -*-
import base64
import datetime
import hashlib
import json
import random

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.json import JSON

EXCISE_UNIT = {
    '101': 'per stick',
    '102': 'per litre',
    '103': 'per kg',
    '104': 'per user per day of access',
    '105': 'per minute',
    '106': 'per 1,000sticks',
    '107': 'per 50kgs',
    '108': '-',
    '109': 'per 1 g',
}
EXCISE_UNIT_SEL = [(key, value) for key, value in EXCISE_UNIT.items()]


class ProductTemplate(models.Model):
    """Inherited the product template model"""
    _inherit = 'product.template'

    has_efris_sync = fields.Boolean(string='Sync with Efris')
    efris_goods_category_id = fields.Many2one('efris.commodity.categories',
                                              string='Commodity Category Id',
                                              required=True)
    efris_item_name = fields.Char(string='Item Name',
                                  compute="_compute_efris_item_name")
    efris_item_code = fields.Char(string='Item Code',
                                  compute="_compute_efris_item_code")
    efris_goods_uom = fields.Many2one('efris.product.uom',
                                      string="EFRIS Measure Unit")
    efris_unit_price = fields.Float(string='EFRIS Unit Price', required=True,
                                    compute = '_compute_efris_unit_price',
                                    readonly=True)
    # review these below
    has_excise_duty = fields.Boolean(string='Has Excise Duty')
    excise_duty = fields.Char(string='Excise Duty Id')
    excise_duty_category = fields.Char(string='Excise Duty Category')
    excise_rule = fields.Selection(string='Excise Rule',
                                   selection=[('1', 'Calculated by Tax Rate'),
                                              ('2', 'Calculated By Quantity')])
    excise_duty_rate = fields.Float(string='Excise Duty Rate (%)')
    excise_unit = fields.Selection(string='Excise Unit',
                                   selection=EXCISE_UNIT_SEL)
    excise_currency_id = fields.Many2one(comodel_name='res.currency',
                                         string='Excise Duty Currency')
    # below required if excise rule =2
    excise_pack = fields.Float(string='Excise Pack')
    excise_stick = fields.Float(string='Excise Stick')
    is_efris_synchronised = fields.Boolean(string="EFRIS Synchronised",
                                           readonly=True)

    @api.depends('efris_goods_category_id')
    def _compute_efris_unit_price(self):
        """Method to compute the EFRIS UNIT Price of the product"""
        for rec in self:
            rec.efris_unit_price = False
            if rec.list_price and rec.efris_goods_category_id:
                unit_price = rec.list_price * 0.18 + rec.list_price
                rec.efris_unit_price = unit_price
            else:
                rec.efris_unit_price = False

    def update_efris_onhand(self):
        """Method to update the Onhand of the product"""
        return {
            'name': _('Update Quantity on EFRIS'),
            'res_model': 'efris.onhand.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'product.template',
                'active_ids': self.ids,
                'default_product_name': self.efris_item_name,
                'default_product_code': self.efris_item_code,
                'default_commodity_categ_id': self.efris_goods_category_id.id,
                'default_efris_goods_uom': self.efris_goods_uom.id,
                'default_unit_price': self.efris_unit_price,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _compute_efris_item_name(self):
        for rec in self:
            rec.efris_item_name = False
            if rec.name:
                rec.efris_item_name = rec.name

    def _compute_efris_item_code(self):
        for rec in self:
            create_date = rec.create_date
            formatted_date = create_date.strftime("%Y%m%d")
            rec.efris_item_code = 'PRD00' + str(rec.id) + str(formatted_date)

    def sync_with_efris(self):
        """Method to sync the product with EFRIS URA"""
        if not self.efris_item_code:
            raise ValidationError(
                'Please define an internal reference for the product to sync with EFRIS!')

        goods = [{
            "operationType": "101",
            "goodsName": self.efris_item_name,
            "goodsCode": self.efris_item_code,
            "measureUnit": self.efris_goods_uom.value,
            "unitPrice": self.list_price,
            "currency": "101",
            "commodityCategoryId": self.efris_goods_category_id.category_code,
            "haveExciseTax": "102",
            "description": "",
            "stockPrewarning": "10",
            "pieceMeasureUnit": "",
            "havePieceUnit": "102",
            "pieceUnitPrice": "",
            "packageScaledValue": "",
            "pieceScaledValue": "",
            "exciseDutyCode": "",
            "haveOtherUnit": "102",
            "goodsOtherUnits": []
        }, ]
        response = self.env.company.efris_access("T130", goods)

        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                base64_string = response_data.get('data').get('content')
                decoded_bytes = base64.b64decode(base64_string)
                decoded_string = decoded_bytes.decode('utf-8')
                json_object = json.loads(decoded_string)
                efris_taxid = self.env.ref('l10n_sa_tax_18.efris_tax_18_percent').with_user(1)
                efis_vat = self.env['account.tax'].search([('name', '=', efris_taxid.name)])
                self.is_efris_synchronised = True
                self.taxes_id = [Command.link(efis_vat.id)]
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'success',
                        'message': _(
                            'Successfully Uploaded the product to EFRIS URA.'),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification
            else:
                # self.is_efris_synchronised = True if returnCode == '602' else False
                    # self.write({'taxes_id': [(4, [1])]})
                raise UserError(_("Can't sync the product with EFRIS URA. "
                                  ' EFRIS error code: %s : %s \n',
                                  vals.get('returnCode'),
                                  vals.get('returnMessage')
                            ))
        else:
            raise UserError(
                _('Authentication Failed with EFRIS URA. Please verify the API URL.'))
