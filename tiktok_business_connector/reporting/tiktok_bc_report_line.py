from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time
from datetime import datetime
import json


class TiktokBcReportLine(models.Model):
    _name = 'tiktok.bc.report.line'
    _description = 'TikTok BC Report Line'
    _inherit = ['tiktok.business.api.mixin']
    _order = 'stat_time_hour DESC, stat_time_day DESC'

    bc_report_id = fields.Many2one('tiktok.bc.report', string='BC Report', index=True, ondelete='cascade')
    report_type = fields.Selection(related='bc_report_id.report_type', string='Report Type', store=True)
    data_level = fields.Selection(related='bc_report_id.data_level', string='Data Level', store=True)

    # các thông tin dimension: link in odoo
    odoo_advertiser_id = fields.Many2one('tiktok.advertiser', string='Advertiser', index=True)
    odoo_campaign_id = fields.Many2one('tiktok.campaign', string='Campaign', index=True)
    odoo_adgroup_id = fields.Many2one('tiktok.ad_group', string='Ad Group', index=True)
    odoo_ad_id = fields.Many2one('tiktok.ad', string='Ad', index=True)

    # các thông tin dimension: data from tiktok
    advertiser_id = fields.Char(string='Advertiser ID', index=True)
    campaign_id = fields.Char(string='Campaign ID', index=True)
    adgroup_id = fields.Char(string='Ad Group ID', index=True)
    ad_id = fields.Char(string='Ad ID', index=True)
    stat_time_day = fields.Date(string='Date', index=True) # Bỏ thông tin giờ 00:00:00
    stat_time_hour = fields.Datetime(string='Hour', index=True) # giữ nguyên, cần convert timezone ??

    # các thông tin metrics: data from tiktok
    spend = fields.Float(string='Cost', digits=(16, 2))
    billed_cost = fields.Float(string='Net Cost', digits=(16, 2))
    cash_spend = fields.Float(string='Cost Charged by Cash', digits=(16, 2))
    voucher_spend = fields.Float(string='Cost Charged by Voucher', digits=(16, 2))
    cpc = fields.Float(string='CPC (destination)', digits=(16, 4))
    cpm = fields.Float(string='CPM', digits=(16, 4))
    impressions = fields.Integer(string='Impressions')
    gross_impressions = fields.Integer(string='Gross Impressions (Includes Invalid Impressions)')
    clicks = fields.Integer(string='Clicks (destination)')
    ctr = fields.Float(string='CTR (destination)', digits=(16, 4))
    reach = fields.Integer(string='Reach')
    cost_per_1000_reached = fields.Float(string='Cost per 1,000 people reached', digits=(16, 4))
    frequency = fields.Float(string='Frequency', digits=(16, 4))
    conversion = fields.Integer(string='Conversions')
    cost_per_conversion = fields.Float(string='Cost per conversion', digits=(16, 4))
    conversion_rate = fields.Float(string='Conversion rate (CVR, clicks)', digits=(16, 4))
    conversion_rate_v2 = fields.Float(string='Conversion rate (CVR)', digits=(16, 4))
    real_time_conversion = fields.Integer(string='Conversions by conversion time')
    real_time_cost_per_conversion = fields.Float(string='Cost per conversion by conversion time', digits=(16, 4))
    real_time_conversion_rate = fields.Float(string='Real-time conversion rate (CVR, clicks)', digits=(16, 4))
    real_time_conversion_rate_v2 = fields.Float(string='Conversion rate (CVR) by conversion time', digits=(16, 4))
    result = fields.Integer(string='Results')
    cost_per_result = fields.Float(string='Cost per result', digits=(16, 4))
    result_rate = fields.Float(string='Result rate', digits=(16, 4))
    real_time_result = fields.Integer(string='Real-time results')
    real_time_cost_per_result = fields.Float(string='Real-time cost per result', digits=(16, 4))
    real_time_result_rate = fields.Float(string='Real-time result rate', digits=(16, 4))
    secondary_goal_result = fields.Integer(string='Deep funnel result')
    cost_per_secondary_goal_result = fields.Float(string='Cost per deep funnel result', digits=(16, 4))
    secondary_goal_result_rate = fields.Float(string='Deep funnel result rate', digits=(16, 4))

    @api.model
    def _map_metric_fields(self):
        """Map API metric fields to Odoo fields"""
        return {
            'spend': 'spend',
            'billed_cost': 'billed_cost',
            'cash_spend': 'cash_spend',
            'voucher_spend': 'voucher_spend',
            'cpc': 'cpc',
            'cpm': 'cpm',
            'impressions': 'impressions',
            'gross_impressions': 'gross_impressions',
            'clicks': 'clicks',
            'ctr': 'ctr',
            'reach': 'reach',
            'cost_per_1000_reached': 'cost_per_1000_reached',
            'frequency': 'frequency',
            'conversion': 'conversion',
            'cost_per_conversion': 'cost_per_conversion',
            'conversion_rate': 'conversion_rate',
            'conversion_rate_v2': 'conversion_rate_v2',
            'real_time_conversion': 'real_time_conversion',
            'real_time_cost_per_conversion': 'real_time_cost_per_conversion',
            'real_time_conversion_rate': 'real_time_conversion_rate',
            'real_time_conversion_rate_v2': 'real_time_conversion_rate_v2',
            'result': 'result',
            'cost_per_result': 'cost_per_result',
            'result_rate': 'result_rate',
            'real_time_result': 'real_time_result',
            'real_time_cost_per_result': 'real_time_cost_per_result',
            'real_time_result_rate': 'real_time_result_rate',
            'secondary_goal_result': 'secondary_goal_result',
            'cost_per_secondary_goal_result': 'cost_per_secondary_goal_result',
            'secondary_goal_result_rate': 'secondary_goal_result_rate',
        }
