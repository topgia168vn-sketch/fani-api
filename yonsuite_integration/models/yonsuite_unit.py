# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteUnit(models.Model):
    _name = 'yonsuite.unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Unit'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Unit ID from YonSuite API'
    )

    code = fields.Char(
        string='Unit Code',
        help='Unit code from YonSuite'
    )

    name = fields.Char(
        string='Unit Name',
        required=True,
        help='Unit name'
    )

    simplified_name = fields.Char(
        string='Simplified Name',
        help='Simplified name from YonSuite'
    )

    english_name = fields.Char(
        string='English Name',
        help='English name from YonSuite'
    )

    # Thông tin độ chính xác
    precision = fields.Integer(
        string='Precision',
        default=0,
        help='Unit precision'
    )

    truncation_type = fields.Integer(
        string='Truncation Type',
        default=0,
        help='Truncation type'
    )

    base_unit = fields.Boolean(
        string='Base Unit',
        default=False,
        help='Is base unit'
    )

    # Thông tin nhóm đơn vị
    unit_group = fields.Char(
        string='Unit Group ID',
        readonly=True,
        help='Unit group ID'
    )

    unit_group_code = fields.Char(
        string='Unit Group Code',
        readonly=True,
        help='Unit group code'
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
        help='Last time this unit was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync unit data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu unit
        api_service = self.env['yonsuite.api']
        result = api_service.get_units_from_api()

        if result.get("code") == "200":
            data = result.get("data", [])
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                units_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                units_data = data
            else:
                units_data = []

            # Tìm unit hiện tại trong dữ liệu trả về
            current_unit = None
            for unit_data in units_data:
                if str(unit_data.get("id")) == str(self.yonsuite_id):
                    current_unit = unit_data
                    break

            if current_unit:
                # Cập nhật dữ liệu unit
                self._update_unit_from_api_data(current_unit)

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
                        'message': _('Unit "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Unit not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_unit_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu unit từ API response
        """
        # Sử dụng method từ yonsuite.api để chuẩn bị dữ liệu
        api_service = self.env['yonsuite.api']
        vals = api_service._prepare_unit_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset unit to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_units_pagination(self):
        """
        Sync units từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.units_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu units
        result = self.env['yonsuite.api'].get_units_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", [])
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                units_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                units_data = data
            else:
                units_data = []

            if not units_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.units_current_page', '1')
                _logger.info("No more units data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(units_data) < page_size:
                should_reset = True
            else:
                should_reset = False

            created_count = 0
            updated_count = 0
            skipped_count = 0
            synced_count = 0

            for unit_data in units_data:
                yonsuite_id = str(unit_data.get('id', ''))
                if not yonsuite_id:
                    skipped_count += 1
                    continue

                # Tìm unit hiện có
                existing_unit = self.search([
                    ('yonsuite_id', '=', yonsuite_id)
                ], limit=1)

                # Chuẩn bị dữ liệu
                vals = self._prepare_unit_data_from_api(unit_data)

                if existing_unit:
                    # Cập nhật unit hiện có
                    existing_unit.write(vals)
                    updated_count += 1
                    _logger.debug("Updated unit: %s (ID: %s)", vals.get('name', ''), yonsuite_id)
                else:
                    # Tạo unit mới
                    vals.update({
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                    })
                    self.create(vals)
                    created_count += 1
                    _logger.debug("Created unit: %s (ID: %s)", vals.get('name', ''), yonsuite_id)

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.units_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.units_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.units_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.units_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.units_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.units_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync units from YonSuite: %s", error_msg)
                return 0

    def _prepare_unit_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu unit từ API response để lưu vào database
        """
        vals = {
            'yonsuite_id': str(api_data.get('id', '')),
            'code': api_data.get('code', ''),
            'precision': api_data.get('precision', 0),
            'truncation_type': api_data.get('truncationType', 0),
            'base_unit': api_data.get('baseUnit', False),
            'unit_group': str(api_data.get('unitGroup', '')),
            'unit_group_code': api_data.get('unitGroupCode', ''),
            'stop_status': api_data.get('stopStatus', False),
        }

        # Xử lý name object
        name_obj = api_data.get('name', {})
        if isinstance(name_obj, dict):
            vals['simplified_name'] = name_obj.get('simplifiedName', '')
            vals['english_name'] = name_obj.get('englishName', '')
            # Sử dụng simplified_name làm name chính nếu có
            vals['name'] = name_obj.get('simplifiedName', '') or name_obj.get('englishName', '')
        else:
            vals['name'] = name_obj or ''
        return vals
