# -*- coding: utf-8 -*-
from . import models
from odoo import api, SUPERUSER_ID


def create_sale_tax_18(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    efris_tax = env.ref('l10n_sa_tax_18.efris_tax_18_percent')
    efris_tax_dict = efris_tax.read(
        ['name', 'sequence', 'type_tax_use', 'amount', 'amount_type', 'active',
         'company_id'])
    current_companies = env['res.company'].search([])
    for rec in current_companies:
        if rec.id != efris_tax.company_id.id:
            efris_tax_dict[-1].update({
                'company_id': rec.id,
            })
            env['account.tax'].with_context(force_company=rec.id).create(
                efris_tax_dict[-1])
