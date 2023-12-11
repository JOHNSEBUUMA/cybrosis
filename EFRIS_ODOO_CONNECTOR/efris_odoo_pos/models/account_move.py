# -*- coding: utf-8 -*-
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError, Warning
import json
import logging

INVOICE = 'out_invoice'
REFUND = 'out_refund'

INVOICE_MULTIPLIER_MAP = {
    INVOICE: 1,
    REFUND: -1,
}

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    """Model for representing an invoice in the Odoo accounting system."""
    _inherit = "account.move"

    fdn_no = fields.Char(string="FDN No", copy=False)
    orig_fdn_no = fields.Char(string="Original FDN No", copy=False)
    verification_code = fields.Char(string="Verification Code:", copy=False)
    efris_inv_bill_number = fields.Char(string='EFRIS INV Bill Number')
    is_authenticated = fields.Boolean(string="EFRIS Authentication",
                                      readonly=True,
                                      copy=False)
    is_efris_reversal = fields.Boolean(string='EFRIS Credit Note Reversal',
                                       readonly=True,
                                       copy=False
                                       )
    is_efris_credit_cancel = fields.Boolean(string='Credit Cancel',
                                            readonly=True,
                                            copy=False
                                            )
    efris_invoiceno = fields.Char(string='EFRIS Invoice Number', readonly=True,
                                  copy=False)
    efris_invoiceid = fields.Char(string='EFRIS Invoice Id', readonly=True,
                                  copy=False)
    efris_qr_code = fields.Binary(string='EFRIS QR Code', readonly=True,
                                  copy=False)
    efris_verification_code = fields.Char(string='EFRIS Verification Code',
                                          readonly=True,
                                          copy=False)
    efris_referenceno = fields.Char(string='EFRIS Credit Note Ref',
                                    readonly=True, copy=False)
    efris_refund_reason = fields.Char(string='EFRIS Credit Note Reason')
    efris_remark = fields.Text('Efris Remark')
    is_ug = fields.Boolean(string='Uganda Company', compute='_compute_is_ug')
    credit_note_application_id = fields.Char(string="Credit Note Id",
                                             readonly=True,
                                             copy=False)
    credit_note_task_id = fields.Char(string='Credit Note Task Id',
                                      readonly=True,
                                      copy=False)
    credit_note_remark = fields.Char(string='Remarks',
                                      readonly=True,
                                      copy=False)

    @api.depends('company_id')
    def _compute_is_ug(self):
        for rec in self:
            rec.is_ug = (
                    rec.company_id.country_id.code == 'UG' and rec.move_type in (
                'out_invoice', 'out_refund'))

    def get_invoice_qr_code(self, summary_info):
        if qrcode and base64:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            data = str(summary_info.get('qrCode'))
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image()
            BytesIO_img = BytesIO()
            img.save(BytesIO_img, format="PNG")
            qr_image = base64.b64encode(BytesIO_img.getvalue())
            self.update({'efris_qr_code': qr_image})

    def get_invoice_info_from_efris(self):
        invoice_num = self.efris_invoiceno
        invoice_content = {"invoiceNo": invoice_num}
        response = self.company_id.efris_access('T108', invoice_content)
        if response:
            response_data = response.json()
            base64_string = response_data.get('data').get('content')
            decoded_bytes = base64.b64decode(base64_string)
            decoded_string = decoded_bytes.decode('utf-8')
            json_object = json.loads(decoded_string)
            basic_info = json_object.get('basicInformation')
            summary_info = json_object.get('summary')
            self.write({
                'efris_invoiceid': basic_info.get('invoiceId'),
                'fdn_no': invoice_num,
                'verification_code': basic_info.get('antifakeCode'),
            })
            self.get_invoice_qr_code(summary_info)
        else:
            raise UserError(
                _('Authentication Failed with EFRIS URA.'
                  ' Please verify the API URL.'))

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        super(AccountInvoice, self).action_register_payment()
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_is_reverse_payment': True if self.reversed_entry_id else False
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def get_efris_credit_note_application_detail(self):
        """Method to get credit note application details"""
        content = {"referenceNo": "",
                   "oriInvoiceNo": "",
                   "invoiceNo": "",
                   "combineKeywords": "",
                   "approveStatus": "",
                   "queryType": "1",
                   "invoiceApplyCategoryCode": "",
                   "startDate": "",
                   "endDate": "",
                   "pageNo": "1",
                   "pageSize": "15"
                   }
        response = self.company_id.efris_access('T111', content)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                base64_string = response_data.get('data').get('content')
                decoded_bytes = base64.b64decode(base64_string)
                decoded_string = decoded_bytes.decode('utf-8')
                json_object = json.loads(decoded_string)
                page_detail = json_object.get('page')
                page_count = page_detail.get('pageCount')
                records = json_object.get('records')
                for rec in records:
                    if rec.get('referenceNo') == self.efris_referenceno:
                        credit_id = rec.get('id')
                        self.write({'credit_note_application_id': credit_id})
                        return credit_id

    def get_credit_task_id(self):
        """Method to get Credit Note Task ID"""
        credit_id = self.get_efris_credit_note_application_detail()
        if credit_id:
            content = {
                "id": credit_id
            }
            response = self.company_id.efris_access('T112', content)
            if response:
                response_data = response.json()
                vals = response_data.get('returnStateInfo')
                if vals.get('returnCode') == '00':
                    base64_string = response_data.get('data').get('content')
                    decoded_bytes = base64.b64decode(base64_string)
                    decoded_string = decoded_bytes.decode('utf-8')
                    json_object = json.loads(decoded_string)
                    task_id = json_object.get('taskId')
                    remark = json_object.get('remarks')
                    self.write({'credit_note_task_id': task_id})
                    self.write({'credit_note_remark': remark})
                    return task_id

    def get_efris_credit_note_approval(self):
        """Method to get Credit Note Approval"""
        ref_num = self.efris_referenceno
        task_id = self.credit_note_task_id
        remarks = self.credit_note_remark
        approval_content = {
            "referenceNo": ref_num,
            "approveStatus": "101",
            "taskId": task_id,
            "remark": remarks
        }
        response = self.company_id.efris_access('T113', approval_content)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'info',
                        'message': _('Credit Note with  %s is Approved Successfully', ref_num),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification
            else:
                self.update({'is_authenticated': False})
                raise UserError(_('Failed to Approve the Credit Note with'
                                  ' Reference number  %s. \n'
                                  'EFRIS error code: %s : %s',
                                  ref_num,
                                  vals.get('returnCode'),
                                  vals.get('returnMessage')))
        else:
            raise UserError(
                _('Authentication Failed with EFRIS URA.Please verify the API URL.'))

    def get_efris_credit_note_cancel(self):
        """Method to cancel the Credit Note"""
        cancel_content = {
            "oriInvoiceId": self.efris_invoiceid,
            "invoiceNo": self.efris_invoiceno,
            "reason": "",
            "reasonCode": "103",
            "invoiceApplyCategoryCode": "104"
        }
        response = self.company_id.efris_access('T114', cancel_content)
        if response:
            response_data = response.json()
            vals = response_data.get('returnStateInfo')
            if vals.get('returnCode') == '00':
                self.write({'is_efris_credit_cancel': True})
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'type': 'info',
                        'message': _(
                            'Credit Note with  %s is Cancelled Successfully',
                            self.efris_referenceno),
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
                return notification
            else:
                raise UserError(_('Connection Failed with EFRIS URA. \n'
                                  'EFRIS error code: %s : %s',
                                  vals.get('returnCode'),
                                  vals.get('returnMessage')))

