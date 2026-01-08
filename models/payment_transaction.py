# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.oe_payment_sep.controllers.main import SEPController


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return SEP-specific rendering values. """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'sep':
            return res

        payload = self._sep_prepare_payment_request_payload()
        return payload
    
    def _sep_prepare_payment_request_payload(self):
        """ Create the payload for the payment request based on the transaction values. """
        base_url = self.provider_id.get_base_url()
        return {
            'provider_id': self.provider_id.id,
            'api_url': urls.url_join(base_url, SEPController._tokenize_url),
            'Amount': int(self.amount),
            'ResNum': self.reference,
            'MID': self.provider_id.sep_terminal_id,
            'RedirectURL': urls.url_join(base_url, SEPController._return_url)
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on SEP data. """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'sep' or len(tx) == 1:
            return tx

        # Find transaction by reference (ResNum in SEP callback)
        reference = notification_data.get('ResNum')
        tx = self.search(
            [('reference', '=', reference), ('provider_code', '=', 'sep')]
        )
        if not tx:
            raise ValidationError("SEP (Saman Electronic Payment): " + _(
                "No transaction found matching reference %s.", reference
            ))
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on SEP data. """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'sep':
            return
        
        # In SEP: ResNum is our internal reference, RefNum is the bank's reference
        res_num = notification_data.get('ResNum')
        ref_num = notification_data.get('RefNum')
        
        # Verify the transaction amount with the bank
        # Note: logic result/10 suggests conversion (e.g., Rials to Tomans or vice versa)
        result = self.provider_id._sep_verify_request(notification_data)
        
        # Check if State is OK and amount matches (assuming result is in Rials and amount in Tomans?)
        if notification_data.get('State') == 'OK' and result and (result / 10) == self.amount:
            self.provider_reference = ref_num
            self._set_done()
        else:
            error_msg = notification_data.get('Status', 'Unknown Error')
            self._set_error(
                "SEP (Saman Electronic Payment): " + _("The payment encountered an error with code %s", error_msg)
            )