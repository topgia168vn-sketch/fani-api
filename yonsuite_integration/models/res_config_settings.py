from dateutil.relativedelta import relativedelta
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    yonsuite_base_url = fields.Char(
        string='YonSuite Base URL',
        config_parameter='yonsuite_integration.base_url',
        default='https://c1.yonyoucloud.com/iuap-api-auth',
        help='Base URL for YonSuite API'
    )

    yonsuite_app_key = fields.Char(
        string='YonSuite App Key',
        config_parameter='yonsuite_integration.app_key',
        help='Application Key for YonSuite API'
    )

    yonsuite_app_secret = fields.Char(
        string='YonSuite App Secret',
        config_parameter='yonsuite_integration.app_secret',
        help='Application Secret for YonSuite API'
    )

    yonsuite_access_token = fields.Char(
        string='YonSuite Access Token',
        config_parameter='yonsuite_integration.access_token',
        readonly=True,
        help='Current access token for YonSuite API'
    )

    yonsuite_token_expire_time = fields.Datetime(
        string='Token Expire Time',
        config_parameter='yonsuite_integration.token_expire_time',
        readonly=True,
        help='When the current access token will expire'
    )

    yonsuite_last_token_refresh = fields.Datetime(
        string='Last Token Refresh',
        config_parameter='yonsuite_integration.last_token_refresh',
        readonly=True,
        help='When the token was last refreshed'
    )

    yonsuite_refresh_count = fields.Integer(
        string='Refresh Count',
        config_parameter='yonsuite_integration.refresh_count',
        readonly=True,
        default=0,
        help='Number of times the token has been refreshed'
    )

    yonsuite_root_org_code = fields.Char(
        string='Root Organization Code',
        config_parameter='yonsuite_integration.root_org_code',
        default='global00',
        help='Root organization code for querying level 0 orgunits'
    )

    # Partners sync statistics
    yonsuite_partners_current_page = fields.Integer(
        string='Partners Current Page',
        config_parameter='yonsuite_integration.partners_current_page',
        readonly=True,
        default=1,
        help='Current page index for partners sync'
    )

    yonsuite_partners_total_synced = fields.Integer(
        string='Partners Total Synced',
        config_parameter='yonsuite_integration.partners_total_synced',
        readonly=True,
        default=0,
        help='Total number of partners synced'
    )

    yonsuite_partners_last_sync = fields.Datetime(
        string='Partners Last Sync',
        config_parameter='yonsuite_integration.partners_last_sync',
        readonly=True,
        help='Last time partners were synced'
    )

    # Products sync statistics
    yonsuite_products_current_page = fields.Integer(
        string='Products Current Page',
        config_parameter='yonsuite_integration.products_current_page',
        readonly=True,
        default=1,
        help='Current page index for products sync'
    )

    yonsuite_products_total_synced = fields.Integer(
        string='Products Total Synced',
        config_parameter='yonsuite_integration.products_total_synced',
        readonly=True,
        default=0,
        help='Total number of products synced'
    )

    yonsuite_products_last_sync = fields.Datetime(
        string='Products Last Sync',
        config_parameter='yonsuite_integration.products_last_sync',
        readonly=True,
        help='Last time products were synced'
    )

    # Orders sync statistics
    yonsuite_orders_current_page = fields.Integer(
        string='Orders Current Page',
        config_parameter='yonsuite_integration.orders_current_page',
        readonly=True,
        default=1,
        help='Current page index for orders sync'
    )
    
    yonsuite_orders_total_synced = fields.Integer(
        string='Orders Total Synced',
        config_parameter='yonsuite_integration.orders_total_synced',
        readonly=True,
        default=0,
        help='Total number of orders synced'
    )
    
    yonsuite_orders_last_sync = fields.Datetime(
        string='Orders Last Sync',
        config_parameter='yonsuite_integration.orders_last_sync',
        readonly=True,
        help='Last time orders were synced'
    )

    # Vendors pagination fields
    yonsuite_vendors_current_page = fields.Integer(
        string='Vendors Current Page',
        config_parameter='yonsuite_integration.vendors_current_page',
        readonly=True,
        default=1,
        help='Current page index for vendors sync'
    )

    # Brands pagination fields
    yonsuite_brands_current_page = fields.Integer(
        string='Brands Current Page',
        config_parameter='yonsuite_integration.brands_current_page',
        readonly=True,
        default=1,
        help='Current page index for brands sync'
    )

    # Units pagination fields
    yonsuite_units_current_page = fields.Integer(
        string='Units Current Page',
        config_parameter='yonsuite_integration.units_current_page',
        readonly=True,
        default=1,
        help='Current page index for units sync'
    )

    # Warehouses pagination fields
    yonsuite_warehouses_current_page = fields.Integer(
        string='Warehouses Current Page',
        config_parameter='yonsuite_integration.warehouses_current_page',
        readonly=True,
        default=1,
        help='Current page index for warehouses sync'
    )

    # Carriers pagination fields
    yonsuite_carriers_current_page = fields.Integer(
        string='Carriers Current Page',
        config_parameter='yonsuite_integration.carriers_current_page',
        readonly=True,
        default=1,
        help='Current page index for carriers sync'
    )

    def action_get_access_token(self):
        self.env['yonsuite.api'].get_access_token()

    @api.model
    def get_access_token_if_needed(self):
        """
        Lấy access token mới nếu cần thiết (được gọi bởi cron job)
        """
        # Lấy thông tin cấu hình
        base_url = self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.base_url')
        app_key = self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.app_key')
        app_secret = self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.app_secret')
        token_expire_time = self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.token_expire_time')

        if not all([base_url, app_key, app_secret]):
            return False

        if token_expire_time:
            expire_time = fields.Datetime.from_string(token_expire_time)
            if expire_time > (fields.Datetime.now() + relativedelta(minutes=10)):
                return False

        try:
            self.env['yonsuite.api'].get_access_token()
            return True
        except Exception as e:
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error("Failed to refresh YonSuite access token: %s", str(e))
            return False

    def action_sync_orders_pagination(self):
        """
        Sync orders with pagination
        """
        try:
            synced_count = self.env['yonsuite.api'].sync_orders_with_pagination()
            return synced_count
        except Exception as e:
            _logger.error("Failed to sync orders with pagination: %s", str(e))
            return 0

    def action_reset_orders_pagination(self):
        """
        Reset orders pagination to page 1
        """
        config_parameter = self.env['ir.config_parameter'].sudo()
        config_parameter.set_param('yonsuite_integration.orders_current_page', '1')
        _logger.info("Orders pagination reset to page 1")
