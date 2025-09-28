# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopeeAdsLiveReport(models.Model):
    _name = 'shopee.ads.live.report'
    _description = 'Shopee Ads Live Report'
    _inherit = 'shopee.report.mixin'
    _order = 'report_date desc, id desc'

    # ==================== HEADER INFO ====================
    shop_id = fields.Many2one(
        'shopee.shop',
        string='Shop',
        required=True,
        index=True,
        ondelete='cascade'
    )

    # Report metadata
    report_date = fields.Date(
        string='Report Date',
        required=True,
        index=True,
        help='Ngày báo cáo'
    )

    # ==================== CAMPAIGN INFO ====================
    campaign_name = fields.Char(
        string='Campaign Name',
        help='Tên chiến dịch'
    )

    campaign_id = fields.Char(
        string='Campaign ID',
        index=True,
        help='ID chiến dịch'
    )

    status = fields.Char(
        string='Status',
        help='Trạng thái'
    )

    objective = fields.Char(
        string='Objective',
        help='Mục tiêu'
    )

    start_date = fields.Date(
        string='Start Date',
        help='Ngày bắt đầu'
    )

    end_date = fields.Date(
        string='End Date',
        help='Ngày kết thúc'
    )

    daily_start_time = fields.Char(
        string='Daily Start Time',
        help='Giờ bắt đầu hàng ngày'
    )

    daily_end_time = fields.Char(
        string='Daily End Time',
        help='Giờ kết thúc hàng ngày'
    )

    budget = fields.Float(
        string='Budget',
        digits=(15, 2),
        help='Ngân sách'
    )

    # ==================== METRICS ====================
    # Views & Orders
    views = fields.Integer(
        string='Views',
        help='Lượt xem'
    )

    orders = fields.Integer(
        string='Orders',
        help='Số đơn hàng'
    )

    conversion_rate = fields.Float(
        string='Conversion Rate',
        digits=(5, 2),
        help='Tỷ lệ chuyển đổi (%)'
    )

    # GMV & Cost
    gmv = fields.Float(
        string='GMV',
        digits=(15, 2),
        help='GMV'
    )

    cost = fields.Float(
        string='Cost',
        digits=(15, 2),
        help='Chi phí'
    )

    roas = fields.Float(
        string='ROAS',
        digits=(5, 2),
        help='ROAS'
    )

    # ==================== HELPER METHODS ====================
    @api.model
    def _import_row(self, shop_id, report_date, row_data):
        """Tạo record từ dữ liệu CSV row"""
        # Parse row data (row_data là dict từ CSV)
        vals = {
            'shop_id': shop_id,
            'report_date': report_date,
            'campaign_name': row_data.get('Tên chiến dịch', ''),
            'campaign_id': row_data.get('ID chiến dịch', ''),
            'status': row_data.get('Trạng thái', ''),
            'objective': row_data.get('Mục tiêu', ''),
            'start_date': self._parse_date(row_data.get('Ngày bắt đầu', ''), '%d/%m/%Y'),
            'end_date': self._parse_date(row_data.get('Ngày kết thúc', ''), '%d/%m/%Y'),
            'daily_start_time': row_data.get('Giờ bắt đầu hàng ngày', ''),
            'daily_end_time': row_data.get('Giờ kết thúc hàng ngày', ''),
            'budget': float(row_data.get('Ngân sách', 0)),
            'views': int(row_data.get('Lượt xem', 0)),
            'orders': int(row_data.get('Số đơn hàng', 0)),
            'conversion_rate': self._parse_percentage(row_data.get('Tỷ lệ chuyển đổi', '0%')),
            'gmv': float(row_data.get('GMV', 0)),
            'cost': float(row_data.get('Chi phí', 0)),
            'roas': float(row_data.get('ROAS', 0)),
        }

        return self._upsert(
            [
                ('shop_id', '=', shop_id),
                ('report_date', '=', report_date),
                ('campaign_id', '=', vals['campaign_id'])
            ],
            vals
        )
