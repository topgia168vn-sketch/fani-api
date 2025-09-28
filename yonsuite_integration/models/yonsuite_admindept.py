# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteAdmindept(models.Model):
    _name = 'yonsuite.admindept'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Admin Department'
    _order = 'create_date desc'
    _parent_name = 'parent_id'
    _parent_store = True

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Admin Department ID from YonSuite API'
    )

    code = fields.Char(
        string='Department Code',
        help='Department code from YonSuite'
    )

    name = fields.Char(
        string='Department Name',
        required=True,
        help='Department name'
    )

    innercode = fields.Char(
        string='Inner Code',
        help='Inner code from YonSuite'
    )

    # Thông tin tổ chức
    parent = fields.Char(
        string='Parent ID (API)',
        readonly=True,
        help='Parent department ID from API'
    )

    parentid = fields.Char(
        string='Parent ID',
        readonly=True,
        help='Parent department ID'
    )

    path = fields.Char(
        string='Path',
        readonly=True,
        help='Department path'
    )

    level = fields.Integer(
        string='Level',
        default=1,
        help='Department level'
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
        help='Organization type'
    )

    isbizunit = fields.Boolean(
        string='Is Business Unit (API)',
        default=False,
        help='Is business unit from API'
    )

    isdefault = fields.Boolean(
        string='Is Default',
        default=False,
        help='Is default department'
    )

    canEmployee = fields.Boolean(
        string='Can Employee',
        default=True,
        help='Can have employees'
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

    # Thông tin trạng thái
    enable = fields.Boolean(
        string='Enable',
        default=True,
        help='Is enabled'
    )

    frozen = fields.Boolean(
        string='Frozen',
        default=False,
        help='Is frozen'
    )

    closed = fields.Boolean(
        string='Closed',
        default=False,
        help='Is closed'
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

    globalorder = fields.Integer(
        string='Global Order',
        default=0,
        help='Global order'
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

    ts = fields.Datetime(
        string='Timestamp',
        readonly=True,
        help='Timestamp from YonSuite'
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

    ytenant = fields.Char(
        string='Y Tenant',
        readonly=True,
        help='Y Tenant name'
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

    sourcetype = fields.Integer(
        string='Source Type',
        default=1,
        help='Source type'
    )

    exchangerate = fields.Char(
        string='Exchange Rate',
        readonly=True,
        help='Exchange rate'
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

    # Thông tin chi tiết từ API detail
    parent_name = fields.Char(
        string='Parent Name',
        readonly=True,
        help='Parent department name'
    )

    parent_code = fields.Char(
        string='Parent Code',
        readonly=True,
        help='Parent department code'
    )

    parentorgid = fields.Char(
        string='Parent Org ID',
        readonly=True,
        help='Parent organization ID'
    )

    parentorgid_name = fields.Char(
        string='Parent Org Name',
        readonly=True,
        help='Parent organization name'
    )

    # Quan hệ cha con
    parent_id = fields.Many2one(
        'yonsuite.admindept',
        string='Parent Department',
        readonly=True,
        help='Parent department'
    )

    child_ids = fields.One2many(
        'yonsuite.admindept',
        'parent_id',
        string='Child Departments',
        readonly=True,
        help='Child departments'
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

    bizorgid = fields.Char(
        string='Business Org ID',
        readonly=True,
        help='Business organization ID'
    )

    bizorgid_name = fields.Char(
        string='Business Org Name',
        readonly=True,
        help='Business organization name'
    )

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

    creator_userName = fields.Char(
        string='Creator User Name',
        readonly=True,
        help='Creator user name'
    )

    modifier_userName = fields.Char(
        string='Modifier User Name',
        readonly=True,
        help='Modifier user name'
    )

    is_biz_unit = fields.Boolean(
        string='Is Business Unit',
        default=False,
        help='Is business unit'
    )

    isEnd = fields.Boolean(
        string='Is End',
        default=False,
        help='Is end department'
    )

    endtime = fields.Datetime(
        string='End Time',
        readonly=True,
        help='End time'
    )

    shortname_zh_CN = fields.Char(
        string='Short Name (Chinese)',
        readonly=True,
        help='Short name in Chinese'
    )

    shortname_vi_VN = fields.Char(
        string='Short Name (Vietnamese)',
        readonly=True,
        help='Short name in Vietnamese'
    )

    shortname_en_US = fields.Char(
        string='Short Name (English)',
        readonly=True,
        help='Short name in English'
    )

    name_zh_CN = fields.Char(
        string='Name (Chinese)',
        readonly=True,
        help='Name in Chinese'
    )

    name_vi_VN = fields.Char(
        string='Name (Vietnamese)',
        readonly=True,
        help='Name in Vietnamese'
    )

    name_en_US = fields.Char(
        string='Name (English)',
        readonly=True,
        help='Name in English'
    )

    description = fields.Text(
        string='Description',
        readonly=True,
        help='Description'
    )

    deptOrgExt_id = fields.Char(
        string='Dept Org Ext ID',
        readonly=True,
        help='Department organization extension ID'
    )

    _mddFormulaExecuteFlag = fields.Char(
        string='MDD Formula Execute Flag',
        readonly=True,
        help='MDD formula execute flag'
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
        help='Last time this department was synchronized with YonSuite'
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt'
    )

    def action_export_to_yonsuite(self):
        """
        Sync department data from YonSuite API
        """
        self.ensure_one()

        # Gọi API để lấy dữ liệu departments
        api_service = self.env['yonsuite.api']
        result = api_service.get_admindepts_from_api()

        if result.get("code") == "200":
            departments_data = result.get("data", [])

            # Tìm department hiện tại trong dữ liệu trả về
            current_department = None
            for dept_data in departments_data:
                if str(dept_data.get("id")) == str(self.yonsuite_id):
                    current_department = dept_data
                    break

            if current_department:
                # Cập nhật dữ liệu department
                self._update_department_from_api_data(current_department)

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
                        'message': _('Department "%s" has been synced from YonSuite successfully!') % self.name,
                        'type': 'success',
                    }
                }
            else:
                raise UserError(_('Department not found in YonSuite API response'))
        else:
            error_msg = result.get("message", "Unknown error")
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _update_department_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu department từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_department_data_from_api(api_data)
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
        Reset department to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_admindepts_pagination(self):
        """
        Sync departments từ YonSuite API và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Gọi API để lấy dữ liệu departments
        api_service = self.env['yonsuite.api']
        result = api_service.get_admindepts_from_api()

        if result.get("code") == "200":
            departments_data = result.get("data", [])

            if not departments_data:
                _logger.info("No departments data received")
                return 0

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(dept_data.get("id")) for dept_data in departments_data]

            # Search một lần duy nhất tất cả departments đã tồn tại
            existing_departments = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_departments_dict = {p.yonsuite_id: p for p in existing_departments}

            # Lưu departments vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for dept_data in departments_data:
                yonsuite_id = str(dept_data.get("id"))
                department = existing_departments_dict.get(yonsuite_id)
                
                # Lấy detail từ API
                dept_detail = self.env['yonsuite.api'].get_admindept_detail_from_api(yonsuite_id)
                detail_payload = {}
                if dept_detail and dept_detail.get('code') == '200':
                    detail_payload = dept_detail.get('data', {}) or {}

                if not department:
                    # Tạo department mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': dept_data.get("name") or dept_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API (ưu tiên detail payload nếu có)
                    vals.update(self._prepare_department_data_from_api(detail_payload or dept_data))

                    department = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra modifiedtime có thay đổi không
                    api_service = self.env['yonsuite.api']
                    api_modified_time = api_service._convert_datetime_string(dept_data.get("modifiedtime"))

                    if api_modified_time and department.modifiedtime != api_modified_time:
                        department._update_department_from_api_data(detail_payload or dept_data)
                        updated_count += 1
                    else:
                        skipped_count += 1

                synced_count += 1

            # Cập nhật quan hệ cha con cho tất cả departments
            try:
                all_departments = self.search([])
                all_departments._update_parent_relationship()
                # Tính toán lại parent store
                self._compute_parent_store()
                _logger.info("Parent relationships updated successfully")
            except Exception as e:
                _logger.error("Failed to update parent relationships: %s", str(e))

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.admindepts_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.admindepts_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.admindepts_last_sync', fields.Datetime.now())

            _logger.info("AdminDepts Sync: Created %d, Updated %d, Skipped %d, Total %d",
                        created_count, updated_count, skipped_count, synced_count)

            return synced_count
        else:
            # Lỗi khác
            error_msg = result.get("message", "Unknown error")
            _logger.error("Failed to sync admindepts from YonSuite: %s", error_msg)
            return 0

    def _prepare_department_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu department từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'name': api_data.get("name"),
            'innercode': api_data.get("innercode"),
            'parent': api_data.get("parent"),
            'parentid': api_data.get("parentid"),
            'path': api_data.get("path"),
            'level': api_data.get("level", 1),
            'orgid': api_data.get("orgid"),
            'orgtype': api_data.get("orgtype", 1),
            'isbizunit': api_data.get("isbizunit", False),
            'isdefault': api_data.get("isdefault", False),
            'canEmployee': api_data.get("canEmployee", True),
            'externalorg': api_data.get("externalorg", False),
            'taxpayername': api_data.get("taxpayername"),
            'taxpayerid': api_data.get("taxpayerid"),
            'taxpayertype': api_data.get("taxpayertype", 1),
            'companytype': api_data.get("companytype"),
            'enable': api_data.get("enable", True),
            'frozen': api_data.get("frozen", False),
            'closed': api_data.get("closed", False),
            'dr': api_data.get("dr", 0),
            'sort': api_data.get("sort", 0),
            'displayorder': api_data.get("displayorder", 0),
            'globalorder': api_data.get("globalorder", 0),
            'creator': api_data.get("creator"),
            'modifier': api_data.get("modifier"),
            'tenantid': api_data.get("tenantid"),
            'tenant': api_data.get("tenant"),
            'ytenant': api_data.get("ytenant"),
            'sysid': api_data.get("sysid"),
            'sourceid': api_data.get("sourceid"),
            'sourcetype': api_data.get("sourcetype", 1),
            'exchangerate': api_data.get("exchangerate"),
            'countryzone': api_data.get("countryzone"),
            'language': api_data.get("language"),
            # Thông tin chi tiết từ API detail
            'parent_name': api_data.get("parent_name"),
            'parent_code': api_data.get("parent_code"),
            'parentorgid': api_data.get("parentorgid"),
            'parentorgid_name': api_data.get("parentorgid_name"),
            'bizorgid': api_data.get("bizorgid"),
            'bizorgid_name': api_data.get("bizorgid_name"),
            'principal': api_data.get("principal"),
            'principal_name': api_data.get("principal_name"),
            'creator_userName': api_data.get("creator_userName"),
            'modifier_userName': api_data.get("modifier_userName"),
            'is_biz_unit': api_data.get("is_biz_unit", False),
            'isEnd': api_data.get("isEnd", False),
            'description': api_data.get("description"),
            'deptOrgExt_id': api_data.get("deptOrgExt", {}).get("id") if api_data.get("deptOrgExt") else False,
            '_mddFormulaExecuteFlag': api_data.get("_mddFormulaExecuteFlag"),
        }

        # Xử lý multi-language fields
        if api_data.get("shortname"):
            shortname_data = api_data.get("shortname", {})
            vals.update({
                'shortname_zh_CN': shortname_data.get("zh_CN"),
                'shortname_vi_VN': shortname_data.get("vi_VN"),
                'shortname_en_US': shortname_data.get("en_US"),
            })

        if api_data.get("name") and isinstance(api_data.get("name"), dict):
            name_data = api_data.get("name", {})
            vals.update({
                'name_zh_CN': name_data.get("zh_CN"),
                'name_vi_VN': name_data.get("vi_VN"),
                'name_en_US': name_data.get("en_US"),
            })
            # Nếu name là dict, lấy name_vi_VN làm name chính
            if name_data.get("vi_VN"):
                vals['name'] = name_data.get("vi_VN")

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

        if api_data.get("ts"):
            converted_datetime = api_service._convert_datetime_string(api_data["ts"])
            if converted_datetime:
                vals['ts'] = converted_datetime

        if api_data.get("endtime"):
            converted_datetime = api_service._convert_datetime_string(api_data["endtime"])
            if converted_datetime:
                vals['endtime'] = converted_datetime

        return vals

    def _update_parent_relationship(self):
        """
        Cập nhật quan hệ cha con dựa trên parentorgid
        """
        for record in self:
            try:
                if record.parentorgid:
                    # Tìm parent department dựa trên parentorgid
                    parent_dept = self.search([('orgid', '=', record.parentorgid)], limit=1)
                    if parent_dept and parent_dept.id != record.id:
                        record.with_context(parent_store_compute=False).write({'parent_id': parent_dept.id})
                    else:
                        record.with_context(parent_store_compute=False).write({'parent_id': False})
                else:
                    record.with_context(parent_store_compute=False).write({'parent_id': False})
            except Exception as e:
                _logger.warning("Failed to update parent relationship for department %s: %s", record.name, str(e))
                continue

    def _compute_parent_store(self):
        """
        Tính toán lại parent store fields một cách an toàn
        """
        try:
            self.env.cr.execute("""
                UPDATE yonsuite_admindept 
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
