# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteVendor(models.Model):
    _name = 'yonsuite.vendor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Vendor'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Vendor ID from YonSuite API'
    )

    code = fields.Char(
        string='Vendor Code',
        help='Vendor code from YonSuite'
    )

    name = fields.Char(
        string='Vendor Name',
        required=True,
        help='Vendor name'
    )

    org_name = fields.Char(
        string='Organization Name',
        help='Organization name'
    )

    # Thông tin liên hệ
    contactphone = fields.Char(
        string='Contact Phone',
        help='Contact phone number'
    )

    vendorphone = fields.Char(
        string='Vendor Phone',
        help='Vendor phone number'
    )

    # Thông tin tổ chức
    org = fields.Char(
        string='Organization ID',
        readonly=True,
        help='Organization ID'
    )

    vendor_apply_range_id = fields.Char(
        string='Vendor Apply Range ID',
        readonly=True,
        help='Vendor apply range ID'
    )

    vendor_apply_range_org = fields.Char(
        string='Vendor Apply Range Org',
        readonly=True,
        help='Vendor apply range organization'
    )

    vendor_apply_range_org_name = fields.Char(
        string='Vendor Apply Range Org Name',
        readonly=True,
        help='Vendor apply range organization name'
    )

    # Thông tin phân loại
    vendorclass = fields.Char(
        string='Vendor Class ID',
        readonly=True,
        help='Vendor class ID'
    )

    vendorclass_name = fields.Char(
        string='Vendor Class Name',
        readonly=True,
        help='Vendor class name'
    )

    vendor_character_define_id = fields.Char(
        string='Vendor Character Define ID',
        readonly=True,
        help='Vendor character define ID'
    )

    # Thông tin trạng thái
    is_applied = fields.Boolean(
        string='Is Applied',
        default=False,
        help='Is vendor applied'
    )

    is_creator = fields.Boolean(
        string='Is Creator',
        default=False,
        help='Is creator'
    )

    internalunit = fields.Boolean(
        string='Internal Unit',
        default=False,
        help='Is internal unit'
    )

    retail_investors = fields.Boolean(
        string='Retail Investors',
        default=False,
        help='Is retail investors'
    )

    stop = fields.Boolean(
        string='Stop',
        default=False,
        help='Stop status'
    )

    # Thông tin thuế
    tax_paying_categories = fields.Integer(
        string='Tax Paying Categories',
        default=0,
        help='Tax paying categories'
    )

    # Thông tin cung cấp
    supply_type = fields.Integer(
        string='Supply Type',
        default=0,
        help='Supply type'
    )

    bcoordination = fields.Integer(
        string='B Coordination',
        default=0,
        help='B coordination'
    )

    # Thông tin nguồn dữ liệu
    datasource = fields.Char(
        string='Data Source',
        readonly=True,
        help='Data source'
    )

    primary_key_for_delete = fields.Char(
        string='Primary Key For Delete',
        readonly=True,
        help='Primary key for delete'
    )

    # Thông tin thời gian
    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

    # Vendor Character Define
    vendor_character_define_ytenant = fields.Char(
        string='Vendor Character Define YTenant',
        readonly=True,
        help='Vendor character define ytenant'
    )

    vendor_character_define_pubts = fields.Datetime(
        string='Vendor Character Define Pubts',
        readonly=True,
        help='Vendor character define pubts'
    )

    # Vendor Extends
    vendor_extends_id = fields.Char(
        string='Vendor Extends ID',
        readonly=True,
        help='Vendor extends ID'
    )

    vendor_extends_freeze_status = fields.Integer(
        string='Freeze Status',
        default=0,
        help='Freeze status'
    )

    vendor_extends_creator = fields.Char(
        string='Vendor Extends Creator',
        readonly=True,
        help='Vendor extends creator'
    )

    vendor_extends_delivery_vendor = fields.Char(
        string='Delivery Vendor',
        readonly=True,
        help='Delivery vendor ID'
    )

    vendor_extends_invoice_vendor = fields.Char(
        string='Invoice Vendor',
        readonly=True,
        help='Invoice vendor ID'
    )

    vendor_extends_currency = fields.Char(
        string='Currency ID',
        readonly=True,
        help='Currency ID'
    )

    vendor_extends_currency_name = fields.Char(
        string='Currency Name',
        readonly=True,
        help='Currency name'
    )

    vendor_extends_vendor = fields.Char(
        string='Vendor ID',
        readonly=True,
        help='Vendor ID in extends'
    )

    vendor_extends_modifier = fields.Char(
        string='Vendor Extends Modifier',
        readonly=True,
        help='Vendor extends modifier'
    )

    vendor_extends_create_time = fields.Datetime(
        string='Vendor Extends Create Time',
        readonly=True,
        help='Vendor extends create time'
    )

    vendor_extends_modify_time = fields.Datetime(
        string='Vendor Extends Modify Time',
        readonly=True,
        help='Vendor extends modify time'
    )

    vendor_extends_help_code = fields.Char(
        string='Help Code',
        readonly=True,
        help='Help code'
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
        help='Last time this vendor was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync vendor data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu vendor
        api_service = self.env['yonsuite.api']
        result = api_service.get_vendors_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            vendors_data = data.get("recordList", [])

            # Tìm vendor hiện tại trong dữ liệu trả về
            current_vendor = None
            for vendor_data in vendors_data:
                if str(vendor_data.get("id")) == str(self.yonsuite_id):
                    current_vendor = vendor_data
                    break

            if current_vendor:
                # Cập nhật dữ liệu vendor
                self._update_vendor_from_api_data(current_vendor)

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
                        'message': _('Vendor "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Vendor not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_vendor_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu vendor từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_vendor_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    @api.model
    def action_import_vendors_pagination(self):
        """
        Sync vendors từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.vendors_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu vendors
        api_service = self.env['yonsuite.api']
        result = api_service.get_vendors_from_api(current_page, page_size)

        if result.get("code") == "200":
            data = result.get("data", {})
            vendors_data = data.get("recordList", [])

            if not vendors_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.vendors_current_page', '1')
                _logger.info("No more vendors data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(vendors_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(vendors_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(vendor_data.get("id")) for vendor_data in vendors_data]

            # Search một lần duy nhất tất cả vendors đã tồn tại
            existing_vendors = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_vendors_dict = {v.yonsuite_id: v for v in existing_vendors}

            # Lưu vendors vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for vendor_data in vendors_data:
                yonsuite_id = str(vendor_data.get("id"))
                vendor = existing_vendors_dict.get(yonsuite_id)

                if not vendor:
                    # Tạo vendor mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': vendor_data.get("name"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_vendor_data_from_api(vendor_data))

                    vendor = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modify_time có thay đổi không
                    vendor_extends = vendor_data.get("vendorextends", {})
                    api_service = self.env['yonsuite.api']
                    api_modify_time = api_service._convert_datetime_string(vendor_extends.get("modifyTime"))

                    if api_modify_time and vendor.vendor_extends_modify_time != api_modify_time:
                        vendor._update_vendor_from_api_data(vendor_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.vendors_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                             current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.vendors_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                             current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.vendors_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.vendors_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.vendors_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.vendors_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync vendors from YonSuite: %s", error_msg)
                return 0

    def _prepare_vendor_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu vendor từ API response
        """
        vals = {
            'yonsuite_id': str(api_data.get("id")),
            'code': api_data.get("code"),
            'name': api_data.get("name"),
            'org_name': api_data.get("org_name"),
            'contactphone': api_data.get("contactphone"),
            'vendorphone': api_data.get("vendorphone"),
            'org': str(api_data.get("org")) if api_data.get("org") else False,
            'vendor_apply_range_id': str(api_data.get("vendorApplyRangeId")) if api_data.get("vendorApplyRangeId") else False,
            'vendor_apply_range_org': str(api_data.get("vendorApplyRange_org")) if api_data.get("vendorApplyRange_org") else False,
            'vendor_apply_range_org_name': api_data.get("vendorApplyRange_org_name"),
            'vendorclass': str(api_data.get("vendorclass")) if api_data.get("vendorclass") else False,
            'vendorclass_name': api_data.get("vendorclass_name"),
            'vendor_character_define_id': str(api_data.get("vendorCharacterDefine__id")) if api_data.get("vendorCharacterDefine__id") else False,
            'is_applied': api_data.get("isApplied", False),
            'is_creator': api_data.get("isCreator", False),
            'internalunit': api_data.get("internalunit", False),
            'retail_investors': api_data.get("retailInvestors", False),
            'stop': api_data.get("stop", False),
            'tax_paying_categories': api_data.get("taxPayingCategories", 0),
            'supply_type': api_data.get("supplyType", 0),
            'bcoordination': api_data.get("bcoordination", 0),
            'datasource': api_data.get("datasource"),
            'primary_key_for_delete': api_data.get("primaryKeyForDelete"),
        }

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        # Handle vendor character define
        vendor_character_def = api_data.get("vendorCharacterDefine", {})
        if vendor_character_def:
            vals['vendor_character_define_ytenant'] = vendor_character_def.get("ytenant")
            if vendor_character_def.get("pubts"):
                converted_datetime = api_service._convert_datetime_string(vendor_character_def["pubts"])
                if converted_datetime:
                    vals['vendor_character_define_pubts'] = converted_datetime

        # Handle vendor extends
        vendor_extends = api_data.get("vendorextends", {})
        if vendor_extends:
            vals.update({
                'vendor_extends_id': str(vendor_extends.get("id")) if vendor_extends.get("id") else False,
                'vendor_extends_freeze_status': vendor_extends.get("freezestatus", 0),
                'vendor_extends_creator': vendor_extends.get("creator"),
                'vendor_extends_delivery_vendor': str(vendor_extends.get("deliveryvendor")) if vendor_extends.get("deliveryvendor") else False,
                'vendor_extends_invoice_vendor': str(vendor_extends.get("invoicevendor")) if vendor_extends.get("invoicevendor") else False,
                'vendor_extends_currency': str(vendor_extends.get("currency")) if vendor_extends.get("currency") else False,
                'vendor_extends_currency_name': vendor_extends.get("currencyname"),
                'vendor_extends_vendor': str(vendor_extends.get("vendor")) if vendor_extends.get("vendor") else False,
                'vendor_extends_modifier': vendor_extends.get("modifier"),
                'vendor_extends_help_code': vendor_extends.get("helpcode"),
            })

            # Handle vendor extends datetime fields
            if vendor_extends.get("createTime"):
                converted_datetime = api_service._convert_datetime_string(vendor_extends["createTime"])
                if converted_datetime:
                    vals['vendor_extends_create_time'] = converted_datetime

            if vendor_extends.get("modifyTime"):
                converted_datetime = api_service._convert_datetime_string(vendor_extends["modifyTime"])
                if converted_datetime:
                    vals['vendor_extends_modify_time'] = converted_datetime

        return vals

    def action_reset_to_draft(self):
        """
        Reset vendor to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })
