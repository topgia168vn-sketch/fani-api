# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteWarehouse(models.Model):
    _name = 'yonsuite.warehouse'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Warehouse'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Warehouse ID from YonSuite API'
    )

    code = fields.Char(
        string='Warehouse Code',
        help='Warehouse code from YonSuite'
    )

    name = fields.Char(
        string='Warehouse Name',
        required=True,
        help='Warehouse name'
    )

    # Thông tin tổ chức
    org = fields.Char(
        string='Organization ID',
        readonly=True,
        help='Organization ID'
    )

    org_name = fields.Char(
        string='Organization Name',
        readonly=True,
        help='Organization name'
    )

    org_code = fields.Char(
        string='Organization Code',
        readonly=True,
        help='Organization code'
    )

    ownerorg = fields.Char(
        string='Owner Organization ID',
        readonly=True,
        help='Owner organization ID'
    )

    ownerorg_name = fields.Char(
        string='Owner Organization Name',
        readonly=True,
        help='Owner organization name'
    )

    ownerorg_code = fields.Char(
        string='Owner Organization Code',
        readonly=True,
        help='Owner organization code'
    )

    # Thông tin địa chỉ
    region_code = fields.Char(
        string='Region Code',
        help='Region code'
    )

    bd_region_code = fields.Char(
        string='BD Region Code',
        help='BD region code'
    )

    address = fields.Text(
        string='Address',
        help='Warehouse address'
    )

    country = fields.Char(
        string='Country',
        help='Country'
    )

    country_name = fields.Char(
        string='Country Name',
        help='Country name'
    )

    longitude = fields.Float(
        string='Longitude',
        help='Longitude coordinate'
    )

    latitude = fields.Float(
        string='Latitude',
        help='Latitude coordinate'
    )

    # Thông tin liên hệ
    linkman = fields.Char(
        string='Contact Person',
        help='Contact person'
    )

    phone = fields.Char(
        string='Phone',
        help='Phone number'
    )

    # Thông tin phòng ban
    department = fields.Char(
        string='Department ID',
        readonly=True,
        help='Department ID'
    )

    department_name = fields.Char(
        string='Department Name',
        readonly=True,
        help='Department name'
    )

    department_code = fields.Char(
        string='Department Code',
        readonly=True,
        help='Department code'
    )

    # Thông tin nhà cung cấp
    vendor = fields.Char(
        string='Vendor ID',
        readonly=True,
        help='Vendor ID'
    )

    vendor_name = fields.Char(
        string='Vendor Name',
        readonly=True,
        help='Vendor name'
    )

    # Thông tin khách hàng
    consignment_customer = fields.Char(
        string='Consignment Customer ID',
        readonly=True,
        help='Consignment customer ID'
    )

    consignment_customer_name = fields.Char(
        string='Consignment Customer Name',
        readonly=True,
        help='Consignment customer name'
    )

    # Thông tin ERP
    erp_code = fields.Char(
        string='ERP Code',
        help='ERP code'
    )

    # Các thuộc tính boolean
    i_serial_manage = fields.Boolean(
        string='Serial Management',
        default=False,
        help='Serial management enabled'
    )

    b_mrp = fields.Boolean(
        string='MRP',
        default=False,
        help='MRP enabled'
    )

    is_goods_position = fields.Boolean(
        string='Goods Position',
        default=False,
        help='Goods position enabled'
    )

    is_goods_position_stock = fields.Boolean(
        string='Goods Position Stock',
        default=False,
        help='Goods position stock enabled'
    )

    e_store = fields.Boolean(
        string='E-Store',
        default=False,
        help='E-Store enabled'
    )

    w_store = fields.Boolean(
        string='W-Store',
        default=False,
        help='W-Store enabled'
    )

    b_wms = fields.Boolean(
        string='WMS',
        default=False,
        help='WMS enabled'
    )

    is_inverted_scour = fields.Boolean(
        string='Inverted Scour',
        default=False,
        help='Inverted scour enabled'
    )

    join_stock_query = fields.Boolean(
        string='Join Stock Query',
        default=False,
        help='Join stock query enabled'
    )

    is_car_sales = fields.Boolean(
        string='Car Sales',
        default=False,
        help='Car sales enabled'
    )

    count_cost = fields.Boolean(
        string='Count Cost',
        default=False,
        help='Count cost enabled'
    )

    is_subcontract_w = fields.Boolean(
        string='Subcontract Warehouse',
        default=False,
        help='Subcontract warehouse enabled'
    )

    is_consignment = fields.Boolean(
        string='Consignment',
        default=False,
        help='Consignment enabled'
    )

    is_pda_storage = fields.Boolean(
        string='PDA Storage',
        default=False,
        help='PDA storage enabled'
    )

    # Thông tin trạng thái
    i_used = fields.Char(
        string='Used Status',
        help='Used status'
    )

    is_waste_warehouse = fields.Char(
        string='Waste Warehouse',
        help='Waste warehouse status'
    )

    # Thông tin người dùng
    operator = fields.Char(
        string='Operator',
        readonly=True,
        help='Operator'
    )

    operator_name = fields.Char(
        string='Operator Name',
        readonly=True,
        help='Operator name'
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

    # Thông tin thời gian bổ sung từ detail API
    create_date_detail = fields.Char(
        string='Create Date (Detail)',
        readonly=True,
        help='Create date from detail API'
    )

    modify_date = fields.Char(
        string='Modify Date',
        readonly=True,
        help='Modify date from detail API'
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
        help='Last time this warehouse was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync warehouse data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu warehouse
        api_service = self.env['yonsuite.api']
        result = api_service.get_warehouses_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                warehouses_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                warehouses_data = data
            else:
                warehouses_data = []

            # Tìm warehouse hiện tại trong dữ liệu trả về
            current_warehouse = None
            for warehouse_data in warehouses_data:
                if str(warehouse_data.get("id")) == str(self.yonsuite_id):
                    current_warehouse = warehouse_data
                    break

            if current_warehouse:
                # Cập nhật dữ liệu warehouse
                self._update_warehouse_from_api_data(current_warehouse)

                # Gọi detail API để lấy thêm thông tin chi tiết
                detail_result = api_service.get_warehouse_detail_from_api(self.yonsuite_id)
                if detail_result.get("code") == "200":
                    detail_data = detail_result.get("data", {}).get("data", {})
                    if detail_data:
                        detail_vals = api_service._prepare_warehouse_detail_data_from_api(detail_data)
                        self.write(detail_vals)
                        _logger.debug("Added detail data for warehouse: %s (ID: %s)", self.name, self.yonsuite_id)

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
                        'message': _('Warehouse "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Warehouse not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_warehouse_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu warehouse từ API response
        """
        # Sử dụng method từ yonsuite.api để chuẩn bị dữ liệu
        api_service = self.env['yonsuite.api']
        vals = api_service._prepare_warehouse_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset warehouse to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_warehouses_pagination(self):
        """
        Sync warehouses từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.warehouses_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu warehouses
        result = self.env['yonsuite.api'].get_warehouses_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            # Kiểm tra nếu data là dict và có recordList
            if isinstance(data, dict) and "recordList" in data:
                warehouses_data = data.get("recordList", [])
            # Nếu data là list trực tiếp
            elif isinstance(data, list):
                warehouses_data = data
            else:
                warehouses_data = []

            if not warehouses_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.warehouses_current_page', '1')
                _logger.info("No more warehouses data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(warehouses_data) < page_size:
                should_reset = True
            else:
                should_reset = False

            created_count = 0
            updated_count = 0
            skipped_count = 0
            synced_count = 0

            for warehouse_data in warehouses_data:
                yonsuite_id = str(warehouse_data.get('id', ''))
                if not yonsuite_id:
                    skipped_count += 1
                    continue

                # Tìm warehouse hiện có
                existing_warehouse = self.search([
                    ('yonsuite_id', '=', yonsuite_id)
                ], limit=1)

                # Chuẩn bị dữ liệu
                vals = self._prepare_warehouse_data_from_api(warehouse_data)

                # Gọi detail API để lấy thêm thông tin chi tiết
                detail_result = self.env['yonsuite.api'].get_warehouse_detail_from_api(yonsuite_id)
                if detail_result.get("code") == "200":
                    detail_data = detail_result.get("data", {}).get("data", {})
                    if detail_data:
                        detail_vals = self._prepare_warehouse_detail_data_from_api(detail_data)
                        vals.update(detail_vals)
                        _logger.debug("Added detail data for warehouse: %s (ID: %s)", vals.get('name', ''), yonsuite_id)

                if existing_warehouse:
                    # Cập nhật warehouse hiện có
                    existing_warehouse.write(vals)
                    updated_count += 1
                    _logger.debug("Updated warehouse: %s (ID: %s)", vals.get('name', ''), yonsuite_id)
                else:
                    # Tạo warehouse mới
                    vals.update({
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                    })
                    self.create(vals)
                    created_count += 1
                    _logger.debug("Created warehouse: %s (ID: %s)", vals.get('name', ''), yonsuite_id)

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.warehouses_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.warehouses_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.warehouses_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.warehouses_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.warehouses_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.warehouses_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync warehouses from YonSuite: %s", error_msg)
                return 0

    def _prepare_warehouse_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu warehouse từ API response để lưu vào database
        """
        vals = {
            'yonsuite_id': str(api_data.get('id', '')),
            'code': api_data.get('code', ''),
            'name': api_data.get('name', ''),
            'org': str(api_data.get('org', '')),
            'org_name': api_data.get('org_name', ''),
            'org_code': api_data.get('org_code', ''),
            'ownerorg': str(api_data.get('ownerorg', '')),
            'ownerorg_name': api_data.get('ownerorg_name', ''),
            'ownerorg_code': api_data.get('ownerorg_code', ''),
            'region_code': api_data.get('regionCode', ''),
            'bd_region_code': api_data.get('bdRegionCode', ''),
            'address': api_data.get('address', ''),
            'country': api_data.get('country', ''),
            'country_name': api_data.get('country_name', ''),
            'longitude': api_data.get('longitude', 0.0),
            'latitude': api_data.get('latitude', 0.0),
            'linkman': api_data.get('linkman', ''),
            'phone': api_data.get('phone', ''),
            'department': str(api_data.get('department', '')),
            'department_name': api_data.get('department_name', ''),
            'department_code': api_data.get('department_code', ''),
            'vendor': str(api_data.get('vendor', '')),
            'vendor_name': api_data.get('vendor_name', ''),
            'consignment_customer': str(api_data.get('consignmentCustomer', '')),
            'consignment_customer_name': api_data.get('consignmentCustomer_name', ''),
            'erp_code': api_data.get('erpCode', ''),
            'i_serial_manage': api_data.get('iSerialManage', False),
            'b_mrp': api_data.get('bMRP', False),
            'is_goods_position': api_data.get('isGoodsPosition', False),
            'is_goods_position_stock': api_data.get('isGoodsPositionStock', False),
            'e_store': api_data.get('eStore', False),
            'w_store': api_data.get('wStore', False),
            'b_wms': api_data.get('bWMS', False),
            'is_inverted_scour': api_data.get('isInvertedScour', False),
            'join_stock_query': api_data.get('joinStockQuery', False),
            'is_car_sales': api_data.get('isCarSales', False),
            'count_cost': api_data.get('countCost', False),
            'is_subcontract_w': api_data.get('isSubcontractW', False),
            'is_consignment': api_data.get('isConsignment', False),
            'is_pda_storage': api_data.get('isPDAStorage', False),
            'i_used': api_data.get('iUsed', ''),
            'is_waste_warehouse': api_data.get('isWasteWarehouse', ''),
            'operator': api_data.get('operator', ''),
            'operator_name': api_data.get('operator_name', ''),
            'creator': api_data.get('creator', ''),
            'modifier': api_data.get('modifier', ''),
        }

        return vals

    def _prepare_warehouse_detail_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu warehouse detail từ API response để lưu vào database
        """
        vals = {
            'create_date_detail': api_data.get('createDate', ''),
            'modify_date': api_data.get('modifyDate', ''),
        }

        return vals
