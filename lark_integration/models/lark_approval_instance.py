from odoo import models, fields, api
import requests
import logging

_logger = logging.getLogger(__name__)


class LarkApprovalInstance(models.Model):
    _name = 'lark.approval.instance'
    _description = 'Lark Approval Instance'

    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    approval_id = fields.Many2one('lark.approval', string='Approval Definition')
    instance_id = fields.Char(string='Instance ID', required=True)
    user_id = fields.Char(string='User ID')
    status = fields.Char(string='Status')
    form_data = fields.Text(string='Form Data')

    def get_instance_details(self):
        """Lấy chi tiết Approval Instance."""
        self.ensure_one()
        user_id = self.user_id
        if not user_id.lark_user_access_token:
            raise Exception("No User Access Token available.")
        url = f'https://open.feishu.cn/open-apis/approval/v4/instances/{self.instance_id}'
        headers = {
            'Authorization': f'Bearer {user_id.lark_user_access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            _logger.info(f"Approval Instance details response: {data}")
            if data.get('code') == 0:
                self.write({
                    'status': data['data'].get('status'),
                    'form_data': str(data['data'].get('form'))
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Approval Instance details retrieved successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            _logger.error(f"Failed to get Approval Instance details: {str(e)}")
            raise Exception(f"Failed to get Approval Instance details: {str(e)}")

    def create_instance(self, approval_code, form_data):
        """Tạo Approval Instance."""
        self.ensure_one()
        user_id = self.user_id
        if not user_id.lark_user_access_token:
            raise Exception("No User Access Token available.")
        url = 'https://open.feishu.cn/open-apis/approval/v4/instances'
        headers = {
            'Authorization': f'Bearer {user_id.lark_user_access_token}',
            'Content-Type': 'application/json'
        }
        payload = {
            'approval_code': approval_code,
            'user_id': user_id.lark_user_open_id,
            'form': form_data
        }
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            _logger.info(f"Create Approval Instance response: {data}")
            if data.get('code') == 0:
                self.write({
                    'instance_id': data['data']['instance_id'],
                    'status': 'PENDING',
                    'form_data': form_data
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Approval Instance created successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            _logger.error(f"Failed to create Approval Instance: {str(e)}")
            raise Exception(f"Failed to create Approval Instance: {str(e)}")

    def cancel_instance(self):
        """Hủy Approval Instance."""
        self.ensure_one()
        user_id = self.user_id
        if not user_id.lark_user_access_token:
            raise Exception("No User Access Token available.")
        url = f'https://open.feishu.cn/open-apis/approval/v4/instances/{self.instance_id}/cancel'
        headers = {
            'Authorization': f'Bearer {user_id.lark_user_access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            _logger.info(f"Cancel Approval Instance response: {data}")
            if data.get('code') == 0:
                self.write({'status': 'CANCELED'})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Approval Instance canceled successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            _logger.error(f"Failed to cancel Approval Instance: {str(e)}")
            raise Exception(f"Failed to cancel Approval Instance: {str(e)}")

    def fetch_instance_list(self):
        """Lấy danh sách Approval Instances."""
        self.ensure_one()
        user_id = self.user_id
        if not user_id.lark_user_access_token:
            raise Exception("No User Access Token available.")
        url = 'https://open.feishu.cn/open-apis/approval/v4/instances'
        headers = {
            'Authorization': f'Bearer {user_id.lark_user_access_token}',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            _logger.info(f"Approval Instances response: {data}")
            if data.get('code') == 0:
                # Xóa các instance cũ
                self.search([('user_id', '=', user_id.id)]).unlink()
                # Tạo mới instances
                for instance in data['data']['instance_list']:
                    approval = self.env['lark.approval'].search([('user_id', '=', user_id.id), ('approval_code', '=', instance.get('approval_code'))], limit=1)
                    self.create({
                        'user_id': user_id.id,
                        'approval_id': approval.id if approval else False,
                        'instance_id': instance.get('instance_id'),
                        'user_id': instance.get('user_id'),
                        'status': instance.get('status'),
                        'form_data': str(instance.get('form'))
                    })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': 'Approval Instances retrieved successfully!',
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise Exception(data.get('msg', 'Unknown error'))
        except requests.RequestException as e:
            _logger.error(f"Failed to fetch Approval Instances: {str(e)}")
            raise Exception(f"Failed to fetch Approval Instances: {str(e)}")
