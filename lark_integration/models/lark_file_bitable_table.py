import logging
import json
from datetime import datetime

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.drive.v1 import *

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class LarkFile(models.Model):
    _name = 'lark.file.bitable.table'
    _description = 'Lark File Bitable Table'

    name = fields.Char(string='Name', required=True)
    revision = fields.Integer(string='Revision')
    table_id = fields.Char(string='Table Id')

    lark_file_id = fields.Many2one('lark.file', "Lark File")
    user_id = fields.Many2one(related='lark_file_id.user_id')

    lark_view_ids = fields.One2many('lark.file.bitable.table.view', 'lark_table_id', string="Lark Views")
    lark_field_ids = fields.One2many('lark.file.bitable.table.field', 'lark_table_id', string="Lark Fields")
    lark_record_ids = fields.One2many('lark.app.table.record', 'lark_table_id', string="Lark Records")

    def fetch_data(self):
        self.ensure_one()
        self._fetch_views()
        self._fetch_fields()
        self._fetch_records()

    def _fetch_views(self):
        self.ensure_one()
        if not self.user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = self.user_id._get_client()
        option = lark.RequestOption.builder().user_access_token(self.user_id.lark_user_access_token).build()

        request: ListAppTableViewRequest = ListAppTableViewRequest.builder() \
            .app_token(self.lark_file_id.token) \
            .table_id(self.table_id) \
            .page_size(50) \
            .build()

        time_retry = 0
        lark_views = []
        while True:
            response = client.bitable.v1.app_table_view.list(request, option)

            if not response.success():
                _logger.error(f"Failed to fetch Views: {response.code} - {response.msg}")
                if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                    if time_retry <= 10:
                        time_retry += 1
                        continue
                raise UserError(f"Failed to fetch Views: {response.msg}")

            if response.data.items is not None:
                lark_views.extend(response.data.items)
                time_retry = 0

            if not response.data.has_more:
                break
            request: ListAppTableViewRequest = ListAppTableViewRequest.builder() \
                .app_token(self.lark_file_id.token) \
                .table_id(self.table_id) \
                .page_size(50) \
                .page_token(response.data.page_token) \
                .build()

        view_vals = []
        exists_views = self.env['lark.file.bitable.table.view'].search([('lark_table_id', '=', self.id)])
        exists_views_ids = {v.view_id: v for v in exists_views}
        for view in lark_views:
            exists_view = exists_views_ids.get(view.view_id, False)
            if exists_view:
                exists_view.write({
                    'view_name': view.view_name,
                    'view_public_level': view.view_public_level,
                    'view_type': view.view_type,
                })
            else:
                view_vals.append({
                    'view_id': view.view_id,
                    'view_name': view.view_name,
                    'view_public_level': view.view_public_level,
                    'view_type': view.view_type,
                    'lark_table_id': self.id,
                })
        if view_vals:
            self.env['lark.file.bitable.table.view'].create(view_vals)
        self.env.cr.commit()

    def _fetch_fields(self):
        self.ensure_one()
        if not self.user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = self.user_id._get_client()
        option = lark.RequestOption.builder().user_access_token(self.user_id.lark_user_access_token).build()

        request = ListAppTableFieldRequest.builder() \
            .app_token(self.lark_file_id.token) \
            .table_id(self.table_id) \
            .page_size(50) \
            .build()

        time_retry = 0
        lark_fields = []
        while True:
            response = client.bitable.v1.app_table_field.list(request, option)

            if not response.success():
                _logger.error(f"Failed to fetch Views: {response.code} - {response.msg}")
                if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                    if time_retry <= 10:
                        time_retry += 1
                        continue
                raise UserError(f"Failed to fetch Views: {response.msg}")

            if response.data.items is not None:
                lark_fields.extend(response.data.items)
                time_retry = 0

            if not response.data.has_more:
                break
            request = ListAppTableFieldRequest.builder() \
                .app_token(self.lark_file_id.token) \
                .table_id(self.table_id) \
                .page_size(50) \
                .page_token(response.data.page_token) \
                .build()

        field_vals = []
        exists_fields = self.env['lark.file.bitable.table.field'].search([('lark_table_id', '=', self.id)])
        exists_field_ids = {f.field_id: f for f in exists_fields}
        for field in lark_fields:
            options = field.property.options if field.property else []
            if not options:
                options = []
            option_vals = [{
                'option_id': opt.id,
                'name': opt.name,
                'color': opt.color,
            } for opt in options]
            val = {
                'field_name': field.field_name,
                'is_primary': field.is_primary,
                'type': field.type,
                'option_ids': [(0, 0, opt) for opt in option_vals],
            }
            if field.property:
                val.update({
                    'formatter': field.property.formatter,
                    'date_formatter': field.property.date_formatter,
                    'auto_fill': field.property.auto_fill,
                    'multiple': field.property.multiple,
                    'table_id': field.property.table_id,
                    'table_name': field.property.table_name,
                    'back_field_name': field.property.back_field_name,
                    'auto_serial': field.property.auto_serial if field.property.auto_serial else False,
                    'location': field.property.location if field.property.location else False,
                    'formula_expression': field.property.formula_expression,
                    'allowed_edit_modes': field.property.allowed_edit_modes,
                    'min_value': field.property.min,
                    'max_value': field.property.max,
                    'range_customize': field.property.range_customize,
                    'currency_code': field.property.currency_code,
                    'rating': field.property.rating if field.property.rating else False,
                    'filter_info': field.property.filter_info,
                })
            exists_field = exists_field_ids.get(field.field_id, False)
            if exists_field:
                exists_field.write(val)
            else:
                val.update({
                    'lark_table_id': self.id,
                    'field_id': field.field_id,
                })
                field_vals.append(val)
        if field_vals:
            self.env['lark.file.bitable.table.field'].create(field_vals)
        self.env.cr.commit()

    def _fetch_records(self):
        self.ensure_one()
        if not self.user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = self.user_id._get_client()
        option = lark.RequestOption.builder().user_access_token(self.user_id.lark_user_access_token).build()

        # Only fech Grid view
        for lark_view in self.lark_view_ids.filtered(lambda v: v.view_type == 'grid'):
            request = ListAppTableRecordRequest.builder() \
                .app_token(self.lark_file_id.token) \
                .table_id(self.table_id) \
                .page_size(50) \
                .view_id(lark_view.view_id)\
                .build()
            time_retry = 0
            lark_records = []
            while True:
                lark_record_ids = []
                response = client.bitable.v1.app_table_record.list(request, option)

                if not response.success():
                    _logger.error(f"Failed to fetch Records: {response.code} - {response.msg}")
                    if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                        if time_retry <= 10:
                            time_retry += 1
                            continue
                    raise UserError(f"Failed to fetch Records: {response.msg}")

                if response.data.items is not None:
                    for item in response.data.items:
                        lark_record_ids.append(item.record_id)

                    batch_request = BatchGetAppTableRecordRequest.builder() \
                        .app_token(self.lark_file_id.token) \
                        .table_id(self.table_id) \
                        .request_body(BatchGetAppTableRecordRequestBody.builder()
                                      .record_ids(lark_record_ids)
                                      .user_id_type("open_id")
                                      .with_shared_url(True)
                                      .automatic_fields(True)
                                      .build()) \
                        .build()

                    batch_response = client.bitable.v1.app_table_record.batch_get(batch_request, option)
                    if not batch_response.success():
                        _logger.error(f"Failed to fetch Records: {batch_response.code} - {batch_response.msg}")
                        if batch_response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                            if time_retry <= 10:
                                time_retry += 1
                                continue
                        raise UserError(f"Failed to fetch Records: {batch_response.msg}")
                    if batch_response.data.records is not None:
                        lark_records.extend(batch_response.data.records)
                time_retry = 0

                if not response.data.has_more:
                    break
                request = ListAppTableRecordRequest.builder() \
                    .app_token(self.lark_file_id.token) \
                    .table_id(self.table_id) \
                    .view_id(lark_view.view_id)\
                    .page_size(50) \
                    .page_token(response.data.page_token) \
                    .build()

            record_vals = []
            exists_records = self.env['lark.app.table.record'].search([
                ('lark_table_id', '=', self.id),
                ('lark_view_id', '=', lark_view.id),
            ])
            exists_records_ids = {r.record_id: r for r in exists_records}
            lark_person = self.env['lark.person'].search_read([], ['lark_person_id'])
            lark_person_id = {p['lark_person_id']: p['id'] for p in lark_person}

            for lark_record in lark_records:
                person_create_id = lark_person_id.get(lark_record.created_by.id, False)
                if not person_create_id:
                    person_create_id = self.env['lark.person'].create({
                        'lark_person_id': lark_record.created_by.id,
                        'avatar_url': lark_record.created_by.avatar_url,
                        'email': lark_record.created_by.email,
                        'en_name': lark_record.created_by.en_name,
                        'name': lark_record.created_by.name,
                    }).id
                    lark_person_id[lark_record.created_by.id] = person_create_id
                person_modifile_id = lark_person_id.get(lark_record.last_modified_by.id, False)
                if not person_modifile_id:
                    person_modifile_id = self.env['lark.person'].create({
                        'lark_person_id': lark_record.last_modified_by.id,
                        'avatar_url': lark_record.last_modified_by.avatar_url,
                        'email': lark_record.last_modified_by.email,
                        'en_name': lark_record.last_modified_by.en_name,
                        'name': lark_record.last_modified_by.name,
                    }).id
                    lark_person_id[lark_record.last_modified_by.id] = person_modifile_id

                val = {
                    'fields_json': lark_record.fields,
                    'record_id': lark_record.record_id,
                    'created_by': person_create_id,
                    'created_time': datetime.fromtimestamp(int(lark_record.created_time/1000)),
                    'last_modified_by': person_modifile_id,
                    'last_modified_time': datetime.fromtimestamp(int(lark_record.last_modified_time/1000)),
                    'shared_url': lark_record.shared_url,
                    'lark_table_id': self.id,
                    'lark_view_id': lark_view.id,
                }
                exists_record = exists_records_ids.get(lark_record.record_id, False)
                if exists_record:
                    if exists_record.last_modified_time != val['last_modified_time']:
                        exists_record.write(val)
                else:
                    record_vals.append(val)
            if record_vals:
                self.env['lark.app.table.record'].create(record_vals)
        self.env.cr.commit()

    def action_view_table(self):
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "lark_table_view",
            "name": self.name,
            "params": {
                "table_id": self.id,
            },
        }

    def get_table_data(self):
        self.ensure_one()
        # Determine primary field to display as Name
        primary_field = False
        for f in self.lark_field_ids:
            if f.is_primary:
                primary_field = f.field_name
                break
        fields = [f.field_name for f in self.lark_field_ids]
        fields_no_primary = [f for f in fields if f != primary_field] if primary_field else fields
        out_fields = (['Name'] + fields_no_primary) if primary_field else fields
        rows = []
        for rec in self.lark_record_ids:
            row = {}
            data = rec.fields_json or {}
            # Compute Name from primary field if available
            if primary_field:
                name_val = data.get(primary_field, "")
                if isinstance(name_val, list):
                    name_val = ", ".join([v.get("text", "") for v in name_val])
                row['Name'] = name_val or rec.record_id
            # Fill remaining fields
            for field in fields_no_primary if primary_field else fields:
                val = data.get(field, "")
                if isinstance(val, list):
                    val = ", ".join([v.get("text", "") for v in val])
                row[field] = val
            row['record_id'] = rec.record_id
            rows.append(row)
        return {
            "fields": out_fields,
            "rows": rows,
        }
