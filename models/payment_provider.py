# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
import requests
from zeep import Client

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.oe_payment_sep import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('sep', 'SEP')], ondelete={'sep': 'set default'}
    )
    
    sep_terminal_id = fields.Char(
        string="Terminal ID",
        help="The ID solely used to identify the terminal account with SEP (Saman Electronic Payment)"
    )
    sep_password = fields.Char(
        string="Terminal Password",
        groups='base.group_system'
    )

    #=== BUSINESS METHODS ===#
    
    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'sep':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _sep_make_request(self, data=None):
        """ Make a request at SEP (Saman Electronic Payment) endpoint. """
        self.ensure_one()
        endpoint = 'https://sep.shaparak.ir/OnlinePG/OnlinePG'

        try:
            response = requests.post(endpoint, data=data, timeout=60)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s", endpoint, pprint.pformat(data)
                )
                raise ValidationError(
                    "SEP (Saman Electronic Payment): " + _(
                        "The communication with the API failed. SEP gave us the following "
                        "information: %s", response.json().get('detail', '')
                    ))
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", endpoint)
            raise ValidationError(
                "SEP (Saman Electronic Payment): " + _("Could not establish the connection to the API.")
            )
        return response.json()

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'sep':
            return default_codes
        return const.DEFAULT_PAYMENT_METHODS_CODES
    

    def _sep_verify_request(self, data=None):
        """ Verify transaction using SEP (Saman Electronic Payment) SOAP service. """
        self.ensure_one()
        endpoint = 'https://verify.sep.ir/payments/referencepayment.asmx?WSDL'

        reference = data.get('RefNum')
        response = None

        try:
            client = Client(wsdl=endpoint)
            # Call the service using the correct terminal ID
            response = client.service.verifyTransaction(reference, self.sep_terminal_id)
        except Exception as e:
            # e.message is deprecated in Python 3, use str(e) or logging
            _logger.error("SEP Verify Request failed: %s", str(e))

        return response