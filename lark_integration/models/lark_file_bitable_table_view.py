from odoo import models, fields


class LarkFileBitableTableView(models.Model):
    _name = 'lark.file.bitable.table.view'
    _description = 'Lark File Bitable Table View'
    _rec_name='view_name'

    view_name = fields.Char(string='View Name', required=True)
    view_id = fields.Char(string='View Id', required=True)
    view_public_level = fields.Char(string='View Public Level', required=True)
    view_type = fields.Selection([
        ('form', 'Form'),
        ('grid', 'Grid'),
        ('gantt', 'Gantt'),
        ('kanban', 'Kanban'),
        ('gallery', 'Gallery'),
    ], string='View Type')

    lark_table_id = fields.Many2one('lark.file.bitable.table', "Lark Table")
