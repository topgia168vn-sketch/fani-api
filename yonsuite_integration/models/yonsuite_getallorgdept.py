# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteGetallorgdept(models.Model):
    _name = 'yonsuite.getallorgdept'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Get All Org Dept'
    _order = 'create_date desc'
    _parent_name = 'parent_id'
    _parent_store = True

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Organization/Department ID from YonSuite API'
    )

    code = fields.Char(
        string='Code',
        help='Organization/Department code from YonSuite'
    )

    name = fields.Char(
        string='Name',
        required=True,
        help='Organization/Department name'
    )

    # Thông tin tổ chức
    parent_name = fields.Char(
        string='Parent Name',
        readonly=True,
        help='Parent organization/department name'
    )

    parentorgid_code = fields.Char(
        string='Parent Org ID Code',
        readonly=True,
        help='Parent organization ID code'
    )

    path = fields.Char(
        string='Path',
        readonly=True,
        help='Organization/Department path'
    )

    level = fields.Integer(
        string='Level',
        default=1,
        help='Organization/Department level'
    )

    # Thông tin doanh nghiệp
    orgid = fields.Char(
        string='Organization ID',
        readonly=True,
        help='Organization ID'
    )

    orgtype = fields.Integer(
        string='Organization Type',
        default=1,
        help='Organization type (1=Organization, 2=Department)'
    )

    isbizunit = fields.Boolean(
        string='Is Business Unit',
        default=False,
        help='Is business unit'
    )

    isEnd = fields.Boolean(
        string='Is End',
        default=False,
        help='Is end organization/department'
    )

    externalorg = fields.Boolean(
        string='External Organization',
        default=False,
        help='Is external organization'
    )

    # Thông tin thuế
    taxpayername = fields.Char(
        string='Tax Payer Name',
        help='Tax payer name'
    )

    taxpayerid = fields.Char(
        string='Tax Payer ID',
        help='Tax payer ID'
    )

    taxpayertype = fields.Integer(
        string='Tax Payer Type',
        default=1,
        help='Tax payer type'
    )

    companytype = fields.Char(
        string='Company Type',
        help='Company type ID'
    )

    companytype_name = fields.Char(
        string='Company Type Name',
        help='Company type name'
    )

    # Thông tin trạng thái
    enable = fields.Integer(
        string='Enable',
        default=1,
        help='Enable status (1=Enabled, 2=Disabled)'
    )

    dr = fields.Integer(
        string='DR',
        default=0,
        help='DR flag'
    )

    # Thông tin sắp xếp
    sort = fields.Integer(
        string='Sort',
        default=0,
        help='Sort order'
    )

    displayorder = fields.Integer(
        string='Display Order',
        default=0,
        help='Display order'
    )

    # Thông tin thời gian
    pubts = fields.Datetime(
        string='Publish Time',
        readonly=True,
        help='Publish timestamp'
    )

    creationtime = fields.Datetime(
        string='Creation Time',
        readonly=True,
        help='Creation time from YonSuite'
    )

    modifiedtime = fields.Datetime(
        string='Modified Time',
        readonly=True,
        help='Modified time from YonSuite'
    )

    effectivedate = fields.Datetime(
        string='Effective Date',
        readonly=True,
        help='Effective date from YonSuite'
    )

    expirationdate = fields.Datetime(
        string='Expiration Date',
        readonly=True,
        help='Expiration date from YonSuite'
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

    # Thông tin hệ thống
    tenantid = fields.Char(
        string='Tenant ID',
        readonly=True,
        help='Tenant ID'
    )

    tenant = fields.Char(
        string='Tenant',
        readonly=True,
        help='Tenant name'
    )

    sysid = fields.Char(
        string='System ID',
        readonly=True,
        help='System ID'
    )

    sourceid = fields.Char(
        string='Source ID',
        readonly=True,
        help='Source ID'
    )

    exchangerate = fields.Char(
        string='Exchange Rate',
        readonly=True,
        help='Exchange rate'
    )

    exchangerate_name = fields.Char(
        string='Exchange Rate Name',
        readonly=True,
        help='Exchange rate name'
    )

    countryzone = fields.Char(
        string='Country Zone',
        readonly=True,
        help='Country zone ID'
    )

    language = fields.Char(
        string='Language',
        readonly=True,
        help='Language ID'
    )

    # Thông tin người phụ trách
    principal = fields.Char(
        string='Principal ID',
        readonly=True,
        help='Principal ID'
    )

    principal_name = fields.Char(
        string='Principal Name',
        readonly=True,
        help='Principal name'
    )

    # Thông tin tên ngắn
    shortname = fields.Char(
        string='Short Name',
        readonly=True,
        help='Short name'
    )

    # Thông tin mở rộng
    deptOrgExt_id = fields.Char(
        string='Dept Org Ext ID',
        readonly=True,
        help='Department organization extension ID'
    )

    # Quan hệ cha con
    parent_id = fields.Many2one(
        'yonsuite.getallorgdept',
        string='Parent Organization/Department',
        readonly=True,
        help='Parent organization/department'
    )

    # Trường quan hệ để chọn parent record
    parent_orgunit_id = fields.Many2one(
        'yonsuite.orgunit',
        string='Parent Organization Unit',
        help='Parent organization unit (for level 2 records)'
    )

    parent_getallorgdept_id = fields.Many2one(
        'yonsuite.getallorgdept',
        string='Parent Org/Dept Record',
        help='Parent organization/department record (for level 3+ records)'
    )

    child_ids = fields.One2many(
        'yonsuite.getallorgdept',
        'parent_id',
        string='Child Organizations/Departments',
        readonly=True,
        help='Child organizations/departments'
    )

    parent_left = fields.Integer(
        string='Parent Left',
        readonly=True,
        help='Left boundary for parent tree'
    )

    parent_right = fields.Integer(
        string='Parent Right',
        readonly=True,
        help='Right boundary for parent tree'
    )

    parent_path = fields.Char(
        string='Parent Path',
        readonly=True,
        index=True,
        help='Parent path for tree structure'
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
        help='Last time this organization/department was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync organization/department data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu organizations/departments
        api_service = self.env['yonsuite.api']
        result = api_service.get_all_orgdept_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            record_list = data.get("recordList", [])

            # Tìm organization/department hiện tại trong dữ liệu trả về
            current_record = None
            for record_data in record_list:
                if str(record_data.get("id")) == str(self.yonsuite_id):
                    current_record = record_data
                    break

            if current_record:
                # Cập nhật dữ liệu organization/department
                self._update_record_from_api_data(current_record)

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
                        'message': _('Organization/Department "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Organization/Department not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_record_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu organization/department từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_record_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)
        # Cập nhật quan hệ cha con
        self._update_parent_relationship()

    def action_reset_to_draft(self):
        """
        Reset organization/department to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_getallorgdept_pagination(self):
        """
        Sync organizations/departments từ YonSuite API và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Gọi API để lấy dữ liệu organizations/departments
        api_service = self.env['yonsuite.api']
        result = api_service.get_all_orgdept_from_api()

        if result.get("code") == "200":
            data = result.get("data", {})
            record_list = data.get("recordList", [])

            if not record_list:
                _logger.info("No organizations/departments data received")
                return 0

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(record_data.get("id")) for record_data in record_list]

            # Search một lần duy nhất tất cả records đã tồn tại
            existing_records = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_records_dict = {p.yonsuite_id: p for p in existing_records}

            # Lưu records vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for record_data in record_list:
                yonsuite_id = str(record_data.get("id"))
                record = existing_records_dict.get(yonsuite_id)

                if not record:
                    # Tạo record mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': record_data.get("name") or record_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_record_data_from_api(record_data))

                    record = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modifiedtime có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modified_time = api_service._convert_datetime_string(record_data.get("modifiedtime"))

                    if api_modified_time and record.modifiedtime != api_modified_time:
                        record._update_record_from_api_data(record_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật quan hệ cha con cho tất cả records
            try:
                all_records = self.search([])
                all_records._update_parent_relationship()
                # Tính toán lại parent store
                self._compute_parent_store()
                _logger.info("Parent relationships updated successfully")
            except Exception as e:
                _logger.error("Failed to update parent relationships: %s", str(e))

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.getallorgdept_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.getallorgdept_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.getallorgdept_last_sync', fields.Datetime.now())

            _logger.info("GetAllOrgDept Sync: Created %d, Updated %d, Skipped %d, Total %d",
                        created_count, updated_count, skipped_count, synced_count)

            return synced_count
        else:
            # Lỗi khác
            error_msg = result.get("message", "Unknown error")
            _logger.error("Failed to sync getallorgdept from YonSuite: %s", error_msg)
            return 0

    def _prepare_record_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu organization/department từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'name': api_data.get("name"),
            'parent_name': api_data.get("parent_name"),
            'parentorgid_code': api_data.get("parentorgid_code"),
            'path': api_data.get("path"),
            'level': api_data.get("level", 1),
            'orgid': api_data.get("orgid"),
            'orgtype': api_data.get("orgtype", 1),
            'isbizunit': api_data.get("isbizunit", False),
            'isEnd': api_data.get("isEnd", False),
            'externalorg': api_data.get("externalorg", False),
            'taxpayername': api_data.get("taxpayername"),
            'taxpayerid': api_data.get("taxpayerid"),
            'taxpayertype': api_data.get("taxpayertype", 1),
            'companytype': api_data.get("companytype"),
            'companytype_name': api_data.get("companytype_name"),
            'enable': api_data.get("enable", 1),
            'dr': api_data.get("dr", 0),
            'sort': api_data.get("sort", 0),
            'displayorder': api_data.get("displayorder", 0),
            'creator': api_data.get("creator"),
            'modifier': api_data.get("modifier"),
            'tenantid': api_data.get("tenantid"),
            'tenant': api_data.get("tenant"),
            'sysid': api_data.get("sysid"),
            'sourceid': api_data.get("sourceid"),
            'exchangerate': api_data.get("exchangerate"),
            'exchangerate_name': api_data.get("exchangerate_name"),
            'countryzone': api_data.get("countryzone"),
            'language': api_data.get("language"),
            'principal': api_data.get("principal"),
            'principal_name': api_data.get("principal_name"),
            'shortname': api_data.get("shortname"),
        }

        # Xử lý deptOrgExt
        if api_data.get("deptOrgExt"):
            dept_org_ext = api_data.get("deptOrgExt", {})
            vals['deptOrgExt_id'] = dept_org_ext.get("id")

        # Xử lý datetime fields
        api_service = self.env['yonsuite.api']
        if api_data.get("pubts"):
            converted_datetime = api_service._convert_datetime_string(api_data["pubts"])
            if converted_datetime:
                vals['pubts'] = converted_datetime

        if api_data.get("creationtime"):
            converted_datetime = api_service._convert_datetime_string(api_data["creationtime"])
            if converted_datetime:
                vals['creationtime'] = converted_datetime

        if api_data.get("modifiedtime"):
            converted_datetime = api_service._convert_datetime_string(api_data["modifiedtime"])
            if converted_datetime:
                vals['modifiedtime'] = converted_datetime

        if api_data.get("effectivedate"):
            converted_datetime = api_service._convert_datetime_string(api_data["effectivedate"])
            if converted_datetime:
                vals['effectivedate'] = converted_datetime

        if api_data.get("expirationdate"):
            converted_datetime = api_service._convert_datetime_string(api_data["expirationdate"])
            if converted_datetime:
                vals['expirationdate'] = converted_datetime

        return vals

    def _update_parent_relationship(self):
        """
        Cập nhật quan hệ cha con dựa trên parentorgid_code và level
        Logic:
        - Level 2: liên kết với yonsuite_orgunit
        - Level 3+: chọn từ chính model yonsuite_getallorgdept
        """
        for record in self:
            try:
                if record.parentorgid_code:
                    if record.level == 2:
                        # Level 2: tìm trong yonsuite_orgunit
                        parent_orgunit = self.env['yonsuite.orgunit'].search([('code', '=', record.parentorgid_code)], limit=1)
                        if parent_orgunit:
                            record.with_context(parent_store_compute=False).write({
                                'parent_orgunit_id': parent_orgunit.id,
                                'parent_getallorgdept_id': False,
                                'parent_id': False
                            })
                        else:
                            record.with_context(parent_store_compute=False).write({
                                'parent_orgunit_id': False,
                                'parent_getallorgdept_id': False,
                                'parent_id': False
                            })
                    elif record.level >= 3:
                        # Level 3+: tìm trong chính model yonsuite_getallorgdept
                        parent_record = self.search([('code', '=', record.parentorgid_code)], limit=1)
                        if parent_record and parent_record.id != record.id:
                            record.with_context(parent_store_compute=False).write({
                                'parent_orgunit_id': False,
                                'parent_getallorgdept_id': parent_record.id,
                                'parent_id': parent_record.id
                            })
                        else:
                            record.with_context(parent_store_compute=False).write({
                                'parent_orgunit_id': False,
                                'parent_getallorgdept_id': False,
                                'parent_id': False
                            })
                    else:
                        # Level 1: không có parent
                        record.with_context(parent_store_compute=False).write({
                            'parent_orgunit_id': False,
                            'parent_getallorgdept_id': False,
                            'parent_id': False
                        })
                else:
                    # Không có parentorgid_code
                    record.with_context(parent_store_compute=False).write({
                        'parent_orgunit_id': False,
                        'parent_getallorgdept_id': False,
                        'parent_id': False
                    })
            except Exception as e:
                _logger.warning("Failed to update parent relationship for record %s: %s", record.name, str(e))
                continue

    def _compute_parent_store(self):
        """
        Tính toán lại parent store fields một cách an toàn
        """
        try:
            self.env.cr.execute("""
                UPDATE yonsuite_getallorgdept 
                SET parent_left = 0, parent_right = 0, parent_path = ''
                WHERE parent_left IS NULL OR parent_right IS NULL
            """)
            
            # Tính toán lại parent store
            self._parent_store_compute()
            _logger.info("Parent store computed successfully")
        except Exception as e:
            _logger.error("Failed to compute parent store: %s", str(e))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create để xử lý parent relationship
        """
        records = super().create(vals_list)
        # Cập nhật parent relationship sau khi tạo
        try:
            records._update_parent_relationship()
        except Exception as e:
            _logger.warning("Failed to update parent relationship during create: %s", str(e))
        return records

    @api.onchange('parent_orgunit_id')
    def _onchange_parent_orgunit_id(self):
        """
        Cập nhật parent_id khi thay đổi parent_orgunit_id
        """
        if self.parent_orgunit_id and self.level == 2:
            # Không cần cập nhật parent_id vì level 2 không dùng parent_id
            pass

    @api.onchange('parent_getallorgdept_id')
    def _onchange_parent_getallorgdept_id(self):
        """
        Cập nhật parent_id khi thay đổi parent_getallorgdept_id
        """
        if self.parent_getallorgdept_id and self.level >= 3:
            self.parent_id = self.parent_getallorgdept_id.id

    def action_update_parent_relationships(self):
        """
        Action để cập nhật lại tất cả parent relationships
        """
        self.ensure_one()
        try:
            self._update_parent_relationship()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Parent relationships updated successfully!'),
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('Failed to update parent relationships: %s') % str(e),
                    'type': 'danger',
                }
            }
