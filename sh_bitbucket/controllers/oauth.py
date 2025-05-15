import logging
from odoo import http
from odoo.http import request
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)

class BitbucketOAuthController(http.Controller):
    @http.route('/en/bitbucket/callback', type='http', auth='public', website=True, csrf=False)
    def oauth_callback(self, **kw):
        """Handle Bitbucket OAuth callback"""
        _logger.info("=== Bitbucket OAuth Callback ===")
        _logger.info("Received parameters: %s", kw)
        
        # Extract parameters
        code = kw.get('code')
        state = kw.get('state')
        error = kw.get('error')
        error_description = kw.get('error_description')
        
        if error:
            _logger.error("OAuth Error: %s - %s", error, error_description)
            return f"Authentication failed: {error_description}"
            
        if not code:
            _logger.error("No authorization code received")
            return "Error: No authorization code received"
            
        _logger.info("Successfully received OAuth code: %s", code)
        _logger.info("State parameter: %s", state)
        
        # Store the code temporarily in session
        request.session['bitbucket_oauth_code'] = code
        request.session['bitbucket_oauth_state'] = state
        
        return """
            <html>
                <head>
                    <title>Bitbucket Authentication Successful</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
                        .success { color: #28a745; }
                        .code { background: #f8f9fa; padding: 10px; margin: 20px; border-radius: 4px; }
                    </style>
                </head>
                <body>
                    <h2 class="success">Authentication Successful!</h2>
                    <p>Your authorization code:</p>
                    <div class="code">%s</div>
                    <p>You can now close this window and return to the application.</p>
                </body>
            </html>
        """ % code 