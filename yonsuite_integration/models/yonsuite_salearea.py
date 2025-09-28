# -*- coding: utf-8 -*-
import logging


from odoo import models, fields, api, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class YonsuiteSalearea(models.Model):
    _name = 'yonsuite.salearea'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'YonSuite Sale Area'
    _order = 'create_date desc'

    # Thông tin cơ bản
    yonsuite_id = fields.Char(
        string='YonSuite ID',
        readonly=True,
        copy=False,
        help='Sale Area ID from YonSuite API',
    )

    code = fields.Char(
        string='Sale Area Code',
        help='Sale area code from YonSuite'
    )

    name = fields.Char(
        string='Sale Area Name',
        required=True,
        help='Sale area name'
    )

    simplified_name = fields.Char(
        string='Simplified Name',
        help='Simplified name from YonSuite'
    )

    # Thông tin tổ chức
    orgId = fields.Char(
        string='Organization ID',
        compute='_compute_orgId',
        store=True,
        help='Organization ID from YonSuite'
    )

    orgunit_id = fields.Many2one(
        'yonsuite.orgunit',
        string='Organization Unit',
        help='Related organization unit'
    )

    level = fields.Integer(
        string='Level',
        default=1,
        help='Sale area level'
    )

    path = fields.Char(
        string='Path',
        readonly=True,
        help='Sale area path',
        copy=False,
    )

    remark = fields.Text(
        string='Remark',
        readonly=True,
        help='Remark from YonSuite'
    )

    stopStatus = fields.Boolean(
        string='Stop Status',
        default=False,
        help='Stop status'
    )

    # Computed field for orgId
    @api.depends('orgunit_id')
    def _compute_orgId(self):
        for record in self:
            if record.orgunit_id and record.orgunit_id.orgid:
                record.orgId = record.orgunit_id.orgid
            # If no orgunit_id or orgunit doesn't have orgid, keep the current value

    # Trạng thái đồng bộ
    state = fields.Selection([
        ('draft', 'Draft'),
        ('synced', 'Synced with YonSuite'),
        ('error', 'Sync Error')
    ], string='Status', default='draft', tracking=True,
        copy=False,)

    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Last time this sale area was synchronized with YonSuite',
        copy=False,
    )

    sync_error_message = fields.Text(
        string='Sync Error Message',
        readonly=True,
        help='Error message from last synchronization attempt',
        copy=False,
    )

    def action_export_to_yonsuite(self):
        """
        Push sale area data to YonSuite API
        """
        self.ensure_one()

        # Validate required fields
        if not self.code:
            raise UserError(_('Code field is required before pushing to YonSuite'))
        if not self.orgId:
            raise UserError(_('Organization ID field is required before pushing to YonSuite'))

        # Prepare data for pushing to YonSuite
        vals = self._prepare_salearea_data_push_to_yonsuite()

        # Call API to push sale area data
        api_service = self.env['yonsuite.api']
        result = api_service.push_saleareas_to_api(vals)

        if result.get("code") == "200":
            # Update the record with success status
            self.write({
                'state': 'synced',
                'last_sync_date': fields.Datetime.now(),
                'sync_error_message': False
            })

            # If API returns the created record with ID, update yonsuite_id
            if result.get("data") and isinstance(result.get("data"), dict):
                yonsuite_id = result.get("data").get("id")
                if yonsuite_id:
                    self.write({'yonsuite_id': str(yonsuite_id)})
        else:
            error_msg = result.get("message", "Unknown error")
            self.write({
                'state': 'error',
                'sync_error_message': error_msg
            })
            raise UserError(_('YonSuite API Error: %s') % error_msg)

    def _prepare_salearea_data_push_to_yonsuite(self):
        """
        Prepare sale area data for pushing to YonSuite API
        """
        self.ensure_one()

        return {
            "data": {
                "code": self.code,
                "orgCode": self.orgunit_id.code,
                "level": self.level or 1,
                "name": {
                    "simplifiedName": self.name
                },
                "stopStatus": self.stopStatus
            }
        }

    def _update_salearea_from_api_data(self, api_data):
        """
        Cập nhật dữ liệu sale area từ API response
        """
        # Sử dụng method local để chuẩn bị dữ liệu
        vals = self._prepare_salearea_data_from_api(api_data)
        vals.update({
            'state': 'synced',
            'last_sync_date': fields.Datetime.now(),
            'sync_error_message': False,
        })
        self.write(vals)

    def action_reset_to_draft(self):
        """
        Reset sale area to draft state
        """
        self.ensure_one()
        self.write({
            'state': 'draft',
            'last_sync_date': False,
            'sync_error_message': False
        })

    @api.model
    def action_import_saleareas_pagination(self):
        """
        Sync sale areas từ YonSuite API và lưu vào database
        """
        config_parameter = self.env['ir.config_parameter'].sudo()

        # Gọi API để lấy dữ liệu sale areas
        api_service = self.env['yonsuite.api']
        result = api_service.get_saleareas_from_api()

        if result.get("code") == "200":
            saleareas_data = result.get("data", [])

            if not saleareas_data:
                _logger.info("No sale areas data received")
                return 0

            # Lấy tất cả yonsuite_id từ API response
            api_yonsuite_ids = [str(area_data.get("id")) for area_data in saleareas_data]

            # Search một lần duy nhất tất cả sale areas đã tồn tại
            existing_saleareas = self.search([('yonsuite_id', 'in', api_yonsuite_ids)])
            existing_saleareas_dict = {p.yonsuite_id: p for p in existing_saleareas}

            # Lưu sale areas vào database
            synced_count = 0
            created_count = 0
            updated_count = 0
            skipped_count = 0

            for area_data in saleareas_data:
                yonsuite_id = str(area_data.get("id"))
                salearea = existing_saleareas_dict.get(yonsuite_id)

                if not salearea:
                    # Tạo sale area mới với đầy đủ dữ liệu
                    vals = {
                        'yonsuite_id': yonsuite_id,
                        'name': area_data.get("name", {}).get("simplifiedName") or area_data.get("code"),
                        'state': 'synced',
                        'last_sync_date': fields.Datetime.now(),
                        'sync_error_message': False
                    }

                    # Thêm dữ liệu từ API
                    vals.update(self._prepare_salearea_data_from_api(area_data))

                    salearea = self.create(vals)
                    created_count += 1
                else:
                    # Kiểm tra có thay đổi không (có thể thêm logic kiểm tra timestamp nếu API có)
                    salearea._update_salearea_from_api_data(area_data)
                    updated_count += 1

                synced_count += 1

            # Cập nhật thống kê
            total_synced = int(config_parameter.get_param('yonsuite_integration.saleareas_total_synced', '0'))
            config_parameter.set_param('yonsuite_integration.saleareas_total_synced', str(total_synced + synced_count))
            config_parameter.set_param('yonsuite_integration.saleareas_last_sync', fields.Datetime.now())

            _logger.info("SaleAreas Sync: Created %d, Updated %d, Skipped %d, Total %d",
                         created_count, updated_count, skipped_count, synced_count)

            return synced_count
        else:
            # Lỗi khác
            error_msg = result.get("message", "Unknown error")
            _logger.error("Failed to sync saleareas from YonSuite: %s", error_msg)
            return 0

    def _prepare_salearea_data_from_api(self, api_data):
        """
        Chuẩn bị dữ liệu sale area từ API response
        """
        vals = {
            'code': api_data.get("code"),
            'orgId': api_data.get("orgId"),
            'level': api_data.get("level", 1),
            'path': api_data.get("path"),
            'stopStatus': api_data.get("stopStatus", False),
        }

        # Xử lý name object
        if api_data.get("name"):
            name_data = api_data.get("name", {})
            vals.update({
                'name': name_data.get("simplifiedName") or api_data.get("code"),
                'simplified_name': name_data.get("simplifiedName"),
            })

        # Xử lý remark object
        if api_data.get("remark"):
            remark_data = api_data.get("remark", {})
            # Có thể xử lý thêm các trường trong remark nếu cần
            vals['remark'] = str(remark_data) if remark_data else False

        # Tìm và liên kết với orgunit
        if api_data.get("orgId"):
            orgunit = self.env['yonsuite.orgunit'].search([('orgid', '=', api_data.get("orgId"))], limit=1)
            if orgunit:
                vals['orgunit_id'] = orgunit.id

        return vals
