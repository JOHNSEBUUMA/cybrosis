# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError
import json
from .constants import DATETIME_FORMAT


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    efris_refund_reason = fields.Selection(string='EFRIS Refund Reason',
                                           selection=[('101',
                                                       'Return of products due to expiry or damage, etc.'),
                                                      ('102',
                                                       'Cancellation of the purchase.'),
                                                      ('103',
                                                       'Invoice amount wrongly stated due to miscalculation of price, tax, or discounts, etc'),
                                                      ('104',
                                                       'Partial or complete waive off of the product sale after the invoice is generated and sent to customer'),
                                                      ('105', 'Others')])
    is_reverse_payment = fields.Boolean(string="Is Reverse")

    def action_create_payments(self):
        """Overwriting the method of create payment for posting the
         record on EFRIS URA."""
        active_move_ids = self.env['account.move'].browse(
            self.env.context['active_id'])
        if not active_move_ids.reversed_entry_id:
            response = self.make_invoice_payload_content()
            inv_num = 'Invoice'
            if response:
                response_data = response.json()
                vals = response_data.get('returnStateInfo')
                if vals.get('returnCode') == '00':
                    base64_string = response_data.get('data').get('content')
                    decoded_bytes = base64.b64decode(base64_string)
                    decoded_string = decoded_bytes.decode('utf-8')
                    json_object = json.loads(decoded_string)
                    basic_info = json_object.get('basicInformation')
                    invoice_num = basic_info.get('invoiceNo')
                    payments = self._create_payments()
                    active_move_ids.write({
                        'efris_invoiceno': invoice_num,
                        'is_authenticated': True,
                    })
                    active_move_ids.get_invoice_info_from_efris()

                else:
                    raise UserError(_('Connection Failed with EFRIS URA. \n'
                                      'EFRIS error code: %s : %s',
                                      vals.get('returnCode'),
                                      vals.get('returnMessage')))
            else:
                raise UserError(_('Authentication Failed with EFRIS URA. '
                                  'Please verify the API URL.'))

        else:
            response = self.make_credit_note_payload_content()
            original_invoice = active_move_ids.reversed_entry_id
            original_invoice.write({

            })
            inv_num = 'Credit Note / Reversal Invoice'
            if response:
                response_data = response.json()
                vals = response_data.get('returnStateInfo')
                if vals.get('returnCode') == '00':
                    base64_string = response_data.get('data').get('content')
                    decoded_bytes = base64.b64decode(base64_string)
                    decoded_string = decoded_bytes.decode('utf-8')
                    json_object = json.loads(decoded_string)
                    credit_reference = json_object.get('referenceNo')
                    verification_code = original_invoice.verification_code
                    payments = self._create_payments()
                    active_move_ids.write({
                        'efris_referenceno': credit_reference,
                        'efris_invoiceno': original_invoice.efris_invoiceno,
                        'efris_invoiceid': original_invoice.efris_invoiceid,
                        'is_authenticated': True,
                        'fdn_no': original_invoice.fdn_no,
                        'verification_code': verification_code,
                        'efris_qr_code': original_invoice.efris_qr_code,
                        'is_efris_reversal': True
                    })
                    active_move_ids.get_credit_task_id()
                    # approval_crdt = active_move_ids.get_efris_credit_note_approval(
                    #     credit_reference, task_id)
                    # print('approval_crdt4................',approval_crdt.json())
                else:
                    raise UserError(_('Connection Failed with EFRIS URA. \n'
                                      'EFRIS error code: %s : %s',
                                      vals.get('returnCode'),
                                      vals.get('returnMessage')))
            else:
                raise UserError(_('Authentication Failed with EFRIS URA. '
                                  'Please verify the API URL.'))

        if self._context.get('dont_redirect_to_payments'):
            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'type': 'success',
                    'message': _('Successfully Uploaded the %s '
                                 ' with EFRIS URA.', inv_num),
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
            return notification
        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action

    def make_invoice_payload_content(self):
        """Method to create the Invoice Payload Content"""
        company = self.company_id
        active_move_ids = self.env['account.move'].browse(
            self.env.context['active_id'])
        formatted_date = active_move_ids.create_date.strftime("%Y%m%d")
        efris_invoiceno = str(self.communication) + str(formatted_date)
        goodsDetails = []
        taxDetails = []
        taxAmount = []
        grossAmount = []
        netAmount = []
        i = -1
        for rec in active_move_ids.invoice_line_ids:
            i = i + 1
            if not rec.product_id.has_efris_sync:
                raise UserError(
                    _('Product :[%s] %s, is not synchronized with EFRIS URA.',
                      rec.product_id.default_code,
                      rec.product_id.name))
            quantity = rec.quantity
            efris_unit_price = rec.efris_unit_price
            total_amount = quantity * efris_unit_price
            unit_tax = rec.efris_unit_price - rec.price_unit
            formatted_total = f"{total_amount:.2f}"
            formatted_tax_total = f"{quantity * unit_tax:.2f}"
            formatted_net_amount = f"{quantity * rec.price_unit:.2f}"
            product_details = {
                "deemedFlag": "2",
                "discountFlag": "2",
                "exciseFlag": "2",
                "exciseTax": "0",
                "goodsCategoryId": rec.product_id.efris_goods_category_id.category_code,
                "goodsCategoryName": rec.product_id.efris_goods_category_id.complete_name,
                "item": rec.product_id.efris_item_name,
                "itemCode": rec.product_id.efris_item_code,
                "orderNumber": i,
                "qty": rec.quantity,
                "unitPrice": efris_unit_price,
                "total": formatted_total,
                "taxRate": "0.18",
                "tax": formatted_tax_total,
                "unitOfMeasure": rec.product_id.efris_goods_uom.value,
                "vatApplicableFlag": "1",
            }
            goodsDetails.append(product_details)

            tax_details = {
                "grossAmount": formatted_total,
                "netAmount": formatted_net_amount,
                "taxAmount": formatted_tax_total,
                "taxCategory": "A: Standard",
                "taxCategoryCode": "01",
                "taxRate": "0.18",
                "taxRateName": "18%",
            }
            taxDetails.append(tax_details)
            taxAmount.append(quantity * unit_tax)
            grossAmount.append(quantity * efris_unit_price)
            netAmount.append(quantity * rec.price_unit)
        content = {
            "sellerDetails": {
                "address": company.business_place or "",
                "branchCode": "00",
                "branchId": "",
                "branchName": company.business_name,
                "businessName": company.business_name,
                "emailAddress": company.email,
                "legalName": company.legal_name,
                "linePhone": company.phone,
                "mobilePhone": company.mobile,
                "referenceNo": str(self.communication) + str(self.id),
                "ninBrn": "",
                "placeOfBusiness": company.business_place,
                "tin": company.login_tin,
            },
            "basicInformation": {
                "antifakeCode": "",
                "currency": self.currency_id.name,
                "currencyRate": "1",
                "dataSource": "106",
                "deviceNo": company.device_no,
                "invoiceId": "",
                "invoiceIndustryCode": "",
                "invoiceKind": "1",
                "invoiceNo": efris_invoiceno,
                "invoiceType": "1",
                "isBatch": "0",
                "isInvalid": "0",
                "isPreview": "0",
                "isRefund": "0",
                "issuedDate": (
                    self.create_date.strftime(DATETIME_FORMAT)),
                "issuedDatePdf": (
                    self.create_date.strftime(DATETIME_FORMAT)),
                "operator": self.env.user.name,
                "payWay": "102",
            },
            "buyerDetails": self.partner_id._get_buyer_details(),
            "goodsDetails": goodsDetails,
            "taxDetails": taxDetails,
            "summary": {
                "grossAmount": f"{sum(grossAmount):.2f}",
                "itemCount": len(netAmount),
                "modeCode": "0",
                "netAmount": f"{sum(netAmount):.2f}",
                "qrCode": "",
                "taxAmount": f"{sum(taxAmount):.2f}",
            }
        }
        response = company.efris_access('T109', content)
        return response

    def make_credit_note_payload_content(self):
        """Method to create the Credit Note Payload Content"""
        company = self.company_id
        active_move_ids = self.env['account.move'].browse(
            self.env.context['active_id'])
        string_value = dict(self._fields['efris_refund_reason'].selection).get(
            self.efris_refund_reason)
        goodsDetails = []
        taxDetails = []
        taxAmount = []
        grossAmount = []
        netAmount = []
        i = -1
        for rec in active_move_ids.invoice_line_ids:
            i = i + 1
            quantity = rec.quantity
            efris_unit_price = rec.efris_unit_price
            total_amount = quantity * efris_unit_price
            unit_tax = rec.efris_unit_price - rec.price_unit
            formatted_total = f"-{total_amount:.2f}"
            formatted_tax_total = f"-{quantity * unit_tax:.2f}"
            formatted_net_amount = f"-{quantity * rec.price_unit:.2f}"
            product_details = {
                "item": rec.product_id.efris_item_name,
                "itemCode": rec.product_id.efris_item_code,
                "qty": -rec.quantity,
                "unitOfMeasure": rec.product_id.efris_goods_uom.value,
                "unitPrice": rec.price_total,
                "total": formatted_total,
                "taxRate": rec.product_id.efris_goods_category_id.rate,
                "tax": formatted_tax_total,
                "orderNumber": i,
                "deemedFlag": "2",
                "exciseFlag": "2",
                "categoryId": "",
                "categoryName": "",
                "goodsCategoryId": rec.product_id.efris_goods_category_id.category_code,
                "goodsCategoryName": rec.product_id.efris_goods_category_id.complete_name,
            }
            goodsDetails.append(product_details)
            tax_details = {
                "grossAmount": formatted_total,
                "netAmount": formatted_net_amount,
                "taxAmount": formatted_tax_total,
                "taxCategory": "A: Standard",
                "taxCategoryCode": "01",
                "taxRate": "0.18",
                "taxRateName": "18%",
            }
            taxDetails.append(tax_details)
            taxAmount.append(quantity * unit_tax)
            grossAmount.append(quantity * efris_unit_price)
            netAmount.append(quantity * rec.price_unit)
        original_invoice = active_move_ids.reversed_entry_id
        current_time = datetime.now()
        formatted_rev_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        reversal_content = {
            "oriInvoiceId": original_invoice.efris_invoiceid,
            "oriInvoiceNo": original_invoice.efris_invoiceno,
            "reasonCode": self.efris_refund_reason,
            "reason": string_value,
            "applicationTime": formatted_rev_time,
            "invoiceApplyCategoryCode": "101",
            "currency": "UGX",
            "contactName": "",
            "contactMobileNum": "",
            "contactEmail": "",
            "source": "106",
            "remarks": self.communication,
            "sellersReferenceNo": "",
            "goodsDetails": goodsDetails,
            "taxDetails": taxDetails,
            "summary": {
                "grossAmount": f"-{sum(grossAmount):.2f}",
                "itemCount": len(netAmount),
                "modeCode": "0",
                "netAmount": f"-{sum(netAmount):.2f}",
                "qrCode": "",
                "taxAmount": f"-{sum(taxAmount):.2f}",
            },
            "payWay": [],
            "buyerDetails": self.partner_id._get_buyer_details(),
            "basicInformation": {
                "operator": self.env.user.name,
                "invoiceKind": "1",
                "invoiceIndustryCode": "",
                "branchId": ""
            }
        }
        response = company.efris_access('T110', reversal_content)
        return response
