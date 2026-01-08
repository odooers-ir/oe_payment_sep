# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SEPController(http.Controller):
    _tokenize_url = "/payment/sep/tokenize"
    _return_url = '/payment/sep/return'

    @http.route(
        _tokenize_url, type='http', auth='public', methods=['POST'], csrf=False,
        save_session=False
    )
    def sep_tokenize(self, **data):
        """
        Initiate the payment process by requesting a token from SEP.
        """
        provider_id = data.pop('provider_id', None)
        if not provider_id:
            _logger.error("SEP Controller: provider_id is missing in the request data.")
            return request.redirect('/shop/payment')

        provider_sudo = request.env['payment.provider'].sudo().browse(int(provider_id))
        
        # Prepare payload for token request
        payload = {
            **data,
            'Action': 'token'
        }
        
        # Conversion logic: Ensure Amount is integer. 
        # Note: Check if multiplication by 10 is for Rial <-> Toman conversion.
        try:
            payload['Amount'] = int(float(payload.get('Amount', 0))) * 10
        except ValueError:
            _logger.error("SEP Controller: Invalid Amount format.")
            return request.redirect('/shop/payment')

        # Request token from SEP
        response = provider_sudo._sep_make_request(payload)
        token = response.get('token')
        
        _logger.info("Received SEP return token:\n%s", pprint.pformat(token))

        if token:
            # Redirect user to SEP payment gateway with the received token
            return request.redirect(f'https://sep.shaparak.ir/OnlinePG/SendToken?token={token}', code=301, local=False)

        # If no token, redirect back to payment page (error handling could be improved here)
        return request.redirect('/shop/payment')
    
    @http.route(
        _return_url, type='http', auth='public', methods=['GET', 'POST'], csrf=False,
        save_session=False
    )
    def sep_return_from_checkout(self, **data):
        """ Process the notification data sent by SEP after redirection from checkout. """
        _logger.info("Handling redirection from SEP with data:\n%s", pprint.pformat(data))
        
        # Handle the notification data to update transaction status
        request.env['payment.transaction'].sudo()._handle_notification_data('sep', data)
        
        # Redirect the user to the payment status page
        return request.redirect('/payment/status')