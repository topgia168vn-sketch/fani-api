# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class YonsuiteOrder(models.Model):
    _name = 'yonsuite.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Order'
    _order = 'create_date desc'
    _rec_name = 'code'

    name = fields.Char(
        string='Order Name',
        help='Name of the order'
    )

    yonsuite_id = fields.Char(
        string='YonSuite Order ID',
        readonly=True,
        copy=False,
        help='Order ID from YonSuite API'
    )

    code = fields.Char(
        string='Order Code',
        help='Order code from YonSuite'
    )

    # Basic order info
    status = fields.Integer(
        string='Status (API)',
        help='Order status from YonSuite API'
    )

    verifystate = fields.Integer(
        string='Verify State',
        help='Verify state from YonSuite'
    )

    quote_status = fields.Char(
        string='Quote Status',
        help='Quote status from YonSuite'
    )

    # Contact information
    receive_contacter = fields.Char(
        string='Receive Contacter',
        help='Receive contacter from YonSuite'
    )

    receive_contacter_phone = fields.Char(
        string='Receive Contacter Phone',
        help='Receive contacter phone from YonSuite'
    )

    corp_contact = fields.Char(
        string='Corp Contact',
        help='Corp contact from YonSuite'
    )

    corp_contact_user_name = fields.Char(
        string='Corp Contact User Name',
        help='Corp contact user name from YonSuite'
    )

    # Agent information
    agent_id = fields.Char(
        string='Agent ID',
        help='Agent ID from YonSuite'
    )

    agent_id_name = fields.Char(
        string='Agent Name',
        help='Agent name from YonSuite'
    )

    # Transaction type
    transaction_type_id = fields.Char(
        string='Transaction Type ID',
        help='Transaction type ID from YonSuite'
    )

    transaction_type_code = fields.Char(
        string='Transaction Type Code',
        help='Transaction type code from YonSuite'
    )

    transaction_type_name = fields.Char(
        string='Transaction Type Name',
        help='Transaction type name from YonSuite'
    )

    # Quote person
    quote_person_id = fields.Char(
        string='Quote Person ID',
        help='Quote person ID from YonSuite'
    )

    quote_person_id_name = fields.Char(
        string='Quote Person Name',
        help='Quote person name from YonSuite'
    )

    # Auditor
    auditor_id = fields.Char(
        string='Auditor ID',
        help='Auditor ID from YonSuite'
    )

    auditor_id_name = fields.Char(
        string='Auditor Name',
        help='Auditor name from YonSuite'
    )

    # Dates
    vouchdate = fields.Datetime(
        string='Vouch Date',
        help='Vouch date from YonSuite'
    )

    audit_time = fields.Datetime(
        string='Audit Time',
        help='Audit time from YonSuite'
    )

    auto_check_date = fields.Datetime(
        string='Auto Check Date',
        help='Auto check date from YonSuite'
    )

    validity_date_begin = fields.Datetime(
        string='Validity Date Begin',
        help='Validity date begin from YonSuite'
    )

    validity_date_end = fields.Datetime(
        string='Validity Date End',
        help='Validity date end from YonSuite'
    )

    open_date = fields.Datetime(
        string='Open Date',
        help='Open date from YonSuite'
    )

    # Currency information
    currency = fields.Char(
        string='Currency (API)',
        help='Currency from YonSuite API'
    )

    currency_name = fields.Char(
        string='Currency Name',
        help='Currency name from YonSuite'
    )

    # Currency relation
    currency_id = fields.Many2one(
        'yonsuite.currency',
        string='Currency',
        help='Related YonSuite Currency'
    )

    currency_price_digit = fields.Integer(
        string='Currency Price Digit',
        help='Currency price digit from YonSuite'
    )

    currency_money_digit = fields.Integer(
        string='Currency Money Digit',
        help='Currency money digit from YonSuite'
    )

    nat_currency = fields.Char(
        string='Native Currency',
        help='Native currency from YonSuite'
    )

    nat_currency_name = fields.Char(
        string='Native Currency Name',
        help='Native currency name from YonSuite'
    )

    nat_currency_code = fields.Char(
        string='Native Currency Code',
        help='Native currency code from YonSuite'
    )

    nat_currency_price_digit = fields.Integer(
        string='Native Currency Price Digit',
        help='Native currency price digit from YonSuite'
    )

    nat_currency_money_digit = fields.Integer(
        string='Native Currency Money Digit',
        help='Native currency money digit from YonSuite'
    )
    currency_code = fields.Char(
        string='Currency Code',
        help='Currency code from YonSuite'
    )
    currency_price_rount = fields.Integer(
        string='Currency Price Round',
        help='Currency price round from YonSuite'
    )
    currency_money_rount = fields.Integer(
        string='Currency Money Round',
        help='Currency money round from YonSuite'
    )
    nat_currency_price_rount = fields.Integer(
        string='Native Currency Price Round',
        help='Native currency price round from YonSuite'
    )
    nat_currency_money_rount = fields.Integer(
        string='Native Currency Money Round',
        help='Native currency money round from YonSuite'
    )

    # Exchange rate
    exchange_rate_type = fields.Char(
        string='Exchange Rate Type',
        help='Exchange rate type from YonSuite'
    )

    exchange_rate_type_name = fields.Char(
        string='Exchange Rate Type Name',
        help='Exchange rate type name from YonSuite'
    )

    exch_rate_date = fields.Datetime(
        string='Exchange Rate Date',
        help='Exchange rate date from YonSuite'
    )

    exch_rate = fields.Float(
        string='Exchange Rate',
        digits='Exchange Rate',
        help='Exchange rate from YonSuite'
    )
    exchange_rate_type_digit = fields.Integer(
        string='Exchange Rate Type Digit',
        help='Exchange rate type digit from YonSuite'
    )

    # Money fields
    quote_table_total_money = fields.Float(
        string='Quote Table Total Money',
        digits='Product Price',
        help='Quote table total money from YonSuite'
    )
    total_money = fields.Float(
        string='Total Money',
        digits='Product Price',
        help='Total money from YonSuite'
    )
    total_ori_money = fields.Float(
        string='Total Original Money',
        digits='Product Price',
        help='Total original money from YonSuite'
    )
    total_ori_tax = fields.Float(
        string='Total Original Tax',
        digits='Product Price',
        help='Total original tax from YonSuite'
    )
    total_particularly_money = fields.Float(
        string='Total Particularly Money',
        digits='Product Price',
        help='Total particularly money from YonSuite'
    )

    total_discount_sum = fields.Float(
        string='Total Discount Sum',
        digits='Product Price',
        help='Total discount sum from YonSuite'
    )

    total_discount_rate = fields.Float(
        string='Total Discount Rate',
        digits='Product Price',
        help='Total discount rate from YonSuite'
    )

    whole_favorable_rate = fields.Float(
        string='Whole Favorable Rate',
        digits='Product Price',
        help='Whole favorable rate from YonSuite'
    )

    # Organization
    sales_org_id = fields.Char(
        string='Sales Organization ID',
        help='Sales organization ID from YonSuite'
    )

    sales_org_id_name = fields.Char(
        string='Sales Organization Name',
        help='Sales organization name from YonSuite'
    )

    # Invoice type
    invoice_type_id = fields.Char(
        string='Invoice Type ID',
        help='Invoice type ID from YonSuite'
    )

    invoice_type_id_code = fields.Char(
        string='Invoice Type Code',
        help='Invoice type code from YonSuite'
    )

    invoice_type_id_name = fields.Char(
        string='Invoice Type Name',
        help='Invoice type name from YonSuite'
    )
    invoice_title_type = fields.Char(
        string='Invoice Title Type',
        help='Invoice title type from YonSuite'
    )
    modify_invoice_type = fields.Boolean(
        string='Modify Invoice Type',
        help='Modify invoice type flag from YonSuite'
    )
    invoice_agent_id = fields.Char(
        string='Invoice Agent ID',
        help='Invoice agent ID from YonSuite'
    )
    invoice_agent_id_name = fields.Char(
        string='Invoice Agent Name',
        help='Invoice agent name from YonSuite'
    )

    # Flags
    is_wf_controlled = fields.Boolean(
        string='Is WF Controlled',
        help='Is workflow controlled from YonSuite'
    )

    is_potential = fields.Boolean(
        string='Is Potential',
        help='Is potential from YonSuite'
    )

    # Variant configuration
    variant_config_cts_version = fields.Char(
        string='Variant Config Version',
        help='Variant configuration version from YonSuite'
    )

    variant_config_cts_code = fields.Char(
        string='Variant Config Code',
        help='Variant configuration code from YonSuite'
    )

    variant_config_cts_id = fields.Char(
        string='Variant Config ID',
        help='Variant configuration ID from YonSuite'
    )

    variant_configuration = fields.Char(
        string='Variant Configuration',
        help='Variant configuration from YonSuite'
    )

    # Optional
    optional_type = fields.Char(
        string='Optional Type',
        help='Optional type from YonSuite'
    )

    optional_quotation_id = fields.Char(
        string='Optional Quotation ID',
        help='Optional quotation ID from YonSuite'
    )

    optional_quotation_id_code = fields.Char(
        string='Optional Quotation Code',
        help='Optional quotation code from YonSuite'
    )

    # Exclusive tax
    exclusive_tax_quotation = fields.Integer(
        string='Exclusive Tax Quotation',
        help='Exclusive tax quotation from YonSuite'
    )

    # Memo
    memo = fields.Text(
        string='Memo',
        help='Memo from YonSuite'
    )
    bustype_extend_attrs_json = fields.Text(
        string='Business Type Extend Attrs',
        help='Business type extend attrs JSON from YonSuite'
    )

    # Timestamps
    pubts = fields.Datetime(
        string='Publish Time',
        help='Publish time from YonSuite'
    )
    audit_date = fields.Datetime(
        string='Audit Date',
        help='Audit date from YonSuite'
    )
    create_date_yonsuite = fields.Datetime(
        string='Create Date (YonSuite)',
        help='Create date from YonSuite'
    )
    create_time = fields.Datetime(
        string='Create Time',
        help='Create time from YonSuite'
    )
    quote_version = fields.Char(
        string='Quote Version',
        help='Quote version from YonSuite'
    )
    tax_setting_type = fields.Char(
        string='Tax Setting Type',
        help='Tax setting type from YonSuite'
    )
    data_source = fields.Char(
        string='Data Source',
        help='Data source from YonSuite'
    )
    source_terminal = fields.Char(
        string='Source Terminal',
        help='Source terminal from YonSuite'
    )
    agent_relation_id = fields.Char(
        string='Agent Relation ID',
        help='Agent relation ID from YonSuite'
    )
    customer = fields.Char(
        string='Customer ID',
        help='Customer ID from YonSuite'
    )
    customer_name = fields.Char(
        string='Customer Name',
        help='Customer name from YonSuite'
    )

    # Customer relation
    customer_id = fields.Many2one(
        'yonsuite.partner',
        string='Customer',
        help='Related YonSuite Partner (Customer)'
    )
    creator_id = fields.Char(
        string='Creator ID',
        help='Creator ID from YonSuite'
    )
    creator = fields.Char(
        string='Creator',
        help='Creator from YonSuite'
    )
    auditor = fields.Char(
        string='Auditor',
        help='Auditor from YonSuite'
    )
    change_status = fields.Integer(
        string='Change Status',
        help='Change status from YonSuite'
    )
    return_count = fields.Integer(
        string='Return Count',
        help='Return count from YonSuite'
    )
    master_org_key_field = fields.Char(
        string='Master Org Key Field',
        help='Master org key field from YonSuite'
    )
    trans_type_key_field = fields.Char(
        string='Trans Type Key Field',
        help='Trans type key field from YonSuite'
    )
    mdd_formula_execute_flag = fields.Char(
        string='MDD Formula Execute Flag',
        help='MDD formula execute flag from YonSuite'
    )

    # Order lines
    order_line_ids = fields.One2many(
        'yonsuite.order.line',
        'order_id',
        string='Order Lines',
        help='Order lines from YonSuite'
    )

    # Sync status fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this order was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_view_order_lines(self):
        """
        View order lines for this order
        """
        self.ensure_one()
        return {
            'name': _('Order Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'yonsuite.order.line',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id': self.id},
            'target': 'current',
        }

    @api.model
    def action_import_orders_pagination(self):
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.orders_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu orders
        result = self.env['yonsuite.api'].get_orders_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            orders_data = data.get("recordList", [])

            if not orders_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.orders_current_page', '1')
                _logger.info("No more orders data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(orders_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(orders_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(order_data.get("id")) for order_data in orders_data]

            # Search một lần duy nhất tất cả orders đã tồn tại
            existing_orders = self.env['yonsuite.order'].search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_orders_dict = {o.yonsuite_id: o for o in existing_orders}

            # Lưu orders vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for order_data in orders_data:
                yonsuite_id = str(order_data.get("id"))
                order = existing_orders_dict.get(yonsuite_id)
                order_detail = self.env['yonsuite.api'].get_order_detail_from_api(yonsuite_id)
                detail_payload = {}
                if order_detail and order_detail.get('code') == '200':
                    detail_payload = order_detail.get('data', {}) or {}
                if not order:
                    # Tạo mới order
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': order_data.get("name"),
                    }

                    # Thêm dữ liệu từ API
                    # Ưu tiên detail payload nếu có, fallback list record
                    vals.update(self._prepare_order_data_from_api(detail_payload or order_data))

                    order = self.env['yonsuite.order'].create(vals)

                    # Tạo order lines
                    # Nếu có childs trong detail, tạo từ childs, ngược lại từ record list
                    if detail_payload.get('childs'):
                        for child in detail_payload.get('childs'):
                            self._create_order_lines(order, child)
                    else:
                        self._create_order_lines(order, order_data)

                    created_count += 1
                else:
                    # Order đã tồn tại, kiểm tra có cần cập nhật không
                    # Vì API không trả về modify_time, ta sẽ cập nhật luôn
                    order._update_order_from_api_data(detail_payload or order_data)

                    # Cập nhật order lines
                    if detail_payload.get('childs'):
                        for child in detail_payload.get('childs'):
                            self._update_order_lines(order, child)
                    else:
                        self._update_order_lines(order, order_data)

                    updated_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.orders_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.orders_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.orders_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.orders_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.orders_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.orders_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync orders from YonSuite: %s", error_msg)
                return 0

    def _prepare_order_data_from_api(self, api_data):
        """
        Prepare order data from API response
        """
        vals = {
            'yonsuite_id': str(api_data.get("id")),
            'name': api_data.get("name"),
            'code': api_data.get("code"),
            'status': api_data.get("status", 0),
            'verifystate': api_data.get("verifystate", 0),
            'quote_status': api_data.get("quoteStatus"),
            'receive_contacter': api_data.get("receiveContacter"),
            'receive_contacter_phone': api_data.get("receiveContacterPhone"),
            'corp_contact': api_data.get("corpContact"),
            'corp_contact_user_name': api_data.get("corpContactUserName"),
            'agent_id': str(api_data.get("agentId")) if api_data.get("agentId") else False,
            'agent_id_name': api_data.get("agentId_name"),
            'transaction_type_id': api_data.get("transactionTypeId"),
            'transaction_type_code': api_data.get("transactionTypeId_code"),
            'transaction_type_name': api_data.get("transactionTypeId_name"),
            'quote_person_id': str(api_data.get("quotePersonId")) if api_data.get("quotePersonId") else False,
            'quote_person_id_name': api_data.get("quotePersonId_name"),
            'auditor_id': api_data.get("auditorId"),
            'auditor_id_name': api_data.get("auditorId_name"),
            'currency': api_data.get("currency"),
            'currency_name': api_data.get("currency_name"),
            'currency_price_digit': api_data.get("currency_priceDigit", 0),
            'currency_money_digit': api_data.get("currency_moneyDigit", 0),
            'nat_currency': api_data.get("natCurrency"),
            'nat_currency_name': api_data.get("natCurrency_name"),
            'nat_currency_code': api_data.get("natCurrency_code"),
            'nat_currency_price_digit': api_data.get("natCurrency_priceDigit", 0),
            'nat_currency_money_digit': api_data.get("natCurrency_moneyDigit", 0),
            'exchange_rate_type': api_data.get("exchangeRateType"),
            'exchange_rate_type_name': api_data.get("exchangeRateType_name"),
            'exch_rate': api_data.get("exchRate", 0.0),
            'quote_table_total_money': api_data.get("quoteTableTotalMoney", 0.0),
            'total_discount_sum': api_data.get("totalDiscountSum", 0.0),
            'total_discount_rate': api_data.get("totalDiscountRate", 0.0),
            'whole_favorable_rate': api_data.get("wholeFavorableRate", 0.0),
            'sales_org_id': api_data.get("salesOrgId"),
            'sales_org_id_name': api_data.get("salesOrgId_name"),
            'invoice_type_id': api_data.get("invoiceTypeId"),
            'invoice_type_id_code': api_data.get("invoiceTypeIdCode"),
            'invoice_type_id_name': api_data.get("invoiceTypeIdName"),
            'is_wf_controlled': api_data.get("isWfControlled", False),
            'is_potential': api_data.get("isPotential", False),
            'variant_config_cts_version': api_data.get("variantconfigctsVersion"),
            'variant_config_cts_code': api_data.get("variantconfigctsCode"),
            'variant_config_cts_id': str(api_data.get("variantconfigctsId")) if api_data.get("variantconfigctsId") else False,
            'variant_configuration': str(api_data.get("variantConfiguration")) if api_data.get("variantConfiguration") else False,
            'optional_type': api_data.get("optionalType"),
            'optional_quotation_id': str(api_data.get("optionalQuotationId")) if api_data.get("optionalQuotationId") else False,
            'optional_quotation_id_code': api_data.get("optionalQuotationIdCode"),
            'exclusive_tax_quotation': api_data.get("exclusiveTaxQuotation", 0),
            'memo': api_data.get("memo"),
        }

        # Extra totals and amounts
        if api_data.get("totalMoney") is not None:
            vals['total_money'] = api_data.get("totalMoney")
        if api_data.get("totalOriMoney") is not None:
            vals['total_ori_money'] = api_data.get("totalOriMoney")
        if api_data.get("totalOriTax") is not None:
            vals['total_ori_tax'] = api_data.get("totalOriTax")
        if api_data.get("totalParticularlyMoney") is not None:
            vals['total_particularly_money'] = api_data.get("totalParticularlyMoney")

        # Currency extras
        if api_data.get("currency_code"):
            vals['currency_code'] = api_data.get("currency_code")
        if api_data.get("currency_priceRount") is not None:
            vals['currency_price_rount'] = api_data.get("currency_priceRount")
        if api_data.get("currency_moneyRount") is not None:
            vals['currency_money_rount'] = api_data.get("currency_moneyRount")
        if api_data.get("natCurrency_priceRount") is not None:
            vals['nat_currency_price_rount'] = api_data.get("natCurrency_priceRount")
        if api_data.get("natCurrency_moneyRount") is not None:
            vals['nat_currency_money_rount'] = api_data.get("natCurrency_moneyRount")

        # Exchange rate extras
        if api_data.get("exchangeRateType_digit") is not None:
            vals['exchange_rate_type_digit'] = api_data.get("exchangeRateType_digit")

        # Invoice extras
        if api_data.get("invoiceTitleType") is not None:
            vals['invoice_title_type'] = api_data.get("invoiceTitleType")
        if api_data.get("modifyInvoiceType") is not None:
            vals['modify_invoice_type'] = api_data.get("modifyInvoiceType")
        if api_data.get("invoiceAgentId"):
            vals['invoice_agent_id'] = str(api_data.get("invoiceAgentId"))
        if api_data.get("invoiceAgentId_name"):
            vals['invoice_agent_id_name'] = api_data.get("invoiceAgentId_name")

        # Other identifiers/info
        if api_data.get("agentRelationId"):
            vals['agent_relation_id'] = str(api_data.get("agentRelationId"))
        if api_data.get("customer"):
            vals['customer'] = str(api_data.get("customer"))
        if api_data.get("customer_name"):
            vals['customer_name'] = api_data.get("customer_name")

        # Link currency relation
        if api_data.get("currency"):
            currency = self.env['yonsuite.currency'].search([
                ('yonsuite_id', '=', str(api_data.get("currency")))
            ], limit=1)
            if currency:
                vals['currency_id'] = currency.id

        # Link customer relation
        if api_data.get("customer"):
            customer = self.env['yonsuite.partner'].search([
                ('yonsuite_id', '=', str(api_data.get("customer")))
            ], limit=1)
            if customer:
                vals['customer_id'] = customer.id
        if api_data.get("creatorId"):
            vals['creator_id'] = str(api_data.get("creatorId"))
        if api_data.get("creator"):
            vals['creator'] = api_data.get("creator")
        if api_data.get("auditor"):
            vals['auditor'] = api_data.get("auditor")
        if api_data.get("changestatus") is not None:
            vals['change_status'] = api_data.get("changestatus")
        if api_data.get("returncount") is not None:
            vals['return_count'] = api_data.get("returncount")
        if api_data.get("masterOrgKeyField"):
            vals['master_org_key_field'] = api_data.get("masterOrgKeyField")
        if api_data.get("transTypeKeyField"):
            vals['trans_type_key_field'] = api_data.get("transTypeKeyField")
        if api_data.get("_mddFormulaExecuteFlag"):
            vals['mdd_formula_execute_flag'] = api_data.get("_mddFormulaExecuteFlag")
        if api_data.get("bustype_extend_attrs_json"):
            vals['bustype_extend_attrs_json'] = api_data.get("bustype_extend_attrs_json")
        if api_data.get("dataSource"):
            vals['data_source'] = api_data.get("dataSource")
        if api_data.get("sourceTerminal"):
            vals['source_terminal'] = api_data.get("sourceTerminal")

        # Handle datetime fields
        if api_data.get("vouchdate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["vouchdate"])
            if converted_datetime:
                vals['vouchdate'] = converted_datetime

        if api_data.get("auditTime"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["auditTime"])
            if converted_datetime:
                vals['audit_time'] = converted_datetime

        if api_data.get("autoCheckDate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["autoCheckDate"])
            if converted_datetime:
                vals['auto_check_date'] = converted_datetime

        if api_data.get("validityDateBegin"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["validityDateBegin"])
            if converted_datetime:
                vals['validity_date_begin'] = converted_datetime

        if api_data.get("validityDateEnd"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["validityDateEnd"])
            if converted_datetime:
                vals['validity_date_end'] = converted_datetime

        if api_data.get("openDate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["openDate"])
            if converted_datetime:
                vals['open_date'] = converted_datetime

        if api_data.get("exchRateDate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["exchRateDate"])
            if converted_datetime:
                vals['exch_rate_date'] = converted_datetime

        if api_data.get("pubts"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        if api_data.get("auditDate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["auditDate"])
            if converted_datetime:
                vals['audit_date'] = converted_datetime

        if api_data.get("createDate"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["createDate"])
            if converted_datetime:
                vals['create_date_yonsuite'] = converted_datetime

        if api_data.get("createTime"):
            converted_datetime = self.env['yonsuite.api']._convert_datetime_string(api_data["createTime"])
            if converted_datetime:
                vals['create_time'] = converted_datetime

        return vals

    def _prepare_order_line_data_from_api(self, line_data):
        """
        Prepare order line data from API response
        """
        vals = {
            'yonsuite_id': str(line_data.get("childs_id")) if line_data.get("childs_id") else (str(line_data.get("id")) if line_data.get("id") else False),
            'childs_product_id': str(line_data.get("childs_productId")) if line_data.get("childs_productId") else (str(line_data.get("productId")) if line_data.get("productId") else False),
            'childs_product_id_code': line_data.get("childs_productId_code") or line_data.get("productId_code"),
            'childs_product_id_name': line_data.get("childs_productId_name") or line_data.get("productId_name"),
            'childs_product_id_model': line_data.get("childs_productId_model"),
            'childs_product_id_model_description': line_data.get("childs_productId_modelDescription"),
            'childs_sku_id': str(line_data.get("childs_skuId")) if line_data.get("childs_skuId") else (str(line_data.get("skuId")) if line_data.get("skuId") else False),
            'childs_sku_id_code': line_data.get("childs_skuId_code") or line_data.get("skuId_code"),
            'childs_sku_id_name': line_data.get("childs_skuId_name") or line_data.get("skuId_name"),
            'childs_sku_id_model': line_data.get("childs_skuId_model"),
            'childs_sku_id_model_description': line_data.get("childs_skuId_modelDescription"),
            'childs_product_class': str(line_data.get("childs_productClass")) if line_data.get("childs_productClass") else False,
            'childs_product_class_code': line_data.get("childs_productClass_code"),
            'childs_product_class_name': line_data.get("childs_productClass_name"),
            'childs_project_id': line_data.get("childs_projectId") or line_data.get("projectId"),
            'childs_project_id_code': line_data.get("childs_projectId_code") or line_data.get("projectId_code"),
            'childs_project_id_name': line_data.get("childs_projectId_name") or line_data.get("projectId_name"),
            'childs_master_unit_id': str(line_data.get("childs_masterUnitId")) if line_data.get("childs_masterUnitId") else (str(line_data.get("masterUnitId")) if line_data.get("masterUnitId") else False),
            'childs_master_unit_id_name': line_data.get("childs_masterUnitId_name") or line_data.get("masterUnitId_name"),
            'childs_master_unit_id_precision': line_data.get("childs_masterUnitId_precision") or line_data.get("masterUnitId_precision", 0),
            'childs_sale_unit_id': str(line_data.get("childs_saleunitId")) if line_data.get("childs_saleunitId") else (str(line_data.get("saleunitId")) if line_data.get("saleunitId") else False),
            'childs_sale_unit_id_name': line_data.get("childs_saleunitId_name") or line_data.get("saleunitId_name"),
            'childs_sale_unit_id_precision': line_data.get("childs_saleunitId_precision") or line_data.get("saleunitId_precision", 0),
            'childs_cqt_unit_id': str(line_data.get("childs_cqtUnitId")) if line_data.get("childs_cqtUnitId") else (str(line_data.get("cqtUnitId")) if line_data.get("cqtUnitId") else False),
            'childs_cqt_unit_id_name': line_data.get("childs_cqtUnitId_name") or line_data.get("cqtUnitId_name"),
            'childs_cqt_unit_id_precision': line_data.get("childs_cqtUnitId_precision") or line_data.get("cqtUnitId_precision", 0),
            'childs_qty': line_data.get("childs_qty", line_data.get("qty", 0.0)),
            'childs_sub_qty': line_data.get("childs_subQty", line_data.get("subQty", 0.0)),
            'childs_price_qty': line_data.get("childs_priceQty", line_data.get("priceQty", 0.0)),
            'childs_ori_unit_price': line_data.get("childs_oriUnitPrice", line_data.get("oriUnitPrice", 0.0)),
            'childs_ori_tax_unit_price': line_data.get("childs_oriTaxUnitPrice", line_data.get("oriTaxUnitPrice", 0.0)),
            'childs_nat_unit_price': line_data.get("childs_natUnitPrice", line_data.get("natUnitPrice", 0.0)),
            'childs_nat_tax_unit_price': line_data.get("childs_natTaxUnitPrice", line_data.get("natTaxUnitPrice", 0.0)),
            'childs_quote_sale_price': line_data.get("childs_quoteSalePrice"),
            'childs_ori_money': line_data.get("childs_oriMoney", line_data.get("oriMoney", 0.0)),
            'childs_ori_sum': line_data.get("childs_oriSum", line_data.get("oriSum", 0.0)),
            'childs_nat_money': line_data.get("childs_natMoney", line_data.get("natMoney", 0.0)),
            'childs_nat_sum': line_data.get("childs_natSum", line_data.get("natSum", 0.0)),
            'childs_discount_rate': line_data.get("childs_discountRate", line_data.get("discountRate", 0.0)),
            'childs_discount_sum': line_data.get("childs_discountSum", line_data.get("discountSum", 0.0)),
            'childs_discount_nat_sum': line_data.get("childs_discountNatSum", line_data.get("discountNatSum", 0.0)),
            'childs_favorable_rate': line_data.get("childs_favorableRate", line_data.get("favorableRate", 0.0)),
            'childs_cus_favorable_rate': line_data.get("childs_cusFavorableRate", line_data.get("cusFavorableRate", 0.0)),
            'childs_tax_rate': line_data.get("childs_taxRate", line_data.get("taxRate", 0.0)),
            'childs_quote_sale_cost': line_data.get("childs_quoteSaleCost"),
            'childs_forecast_cb_price': line_data.get("childs_forecastCBPrice", line_data.get("forecastCostPrice", 0.0)),
            'childs_forecast_cb_price_sum': line_data.get("childs_forecastCBPriceSum", line_data.get("forecastCostPriceSum", 0.0)),
            'childs_cost_currency': str(line_data.get("childs_costCurrency")) if line_data.get("childs_costCurrency") else False,
            'childs_cost_currency_name': line_data.get("childs_costCurrency_name"),
            'childs_settlement_org_id': line_data.get("childs_settlementOrgId") or line_data.get("settlementOrgId"),
            'childs_settlement_org_id_name': line_data.get("childs_settlementOrgId_name") or line_data.get("settlementOrgId_name"),
            'childs_total_push_sact_qty': line_data.get("childs_totalPushSactQty", 0.0),
            'childs_total_push_sale_qty': line_data.get("childs_totalPushSaleQty", 0.0),
            'childs_price_mark': line_data.get("childs_priceMark") or line_data.get("priceMark"),
            'childs_quotation_exclusive_tax_money': line_data.get("childs_quotationExclusiveTaxMoney"),
            'childs_basic_quotation': line_data.get("childs_basicQuotation"),
            'childs_basic_quotation_money': line_data.get("childs_basicQuotationMoney"),
            'childs_quotation_deduction_rate': line_data.get("childs_quotationDeductionRate"),
            'childs_quotation_deduction': line_data.get("childs_quotationDeduction"),
            'childs_lowest_selline_price': line_data.get("childs_lowestSellinePrice"),
        }

        return vals

    def _create_order_lines(self, order, order_data):
        """
        Create order lines from API data
        """
        # Tạo order line từ dữ liệu (có thể là phần tử trong 'childs')
        line_vals = self._prepare_order_line_data_from_api(order_data)
        line_vals['order_id'] = order.id

        # Tìm product relation: link bằng productId
        if line_vals.get('childs_product_id'):
            product = self.env['yonsuite.product'].search([
                ('yonsuite_id', '=', line_vals['childs_product_id'])
            ], limit=1)
            if product:
                line_vals['product_id'] = product.id

        self.env['yonsuite.order.line'].create(line_vals)

    def _update_order_lines(self, order, order_data):
        """
        Update order lines from API data
        """
        # Xác định id line theo childs_id hoặc id
        target_line_id = str(order_data.get("childs_id") or order_data.get("id") or '')
        existing_line = order.order_line_ids.filtered(lambda l: l.yonsuite_id == target_line_id)

        if existing_line:
            # Cập nhật line hiện tại
            line_vals = self._prepare_order_line_data_from_api(order_data)

            # Tìm product relation qua productId
            if line_vals.get('childs_product_id'):
                product = self.env['yonsuite.product'].search([
                    ('yonsuite_id', '=', line_vals['childs_product_id'])
                ], limit=1)
                if product:
                    line_vals['product_id'] = product.id

            existing_line.write(line_vals)
        else:
            # Tạo line mới
            self._create_order_lines(order, order_data)

    def _update_order_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu order từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_order_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    @api.model
    def action_update_existing_relations(self):
        """
        Cập nhật các liên kết cho các order đã tồn tại
        """
        orders = self.search([])
        updated_count = 0
        
        for order in orders:
            updated = False
            
            # Cập nhật currency relation
            if order.currency and not order.currency_id:
                currency = self.env['yonsuite.currency'].search([
                    ('yonsuite_id', '=', str(order.currency))
                ], limit=1)
                if currency:
                    order.currency_id = currency.id
                    updated = True
            
            # Cập nhật customer relation
            if order.customer and not order.customer_id:
                customer = self.env['yonsuite.partner'].search([
                    ('yonsuite_id', '=', str(order.customer))
                ], limit=1)
                if customer:
                    order.customer_id = customer.id
                    updated = True
            
            # Cập nhật order lines product relations
            for line in order.order_line_ids:
                if line.childs_product_id and not line.product_id:
                    product = self.env['yonsuite.product'].search([
                        ('yonsuite_id', '=', line.childs_product_id)
                    ], limit=1)
                    if product:
                        line.product_id = product.id
                        updated = True
            
            if updated:
                updated_count += 1
        
        _logger.info("Updated relations for %d orders", updated_count)
        return updated_count
