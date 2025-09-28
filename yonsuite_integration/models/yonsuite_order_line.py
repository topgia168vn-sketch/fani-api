# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class YonsuiteOrderLine(models.Model):
    _name = 'yonsuite.order.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Order Line'
    _order = 'id'

    yonsuite_id = fields.Char(
        string='YonSuite Line ID',
        readonly=True,
        copy=False,
        help='Line ID from YonSuite API'
    )
    
    order_id = fields.Many2one(
        'yonsuite.order',
        string='Order',
        required=True,
        ondelete='cascade',
        help='Related YonSuite Order'
    )
    
    # Product information
    product_id = fields.Many2one(
        'yonsuite.product',
        string='Product',
        help='Related YonSuite Product'
    )
    
    childs_product_id = fields.Char(
        string='Product ID',
        help='Product ID from YonSuite'
    )
    
    childs_product_id_code = fields.Char(
        string='Product Code',
        help='Product code from YonSuite'
    )
    
    childs_product_id_name = fields.Char(
        string='Product Name',
        help='Product name from YonSuite'
    )
    
    childs_product_id_model = fields.Char(
        string='Product Model',
        help='Product model from YonSuite'
    )
    
    childs_product_id_model_description = fields.Char(
        string='Product Model Description',
        help='Product model description from YonSuite'
    )
    
    # SKU information
    childs_sku_id = fields.Char(
        string='SKU ID',
        help='SKU ID from YonSuite'
    )
    
    childs_sku_id_code = fields.Char(
        string='SKU Code',
        help='SKU code from YonSuite'
    )
    
    childs_sku_id_name = fields.Char(
        string='SKU Name',
        help='SKU name from YonSuite'
    )
    
    childs_sku_id_model = fields.Char(
        string='SKU Model',
        help='SKU model from YonSuite'
    )
    
    childs_sku_id_model_description = fields.Char(
        string='SKU Model Description',
        help='SKU model description from YonSuite'
    )
    
    # Product class
    childs_product_class = fields.Char(
        string='Product Class',
        help='Product class from YonSuite'
    )
    
    childs_product_class_code = fields.Char(
        string='Product Class Code',
        help='Product class code from YonSuite'
    )
    
    childs_product_class_name = fields.Char(
        string='Product Class Name',
        help='Product class name from YonSuite'
    )
    
    # Project information
    childs_project_id = fields.Char(
        string='Project ID',
        help='Project ID from YonSuite'
    )
    
    childs_project_id_code = fields.Char(
        string='Project Code',
        help='Project code from YonSuite'
    )
    
    childs_project_id_name = fields.Char(
        string='Project Name',
        help='Project name from YonSuite'
    )
    
    # Unit information
    childs_master_unit_id = fields.Char(
        string='Master Unit ID',
        help='Master unit ID from YonSuite'
    )
    
    childs_master_unit_id_name = fields.Char(
        string='Master Unit Name',
        help='Master unit name from YonSuite'
    )
    
    childs_master_unit_id_precision = fields.Integer(
        string='Master Unit Precision',
        help='Master unit precision from YonSuite'
    )
    
    childs_sale_unit_id = fields.Char(
        string='Sale Unit ID',
        help='Sale unit ID from YonSuite'
    )
    
    childs_sale_unit_id_name = fields.Char(
        string='Sale Unit Name',
        help='Sale unit name from YonSuite'
    )
    
    childs_sale_unit_id_precision = fields.Integer(
        string='Sale Unit Precision',
        help='Sale unit precision from YonSuite'
    )
    
    childs_cqt_unit_id = fields.Char(
        string='CQT Unit ID',
        help='CQT unit ID from YonSuite'
    )
    
    childs_cqt_unit_id_name = fields.Char(
        string='CQT Unit Name',
        help='CQT unit name from YonSuite'
    )
    
    childs_cqt_unit_id_precision = fields.Integer(
        string='CQT Unit Precision',
        help='CQT unit precision from YonSuite'
    )
    
    # Quantity
    childs_qty = fields.Float(
        string='Quantity',
        digits='Product Unit of Measure',
        help='Quantity from YonSuite'
    )
    
    childs_sub_qty = fields.Float(
        string='Sub Quantity',
        digits='Product Unit of Measure',
        help='Sub quantity from YonSuite'
    )
    
    childs_price_qty = fields.Float(
        string='Price Quantity',
        digits='Product Unit of Measure',
        help='Price quantity from YonSuite'
    )
    
    # Price information
    childs_ori_unit_price = fields.Float(
        string='Original Unit Price',
        digits='Product Price',
        help='Original unit price from YonSuite'
    )
    
    childs_ori_tax_unit_price = fields.Float(
        string='Original Tax Unit Price',
        digits='Product Price',
        help='Original tax unit price from YonSuite'
    )
    
    childs_nat_unit_price = fields.Float(
        string='Native Unit Price',
        digits='Product Price',
        help='Native unit price from YonSuite'
    )
    
    childs_nat_tax_unit_price = fields.Float(
        string='Native Tax Unit Price',
        digits='Product Price',
        help='Native tax unit price from YonSuite'
    )
    
    childs_quote_sale_price = fields.Float(
        string='Quote Sale Price',
        digits='Product Price',
        help='Quote sale price from YonSuite'
    )
    
    # Money fields
    childs_ori_money = fields.Float(
        string='Original Money',
        digits='Product Price',
        help='Original money from YonSuite'
    )
    
    childs_ori_sum = fields.Float(
        string='Original Sum',
        digits='Product Price',
        help='Original sum from YonSuite'
    )
    
    childs_nat_money = fields.Float(
        string='Native Money',
        digits='Product Price',
        help='Native money from YonSuite'
    )
    
    childs_nat_sum = fields.Float(
        string='Native Sum',
        digits='Product Price',
        help='Native sum from YonSuite'
    )
    
    # Discount
    childs_discount_rate = fields.Float(
        string='Discount Rate',
        digits='Product Price',
        help='Discount rate from YonSuite'
    )
    
    childs_discount_sum = fields.Float(
        string='Discount Sum',
        digits='Product Price',
        help='Discount sum from YonSuite'
    )
    
    childs_discount_nat_sum = fields.Float(
        string='Discount Native Sum',
        digits='Product Price',
        help='Discount native sum from YonSuite'
    )
    
    childs_favorable_rate = fields.Float(
        string='Favorable Rate',
        digits='Product Price',
        help='Favorable rate from YonSuite'
    )
    
    childs_cus_favorable_rate = fields.Float(
        string='Customer Favorable Rate',
        digits='Product Price',
        help='Customer favorable rate from YonSuite'
    )
    
    # Tax
    childs_tax_rate = fields.Float(
        string='Tax Rate',
        digits='Product Price',
        help='Tax rate from YonSuite'
    )
    
    # Cost information
    childs_quote_sale_cost = fields.Float(
        string='Quote Sale Cost',
        digits='Product Price',
        help='Quote sale cost from YonSuite'
    )
    
    childs_forecast_cb_price = fields.Float(
        string='Forecast CB Price',
        digits='Product Price',
        help='Forecast CB price from YonSuite'
    )
    
    childs_forecast_cb_price_sum = fields.Float(
        string='Forecast CB Price Sum',
        digits='Product Price',
        help='Forecast CB price sum from YonSuite'
    )
    
    # Cost currency
    childs_cost_currency = fields.Char(
        string='Cost Currency',
        help='Cost currency from YonSuite'
    )
    
    childs_cost_currency_name = fields.Char(
        string='Cost Currency Name',
        help='Cost currency name from YonSuite'
    )
    
    # Settlement organization
    childs_settlement_org_id = fields.Char(
        string='Settlement Organization ID',
        help='Settlement organization ID from YonSuite'
    )
    
    childs_settlement_org_id_name = fields.Char(
        string='Settlement Organization Name',
        help='Settlement organization name from YonSuite'
    )
    
    # Push quantities
    childs_total_push_sact_qty = fields.Float(
        string='Total Push SACT Quantity',
        digits='Product Unit of Measure',
        help='Total push SACT quantity from YonSuite'
    )
    
    childs_total_push_sale_qty = fields.Float(
        string='Total Push Sale Quantity',
        digits='Product Unit of Measure',
        help='Total push sale quantity from YonSuite'
    )
    
    # Quotation fields
    childs_price_mark = fields.Char(
        string='Price Mark',
        help='Price mark from YonSuite'
    )
    
    childs_quotation_exclusive_tax_money = fields.Float(
        string='Quotation Exclusive Tax Money',
        digits='Product Price',
        help='Quotation exclusive tax money from YonSuite'
    )
    
    childs_basic_quotation = fields.Float(
        string='Basic Quotation',
        digits='Product Price',
        help='Basic quotation from YonSuite'
    )
    
    childs_basic_quotation_money = fields.Float(
        string='Basic Quotation Money',
        digits='Product Price',
        help='Basic quotation money from YonSuite'
    )
    
    childs_quotation_deduction_rate = fields.Float(
        string='Quotation Deduction Rate',
        digits='Product Price',
        help='Quotation deduction rate from YonSuite'
    )
    
    childs_quotation_deduction = fields.Float(
        string='Quotation Deduction',
        digits='Product Price',
        help='Quotation deduction from YonSuite'
    )
    
    childs_lowest_selline_price = fields.Float(
        string='Lowest Selline Price',
        digits='Product Price',
        help='Lowest selline price from YonSuite'
    )

    @api.model
    def _update_product_relation(self):
        """
        Update product relation based on childs_product_id
        """
        for line in self:
            if line.childs_product_id and not line.product_id:
                product = self.env['yonsuite.product'].search([
                    ('yonsuite_id', '=', line.childs_product_id)
                ], limit=1)
                if product:
                    line.product_id = product.id
