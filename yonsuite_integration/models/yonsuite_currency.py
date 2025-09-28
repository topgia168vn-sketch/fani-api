# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteCurrency(models.Model):
    _name = 'yonsuite.currency'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Currency'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Currency ID from YonSuite API'
    )

    code = fields.Char(
        string='Currency Code',
        help='Currency code from YonSuite (e.g., CNY, USD)'
    )

    name = fields.Char(
        string='Currency Name',
        required=True,
        help='Currency name'
    )

    # Thông tin tên đa ngôn ngữ
    name_zh_tw = fields.Char(
        string='Name (zh_TW)',
        readonly=True,
        help='Currency name in Traditional Chinese'
    )

    name_vi_vn = fields.Char(
        string='Name (vi_VN)',
        readonly=True,
        help='Currency name in Vietnamese'
    )

    name_zh_cn = fields.Char(
        string='Name (zh_CN)',
        readonly=True,
        help='Currency name in Simplified Chinese'
    )

    name_en_us = fields.Char(
        string='Name (en_US)',
        readonly=True,
        help='Currency name in English'
    )

    # Thông tin ký hiệu và định dạng
    curr_type_sign = fields.Char(
        string='Currency Sign',
        readonly=True,
        help='Currency symbol (e.g., ¥, $)'
    )

    money_digit = fields.Integer(
        string='Money Digit',
        default=2,
        help='Number of decimal places for money'
    )

    price_digit = fields.Integer(
        string='Price Digit',
        default=2,
        help='Number of decimal places for price'
    )

    money_round = fields.Integer(
        string='Money Round',
        default=4,
        help='Money rounding precision'
    )

    price_round = fields.Integer(
        string='Price Round',
        default=4,
        help='Price rounding precision'
    )

    # Thông tin hệ thống
    sysid = fields.Char(
        string='System ID',
        readonly=True,
        help='System ID'
    )

    ytenant = fields.Char(
        string='YonSuite Tenant',
        readonly=True,
        help='YonSuite tenant'
    )

    tenant = fields.Char(
        string='Tenant',
        readonly=True,
        help='Tenant'
    )

    source_unique = fields.Char(
        string='Source Unique',
        readonly=True,
        help='Source unique identifier'
    )

    # Thông tin trạng thái
    dr = fields.Integer(
        string='DR',
        default=0,
        help='DR field'
    )

    is_default = fields.Boolean(
        string='Is Default',
        default=False,
        help='Is default currency'
    )

    enable = fields.Boolean(
        string='Enable',
        default=True,
        help='Is currency enabled'
    )

    order_grade = fields.Integer(
        string='Order Grade',
        default=0,
        help='Order grade for sorting'
    )

    # Thông tin người dùng
    modifier = fields.Char(
        string='Modifier ID',
        readonly=True,
        help='Modifier user ID'
    )

    modifier_code = fields.Char(
        string='Modifier Code',
        readonly=True,
        help='Modifier user code'
    )

    modifier_name = fields.Char(
        string='Modifier Name',
        readonly=True,
        help='Modifier user name'
    )

    # Thông tin thời gian
    creationtime = fields.Datetime(
        string='Creation Time',
        readonly=True,
        help='Creation timestamp'
    )

    modifiedtime = fields.Datetime(
        string='Modified Time',
        readonly=True,
        help='Last modification timestamp'
    )

    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

    # Trạng thái đồng bộ
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this currency was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync currency data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu currency
        api_service = self.env['yonsuite.api']
        result = api_service.get_currencies_from_api()

        if result.get("code") == "200":
            currencies_data = result.get("data", {}).get("recordList", [])

            # Tìm currency hiện tại trong dữ liệu trả về
            current_currency = None
            for currency_item in currencies_data:
                if str(currency_item.get("id")) == str(self.yonsuite_id):
                    current_currency = currency_item
                    break

            if current_currency:
                # Cập nhật dữ liệu currency
                self._update_currency_from_api_data(current_currency)

                self.write({
                    'state': 'synced',
                    'last_sync_date': fields.Datetime.now(),
                    'sync_error_message': False
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Currency "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Currency not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_currency_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu currency từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_currency_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset currency to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_currencies_pagination(self):
        """
        Sync currencies từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.currencies_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu currencies
        api_service = self.env['yonsuite.api']
        result = api_service.get_currencies_from_api(current_page, page_size)

        if result.get("code") == "200":
            currencies_data = result.get("data", {}).get("recordList", [])

            if not currencies_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.currencies_current_page', '1')
                _logger.info("No more currencies data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(currencies_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(currencies_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(currency_item.get("id")) for currency_item in currencies_data]

            # Search một lần duy nhất tất cả currencies đã tồn tại
            existing_currencies = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_currencies_dict = {c.yonsuite_id: c for c in existing_currencies}

            # Lưu currencies vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for currency_item in currencies_data:
                yonsuite_id = str(currency_item.get("id"))
                currency = existing_currencies_dict.get(yonsuite_id)

                if not currency:
                    # Tạo currency mới với đầy đủ dữ liệu
                    name_data = currency_item.get("name", {})
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': name_data.get("en_US") or name_data.get("zh_CN") or currency_item.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_currency_data_from_api(currency_item))

                    currency = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modifiedtime có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modifiedtime = api_service._convert_datetime_string(currency_item.get("modifiedtime"))

                    if api_modifiedtime and currency.modifiedtime != api_modifiedtime:
                        currency._update_currency_from_api_data(currency_item)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.currencies_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.currencies_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.currencies_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.currencies_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.currencies_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.currencies_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync currencies from YonSuite: %s", error_msg)
                return 0

    def _prepare_currency_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu currency từ API response
        """
        name_data = api_data.get("name", {})

        vals = {
            'code': api_data.get("code"),
            'name': name_data.get("en_US") or name_data.get("zh_CN") or api_data.get("code"),
            'name_zh_tw': name_data.get("zh_TW"),
            'name_vi_vn': name_data.get("vi_VN"),
            'name_zh_cn': name_data.get("zh_CN"),
            'name_en_us': name_data.get("en_US"),
            'curr_type_sign': api_data.get("currTypeSign"),
            'money_digit': api_data.get("moneyDigit", 2),
            'price_digit': api_data.get("priceDigit", 2),
            'money_round': api_data.get("moneyRount", 4),
            'price_round': api_data.get("priceRount", 4),
            'sysid': api_data.get("sysid"),
            'ytenant': api_data.get("ytenant"),
            'tenant': api_data.get("tenant"),
            'source_unique': api_data.get("sourceUnique"),
            'dr': api_data.get("dr", 0),
            'is_default': api_data.get("isDefault") == "1" if api_data.get("isDefault") else False,
            'enable': api_data.get("enable", True),
            'order_grade': api_data.get("orderGrade", 0),
            'modifier': api_data.get("modifier"),
            'modifier_code': api_data.get("modifier___code"),
            'modifier_name': api_data.get("modifier___name"),
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("creationtime"):
            converted_datetime = api_service._convert_datetime_string(api_data["creationtime"])
            if converted_datetime:
                vals['creationtime'] = converted_datetime

        if api_data.get("modifiedtime"):
            converted_datetime = api_service._convert_datetime_string(api_data["modifiedtime"])
            if converted_datetime:
                vals['modifiedtime'] = converted_datetime

        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        return vals
