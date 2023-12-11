# -*- coding: utf-8 -*-

import base64

from odoo import models, fields, api, _
import json

from odoo.exceptions import UserError


class YourWizardModel(models.TransientModel):
    _name = 'efris.onhand.wizard'
    _description = 'EFRIS onhand Update'

    product_name = fields.Char(string='Product Name', readonly=True)
    product_code = fields.Char(string='Product Code', readonly=True)
    efris_goods_uom = fields.Many2one('efris.product.uom',
                                      string="EFRIS Measure Unit")
    commodity_categ_id = fields.Many2one('efris.commodity.categories',
                                         string='Commodity Category',
                                         readonly=True)
    update_type = fields.Selection(string="Update Type",
                                   selection=[('increase', 'Increase'),
                                              ('decrease', 'Reduce')],
                                   default='increase', required=True)
    product_onhand = fields.Integer(string='Onhand Quantity')
    reduce_reason = fields.Selection(string="Onhand Reduce Reason",
                                     selection=[('101', 'Expired Goods'),
                                                ('102', 'Damaged Goods'),
                                                ('103', 'Personal Uses'),
                                                ('104', 'Others'),
                                                ])
    remarks = fields.Text(string="Remarks")
    unit_price = fields.Float(string='Unit Price', readonly=True)

    def goods_quantity_update(self):
        stock_maintain = {
            "goodsStockIn": {
                "operationType": "101",
                "supplierTin": "",
                "supplierName": "Mr. EMUR SAM",
                "adjustType": "",
                "remarks": "",
                "stockInDate": "",
                "stockInType": "101",
                "productionBatchNo": "",
                "productionDate": "",
                "branchId": "",
                "invoiceNo": "",
                "isCheckBatchNo": "0"
            },
            "goodsStockInItem": [{
                "commodityGoodsId": "",
                "goodsCode": self.product_code,
                "measureUnit": self.efris_goods_uom.value,
                "quantity": self.product_onhand,
                "unitPrice": self.unit_price,
            }]
        }
        response = self.env.company.efris_access("T131", stock_maintain)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'success',
                        'message': _(
                            'Successfully Updated the Product'
                            ' Onhand Quantity in EFRIS.'),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification

            else:
                base64_string = response_data.get('data').get('content')
                decoded_bytes = base64.b64decode(base64_string)
                decoded_string = decoded_bytes.decode('utf-8')
                json_object = json.loads(decoded_string)
                returnCode = json_object[0].get('returnCode')
                returnMessage = json_object[0].get('returnMessage')
                raise UserError(_("Failed the Operation on Updating the "
                                  "Onhand. "
                                  ' EFRIS error code: %s : %s \n '
                                  'returnCode: %s,'
                                  ' returnMessage: %s',
                                  vals.get('returnCode'),
                                  vals.get('returnMessage'),returnCode, returnMessage ))
        else:
            raise UserError(
                _('Authentication Failed with EFRIS URA. Please verify the API URL.'))

    def goods_quantity_reduce(self):
        reduce_stock = {
            "goodsStockIn": {
                "operationType": "102",
                "supplierTin": "",
                "supplierName": "",
                "adjustType": self.reduce_reason,
                "remarks": self.remarks or '',
                "stockInDate": "",
                "stockInType": "",
                "productionBatchNo": "",
                "productionDate": "",
                "branchId": "",
                "invoiceNo": "",
                "isCheckBatchNo": "0"
            },
            "goodsStockInItem": [{
                "commodityGoodsId": "",
                "goodsCode": self.product_code,
                "measureUnit": self.efris_goods_uom.value,
                "quantity": self.product_onhand,
                "unitPrice": self.unit_price,
            }]
        }
        response = self.env.company.efris_access("T131", reduce_stock)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'warning',
                        'message': _(
                            'Successfully Reduced the Product'
                            ' Onhand Quantity in EFRIS.'),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification

            else:
                raise UserError(_("Failed the Operation on Updating the "
                                  "Onhand. "
                                  ' EFRIS error code: %s : %s \n '
                                  'returnCode: %s,'
                                  ' returnMessage: %s',
                                  vals.get('returnCode'),
                                  vals.get('returnMessage')
                                  ))
        else:
            raise UserError(
                _('Authentication Failed with EFRIS URA. Please verify the API URL.'))

