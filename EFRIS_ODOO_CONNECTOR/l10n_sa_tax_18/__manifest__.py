# -*- coding: utf-8 -*-

{
    'name': 'Ugandan - Accounting',
    'version': '1.0',
    'category': 'Accounting/Localizations/Account Charts',
    'description': """This module will helps to install the ugandan sales tax of 18%""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'account'],
    'data': [
        'data/sale_tax_18.xml',
    ],

    'license': 'AGPL-3',
    'installable': True,
    'post_init_hook': 'create_sale_tax_18',
    'application': False,
    'auto_install': False,
}
