# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteCarrier(models.Model):
    _name = 'yonsuite.carrier'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Carrier'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Carrier ID from YonSuite API'
    )

    code = fields.Char(
        string='Carrier Code',
        help='Carrier code from YonSuite'
    )

    name = fields.Char(
        string='Carrier Name',
        required=True,
        help='Carrier name'
    )

    # Thông tin địa chỉ
    address = fields.Text(
        string='Address',
        help='Carrier address'
    )

    # Thông tin liên hệ
    contacts = fields.Char(
        string='Contacts',
        help='Contact person'
    )

    contacts_phone = fields.Char(
        string='Contacts Phone',
        help='Contact phone number'
    )

    # Thông tin pháp lý
    legal_person = fields.Char(
        string='Legal Person',
        help='Legal person name'
    )

    legal_person_identity = fields.Char(
        string='Legal Person Identity',
        help='Legal person identity card'
    )

    license = fields.Char(
        string='License',
        help='Business license'
    )

    # Thông tin nhà cung cấp
    supplier = fields.Char(
        string='Supplier ID',
        readonly=True,
        help='Supplier ID'
    )

    supplier_name = fields.Char(
        string='Supplier Name',
        readonly=True,
        help='Supplier name'
    )

    # Trạng thái
    benable = fields.Char(
        string='Enable Status',
        help='Enable status'
    )

    # Thông tin người dùng
    creator = fields.Char(
        string='Creator',
        readonly=True,
        help='Creator ID'
    )

    creator_name = fields.Char(
        string='Creator Name',
        readonly=True,
        help='Creator name'
    )

    modifier = fields.Char(
        string='Modifier',
        readonly=True,
        help='Modifier ID'
    )

    modifier_name = fields.Char(
        string='Modifier Name',
        readonly=True,
        help='Modifier name'
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

    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

    # Thông tin chi tiết từ detail API
    carrier_relation_list = fields.Text(
        string='Carrier Relations',
        readonly=True,
        help='Carrier relation list from detail API'
    )

    driver_list = fields.Text(
        string='Driver List',
        readonly=True,
        help='Driver list from detail API'
    )

    vehicle_list = fields.Text(
        string='Vehicle List',
        readonly=True,
        help='Vehicle list from detail API'
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
        help='Last time this carrier was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync carrier data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu carrier
        api_service = self.env['yonsuite.api']
        result = api_service.get_carriers_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                carriers_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                carriers_data = data
            else:
                carriers_data = []

            # Tìm carrier hiện tại trong dữ liệu trả về
            current_carrier = None
            for carrier_data in carriers_data:
                if str(carrier_data.get("id")) == str(self.yonsuite_id):
                    current_carrier = carrier_data
                    break

            if current_carrier:
                # Cập nhật dữ liệu carrier
                self._update_carrier_from_api_data(current_carrier)

                # Gọi detail API để lấy thêm thông tin chi tiết
                try:
                    detail_result = api_service.get_carrier_detail_from_api(self.yonsuite_id)
                    if detail_result.get("code") == "200":
                        detail_data = detail_result.get("data", {})
                        if detail_data:
                            detail_vals = self._prepare_carrier_detail_data_from_api(detail_data)
                            self.write(detail_vals)
                            _logger.debug("Added detail data for carrier: %s (ID: %s)", self.name, self.yonsuite_id)
                except Exception as e:
                    _logger.warning("Failed to get detail for carrier %s: %s", self.yonsuite_id, str(e))

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
                        'message': _('Carrier "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Carrier not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_carrier_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu carrier từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_carrier_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset carrier to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_carriers_pagination(self):
        # TODO: API này không tồn tại, nhưng doc có
        """
        Sync carriers từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.carriers_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu carriers
        result = self.env['yonsuite.api'].get_carriers_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                carriers_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                carriers_data = data
            else:
                carriers_data = []

            if not carriers_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.carriers_current_page', '1')
                _logger.info("No more carriers data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(carriers_data) < page_size:
                should_reset = True
            else:
                should_reset = False

            created_count = 0
            updated_count = 0
            skipped_count = 0
            synced_count = 0

            for carrier_data in carriers_data:
                yonsuite_id = str(carrier_data.get('id', ''))
                if not yonsuite_id:
                    skipped_count += 1
                    continue

                # Tìm carrier hiện có
                existing_carrier = self.search([
                    ('yonsuite_id', '=', yonsuite_id)
                ], limit=1)

                # Chuẩn bị dữ liệu
                vals = self._prepare_carrier_data_from_api(carrier_data)

                # Gọi detail API để lấy thêm thông tin chi tiết
                detail_result = self.env['yonsuite.api'].get_carrier_detail_from_api(yonsuite_id)
                if detail_result.get("code") == "200":
                    detail_data = detail_result.get("data", {})
                    if detail_data:
                        detail_vals = self._prepare_carrier_detail_data_from_api(detail_data)
                        vals.update(detail_vals)
                        _logger.debug("Added detail data for carrier: %s (ID: %s)", vals.get('name', ''), yonsuite_id)
                if existing_carrier:
                    # Cập nhật carrier hiện có
                    existing_carrier.write(vals)
                    updated_count += 1
                    _logger.debug("Updated carrier: %s (ID: %s)", vals.get('name', ''), yonsuite_id)
                else:
                    # Tạo carrier mới
                    vals.update({
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                    })
                    self.create(vals)
                    created_count += 1
                    _logger.debug("Created carrier: %s (ID: %s)", vals.get('name', ''), yonsuite_id)

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.carriers_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.carriers_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.carriers_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.carriers_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.carriers_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.carriers_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync carriers from YonSuite: %s", error_msg)
                return 0

    def _prepare_carrier_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu carrier từ API response để lưu vào database
        """
        vals = {
            'yonsuite_id': str(api_data.get('id', '')),
            'code': api_data.get('code', ''),
            'name': api_data.get('name', ''),
            'address': api_data.get('address', ''),
            'contacts': api_data.get('contacts', ''),
            'contacts_phone': api_data.get('contactsphone', ''),
            'legal_person': api_data.get('legalperson', ''),
            'legal_person_identity': api_data.get('legalpersonIdentity', ''),
            'license': api_data.get('license', ''),
            'supplier': str(api_data.get('supplier', '')),
            'supplier_name': api_data.get('supplier_name', ''),
            'benable': api_data.get('benable', ''),
            'creator': api_data.get('creator', ''),
            'creator_name': api_data.get('creator_name', ''),
            'modifier': api_data.get('modifier', ''),
            'modifier_name': api_data.get('modifier_name', ''),
        }

        return vals

    def _prepare_carrier_detail_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu carrier detail từ API response để lưu vào database
        """
        import json

        vals = {}

        # Xử lý carrierRelationList
        carrier_relation_list = api_data.get('carrierRelationList', [])
        if carrier_relation_list:
            vals['carrier_relation_list'] = json.dumps(carrier_relation_list, ensure_ascii=False, indent=2)

        # Xử lý driverList
        driver_list = api_data.get('driverList', [])
        if driver_list:
            vals['driver_list'] = json.dumps(driver_list, ensure_ascii=False, indent=2)

        # Xử lý vehicleList
        vehicle_list = api_data.get('vehicleList', [])
        if vehicle_list:
            vals['vehicle_list'] = json.dumps(vehicle_list, ensure_ascii=False, indent=2)

        return vals
