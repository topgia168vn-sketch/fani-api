from odoo import models, fields


class LarkFileBitableTableField(models.Model):
    _name = 'lark.file.bitable.table.field'
    _description = 'Lark File Bitable Table Field'
    _rec_name = 'field_name'

    field_name = fields.Char(string='Field Name')
    field_id = fields.Char(string='Field Id')
    is_primary = fields.Boolean(string='Is Primary')
    type = fields.Integer(string='Type')

    # Property
    option_ids = fields.One2many('lark.file.bitable.table.field.option', 'field_id', string="Field Options")
    formatter = fields.Char(string='Formatter')
    date_formatter = fields.Char(string='Date Formatter')
    auto_fill = fields.Boolean(string='Auto Fill')
    multiple = fields.Boolean(string='Multiple')
    table_id = fields.Char(string='Table Id')
    table_name = fields.Char(string='Table Name')
    back_field_name = fields.Char(string='Back Field Name')
    auto_serial = fields.Selection([
        ('none', 'None'),
        ('serial', 'Serial'),
        # Add other options based on AppFieldPropertyAutoSerial enum if known
    ], string='Auto Serial', default='none')
    location = fields.Selection([
        ('none', 'None'),
        ('country', 'Country'),
        ('province', 'Province'),
        ('city', 'City'),
        ('district', 'District'),
        # Add other options based on AppFieldPropertyLocation enum if known
    ], string='Location', default='none')
    formula_expression = fields.Char(string='Formula Expression')
    allowed_edit_modes = fields.Integer(string='Allowed Edit Modes')
    min_value = fields.Float(string='Min')
    max_value = fields.Float(string='Max')
    range_customize = fields.Boolean(string='Range Customize')
    currency_code = fields.Char(string='Currency Code')
    rating = fields.Selection([
        ('star', 'Star'),
        ('heart', 'Heart'),
        ('like', 'Like'),
        ('flag', 'Flag'),
    ], string='Rating', default='star')
    filter_info = fields.Text(string='Filter Info')

    lark_table_id = fields.Many2one('lark.file.bitable.table', string="Lark Table")


class LarkFileBitableTableFieldOption(models.Model):
    _name = 'lark.file.bitable.table.field.option'
    _description = 'Lark File Bitable Table Field Option'

    field_id = fields.Many2one('lark.file.bitable.table.field', string="Field", required=True, ondelete='cascade')
    option_id = fields.Char(string='Option ID')
    name = fields.Char(string='Option Name')
    color = fields.Integer(string='Color')
