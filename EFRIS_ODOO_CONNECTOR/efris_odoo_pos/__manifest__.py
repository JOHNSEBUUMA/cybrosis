# -*- coding: utf-8 -*-

{
    'name': 'EFRIS Odoo Connector',
    'version': '16.0.1.0.0',
    'summary': """This Module will help to integrate EFRIS to Odoo""",
    'description': """This Module will help to integrate EFRIS to Odoo POS""",
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web', 'point_of_sale', 'queue_job_cron_jobrunner',
                'queue_job', 'l10n_sa_tax_18', 'l10n_za'],
    'data': [
            # 'data/efris_pos_paper_format.xml',
            # 'data/efris_invoice_reciept_template.xml',
            'security/ir.model.access.csv',
            'views/account_move_views.xml',
            'views/product_template_view.xml',
            'views/res_company_view.xml',
            'views/res_partner_view.xml',
            'views/efris_commodity_categories_view.xml',
            'views/account_payment_register.xml',
            'views/efris_product_uom_views.xml',
            'report/efris_report_invoice.xml',
            'wizard/efris_onhand.xml',

        ],
    # 'assets': {
    #         'point_of_sale.assets': [
    #             'efris_odoo_pos/static/src/js/PaymentScreen.js'
    #         ],
    #     },
    'license': 'AGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
