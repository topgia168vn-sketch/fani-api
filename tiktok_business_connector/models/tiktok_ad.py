from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time
from datetime import datetime
import json

_logger = logging.getLogger(__name__)

# Fields cần convert timestamp sang Datetime
AD_DATETIME_FIELDS = ['create_time', 'modify_time']
# Fields cần convert sang Text
AD_LIST_TO_STRING_FIELDS = [
    'item_group_ids',
    'sku_ids',
    'vehicle_ids',
    'showcase_products',
    'image_ids',
    'auto_disclaimer_types',
    'product_display_field_list',
    'ad_texts',
    'utm_params',
    'deeplink_utm_params',
    'disclaimer_text',
    'disclaimer_clickable_texts',
    'tracking_offline_event_set_ids',
]


class TiktokAd(models.Model):
    _name = 'tiktok.ad'
    _description = 'TikTok Ad'
    _inherit = ['tiktok.business.api.mixin']
    _rec_name = 'ad_name'
    _order = 'create_time DESC'

    # Fields theo TikTok API response - Sắp xếp theo thứ tự trong fields.py
    advertiser_id = fields.Char(string='Advertiser ID', index=True, help='Advertiser ID')
    campaign_id = fields.Char(string='Campaign ID', index=True, help='Campaign ID')
    campaign_name = fields.Char(string='Campaign Name', index=True, help='Campaign Name')
    campaign_system_origin = fields.Char(string='Campaign System Origin', help='Campaign System Origin')
    adgroup_id = fields.Char(string='Ad Group ID', index=True, help='Ad Group ID')
    adgroup_name = fields.Char(string='Ad Group Name', index=True, help='Ad Group Name')
    ad_id = fields.Char(string='Ad ID', index=True, help='Ad ID')
    ad_name = fields.Char(string='Ad Name', index=True, help='Ad Name')
    create_time = fields.Datetime(string='Created Date', index=True, help='Created Date')
    modify_time = fields.Datetime(string='Modified Date', help='Modified Date')
    identity_id = fields.Char(string='Identity ID', help='Identity ID')
    identity_type = fields.Char(string='Identity Type', help='Identity Type')
    identity_authorized_bc_id = fields.Char(string='Identity Authorized BC ID', help='Identity Authorized BC ID')
    catalog_id = fields.Char(string='Catalog ID', help='Catalog ID')
    product_specific_type = fields.Char(string='Product Specific Type', help='Product Specific Type')
    item_group_ids = fields.Text(string='Item Group IDs', help='Item Group IDs')
    product_set_id = fields.Char(string='Product Set ID', help='Product Set ID')
    sku_ids = fields.Text(string='SKU IDs', help='SKU IDs')
    vehicle_ids = fields.Text(string='Vehicle IDs', help='Vehicle IDs')
    showcase_products = fields.Text(string='Showcase Products', help='Showcase Products')
    ad_format = fields.Char(string='Ad Format', help='Ad Format')
    vertical_video_strategy = fields.Char(string='Vertical Video Strategy', help='Vertical Video Strategy')
    dynamic_format = fields.Char(string='Dynamic Format', help='Dynamic Format')
    video_id = fields.Char(string='Video ID', help='Video ID')
    image_ids = fields.Text(string='Image IDs', help='Image IDs')
    carousel_image_index = fields.Integer(string='Carousel Image Index', help='Carousel Image Index')
    end_card_cta = fields.Char(string='End Card CTA', help='End Card CTA')
    auto_disclaimer_types = fields.Text(string='Auto Disclaimer Types', help='Auto Disclaimer Types')
    product_display_field_list = fields.Text(string='Product Display Field List', help='Product Display Field List')
    music_id = fields.Char(string='Music ID', help='Music ID')
    tiktok_item_id = fields.Char(string='TikTok Item ID', help='TikTok Item ID')
    promotional_music_disabled = fields.Boolean(string='Promotional Music Disabled', help='Promotional Music Disabled')
    item_duet_status = fields.Char(string='Item Duet Status', help='Item Duet Status')
    item_stitch_status = fields.Char(string='Item Stitch Status', help='Item Stitch Status')
    dark_post_status = fields.Char(string='Dark Post Status', help='Dark Post Status')
    branded_content_disabled = fields.Boolean(string='Branded Content Disabled', help='Branded Content Disabled')
    shopping_ads_video_package_id = fields.Char(string='Shopping Ads Video Package ID', help='Shopping Ads Video Package ID')
    ad_text = fields.Text(string='Ad Text', help='Ad Text')
    ad_texts = fields.Text(string='Ad Texts', help='Ad Texts')
    call_to_action = fields.Char(string='Call To Action', help='Call To Action')
    call_to_action_id = fields.Char(string='Call To Action ID', help='Call To Action ID')
    card_id = fields.Char(string='Card ID', help='Card ID')
    landing_page_url = fields.Char(string='Landing Page URL', help='Landing Page URL')
    utm_params = fields.Text(string='UTM Params', help='UTM Params')
    page_id = fields.Float(string='Page ID', help='Page ID')
    cpp_url = fields.Char(string='CPP URL', help='CPP URL')
    tiktok_page_category = fields.Char(string='TikTok Page Category', help='TikTok Page Category')
    phone_region_code = fields.Char(string='Phone Region Code', help='Phone Region Code')
    phone_region_calling_code = fields.Char(string='Phone Region Calling Code', help='Phone Region Calling Code')
    phone_number = fields.Char(string='Phone Number', help='Phone Number')
    deeplink = fields.Char(string='Deeplink', help='Deeplink')
    deeplink_type = fields.Char(string='Deeplink Type', help='Deeplink Type')
    deeplink_format_type = fields.Char(string='Deeplink Format Type', help='Deeplink Format Type')
    shopping_ads_deeplink_type = fields.Char(string='Shopping Ads Deeplink Type', help='Shopping Ads Deeplink Type')
    deeplink_utm_params = fields.Text(string='Deeplink UTM Params', help='Deeplink UTM Params')
    shopping_ads_fallback_type = fields.Char(string='Shopping Ads Fallback Type', help='Shopping Ads Fallback Type')
    fallback_type = fields.Char(string='Fallback Type', help='Fallback Type')
    dynamic_destination = fields.Char(string='Dynamic Destination', help='Dynamic Destination')
    auto_message_id = fields.Char(string='Auto Message ID', help='Auto Message ID')
    aigc_disclosure_type = fields.Char(string='AIGC Disclosure Type', help='AIGC Disclosure Type')
    disclaimer_type = fields.Char(string='Disclaimer Type', help='Disclaimer Type')
    disclaimer_text = fields.Text(string='Disclaimer Text', help='Disclaimer Text')
    disclaimer_clickable_texts = fields.Text(string='Disclaimer Clickable Texts', help='Disclaimer Clickable Texts')
    tracking_pixel_id = fields.Float(string='Tracking Pixel ID', help='Tracking Pixel ID')
    tracking_app_id = fields.Char(string='Tracking App ID', help='Tracking App ID')
    tracking_offline_event_set_ids = fields.Text(string='Tracking Offline Event Set IDs', help='Tracking Offline Event Set IDs')
    tracking_message_event_set_id = fields.Char(string='Tracking Message Event Set ID', help='Tracking Message Event Set ID')
    vast_moat_enabled = fields.Boolean(string='VAST Moat Enabled', help='VAST Moat Enabled')
    viewability_postbid_partner = fields.Char(string='Viewability Postbid Partner', help='Viewability Postbid Partner')
    viewability_vast_url = fields.Char(string='Viewability VAST URL', help='Viewability VAST URL')
    brand_safety_postbid_partner = fields.Char(string='Brand Safety Postbid Partner', help='Brand Safety Postbid Partner')
    brand_safety_vast_url = fields.Char(string='Brand Safety VAST URL', help='Brand Safety VAST URL')
    impression_tracking_url = fields.Char(string='Impression Tracking URL', help='Impression Tracking URL')
    click_tracking_url = fields.Char(string='Click Tracking URL', help='Click Tracking URL')
    playable_url = fields.Char(string='Playable URL', help='Playable URL')
    operation_status = fields.Char(string='Operation Status', index=True, help='Operation Status')
    secondary_status = fields.Char(string='Secondary Status', index=True, help='Secondary Status')
    creative_type = fields.Char(string='Creative Type', help='Creative Type')
    app_name = fields.Char(string='App Name', help='App Name')
    display_name = fields.Char(string='Display Name', help='Display Name')
    avatar_icon_web_uri = fields.Char(string='Avatar Icon Web URI', help='Avatar Icon Web URI')
    profile_image_url = fields.Char(string='Profile Image URL', help='Profile Image URL')
    creative_authorized = fields.Boolean(string='Creative Authorized', help='Creative Authorized')
    is_aco = fields.Boolean(string='Is ACO', help='Is ACO')
    is_new_structure = fields.Boolean(string='Is New Structure', help='Is New Structure')
    optimization_event = fields.Char(string='Optimization Event', help='Optimization Event')

    # Trường quan hệ
    odoo_ad_group_id = fields.Many2one('tiktok.ad_group', string='Ad Group', index=True)
    odoo_campaign_id = fields.Many2one(related='odoo_ad_group_id.odoo_campaign_id', store=True, index=True)
    odoo_advertiser_id = fields.Many2one(related='odoo_ad_group_id.odoo_advertiser_id', store=True, index=True)

    # Raw data for re-check
    raw_payload = fields.Json(string='Raw Payload')

    def _sync_ads(self, dict_params, access_token, page_index=1):
        """
        Đồng bộ dữ liệu ads từ TikTok Business API
        Args:
            dict_params: dict: params for API
                - filtering:
                    - ad_ids: list of ad ids. max 100
                    - adgroup_ids: list of adgroup ids. max 100
                    - campaign_ids: list of campaign ids. max 100
                    - creation_filter_start_time. format YYYY-MM-DD HH:MM:SS (UTC time zone)
                    - creation_filter_end_time. format YYYY-MM-DD HH:MM:SS (UTC time zone)
            access_token: str: access token
            page_index: int: page index
        Returns:
            None
        """
        ad_total = 0
        start_time = time.time()
        while True:
            # Gọi API để lấy danh sách ads
            dict_params.update({  # Mặc định là max page_size, tăng page_index để lấy phần tiếp theo
                'page': page_index,
                'page_size': 1000,
            })
            
            endpoint = "ad/get/"
            ads_data = self._call_tiktok_api(endpoint, access_token, method='GET', params=dict_params)
            
            if not ads_data:
                _logger.error(f"Tiktok Marketing API {endpoint}: Không có dữ liệu ads từ TikTok API")
                break
            
            # Xử lý dữ liệu trả về
            ads_list = ads_data.get('list', [])
            page_info = ads_data.get('page_info', {})

            if not ads_list:
                advertiser_id = dict_params.get('advertiser_id')
                _logger.info(f"Tiktok Marketing API {endpoint}: Danh sách ads trống -> Advertiser ID: {advertiser_id}")
                break
            
            if ads_list:
                # Update ads
                ad_total += len(ads_list)
                self._update_ads(ads_list)

            # Check page_info: Nếu page_index < total_page, tăng page_index để lấy phần tiếp theo
            if page_index < page_info.get('total_page', page_index):
                page_index += 1
            else:
                break
        if ad_total > 0:
            end_time = time.time()
            _logger.info(f"Tiktok Marketing API {endpoint}: Đã đồng bộ {ad_total} ads -> {end_time - start_time} (s)")

    def _update_ads(self, ads_list):
        """
        Cập nhật/tạo mới ads
        Args:
            ads_list: list of ads data
        Returns:
            None
        """
        # Lấy danh sách ad_ids từ response
        ad_ids = [ad.get('ad_id') for ad in ads_list]
        # Tìm các ads hiện có
        existing_ads = self.search_read([('ad_id', 'in', ad_ids)], fields=['id', 'ad_id'])
        existing_ads_map = {r['ad_id']: r['id'] for r in existing_ads}

        # Lấy danh sách adgroup_ids từ response
        adgroup_ids = [ad.get('adgroup_id') for ad in ads_list]
        # Tìm các ad groups hiện có
        existing_ad_groups = self.env['tiktok.ad_group'].with_context(active_test=False).search_read([('adgroup_id', 'in', adgroup_ids)], fields=['id', 'adgroup_id'])
        existing_ad_groups_map = {r['adgroup_id']: r['id'] for r in existing_ad_groups}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()

        # Duyệt từng dict trong ads_list
        for ad_data in ads_list:
            ad_id = ad_data.get('ad_id')
            if not ad_id:
                continue
            
            # Prepare data using map_fields
            ad_vals = {
                'raw_payload': ad_data,
                'odoo_ad_group_id': existing_ad_groups_map.get(ad_data.get('adgroup_id'), False)
            }
            for key, value in ad_data.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in AD_DATETIME_FIELDS:
                        ad_vals[field_key] = self._convert_timestamp_to_datetime(value)
                    elif field_key in AD_LIST_TO_STRING_FIELDS:
                        ad_vals[field_key] = self._convert_array_to_text(value)
                    else:
                        ad_vals[field_key] = value
            
            # Kiểm tra ad đã tồn tại chưa, nếu có thì update, nếu không thì create
            if ad_id in existing_ads_map:
                update_vals_list.append((existing_ads_map[ad_id], ad_vals))
            else:
                new_vals_list.append(ad_vals)
        
        # Tạo ads mới
        if new_vals_list:
            self.sudo().create(new_vals_list)
        # Update ads
        for ad_id, vals in update_vals_list:
            ad = self.browse(ad_id)
            ad.sudo().write(vals)

    def action_sync_ads(self):
        """
        Đồng bộ 1 Ad, nếu đồng bộ nhiều Ad thì nên động bộ theo từng cấp như Ad Group, Campaign, Advertiser
        Returns: display notification
        """
        self.ensure_one()
        self.odoo_advertiser_id._sync_ads(ad_ids=[self.ad_id])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced Ad successfully!'),
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
            'adgroup_id': 'adgroup_id',
            'adgroup_name': 'adgroup_name',
            'ad_id': 'ad_id',
            'ad_name': 'ad_name',
            'create_time': 'create_time',
            'modify_time': 'modify_time',
            'identity_id': 'identity_id',
            'identity_type': 'identity_type',
            'identity_authorized_bc_id': 'identity_authorized_bc_id',
            'catalog_id': 'catalog_id',
            'product_specific_type': 'product_specific_type',
            'item_group_ids': 'item_group_ids',
            'product_set_id': 'product_set_id',
            'sku_ids': 'sku_ids',
            'vehicle_ids': 'vehicle_ids',
            'showcase_products': 'showcase_products',
            'ad_format': 'ad_format',
            'vertical_video_strategy': 'vertical_video_strategy',
            'dynamic_format': 'dynamic_format',
            'video_id': 'video_id',
            'image_ids': 'image_ids',
            'carousel_image_index': 'carousel_image_index',
            'end_card_cta': 'end_card_cta',
            'auto_disclaimer_types': 'auto_disclaimer_types',
            'product_display_field_list': 'product_display_field_list',
            'music_id': 'music_id',
            'tiktok_item_id': 'tiktok_item_id',
            'promotional_music_disabled': 'promotional_music_disabled',
            'item_duet_status': 'item_duet_status',
            'item_stitch_status': 'item_stitch_status',
            'dark_post_status': 'dark_post_status',
            'branded_content_disabled': 'branded_content_disabled',
            'shopping_ads_video_package_id': 'shopping_ads_video_package_id',
            'ad_text': 'ad_text',
            'ad_texts': 'ad_texts',
            'call_to_action': 'call_to_action',
            'call_to_action_id': 'call_to_action_id',
            'card_id': 'card_id',
            'landing_page_url': 'landing_page_url',
            'utm_params': 'utm_params',
            'page_id': 'page_id',
            'cpp_url': 'cpp_url',
            'tiktok_page_category': 'tiktok_page_category',
            'phone_region_code': 'phone_region_code',
            'phone_region_calling_code': 'phone_region_calling_code',
            'phone_number': 'phone_number',
            'deeplink': 'deeplink',
            'deeplink_type': 'deeplink_type',
            'deeplink_format_type': 'deeplink_format_type',
            'shopping_ads_deeplink_type': 'shopping_ads_deeplink_type',
            'deeplink_utm_params': 'deeplink_utm_params',
            'shopping_ads_fallback_type': 'shopping_ads_fallback_type',
            'fallback_type': 'fallback_type',
            'dynamic_destination': 'dynamic_destination',
            'auto_message_id': 'auto_message_id',
            'aigc_disclosure_type': 'aigc_disclosure_type',
            'disclaimer_type': 'disclaimer_type',
            'disclaimer_text': 'disclaimer_text',
            'disclaimer_clickable_texts': 'disclaimer_clickable_texts',
            'tracking_pixel_id': 'tracking_pixel_id',
            'tracking_app_id': 'tracking_app_id',
            'tracking_offline_event_set_ids': 'tracking_offline_event_set_ids',
            'tracking_message_event_set_id': 'tracking_message_event_set_id',
            'vast_moat_enabled': 'vast_moat_enabled',
            'viewability_postbid_partner': 'viewability_postbid_partner',
            'viewability_vast_url': 'viewability_vast_url',
            'brand_safety_postbid_partner': 'brand_safety_postbid_partner',
            'brand_safety_vast_url': 'brand_safety_vast_url',
            'impression_tracking_url': 'impression_tracking_url',
            'click_tracking_url': 'click_tracking_url',
            'playable_url': 'playable_url',
            'operation_status': 'operation_status',
            'secondary_status': 'secondary_status',
            'creative_type': 'creative_type',
            'app_name': 'app_name',
            'display_name': 'display_name',
            'avatar_icon_web_uri': 'avatar_icon_web_uri',
            'profile_image_url': 'profile_image_url',
            'creative_authorized': 'creative_authorized',
            'is_aco': 'is_aco',
            'is_new_structure': 'is_new_structure',
            'optimization_event': 'optimization_event',
        }