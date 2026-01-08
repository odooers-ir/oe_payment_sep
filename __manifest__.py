# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: SEP (Saman Electronic Payment)',
    'version': '18.0.1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 351,
    'summary': "A Payment Provider for Saman Electronic Payment (SEP) covering IRAN.",
    'description': " ",  # Non-empty string to avoid loading the README file.
    'author': 'Odooers',
    'website': 'https://www.odooers.ir/',
    'depends': ['payment'],
    'data': [
        'views/payment_sep_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}