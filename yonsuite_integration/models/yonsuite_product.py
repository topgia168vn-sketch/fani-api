# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time

_logger = logging.getLogger(__name__)


class YonsuiteProduct(models.Model):
    _name = 'yonsuite.product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Product'
    _order = 'create_date desc'

    name = fields.Char(
        string='Product Name',
        required=True,
        help='Name of the product'
    )

    yonsuite_id = fields.Char(
        string='YonSuite Product ID',
        readonly=True,
        copy=False,
        help='Product ID from YonSuite API'
    )

    code = fields.Char(
        string='Product Code',
        help='Product code from YonSuite'
    )

    # Basic product info
    trans_type = fields.Char(
        string='Transaction Type',
        help='Transaction type from YonSuite'
    )

    # Unit information
    yonsuite_unit_id = fields.Many2one(
        'yonsuite.unit',
        string='YonSuite Unit',
        help='Unit from YonSuite'
    )

    unit_id = fields.Char(
        string='Unit ID',
        readonly=True,
        help='Unit ID from YonSuite'
    )

    unit_code = fields.Char(
        string='Unit Code',
        readonly=True,
        help='Unit code from YonSuite'
    )

    unit_name = fields.Char(
        string='Unit Name',
        readonly=True,
        help='Unit name from YonSuite'
    )

    unit_use_type = fields.Integer(
        string='Unit Use Type',
        help='Unit use type from YonSuite'
    )

    # Product character definition
    product_character_def_id = fields.Char(
        string='Product Character Def ID',
        help='Product character definition ID from YonSuite'
    )

    # Management class
    yonsuite_management_class_id = fields.Many2one(
        'yonsuite.management.class',
        string='YonSuite Management Class',
        help='Management class from YonSuite'
    )

    manage_class = fields.Char(
        string='Manage Class',
        help='Management class from YonSuite'
    )

    manage_class_code = fields.Char(
        string='Manage Class Code',
        help='Management class code from YonSuite'
    )

    manage_class_name = fields.Char(
        string='Manage Class Name',
        help='Management class name from YonSuite'
    )

    # Sale product class
    yonsuite_sale_class_id = fields.Many2one(
        'yonsuite.sale.class',
        string='YonSuite Sale Class',
        help='Sale class from YonSuite'
    )

    sale_product_class = fields.Char(
        string='Sale Product Class',
        help='Sale product class from YonSuite'
    )

    sale_product_class_code = fields.Char(
        string='Sale Product Class Code',
        help='Sale product class code from YonSuite'
    )

    sale_product_class_name = fields.Char(
        string='Sale Product Class Name',
        help='Sale product class name from YonSuite'
    )

    # Purchase class
    yonsuite_purchase_class_id = fields.Many2one(
        'yonsuite.purchase.class',
        string='YonSuite Purchase Class',
        help='Purchase class from YonSuite'
    )

    purchase_class = fields.Char(
        string='Purchase Class',
        help='Purchase class from YonSuite'
    )

    purchase_class_code = fields.Char(
        string='Purchase Class Code',
        help='Purchase class code from YonSuite'
    )

    purchase_class_name = fields.Char(
        string='Purchase Class Name',
        help='Purchase class name from YonSuite'
    )

    # Product template
    product_template = fields.Char(
        string='Product Template',
        help='Product template from YonSuite'
    )

    product_template_name = fields.Char(
        string='Product Template Name',
        help='Product template name from YonSuite'
    )

    # Product family and operations
    product_family = fields.Integer(
        string='Product Family',
        help='Product family from YonSuite'
    )

    sales_and_operations = fields.Integer(
        string='Sales and Operations',
        help='Sales and operations from YonSuite'
    )

    # Medical fields
    med_is_registration_manager = fields.Boolean(
        string='Medical Registration Manager',
        help='Medical registration manager flag from YonSuite'
    )

    med_is_authorization_manager = fields.Boolean(
        string='Medical Authorization Manager',
        help='Medical authorization manager flag from YonSuite'
    )

    # Product specifications
    has_specs = fields.Boolean(
        string='Has Specifications',
        help='Whether product has specifications from YonSuite'
    )

    # Product URL
    url = fields.Char(
        string='Product URL',
        help='Product URL from YonSuite'
    )

    # Status
    stop_status = fields.Boolean(
        string='Stop Status',
        help='Stop status from YonSuite'
    )

    # Product attributes
    real_product_attribute = fields.Text(
        string='Real Product Attribute',
        help='Real product attribute from YonSuite'
    )

    real_product_attribute_type = fields.Text(
        string='Real Product Attribute Type',
        help='Real product attribute type from YonSuite'
    )

    virtual_product_attribute = fields.Text(
        string='Virtual Product Attribute',
        help='Virtual product attribute from YonSuite'
    )

    # Organization info
    yonsuite_getallorgdept_id = fields.Many2one(
        'yonsuite.getallorgdept',
        string='YonSuite Organization/Department',
        help='Organization/Department from YonSuite'
    )

    create_org_id = fields.Char(
        string='Create Organization ID',
        readonly=True,
        help='Create organization ID from YonSuite'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this product was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    # Additional fields from product detail API
    url = fields.Char(
        string='Product URL',
        help='Product URL from YonSuite'
    )

    platform_code = fields.Char(
        string='Platform Code',
        help='Platform code from YonSuite'
    )

    product_line = fields.Char(
        string='Product Line',
        help='Product line from YonSuite'
    )

    product_line_code = fields.Char(
        string='Product Line Code',
        help='Product line code from YonSuite'
    )

    product_line_name = fields.Char(
        string='Product Line Name',
        help='Product line name from YonSuite'
    )

    brand = fields.Char(
        string='Brand',
        help='Brand from YonSuite'
    )

    brand_code = fields.Char(
        string='Brand Code',
        help='Brand code from YonSuite'
    )

    brand_name = fields.Char(
        string='Brand Name',
        help='Brand name from YonSuite'
    )

    place_of_origin = fields.Char(
        string='Place of Origin',
        help='Place of origin from YonSuite'
    )

    manufacturer = fields.Char(
        string='Manufacturer',
        help='Manufacturer from YonSuite'
    )

    platform_status = fields.Char(
        string='Platform Status',
        help='Platform status from YonSuite'
    )

    platform_remark = fields.Text(
        string='Platform Remark',
        help='Platform remark from YonSuite'
    )

    gift_card_id = fields.Char(
        string='Gift Card ID',
        help='Gift card ID from YonSuite'
    )

    gift_card_name = fields.Char(
        string='Gift Card Name',
        help='Gift card name from YonSuite'
    )

    coupon_id = fields.Char(
        string='Coupon ID',
        help='Coupon ID from YonSuite'
    )

    coupon_type = fields.Char(
        string='Coupon Type',
        help='Coupon type from YonSuite'
    )

    coupon_name = fields.Char(
        string='Coupon Name',
        help='Coupon name from YonSuite'
    )

    weight = fields.Float(
        string='Weight',
        help='Weight from YonSuite'
    )

    weight_unit = fields.Char(
        string='Weight Unit',
        help='Weight unit from YonSuite'
    )

    weight_unit_name = fields.Char(
        string='Weight Unit Name',
        help='Weight unit name from YonSuite'
    )

    volume = fields.Float(
        string='Volume',
        help='Volume from YonSuite'
    )

    volume_unit = fields.Char(
        string='Volume Unit',
        help='Volume unit from YonSuite'
    )

    volume_unit_name = fields.Char(
        string='Volume Unit Name',
        help='Volume unit name from YonSuite'
    )

    tax_class = fields.Char(
        string='Tax Class',
        help='Tax class from YonSuite'
    )

    tax_class_code = fields.Char(
        string='Tax Class Code',
        help='Tax class code from YonSuite'
    )

    tax_class_name = fields.Char(
        string='Tax Class Name',
        help='Tax class name from YonSuite'
    )

    creator = fields.Char(
        string='Creator',
        help='Creator from YonSuite'
    )

    create_date = fields.Date(
        string='Create Date',
        help='Create date from YonSuite'
    )

    create_time = fields.Datetime(
        string='Create Time',
        help='Create time from YonSuite'
    )

    modifier = fields.Char(
        string='Modifier',
        help='Modifier from YonSuite'
    )

    modify_time = fields.Datetime(
        string='Modify Time',
        help='Modify time from YonSuite'
    )

    modify_date = fields.Date(
        string='Modify Date',
        help='Modify date from YonSuite'
    )

    customer_service_day = fields.Integer(
        string='Customer Service Day',
        help='Customer service day from YonSuite'
    )

    dimension_code = fields.Char(
        string='Dimension Code',
        help='Dimension code from YonSuite'
    )

    # Detail fields
    exemption = fields.Boolean(
        string='Exemption',
        help='Exemption from YonSuite detail'
    )

    warehousing_by_result = fields.Char(
        string='Warehousing By Result',
        help='Warehousing by result from YonSuite detail'
    )

    sales_returns_exemption = fields.Char(
        string='Sales Returns Exemption',
        help='Sales returns exemption from YonSuite detail'
    )

    returns_warehousing_by_result = fields.Char(
        string='Returns Warehousing By Result',
        help='Returns warehousing by result from YonSuite detail'
    )

    periodical_inspection = fields.Char(
        string='Periodical Inspection',
        help='Periodical inspection from YonSuite detail'
    )

    periodical_inspection_cycle = fields.Integer(
        string='Periodical Inspection Cycle',
        help='Periodical inspection cycle from YonSuite detail'
    )

    short_name = fields.Char(
        string='Short Name',
        help='Short name from YonSuite detail'
    )

    mnemonic_code = fields.Char(
        string='Mnemonic Code',
        help='Mnemonic code from YonSuite detail'
    )

    bar_code = fields.Char(
        string='Bar Code',
        help='Bar code from YonSuite detail'
    )

    business_attribute = fields.Char(
        string='Business Attribute',
        help='Business attribute from YonSuite detail'
    )

    sale_channel = fields.Char(
        string='Sale Channel',
        help='Sale channel from YonSuite detail'
    )

    product_apply_range_id = fields.Char(
        string='Product Apply Range ID',
        help='Product apply range ID from YonSuite detail'
    )

    purchase_unit_name = fields.Char(
        string='Purchase Unit Name',
        help='Purchase unit name from YonSuite detail'
    )

    purchase_price_unit_name = fields.Char(
        string='Purchase Price Unit Name',
        help='Purchase price unit name from YonSuite detail'
    )

    stock_unit_name = fields.Char(
        string='Stock Unit Name',
        help='Stock unit name from YonSuite detail'
    )

    produce_unit_name = fields.Char(
        string='Produce Unit Name',
        help='Produce unit name from YonSuite detail'
    )

    batch_price_unit_name = fields.Char(
        string='Batch Price Unit Name',
        help='Batch price unit name from YonSuite detail'
    )

    batch_unit_name = fields.Char(
        string='Batch Unit Name',
        help='Batch unit name from YonSuite detail'
    )

    online_unit_name = fields.Char(
        string='Online Unit Name',
        help='Online unit name from YonSuite detail'
    )

    offline_unit_name = fields.Char(
        string='Offline Unit Name',
        help='Offline unit name from YonSuite detail'
    )

    require_unit_name = fields.Char(
        string='Require Unit Name',
        help='Require unit name from YonSuite detail'
    )

    batch_price = fields.Float(
        string='Batch Price',
        help='Batch price from YonSuite detail'
    )

    f_mark_price = fields.Float(
        string='Mark Price',
        help='Mark price from YonSuite detail'
    )

    f_lowest_mark_price = fields.Float(
        string='Lowest Mark Price',
        help='Lowest mark price from YonSuite detail'
    )

    f_sale_price = fields.Float(
        string='Sale Price',
        help='Sale price from YonSuite detail'
    )

    f_market_price = fields.Float(
        string='Market Price',
        help='Market price from YonSuite detail'
    )

    is_display_price = fields.Boolean(
        string='Is Display Price',
        help='Is display price from YonSuite detail'
    )

    price_area_message = fields.Char(
        string='Price Area Message',
        help='Price area message from YonSuite detail'
    )

    receipt_name_zh_cn = fields.Char(
        string='Receipt Name (Chinese)',
        help='Receipt name in Chinese from YonSuite detail'
    )

    receipt_name_en_us = fields.Char(
        string='Receipt Name (English)',
        help='Receipt name in English from YonSuite detail'
    )

    receipt_name_zh_tw = fields.Char(
        string='Receipt Name (Traditional)',
        help='Receipt name in Traditional Chinese from YonSuite detail'
    )

    in_taxrate = fields.Char(
        string='In Tax Rate',
        help='In tax rate from YonSuite detail'
    )

    in_taxrate_name = fields.Char(
        string='In Tax Rate Name',
        help='In tax rate name from YonSuite detail'
    )

    out_taxrate = fields.Char(
        string='Out Tax Rate',
        help='Out tax rate from YonSuite detail'
    )

    out_taxrate_name = fields.Char(
        string='Out Tax Rate Name',
        help='Out tax rate name from YonSuite detail'
    )

    preferential_policy_type = fields.Char(
        string='Preferential Policy Type',
        help='Preferential policy type from YonSuite detail'
    )

    preferential_policy_type_name = fields.Char(
        string='Preferential Policy Type Name',
        help='Preferential policy type name from YonSuite detail'
    )

    i_order = fields.Integer(
        string='Order',
        help='Order from YonSuite detail'
    )

    i_status = fields.Boolean(
        string='Status',
        help='Status from YonSuite detail'
    )

    mall_up_time = fields.Char(
        string='Mall Up Time',
        help='Mall up time from YonSuite detail'
    )

    i_u_order_status = fields.Boolean(
        string='U Order Status',
        help='U order status from YonSuite detail'
    )

    uorder_up_time = fields.Char(
        string='UOrder Up Time',
        help='UOrder up time from YonSuite detail'
    )

    product_vendor = fields.Char(
        string='Product Vendor',
        help='Product vendor from YonSuite detail'
    )

    product_vendor_name = fields.Char(
        string='Product Vendor Name',
        help='Product vendor name from YonSuite detail'
    )

    product_buyer = fields.Char(
        string='Product Buyer',
        help='Product buyer from YonSuite detail'
    )

    product_buyer_name = fields.Char(
        string='Product Buyer Name',
        help='Product buyer name from YonSuite detail'
    )

    f_prime_costs = fields.Float(
        string='Prime Costs',
        help='Prime costs from YonSuite detail'
    )

    max_prime_costs = fields.Float(
        string='Max Prime Costs',
        help='Max prime costs from YonSuite detail'
    )

    request_order_limit = fields.Float(
        string='Request Order Limit',
        help='Request order limit from YonSuite detail'
    )

    can_sale = fields.Boolean(
        string='Can Sale',
        help='Can sale from YonSuite detail'
    )

    i_min_order_quantity = fields.Float(
        string='Min Order Quantity',
        help='Min order quantity from YonSuite detail'
    )

    delivery_days = fields.Integer(
        string='Delivery Days',
        help='Delivery days from YonSuite detail'
    )

    uorder_dly_fee_rule_id = fields.Char(
        string='UOrder Dly Fee Rule ID',
        help='UOrder dly fee rule ID from YonSuite detail'
    )

    uorder_dly_fee_rule_id_name = fields.Char(
        string='UOrder Dly Fee Rule ID Name',
        help='UOrder dly fee rule ID name from YonSuite detail'
    )

    be_up_time = fields.Char(
        string='Be Up Time',
        help='Be up time from YonSuite detail'
    )

    is_batch_manage = fields.Boolean(
        string='Is Batch Manage',
        help='Is batch manage from YonSuite detail'
    )

    is_expiry_date_manage = fields.Boolean(
        string='Is Expiry Date Manage',
        help='Is expiry date manage from YonSuite detail'
    )

    expire_date_no = fields.Integer(
        string='Expire Date No',
        help='Expire date no from YonSuite detail'
    )

    expire_date_unit = fields.Char(
        string='Expire Date Unit',
        help='Expire date unit from YonSuite detail'
    )

    days_before_validity_reject = fields.Integer(
        string='Days Before Validity Reject',
        help='Days before validity reject from YonSuite detail'
    )

    validity_warning_days = fields.Integer(
        string='Validity Warning Days',
        help='Validity warning days from YonSuite detail'
    )

    is_serial_no_manage = fields.Boolean(
        string='Is Serial No Manage',
        help='Is serial no manage from YonSuite detail'
    )

    is_barcode_manage = fields.Boolean(
        string='Is Barcode Manage',
        help='Is barcode manage from YonSuite detail'
    )

    safety_stock = fields.Float(
        string='Safety Stock',
        help='Safety stock from YonSuite detail'
    )

    highest_stock = fields.Float(
        string='Highest Stock',
        help='Highest stock from YonSuite detail'
    )

    lowest_stock = fields.Float(
        string='Lowest Stock',
        help='Lowest stock from YonSuite detail'
    )

    rop_stock = fields.Float(
        string='ROP Stock',
        help='ROP stock from YonSuite detail'
    )

    warehouse_manager = fields.Char(
        string='Warehouse Manager',
        help='Warehouse manager from YonSuite detail'
    )

    warehouse_manager_name = fields.Char(
        string='Warehouse Manager Name',
        help='Warehouse manager name from YonSuite detail'
    )

    delivery_warehouse = fields.Char(
        string='Delivery Warehouse',
        help='Delivery warehouse from YonSuite detail'
    )

    delivery_warehouse_name = fields.Char(
        string='Delivery Warehouse Name',
        help='Delivery warehouse name from YonSuite detail'
    )

    return_warehouse = fields.Char(
        string='Return Warehouse',
        help='Return warehouse from YonSuite detail'
    )

    return_warehouse_name = fields.Char(
        string='Return Warehouse Name',
        help='Return warehouse name from YonSuite detail'
    )

    in_store_excess_limit = fields.Float(
        string='In Store Excess Limit',
        help='In store excess limit from YonSuite detail'
    )

    out_store_excess_limit = fields.Float(
        string='Out Store Excess Limit',
        help='Out store excess limit from YonSuite detail'
    )

    storage_loss_rate = fields.Float(
        string='Storage Loss Rate',
        help='Storage loss rate from YonSuite detail'
    )

    plan_default_attribute = fields.Char(
        string='Plan Default Attribute',
        help='Plan default attribute from YonSuite detail'
    )

    allow_negative_inventory = fields.Boolean(
        string='Allow Negative Inventory',
        help='Allow negative inventory from YonSuite detail'
    )

    plan_method = fields.Char(
        string='Plan Method',
        help='Plan method from YonSuite detail'
    )

    plan_strategy = fields.Char(
        string='Plan Strategy',
        help='Plan strategy from YonSuite detail'
    )

    plan_strategy_name = fields.Char(
        string='Plan Strategy Name',
        help='Plan strategy name from YonSuite detail'
    )

    key_sub_part = fields.Boolean(
        string='Key Sub Part',
        help='Key sub part from YonSuite detail'
    )

    bind_carrier = fields.Boolean(
        string='Bind Carrier',
        help='Bind carrier from YonSuite detail'
    )

    purpose = fields.Char(
        string='Purpose',
        help='Purpose from YonSuite detail'
    )

    utility = fields.Char(
        string='Utility',
        help='Utility from YonSuite detail'
    )

    supply_demand_policy = fields.Char(
        string='Supply Demand Policy',
        help='Supply demand policy from YonSuite detail'
    )

    fixed_lead_time = fields.Integer(
        string='Fixed Lead Time',
        help='Fixed lead time from YonSuite detail'
    )

    batch_policy = fields.Integer(
        string='Batch Policy',
        help='Batch policy from YonSuite detail'
    )

    supply_type = fields.Integer(
        string='Supply Type',
        help='Supply type from YonSuite detail'
    )

    produce_department = fields.Char(
        string='Produce Department',
        help='Produce department from YonSuite detail'
    )

    produce_department_name = fields.Char(
        string='Produce Department Name',
        help='Produce department name from YonSuite detail'
    )

    manufacture_planner = fields.Char(
        string='Manufacture Planner',
        help='Manufacture planner from YonSuite detail'
    )

    manufacture_planner_name = fields.Char(
        string='Manufacture Planner Name',
        help='Manufacture planner name from YonSuite detail'
    )

    engineering_drawing_no = fields.Char(
        string='Engineering Drawing No',
        help='Engineering drawing no from YonSuite detail'
    )

    supply_times = fields.Integer(
        string='Supply Times',
        help='Supply times from YonSuite detail'
    )

    plan_produce_limit = fields.Float(
        string='Plan Produce Limit',
        help='Plan produce limit from YonSuite detail'
    )

    weigh = fields.Boolean(
        string='Weigh',
        help='Weigh from YonSuite detail'
    )

    value_manage_type = fields.Char(
        string='Value Manage Type',
        help='Value manage type from YonSuite detail'
    )

    cost_valuation = fields.Char(
        string='Cost Valuation',
        help='Cost valuation from YonSuite detail'
    )

    check_by_cost = fields.Boolean(
        string='Check By Cost',
        help='Check by cost from YonSuite detail'
    )

    f_no_tax_cost_price = fields.Float(
        string='No Tax Cost Price',
        help='No tax cost price from YonSuite detail'
    )

    check_by_batch = fields.Boolean(
        string='Check By Batch',
        help='Check by batch from YonSuite detail'
    )

    accounting_by_item = fields.Boolean(
        string='Accounting By Item',
        help='Accounting by item from YonSuite detail'
    )

    material_cost = fields.Boolean(
        string='Material Cost',
        help='Material cost from YonSuite detail'
    )

    is_check_free = fields.Integer(
        string='Is Check Free',
        help='Is check free from YonSuite detail'
    )

    sale_style = fields.Char(
        string='Sale Style',
        help='Sale style from YonSuite detail'
    )

    sale_points = fields.Float(
        string='Sale Points',
        help='Sale points from YonSuite detail'
    )

    l_inventory_count = fields.Float(
        string='Inventory Count',
        help='Inventory count from YonSuite detail'
    )

    i_base_sale_count = fields.Float(
        string='Base Sale Count',
        help='Base sale count from YonSuite detail'
    )

    dly_fee_rule_id = fields.Char(
        string='Dly Fee Rule ID',
        help='Dly fee rule ID from YonSuite detail'
    )

    dly_fee_rule_id_name = fields.Char(
        string='Dly Fee Rule ID Name',
        help='Dly fee rule ID name from YonSuite detail'
    )

    meta_description_zh_cn = fields.Char(
        string='Meta Description (Chinese)',
        help='Meta description in Chinese from YonSuite detail'
    )

    meta_description_en_us = fields.Char(
        string='Meta Description (English)',
        help='Meta description in English from YonSuite detail'
    )

    meta_description_zh_tw = fields.Char(
        string='Meta Description (Traditional)',
        help='Meta description in Traditional Chinese from YonSuite detail'
    )

    enable_subscribe = fields.Boolean(
        string='Enable Subscribe',
        help='Enable subscribe from YonSuite detail'
    )

    enable_deposit = fields.Boolean(
        string='Enable Deposit',
        help='Enable deposit from YonSuite detail'
    )

    deposit_deal_pay_type = fields.Integer(
        string='Deposit Deal Pay Type',
        help='Deposit deal pay type from YonSuite detail'
    )

    deposits = fields.Float(
        string='Deposits',
        help='Deposits from YonSuite detail'
    )

    deposit_percentage = fields.Float(
        string='Deposit Percentage',
        help='Deposit percentage from YonSuite detail'
    )

    enable_modify_deposit = fields.Boolean(
        string='Enable Modify Deposit',
        help='Enable modify deposit from YonSuite detail'
    )

    minimum_deposits = fields.Float(
        string='Minimum Deposits',
        help='Minimum deposits from YonSuite detail'
    )

    deposit_pay_type = fields.Integer(
        string='Deposit Pay Type',
        help='Deposit pay type from YonSuite detail'
    )

    service_duration = fields.Integer(
        string='Service Duration',
        help='Service duration from YonSuite detail'
    )

    service_duration_unit = fields.Integer(
        string='Service Duration Unit',
        help='Service duration unit from YonSuite detail'
    )

    can_order = fields.Boolean(
        string='Can Order',
        help='Can order from YonSuite detail'
    )

    only_order = fields.Boolean(
        string='Only Order',
        help='Only order from YonSuite detail'
    )

    order_advance_time = fields.Integer(
        string='Order Advance Time',
        help='Order advance time from YonSuite detail'
    )

    i_enable_cycle_purchase = fields.Boolean(
        string='Enable Cycle Purchase',
        help='Enable cycle purchase from YonSuite detail'
    )

    f_settle_accounts_rate = fields.Float(
        string='Settle Accounts Rate',
        help='Settle accounts rate from YonSuite detail'
    )

    is_all_area = fields.Boolean(
        string='Is All Area',
        help='Is all area from YonSuite detail'
    )

    i_enable_econtract = fields.Boolean(
        string='Enable Econtract',
        help='Enable econtract from YonSuite detail'
    )

    page_title = fields.Char(
        string='Page Title',
        help='Page title from YonSuite detail'
    )

    is_recommend = fields.Boolean(
        string='Is Recommend',
        help='Is recommend from YonSuite detail'
    )

    display_name_zh_cn = fields.Char(
        string='Display Name (Chinese)',
        help='Display name in Chinese from YonSuite detail'
    )

    display_name_en_us = fields.Char(
        string='Display Name (English)',
        help='Display name in English from YonSuite detail'
    )

    display_name_zh_tw = fields.Char(
        string='Display Name (Traditional)',
        help='Display name in Traditional Chinese from YonSuite detail'
    )

    title_memo_zh_cn = fields.Char(
        string='Title Memo (Chinese)',
        help='Title memo in Chinese from YonSuite detail'
    )

    title_memo_en_us = fields.Char(
        string='Title Memo (English)',
        help='Title memo in English from YonSuite detail'
    )

    title_memo_zh_tw = fields.Char(
        string='Title Memo (Traditional)',
        help='Title memo in Traditional Chinese from YonSuite detail'
    )

    allow_store_purchase = fields.Boolean(
        string='Allow Store Purchase',
        help='Allow store purchase from YonSuite detail'
    )

    is_sale_in_offline_store = fields.Boolean(
        string='Is Sale In Offline Store',
        help='Is sale in offline store from YonSuite detail'
    )

    is_price_change_allowed = fields.Boolean(
        string='Is Price Change Allowed',
        help='Is price change allowed from YonSuite detail'
    )

    is_offline_store_order = fields.Boolean(
        string='Is Offline Store Order',
        help='Is offline store order from YonSuite detail'
    )

    is_offline_store_return = fields.Boolean(
        string='Is Offline Store Return',
        help='Is offline store return from YonSuite detail'
    )

    retail_price_dimension = fields.Integer(
        string='Retail Price Dimension',
        help='Retail price dimension from YonSuite detail'
    )

    deliver_quantity_change = fields.Integer(
        string='Deliver Quantity Change',
        help='Deliver quantity change from YonSuite detail'
    )

    is_process = fields.Boolean(
        string='Is Process',
        help='Is process from YonSuite detail'
    )

    process_type = fields.Char(
        string='Process Type',
        help='Process type from YonSuite detail'
    )

    is_material = fields.Boolean(
        string='Is Material',
        help='Is material from YonSuite detail'
    )

    is_weight = fields.Boolean(
        string='Is Weight',
        help='Is weight from YonSuite detail'
    )

    # Additional fields from new API response format
    default_sku_id = fields.Char(
        string='Default SKU ID',
        help='Default SKU ID from YonSuite'
    )

    tenant = fields.Char(
        string='Tenant',
        help='Tenant from YonSuite'
    )

    deleted = fields.Boolean(
        string='Deleted',
        help='Deleted flag from YonSuite'
    )

    creator_id = fields.Char(
        string='Creator ID',
        help='Creator ID from YonSuite'
    )

    modifier_id = fields.Char(
        string='Modifier ID',
        help='Modifier ID from YonSuite'
    )

    name1 = fields.Char(
        string='Name 1',
        help='Name 1 from YonSuite'
    )

    name4 = fields.Char(
        string='Name 4',
        help='Name 4 from YonSuite'
    )

    registration_manager = fields.Boolean(
        string='Registration Manager',
        help='Registration manager from YonSuite'
    )

    authorization_manager = fields.Boolean(
        string='Authorization Manager',
        help='Authorization manager from YonSuite'
    )

    ytenant_id = fields.Char(
        string='YTenant ID',
        help='YTenant ID from YonSuite'
    )

    trans_type_code = fields.Char(
        string='Transaction Type Code',
        help='Transaction type code from YonSuite'
    )

    trans_type_name = fields.Char(
        string='Transaction Type Name',
        help='Transaction type name from YonSuite'
    )

    shop = fields.Integer(
        string='Shop',
        help='Shop from YonSuite'
    )

    source = fields.Integer(
        string='Source',
        help='Source from YonSuite'
    )

    use_sku = fields.Integer(
        string='Use SKU',
        help='Use SKU from YonSuite'
    )

    # Product Organizations relationship
    product_orges_ids = fields.One2many(
        'yonsuite.product.orges',
        'product_id',
        string='Product Organizations',
        help='Organizations associated with this product'
    )

    # Additional multilingual fields from object responses
    model_description_zh_cn = fields.Char(
        string='Model Description (Chinese)',
        help='Model description in Chinese from YonSuite'
    )

    model_description_en_us = fields.Char(
        string='Model Description (English)',
        help='Model description in English from YonSuite'
    )

    model_description_zh_tw = fields.Char(
        string='Model Description (Traditional)',
        help='Model description in Traditional Chinese from YonSuite'
    )

    model_zh_cn = fields.Char(
        string='Model (Chinese)',
        help='Model in Chinese from YonSuite'
    )

    model_en_us = fields.Char(
        string='Model (English)',
        help='Model in English from YonSuite'
    )

    model_zh_tw = fields.Char(
        string='Model (Traditional)',
        help='Model in Traditional Chinese from YonSuite'
    )

    keywords_zh_cn = fields.Char(
        string='Keywords (Chinese)',
        help='Keywords in Chinese from YonSuite'
    )

    keywords_en_us = fields.Char(
        string='Keywords (English)',
        help='Keywords in English from YonSuite'
    )

    keywords_zh_tw = fields.Char(
        string='Keywords (Traditional)',
        help='Keywords in Traditional Chinese from YonSuite'
    )

    share_description_zh_cn = fields.Char(
        string='Share Description (Chinese)',
        help='Share description in Chinese from YonSuite'
    )

    share_description_en_us = fields.Char(
        string='Share Description (English)',
        help='Share description in English from YonSuite'
    )

    share_description_zh_tw = fields.Char(
        string='Share Description (Traditional)',
        help='Share description in Traditional Chinese from YonSuite'
    )

    def action_export_to_yonsuite(self):
        """
        Sync product to YonSuite
        """
        self.ensure_one()

        if not self.name:
            raise UserError(_('Please enter a product name first.'))

        try:
            # Prepare product data for API (new format)
            product_data = self._prepare_product_data_push_to_yonsuite()
            
            # Wrap in the required API format
            api_payload = {
                "data": [product_data],
                "matchRule": "id"
            }

            # Call API to push product data
            api_service = self.env['yonsuite.api']
            result = api_service.push_product_to_api(api_payload)

            # Check API response
            if result.get("code") == "00000" or result.get("code") == "200":
                # Success - update product state
                yonsuite_id = None
                if result.get("data"):
                    # Try to extract product ID from response
                    data = result.get("data")
                    if isinstance(data, list) and len(data) > 0:
                        yonsuite_id = data[0].get("id")
                    elif isinstance(data, dict):
                        yonsuite_id = data.get("id")
                
                self.write({
                    'state': 'synced',
                    'yonsuite_id': yonsuite_id or f'YS_PRODUCT_{self.id}_{int(time.time())}',
                    'last_sync_date': fields.Datetime.now(),
                    'sync_error_message': False
                })
                
                _logger.info("Successfully synced product %s to YonSuite", self.name)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Product %s has been successfully synced to YonSuite.') % self.name,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                # API returned error
                error_message = result.get("message", "Unknown error")
                self.write({
                    'state': 'error',
                    'sync_error_message': error_message
                })
                
                _logger.error("Failed to sync product %s to YonSuite: %s", self.name, error_message)
                raise UserError(_('Failed to sync product to YonSuite: %s') % error_message)

        except Exception as e:
            # Handle any other errors
            error_message = str(e)
            self.write({
                'state': 'error',
                'sync_error_message': error_message
            })
            
            _logger.error("Error syncing product %s to YonSuite: %s", self.name, error_message)
            raise UserError(_('Error syncing product to YonSuite: %s') % error_message)

    def action_reset_to_draft(self):
        """
        Reset product to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'yonsuite_id': False,
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.onchange('yonsuite_unit_id')
    def _onchange_yonsuite_unit_id(self):
        """
        Update unit fields when yonsuite_unit_id changes
        """
        if self.yonsuite_unit_id:
            self.unit_id = self.yonsuite_unit_id.yonsuite_id
            self.unit_code = self.yonsuite_unit_id.code
            self.unit_name = self.yonsuite_unit_id.name
        else:
            self.unit_id = False
            self.unit_code = False
            self.unit_name = False

    @api.onchange('yonsuite_getallorgdept_id')
    def _onchange_yonsuite_getallorgdept_id(self):
        """
        Update create_org_id when yonsuite_getallorgdept_id changes
        """
        if self.yonsuite_getallorgdept_id:
            self.create_org_id = self.yonsuite_getallorgdept_id.yonsuite_id
        else:
            self.create_org_id = False

    def _find_yonsuite_unit_from_api_data(self, api_data):
        """
        Find yonsuite_unit based on unit_id or unit_code from API data
        """
        unit_id = api_data.get("unitId")
        unit_code = api_data.get("unitCode")
        
        if not unit_id and not unit_code:
            return False
        
        # First try to find by yonsuite_id (unit_id from API)
        if unit_id:
            yonsuite_unit = self.env['yonsuite.unit'].search([
                ('yonsuite_id', '=', str(unit_id)),
                ('state', '=', 'synced')
            ], limit=1)
            if yonsuite_unit:
                return yonsuite_unit
        
        # If not found by yonsuite_id, try to find by code
        if unit_code:
            yonsuite_unit = self.env['yonsuite.unit'].search([
                ('code', '=', unit_code),
                ('state', '=', 'synced')
            ], limit=1)
            if yonsuite_unit:
                return yonsuite_unit
        
        return False

    def _find_yonsuite_getallorgdept_from_api_data(self, api_data):
        """
        Find yonsuite_getallorgdept based on create_org_id from API data
        """
        create_org_id = api_data.get("createOrgId")
        
        if not create_org_id:
            return False
        
        # Find by yonsuite_id (create_org_id from API)
        yonsuite_getallorgdept = self.env['yonsuite.getallorgdept'].search([
            ('yonsuite_id', '=', str(create_org_id)),
            ('state', '=', 'synced')
        ], limit=1)
        
        return yonsuite_getallorgdept if yonsuite_getallorgdept else False

    def _update_product_from_api_data(self, api_data):
        """
        Update product from API data
        """
        self.ensure_one()

        # Prepare data from API
        vals = self._prepare_product_data_from_api(api_data)
        
        # Auto-link yonsuite_unit if unit_id or unit_code is available
        yonsuite_unit = self._find_yonsuite_unit_from_api_data(api_data)
        if yonsuite_unit:
            vals['yonsuite_unit_id'] = yonsuite_unit.id
        
        # Auto-link yonsuite_getallorgdept if create_org_id is available
        yonsuite_getallorgdept = self._find_yonsuite_getallorgdept_from_api_data(api_data)
        if yonsuite_getallorgdept:
            vals['yonsuite_getallorgdept_id'] = yonsuite_getallorgdept.id
        
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)
        
        # Process productOrges data
        product_orges_data = api_data.get("productOrges", [])
        if product_orges_data:
            self._process_product_orges_data(self.id, product_orges_data)

    @api.model
    def action_import_products_pagination(self):
        """
        Sync products from YonSuite API with pagination
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.products_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu products
        api_service = self.env['yonsuite.api']
        result = api_service.get_products_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            products_data = data.get("recordList", [])

            if not products_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.products_current_page', '1')
                _logger.info("No more products data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(products_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(products_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(product_data.get("id")) for product_data in products_data]

            # Search một lần duy nhất tất cả products đã tồn tại
            existing_products = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_products_dict = {p.yonsuite_id: p for p in existing_products}

            # Lưu products vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for product_data in products_data:
                yonsuite_id = str(product_data.get("id"))
                create_org_id = str(product_data.get("createOrgId"))
                product = existing_products_dict.get(yonsuite_id)

                # Gọi API để lấy chi tiết product
                try:
                    detail_result = api_service.get_product_detail_from_api(yonsuite_id, create_org_id)
                    if detail_result.get("code") == "00000" or detail_result.get("code") == "200":
                        detail_data_list = detail_result.get("data", [])
                        if detail_data_list and len(detail_data_list) > 0:
                            detail_data = detail_data_list[0]  # Lấy item đầu tiên từ array
                            # Merge detail data với product_data
                            product_data.update(detail_data)
                        else:
                            _logger.warning("No detail data returned for product ID %s", yonsuite_id)
                    else:
                        _logger.warning("Failed to get product detail for ID %s: %s", yonsuite_id, detail_result.get("message", "Unknown error"))
                except Exception as e:
                    _logger.warning("Error getting product detail for ID %s: %s", yonsuite_id, str(e))

                if not product:
                    # Handle name from object
                    name_obj = product_data.get("name", {})
                    if isinstance(name_obj, dict):
                        product_name = name_obj.get("simplifiedName") if name_obj else product_data.get("name")
                    else:
                        product_name = name_obj or product_data.get("name")
                    
                    # Tạo mới product
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': product_name,
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_product_data_from_api(product_data))
                    
                    # Auto-link yonsuite_unit if available
                    yonsuite_unit = self._find_yonsuite_unit_from_api_data(product_data)
                    if yonsuite_unit:
                        vals['yonsuite_unit_id'] = yonsuite_unit.id
                    
                    # Auto-link yonsuite_getallorgdept if available
                    yonsuite_getallorgdept = self._find_yonsuite_getallorgdept_from_api_data(product_data)
                    if yonsuite_getallorgdept:
                        vals['yonsuite_getallorgdept_id'] = yonsuite_getallorgdept.id

                    product = self.create(vals)
                    
                    # Process productOrges data for new product
                    product_orges_data = product_data.get("productOrges", [])
                    if product_orges_data:
                        product._process_product_orges_data(product.id, product_orges_data)
                    
                    created_count += 1
                else:
                    # Product đã tồn tại, kiểm tra có cần cập nhật không
                    # Vì API không trả về modify_time, ta sẽ cập nhật luôn
                    product._update_product_from_api_data(product_data)
                    updated_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.products_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.products_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.products_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.products_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.products_last_sync', fields.Datetime.now())

            return synced_count
        else:
            # Kiểm tra message để xác định có phải là "rỗng" không
            message = result.get("message", "")
            message_lower = message.lower()
            # Check for various empty result indicators
            empty_indicators = ["rỗng", "empty", "không có", "khong co"]
            is_empty = any(indicator in message or indicator in message_lower for indicator in empty_indicators)

            if is_empty:
                # Kết quả truy vấn rỗng, reset về trang 1
                config_parameter.set_param('yonsuite_integration.products_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync products from YonSuite: %s", error_msg)
                return 0

    def _prepare_product_data_from_api(self, api_data):
        """
        Prepare product data from API response
        """
        # Handle name from object
        name_obj = api_data.get("name", {})
        if isinstance(name_obj, dict):
            product_name = name_obj.get("simplifiedName") if name_obj else api_data.get("name")
        else:
            product_name = name_obj or api_data.get("name")
        
        vals = {
            'yonsuite_id': str(api_data.get("id")),
            'name': product_name,
            'code': api_data.get("code"),
            'trans_type': api_data.get("transType"),
            'unit_id': str(api_data.get("unitId")) if api_data.get("unitId") else False,
            'unit_code': api_data.get("unitCode"),
            'unit_name': api_data.get("unitName"),
            'unit_use_type': api_data.get("unitUseType", 0),
            'manage_class': str(api_data.get("manageClass")) if api_data.get("manageClass") else False,
            'manage_class_code': api_data.get("manageClassCode"),
            'manage_class_name': api_data.get("manageClassName"),
            'sale_product_class': str(api_data.get("saleProductClass")) if api_data.get("saleProductClass") else False,
            'sale_product_class_code': api_data.get("saleProductClassCode"),
            'sale_product_class_name': api_data.get("saleProductClassName"),
            'purchase_class': str(api_data.get("purchaseClass")) if api_data.get("purchaseClass") else False,
            'purchase_class_code': api_data.get("purchaseClassCode"),
            'purchase_class_name': api_data.get("purchaseClassName"),
            'product_template': str(api_data.get("productTemplate")) if api_data.get("productTemplate") else False,
            'product_template_name': api_data.get("productTemplateName"),
            'product_family': api_data.get("productFamily", 0),
            'sales_and_operations': api_data.get("salesAndOperations", 0),
            'med_is_registration_manager': api_data.get("medIsRegistrationManager", False),
            'med_is_authorization_manager': api_data.get("medIsAuthorizationManager", False),
            'has_specs': api_data.get("hasSpecs", False),
            'url': api_data.get("url"),
            'stop_status': api_data.get("stopStatus", False),
            'real_product_attribute': api_data.get("realProductAttribute"),
            'real_product_attribute_type': api_data.get("realProductAttributeType"),
            'virtual_product_attribute': api_data.get("virtualProductAttribute"),
            'create_org_id': api_data.get("createOrgId"),
            
            # Additional fields from product detail API
            'platform_code': api_data.get("platformCode"),
            'product_line': str(api_data.get("productLine")) if api_data.get("productLine") else False,
            'product_line_code': api_data.get("productLine_Code"),
            'product_line_name': api_data.get("productLine_Name"),
            'brand': str(api_data.get("brand")) if api_data.get("brand") else False,
            'brand_code': api_data.get("brand_Code"),
            'brand_name': api_data.get("brand_Name"),
            'place_of_origin': api_data.get("placeOfOrigin"),
            'manufacturer': api_data.get("manufacturer"),
            'platform_status': api_data.get("platFormStaus"),
            'platform_remark': api_data.get("cPlatFormRemark"),
            'gift_card_id': str(api_data.get("giftCardId")) if api_data.get("giftCardId") else False,
            'gift_card_name': api_data.get("giftCardId_Name"),
            'coupon_id': str(api_data.get("couponId")) if api_data.get("couponId") else False,
            'coupon_type': api_data.get("couponType"),
            'coupon_name': api_data.get("couponId_Name"),
            'weight': api_data.get("weight", 0.0),
            'weight_unit': str(api_data.get("weightUnit")) if api_data.get("weightUnit") else False,
            'weight_unit_name': api_data.get("weightUnit_Name"),
            'volume': api_data.get("volume", 0.0),
            'volume_unit': str(api_data.get("volumeUnit")) if api_data.get("volumeUnit") else False,
            'volume_unit_name': api_data.get("volumeUnit_Name"),
            'tax_class': str(api_data.get("taxClass")) if api_data.get("taxClass") else False,
            'tax_class_code': api_data.get("taxClass_Code"),
            'tax_class_name': api_data.get("taxClass_Name"),
            'creator': api_data.get("creator"),
            'create_date': api_data.get("createDate"),
            'create_time': api_data.get("createTime"),
            'modifier': api_data.get("modifier"),
            'modify_time': api_data.get("modifyTime"),
            'modify_date': api_data.get("modifyDate"),
            'customer_service_day': api_data.get("customerServiceDay", 0),
            'dimension_code': api_data.get("dimensionCode"),
            
            # Additional fields from new API response format
            'default_sku_id': str(api_data.get("defaultSKUId")) if api_data.get("defaultSKUId") else False,
            'tenant': str(api_data.get("tenant")) if api_data.get("tenant") else False,
            'deleted': api_data.get("deleted", False),
            'create_time': api_data.get("createTime"),
            'create_date': api_data.get("createDate"),
            'modify_time': api_data.get("modifyTime"),
            'modify_date': api_data.get("modifyDate"),
            'creator': api_data.get("creator"),
            'modifier': api_data.get("modifier"),
            'creator_id': str(api_data.get("creatorId")) if api_data.get("creatorId") else False,
            'modifier_id': str(api_data.get("modifierId")) if api_data.get("modifierId") else False,
            'name1': api_data.get("name1"),
            'name4': api_data.get("name4"),
            'registration_manager': api_data.get("registrationManager", False),
            'authorization_manager': api_data.get("authorizationManager", False),
            'ytenant_id': api_data.get("ytenantId"),
            'trans_type': api_data.get("transType"),
            'trans_type_code': api_data.get("transTypeCode"),
            'trans_type_name': api_data.get("transTypeName"),
            'product_family': api_data.get("productFamily", 0),
            'sales_and_operations': api_data.get("salesAndOperations", 0),
            'shop': api_data.get("shop", -1),
            'source': api_data.get("source", 1),
            'use_sku': api_data.get("useSku", 1),
        }

        # Handle product character definition
        product_character_def = api_data.get("productCharacterDef", {})
        if product_character_def:
            vals['product_character_def_id'] = product_character_def.get("id")

        # Find management class based on manage_class or manage_class_code
        management_class = self._find_management_class(api_data)
        if management_class:
            vals['yonsuite_management_class_id'] = management_class.id

        # Find purchase class based on purchase_class or purchase_class_code
        purchase_class = self._find_purchase_class(api_data)
        if purchase_class:
            vals['yonsuite_purchase_class_id'] = purchase_class.id

        # Find sale class based on sale_product_class or sale_product_class_code
        sale_class = self._find_sale_class(api_data)
        if sale_class:
            vals['yonsuite_sale_class_id'] = sale_class.id

        # Handle detail fields
        detail = api_data.get("detail", {})
        if detail:
            detail_vals = {
                'exemption': detail.get("exemption", False),
                'warehousing_by_result': detail.get("warehousingByResult"),
                'sales_returns_exemption': detail.get("salesReturnsExemption"),
                'returns_warehousing_by_result': detail.get("returnsWarehousingByResult"),
                'periodical_inspection': detail.get("periodicalInspection"),
                'periodical_inspection_cycle': detail.get("periodicalInspectionCycle", 0),
                'short_name': detail.get("shortName"),
                'mnemonic_code': detail.get("mnemonicCode"),
                'bar_code': detail.get("barCode"),
                'business_attribute': detail.get("businessAttribute", 0),
                'sale_channel': detail.get("saleChannel", 0),
                'product_apply_range_id': str(detail.get("productApplyRangeId")) if detail.get("productApplyRangeId") else False,
                'purchase_unit_name': detail.get("purchaseUnitName"),
                'purchase_price_unit_name': detail.get("purchasePriceUnitName"),
                'stock_unit_name': detail.get("stockUnitName"),
                'produce_unit_name': detail.get("produceUnitName"),
                'batch_price_unit_name': detail.get("batchPriceUnitName"),
                'batch_unit_name': detail.get("batchUnitName"),
                'online_unit_name': detail.get("onlineUnitName"),
                'offline_unit_name': detail.get("offlineUnitName"),
                'require_unit_name': detail.get("requireUnitName"),
                'batch_price': detail.get("batchPrice", 0.0),
                'f_mark_price': detail.get("fMarkPrice", 0.0),
                'f_lowest_mark_price': detail.get("fLowestMarkPrice", 0.0),
                'f_sale_price': detail.get("fSalePrice", 0.0),
                'f_market_price': detail.get("fMarketPrice", 0.0),
                'is_display_price': detail.get("isDisplayPrice", False),
                'price_area_message': detail.get("priceAreaMessage"),
                'in_taxrate': str(detail.get("incomeTaxRates")) if detail.get("incomeTaxRates") else False,
                'in_taxrate_name': detail.get("incomeTaxRatesName"),
                'out_taxrate': str(detail.get("outputTaxRate")) if detail.get("outputTaxRate") else False,
                'out_taxrate_name': detail.get("outTaxRateName"),
                'preferential_policy_type': str(detail.get("preferentialPolicyType")) if detail.get("preferentialPolicyType") else False,
                'preferential_policy_type_name': detail.get("preferentialPolicyTypeName"),
                'i_order': detail.get("iOrder", 0),
                'i_status': detail.get("iStatus", False),
                'mall_up_time': detail.get("mallUpTime"),
                'i_u_order_status': detail.get("iUOrderStatus", False),
                'uorder_up_time': detail.get("uorderUpTime"),
                'product_vendor': str(detail.get("productVendor")) if detail.get("productVendor") else False,
                'product_vendor_name': detail.get("productVendor_Name"),
                'product_buyer': detail.get("productBuyer"),
                'product_buyer_name': detail.get("productBuyer_Name"),
                'f_prime_costs': detail.get("fPrimeCosts", 0.0),
                'max_prime_costs': detail.get("maxPrimeCosts", 0.0),
                'request_order_limit': detail.get("requestOrderLimit", 0.0),
                'can_sale': detail.get("canSale", False),
                'i_min_order_quantity': detail.get("iMinOrderQuantity", 0.0),
                'delivery_days': detail.get("deliveryDays", 0),
                'uorder_dly_fee_rule_id': str(detail.get("uorderDlyFeeRuleId")) if detail.get("uorderDlyFeeRuleId") else False,
                'uorder_dly_fee_rule_id_name': detail.get("uorderDlyFeeRuleId_Name"),
                'be_up_time': detail.get("beUpTime"),
                'is_batch_manage': detail.get("isBatchManage", False),
                'is_expiry_date_manage': detail.get("isExpiryDateManage", False),
                'expire_date_no': detail.get("expireDateNo", 0),
                'expire_date_unit': detail.get("expireDateUnit"),
                'days_before_validity_reject': detail.get("daysBeforeValidityReject", 0),
                'validity_warning_days': detail.get("validityWarningDays", 0),
                'is_serial_no_manage': detail.get("isSerialNoManage", False),
                'is_barcode_manage': detail.get("isBarcodeManage", False),
                'safety_stock': detail.get("safetyStock", 0.0),
                'highest_stock': detail.get("highestStock", 0.0),
                'lowest_stock': detail.get("lowestStock", 0.0),
                'rop_stock': detail.get("ropStock", 0.0),
                'warehouse_manager': detail.get("warehouseManager"),
                'warehouse_manager_name': detail.get("warehouseManager_Name"),
                'delivery_warehouse': str(detail.get("deliveryWarehouse")) if detail.get("deliveryWarehouse") else False,
                'delivery_warehouse_name': detail.get("deliveryWarehouse_Name"),
                'return_warehouse': str(detail.get("returnWarehouse")) if detail.get("returnWarehouse") else False,
                'return_warehouse_name': detail.get("returnWarehouse_Name"),
                'in_store_excess_limit': detail.get("inStoreExcessLimit", 0.0),
                'out_store_excess_limit': detail.get("outStoreExcessLimit", 0.0),
                'storage_loss_rate': detail.get("storageLossRate", 0.0),
                'plan_default_attribute': detail.get("planDefaultAttribute"),
                'allow_negative_inventory': detail.get("allowNegativeInventory", False),
                'plan_method': detail.get("planMethod"),
                'plan_strategy': detail.get("planStrategy"),
                'plan_strategy_name': detail.get("planStrategy_Name"),
                'key_sub_part': detail.get("keySubPart", False),
                'bind_carrier': detail.get("bindCarrier", False),
                'purpose': detail.get("purpose"),
                'utility': detail.get("utility"),
                'supply_demand_policy': detail.get("supplyDemandPolicy"),
                'fixed_lead_time': detail.get("fixedLeadTime", 0),
                'batch_policy': detail.get("batchPolicy", 0),
                'supply_type': detail.get("supplyType", 0),
                'produce_department': detail.get("produceDepartment"),
                'produce_department_name': detail.get("produceDepartment_Name"),
                'manufacture_planner': detail.get("manufacturePlanner"),
                'manufacture_planner_name': detail.get("manufacturePlanner_Name"),
                'engineering_drawing_no': detail.get("engineeringDrawingNo"),
                'supply_times': detail.get("supplyTimes", 0),
                'plan_produce_limit': detail.get("planProduceLimit", 0.0),
                'weigh': detail.get("weigh", False),
                'value_manage_type': detail.get("valueManageType"),
                'cost_valuation': detail.get("costValuation"),
                'check_by_cost': detail.get("checkByCost", False),
                'f_no_tax_cost_price': detail.get("fNoTaxCostPrice", 0.0),
                'check_by_batch': detail.get("checkByBatch", False),
                'accounting_by_item': detail.get("accountingByItem", False),
                'material_cost': detail.get("materialCost", False),
                'is_check_free': detail.get("isCheckFree", 0),
                'sale_style': detail.get("saleStyle"),
                'sale_points': detail.get("salePoints", 0.0),
                'l_inventory_count': detail.get("lInventoryCount", 0.0),
                'i_base_sale_count': detail.get("iBaseSaleCount", 0.0),
                'dly_fee_rule_id': str(detail.get("dlyFeeRuleId")) if detail.get("dlyFeeRuleId") else False,
                'dly_fee_rule_id_name': detail.get("dlyFeeRuleId_Name"),
                'enable_subscribe': detail.get("enableSubscribe", False),
                'enable_deposit': detail.get("enableDeposit", False),
                'deposit_deal_pay_type': detail.get("depositDealPayType", 0),
                'deposits': detail.get("deposits", 0.0),
                'deposit_percentage': detail.get("depositPercentage", 0.0),
                'enable_modify_deposit': detail.get("enablemodifyDeposit", False),
                'minimum_deposits': detail.get("minimumDeposits", 0.0),
                'deposit_pay_type': detail.get("depositPayType", 0),
                'service_duration': detail.get("serviceDuration", 0),
                'service_duration_unit': detail.get("serviceDurationUnit", 0),
                'can_order': detail.get("canOrder", False),
                'only_order': detail.get("onlyOrder", False),
                'order_advance_time': detail.get("orderAdvanceTime", 0),
                'i_enable_cycle_purchase': detail.get("iEnableCyclePurchase", False),
                'f_settle_accounts_rate': detail.get("fSettleAccountsRate", 0.0),
                'is_all_area': detail.get("isAllArea", False),
                'i_enable_econtract': detail.get("iEnableEcontract", False),
                'page_title': detail.get("pageTitle"),
                'is_recommend': detail.get("isRecommend", False),
                'allow_store_purchase': detail.get("allowStorePurchase", False),
                'is_sale_in_offline_store': detail.get("isSaleInOfflineStore", False),
                'is_price_change_allowed': detail.get("isPriceChangeAllowed", False),
                'is_offline_store_order': detail.get("isOfflineStoreOrder", False),
                'is_offline_store_return': detail.get("isOfflineStoreReturn", False),
                'retail_price_dimension': detail.get("retailPriceDimension", 0),
                'deliver_quantity_change': detail.get("deliverQuantityChange", 0),
                'is_process': detail.get("isProcess", False),
                'process_type': detail.get("processType"),
                'is_material': detail.get("isMaterial", False),
                'is_weight': detail.get("isWeight", False),
            }
            vals.update(detail_vals)
            
            # Handle receipt name
            receipt_name = detail.get("receiptName", {})
            if receipt_name:
                vals.update({
                    'receipt_name_zh_cn': receipt_name.get("zh_CN"),
                    'receipt_name_en_us': receipt_name.get("en_US"),
                    'receipt_name_zh_tw': receipt_name.get("zh_TW"),
                })
            
            # Handle meta description
            meta_description = detail.get("metaDescription", {})
            if meta_description:
                vals.update({
                    'meta_description_zh_cn': meta_description.get("zh_CN"),
                    'meta_description_en_us': meta_description.get("en_US"),
                    'meta_description_zh_tw': meta_description.get("zh_TW"),
                })
            
            # Handle display name
            display_name = detail.get("displayName", {})
            if display_name:
                vals.update({
                    'display_name_zh_cn': display_name.get("zh_CN"),
                    'display_name_en_us': display_name.get("en_US"),
                    'display_name_zh_tw': display_name.get("zh_TW"),
                })
            
            # Handle title memo
            title_memo = detail.get("titleMemo", {})
            if title_memo:
                vals.update({
                    'title_memo_zh_cn': title_memo.get("zh_CN"),
                    'title_memo_en_us': title_memo.get("en_US"),
                    'title_memo_zh_tw': title_memo.get("zh_TW"),
                })

        # Handle other object fields from main API response
        # Handle modelDescription
        model_description = api_data.get("modelDescription", {})
        if model_description:
            vals.update({
                'model_description_zh_cn': model_description.get("zh_CN"),
                'model_description_en_us': model_description.get("en_US"),
                'model_description_zh_tw': model_description.get("zh_TW"),
            })
        
        # Handle model
        model = api_data.get("model", {})
        if model:
            vals.update({
                'model_zh_cn': model.get("zh_CN"),
                'model_en_us': model.get("en_US"),
                'model_zh_tw': model.get("zh_TW"),
            })
        
        # Handle keywords
        keywords = api_data.get("keywords", {})
        if keywords:
            vals.update({
                'keywords_zh_cn': keywords.get("zh_CN"),
                'keywords_en_us': keywords.get("en_US"),
                'keywords_zh_tw': keywords.get("zh_TW"),
            })
        
        # Handle shareDescription
        share_description = api_data.get("shareDescription", {})
        if share_description:
            vals.update({
                'share_description_zh_cn': share_description.get("zh_CN"),
                'share_description_en_us': share_description.get("en_US"),
                'share_description_zh_tw': share_description.get("zh_TW"),
            })

        return vals

    def _process_product_orges_data(self, product_id, product_orges_data):
        """
        Process productOrges data and create/update records
        
        Args:
            product_id (int): ID of the yonsuite.product record
            product_orges_data (list): List of productOrges data from API
        """
        if product_orges_data:
            product_orges_model = self.env['yonsuite.product.orges']
            product_orges_model.create_or_update_product_orges(product_id, product_orges_data)

    def _find_management_class(self, api_data):
        """
        Find management class based on manage_class or manage_class_code
        """
        manage_class_id = api_data.get("manageClass")
        manage_class_code = api_data.get("manageClassCode")
        
        if not manage_class_id and not manage_class_code:
            return False
            
        # Search by yonsuite_id first (most reliable)
        if manage_class_id:
            management_class = self.env['yonsuite.management.class'].search([
                ('yonsuite_id', '=', str(manage_class_id))
            ], limit=1)
            if management_class:
                return management_class
        
        # Search by code as fallback
        if manage_class_code:
            management_class = self.env['yonsuite.management.class'].search([
                ('code', '=', manage_class_code)
            ], limit=1)
            if management_class:
                return management_class
                
        return False

    def _find_purchase_class(self, api_data):
        """
        Find purchase class based on purchase_class or purchase_class_code
        """
        purchase_class_id = api_data.get("purchaseClass")
        purchase_class_code = api_data.get("purchaseClassCode")
        
        if not purchase_class_id and not purchase_class_code:
            return False
            
        # Search by yonsuite_id first (most reliable)
        if purchase_class_id:
            purchase_class = self.env['yonsuite.purchase.class'].search([
                ('yonsuite_id', '=', str(purchase_class_id))
            ], limit=1)
            if purchase_class:
                return purchase_class
        
        # Search by code as fallback
        if purchase_class_code:
            purchase_class = self.env['yonsuite.purchase.class'].search([
                ('code', '=', purchase_class_code)
            ], limit=1)
            if purchase_class:
                return purchase_class
                
        return False

    def _find_sale_class(self, api_data):
        """
        Find sale class based on sale_product_class or sale_product_class_code
        """
        sale_class_id = api_data.get("saleProductClass")
        sale_class_code = api_data.get("saleProductClassCode")
        
        if not sale_class_id and not sale_class_code:
            return False
            
        # Search by yonsuite_id first (most reliable)
        if sale_class_id:
            sale_class = self.env['yonsuite.sale.class'].search([
                ('yonsuite_id', '=', str(sale_class_id))
            ], limit=1)
            if sale_class:
                return sale_class
        
        # Search by code as fallback
        if sale_class_code:
            sale_class = self.env['yonsuite.sale.class'].search([
                ('code', '=', sale_class_code)
            ], limit=1)
            if sale_class:
                return sale_class
                
        return False

    @api.onchange('yonsuite_management_class_id')
    def _onchange_yonsuite_management_class_id(self):
        """
        Auto-update manage_class fields when yonsuite_management_class_id changes
        """
        if self.yonsuite_management_class_id:
            self.manage_class = self.yonsuite_management_class_id.yonsuite_id
            self.manage_class_code = self.yonsuite_management_class_id.code
            self.manage_class_name = self.yonsuite_management_class_id.name
        else:
            self.manage_class = False
            self.manage_class_code = False
            self.manage_class_name = False

    @api.onchange('yonsuite_purchase_class_id')
    def _onchange_yonsuite_purchase_class_id(self):
        """
        Auto-update purchase_class fields when yonsuite_purchase_class_id changes
        """
        if self.yonsuite_purchase_class_id:
            self.purchase_class = self.yonsuite_purchase_class_id.yonsuite_id
            self.purchase_class_code = self.yonsuite_purchase_class_id.code
            self.purchase_class_name = self.yonsuite_purchase_class_id.name
        else:
            self.purchase_class = False
            self.purchase_class_code = False
            self.purchase_class_name = False

    @api.onchange('yonsuite_sale_class_id')
    def _onchange_yonsuite_sale_class_id(self):
        """
        Auto-update sale_product_class fields when yonsuite_sale_class_id changes
        """
        if self.yonsuite_sale_class_id:
            self.sale_product_class = self.yonsuite_sale_class_id.yonsuite_id
            self.sale_product_class_code = self.yonsuite_sale_class_id.code
            self.sale_product_class_name = self.yonsuite_sale_class_id.name
        else:
            self.sale_product_class = False
            self.sale_product_class_code = False
            self.sale_product_class_name = False

    def _prepare_product_data_push_to_yonsuite(self):
        """
        Prepare product data for pushing to YonSuite API (New Format)
        """
        self.ensure_one()
        
        # Get organization info from config or default values
        config_parameter = self.env['ir.config_parameter'].sudo()
        org_code = config_parameter.get_param('yonsuite_integration.org_code', 'global00')
        
        # Prepare the product data structure according to new YonSuite API format
        # Only include fields that actually exist in the model
        product_data = {
            "sourceUnique": str(self.id),
            "targetUnique": self.yonsuite_id or "",
            "erpCode": self.code or f"ERP_{self.id}",
            "code": self.code or f"PROD_{self.id}",
            "couponType": getattr(self, 'coupon_type', 0) or 0,
            "cPlatFormRemark": getattr(self, 'platform_remark', "") or "",
            "creatorType": getattr(self, 'creator_type', 1) or 1,
            "customerServiceDay": getattr(self, 'customer_service_day', 1) or 1,
            "enableAssistUnit": getattr(self, 'enable_assist_unit', False) or False,
            "height": getattr(self, 'height', 0) or 0,
            "homepageBusinessId": getattr(self, 'homepage_business_id', "") or "",
            "id": int(self.yonsuite_id) if self.yonsuite_id else 0,
            "imgBusinessId": getattr(self, 'img_business_id', "") or "",
            "internalSupplyOrgId___code": getattr(self, 'internal_supply_org_code', "") or "",
            "isAuthorizationManager": getattr(self, 'is_authorization_manager', False) or False,
            "isBatch": getattr(self, 'is_batch', False) or False,
            "isDerivedMaterial": getattr(self, 'is_derived_material', 0) or 0,
            "isOptionalMaterial": getattr(self, 'is_optional_material', 0) or 0,
            "isRegistrationManager": getattr(self, 'is_registration_manager', False) or False,
            "keywords": {
                "zh_CN": getattr(self, 'keywords_zh_cn', "") or "",
                "en_US": getattr(self, 'keywords_en_us', "") or "",
                "zh_TW": getattr(self, 'keywords_zh_tw', "") or ""
            },
            "length": getattr(self, 'length', 0) or 0,
            "lifeCycleTemplate___code": getattr(self, 'life_cycle_template_code', "") or "",
            "manageClass___code": getattr(self, 'manage_class_code', "") or "",
            "manufacturer": getattr(self, 'manufacturer', "") or "",
            "materialStatus___code": getattr(self, 'material_status_code', "system_01") or "system_01",
            "model": {
                "zh_CN": getattr(self, 'model_zh_cn', "") or "",
                "en_US": getattr(self, 'model_en_us', "") or "",
                "zh_TW": getattr(self, 'model_zh_tw', "") or ""
            },
            "modelDescription": {
                "zh_CN": getattr(self, 'model_description_zh_cn', "") or "",
                "en_US": getattr(self, 'model_description_en_us', "") or "",
                "zh_TW": getattr(self, 'model_description_zh_tw', "") or ""
            },
            "name": {
                "zh_CN": self.name or "",
                "en_US": self.name or "",
                "zh_TW": self.name or ""
            },
            "netWeight": getattr(self, 'net_weight', 0) or 0,
            "netWeightUnit___code": getattr(self, 'net_weight_unit_code', "kg") or "kg",
            "optionalMaterialId___code": getattr(self, 'optional_material_code', "") or "",
            "optionalType": getattr(self, 'optional_type', 0) or 0,
            "orgId___code": org_code,
            "placeOfOrigin": getattr(self, 'place_of_origin', "") or "",
            "planClass___code": getattr(self, 'plan_class_code', "") or "",
            "platformCode": getattr(self, 'platform_code', "") or "",
            "productClass___code": getattr(self, 'product_class_code', "") or "",
            "productFamily": getattr(self, 'product_family', 1) or 1,
            "productLine___code": getattr(self, 'product_line_code', "") or "",
            "productTemplate___name": getattr(self, 'product_template_name', "") or "",
            "ptoPriceType": getattr(self, 'pto_price_type', 0) or 0,
            "purchaseClass___code": getattr(self, 'purchase_class_code', "") or "",
            "realProductAttribute": getattr(self, 'real_product_attribute', 1) or 1,
            "realProductAttributeType": getattr(self, 'real_product_attribute_type', 1) or 1,
            "registrationNo": getattr(self, 'registration_no', "") or "",
            "salesAndOperations": getattr(self, 'sales_and_operations', 0) or 0,
            "shareDescription": {
                "zh_CN": getattr(self, 'share_description_zh_cn', "") or "",
                "en_US": getattr(self, 'share_description_en_us', "") or "",
                "zh_TW": getattr(self, 'share_description_zh_tw', "") or ""
            },
            "shop___code": getattr(self, 'shop_code', "") or "",
            "sunshinePurchaseNo": getattr(self, 'sunshine_purchase_no', "") or "",
            "taxClass___code": getattr(self, 'tax_class_code', "") or "",
            "transType___code": getattr(self, 'trans_type_code', "") or "",
            "unit___code": self.unit_code or "KGM",
            "unitUseType": self.unit_use_type or 2,
            "useSku": getattr(self, 'use_sku', 1) or 1,
            "videoBusinessId": getattr(self, 'video_business_id', "") or "",
            "virtualProductAttribute": getattr(self, 'virtual_product_attribute', 7) or 7,
            "volume": getattr(self, 'volume', 0) or 0,
            "volumeUnit___code": getattr(self, 'volume_unit_code', "MTQ") or "MTQ",
            "weight": getattr(self, 'weight', 0) or 0,
            "weightUnit___code": getattr(self, 'weight_unit_code', "kg") or "kg",
            "width": getattr(self, 'width', 0) or 0,
            "productOrgs": self._prepare_product_orgs_data(),
            "productAssistUnitExchanges": self._prepare_product_assist_unit_exchanges_data(),
            "productTags": self._prepare_product_tags_data(),
            "productAssistClasses": self._prepare_product_assist_classes_data(),
            "productBarCodes": self._prepare_product_bar_codes_data(),
            "detail": self._prepare_product_detail_data()
        }
        
        return product_data

    def _prepare_product_orgs_data(self):
        """
        Prepare productOrgs data for API
        """
        return [{
            "orgId___code": self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.org_code', 'global00'),
            "rangeType": 1
        }]

    def _prepare_product_assist_unit_exchanges_data(self):
        """
        Prepare productAssistUnitExchanges data for API
        """
        return [{
            "unitExchangeType": 0,
            "assistUnit___code": "TNE",
            "assistUnitCount": 1,
            "mainUnitCount": 1000,
            "iOrder": 0
        }]

    def _prepare_product_tags_data(self):
        """
        Prepare productTags data for API
        """
        return [{
            "tagId___name": "tag01"
        }]

    def _prepare_product_assist_classes_data(self):
        """
        Prepare productAssistClasses data for API
        """
        return [{
            "productClassId___code": "test1"
        }]

    def _prepare_product_bar_codes_data(self):
        """
        Prepare productBarCodes data for API
        """
        return [{
            "barCode": self.code or f"BC_{self.id}"
        }]

    def _prepare_product_detail_data(self):
        """
        Prepare detail data for API
        """
        return {
            "stopstatus": getattr(self, 'stop_status', False) or False,
            "accountingByItem": False,
            "allowNegativeInventory": False,
            "allowStorePurchase": True,
            "arrivalAllowErrorLimit": 1,
            "atpInspection": 0,
            "barCode": self.code or f"BC_{self.id}",
            "batchDouble": 10,
            "batchPolicy": 0,
            "batchPrice": 0,
            "batchPriceUnit___code": self.unit_code or "KGM",
            "batchRule": 0,
            "batchUnit___code": self.unit_code or "KGM",
            "behindLeadTime": 10,
            "beyondSupplyDays": 10,
            "billingUnit___code": self.unit_code or "KGM",
            "bindCarrier": True,
            "BOMSource___code": "",
            "BOMType": 0,
            "businessAttribute": getattr(self, 'business_attribute', "1,7") or "1,7",
            "businessAttributeOutSourcing": 0,
            "businessAttributePurchase": 0,
            "businessAttributeSale": 0,
            "businessAttributeSelfCreate": 0,
            "canOrder": True,
            "canSale": True,
            "checkByBatch": False,
            "checkByClient": 0,
            "checkByCost": False,
            "checkByOutsourcing": 0,
            "checkByProject": 0,
            "checkByRevenueManagement": 0,
            "checkBySalesOrders": 0,
            "checkReminderLeadTime": 5,
            "costItems___code": getattr(self, 'cost_items_code', "test1") or "test1",
            "costValuation": 1,
            "customerId___code": "",
            "daysBeforeValidityReject": 0,
            "deliverQuantityChange": 1,
            "deliveryDays": 0,
            "deliveryWarehouse___code": getattr(self, 'delivery_warehouse_code', "000036") or "000036",
            "demandConsolidation": 0,
            "demandConsolidationDateType": 0,
            "demandConsolidationNumber": 1,
            "demandConsolidationType": 0,
            "demandConsolidationUnit": 0,
            "demandPlanningUnit___code": self.unit_code or "KGM",
            "depositDealPayType": 0,
            "depositPayType": 0,
            "depositPercentage": 10,
            "deposits": 100,
            "directProduction": 0,
            "displayName": {
                "zh_CN": getattr(self, 'display_name_zh_cn', "") or self.name or "",
                "en_US": getattr(self, 'display_name_en_us', "") or self.name or "",
                "zh_TW": getattr(self, 'display_name_zh_tw', "") or self.name or ""
            },
            "dlyFeeRuleId___dlyFeeRuleId___code": getattr(self, 'dly_fee_rule_code', "test1") or "test1",
            "doublePick": 10,
            "doubleReplenish": 10,
            "ECNControl": False,
            "economicQuantity": 10,
            "effectiveLeadTime": 5,
            "enableDeposit": False,
            "enablemodifyDeposit": False,
            "enableSparePartsManagement": 0,
            "enableStockExpireCheck": 0,
            "enableStockPeriodRecheck": 0,
            "enableSubscribe": False,
            "engineeringDrawingNo": getattr(self, 'engineering_drawing_no', "10101") or "10101",
            "erpOuterCode": getattr(self, 'erp_outer_code', "") or self.code or f"ERP_{self.id}",
            "exemption": getattr(self, 'exemption', False) or False,
            "expireDateNo": 0,
            "expireDateUnit": 1,
            "fixedLeadTime": 0,
            "fixedQuantity": 10,
            "fixedReturn": True,
            "fixedWastage": 10,
            "fLowestMarkPrice": getattr(self, 'f_lowest_mark_price', 8) or 8,
            "fMarketPrice": getattr(self, 'f_market_price', 10) or 10,
            "fMarkPrice": getattr(self, 'f_mark_price', 10) or 10,
            "fNoTaxCostPrice": getattr(self, 'f_no_tax_cost_price', 1) or 1,
            "fPrimeCosts": getattr(self, 'f_prime_costs', 8) or 8,
            "frontLeadTime": 10,
            "fSalePrice": getattr(self, 'f_sale_price', 10) or 10,
            "fSettleAccountsRate": getattr(self, 'f_settle_accounts_rate', 5) or 5,
            "fullSetInspection": 0,
            "highestStock": getattr(self, 'highest_stock', 10) or 10,
            "iABCClass": 1,
            "iBaseSaleCount": 0,
            "iDoubleSale": 0,
            "iEnableCyclePurchase": False,
            "iEnableEcontract": False,
            "iMinOrderQuantity": getattr(self, 'i_min_order_quantity', 1) or 1,
            "inspectionType": 0,
            "inspectionUnit___code": self.unit_code or "KGM",
            "inStoreExcessLimit": 1,
            "inStoreLessLimit": 1,
            "inTaxrate___code": getattr(self, 'in_taxrate_code', "VATR6") or "VATR6",
            "inventoryPlanStrategy": 0,
            "invoiceAllowErrorLimit": 1,
            "iOrder": 0,
            "isAllArea": True,
            "isBarcodeManage": False,
            "isBatchManage": False,
            "isCheckFree": 0,
            "isCreator": True,
            "isDisplayPrice": True,
            "isExpiryDateCalculationMethod": 0,
            "isExpiryDateManage": False,
            "isMaterial": False,
            "isOfflineStoreOrder": True,
            "isOfflineStoreReturn": True,
            "isPriceChangeAllowed": False,
            "isProcess": False,
            "isRecommend": False,
            "isSaleInOfflineStore": True,
            "isSerialNoManage": False,
            "iStatus": False,
            "isWeight": False,
            "iUOrderStatus": False,
            "keySubPart": False,
            "leadTimeCoefficient": 1,
            "leadTimeQuantity": 1,
            "lInventoryCount": 1,
            "logisticsRelated": False,
            "lossType": 0,
            "lowestStock": getattr(self, 'lowest_stock', 1) or 1,
            "malldowncount": 1,
            "mallupcount": 1,
            "manageByInventory": 0,
            "manufacturePlanner___code": getattr(self, 'manufacture_planner_code', "test1") or "test1",
            "manufacturingStrategy": "MTO",
            "materialCost": False,
            "materialStatus___code": getattr(self, 'material_status_code', "system_01") or "system_01",
            "maxBatchPrice": 1,
            "maximumTurnoverDays": 1,
            "maxPrimeCosts": 0,
            "metaDescription": {
                "zh_CN": getattr(self, 'meta_description_zh_cn', "") or "",
                "en_US": getattr(self, 'meta_description_en_us', "") or "",
                "zh_TW": getattr(self, 'meta_description_zh_tw', "") or ""
            },
            "minBatchPrice": 1,
            "minimumDeposits": 0,
            "mnemonicCode": getattr(self, 'mnemonic_code', "") or self.code or f"MC_{self.id}",
            "mtoStrategy": 0,
            "offlineUnit___code": self.unit_code or "KGM",
            "omsWarehouse___code": getattr(self, 'oms_warehouse_code', "test1") or "test1",
            "onlineUnit___code": self.unit_code or "KGM",
            "onlyOrder": True,
            "orderAdvanceTime": 0,
            "orgId___code": self.env['ir.config_parameter'].sudo().get_param('yonsuite_integration.org_code', 'global00'),
            "outStoreExcessLimit": 1,
            "outStoreLessLimit": 1,
            "outTaxrate___code": getattr(self, 'out_taxrate_code', "VATR6") or "VATR6",
            "overSigning": 0,
            "pageTitle": getattr(self, 'page_title', "test") or "test",
            "periodicalInspection": False,
            "periodicalInspectionCycle": 1,
            "planCheckDays": 1,
            "planDefaultAttribute": 1,
            "planMethod": 0,
            "planProduceLimit": 0,
            "planStrategy___code": getattr(self, 'plan_strategy_code', "test1") or "test1",
            "preferentialPolicyType___taxRevenueCode": "1110101000000000000",
            "prepareFeed": False,
            "priceAreaMessage": getattr(self, 'price_area_message', "价格提示信息") or "价格提示信息",
            "processType": 0,
            "produceDepartment___code": getattr(self, 'produce_department_code', "00012") or "00012",
            "produceUnit___code": self.unit_code or "KGM",
            "productBuyer___code": getattr(self, 'product_buyer_code', "test1") or "test1",
            "productionMode": 0,
            "productVendor___code": getattr(self, 'product_vendor_code', "0001000102") or "0001000102",
            "projectTrackStrategy": 0,
            "purchaseOrderQuantity": 0,
            "purchasePriceUnit___code": self.unit_code or "KGM",
            "purchaseTimes": 0,
            "purchaseUnit___code": self.unit_code or "KGM",
            "purpose": 1,
            "rangeType": 1,
            "receiptModel": {
                "zh_CN": getattr(self, 'receipt_model_zh_cn', "") or "",
                "en_US": getattr(self, 'receipt_model_en_us', "") or "",
                "zh_TW": getattr(self, 'receipt_model_zh_tw', "") or ""
            },
            "receiptName": {
                "zh_CN": getattr(self, 'receipt_name_zh_cn', "") or "",
                "en_US": getattr(self, 'receipt_name_en_us', "") or "",
                "zh_TW": getattr(self, 'receipt_name_zh_tw', "") or ""
            },
            "receiptSpec": {
                "zh_CN": getattr(self, 'receipt_spec_zh_cn', "") or "",
                "en_US": getattr(self, 'receipt_spec_en_us', "") or "",
                "zh_TW": getattr(self, 'receipt_spec_zh_tw', "") or ""
            },
            "receiptWarehouse___code": getattr(self, 'receipt_warehouse_code', "test1") or "test1",
            "recheckReminderLeadTime": 1,
            "rejectRate": 0,
            "remark": {
                "zh_CN": getattr(self, 'remark_zh_cn', "") or "",
                "en_US": getattr(self, 'remark_en_us', "") or "",
                "zh_TW": getattr(self, 'remark_zh_tw', "") or ""
            },
            "requestOrderLimit": 0,
            "requirementTrackingMethod": 0,
            "requireUnit___code": self.unit_code or "KGM",
            "reservation": False,
            "resetBackwardDays": 0,
            "resetForwardDays": 0,
            "retailPriceDimension": 1,
            "returnInspection": 0,
            "returnsWarehousingByResult": True,
            "returnWarehouse___code": getattr(self, 'return_warehouse_code', "test1") or "test1",
            "reviewCycle": 0,
            "reviewGrossWeight": False,
            "ropStock": 0,
            "safetyStock": getattr(self, 'safety_stock', 10) or 10,
            "saleChannel": getattr(self, 'sale_channel', "1,2,3") or "1,2,3",
            "saleChannelOfDistribution": False,
            "saleChannelOfOfflineRetail": False,
            "saleChannelOfOnlineBatch": False,
            "saleChannelOfOnlineRetail": False,
            "salePoints": 0,
            "salesReturnsExemption": False,
            "saleStyle": "1",
            "scanCountUnit": 0,
            "sendInspection": 0,
            "serviceDuration": 0,
            "serviceDurationUnit": 1,
            "shopId___code": getattr(self, 'shop_id_code', "test1") or "test1",
            "shortName": getattr(self, 'short_name', "物料简称") or "物料简称",
            "singleInspection": 0,
            "specialCarTransport": False,
            "specialMaterials": False,
            "stockUnit___code": self.unit_code or "KGM",
            "storageLossRate": 1,
            "strategyComparisonRule": 0,
            "supplyDemandPolicy": 0,
            "supplyTimes": 0,
            "supplyType": 0,
            "testRule": 1,
            "titleMemo": {
                "zh_CN": getattr(self, 'title_memo_zh_cn', "") or "",
                "en_US": getattr(self, 'title_memo_en_us', "") or "",
                "zh_TW": getattr(self, 'title_memo_zh_tw', "") or ""
            },
            "uorderDlyFeeRuleId": 2281192894353664,
            "uorderdowncount": 0,
            "uorderupcount": 0,
            "utility": False,
            "validityWarningDays": 0,
            "valueManageType": 0,
            "virtualPart": False,
            "warehouseManager___code": getattr(self, 'warehouse_manager_code', "test1") or "test1",
            "warehousingByResult": False,
            "wastageRate": 0,
            "weigh": False,
            "weighingMode": 0,
            "workingPlan": False,
            "deliveryMethod": "1,2,3"
        }
