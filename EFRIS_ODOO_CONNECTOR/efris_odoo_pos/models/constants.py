RESPONSE_DATETIME = '%d/%MM/%yyyy'
RESPONSE_DATETIME_FORMAT = '%d/%MM/%yyyy %HH:%mm:%ss'
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
INTERFACE_CODES = {
    'server_time': 'T101',  # Get Server Time
    'client_login': 'T103',  # Client Login
    'invoice_status': 'T106',  # Query invoice/refund details
    'query_invoice': 'T108',  # Query Signed Invoice based on Efris Fiscal No
    'sign_invoice': 'T109',  # Invoice Upload
    'sign_refund': 'T110',  # Credit Note Upload
    'taxpayer_info': 'T119',  # Query Taxpayer Information
    'exchange_rate': 'T121',  # Acquiring Exchange Rate
    'goods_category': 'T124',  # Get Commodity Categories
    'goods_inquiry': 'T127',  # Get goods and services from efris
}
PAYLOAD_FORMAT = {
    'data': {
        'content': '',
        'signature': '',
        'dataDescription': {
            'codeType': '0',
            'encryptCode': '0',
            'zipCode': '0'
        }
    },
    'globalInfo': {
        'appId': 'AP04',
        'version': '1.1.20191201',
        'dataExchangeId': '9230489223014123',
        'interfaceCode': '',
        'requestCode': 'TP',
        'requestTime': '',
        'responseCode': 'TA',
        'userName': 'admin',
        'deviceMAC': 'FFFFFFFFFFFF',
        'deviceNo': '',
        'tin': '',
        'brn': '',
        'taxpayerID': '1',
        'longitude': '116.397128',
        'latitude': '39.916527',
        'extendField': {
            'responseDateFormat': 'dd/MM/yyyy',
            'responseTimeFormat': 'dd/MM/yyyy HH:mm:ss',
            'referenceNo': '21PL010020807'
        }
    },
    'returnStateInfo': {
        'returnCode': '',
        'returnMessage': ''
    }
}

# invoice type
INVOICE_TYPE = {
    'out_invoice': '1',  # Invoice/Receipt'
    'out_refund': '5',  # Credit Memo/rebate'
    'debit': '4',  # Debit Note
}

INVOICE_KIND = {
    'invoice': '1',
    'receipt': '2'
}

CREDIT_NOTE_REASONS = {
    '101': 'Return of products due to expiry or damage, etc.',
    '102': 'Cancellation of the purchase.',
    '103': 'Invoice amount wrongly stated due to miscalculation of price, tax, or discounts, etc.',
    '104': 'Partial or complete waive off of the product sale after the invoice is generated and sent to customer.',
    '105': 'Others (Please specify)',
}

INDUSTRY_CODE = {
    'general': '101',
    'export': '102',
    'imported': '104',
    'telecom': '105',
    'stamp_duty': '106',
    'hotel_service': '107',
    'other_taxes': '108',
    'airline': '109',
    'edc': '110',
}

DATA_SOURCE = {
    'efd': '101',
    'windows_client_app': '102',
    'webservice_api': '103',
    'mis': '104',
    'web_portal': '105',
    'offline_mode': '106',
}

TAXPAYER_TYPE = {
    '201': 'Individual',
    '202': 'Non-Individual',
}

TAXPAYER_TYPE_SEL = [(key, value) for key, value in TAXPAYER_TYPE.items()]


BUYER_TYPE = {
    '0': 'B2B or B2G',
    '1': 'B2C',
    '2': 'B2Foreigner',
}
BUYER_TYPE_SEL = [(key, value) for key, value in BUYER_TYPE.items()]

SIGN_MODE = {
    'online': '1',
    'offline': '0',
}

PAYMENT_MODE = {
    'credit': '101',
    'cash': '102',  # default
    'cheque': '103',
    'demand_draft': '104',
    'mobile_money': '105',
    'card': '106',
    'eft': '107',
    'pos': '108',
    'rtgs': '109',
    'swift_transfer': '110',
}