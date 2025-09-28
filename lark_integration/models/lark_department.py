import logging
import logging
from time import sleep
import lark_oapi as lark
from lark_oapi.api.approval.v4 import *

import lark_oapi as lark
from lark_oapi.api.contact.v3 import *

from odoo import models, fields
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class LarkDepartment(models.Model):
    _name = 'lark.department'
    _description = 'Lark Department'

    department_id = fields.Char(string='Department ID', required=True)
    open_department_id = fields.Char(string='Open Department ID')
    name = fields.Char(string='Name', required=True)
    parent_department_id = fields.Char(string='Parent Department ID')

    chat_id = fields.Char("Chat Id")
    leader_user_id = fields.Char("Leader User Id")

    def fetch_department_list(self, user_id=False):
        if not user_id:
            user_id = self.env.user
        if not user_id.lark_user_access_token:
            raise UserError("No App Access Token available.")
        department_ids = self.env['lark.department'].search([]).mapped('department_id')

        client = user_id._get_client()
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        departments = []
        for letter in alphabet:
            text_search = letter
            request: SearchDepartmentRequest = SearchDepartmentRequest.builder() \
                .page_size(10) \
                .request_body(SearchDepartmentRequestBody.builder()
                              .query(text_search)
                              .build()) \
                .build()

            option = lark.RequestOption.builder().user_access_token(user_id.lark_user_access_token).build()
            while True:
                response = client.contact.v3.department.search(request, option)
                if not response.success():
                    _logger.error(f"Failed to fetch departments: {response.code} - {response.msg}")
                    if response.msg in ('Gateway timeout. Please try again later.', 'Internal Server Error'):
                        sleep(3)
                        continue
                    raise UserError(f"Failed to fetch departments: {response.msg}")

                if response.data.items is not None:
                    departments.extend(response.data.items)

                if not response.data.has_more:
                    break

                sleep(3)
                request: SearchDepartmentRequest = SearchDepartmentRequest.builder() \
                    .page_token(response.data.page_token)\
                    .page_size(20) \
                    .request_body(SearchDepartmentRequestBody.builder()
                                  .query(text_search)
                                  .build()) \
                    .build()

        department_vals = []
        for dept in departments:
            if dept.department_id in department_ids:
                continue
            department_ids.append(dept.department_id)
            department_vals.append({
                'department_id': dept.department_id,
                'open_department_id': dept.open_department_id,
                'name': dept.name,
                'parent_department_id': dept.parent_department_id,
                'chat_id': dept.chat_id,
                'leader_user_id': dept.leader_user_id,
            })
        if department_vals:
            self.env['lark.department'].create(department_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Successfully fetched and saved {len(departments)} departments!',
                'type': 'success',
                'sticky': False,
            }
        }
