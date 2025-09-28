# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteBrand(models.Model):
    _name = 'yonsuite.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Brand'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Brand ID from YonSuite API'
    )

    code = fields.Char(
        string='Brand Code',
        help='Brand code from YonSuite'
    )

    name = fields.Char(
        string='Brand Name',
        required=True,
        help='Brand name'
    )

    simplified_name = fields.Char(
        string='Simplified Name',
        help='Simplified name from YonSuite'
    )

    english_name = fields.Char(
        string='English Name',
        help='English name from YonSuite'
    )

    # Thông tin mô tả
    brand_desc = fields.Text(
        string='Brand Description',
        help='Brand description'
    )

    brand_keywords = fields.Char(
        string='Brand Keywords',
        help='Brand keywords'
    )

    # Thông tin phân loại
    brand_class = fields.Char(
        string='Brand Class ID',
        readonly=True,
        help='Brand class ID'
    )

    brand_class_code = fields.Char(
        string='Brand Class Code',
        readonly=True,
        help='Brand class code'
    )

    brand_class_name = fields.Char(
        string='Brand Class Name',
        readonly=True,
        help='Brand class name'
    )

    # Thông tin URL
    brand_url = fields.Char(
        string='Brand URL',
        help='Brand URL'
    )

    # Thông tin thứ tự
    order_number = fields.Integer(
        string='Order Number',
        default=0,
        help='Order number'
    )

    stop_status = fields.Boolean(
        string='Stop Status',
        default=False,
        help='Stop status'
    )

    # Thông tin thời gian
    create_time = fields.Datetime(
        string='Create Time',
        readonly=True,
        help='Create time from YonSuite'
    )

    modify_time = fields.Datetime(
        string='Modify Time',
        readonly=True,
        help='Modify time from YonSuite'
    )

    creator = fields.Char(
        string='Creator',
        readonly=True,
        help='Creator name'
    )

    modifier = fields.Char(
        string='Modifier',
        readonly=True,
        help='Modifier name'
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
        help='Last time this brand was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync brand data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu brand
        api_service = self.env['yonsuite.api']
        result = api_service.get_brands_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                brands_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                brands_data = data
            else:
                brands_data = []

            # Tìm brand hiện tại trong dữ liệu trả về
            current_brand = None
            for brand_data in brands_data:
                if str(brand_data.get("id")) == str(self.yonsuite_id):
                    current_brand = brand_data
                    break

            if current_brand:
                # Cập nhật dữ liệu brand
                self._update_brand_from_api_data(current_brand)

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
                        'message': _('Brand "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Brand not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_brand_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu brand từ API response
        """
        # Sử dụng method từ yonsuite.api để chuẩn bị dữ liệu
        api_service = self.env['yonsuite.api']
        vals = api_service._prepare_brand_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset brand to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_brands_pagination(self):
        """
        Sync brands từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.brands_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu brands
        result = self.env['yonsuite.api'].get_brands_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                brands_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                brands_data = data
            else:
                brands_data = []

            if not brands_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.brands_current_page', '1')
                _logger.info("No more brands data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(brands_data) < page_size:
                should_reset = True
            else:
                should_reset = False

            created_count = 0
            updated_count = 0
            skipped_count = 0
            synced_count = 0

            for brand_data in brands_data:
                yonsuite_id = str(brand_data.get('id', ''))
                if not yonsuite_id:
                    skipped_count += 1
                    continue

                # Tìm brand hiện có
                existing_brand = self.search([
                    ('yonsuite_id', '=', yonsuite_id)
                ], limit=1)

                # Chuẩn bị dữ liệu
                vals = self._prepare_brand_data_from_api(brand_data)

                if existing_brand:
                    # Cập nhật brand hiện có
                    existing_brand.write(vals)
                    updated_count += 1
                    _logger.debug("Updated brand: %s (ID: %s)", vals.get('name', ''), yonsuite_id)
                else:
                    # Tạo brand mới
                    vals.update({
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                    })
                    self.create(vals)
                    created_count += 1
                    _logger.debug("Created brand: %s (ID: %s)", vals.get('name', ''), yonsuite_id)

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.brands_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.brands_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.brands_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.brands_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.brands_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.brands_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync brands from YonSuite: %s", error_msg)
                return 0

    def _prepare_brand_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu brand từ API response để lưu vào database
        """
        vals = {
            'yonsuite_id': str(api_data.get('id', '')),
            'code': api_data.get('code', ''),
            'order_number': api_data.get('orderNumber', 0),
            'stop_status': api_data.get('stopStatus', False),
            'brand_class': str(api_data.get('brandClass', '')),
            'brand_class_code': api_data.get('brandClassCode', ''),
            'brand_class_name': api_data.get('brandClassName', ''),
        }

        # Xử lý name object
        name_obj = api_data.get('name', {})
        if name_obj:
            vals['simplified_name'] = name_obj.get('simplifiedName', '')
            vals['english_name'] = name_obj.get('englishName', '')
            # Sử dụng simplified_name làm name chính nếu có
            vals['name'] = name_obj.get('simplifiedName', '') or name_obj.get('englishName', '')

        # Xử lý brandDesc object
        brand_desc_obj = api_data.get('brandDesc', {})
        if brand_desc_obj:
            vals['brand_desc'] = brand_desc_obj.get('simplifiedName', '') or str(brand_desc_obj)

        # Xử lý randKeywords object
        keywords_obj = api_data.get('randKeywords', {})
        if keywords_obj:
            vals['brand_keywords'] = keywords_obj.get('simplifiedName', '') or str(keywords_obj)

        # Xử lý brandUrl object
        url_obj = api_data.get('brandUrl', {})
        if url_obj:
            vals['brand_url'] = str(url_obj)

        return vals
