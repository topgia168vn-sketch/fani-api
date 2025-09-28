from odoo import models, fields


class LarkAppTableRecord(models.Model):
    _name = 'lark.app.table.record'
    _description = 'Lark App Table Record'
    _rec_name = 'record_id'

    fields_json = fields.Json(string='Fields')
    record_id = fields.Char(string='Record Id', required=True)
    created_by = fields.Many2one('lark.person', "Create By")
    created_time = fields.Datetime("Create Time")
    last_modified_by = fields.Many2one('lark.person', "Last Modified By")
    last_modified_time = fields.Datetime("Last Modified Time")
    shared_url = fields.Char("Shared Url")
    record_url = fields.Char("Record Url")

    lark_table_id = fields.Many2one('lark.file.bitable.table', "Lark Table")
    lark_view_id = fields.Many2one('lark.file.bitable.table.view', "Lark View")

