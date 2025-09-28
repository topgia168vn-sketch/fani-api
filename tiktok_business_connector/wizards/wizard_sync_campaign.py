from odoo import models, fields
import json


class WizardSyncTiktokCampaign(models.TransientModel):
    _name = 'wizard.sync.tiktok.campaign'
    _description = 'Wizard Sync Campaign'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    odoo_advertiser_ids = fields.Many2many('tiktok.advertiser', string='Advertisers', required=True)
    date_from = fields.Datetime("Ngày Bắt đầu Campaign", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc Campaign", default=_default_date_to)

    def action_sync(self):
        dict_filtering = {}
        # format of YYYY-MM-DD HH:MM:SS (UTC time zone)
        if self.date_from:
            date_from_str = self.date_from.strftime('%Y-%m-%d %H:%M:%S')
            dict_filtering['creation_filter_start_time'] = date_from_str
        if self.date_to:
            date_end_str = self.date_to.strftime('%Y-%m-%d %H:%M:%S')
            dict_filtering['creation_filter_end_time'] = date_end_str

        for odoo_advertiser in self.odoo_advertiser_ids:
            dict_params_advertiser = {'advertiser_id': odoo_advertiser.advertiser_id}
            if dict_filtering:
                dict_params_advertiser['filtering'] = json.dumps(dict_filtering)

            # lấy access token từ business account của advertiser, có thể có nhiều access token trong nhiều business accounts
            access_token_list = odoo_advertiser.business_account_ids.sudo().mapped('access_token')
            for access_token in access_token_list:
                if not access_token:
                    continue
                self.env['tiktok.campaign']._sync_campaigns(dict_params=dict_params_advertiser, access_token=access_token)
