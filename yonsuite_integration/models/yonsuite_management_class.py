# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class YonsuiteManagementClass(models.Model):
    _name = 'yonsuite.management.class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Management Class'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Management Class ID from YonSuite API'
    )

    code = fields.Char(
        string='Management Class Code',
        help='Management class code from YonSuite'
    )

    name = fields.Char(
        string='Management Class Name',
        required=True,
        help='Management class name'
    )

    simplified_name = fields.Char(
        string='Simplified Name',
        help='Simplified name from YonSuite'
    )

    # Thông tin phân cấp
    level = fields.Integer(
        string='Level',
        default=0,
        help='Management class level'
    )

    path = fields.Char(
        string='Path',
        readonly=True,
        help='Management class path'
    )

    # Thông tin tổ chức
    org_id = fields.Char(
        string='Organization ID',
        readonly=True,
        help='Organization ID'
    )

    org_code = fields.Char(
        string='Organization Code',
        readonly=True,
        help='Organization code'
    )

    org_name = fields.Char(
        string='Organization Name',
        readonly=True,
        help='Organization name'
    )

    # Thông tin sắp xếp
    order = fields.Integer(
        string='Order',
        default=0,
        help='Order number'
    )

    stop_status = fields.Boolean(
        string='Stop Status',
        default=False,
        help='Stop status'
    )

    # Thông tin ghi chú
    remark = fields.Text(
        string='Remark',
        help='Remark information'
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


    # Trạng thái đồng bộ
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this management class was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync management class data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu management class
        api_service = self.env['yonsuite.api']
        result = api_service.get_management_classes_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            management_classes_data = data.get("recordList", [])

            # Tìm management class hiện tại trong dữ liệu trả về
            current_management_class = None
            for management_class_data in management_classes_data:
                if str(management_class_data.get("id")) == str(self.yonsuite_id):
                    current_management_class = management_class_data
                    break

            if current_management_class:
                # Cập nhật dữ liệu management class
                self._update_management_class_from_api_data(current_management_class)

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
                        'message': _('Management Class "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Management Class not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_management_class_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu management class từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_management_class_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset management class to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_management_classes_pagination(self):
        """
        Sync management classes từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.management_classes_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu management classes
        api_service = self.env['yonsuite.api']
        result = api_service.get_management_classes_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            management_classes_data = data.get("recordList", [])
            have_next_page = data.get("haveNextPage", False)

            if not management_classes_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.management_classes_current_page', '1')
                _logger.info("No more management classes data, reset to page 1")
                return 0

            # Kiểm tra nếu không có trang tiếp theo thì đã hết dữ liệu
            if not have_next_page:
                _logger.info("Received %d records, no next page available, this is the last page", len(management_classes_data))
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(management_class_data.get("id")) for management_class_data in management_classes_data]

            # Search một lần duy nhất tất cả management classes đã tồn tại
            existing_management_classes = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_management_classes_dict = {p.yonsuite_id: p for p in existing_management_classes}

            # Lưu management classes vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for management_class_data in management_classes_data:
                yonsuite_id = str(management_class_data.get("id"))
                management_class = existing_management_classes_dict.get(yonsuite_id)

                if not management_class:
                    # Tạo management class mới với đầy đủ dữ liệu
                    name_data = management_class_data.get("name", {})
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': name_data.get("simplifiedName") or management_class_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_management_class_data_from_api(management_class_data))

                    management_class = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modify_time có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modify_time = api_service._convert_datetime_string(management_class_data.get("modifyTime"))

                    if api_modify_time and management_class.modify_time != api_modify_time:
                        management_class._update_management_class_from_api_data(management_class_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.management_classes_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.management_classes_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.management_classes_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.management_classes_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.management_classes_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.management_classes_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync management classes from YonSuite: %s", error_msg)
                return 0

    def _prepare_management_class_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu management class từ API response
        """
        name_data = api_data.get("name", {})
        remark_data = api_data.get("remark", {})

        vals = {
            'code': api_data.get("code"),
            'name': name_data.get("simplifiedName") or api_data.get("code"),
            'simplified_name': name_data.get("simplifiedName"),
            'level': api_data.get("level", 0),
            'path': api_data.get("path"),
            'org_id': api_data.get("orgId"),
            'org_code': api_data.get("orgCode"),
            'org_name': api_data.get("orgName"),
            'order': api_data.get("order", 0),
            'stop_status': api_data.get("stopStatus", False),
            'remark': str(remark_data) if remark_data else '',
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("createTime"):
            converted_datetime = api_service._convert_datetime_string(api_data["createTime"])
            if converted_datetime:
                vals['create_time'] = converted_datetime

        if api_data.get("modifyTime"):
            converted_datetime = api_service._convert_datetime_string(api_data["modifyTime"])
            if converted_datetime:
                vals['modify_time'] = converted_datetime

        return vals
