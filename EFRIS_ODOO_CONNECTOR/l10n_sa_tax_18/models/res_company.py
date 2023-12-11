# -*- coding: utf-8 -*-
import gzip
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Model for representing an invoice in the Odoo accounting system."""
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals):
        res = super(ResCompany, self).create(vals)
        efris_tax = self.env.ref(
            'l10n_sa_tax_18.efris_tax_18_percent').with_user(1)
        efris_tax_dict = efris_tax.read(
            ['name', 'sequence', 'type_tax_use', 'amount', 'amount_type',
             'active', 'company_id'])
        if res.id != efris_tax.company_id.id:
            efris_tax_dict[-1].update({
                'company_id': res.id,
                'country_id': self.env.ref('base.ug').id
            })
            self.env['account.tax'].with_user(1).with_context(
                force_company=res.id).create(efris_tax_dict[-1])
        return res
