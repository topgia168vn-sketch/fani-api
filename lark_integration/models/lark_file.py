import logging
from datetime import datetime

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *


from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LarkFile(models.Model):
    _name = 'lark.file'
    _description = 'Lark File'

    name = fields.Char(string='Name', required=True)
    created_time = fields.Datetime(string='Created Time', required=True)
    modified_time = fields.Datetime(string='Modified Time', required=True)
    owner_id = fields.Char(string='Owner ID', required=True)
    parent_token = fields.Char(string='Parent Token')
    token = fields.Char(string='Token', required=True)
    type = fields.Selection([
        ('folder', 'Folder'),
        ('bitable', 'Base'),
        ('docx', 'Doc'),
        ('mindnote', 'Mindnote'),
        ('slides', 'Slides'),
        ('sheet', 'Sheet'),
    ], string='Type', required=True)
    url = fields.Char(string='URL')

    user_id = fields.Many2one('res.users', string='Users', required=True, ondelete='cascade')
    lark_table_ids = fields.One2many('lark.file.bitable.table', 'lark_file_id', "Tables")

    parent_id = fields.Many2one('lark.file', string="Parent", compute='_compute_partent_id', store=True)

    @api.depends('parent_token')
    def _compute_partent_id(self):
        for r in self:
            r.parent_id = self.env['lark.file'].search([('user_id', '=', r.user_id.id), ('token', '=', r.parent_token)])

    def fetch_items_in_this_folder(self):
        self.ensure_one()
        self.fetch_items_in_folder(user_id=self.env.user, folder_token=self.token)

    @api.model
    def fetch_items_in_root_folder(self):
        self.fetch_items_in_folder(self.env.user)

    @api.model
    def fetch_items_in_folder(self, user_id, folder_token=''):
        if not user_id:
            user_id = self.env.user

        if not user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = user_id._get_client()
        option = option = lark.RequestOption.builder().user_access_token(user_id.lark_user_access_token).build()

        if folder_token:
            request = ListFileRequest.builder() \
                .folder_token(folder_token) \
                .page_size(50)\
                .order_by("EditedTime") \
                .direction("DESC") \
                .user_id_type("open_id") \
                .build()
        else:
            request = ListFileRequest.builder() \
                .order_by("EditedTime") \
                .page_size(50)\
                .direction("DESC") \
                .user_id_type("open_id") \
                .build()

        time_retry = 0
        files_data = []
        while True:
            response = client.drive.v1.file.list(request, option)
            if not response.success():
                _logger.error(f"Failed to fetch contacts: {response.code} - {response.msg}")
                if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                    if time_retry <= 10:
                        time_retry += 1
                        continue
                raise UserError(f"Failed to fetch contacts: {response.msg}")

            if response.data.files is not None:
                files_data.extend(response.data.files)
                time_retry = 0

            if not response.data.has_more:
                break

            if folder_token:
                request: ListFileRequest = ListFileRequest.builder() \
                    .folder_token(folder_token) \
                    .page_size(50)\
                    .order_by("EditedTime") \
                    .direction("DESC") \
                    .user_id_type("open_id") \
                    .page_token(response.data.next_page_token) \
                    .build()\

            else:
                request: ListFileRequest = ListFileRequest.builder() \
                    .order_by("EditedTime") \
                    .page_size(50)\
                    .direction("DESC") \
                    .user_id_type("open_id") \
                    .page_token(response.data.next_page_token) \
                    .build()

        exists_token = self.env['lark.file'].search([]).mapped('token')
        file_vals = []
        for file in files_data:
            if file.token in exists_token:
                continue
            file_vals.append({
                'name': file.name,
                'created_time': datetime.fromtimestamp(int(file.created_time)),
                'modified_time': datetime.fromtimestamp(int(file.modified_time)),
                'owner_id': file.owner_id,
                'parent_token': file.parent_token,
                'token': file.token,
                'type': file.type,
                'url': file.url,
                'user_id': user_id.id,
            })
        if file_vals:
            self.env['lark.file'].create(file_vals)

    def fetch_data(self):
        self.ensure_one()
        self._fetch_table()
        for table in self.lark_table_ids:
            table.fetch_data()

    def _fetch_table(self):
        self.ensure_one()
        if not self.user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = self.user_id._get_client()
        option = lark.RequestOption.builder().user_access_token(self.user_id.lark_user_access_token).build()

        request = ListAppTableRequest.builder() \
            .app_token(self.token) \
            .page_size(50) \
            .build()

        time_retry = 0
        tables = []
        while True:
            response = client.bitable.v1.app_table.list(request, option)

            if not response.success():
                _logger.error(f"Failed to fetch table: {response.code} - {response.msg}")
                if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                    if time_retry <= 10:
                        time_retry += 1
                        continue
                raise UserError(f"Failed to fetch table: {response.msg}")

            if response.data.items is not None:
                tables.extend(response.data.items)
                time_retry = 0

            if not response.data.has_more:
                break
            request = ListAppTableRequest.builder() \
                .app_token(self.token) \
                .page_size(50) \
                .page_token(response.data.page_token) \
                .build()

        table_vals = []
        exists_tables = self.env['lark.file.bitable.table'].search([('lark_file_id', '=', self.id)])
        exists_table_ids = {t.table_id: t for t in exists_tables}
        for table in tables:
            exists_table = exists_table_ids.get(table.table_id, False)
            if exists_table:
                # revision không hoạt động khi đổi tên bảng
                exists_table.write({
                    'name': table.name,
                    'revision': table.revision,
                })
            else:
                table_vals.append({
                    'name': table.name,
                    'revision': table.revision,
                    'table_id': table.table_id,
                    'lark_file_id': self.id,
                })
        if table_vals:
            self.env['lark.file.bitable.table'].create(table_vals)
        self.env.cr.commit()
