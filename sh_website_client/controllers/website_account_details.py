from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
import logging, sys
_logger = logging.getLogger(__name__)

class CustomerPortalInerith(CustomerPortal):
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "access_token", 'username', 'is_autor', 'is_collaborator', 'platform', 'identifier', '_gpassword', 'html_url']