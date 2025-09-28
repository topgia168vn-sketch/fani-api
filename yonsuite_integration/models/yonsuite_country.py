# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteCountry(models.Model):
    _name = 'yonsuite.country'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Country'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Country ID from YonSuite API'
    )

    code = fields.Char(
        string='Country Code',
        help='Country code from YonSuite'
    )

    name = fields.Char(
        string='Country Name',
        required=True,
        help='Country name'
    )

    # Thông tin mã quốc gia
    alpha_code = fields.Char(
        string='Alpha Code',
        readonly=True,
        help='Alpha code (3-letter country code)'
    )

    numeric_code = fields.Char(
        string='Numeric Code',
        readonly=True,
        help='Numeric country code'
    )

    # Thông tin tên đa ngôn ngữ
    name_zh_tw = fields.Char(
        string='Name (zh_TW)',
        readonly=True,
        help='Country name in Traditional Chinese'
    )

    name_vi_vn = fields.Char(
        string='Name (vi_VN)',
        readonly=True,
        help='Country name in Vietnamese'
    )

    name_zh_cn = fields.Char(
        string='Name (zh_CN)',
        readonly=True,
        help='Country name in Simplified Chinese'
    )

    name_en_us = fields.Char(
        string='Name (en_US)',
        readonly=True,
        help='Country name in English'
    )

    # Thông tin hệ thống
    name_resid = fields.Char(
        string='Name Resource ID',
        readonly=True,
        help='Name resource ID'
    )

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

    ispreset = fields.Boolean(
        string='Is Preset',
        default=False,
        help='Is preset country'
    )

    enable = fields.Boolean(
        string='Enable',
        default=True,
        help='Is country enabled'
    )

    sort_num = fields.Integer(
        string='Sort Number',
        default=0,
        help='Sort number'
    )

    # Thông tin thời gian
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
        help='Last time this country was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync country data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu country
        api_service = self.env['yonsuite.api']
        result = api_service.get_countries_from_api()

        if result.get("code") == "200":
            countries_data = result.get("data", {}).get("recordList", [])

            # Tìm country hiện tại trong dữ liệu trả về
            current_country = None
            for country_item in countries_data:
                if str(country_item.get("id")) == str(self.yonsuite_id):
                    current_country = country_item
                    break

            if current_country:
                # Cập nhật dữ liệu country
                self._update_country_from_api_data(current_country)

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
                        'message': _('Country "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Country not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_country_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu country từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_country_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset country to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_countries_pagination(self):
        """
        Sync countries từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.countries_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu countries
        api_service = self.env['yonsuite.api']
        result = api_service.get_countries_from_api(current_page, page_size)

        if result.get("code") == "200":
            countries_data = result.get("data", {}).get("recordList", [])

            if not countries_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.countries_current_page', '1')
                _logger.info("No more countries data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(countries_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(countries_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(country_item.get("id")) for country_item in countries_data]

            # Search một lần duy nhất tất cả countries đã tồn tại
            existing_countries = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_countries_dict = {c.yonsuite_id: c for c in existing_countries}

            # Lưu countries vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for country_item in countries_data:
                yonsuite_id = str(country_item.get("id"))
                country = existing_countries_dict.get(yonsuite_id)

                if not country:
                    # Tạo country mới với đầy đủ dữ liệu
                    name_data = country_item.get("name", {})
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': name_data.get("en_US") or name_data.get("zh_CN") or country_item.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_country_data_from_api(country_item))

                    country = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra pubts có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_pubts = api_service._convert_datetime_string(country_item.get("pubts"))

                    if api_pubts and country.pubts != api_pubts:
                        country._update_country_from_api_data(country_item)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.countries_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.countries_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.countries_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.countries_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.countries_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.countries_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync countries from YonSuite: %s", error_msg)
                return 0

    def _prepare_country_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu country từ API response
        """
        name_data = api_data.get("name", {})

        vals = {
            'code': api_data.get("code"),
            'name': name_data.get("en_US") or name_data.get("zh_CN") or api_data.get("code"),
            'alpha_code': api_data.get("alpha_code"),
            'numeric_code': api_data.get("numeric_code"),
            'name_zh_tw': name_data.get("zh_TW"),
            'name_vi_vn': name_data.get("vi_VN"),
            'name_zh_cn': name_data.get("zh_CN"),
            'name_en_us': name_data.get("en_US"),
            'name_resid': api_data.get("name_resid"),
            'sysid': api_data.get("sysid"),
            'ytenant': api_data.get("ytenant"),
            'tenant': api_data.get("tenant"),
            'source_unique': api_data.get("sourceUnique"),
            'dr': api_data.get("dr", 0),
            'ispreset': api_data.get("ispreset", False),
            'enable': api_data.get("enable", True),
            'sort_num': api_data.get("sort_num", 0),
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        return vals
