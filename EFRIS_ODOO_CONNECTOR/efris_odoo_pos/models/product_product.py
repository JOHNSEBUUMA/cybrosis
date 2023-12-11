# -*- coding: utf-8 -*-
import base64
import json

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.product'

    @api.depends('efris_goods_category_id')
    def _compute_efris_unit_price(self):
        """Method to compute the unit price of the product after
         sync product with EFRIS"""
        for rec in self:
            rec.efris_unit_price = False
            if rec.list_price and rec.efris_goods_category_id:
                unit_price = rec.list_price * 0.18 + rec.list_price
                rec.efris_unit_price = unit_price
            else:
                rec.efris_unit_price = False

    def update_efris_onhand(self):
        """Method to update the on-hand of the product in EFRIS"""
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
        """Method to compute the EFRIS product name"""
        for rec in self:
            rec.efris_item_name = False
            if rec.name:
                rec.efris_item_name = rec.name

    def _compute_efris_item_code(self):
        """Method to compute EFRIS the product code"""
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
                efris_taxid = self.env.ref(
                    'l10n_sa_tax_18.efris_tax_18_percent').with_user(1)
                efis_vat = self.env['account.tax'].search(
                    [('name', '=', efris_taxid.name)])
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
