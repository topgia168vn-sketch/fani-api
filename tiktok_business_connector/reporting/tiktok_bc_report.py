from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from odoo.tools import format_date
import time
from datetime import datetime
import json

_logger = logging.getLogger(__name__)


class TiktokBcReport(models.Model):
    _name = 'tiktok.bc.report'
    _description = 'TikTok BC Report'
    _inherit = ['tiktok.business.api.mixin']

    def _get_default_metrics(self):
        """Get default metrics for the report"""
        return [
            "spend", "billed_cost", "cash_spend", "voucher_spend",
            "cpc", "cpm", "impressions", "gross_impressions",
            "clicks", "ctr", "reach", "cost_per_1000_reached",
            "frequency", "conversion", "cost_per_conversion",
            "conversion_rate", "conversion_rate_v2",
            "real_time_conversion", "real_time_cost_per_conversion",
            "real_time_conversion_rate", "real_time_conversion_rate_v2",
            "result", "cost_per_result", "result_rate",
            "real_time_result", "real_time_cost_per_result",
            "real_time_result_rate", "secondary_goal_result",
            "cost_per_secondary_goal_result", "secondary_goal_result_rate"
        ]

    def _get_default_dimensions(self):
        """Get default dimensions for the report"""
        return [
            'advertiser_id',
            'stat_time_day'
        ]


    name = fields.Char(string='Name', required=True)
    odoo_bc_id = fields.Many2one('tiktok.bussiness.account', string='Business Account (BC)')
    odoo_advertiser_id = fields.Many2one('tiktok.advertiser', string='Advertiser')
    report_line_ids = fields.One2many('tiktok.bc.report.line', 'bc_report_id', string='Report Lines')

    report_type = fields.Selection([
        ('BASIC', 'Basic'),
        ('AUDIENCE', 'Audience')
    ], string='Report Type', default='BASIC', required=True)
    data_level = fields.Selection([
        ('AUCTION_ADVERTISER', 'Advertiser Level'),
        ('AUCTION_CAMPAIGN', 'Campaign Level'),
        ('AUCTION_ADGROUP', 'Ad Group Level'),
        ('AUCTION_AD', 'Ad Level'),
    ], string='Data Level', default='AUCTION_ADVERTISER', required=True)
    page_size = fields.Integer(string='Page Size', default=1000)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    dimensions = fields.Text(string='Dimensions', default=lambda self: json.dumps(self._get_default_dimensions()), required=True)
    metrics = fields.Text(string='Metrics', default=lambda self: json.dumps(self._get_default_metrics()), required=True)
    filters = fields.Text(string='Filters')

    final_params = fields.Text(string='Final Params', compute='_compute_final_params', store=True, readonly=False)

    no_data = fields.Boolean(string='No Data', default=False, help='Report này không có thông tin từ TikTok!')

    raw_payload = fields.Json(string='Raw Payload')
    raw_data = fields.Json(string='Raw Data')

    # for template
    is_template = fields.Boolean(string='Is Template', default=False)
    odoo_advertiser_ids = fields.Many2many('tiktok.advertiser', string='Advertisers')
    report_id = fields.Many2one('tiktok.bc.report', string='Report Template')

    @api.depends('report_type', 'data_level', 'dimensions', 'metrics', 'start_date', 'end_date', 'odoo_advertiser_id', 'page_size', 'filters', 'is_template')
    def _compute_final_params(self):
        """
        Dựa vào các thông tin -> chuẩn bị params để gọi API
        """
        for record in self.filtered(lambda r: not r.is_template):
            vals = record._get_final_params()
            record.final_params = json.dumps(vals)

    def _get_final_params(self):
        """
        Get final params for the report
        """
        vals = {
            "report_type": self.report_type,
            "data_level": self.data_level,
            "dimensions": self.dimensions,
            "start_date": self.start_date.strftime('%Y-%m-%d') if self.start_date else False, # YYYY-MM-DD
            "end_date": self.end_date.strftime('%Y-%m-%d') if self.end_date else False, # YYYY-MM-DD
            "advertiser_id": self.odoo_advertiser_id.advertiser_id,
            "page_size": self.page_size
        }
        if self.metrics:
            vals["metrics"] = self.metrics
        if self.filters:
            vals["filters"] = json.dumps(self.filters)
        return vals

    def _action_generate_data(self):
        for record in self:
            if record.report_type == 'AUDIENCE':
                raise UserError(_("Audience report is not supported yet."))
            
            # Validate required fields
            if not record.odoo_advertiser_id:
                raise UserError(_("Please select an advertiser first."))
            
            if not record.start_date or not record.end_date:
                raise UserError(_("Please set start date and end date."))
            
            # Get access token from business account
            if not record.odoo_bc_id:
                raise UserError(_("Business account (BC) not found. Please choose the business account first."))
            access_token = record.odoo_bc_id.sudo().access_token
            if not access_token:
                raise UserError(_("Access token (BC) not found. Please authorize the business account first."))
            
            # Prepare API payload
            api_payload = record._get_final_params()
            
            page_index = 1
            while True:
                api_payload['page'] = page_index
                # Call TikTok Business API
                try:
                    endpoint = "report/integrated/get/"
                    response_data = record._call_tiktok_api(
                        endpoint=endpoint,
                        access_token=access_token,
                        method='GET',
                        params=api_payload
                    )
                    
                    # Store raw payload for debugging
                    record.write({
                        'raw_payload': api_payload,
                        'raw_data': response_data,
                    })
                    
                    # Process response and create report lines
                    record._process_api_response(response_data)

                    # Check page_info: Nếu page_index < total_page, tăng page_index để lấy phần tiếp theo
                    page_info = response_data.get('page_info', {})
                    if page_index < page_info.get('total_page', page_index):
                        page_index += 1
                    else:
                        break
                    
                except Exception as e:
                    _logger.error(f"Tiktok Marketing API: Error generating TikTok report data: {str(e)}")
                    raise UserError(_("Tiktok Marketing API: Error generating report data: %s") % str(e))


    def action_generate_data(self):
        """
        Generate report data by calling TikTok Business API reporting endpoint
        """
        self._action_generate_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Report data generated successfully!'),
                'type': 'success',
            }
        }

    def action_generate_report_and_data(self):
        """
        Generate reports and data by calling TikTok Business API reporting endpoint
        """
        self.ensure_one()
        report_vals = []
        for odoo_advertiser in self.odoo_advertiser_ids:
            date_from_display = format_date(self.env, self.start_date)
            date_to_display = format_date(self.env, self.end_date)
            vals = {
                'odoo_advertiser_id': odoo_advertiser.id,
                'odoo_bc_id': odoo_advertiser.business_account_ids[:1].id,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'data_level': self.data_level,
                'report_type': self.report_type,
                'report_id': self.id,
                'dimensions': self.dimensions,
                'metrics': self.metrics,
                'filters': self.filters,
                'page_size': self.page_size,
                'is_template': False,
            }
            if self.data_level == 'AUCTION_ADVERTISER':
                vals['name'] = f'[{date_from_display} - {date_to_display}] {odoo_advertiser.name} -> Cấp độ Nhà quảng cáo'
            elif self.data_level == 'AUCTION_CAMPAIGN':
                vals['name'] = f'[{date_from_display} - {date_to_display}] {odoo_advertiser.name} -> Cấp độ Chiến dịch'
            elif self.data_level == 'AUCTION_ADGROUP':
                vals['name'] = f'[{date_from_display} - {date_to_display}] {odoo_advertiser.name} -> Cấp độ Nhóm Quảng cáo'
            elif self.data_level == 'AUCTION_AD':
                vals['name'] = f'[{date_from_display} - {date_to_display}] {odoo_advertiser.name} -> Cấp độ Quảng cáo'
            else:
                vals['name'] = self.name
            report_vals.append(vals)
        reports = self.env['tiktok.bc.report'].create(report_vals)
        reports._action_generate_data()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Report data generated successfully!'),
                'type': 'success',
            }
        }
    
    def _process_api_response(self, response_data):
        """Process API response and create report lines"""
        if not response_data:
            raise UserError(_("No data received from TikTok API"))
        
        # Get list of report data
        report_list = response_data.get('list', [])
        if not report_list:
            _logger.info(f"Tiktok Marketing API: Report {self.name}: No report data found in API response")
            self.write({'no_data': True})
            return
        else:
            self.write({'no_data': False})
        
        # Clear existing report lines
        self.report_line_ids.unlink()
        

        # read all odoo records
        campaign_ids = [item.get('dimensions', {}).get('campaign_id') for item in report_list if item.get('dimensions', {}).get('campaign_id')]
        adgroup_ids = [item.get('dimensions', {}).get('adgroup_id') for item in report_list if item.get('dimensions', {}).get('adgroup_id')]
        ad_ids = [item.get('dimensions', {}).get('ad_id') for item in report_list if item.get('dimensions', {}).get('ad_id')]

        # Tìm các records hiện có
        existing_campaigns = self.env['tiktok.campaign'].search_read([('campaign_id', 'in', campaign_ids)], fields=['id', 'campaign_id'])
        existing_ad_groups = self.env['tiktok.ad_group'].search_read([('adgroup_id', 'in', adgroup_ids)], fields=['id', 'adgroup_id'])
        existing_ads = self.env['tiktok.ad'].search_read([('ad_id', 'in', ad_ids)], fields=['id', 'ad_id'])

        # Map odoo records
        odoo_campaigns_map = {r['campaign_id']: r['id'] for r in existing_campaigns}
        odoo_adgroups_map = {r['adgroup_id']: r['id'] for r in existing_ad_groups}
        odoo_ads_map = {r['ad_id']: r['id'] for r in existing_ads}

        # Create new report lines
        report_line_vals = []
        for item in report_list:
            line_vals = self._prepare_report_line_vals(item, odoo_campaigns_map, odoo_adgroups_map, odoo_ads_map)
            report_line_vals.append(line_vals)
        
        # Create all report lines at once
        if report_line_vals:
            self.env['tiktok.bc.report.line'].create(report_line_vals)

    def _prepare_report_line_vals(self, item, odoo_campaigns_map, odoo_adgroups_map, odoo_ads_map):
        """Prepare values for creating a report line"""
        dimensions_data = item.get('dimensions', {})
        metrics_data = item.get('metrics', {})


        vals = {
            'bc_report_id': self.id,
            'advertiser_id': self.odoo_advertiser_id.advertiser_id,
            'campaign_id': dimensions_data.get('campaign_id', False),
            'adgroup_id': dimensions_data.get('adgroup_id', False),
            'ad_id': dimensions_data.get('ad_id', False),
            'odoo_advertiser_id': self.odoo_advertiser_id.id,
            'stat_time_day': self._convert_timestamp_to_datetime(dimensions_data.get('stat_time_day', False)),
            'stat_time_hour': self._convert_timestamp_to_datetime(dimensions_data.get('stat_time_hour', False)),
        }
        if vals['campaign_id']:
            vals['odoo_campaign_id'] = odoo_campaigns_map.get(vals['campaign_id'], False)
        if vals['adgroup_id']:
            vals['odoo_adgroup_id'] = odoo_adgroups_map.get(vals['adgroup_id'], False)
        if vals['ad_id']:
            vals['odoo_ad_id'] = odoo_ads_map.get(vals['ad_id'], False)
        
        # Map metric fields
        metric_mapping = self.env['tiktok.bc.report.line']._map_metric_fields()
        
        for key, value in metrics_data.items():
            field_key = metric_mapping.get(key)
            if field_key:
                vals[field_key] = self._convert_string_to_float(value)
        return vals

    def action_view_report_lines(self):
        """Action to view report lines"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Report Lines'),
            'res_model': 'tiktok.bc.report.line',
            'view_mode': 'list,form',
            'domain': [('bc_report_id', '=', self.id)],
            'context': {'default_bc_report_id': self.id},
        }