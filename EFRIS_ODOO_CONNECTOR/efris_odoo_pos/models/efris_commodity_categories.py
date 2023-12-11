# -*- coding: utf-8 -*-
import base64
import gzip
import io
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EfrisCommodityCategories(models.Model):
    _name = 'efris.commodity.categories'
    _description = "Goods Commodity Category"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Category Name')
    complete_name = fields.Char('Complete Name',
                                compute='_compute_complete_name')
    parent_id = fields.Many2one('efris.commodity.categories',
                                'Parent Category',
                                index=True,
                                ondelete='cascade')
    parent_path = fields.Char(index=True, unaccent=False)
    category_code = fields.Char(string='Category Code')
    parent_code = fields.Char(string='Parent Code')
    rate = fields.Char(string='Rate')
    is_leaf_node = fields.Selection(string='Is Leaf Node',
                                    selection=[('101', 'Yes'), ('102', 'No')])
    service_mark = fields.Selection(string='Service Mark',
                                    selection=[('101', 'Yes'), ('102', 'No')])
    is_zero_rate = fields.Selection(string='Is Zero Rate',
                                    selection=[('101', 'Yes'), ('102', 'No')])
    commodity_category_Level = fields.Char(string='Commodity Category Level')
    is_exempt = fields.Selection(string='isExempt',
                                    selection=[('101', 'Yes'), ('102', 'No')])
    enable_status_code = fields.Boolean(string='Enable Status')
    exclusion = fields.Selection(string='Exclusion',
                                    selection=[('0', 'Zero'), ('1', 'Exempt'),
                                               ('2', 'No exclusion'), ('3', 'Both 0% & -')])

    def _compute_complete_name(self):
        for category in self:
            category.complete_name = False
            if category.category_code:
                category.complete_name = '(%s) %s' % (category.category_code, category.name)
            else:
                category.complete_name = category.name

    def _commodity_cron_action(self, record):
        content = {
            "pageNo": str(record),
            "pageSize": "9999"
        }
        response = self.env.company.efris_access("T124", content)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            base64_string = response_data.get('data').get('content')
            decoded_bytes = base64.b64decode(base64_string)
            with gzip.GzipFile(fileobj=io.BytesIO(decoded_bytes), mode='rb') as f:
                json_object = json.loads(f.read().decode('utf-8'))
            category_list = self.env['efris.commodity.categories'].search([]).mapped(
                'category_code')
            records = json_object.get('records')
            for rec in records:
                if rec.get('commodityCategoryCode') not in category_list and rec.get('commodityCategoryLevel') == '4':
                    self.env['efris.commodity.categories'].create({
                        'name': rec.get('commodityCategoryName'),
                        'category_code': rec.get('commodityCategoryCode'),
                        'parent_code': rec.get('parentCode'),
                        'rate': rec.get('rate'),
                        'is_leaf_node': rec.get('isLeafNode'),
                        'service_mark': rec.get('serviceMark'),
                        'is_zero_rate': rec.get('isZeroRate'),
                        'commodity_category_Level': rec.get('commodityCategoryLevel'),
                        'is_exempt': rec.get('isExempt'),
                        'enable_status_code': rec.get('enableStatusCode'),
                        'exclusion': rec.get('exclusion'),

                    })
        else:
            raise UserError(_('Authentication Failed with EFRIS URA.Please verify the API URL.'))

    def _get_commodity_category_ids(self):
        for record in range(16):
            delay = self.with_delay(priority=1, eta=60)
            delay._commodity_cron_action(record)

