from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time
from datetime import datetime
import json

_logger = logging.getLogger(__name__)

# Fields cần convert timestamp sang Datetime
CAMPAIGN_DATETIME_FIELDS = ['create_time', 'modify_time']
# Fields cần convert array sang Text
CAMPAIGN_LIST_TO_STRING_FIELDS = ['special_industries']

# Selection options for type fields
OBJECTIVE_TYPE_SELECTION = [
    ('APP_PROMOTION', 'App Promotion'),
    ('WEB_CONVERSIONS', 'Web Conversions'),
    ('REACH', 'Reach'),
    ('TRAFFIC', 'Traffic'),
    ('VIDEO_VIEWS', 'Video Views'),
    ('PRODUCT_SALES', 'Product Sales'),
    ('ENGAGEMENT', 'Engagement'),
    ('LEAD_GENERATION', 'Lead Generation'),
    ('RF_REACH', 'RF Reach'),
    ('TOPVIEW_REACH', 'Topview Reach'),
    ('OTHER', 'Other')  # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

APP_PROMOTION_TYPE_SELECTION = [
    ('APP_INSTALL', 'App Install'),
    ('APP_RETARGETING', 'App Retargeting'),
    ('APP_PREREGISTRATION', 'App Preregistration'),
    ('APP_POSTS_PROMOTION', 'App Posts Promotion'),
    ('UNSET', 'Unset'), # Debug
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]
CAMPAIGN_TYPE_SELECTION = [
    ('REGULAR_CAMPAIGN', 'Regular Campaign'),
    ('IOS14_CAMPAIGN', 'IOS14 Campaign'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

BID_ALIGN_TYPE_SELECTION = [
    ('SAND', 'San'),
    ('SKAN', 'SKAN'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

RF_CAMPAIGN_TYPE_SELECTION = [
    ('STANDARD', 'Standard'),
    ('PULSE', 'Pulse'),
    ('TOPVIEW', 'Topview'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

BID_TYPE_SELECTION = [
    ('BID_TYPE_NO_BID', 'No Bid'),
    ('BID_TYPE_CUSTOM', 'Custom'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

DEEP_BID_TYPE_SELECTION = [
    ('DEFAULT', 'Default'),
    ('MIN', 'Min'),
    ('PACING', 'Pacing'),
    ('VO_MIN_ROAS', 'VO Min ROAS'),
    ('VO_HIGHEST_VALUE', 'VO Highest Value'),
    ('AEO', 'AEO'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

SALES_DESTINATION_SELECTION = [
    ('TIKTOK_SHOP', 'Google App Store'),
    ('WEBSITE', 'App Store'),
    ('APP', 'App'),
    ('WEB_AND_APP', 'Web and App'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

# Enum values: INVALID, UNSET, ON, OFF.
CAMPAIGN_APP_PROFILE_PAGE_STATE_SELECTION = [
    ('INVALID', 'Invalid'),
    ('UNSET', 'Unset'),
    ('ON', 'On'),
    ('OFF', 'Off'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

campaign_product_source_SELECTION = [
    ('CATALOG', 'Catalog'),
    ('STORE', 'TikTok Shop, or TikTok Showcase'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

optimization_goal_SELECTION = [
    ('CLICK', 'Click'),
    ('CONVERT', 'Convert'),
    ('INSTALL', 'Install'),
    ('IN_APP_EVENT', 'In App Event'),
    ('SHOW', 'Show'),
    ('REACH', 'Reach'),
    ('LEAD_GENERATION', 'Lead Generation'),
    ('CONVERSATION', 'Conversation'),
    ('FOLLOWERS', 'Followers'),
    ('PAGE_VISIT', 'Page Visit'),
    ('VALUE', 'Value'),
    ('AUTOMATIC_VALUE_OPTIMIZATION', 'Automatic Value Optimization'),
    ('GMV', 'GMV'),
    ('PURCHASES', 'Purchases'),
    ('INITIATE_CHECKOUTS', 'Initiate Checkouts'),
    ('MT_LIVE_ROOM', 'MT Live Room'),
    ('PRODUCT_CLICK_IN_LIVE', 'Product Click In Live'),
    ('ENGAGED_VIEW', 'Engaged View'),
    ('ENGAGED_VIEW_FIFTEEN', 'Engaged View Fifteen'),
    ('TRAFFIC_LANDING_PAGE_VIEW', 'Traffic Landing Page View'),
    ('DESTINATION_VISIT', 'Destination Visit'),
    ('PREFERRED_LEAD', 'Preferred Lead'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

BUDGET_MODE_SELECTION = [
    ('BUDGET_MODE_INFINITE', 'Unlimited budget'),
    ('BUDGET_MODE_TOTAL', 'Lifetime budget'),
    ('BUDGET_MODE_DAY', 'Daily budget'),
    ('BUDGET_MODE_DYNAMIC_DAILY_BUDGET', 'Dynamic daily budget'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

# ENABLE, DISABLE
operation_status_SELECTION = [
    ('ENABLE', 'Enable'),
    ('DISABLE', 'Disable'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

secondary_status_SELECTION = [
    ('CAMPAIGN_STATUS_DELETE', 'Delete'),
    ('CAMPAIGN_STATUS_ADVERT ISER_AUDIT_DENY', 'Advertiser Audit Deny'),
    ('CAMPAIGN_STATUS_ADVERT ISER_AUDIT', 'Advertiser Audit'),
    ('ADVERTISER_CONTRACT_PENDING', 'Advertiser Contract Pending'),
    ('ADVERTISER_ACCOUNT_PUNISH', 'Advertiser Account Punish'),
    ('CAMPAIGN_STATUS_BUDGET_EXCEED', 'Budget Exceed'),
    ('CAMPAIGN_STATUS_DISABLE', 'Disable'),
    ('CAMPAIGN_STATUS_AWAITING_RELEASE', 'Awaiting Release'),
    ('CAMPAIGN_STATUS_IDENTITY_USED_BY_GMV_MAX_AD', 'Identity Used By GMV Max AD'),
    ('CAMPAIGN_STATUS_ENABLE', 'Enable'),
    ('CAMPAIGN_STATUS_ALL', 'All'),
    ('CAMPAIGN_STATUS_NOT_DELETE', 'Not Delete'),
    ('CAMPAIGN_STATUS_TTS_TT_ASSET_UNAVAILABLE', 'TTS TT Asset Unavailable'),
    ('CAMPAIGN_STATUS_TTS_TT_IDENTITY_UNAVAILABLE', 'TTS TT Identity Unavailable'),
    ('CAMPAIGN_STATUS_TIKTOK_SHOP_UNAVAILABLE', 'TikTok Shop Unavailable'),
    ('CAMPAIGN_STATUS_REVIEW_DISAPPROVED', 'Review Disapproved'),
    ('CAMPAIGN_STATUS_AD_UNAVAILABLE', 'AD Unavailable'),
    ('CAMPAIGN_STATUS_PRODUCT_UNAVAILABLE', 'Product Unavailable'),
    ('CAMPAIGN_STATUS_LIVE_GMV_MAX_AUTHORIZATION_CANCEL', 'Live GMV Max Authorization Cancel'),
    ('CAMPAIGN_STATUS_PRODUCT_GMV_MAX_AUTHORIZATION_CANCEL', 'Product GMV Max Authorization Cancel'),
    ('CAMPAIGN_STATUS_IDENTITY_USED_BY_LIVE_GMV_MAX', 'Identity Used By Live GMV Max'),
    ('CAMPAIGN_STATUS_PRODUCT_USED_BY_PRODUCT_GMV_MAX', 'Product Used By Product GMV Max'),
    ('OTHER', 'Other'), # Nếu không nằm trong danh sách bên trên thì đưa vào đây
]

class TiktokCampaign(models.Model):
    _name = 'tiktok.campaign'
    _description = 'TikTok Campaign'
    _inherit = ['tiktok.business.api.mixin']
    _rec_name = 'campaign_name'
    _order = 'create_time DESC'

    # Fields theo TikTok API response
    advertiser_id = fields.Char(string='Advertiser ID', index=True)
    campaign_id = fields.Char(string='Campaign ID', index=True)
    campaign_system_origin = fields.Char(string='System Origin', index=True)
    create_time = fields.Datetime(string='Created Date', index=True)
    modify_time = fields.Datetime(string='Modified Date')
    objective_type = fields.Selection(selection=OBJECTIVE_TYPE_SELECTION, string='Objective Type', index=True)
    app_promotion_type = fields.Selection(selection=APP_PROMOTION_TYPE_SELECTION, string='App Promotion Type', index=True)
    virtual_objective_type = fields.Char(string='Virtual Objective Type', index=True)  # chưa xác định được selection
    sales_destination = fields.Selection(selection=SALES_DESTINATION_SELECTION, string='Sales Destination', index=True)
    is_search_campaign = fields.Boolean(string='Is Search Campaign', index=True)
    is_smart_performance_campaign = fields.Boolean(string='Is Smart Performance Campaign', index=True)
    campaign_type = fields.Selection(selection=CAMPAIGN_TYPE_SELECTION, string='Campaign Type', index=True)
    app_id = fields.Char(string='App ID')
    is_advanced_dedicated_campaign = fields.Boolean(string='Is Advanced Dedicated Campaign')
    disable_skan_campaign = fields.Boolean(string='Disable SKAN Campaign')
    bid_align_type = fields.Selection(selection=BID_ALIGN_TYPE_SELECTION, string='Bid Align Type')
    campaign_app_profile_page_state = fields.Selection(CAMPAIGN_APP_PROFILE_PAGE_STATE_SELECTION, string='Campaign App Profile Page State')
    rf_campaign_type = fields.Selection(selection=RF_CAMPAIGN_TYPE_SELECTION, string='RF Campaign Type')
    campaign_product_source = fields.Selection(selection=campaign_product_source_SELECTION, string='Campaign Product Source', index=True)
    catalog_enabled = fields.Boolean(string='Catalog Enabled')
    campaign_name = fields.Char(string='Campaign Name', index=True)
    special_industries = fields.Text(string='Special Industries')  # string[] -> Text
    budget_optimize_on = fields.Boolean(string='Budget Optimization')
    bid_type = fields.Selection(selection=BID_TYPE_SELECTION, string='Bid Type', index=True)
    deep_bid_type = fields.Selection(selection=DEEP_BID_TYPE_SELECTION, string='Deep Bid Type', index=True)
    roas_bid = fields.Float(string='ROAS Bid')
    optimization_goal = fields.Selection(selection=optimization_goal_SELECTION, string='Optimization Goal', index=True)
    budget_mode = fields.Selection(selection=BUDGET_MODE_SELECTION, string='Budget Mode', index=True)
    budget = fields.Float(string='Budget')
    rta_id = fields.Char(string='RTA ID')
    rta_bid_enabled = fields.Boolean(string='RTA Bid Enabled')
    rta_product_selection_enabled = fields.Boolean(string='RTA Product Selection')
    operation_status = fields.Selection(selection=operation_status_SELECTION, string='Operation Status', index=True)
    secondary_status = fields.Selection(selection=secondary_status_SELECTION, string='Secondary Status', index=True)
    postback_window_mode = fields.Char(string='Postback Window Mode', index=True)
    is_new_structure = fields.Boolean(string='Is New Structure')
    objective = fields.Char(string='Objective')

    # Trường quan hệ
    odoo_advertiser_id = fields.Many2one('tiktok.advertiser', string='Advertiser', index=True)

    # Raw data for re-check
    raw_payload = fields.Json(string='Raw Payload')

    def _sync_campaigns(self, dict_params, access_token, page_index=1):
        """
        Đồng bộ dữ liệu campaigns từ TikTok Business API
        Args:
            dict_params: dict: params for API
            page_index: int: page index
        Returns:
            None
        """
        campaign_total = 0
        start_time = time.time()
        while True:
            # Gọi API để lấy danh sách campaigns
            dict_params.update({  # Mặc định là max page_size, tăng page_index để lấy phần tiếp theo
                'page': page_index,
                'page_size': 1000,
            })
            
            endpoint = "campaign/get/"
            # Example of correct filtering format:
            # dict_params = {
            #     'advertiser_id': '7130449360583655426', 
            #     'filtering': json.dumps({'campaign_ids': ["1843403545932801", "1843332155273393"]}), 
            #     'page': 1, 
            #     'page_size': 1000
            # }
            campaigns_data = self._call_tiktok_api(endpoint, access_token, method='GET', params=dict_params)
            
            if not campaigns_data:
                _logger.error(f"Tiktok Marketing API {endpoint}: Không có dữ liệu campaigns từ TikTok API")
                break
            
            # Xử lý dữ liệu trả về
            campaigns_list = campaigns_data.get('list', [])
            page_info = campaigns_data.get('page_info', {})


            if not campaigns_list:
                advertiser_id = dict_params.get('advertiser_id')
                _logger.info(f"Tiktok Marketing API {endpoint}: Danh sách campaigns trống -> Advertiser ID: {advertiser_id}")
                break
            
            if campaigns_list:
                # Update campaigns
                campaign_total += len(campaigns_list)
                self._update_campaigns(campaigns_list)

            # Check page_info: Nếu page_index < total_page, tăng page_index để lấy phần tiếp theo
            if page_index < page_info.get('total_page', page_index):
                page_index += 1
            else:
                break
        if campaign_total > 0:
            end_time = time.time()
            _logger.info(f"Tiktok Marketing API {endpoint}: Đã đồng bộ {campaign_total} campaigns -> {end_time - start_time} (s)")

    def _update_campaigns(self, campaigns_list):
        """
        Cập nhật/tạo mới campaigns
        Args:
            campaigns_list: list of campaigns ids
        Returns:
            None
        """
        # Lấy danh sách campaign_ids từ response
        campaign_ids = [camp.get('campaign_id') for camp in campaigns_list]
        # Tìm các campaigns hiện có
        existing_campaigns = self.search_read([('campaign_id', 'in', campaign_ids)], fields=['id', 'campaign_id'])
        existing_campaigns_map = {r['campaign_id']: r['id'] for r in existing_campaigns}

        # Lấy danh sách advertiser_ids từ response
        advertiser_ids = [camp.get('advertiser_id') for camp in campaigns_list]
        # Tìm các advertisers hiện có
        existing_advertisers = self.env['tiktok.advertiser'].with_context(active_test=False).search_read([('advertiser_id', 'in', advertiser_ids)], fields=['id', 'advertiser_id'])
        existing_advertisers_map = {r['advertiser_id']: r['id'] for r in existing_advertisers}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()

        # Duyệt từng dict trong campaigns_list
        for campaign_data in campaigns_list:
            campaign_id = campaign_data.get('campaign_id')
            if not campaign_id:
                continue
            
            # Prepare data using map_fields
            campaign_vals = {
                'raw_payload': campaign_data,
                'odoo_advertiser_id': existing_advertisers_map.get(campaign_data.get('advertiser_id'), False)
            }
            for key, value in campaign_data.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in CAMPAIGN_DATETIME_FIELDS:
                        campaign_vals[field_key] = self._convert_timestamp_to_datetime(value)
                    elif field_key in CAMPAIGN_LIST_TO_STRING_FIELDS:
                        campaign_vals[field_key] = self._convert_array_to_text(value)
                    elif field_key in self._map_field_selection_list():
                        campaign_vals[field_key] = self._set_selection_field(self._map_field_selection_list()[field_key], value)
                    else:
                        campaign_vals[field_key] = value
            
            # Kiểm tra campaign đã tồn tại chưa, nếu có thì update, nếu không thì create
            if campaign_id in existing_campaigns_map:
                update_vals_list.append((existing_campaigns_map[campaign_id], campaign_vals))
            else:
                new_vals_list.append(campaign_vals)
        
        # Tạo campaigns mới
        if new_vals_list:
            self.sudo().create(new_vals_list)
        # Update campaigns
        for campaign_id, vals in update_vals_list:
            campaign = self.browse(campaign_id)
            campaign.sudo().write(vals)

    def action_sync_campaigns(self):
        """
        Đồng bộ các Campaigns được chọn
        Returns: display notification
        """
        self = self.filtered(lambda c: c.advertiser_id and c.campaign_id)
        for advertiser in self.odoo_advertiser_id:
            # lấy access token từ business account của advertiser, có thể có nhiều access token trong nhiều business accounts
            access_token_list = advertiser.business_account_ids.sudo().mapped('access_token')
            for access_token in access_token_list:
                if not access_token:
                    continue
                campaign_ids = self.mapped('campaign_id')

                # Call api max 100 campaigns 1 lần
                while campaign_ids:
                    # Chuẩn bị params - đảm bảo campaign_ids là list các string
                    dict_params = {
                        'advertiser_id': advertiser.advertiser_id,
                        'filtering': json.dumps({
                            'campaign_ids': campaign_ids[:100]
                        })
                    }
                    # Gọi method sync
                    self._sync_campaigns(dict_params, access_token)
                    # Cập nhật lại campaign_ids cần call
                    campaign_ids = campaign_ids[100:]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced %s campaigns successfully!') % len(self),
                'type': 'success',
            }
        }

    def _map_fields(self):
        """Map TikTok API fields to Odoo model fields
        Return dict {
            response_key: odoo_field_name,
            ...
        }
        """
        return {
            'advertiser_id': 'advertiser_id',
            'campaign_id': 'campaign_id',
            'campaign_system_origin': 'campaign_system_origin',
            'create_time': 'create_time',
            'modify_time': 'modify_time',
            'objective_type': 'objective_type',
            'app_promotion_type': 'app_promotion_type',
            'virtual_objective_type': 'virtual_objective_type',
            'sales_destination': 'sales_destination',
            'is_search_campaign': 'is_search_campaign',
            'is_smart_performance_campaign': 'is_smart_performance_campaign',
            'campaign_type': 'campaign_type',
            'app_id': 'app_id',
            'is_advanced_dedicated_campaign': 'is_advanced_dedicated_campaign',
            'disable_skan_campaign': 'disable_skan_campaign',
            'bid_align_type': 'bid_align_type',
            'campaign_app_profile_page_state': 'campaign_app_profile_page_state',
            'rf_campaign_type': 'rf_campaign_type',
            'campaign_product_source': 'campaign_product_source',
            'catalog_enabled': 'catalog_enabled',
            'campaign_name': 'campaign_name',
            'special_industries': 'special_industries',
            'budget_optimize_on': 'budget_optimize_on',
            'bid_type': 'bid_type',
            'deep_bid_type': 'deep_bid_type',
            'roas_bid': 'roas_bid',
            'optimization_goal': 'optimization_goal',
            'budget_mode': 'budget_mode',
            'budget': 'budget',
            'rta_id': 'rta_id',
            'rta_bid_enabled': 'rta_bid_enabled',
            'rta_product_selection_enabled': 'rta_product_selection_enabled',
            'operation_status': 'operation_status',
            'secondary_status': 'secondary_status',
            'postback_window_mode': 'postback_window_mode',
            'is_new_structure': 'is_new_structure',
            'objective': 'objective',
        }

    def _map_field_selection_list(self):
        """Map TikTok API fields to Odoo model fields
        Return dict {
            odoo_field_name: list of tuple (key, value)
            ...
        }
        """
        return {
            'objective_type': OBJECTIVE_TYPE_SELECTION,
            'app_promotion_type': APP_PROMOTION_TYPE_SELECTION,
            'campaign_type': CAMPAIGN_TYPE_SELECTION,
            'bid_align_type': BID_ALIGN_TYPE_SELECTION,
            'rf_campaign_type': RF_CAMPAIGN_TYPE_SELECTION,
            'bid_type': BID_TYPE_SELECTION,
            'deep_bid_type': DEEP_BID_TYPE_SELECTION,
            'sales_destination': SALES_DESTINATION_SELECTION,
            'campaign_app_profile_page_state': CAMPAIGN_APP_PROFILE_PAGE_STATE_SELECTION,
            'campaign_product_source': campaign_product_source_SELECTION,
            'optimization_goal': optimization_goal_SELECTION,
            'budget_mode': BUDGET_MODE_SELECTION,
            'operation_status': operation_status_SELECTION,
            'secondary_status': secondary_status_SELECTION,
        }

    def _set_selection_field(self, selection_list, value):
        """
        Xác định giá trị của field selection
        Args:
            selection_list: list of tuple (key, value)
            value: value of field
        Returns:
            value if value in selection_list, otherwise 'OTHER' or None
        """
        if not value:
            return None
        if value in [item[0] for item in selection_list]:
            return value
        else:
            return 'OTHER'

    def action_sync_ad_groups(self):
        """Đồng bộ ad groups cho các campaigns được chọn"""
        for advertiser in self.odoo_advertiser_id:
            campaign_ids = self.filtered(lambda c: c.odoo_advertiser_id == advertiser).mapped('campaign_id')
            while campaign_ids:
                advertiser._sync_ad_groups(campaign_ids=campaign_ids[:100])
                campaign_ids = campaign_ids[100:]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced ad groups successfully!'),
                'type': 'success',
            }
        }

    def action_sync_ads(self):
        """Đồng bộ ads cho các ad groups được chọn"""
        for advertiser in self.odoo_advertiser_id:
            campaign_ids = self.filtered(lambda c: c.odoo_advertiser_id == advertiser).mapped('campaign_id')
            while campaign_ids:
                advertiser._sync_ads(campaign_ids=campaign_ids[:100])
                campaign_ids = campaign_ids[100:]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced ads successfully!'),
                'type': 'success',
            }
        }