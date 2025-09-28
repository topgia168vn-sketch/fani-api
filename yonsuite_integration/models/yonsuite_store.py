# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteStore(models.Model):
    _name = 'yonsuite.store'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Store'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Store ID from YonSuite API'
    )

    code = fields.Char(
        string='Store Code',
        help='Store code from YonSuite'
    )

    name = fields.Char(
        string='Store Name',
        required=True,
        help='Store name'
    )

    mnemonic = fields.Char(
        string='Mnemonic',
        help='Store mnemonic from YonSuite'
    )

    codebianma = fields.Char(
        string='Code Bianma',
        help='Code bianma from YonSuite'
    )

    # Thông tin tổ chức
    org_id = fields.Many2one(
        'yonsuite.orgunit',
        string='Organization',
        help='Organization unit from YonSuite'
    )

    orgid = fields.Char(
        string='Organization ID',
        help='Organization ID (auto-calculated from org_id or manually entered)'
    )

    org_name = fields.Char(
        string='Organization Name',
        readonly=True,
        help='Organization name'
    )

    # Thông tin khách hàng
    cust_id = fields.Many2one(
        'yonsuite.partner',
        string='Customer',
        help='Customer partner from YonSuite'
    )

    cust = fields.Char(
        string='Customer ID',
        help='Customer ID (auto-calculated from cust_id or manually entered)'
    )

    cust_name = fields.Char(
        string='Customer Name',
        readonly=True,
        help='Customer name'
    )

    # Thông tin kho
    warehouse_id = fields.Many2one(
        'yonsuite.warehouse',
        string='Warehouse',
        help='Warehouse from YonSuite'
    )

    warehouse = fields.Char(
        string='Warehouse ID',
        help='Warehouse ID (auto-calculated from warehouse_id or manually entered)'
    )

    warehouse_name = fields.Char(
        string='Warehouse Name',
        readonly=True,
        help='Warehouse name'
    )

    # Thông tin khu vực
    area_class_id = fields.Many2one(
        'yonsuite.salearea',
        string='Area Class',
        help='Sale area from YonSuite'
    )

    area_class = fields.Char(
        string='Area Class ID',
        help='Area class ID (auto-calculated from area_class_id or manually entered)'
    )

    area_class_name = fields.Char(
        string='Area Class Name',
        readonly=True,
        help='Area class name'
    )

    # Thông tin loại cửa hàng
    store_type = fields.Integer(
        string='Store Type',
        default=0,
        help='Store type'
    )

    # Thông tin doanh nghiệp
    membercorp = fields.Integer(
        string='Member Corp',
        default=0,
        help='Member corporation'
    )

    c_app_id = fields.Char(
        string='C App ID',
        readonly=True,
        help='C App ID'
    )

    stop = fields.Boolean(
        string='Stop Status',
        default=False,
        help='Stop status'
    )

    # Thông tin bổ sung từ API detail
    platform_type = fields.Char(
        string='Platform Type',
        readonly=True,
        help='Platform type from YonSuite'
    )

    terminal_type = fields.Char(
        string='Terminal Type',
        readonly=True,
        help='Terminal type from YonSuite'
    )

    terminal_category = fields.Char(
        string='Terminal Category',
        readonly=True,
        help='Terminal category from YonSuite'
    )

    channel_customer = fields.Integer(
        string='Channel Customer',
        default=0,
        help='Channel customer'
    )

    merchant_store = fields.Integer(
        string='Merchant Store',
        default=0,
        help='Merchant store'
    )

    delivery_method = fields.Char(
        string='Delivery Method',
        readonly=True,
        help='Delivery method from YonSuite'
    )

    km_radius = fields.Integer(
        string='KM Radius',
        default=0,
        help='KM radius'
    )

    circle_radius = fields.Integer(
        string='Circle Radius',
        default=0,
        help='Circle radius'
    )

    start_time = fields.Char(
        string='Start Time',
        readonly=True,
        help='Start time from YonSuite'
    )

    end_time = fields.Char(
        string='End Time',
        readonly=True,
        help='End time from YonSuite'
    )

    i_online_delivery = fields.Integer(
        string='Online Delivery',
        default=0,
        help='Online delivery flag'
    )

    central_warehouse_distribution = fields.Integer(
        string='Central Warehouse Distribution',
        default=0,
        help='Central warehouse distribution'
    )

    share_res = fields.Integer(
        string='Share Resource',
        default=0,
        help='Share resource'
    )

    cust_shipping_address = fields.Char(
        string='Customer Shipping Address ID',
        readonly=True,
        help='Customer shipping address ID'
    )

    cust_shipping_address_name = fields.Char(
        string='Customer Shipping Address',
        readonly=True,
        help='Customer shipping address name'
    )

    # Thông tin thời gian
    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

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
        help='Last time this store was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    @api.onchange('org_id')
    def _onchange_org_id(self):
        """
        Tự động tính toán orgid và org_name khi chọn org_id
        """
        if self.org_id:
            self.orgid = self.org_id.yonsuite_id
            self.org_name = self.org_id.name
        else:
            self.orgid = False
            self.org_name = False

    @api.depends('org_id')
    def _compute_orgid_readonly(self):
        """
        Tính toán readonly state cho orgid field
        """
        for record in self:
            record.orgid_readonly = bool(record.org_id)

    orgid_readonly = fields.Boolean(
        string='Orgid Readonly',
        compute='_compute_orgid_readonly',
        help='Technical field to control orgid readonly state'
    )

    @api.onchange('cust_id')
    def _onchange_cust_id(self):
        """
        Tự động tính toán cust và cust_name khi chọn cust_id
        """
        if self.cust_id:
            self.cust = self.cust_id.yonsuite_id
            self.cust_name = self.cust_id.name
        else:
            self.cust = False
            self.cust_name = False

    @api.depends('cust_id')
    def _compute_cust_readonly(self):
        """
        Tính toán readonly state cho cust field
        """
        for record in self:
            record.cust_readonly = bool(record.cust_id)

    cust_readonly = fields.Boolean(
        string='Cust Readonly',
        compute='_compute_cust_readonly',
        help='Technical field to control cust readonly state'
    )

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Tự động tính toán warehouse và warehouse_name khi chọn warehouse_id
        """
        if self.warehouse_id:
            self.warehouse = self.warehouse_id.yonsuite_id
            self.warehouse_name = self.warehouse_id.name
        else:
            self.warehouse = False
            self.warehouse_name = False

    @api.depends('warehouse_id')
    def _compute_warehouse_readonly(self):
        """
        Tính toán readonly state cho warehouse field
        """
        for record in self:
            record.warehouse_readonly = bool(record.warehouse_id)

    warehouse_readonly = fields.Boolean(
        string='Warehouse Readonly',
        compute='_compute_warehouse_readonly',
        help='Technical field to control warehouse readonly state'
    )

    @api.onchange('area_class_id')
    def _onchange_area_class_id(self):
        """
        Tự động tính toán area_class và area_class_name khi chọn area_class_id
        """
        if self.area_class_id:
            self.area_class = self.area_class_id.yonsuite_id
            self.area_class_name = self.area_class_id.name
        else:
            self.area_class = False
            self.area_class_name = False

    @api.depends('area_class_id')
    def _compute_area_class_readonly(self):
        """
        Tính toán readonly state cho area_class field
        """
        for record in self:
            record.area_class_readonly = bool(record.area_class_id)

    area_class_readonly = fields.Boolean(
        string='Area Class Readonly',
        compute='_compute_area_class_readonly',
        help='Technical field to control area_class readonly state'
    )

    def action_export_to_yonsuite(self):
        """
        Push store data to YonSuite API
        """
        self.ensure_one()

        # Chuẩn bị dữ liệu để push lên YonSuite
        vals = self._prepare_store_data_push_to_yonsuite()

        # Gọi API để push dữ liệu store
        api_service = self.env['yonsuite.api']
        result = api_service.push_store_to_api(vals)

        if result.get("code") == 200:
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
                    'message': _('Store "%s" has been pushed to YonSuite successfully!') % self.name,
                    'type': 'success',
                }
            }
        else:
            error_msg = result.get("message", "Unknown error")
            self.write({
                'state': 'error',
                'sync_error_message': error_msg
            })
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_store_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu store từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_store_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset store to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_stores_pagination(self):
        """
        Sync stores từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.stores_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu stores
        api_service = self.env['yonsuite.api']
        result = api_service.get_stores_from_api(current_page, page_size)

        if result.get("code") == 200:
            stores_data = result.get("data", {}).get("recordList", [])

            if not stores_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.stores_current_page', '1')
                _logger.info("No more stores data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(stores_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(stores_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False
            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(store_data.get("id")) for store_data in stores_data]

            # Search một lần duy nhất tất cả stores đã tồn tại
            existing_stores = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_stores_dict = {p.yonsuite_id: p for p in existing_stores}

            # Lưu stores vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for store_data in stores_data:
                yonsuite_id = str(store_data.get("id"))
                store = existing_stores_dict.get(yonsuite_id)

                if not store:
                    # Tạo store mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': store_data.get("name") or store_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API list
                    vals.update(self._prepare_store_data_from_api(store_data))

                    # Gọi API detail để lấy thông tin đầy đủ
                    detail_data = self._get_store_detail_from_api(yonsuite_id)
                    if detail_data:
                        vals.update(self._prepare_store_data_from_detail_api(detail_data))

                    store = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modify_time có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modify_time = api_service._convert_datetime_string(store_data.get("modifyTime"))

                    if api_modify_time and store.modify_time != api_modify_time:
                        store._update_store_from_api_data(store_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.stores_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.stores_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.stores_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.stores_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.stores_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.stores_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync stores from YonSuite: %s", error_msg)
                return 0

    def _prepare_store_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu store từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'name': api_data.get("name"),
            'mnemonic': api_data.get("mnemonic"),
            'codebianma': api_data.get("codebianma"),
            'orgid': api_data.get("org"),  # Set orgid from API org field
            'org_name': api_data.get("org_name"),
            'cust': api_data.get("cust"),
            'cust_name': api_data.get("cust_name"),
            'warehouse': api_data.get("warehouse"),
            'warehouse_name': api_data.get("warehouse_name"),
            'area_class': api_data.get("areaClass"),
            'area_class_name': api_data.get("areaClass_name"),
            'store_type': api_data.get("storeType", 0),
            'membercorp': api_data.get("membercorp", 0),
            'c_app_id': api_data.get("cAppID"),
            'stop': api_data.get("stop", False),
            'creator': api_data.get("creator"),
            'modifier': api_data.get("modifier"),
        }

        # Tự động tìm org_id dựa vào org từ API
        org_from_api = api_data.get("org")
        if org_from_api:
            # Tìm yonsuite.orgunit có yonsuite_id = org_from_api và đã synced
            orgunit = self.env['yonsuite.orgunit'].search([('yonsuite_id', '=', org_from_api), ('state', '=', 'synced')], limit=1)
            if orgunit:
                vals['org_id'] = orgunit.id
                vals['org_name'] = orgunit.name  # Tự động điền org_name
            else:
                # Nếu không tìm thấy orgunit đã synced, để trống org_id
                vals['org_id'] = False
        else:
            vals['org_id'] = False

        # Tự động tìm cust_id dựa vào cust từ API
        cust_from_api = api_data.get("cust")
        if cust_from_api:
            # Tìm yonsuite.partner có yonsuite_id = cust_from_api và đã synced
            partner = self.env['yonsuite.partner'].search([('yonsuite_id', '=', cust_from_api), ('state', '=', 'synced')], limit=1)
            if partner:
                vals['cust_id'] = partner.id
                vals['cust_name'] = partner.name  # Tự động điền cust_name
            else:
                # Nếu không tìm thấy partner đã synced, để trống cust_id
                vals['cust_id'] = False
        else:
            vals['cust_id'] = False

        # Tự động tìm warehouse_id dựa vào warehouse từ API
        warehouse_from_api = api_data.get("warehouse")
        if warehouse_from_api:
            # Tìm yonsuite.warehouse có yonsuite_id = warehouse_from_api và đã synced
            warehouse = self.env['yonsuite.warehouse'].search([('yonsuite_id', '=', warehouse_from_api), ('state', '=', 'synced')], limit=1)
            if warehouse:
                vals['warehouse_id'] = warehouse.id
                vals['warehouse_name'] = warehouse.name  # Tự động điền warehouse_name
            else:
                # Nếu không tìm thấy warehouse đã synced, để trống warehouse_id
                vals['warehouse_id'] = False
        else:
            vals['warehouse_id'] = False

        # Tự động tìm area_class_id dựa vào areaClass từ API
        area_class_from_api = api_data.get("areaClass")
        if area_class_from_api:
            # Tìm yonsuite.salearea có yonsuite_id = area_class_from_api và đã synced
            salearea = self.env['yonsuite.salearea'].search([('yonsuite_id', '=', area_class_from_api), ('state', '=', 'synced')], limit=1)
            if salearea:
                vals['area_class_id'] = salearea.id
                vals['area_class_name'] = salearea.name  # Tự động điền area_class_name
            else:
                # Nếu không tìm thấy salearea đã synced, để trống area_class_id
                vals['area_class_id'] = False
        else:
            vals['area_class_id'] = False

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        if api_data.get("createTime"):
            converted_datetime = api_service._convert_datetime_string(api_data["createTime"])
            if converted_datetime:
                vals['create_time'] = converted_datetime

        if api_data.get("modifyTime"):
            converted_datetime = api_service._convert_datetime_string(api_data["modifyTime"])
            if converted_datetime:
                vals['modify_time'] = converted_datetime

        return vals

    def _prepare_store_data_push_to_yonsuite(self):
        """
        Chuẩn bị dữ liệu store để push lên YonSuite API
        """
        self.ensure_one()
        
        # Chuẩn bị dữ liệu cơ bản
        store_data = {
            "org": self.orgid or "",
            "codebianma": self.codebianma or "",
            "name": {
                "zh_CN": self.name or "",
                "en_US": self.name or "",
                "zh_TW": self.name or ""
            },
            "mnemonic": self.mnemonic or "",
            "terminalType": self.terminal_type or "4",
            "storeType": str(self.store_type) if self.store_type else "1",
            "platformType": self.platform_type or "12",
            "code": self.code or "",
            "centralWarehouseDistribution": str(self.central_warehouse_distribution) if self.central_warehouse_distribution else "0",
            "channelCustomer": str(self.channel_customer) if self.channel_customer else "0",
            "merchantStore": self.merchant_store or 0,
            "cust": self.cust or "",
            "regionCode": "DEVTEST",
            "province": "北京市",
            "city": "市辖区",
            "area": "东城区",
            "deliveryMethod": self.delivery_method or "circle",
            "warehouses": [
                {
                    "isDefault": "1",
                    "isDefaultMaterial": "0",
                    "isDefaultRequire": "0",
                    "warehouse": self.warehouse or "",
                    "priorityLevel": "1",
                    "_status": "Insert"
                }
            ],
            "welcome": {
                "zh_CN": self.name or "",
                "en_US": self.name or "",
                "zh_TW": self.name or ""
            },
            "iQRCode": {
                "_status": "Insert"
            },
            "desc": self.name or "",
            "stop": "0" if not self.stop else "1",
            "productsOfStore": "",
            "maxNumLicence": 100,
            "iOnlineDelivery": str(self.i_online_delivery) if self.i_online_delivery else "1",
            "kmradius": self.km_radius or 5,
            "circleRadius": self.circle_radius or 5000,
            "startTime": self.start_time or "10:00:00",
            "endTime": self.end_time or "21:00:00",
            "shareRes": self.share_res or 2,
            "shoppingMall": {
                "iStart": "1",
                "iDeleted": "0",
                "isHeadQuarters": "false",
                "iHotSpot": "0",
                "name": "Shopping mail",
                "referenceRetailPrice": "0",
                "cInventoryType": "0",
                "deliveryMethod": "circle",
                "cPaytypeCodes": "weixin",
                "deliveryType": "0",
                "iDistributionMode": "2",
                "latitude": "20.835245981144904",
                "longitude": "106.66470745432152",
                "_status": "Insert"
            },
            "electronicCommerce": [
                {
                    "platType": "12",
                    "invoiceType": "EnterpriseDeliver",
                    "isAutoAccessOrder": "false",
                    "autoMergerDelivery": "true",
                    "autoMatchWarehouse": "true",
                    "autoMatchLogistics": "true",
                    "autoMatchWarehouseByInv": "false",
                    "autoMatchExpressByWeight": "false",
                    "isModifyAdress": "false",
                    "isSplitRefund": 0,
                    "autoMatchRefund": "false",
                    "taxPayer": "0",
                    "isAgRefund": "false",
                    "isModifySku": "false",
                    "isProviderShop": "false",
                    "autoDeliveryWarning": "true",
                    "shopName": "",
                    "shopCode": "",
                    "accordingTo": "0",
                    "storevalue_transtype": "",
                    "trade_transtype": "",
                    "refund_transtype": "",
                    "ys_salesman": "",
                    "memo": "",
                    "ys_currency": "2298333362375360520",
                    "_status": ""
                }
            ],
            "operatorStore": [
                {
                    "operatorId": "",
                    "_status": "Insert"
                }
            ],
            "AdjacentStores": [
                {
                    "_status": ""
                }
            ],
            "paymentMethodStore": [
                {
                    "_status": ""
                }
            ],
            "_status": "Insert",
            "latestFollowUpTime": "",
            "storeDefineCharacter": {
                "id": ""
            }
        }
        
        return {"data": [store_data]}

    def _get_store_detail_from_api(self, store_id):
        """
        Gọi API detail để lấy thông tin đầy đủ của store
        """
        try:
            api_service = self.env['yonsuite.api']
            result = api_service.get_store_detail_from_api(store_id)
            
            if result.get("code") == "200":
                return result.get("data", {})
            else:
                _logger.warning("Failed to get store detail for ID %s: %s", store_id, result.get("message"))
                return None
        except Exception as e:
            _logger.error("Error getting store detail for ID %s: %s", store_id, str(e))
            return None

    def _prepare_store_data_from_detail_api(self, detail_data):
        """
        Chuẩn bị dữ liệu store từ API detail response
        """
        vals = {
            'platform_type': detail_data.get("platformType"),
            'terminal_type': detail_data.get("terminalType"),
            'terminal_category': detail_data.get("terminalCategory"),
            'channel_customer': detail_data.get("channelCustomer", 0),
            'merchant_store': detail_data.get("merchantStore", 0),
            'delivery_method': detail_data.get("deliveryMethod"),
            'km_radius': detail_data.get("kmradius", 0),
            'circle_radius': detail_data.get("circleRadius", 0),
            'start_time': detail_data.get("startTime"),
            'end_time': detail_data.get("endTime"),
            'i_online_delivery': detail_data.get("iOnlineDelivery", 0),
            'central_warehouse_distribution': detail_data.get("centralWarehouseDistribution", 0),
            'share_res': detail_data.get("shareRes", 0),
            'cust_shipping_address': detail_data.get("custShippingAddress"),
            'cust_shipping_address_name': detail_data.get("custShippingAddress_cAddress"),
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if detail_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(detail_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        if detail_data.get("createTime"):
            converted_datetime = api_service._convert_datetime_string(detail_data["createTime"])
            if converted_datetime:
                vals['create_time'] = converted_datetime

        if detail_data.get("modifyTime"):
            converted_datetime = api_service._convert_datetime_string(detail_data["modifyTime"])
            if converted_datetime:
                vals['modify_time'] = converted_datetime

        return vals
