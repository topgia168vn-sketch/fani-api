# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class YonsuiteSaleClass(models.Model):
    _name = 'yonsuite.sale.class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Sale Class'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Sale Class ID from YonSuite API'
    )

    code = fields.Char(
        string='Sale Class Code',
        help='Sale class code from YonSuite'
    )

    name = fields.Char(
        string='Sale Class Name',
        required=True,
        help='Sale class name'
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

    path = fields.Char(
        string='Path',
        readonly=True,
        help='Sale class path'
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

    # Trạng thái đồng bộ
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this sale class was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync sale class data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu sale class
        api_service = self.env['yonsuite.api']
        result = api_service.get_sale_classes_from_api()

        if result.get("code") == "200":
            data = result.get("data", [])
            sale_classes_data = data

            # Tìm sale class hiện tại trong dữ liệu trả về
            current_sale_class = None
            for sale_class_data in sale_classes_data:
                if str(sale_class_data.get("id")) == str(self.yonsuite_id):
                    current_sale_class = sale_class_data
                    break

            if current_sale_class:
                # Cập nhật dữ liệu sale class
                self._update_sale_class_from_api_data(current_sale_class)

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
                        'message': _('Sale Class "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Sale Class not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_sale_class_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu sale class từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_sale_class_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset sale class to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_sale_classes_pagination(self):
        """
        Sync sale classes từ YonSuite API và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Gọi API để lấy dữ liệu sale classes
        api_service = self.env['yonsuite.api']
        result = api_service.get_sale_classes_from_api()

        if result.get("code") == "200":
            data = result.get("data", [])
            sale_classes_data = data

            if not sale_classes_data:
                _logger.info("No sale classes data found")
                return 0

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(sale_class_data.get("id")) for sale_class_data in sale_classes_data]

            # Search một lần duy nhất tất cả sale classes đã tồn tại
            existing_sale_classes = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_sale_classes_dict = {p.yonsuite_id: p for p in existing_sale_classes}

            # Lưu sale classes vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for sale_class_data in sale_classes_data:
                yonsuite_id = str(sale_class_data.get("id"))
                sale_class = existing_sale_classes_dict.get(yonsuite_id)

                if not sale_class:
                    # Tạo sale class mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': sale_class_data.get("name") or sale_class_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_sale_class_data_from_api(sale_class_data))

                    sale_class = self.create(vals)
                    created_count += 1
                else:
                    # Cập nhật dữ liệu hiện có
                    sale_class._update_sale_class_from_api_data(sale_class_data)
                    updated_count += 1

                synced_count += 1

            _logger.info("Sale Classes sync completed: Created %d, Updated %d, Total %d",
                        created_count, updated_count, synced_count)

            # Cập nhật thống kê
            config_parameter.set_param('yonsuite_integration.sale_classes_total_synced', str(synced_count))
            config_parameter.set_param('yonsuite_integration.sale_classes_last_sync', fields.Datetime.now())

            return synced_count
        else:
            # Kiểm tra message để xác định có phải là "rỗng" không
            message = result.get("message", "")
            message_lower = message.lower()
            # Check for various empty result indicators
            empty_indicators = ["rỗng", "empty", "không có", "khong co"]
            is_empty = any(indicator in message or indicator in message_lower for indicator in empty_indicators)

            if is_empty:
                _logger.info("Query result is empty (message: '%s')", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync sale classes from YonSuite: %s", error_msg)
                return 0

    def _prepare_sale_class_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu sale class từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'name': api_data.get("name") or api_data.get("code"),
            'org_id': api_data.get("orgId"),
            'org_code': api_data.get("orgCode"),
            'org_name': api_data.get("orgName"),
            'order': api_data.get("order", 0),
            'path': api_data.get("path"),
            'stop_status': api_data.get("stopStatus", False),
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
