# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuitePartner(models.Model):
    _name = 'yonsuite.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Partner'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Partner ID from YonSuite API'
    )

    code = fields.Char(
        string='Partner Code',
        help='Partner code from YonSuite'
    )

    name = fields.Char(
        string='Partner Name',
        required=True,
        help='Partner name'
    )

    simplified_name = fields.Char(
        string='Simplified Name',
        help='Simplified name from YonSuite'
    )

    # Thông tin tổ chức
    create_org_id = fields.Char(
        string='Create Org ID',
        readonly=True,
        help='Create organization ID'
    )

    create_org_code = fields.Char(
        string='Create Org Code',
        readonly=True,
        help='Create organization code'
    )

    belong_org_id = fields.Char(
        string='Belong Org ID',
        readonly=True,
        help='Belong organization ID'
    )

    belong_org_code = fields.Char(
        string='Belong Org Code',
        readonly=True,
        help='Belong organization code'
    )

    # Thông tin giao dịch
    trans_type_id = fields.Char(
        string='Transaction Type ID',
        readonly=True,
        help='Transaction type ID'
    )

    trans_type_code = fields.Char(
        string='Transaction Type Code',
        readonly=True,
        help='Transaction type code'
    )

    # Thông tin khách hàng
    customer_class_id = fields.Char(
        string='Customer Class ID',
        readonly=True,
        help='Customer class ID'
    )

    customer_class_code = fields.Char(
        string='Customer Class Code',
        readonly=True,
        help='Customer class code'
    )

    # Thông tin doanh nghiệp
    retail_investors = fields.Boolean(
        string='Retail Investors',
        default=False,
        help='Is retail investors'
    )

    internal_org = fields.Boolean(
        string='Internal Organization',
        default=False,
        help='Is internal organization'
    )

    tax_paying_categories = fields.Integer(
        string='Tax Paying Categories',
        default=0,
        help='Tax paying categories'
    )

    enterprise_nature = fields.Integer(
        string='Enterprise Nature',
        default=0,
        help='Enterprise nature'
    )

    scope_model = fields.Integer(
        string='Scope Model',
        default=0,
        help='Scope model'
    )

    stop_status = fields.Boolean(
        string='Stop Status',
        default=False,
        help='Stop status'
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
        help='Last time this partner was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync partner data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu partner
        api_service = self.env['yonsuite.api']
        result = api_service.get_partners_from_api()

        if result.get("code") == "200":
            partners_data = result.get("data", [])

            # Tìm partner hiện tại trong dữ liệu trả về
            current_partner = None
            for partner_data in partners_data:
                if str(partner_data.get("id")) == str(self.yonsuite_id):
                    current_partner = partner_data
                    break

            if current_partner:
                # Cập nhật dữ liệu partner
                self._update_partner_from_api_data(current_partner)

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
                        'message': _('Partner "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Partner not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_partner_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu partner từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_partner_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset partner to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_partners_pagination(self):
        """
        Sync partners từ YonSuite API với phân trang và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Lấy pageIndex hiện tại từ config
        current_page = int(config_parameter.get_param('yonsuite_integration.partners_current_page', '1'))
        page_size = 5000

        # Gọi API để lấy dữ liệu partners
        api_service = self.env['yonsuite.api']
        result = api_service.get_partners_from_api(current_page, page_size)

        if result.get("code") == "200":
            partners_data = result.get("data", [])

            if not partners_data:
                # Không có dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.partners_current_page', '1')
                _logger.info("No more partners data, reset to page 1")
                return 0

            # Kiểm tra nếu số lượng records ít hơn page_size thì đã hết dữ liệu
            if len(partners_data) < page_size:
                _logger.info("Received %d records (less than page_size %d), this is the last page", len(partners_data), page_size)
                # Đánh dấu để reset sau khi xử lý xong
                should_reset = True
            else:
                should_reset = False
            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(partner_data.get("id")) for partner_data in partners_data]

            # Search một lần duy nhất tất cả partners đã tồn tại
            existing_partners = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_partners_dict = {p.yonsuite_id: p for p in existing_partners}

            # Lưu partners vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for partner_data in partners_data:
                yonsuite_id = str(partner_data.get("id"))
                partner = existing_partners_dict.get(yonsuite_id)

                if not partner:
                    # Tạo partner mới với đầy đủ dữ liệu
                    name_data = partner_data.get("name", {})
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': name_data.get("simplifiedName") or partner_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_partner_data_from_api(partner_data))

                    partner = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modify_time có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modify_time = api_service._convert_datetime_string(partner_data.get("modifyTime"))

                    if api_modify_time and partner.modify_time != api_modify_time:
                        partner._update_partner_from_api_data(partner_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật pageIndex cho lần tiếp theo
            if should_reset:
                # Đã hết dữ liệu, reset về trang 1
                config_parameter.set_param('yonsuite_integration.partners_current_page', '1')
                _logger.info("Page %d (last page): Created %d, Updated %d, Skipped %d, Total %d - Reset to page 1",
                                current_page, created_count, updated_count, skipped_count, synced_count)
            else:
                # Còn dữ liệu, tăng pageIndex
                next_page = current_page + 1
                config_parameter.set_param('yonsuite_integration.partners_current_page', str(next_page))
                _logger.info("Page %d: Created %d, Updated %d, Skipped %d, Total %d - Next page: %d",
                                current_page, created_count, updated_count, skipped_count, synced_count, next_page)

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.partners_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.partners_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.partners_last_sync', fields.Datetime.now())

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
                config_parameter.set_param('yonsuite_integration.partners_current_page', '1')
                _logger.info("Query result is empty (message: '%s'), reset to page 1", message)
                return 0
            else:
                # Lỗi khác
                error_msg = result.get("message", "Unknown error")
                _logger.error("Failed to sync partners from YonSuite: %s", error_msg)
                return 0

    def _prepare_partner_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu partner từ API response
        """
        name_data = api_data.get("name", {})

        vals = {
            'code': api_data.get("code"),
            'name': name_data.get("simplifiedName") or api_data.get("code"),
            'simplified_name': name_data.get("simplifiedName"),
            'create_org_id': api_data.get("createOrgId"),
            'create_org_code': api_data.get("createOrgCode"),
            'belong_org_id': api_data.get("belongOrgId"),
            'belong_org_code': api_data.get("belongOrgCode"),
            'trans_type_id': api_data.get("transTypeId"),
            'trans_type_code': api_data.get("transTypeCode"),
            'customer_class_id': api_data.get("customerClassId"),
            'customer_class_code': api_data.get("customerClassCode"),
            'retail_investors': api_data.get("retailInvestors", False),
            'internal_org': api_data.get("internalOrg", False),
            'tax_paying_categories': api_data.get("taxPayingCategories", 0),
            'enterprise_nature': api_data.get("enterpriseNature", 0),
            'scope_model': api_data.get("scopeModel", 0),
            'stop_status': api_data.get("stopStatus", False),
            'creator': api_data.get("creator"),
            'modifier': api_data.get("modifier"),
        }

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

