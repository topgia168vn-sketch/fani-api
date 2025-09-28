from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time
from datetime import datetime
import json

_logger = logging.getLogger(__name__)

# Fields cần convert timestamp sang Datetime
AD_GROUP_DATETIME_FIELDS = ['create_time', 'modify_time', 'schedule_start_time', 'schedule_end_time']
# Fields cần convert sang Text
AD_GROUP_LIST_TO_STRING_FIELDS = [
    'app_config',
    'placements',
    'tiktok_subplacements',
    'search_keywords',
    'blocked_pangle_app_ids',
    'audience_rule',
    'included_custom_actions',
    'excluded_custom_actions',
    'location_ids',
    'zipcode_ids',
    'languages',
    'age_groups',
    'household_income',
    'audience_ids',
    'excluded_audience_ids',
    'interest_category_ids',
    'interest_keyword_ids',
    'purchase_intention_keyword_ids',
    'actions',
    'included_pangle_audience_package_ids',
    'excluded_pangle_audience_package_ids',
    'operating_systems',
    'device_model_ids',
    'network_types',
    'carrier_ids',
    'isp_ids',
    'device_price_ranges',
    'contextual_tag_ids',
    'category_exclusion_ids',
    'topview_reach_range',
    'schedule_infos'
]


class TiktokAdGroup(models.Model):
    _name = 'tiktok.ad_group'
    _description = 'TikTok Ad Group'
    _inherit = ['tiktok.business.api.mixin']
    _rec_name = 'adgroup_name'
    _order = 'create_time DESC'

    # Fields theo TikTok API response - Sắp xếp theo thứ tự trong fields.py (dòng 2-144)
    advertiser_id = fields.Char(string='Advertiser ID', index=True, help='Advertiser ID')
    campaign_id = fields.Char(string='Campaign ID', index=True, help='Campaign ID')
    campaign_name = fields.Char(string='Campaign Name', index=True, help='Campaign Name')
    campaign_system_origin = fields.Char(string='Campaign System Origin', help='Campaign System Origin')
    is_smart_performance_campaign = fields.Boolean(string='Is Smart Performance Campaign', help='Is Smart Performance Campaign')
    adgroup_id = fields.Char(string='Ad Group ID', index=True, help='Ad Group ID')
    adgroup_name = fields.Char(string='Ad Group Name', index=True, help='Ad Group Name')
    create_time = fields.Datetime(string='Created Date', index=True, help='Created Date')
    modify_time = fields.Datetime(string='Modified Date', help='Modified Date')
    shopping_ads_type = fields.Char(string='Shopping Ads Type', help='Shopping Ads Type')
    identity_id = fields.Char(string='Identity ID', help='Identity ID')
    identity_type = fields.Char(string='Identity Type', help='Identity Type')
    identity_authorized_bc_id = fields.Char(string='Identity Authorized BC ID', help='Identity Authorized BC ID')
    product_source = fields.Char(string='Product Source', help='Product Source')
    catalog_id = fields.Char(string='Catalog ID', help='Catalog ID')
    catalog_authorized_bc_id = fields.Char(string='Catalog Authorized BC ID', help='Catalog Authorized BC ID')
    store_id = fields.Char(string='Store ID', help='Store ID')
    store_authorized_bc_id = fields.Char(string='Store Authorized BC ID', help='Store Authorized BC ID')
    promotion_type = fields.Char(string='Promotion Type', help='Promotion Type')
    promotion_target_type = fields.Char(string='Promotion Target Type', help='Promotion Target Type')
    messaging_app_type = fields.Char(string='Messaging App Type', help='Messaging App Type')
    messaging_app_account_id = fields.Char(string='Messaging App Account ID', help='Messaging App Account ID')
    phone_region_code = fields.Char(string='Phone Region Code', help='Phone Region Code')
    phone_region_calling_code = fields.Char(string='Phone Region Calling Code', help='Phone Region Calling Code')
    phone_number = fields.Char(string='Phone Number', help='Phone Number')
    promotion_website_type = fields.Char(string='Promotion Website Type', help='Promotion Website Type')
    app_id = fields.Char(string='App ID', help='App ID')
    app_type = fields.Char(string='App Type', help='App Type')
    app_download_url = fields.Char(string='App Download URL', help='App Download URL')
    pixel_id = fields.Char(string='Pixel ID', help='Pixel ID')
    optimization_event = fields.Char(string='Optimization Event', help='Optimization Event')
    custom_conversion_id = fields.Char(string='Custom Conversion ID', help='Custom Conversion ID')
    app_config = fields.Text(string='App Config', help='App Config')
    deep_funnel_optimization_status = fields.Char(string='Deep Funnel Optimization Status', help='Deep Funnel Optimization Status')
    deep_funnel_event_source = fields.Char(string='Deep Funnel Event Source', help='Deep Funnel Event Source')
    deep_funnel_event_source_id = fields.Char(string='Deep Funnel Event Source ID', help='Deep Funnel Event Source ID')
    deep_funnel_optimization_event = fields.Char(string='Deep Funnel Optimization Event', help='Deep Funnel Optimization Event')
    placement_type = fields.Char(string='Placement Type', help='Placement Type')
    placements = fields.Text(string='Placements', help='Placements')
    tiktok_subplacements = fields.Text(string='TikTok Subplacements', help='TikTok Subplacements')
    search_result_enabled = fields.Boolean(string='Search Result Enabled', help='Search Result Enabled')
    automated_keywords_enabled = fields.Boolean(string='Automated Keywords Enabled', help='Automated Keywords Enabled')
    search_keywords = fields.Text(string='Search Keywords', help='Search Keywords')
    comment_disabled = fields.Boolean(string='Comment Disabled', help='Comment Disabled')
    video_download_disabled = fields.Boolean(string='Video Download Disabled', help='Video Download Disabled')
    share_disabled = fields.Boolean(string='Share Disabled', help='Share Disabled')
    blocked_pangle_app_ids = fields.Text(string='Blocked Pangle App IDs', help='Blocked Pangle App IDs')
    audience_type = fields.Char(string='Audience Type', help='Audience Type')
    audience_rule = fields.Text(string='Audience Rule', help='Audience Rule')
    shopping_ads_retargeting_type = fields.Char(string='Shopping Ads Retargeting Type', help='Shopping Ads Retargeting Type')
    shopping_ads_retargeting_actions_days = fields.Float(string='Shopping Ads Retargeting Actions Days', help='Shopping Ads Retargeting Actions Days')
    included_custom_actions = fields.Text(string='Included Custom Actions', help='Included Custom Actions')
    excluded_custom_actions = fields.Text(string='Excluded Custom Actions', help='Excluded Custom Actions')
    shopping_ads_retargeting_custom_audience_relation = fields.Char(string='Shopping Ads Retargeting Custom Audience Relation', help='Shopping Ads Retargeting Custom Audience Relation')
    location_ids = fields.Text(string='Location IDs', help='Location IDs')
    zipcode_ids = fields.Text(string='Zipcode IDs', help='Zipcode IDs')
    languages = fields.Text(string='Languages', help='Languages')
    gender = fields.Char(string='Gender', help='Gender')
    age_groups = fields.Text(string='Age Groups', help='Age Groups')
    spending_power = fields.Char(string='Spending Power', help='Spending Power')
    household_income = fields.Text(string='Household Income', help='Household Income')
    audience_ids = fields.Text(string='Audience IDs', help='Audience IDs')
    smart_audience_enabled = fields.Boolean(string='Smart Audience Enabled', help='Smart Audience Enabled')
    excluded_audience_ids = fields.Text(string='Excluded Audience IDs', help='Excluded Audience IDs')
    interest_category_ids = fields.Text(string='Interest Category IDs', help='Interest Category IDs')
    interest_keyword_ids = fields.Text(string='Interest Keyword IDs', help='Interest Keyword IDs')
    purchase_intention_keyword_ids = fields.Text(string='Purchase Intention Keyword IDs', help='Purchase Intention Keyword IDs')
    actions = fields.Text(string='Actions', help='Actions')
    smart_interest_behavior_enabled = fields.Boolean(string='Smart Interest Behavior Enabled', help='Smart Interest Behavior Enabled')
    included_pangle_audience_package_ids = fields.Text(string='Included Pangle Audience Package IDs', help='Included Pangle Audience Package IDs')
    excluded_pangle_audience_package_ids = fields.Text(string='Excluded Pangle Audience Package IDs', help='Excluded Pangle Audience Package IDs')
    operating_systems = fields.Text(string='Operating Systems', help='Operating Systems')
    min_android_version = fields.Char(string='Min Android Version', help='Min Android Version')
    ios14_targeting = fields.Char(string='iOS14 Targeting', help='iOS14 Targeting')
    min_ios_version = fields.Char(string='Min iOS Version', help='Min iOS Version')
    ios14_quota_type = fields.Char(string='iOS14 Quota Type', help='iOS14 Quota Type')
    device_model_ids = fields.Text(string='Device Model IDs', help='Device Model IDs')
    network_types = fields.Text(string='Network Types', help='Network Types')
    carrier_ids = fields.Text(string='Carrier IDs', help='Carrier IDs')
    isp_ids = fields.Text(string='ISP IDs', help='ISP IDs')
    device_price_ranges = fields.Text(string='Device Price Ranges', help='Device Price Ranges')
    saved_audience_id = fields.Char(string='Saved Audience ID', help='Saved Audience ID')
    contextual_tag_ids = fields.Text(string='Contextual Tag IDs', help='Contextual Tag IDs')
    brand_safety_type = fields.Char(string='Brand Safety Type', help='Brand Safety Type')
    brand_safety_partner = fields.Char(string='Brand Safety Partner', help='Brand Safety Partner')
    inventory_filter_enabled = fields.Boolean(string='Inventory Filter Enabled', help='Inventory Filter Enabled')
    category_exclusion_ids = fields.Text(string='Category Exclusion IDs', help='Category Exclusion IDs')
    vertical_sensitivity_id = fields.Char(string='Vertical Sensitivity ID', help='Vertical Sensitivity ID')
    budget_mode = fields.Char(string='Budget Mode', index=True, help='Budget Mode')
    budget = fields.Float(string='Budget', help='Budget')
    scheduled_budget = fields.Float(string='Scheduled Budget', help='Scheduled Budget')
    schedule_type = fields.Char(string='Schedule Type', help='Schedule Type')
    schedule_start_time = fields.Datetime(string='Schedule Start Time', help='Schedule Start Time')
    schedule_end_time = fields.Datetime(string='Schedule End Time', help='Schedule End Time')
    predict_impression = fields.Float(string='Predict Impression', help='Predict Impression')
    topview_reach_range = fields.Text(string='Topview Reach Range', help='Topview Reach Range')
    pre_discount_cpm = fields.Float(string='Pre Discount CPM', help='Pre Discount CPM')
    cpm = fields.Float(string='CPM', help='CPM')
    discount_type = fields.Char(string='Discount Type', help='Discount Type')
    discount_amount = fields.Float(string='Discount Amount', help='Discount Amount')
    discount_percentage = fields.Float(string='Discount Percentage', help='Discount Percentage')
    pre_discount_budget = fields.Float(string='Pre Discount Budget', help='Pre Discount Budget')
    schedule_infos = fields.Text(string='Schedule Infos', help='Schedule Infos')
    delivery_mode = fields.Char(string='Delivery Mode', help='Delivery Mode')
    dayparting = fields.Char(string='Dayparting', help='Dayparting')
    optimization_goal = fields.Char(string='Optimization Goal', index=True, help='Optimization Goal')
    secondary_optimization_event = fields.Char(string='Secondary Optimization Event', help='Secondary Optimization Event')
    message_event_set_id = fields.Char(string='Message Event Set ID', help='Message Event Set ID')
    frequency = fields.Float(string='Frequency', help='Frequency')
    frequency_schedule = fields.Float(string='Frequency Schedule', help='Frequency Schedule')
    bid_type = fields.Char(string='Bid Type', index=True, help='Bid Type')
    bid_price = fields.Float(string='Bid Price', help='Bid Price')
    conversion_bid_price = fields.Float(string='Conversion Bid Price', help='Conversion Bid Price')
    deep_bid_type = fields.Char(string='Deep Bid Type', index=True, help='Deep Bid Type')
    roas_bid = fields.Float(string='ROAS Bid', help='ROAS Bid')
    vbo_window = fields.Char(string='VBO Window', help='VBO Window')
    bid_display_mode = fields.Char(string='Bid Display Mode', help='Bid Display Mode')
    deep_cpa_bid = fields.Float(string='Deep CPA Bid', help='Deep CPA Bid')
    cpv_video_duration = fields.Char(string='CPV Video Duration', help='CPV Video Duration')
    next_day_retention = fields.Float(string='Next Day Retention', help='Next Day Retention')
    click_attribution_window = fields.Char(string='Click Attribution Window', help='Click Attribution Window')
    engaged_view_attribution_window = fields.Char(string='Engaged View Attribution Window', help='Engaged View Attribution Window')
    view_attribution_window = fields.Char(string='View Attribution Window', help='View Attribution Window')
    attribution_event_count = fields.Char(string='Attribution Event Count', help='Attribution Event Count')
    billing_event = fields.Char(string='Billing Event', help='Billing Event')
    pacing = fields.Char(string='Pacing', help='Pacing')
    operation_status = fields.Char(string='Operation Status', index=True, help='Operation Status')
    secondary_status = fields.Char(string='Secondary Status', index=True, help='Secondary Status')
    statistic_type = fields.Char(string='Statistic Type', help='Statistic Type')
    is_hfss = fields.Boolean(string='Is HFSS', help='Is HFSS')
    creative_material_mode = fields.Char(string='Creative Material Mode', help='Creative Material Mode')
    adgroup_app_profile_page_state = fields.Char(string='Ad Group App Profile Page State', help='Ad Group App Profile Page State')
    feed_type = fields.Char(string='Feed Type', help='Feed Type')
    rf_purchased_type = fields.Char(string='RF Purchased Type', help='RF Purchased Type')
    purchased_impression = fields.Float(string='Purchased Impression', help='Purchased Impression')
    purchased_reach = fields.Float(string='Purchased Reach', help='Purchased Reach')
    rf_estimated_cpr = fields.Float(string='RF Estimated CPR', help='RF Estimated CPR')
    rf_estimated_frequency = fields.Float(string='RF Estimated Frequency', help='RF Estimated Frequency')
    split_test_group_id = fields.Char(string='Split Test Group ID', help='Split Test Group ID')
    split_test_status = fields.Char(string='Split Test Status', help='Split Test Status')
    is_new_structure = fields.Boolean(string='Is New Structure', help='Is New Structure')
    skip_learning_phase = fields.Boolean(string='Skip Learning Phase', help='Skip Learning Phase')

    # Trường quan hệ
    odoo_campaign_id = fields.Many2one('tiktok.campaign', string='Campaign', index=True)
    odoo_advertiser_id = fields.Many2one(related='odoo_campaign_id.odoo_advertiser_id', store=True, index=True)

    # Raw data for re-check
    raw_payload = fields.Json(string='Raw Payload')

    def _sync_ad_groups(self, dict_params, access_token, page_index=1):
        """
        Đồng bộ dữ liệu ad groups từ TikTok Business API
        Args:
            dict_params: dict: params for API
                - filtering:
                    - adgroup_ids: list of adgroup ids. max 100
                    - campaign_ids: list of campaign ids. max 100
                    - creation_filter_start_time. format YYYY-MM-DD HH:MM:SS (UTC time zone)
                    - creation_filter_end_time. format YYYY-MM-DD HH:MM:SS (UTC time zone)
            access_token: str: access token
            page_index: int: page index
        Returns:
            None
        """
        ad_group_total = 0
        start_time = time.time()
        while True:
            # Gọi API để lấy danh sách ad groups
            dict_params.update({  # Mặc định là max page_size, tăng page_index để lấy phần tiếp theo
                'page': page_index,
                'page_size': 1000,
            })
            
            endpoint = "adgroup/get/"
            ad_groups_data = self._call_tiktok_api(endpoint, access_token, method='GET', params=dict_params)
            
            if not ad_groups_data:
                _logger.error(f"Tiktok Marketing API {endpoint}: Không có dữ liệu ad groups từ TikTok API")
                break
            
            # Xử lý dữ liệu trả về
            ad_groups_list = ad_groups_data.get('list', [])
            page_info = ad_groups_data.get('page_info', {})

            if not ad_groups_list:
                advertiser_id = dict_params.get('advertiser_id')
                _logger.info(f"Tiktok Marketing API {endpoint}: Danh sách ad groups trống -> Advertiser ID: {advertiser_id}")
                break
            
            if ad_groups_list:
                # Update ad groups
                ad_group_total += len(ad_groups_list)
                self._update_ad_groups(ad_groups_list)

            # Check page_info: Nếu page_index < total_page, tăng page_index để lấy phần tiếp theo
            if page_index < page_info.get('total_page', page_index):
                page_index += 1
            else:
                break
        if ad_group_total > 0:
            end_time = time.time()
            _logger.info(f"Tiktok Marketing API {endpoint}: Đã đồng bộ {ad_group_total} ad groups -> {end_time - start_time} (s)")

    def _update_ad_groups(self, ad_groups_list):
        """
        Cập nhật/tạo mới ad groups
        Args:
            ad_groups_list: list of ad groups data
        Returns:
            None
        """
        # Lấy danh sách adgroup_ids từ response
        adgroup_ids = [ad_group.get('adgroup_id') for ad_group in ad_groups_list]
        # Tìm các ad groups hiện có
        existing_ad_groups = self.search_read([('adgroup_id', 'in', adgroup_ids)], fields=['id', 'adgroup_id'])
        existing_ad_groups_map = {r['adgroup_id']: r['id'] for r in existing_ad_groups}

        # Lấy danh sách campaign_ids từ response
        campaign_ids = [ad_group.get('campaign_id') for ad_group in ad_groups_list]
        # Tìm các campaigns hiện có
        existing_campaigns = self.env['tiktok.campaign'].with_context(active_test=False).search_read([('campaign_id', 'in', campaign_ids)], fields=['id', 'campaign_id'])
        existing_campaigns_map = {r['campaign_id']: r['id'] for r in existing_campaigns}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()

        # Duyệt từng dict trong ad_groups_list
        for ad_group_data in ad_groups_list:
            adgroup_id = ad_group_data.get('adgroup_id')
            if not adgroup_id:
                continue
            
            # Prepare data using map_fields
            ad_group_vals = {
                'raw_payload': ad_group_data,
                'odoo_campaign_id': existing_campaigns_map.get(ad_group_data.get('campaign_id'), False)
            }
            for key, value in ad_group_data.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in AD_GROUP_DATETIME_FIELDS:
                        ad_group_vals[field_key] = self._convert_timestamp_to_datetime(value)
                    elif field_key in AD_GROUP_LIST_TO_STRING_FIELDS:
                        ad_group_vals[field_key] = self._convert_array_to_text(value)
                    else:
                        ad_group_vals[field_key] = value
            
            # Kiểm tra ad group đã tồn tại chưa, nếu có thì update, nếu không thì create
            if adgroup_id in existing_ad_groups_map:
                update_vals_list.append((existing_ad_groups_map[adgroup_id], ad_group_vals))
            else:
                new_vals_list.append(ad_group_vals)
        
        # Tạo ad groups mới
        if new_vals_list:
            self.sudo().create(new_vals_list)
        # Update ad groups
        for ad_group_id, vals in update_vals_list:
            ad_group = self.browse(ad_group_id)
            ad_group.sudo().write(vals)

    def action_sync_ad_groups(self):
        """Đồng bộ ad groups cho các campaigns được chọn"""
        for advertiser in self.odoo_advertiser_id:
            adgroup_ids = self.filtered(lambda c: c.odoo_advertiser_id == advertiser).mapped('adgroup_id')
            while adgroup_ids:
                advertiser._sync_ad_groups(adgroup_ids=adgroup_ids[:100])
                adgroup_ids = adgroup_ids[100:]
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
            ad_group_ids = self.filtered(lambda c: c.odoo_advertiser_id == advertiser).mapped('adgroup_id')
            while ad_group_ids:
                advertiser._sync_ads(adgroup_ids=ad_group_ids[:100])
                ad_group_ids = ad_group_ids[100:]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced ads successfully!'),
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
            'campaign_name': 'campaign_name',
            'campaign_system_origin': 'campaign_system_origin',
            'is_smart_performance_campaign': 'is_smart_performance_campaign',
            'adgroup_id': 'adgroup_id',
            'adgroup_name': 'adgroup_name',
            'create_time': 'create_time',
            'modify_time': 'modify_time',
            'shopping_ads_type': 'shopping_ads_type',
            'identity_id': 'identity_id',
            'identity_type': 'identity_type',
            'identity_authorized_bc_id': 'identity_authorized_bc_id',
            'product_source': 'product_source',
            'catalog_id': 'catalog_id',
            'catalog_authorized_bc_id': 'catalog_authorized_bc_id',
            'store_id': 'store_id',
            'store_authorized_bc_id': 'store_authorized_bc_id',
            'promotion_type': 'promotion_type',
            'promotion_target_type': 'promotion_target_type',
            'messaging_app_type': 'messaging_app_type',
            'messaging_app_account_id': 'messaging_app_account_id',
            'phone_region_code': 'phone_region_code',
            'phone_region_calling_code': 'phone_region_calling_code',
            'phone_number': 'phone_number',
            'promotion_website_type': 'promotion_website_type',
            'app_id': 'app_id',
            'app_type': 'app_type',
            'app_download_url': 'app_download_url',
            'pixel_id': 'pixel_id',
            'optimization_event': 'optimization_event',
            'custom_conversion_id': 'custom_conversion_id',
            'app_config': 'app_config',
            'deep_funnel_optimization_status': 'deep_funnel_optimization_status',
            'deep_funnel_event_source': 'deep_funnel_event_source',
            'deep_funnel_event_source_id': 'deep_funnel_event_source_id',
            'deep_funnel_optimization_event': 'deep_funnel_optimization_event',
            'placement_type': 'placement_type',
            'placements': 'placements',
            'tiktok_subplacements': 'tiktok_subplacements',
            'search_result_enabled': 'search_result_enabled',
            'automated_keywords_enabled': 'automated_keywords_enabled',
            'search_keywords': 'search_keywords',
            'comment_disabled': 'comment_disabled',
            'video_download_disabled': 'video_download_disabled',
            'share_disabled': 'share_disabled',
            'blocked_pangle_app_ids': 'blocked_pangle_app_ids',
            'audience_type': 'audience_type',
            'audience_rule': 'audience_rule',
            'shopping_ads_retargeting_type': 'shopping_ads_retargeting_type',
            'shopping_ads_retargeting_actions_days': 'shopping_ads_retargeting_actions_days',
            'included_custom_actions': 'included_custom_actions',
            'excluded_custom_actions': 'excluded_custom_actions',
            'shopping_ads_retargeting_custom_audience_relation': 'shopping_ads_retargeting_custom_audience_relation',
            'location_ids': 'location_ids',
            'zipcode_ids': 'zipcode_ids',
            'languages': 'languages',
            'gender': 'gender',
            'age_groups': 'age_groups',
            'spending_power': 'spending_power',
            'household_income': 'household_income',
            'audience_ids': 'audience_ids',
            'smart_audience_enabled': 'smart_audience_enabled',
            'excluded_audience_ids': 'excluded_audience_ids',
            'interest_category_ids': 'interest_category_ids',
            'interest_keyword_ids': 'interest_keyword_ids',
            'purchase_intention_keyword_ids': 'purchase_intention_keyword_ids',
            'actions': 'actions',
            'smart_interest_behavior_enabled': 'smart_interest_behavior_enabled',
            'included_pangle_audience_package_ids': 'included_pangle_audience_package_ids',
            'excluded_pangle_audience_package_ids': 'excluded_pangle_audience_package_ids',
            'operating_systems': 'operating_systems',
            'min_android_version': 'min_android_version',
            'ios14_targeting': 'ios14_targeting',
            'min_ios_version': 'min_ios_version',
            'ios14_quota_type': 'ios14_quota_type',
            'device_model_ids': 'device_model_ids',
            'network_types': 'network_types',
            'carrier_ids': 'carrier_ids',
            'isp_ids': 'isp_ids',
            'device_price_ranges': 'device_price_ranges',
            'saved_audience_id': 'saved_audience_id',
            'contextual_tag_ids': 'contextual_tag_ids',
            'brand_safety_type': 'brand_safety_type',
            'brand_safety_partner': 'brand_safety_partner',
            'inventory_filter_enabled': 'inventory_filter_enabled',
            'category_exclusion_ids': 'category_exclusion_ids',
            'vertical_sensitivity_id': 'vertical_sensitivity_id',
            'budget_mode': 'budget_mode',
            'budget': 'budget',
            'scheduled_budget': 'scheduled_budget',
            'schedule_type': 'schedule_type',
            'schedule_start_time': 'schedule_start_time',
            'schedule_end_time': 'schedule_end_time',
            'predict_impression': 'predict_impression',
            'topview_reach_range': 'topview_reach_range',
            'pre_discount_cpm': 'pre_discount_cpm',
            'cpm': 'cpm',
            'discount_type': 'discount_type',
            'discount_amount': 'discount_amount',
            'discount_percentage': 'discount_percentage',
            'pre_discount_budget': 'pre_discount_budget',
            'schedule_infos': 'schedule_infos',
            'delivery_mode': 'delivery_mode',
            'dayparting': 'dayparting',
            'optimization_goal': 'optimization_goal',
            'secondary_optimization_event': 'secondary_optimization_event',
            'message_event_set_id': 'message_event_set_id',
            'frequency': 'frequency',
            'frequency_schedule': 'frequency_schedule',
            'bid_type': 'bid_type',
            'bid_price': 'bid_price',
            'conversion_bid_price': 'conversion_bid_price',
            'deep_bid_type': 'deep_bid_type',
            'roas_bid': 'roas_bid',
            'vbo_window': 'vbo_window',
            'bid_display_mode': 'bid_display_mode',
            'deep_cpa_bid': 'deep_cpa_bid',
            'cpv_video_duration': 'cpv_video_duration',
            'next_day_retention': 'next_day_retention',
            'click_attribution_window': 'click_attribution_window',
            'engaged_view_attribution_window': 'engaged_view_attribution_window',
            'view_attribution_window': 'view_attribution_window',
            'attribution_event_count': 'attribution_event_count',
            'billing_event': 'billing_event',
            'pacing': 'pacing',
            'operation_status': 'operation_status',
            'secondary_status': 'secondary_status',
            'statistic_type': 'statistic_type',
            'is_hfss': 'is_hfss',
            'creative_material_mode': 'creative_material_mode',
            'adgroup_app_profile_page_state': 'adgroup_app_profile_page_state',
            'feed_type': 'feed_type',
            'rf_purchased_type': 'rf_purchased_type',
            'purchased_impression': 'purchased_impression',
            'purchased_reach': 'purchased_reach',
            'rf_estimated_cpr': 'rf_estimated_cpr',
            'rf_estimated_frequency': 'rf_estimated_frequency',
            'split_test_group_id': 'split_test_group_id',
            'split_test_status': 'split_test_status',
            'is_new_structure': 'is_new_structure',
            'skip_learning_phase': 'skip_learning_phase',
        }
