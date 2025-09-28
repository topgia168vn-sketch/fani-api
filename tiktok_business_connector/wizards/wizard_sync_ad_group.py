from odoo import models, fields


class WizardSyncTiktokAdGroup(models.TransientModel):
    _name = 'wizard.sync.tiktok.ad_group'
    _description = 'Wizard Sync Ad Group'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    odoo_advertiser_ids = fields.Many2many('tiktok.advertiser', string='Advertisers', required=True)
    date_from = fields.Datetime("Ngày Bắt đầu Campaign", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc Campaign", default=_default_date_to)

    def action_sync(self):
        filtering = {}
        # format of YYYY-MM-DD HH:MM:SS (UTC time zone)
        if self.date_from:
            date_from_str = self.date_from.strftime('%Y-%m-%d %H:%M:%S')
            filtering['creation_filter_start_time'] = date_from_str
        if self.date_to:
            date_end_str = self.date_to.strftime('%Y-%m-%d %H:%M:%S')
            filtering['creation_filter_end_time'] = date_end_str

        self.odoo_advertiser_ids._sync_ad_groups(filtering=filtering)
