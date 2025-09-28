from odoo import models, fields, api

class LarkApproval(models.Model):
    _name = 'lark.approval'
    _description = 'Lark Approval Definition'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    approval_code = fields.Char(string='Approval Code')
    approval_name = fields.Char(string='Approval Name')
    status = fields.Char(string='Status')
