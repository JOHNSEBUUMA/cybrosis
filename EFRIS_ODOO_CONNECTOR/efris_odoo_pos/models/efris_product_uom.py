# -*- coding: utf-8 -*-
import base64
import gzip
import io
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EfrisProductUOM(models.Model):
    _name = 'efris.product.uom'
    _description = "Goods Unit of Measure"
    _rec_name = "name"

    value = fields.Char(string="EFRIS Value")
    name = fields.Char(string="Name")

    def _fetch_efris_uom(self):
        response = self.env.company.efris_access("T115", None)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            base64_string = response_data.get('data').get('content')
            decoded_bytes = base64.b64decode(base64_string)
            with gzip.GzipFile(fileobj=io.BytesIO(decoded_bytes), mode='rb') as f:
                json_object = json.loads(f.read().decode('utf-8'))
            uom_list = self.env['efris.product.uom'].search([]).mapped('value')
            uom_records = json_object.get('rateUnit')
            for rec in uom_records:
                if rec.get('value') not in uom_list:
                    self.env['efris.product.uom'].create({
                        'name': rec.get('name'),
                        'value': rec.get('value'),
                    })
        else:
            raise UserError(_('Authentication Failed with EFRIS URA.Please verify the API URL.'))


