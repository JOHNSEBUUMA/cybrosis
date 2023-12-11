# -*- coding: utf-8 -*-
import gzip
from datetime import datetime
import logging
import requests
import base64
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from uuid import uuid4
import json
from .constants import DATETIME_FORMAT, PAYLOAD_FORMAT
from odoo import fields, models, _
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Model for representing an invoice in the Odoo accounting system."""
    _inherit = "res.company"

    efris_enable = fields.Boolean(string='Enable EFRIS',
                                  help="Enable Invoices Signing to Efris")
    login_tin = fields.Char(string='TIN Number')
    login_password = fields.Char(string='Login Password')
    device_no = fields.Char(string='Device Number')
    api_url = fields.Char(string='API URL')
    tax_payer_id = fields.Char(string='Tax Payers ID',readonly=True)

    legal_name = fields.Char(string='Company Legal Name', readonly=True)
    business_name = fields.Char(string='Company Business Name',
                                      readonly=True)
    business_place = fields.Text(string='Company Business Place',
                                       readonly=True)
    branch_id = fields.Char(string='Company Branch Id', readonly=True)
    branch_code = fields.Char(string='Company Branch Code',
                                    readonly=True)
    branch_name = fields.Char(string='Company Branch Name',
                                    readonly=True)
    credit_max = fields.Char(string='Credit Memo Period (Days)', readonly=True,
                                   help='The maximum number of days allowed to make a credit note '
                                        'from when original invoice was signed.')
    is_authenticated = fields.Boolean(string='Authenticated', readonly=True)

    def efris_access(self, interface, content=None):
        """Method to get access from EFRIS URA"""
        headers = {'Content-Type': 'application/json'}
        payload = self._make_payload_data(interface, content)
        url = self.api_url
        response = requests.request('POST', url, headers=headers, data=json.dumps(payload))
        return response

    def get_efris_authentication(self):
        """Method to get EFRIS Authentication from a button action"""
        self.ensure_one()
        if not self.login_tin or not self.device_no:
            raise ValidationError('Please define a company TIN No or add a Device Number and run this again!')
        response = self.efris_access('T101', None)
        if response:
            response_data = response.json()
            response_code = response_data.get('returnStateInfo')
            if response_code.get('returnCode') == '00':
                res = self.efris_access('T103', content=None)
                response_data = res.json()
                content = response_data.get('data', {}).get('content')
                try:
                    res_content = base64.b64decode(content.encode('utf-8')).decode('utf-8')
                except UnicodeDecodeError:
                    res_content = gzip.decompress(base64.b64decode(content.encode('utf-8'))).decode('utf-8')
                json_content = json.loads(res_content)
                taxpayer = json_content.get('taxpayer')
                branch = json_content.get('taxpayerBranch')
                self.write({
                    'legal_name': taxpayer.get('legalName'),
                    'tax_payer_id': taxpayer.get('id'),
                    'business_name': taxpayer.get('businessName'),
                    'email': taxpayer.get('contactEmail'),
                    'mobile': taxpayer.get('contactMobile'),
                    'phone': taxpayer.get('contactNumber'),
                    'business_place': taxpayer.get('placeOfBusiness'),
                    'branch_id': branch.get('id'),
                    'branch_code': branch.get('branchCode'),
                    'branch_name': branch.get('branchName'),
                    'credit_max': json_content.get('creditMemoPeriodDate'),
                    'is_authenticated': True
                })
                # Fetching the EFRIS Product UOM
                self.env['efris.product.uom']._fetch_efris_uom()
                # Fetching the EFRIS Commodity Categories
                self.env['efris.commodity.categories']._get_commodity_category_ids()
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'success',
                        'message': _('Successfully Connected with EFRIS URA.'),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification

            else:
                self.update({'is_authenticated': False})
                raise UserError(_('Connection Failed with EFRIS URA.z'
                                  'EFRIS error code: %s : %s', response_code.get('returnCode'),
                                  response_code.get('returnMessage')))
        else:
            raise UserError(_('Authentication Failed with EFRIS URA.Please verify the API URL.'))

    def _make_payload_data(self, interface, content=None):
        """Method to make Payload content"""
        payload_data = PAYLOAD_FORMAT.copy()
        request_utc_time = datetime.utcnow() + relativedelta(hours=3)
        formatted_utc_time = request_utc_time.strftime(DATETIME_FORMAT)
        # Define your request data
        payload_data['globalInfo'].update({
            'tin': self.login_tin,
            'deviceNo': self.device_no,
            'brn': '',
            'dataExchangeId': str(uuid4())[:32],
            'requestTime': formatted_utc_time,
            'interfaceCode': interface,
            'taxpayerID': self.tax_payer_id or '1'
        })
        if content:
            # base64-encoded string of the content
            content = base64.b64encode(str.encode(str(content))).decode('utf-8')
            payload_data['data'].update(content=content)
        return payload_data

    def _get_seller_details(self):
        """Method to get seller details"""
        self.ensure_one()
        req_fields = [self.login_tin, self.contact_email, self.branch_id,
                      self.legal_name]
        if not all(req_fields):
            labels = ['Pin No', 'Contact Email', 'Branch Id', 'Legal Name']
            raise ValidationError(
                f'Missing company configuration, one of these company fields is not set {labels}')

        return {
            "tin": self.login_tin,
            "legalName": self.partner_id,
            "businessName": self.business_name,
            "emailAddress": self.email,
            "placeOfBusiness": self.street,
            "branchId": self.branch_id,
            "branchName": self.branch_name,
            "branchCode": self.branch_code,
            "ninBrn": "",
            "isCheckReferenceNo": "0",
            "mobilePhone": self.mobile or "",
            "linePhone": self.phone or "",
            "address": "",
            "referenceNo": "",
        }

    def _get_server_time(self, company):
        """Method to get the server time for Offline enabler"""
        data_info = {
            'content': '',
            'signature': '',
            'dataDescription': {
                'codeType': 0,
                'encryptCode': 0,
                'zipCode': 0
            }
        }
        global_info = {'interfaceCode': 'T101'}
        payload = self._make_payload_data(company, data_info, global_info, crypt=False)
        self.efris_access(company, payload)
