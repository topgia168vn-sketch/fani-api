from odoo import models, fields


class LarkPerson(models.Model):
    _name = 'lark.person'
    _description = 'Lark Person'

    lark_person_id = fields.Char('id')
    name = fields.Char('Name')
    en_name = fields.Char('EN Name')
    email = fields.Char('Email')
    avatar_url = fields.Char('Avatar Url')

