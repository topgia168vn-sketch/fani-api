from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json
_logger = logging.getLogger(__name__)


class TiktokAdvertiser(models.Model):
    _name = 'tiktok.advertiser'
    _description = 'TikTok Advertiser'
    _inherit = ['tiktok.business.api.mixin']

    name = fields.Char(string='Name')
    advertiser_id = fields.Char(string='Advertiser ID')
    active = fields.Boolean(string='Active', default=True)


    # Trường quan hệ
    # 1 advertiser có thể ở nhiều business accounts
    business_account_ids = fields.Many2many('tiktok.bussiness.account', string='Business Accounts')

    # Lưu data để check lại khi cần
    raw_payload = fields.Json(string='Raw Payload')

    def sync_advertisers(self, advertiser_ids=None, access_token=None):
        """Đồng bộ dữ liệu advertisers từ TikTok Business API"""
        # Gọi API để lấy danh sách advertisers -> Update
        try:
            advertiser_ids = advertiser_ids or self.mapped('advertiser_id')
            endpoint = "advertiser/info/"
            params = {
                'advertiser_ids': json.dumps(advertiser_ids),
            }
            advertisers_data = self._call_tiktok_api(endpoint, access_token, method='GET', params=params)
            
            if not advertisers_data:
                raise UserError(_('Không có dữ liệu advertisers từ TikTok API'))
            
            # Xử lý dữ liệu trả về
            advertisers_list = advertisers_data.get('list', [])
            
            if not advertisers_list:
                raise UserError(_('Danh sách advertisers trống'))
            

            advertisers = self.search([('advertiser_id', 'in', advertiser_ids)])
            advertiser_vals_list = []  # for create multiple records
            
            # Cập nhật hoặc tạo mới records
            advertisers_synced = self.env['tiktok.advertiser']
            for advertiser_data in advertisers_list:
                advertiser_id = advertiser_data.get('advertiser_id')
                if not advertiser_id:
                    continue
                
                # Tìm record hiện tại hoặc tạo mới
                advertiser_record = advertisers.filtered(lambda a: a.advertiser_id == advertiser_id)                
                if advertiser_record:
                    # Cập nhật raw_payload với toàn bộ dữ liệu từ API
                    advertiser_record.write({
                        'name': advertiser_data.get('name', advertiser_record.name),
                        'raw_payload': advertiser_data,
                    })
                    advertisers_synced |= advertiser_record
                else:
                    # Update vals to list
                    advertiser_vals_list.append({
                            'advertiser_id': advertiser_id,
                            'name': advertiser_data.get('name', ''),
                            'raw_payload': advertiser_data,
                        })
            
            # Tạo advertisers mới
            if advertiser_vals_list:
                new_advertisers = self.create(advertiser_vals_list)
                advertisers_synced |= new_advertisers
            
            # trả về danh sách advertisers đã đồng bộ cho business account để link với nhau
            return advertisers_synced
            
        except Exception as e:
            _logger.error(f"Tiktok Marketing API: Error syncing advertisers: {str(e)}")
            raise UserError(_('Tiktok Marketing API: Lỗi khi đồng bộ advertisers: %s') % str(e))

    def _sync_campaigns(self):
        """Đồng bộ campaigns cho các advertisers được chọn"""
        for advertiser in self:
            dict_params = {'advertiser_id': advertiser.advertiser_id}
            # lấy access token từ business account của advertiser, có thể có nhiều access token trong nhiều business accounts
            access_token_list = advertiser.business_account_ids.sudo().mapped('access_token')
            for access_token in access_token_list:
                if not access_token:
                    continue
                self.env['tiktok.campaign']._sync_campaigns(dict_params=dict_params, access_token=access_token)

    def action_sync_campaigns(self):
        """Đồng bộ campaigns cho các advertisers được chọn"""
        self._sync_campaigns()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced campaigns successfully!'),
                'type': 'success',
            }
        }

    def _sync_ad_groups(self, campaign_ids=None, adgroup_ids=None, filtering=None):
        """Đồng bộ ad groups cho các advertisers được chọn
        Args:
            campaign_ids: list of campaign ids, default is None, max 100 ids
        Returns:
            None
        """
        for advertiser in self:
            dict_params = { 'advertiser_id': advertiser.advertiser_id}
            filtering = filtering or {}
            if campaign_ids:
                filtering['campaign_ids'] = campaign_ids
            if adgroup_ids:
                filtering['adgroup_ids'] = adgroup_ids
            if filtering:
                dict_params['filtering'] = json.dumps(filtering)
            # lấy access token từ business account của advertiser, có thể có nhiều access token trong nhiều business accounts
            access_token_list = advertiser.business_account_ids.sudo().mapped('access_token')
            for access_token in access_token_list:
                if not access_token:
                    continue
                self.env['tiktok.ad_group']._sync_ad_groups(dict_params=dict_params, access_token=access_token)

    def action_sync_ad_groups(self):
        """Đồng bộ ad groups cho các advertisers được chọn"""
        self._sync_ad_groups()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced ad groups successfully!'),
                'type': 'success',
            }
        }

    def _sync_ads(self, ad_ids=None, adgroup_ids=None, campaign_ids=None, filtering=None):
        """Đồng bộ ads cho các advertisers được chọn
        Args:
            ad_ids: list of ad ids, default is None, max 100 ids
            adgroup_ids: list of adgroup ids, default is None, max 100 ids
            campaign_ids: list of campaign ids, default is None, max 100 ids
            filtering: dict, default is None
        Returns:
            None
        """
        for advertiser in self:
            dict_params = { 'advertiser_id': advertiser.advertiser_id}
            filtering = filtering or {}
            if ad_ids:
                filtering['ad_ids'] = ad_ids
            if adgroup_ids:
                filtering['adgroup_ids'] = adgroup_ids
            if campaign_ids:
                filtering['campaign_ids'] = campaign_ids
            if filtering:
                dict_params['filtering'] = json.dumps(filtering)
            # lấy access token từ business account của advertiser, có thể có nhiều access token trong nhiều business accounts
            access_token_list = advertiser.business_account_ids.sudo().mapped('access_token')
            for access_token in access_token_list:
                if not access_token:
                    continue
                self.env['tiktok.ad']._sync_ads(dict_params=dict_params, access_token=access_token)

    def action_sync_ads(self):
        """Đồng bộ ads cho các advertisers được chọn"""
        self._sync_ads()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Synced ads successfully!'),
                'type': 'success',
            }
        }