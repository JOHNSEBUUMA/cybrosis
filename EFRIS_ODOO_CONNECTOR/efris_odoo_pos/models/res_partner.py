# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Model for representing the users"""
    _inherit = 'res.partner'

    partner_type = fields.Selection(string='Partner Type',
                                    selection=([('0', 'Business'),
                                                ('1', 'Consumer'),
                                                ('2', 'Government'),
                                                ('3', 'Foreigner')]),
                                    required=True,
                                    default='1')
    taxpayer_type = fields.Selection(string='TaxPayer Type',
                                     selection=([('201', 'Individual'),
                                                 ('202', 'Non-Individual')]),
                                     required=True,
                                     default='201')

    def _get_buyer_details(self):
        """Method to get the buyer details"""
        self.ensure_one()
        if self.parent_id:
            res = self.parent_id
        else:
            res = self

        if not res.partner_type:
            raise ValidationError('Please define this contacts Partner Type.')
        if res.partner_type == '0' and not res.vat:
            raise ValidationError(
                'Contacts of partner type Business or Government must have a Tin')

        buyer_details = {
            "buyerTin": res.vat and res.vat[:21] or '',
            "buyerNinBrn": "",
            "buyerPassportNum": "",
            "buyerLegalName": res.name[:256],
            "buyerBusinessName": "",
            "buyerAddress": "",
            "buyerEmail": res.email and res.email[:50] or "",
            "buyerMobilePhone": res.mobile and res.mobile[:30] or "",
            "buyerLinePhone": res.phone and res.phone[:30] or "",
            "buyerPlaceOfBusi": "",
            "buyerType": res.partner_type,
            "buyerCitizenship": "",
            "buyerSector": "",
            "buyerReferenceNo": str(res.id)[:50]
        }
        return buyer_details