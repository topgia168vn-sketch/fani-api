import logging

import lark_oapi as lark
from lark_oapi.api.contact.v3 import *

from odoo import models, fields, api
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class LarkContact(models.Model):
    _name = 'lark.contact'
    _description = 'Lark Contact'

    user_id = fields.Char(string='User ID', required=True)
    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    department_ids = fields.Many2many('lark.department', string='Departments')
    avatar_240 = fields.Char(string='Avatar 240x240')
    avatar_640 = fields.Char(string='Avatar 640x640')
    avatar_72 = fields.Char(string='Avatar 72x72')
    avatar_origin = fields.Char(string='Avatar Original')
    city = fields.Char(string='City')
    country = fields.Char(string='Country')
    description = fields.Text(string='Description')
    employee_no = fields.Char(string='Employee Number')
    employee_type = fields.Integer(string='Employee Type')
    en_name = fields.Char(string='English Name')
    enterprise_email = fields.Char(string='Enterprise Email')
    gender = fields.Integer(string='Gender')
    is_tenant_manager = fields.Boolean(string='Is Tenant Manager')
    job_title = fields.Char(string='Job Title')
    join_time = fields.Integer(string='Join Time')
    leader_user_id = fields.Char(string='Leader User ID')
    mobile = fields.Char(string='Mobile')
    mobile_visible = fields.Boolean(string='Mobile Visible')
    open_id = fields.Char(string='Open ID')
    union_id = fields.Char(string='Union ID')
    work_station = fields.Char(string='Work Station')

    @api.model
    def _fetch_contact_list(self, user_id=False):
        if not user_id:
            user_id = self.env.user
        if not user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")

        client = user_id._get_client()
        lark_user_ids = self.env['lark.contact'].search([]).mapped('user_id')
        contacts = []

        department_search = self.env['lark.department'].search_read([('config_id', '=', self.id)], ['open_department_id'])

        department_dict = {}
        dp_lark_ids = []
        for dp_lark in department_search:
            department_dict[dp_lark['open_department_id']] = dp_lark['id']
            dp_lark_ids.append(dp_lark['open_department_id'])

        option = option = lark.RequestOption.builder().user_access_token(user_id.lark_user_access_token).build()
        for dp_lark_id in dp_lark_ids:
            request = FindByDepartmentUserRequest.builder() \
                .user_id_type("open_id") \
                .department_id_type("open_department_id") \
                .department_id(dp_lark_id) \
                .page_size(10) \
                .build()

            time_retry = 0
            while True:
                response = client.contact.v3.user.find_by_department(request, option)
                if not response.success():
                    _logger.error(f"Failed to fetch contacts: {response.code} - {response.msg}")
                    if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error', 'Internal Error'):
                        if time_retry <= 10:
                            time_retry += 1
                            continue
                    raise UserError(f"Failed to fetch contacts: {response.msg}")

                if response.data.items is not None:
                    contacts.extend(response.data.items)
                    time_retry = 0

                if not response.data.has_more:
                    break

                request = FindByDepartmentUserRequest.builder() \
                    .user_id_type("open_id") \
                    .department_id_type("open_department_id") \
                    .department_id(dp_lark_id) \
                    .page_size(10) \
                    .page_token(response.data.page_token) \
                    .build()

        contact_vals = []
        for contact in contacts:
            if contact.user_id in lark_user_ids:
                continue

            lark_user_ids.append(contact.user_id)
            department_ids = [department_dict.get(dept_id) for dept_id in contact.department_ids if dept_id in department_dict]
            contact_vals.append({
                'user_id': contact.user_id,
                'name': contact.name,
                'email': contact.email,
                'department_ids': [(6, 0, department_ids)] if department_ids else [(5, 0, 0)],
                'avatar_240': contact.avatar.avatar_240 if hasattr(contact.avatar, 'avatar_240') else False,
                'avatar_640': contact.avatar.avatar_640 if hasattr(contact.avatar, 'avatar_640') else False,
                'avatar_72': contact.avatar.avatar_72 if hasattr(contact.avatar, 'avatar_72') else False,
                'avatar_origin': contact.avatar.avatar_origin if hasattr(contact.avatar, 'avatar_origin') else False,
                'city': contact.city,
                'country': contact.country,
                'description': contact.description,
                'employee_no': contact.employee_no,
                'employee_type': contact.employee_type,
                'en_name': contact.name,
                'enterprise_email': contact.enterprise_email,
                'gender': contact.gender,
                'is_tenant_manager': contact.is_tenant_manager,
                'job_title': contact.job_title,
                'join_time': contact.join_time,
                'leader_user_id': contact.leader_user_id,
                'mobile': contact.mobile,
                'mobile_visible': contact.mobile_visible,
                'open_id': contact.open_id,
                'union_id': contact.union_id,
                'work_station': contact.work_station,
            })
        if contact_vals:
            self.create(contact_vals)
