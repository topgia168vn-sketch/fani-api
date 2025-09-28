# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteStaff(models.Model):
    _name = 'yonsuite.staff'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Staff'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Staff ID from YonSuite API'
    )

    code = fields.Char(
        string='Staff Code',
        help='Staff code from YonSuite'
    )

    name = fields.Char(
        string='Staff Name',
        required=True,
        help='Staff name'
    )

    # Thông tin người dùng
    user_id = fields.Char(
        string='User ID',
        readonly=True,
        help='User ID from YonSuite'
    )

    dept_id = fields.Char(
        string='Department ID',
        readonly=True,
        help='Department ID from YonSuite'
    )

    email = fields.Char(
        string='Email',
        help='Staff email address'
    )

    mobile = fields.Char(
        string='Mobile',
        help='Staff mobile phone number'
    )

    # Thông tin tổ chức
    org_id = fields.Char(
        string='Organization ID',
        readonly=True,
        help='Organization ID'
    )

    # Thông tin trạng thái
    enable = fields.Boolean(
        string='Enable',
        default=True,
        help='Is staff enabled'
    )

    # Thông tin thời gian
    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

    enddate = fields.Datetime(
        string='End Date',
        readonly=True,
        help='Employment end date'
    )

    # Thông tin bổ sung
    ordernumber = fields.Char(
        string='Order Number',
        readonly=True,
        help='Order number'
    )

    dr = fields.Char(
        string='DR',
        readonly=True,
        help='DR field'
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
        help='Last time this staff was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync staff data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu staff
        api_service = self.env['yonsuite.api']
        result = api_service.get_staff_from_api()

        if result.get("code") == "200":
            staff_data = result.get("data", {}).get("recordList", [])

            # Tìm staff hiện tại trong dữ liệu trả về
            current_staff = None
            for staff_item in staff_data:
                if str(staff_item.get("id")) == str(self.yonsuite_id):
                    current_staff = staff_item
                    break

            if current_staff:
                # Cập nhật dữ liệu staff
                self._update_staff_from_api_data(current_staff)

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
                        'message': _('Staff "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Staff not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_staff_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu staff từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_staff_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset staff to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_staff_pagination(self):
        """
        Sync staff từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.staff_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu staff
        api_service = self.env['yonsuite.api']
        result = api_service.get_staff_from_api(current_page, page_size)

        if result.get("code") == "200":
            staff_data = result.get("data", {}).get("recordList", [])

            if not staff_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.staff_current_page', '1')
                _logger.info("No more staff data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(staff_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(staff_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(staff_item.get("id")) for staff_item in staff_data]

            # Search một lần duy nhất tất cả staff đã tồn tại
            existing_staff = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_staff_dict = {s.yonsuite_id: s for s in existing_staff}

            # Lưu staff vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for staff_item in staff_data:
                yonsuite_id = str(staff_item.get("id"))
                staff = existing_staff_dict.get(yonsuite_id)

                if not staff:
                    # Tạo staff mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': staff_item.get("name") or staff_item.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_staff_data_from_api(staff_item))

                    staff = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra pubts có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_pubts = api_service._convert_datetime_string(staff_item.get("pubts"))

                    if api_pubts and staff.pubts != api_pubts:
                        staff._update_staff_from_api_data(staff_item)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.staff_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.staff_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.staff_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.staff_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.staff_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.staff_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync staff from YonSuite: %s", error_msg)
                return 0

    def _prepare_staff_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu staff từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'name': api_data.get("name"),
            'user_id': api_data.get("user_id"),
            'dept_id': api_data.get("dept_id"),
            'email': api_data.get("email"),
            'mobile': api_data.get("mobile"),
            'org_id': api_data.get("org_id"),
            'enable': api_data.get("enable", True),
            'ordernumber': api_data.get("ordernumber"),
            'dr': api_data.get("dr"),
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        if api_data.get("enddate"):
            converted_datetime = api_service._convert_datetime_string(api_data["enddate"])
            if converted_datetime:
                vals['enddate'] = converted_datetime

        return vals
