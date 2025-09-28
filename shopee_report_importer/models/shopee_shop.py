# -*- coding: utf-8 -*-

import json
import os
import base64
import shutil
from odoo import models, fields, api
from odoo.tools import config
from odoo.exceptions import UserError


class ShopeeShop(models.Model):
    _name = 'shopee.shop'
    _description = 'Shopee Shop'
    _order = 'name'

    name = fields.Char(
        string='Shop Name',
        required=True,
        help='Tên shop trên Shopee'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # Headers text field - format: SPC_SI=xxx; SPC_F=yyy; CTOKEN=zzz
    headers_text = fields.Text(
        string='Headers Text',
        help='Headers/cookies dạng text. Format: SPC_SI=xxx; SPC_F=yyy; CTOKEN=zzz'
    )

    # Binary field để lưu file cookies JSON
    cookies_file = fields.Binary(
        string='Cookies File',
        help='File cookies JSON được tạo từ headers text'
    )
    cookies_filename = fields.Char(
        string='Cookies Filename',
        default='cookies_shopee.json'
    )
    cookie_file_path = fields.Char(
        string='Cookie File Path',
        compute='_compute_cookie_file_path',
        store=True,
        help='Đường dẫn đến file cookies để chạy scripts'
    )

    # Workspace path for scripts
    workspace_path = fields.Char(
        string='Workspace Path',
        readonly=True,
        help='Đường dẫn workspace cho scripts (tạo bởi Deploy Workspace)'
    )

    # Workspace deployment status
    workspace_deployed = fields.Boolean(
        string='Workspace Deployed',
        compute='_compute_workspace_deployed',
        help='Kiểm tra workspace đã được deploy chưa'
    )

    # Thông tin khác
    last_sync_date = fields.Datetime(
        string='Last Sync Date',
        readonly=True,
        help='Lần đồng bộ cuối cùng'
    )

    # Last run log from workspace
    last_run_log = fields.Text(
        string='Last Run Log',
        compute='_compute_last_run_log',
        help='Log từ lần chạy cuối cùng trong workspace'
    )

    @api.depends('cookies_file')
    def _compute_cookie_file_path(self):
        """Compute file path từ attachment"""
        for shop in self:
            if shop.cookies_file:
                attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', 'shopee.shop'),
                    ('res_id', '=', shop.id),
                    ('res_field', '=', 'cookies_file')
                ], limit=1)

                if attachment and attachment.store_fname:
                    filestore_path = config.filestore(self.env.cr.dbname)
                    shop.cookie_file_path = os.path.join(filestore_path, attachment.store_fname)
                else:
                    shop.cookie_file_path = None
            else:
                shop.cookie_file_path = None

    @api.depends('workspace_path')
    def _compute_workspace_deployed(self):
        """Compute workspace deployment status"""
        for shop in self:
            if shop.workspace_path and os.path.exists(shop.workspace_path):
                # Check if essential files exist
                cookies_file = os.path.join(shop.workspace_path, 'cookies_shopee.json')
                shell_script = os.path.join(shop.workspace_path, 'run_shopee_scripts.sh')

                shop.workspace_deployed = (
                    os.path.exists(cookies_file) and
                    os.path.exists(shell_script)
                )
            else:
                shop.workspace_deployed = False

    @api.depends('workspace_path')
    def _compute_last_run_log(self):
        """Compute last run log from workspace"""
        for shop in self:
            if shop.workspace_path and os.path.exists(shop.workspace_path):
                log_file = os.path.join(shop.workspace_path, 'shopee_scripts.log')
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            shop.last_run_log = f.read()
                    except Exception:
                        shop.last_run_log = "Error reading log file"
                else:
                    shop.last_run_log = "No log file found"
            else:
                shop.last_run_log = "Workspace not deployed"

    def _parse_headers_to_cookies(self, headers_text):
        """Parse headers text thành cookies list (giống TH.py)"""
        if not headers_text:
            return []

        cookies = []
        for part in headers_text.split(";"):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            cookies.append({
                "name": k.strip(),
                "value": v.strip(),
                "domain": ".shopee.vn",
                "path": "/",
                "secure": True
            })
        return cookies

    def action_generate_cookies_file(self):
        """Tạo file cookies từ headers text"""
        self.ensure_one()
        if not self.headers_text:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'Vui lòng nhập headers text trước!',
                    'type': 'danger',
                }
            }

        cookies = self._parse_headers_to_cookies(self.headers_text)
        cookies_json = json.dumps(cookies, ensure_ascii=False, indent=2)

        # Lưu vào binary field
        virtual_content = cookies_json.encode('utf-8')
        self.cookies_file = base64.b64encode(virtual_content)
        self.cookies_filename = 'cookies_shopee.json'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Tạo file cookies thành công!',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_download_cookies_file(self):
        """Download cookies file"""
        self.ensure_one()
        if not self.cookies_file:
            raise UserError('Cookies file is required!')

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/shopee.shop/{self.id}/cookies_file/{self.cookies_filename}?download=1',
            'target': 'new',
        }

    def action_deploy_workspace(self):
        """Deploy workspace for this shop"""
        self.ensure_one()
        if not self.cookies_file:
            raise UserError('Cookies file is required!')

        # Get filestore directory
        filestore_path = config.filestore(self.env.cr.dbname)
        shopee_scripts_dir = os.path.join(filestore_path, 'shopee_scripts')
        shop_workspace_dir = os.path.join(shopee_scripts_dir, f'shop_{self.id}')

        # Create directories
        self._create_workspace(shop_workspace_dir, self.cookies_file)

        # Update workspace path
        self.workspace_path = shop_workspace_dir

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Workspace deployed successfully!\nPath: {shop_workspace_dir}',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _create_workspace(self, workspace_path, cookies_file):
        """Create workspace for this shop"""
        # Create directories
        os.makedirs(workspace_path, exist_ok=True)

        # Copy cookies file
        cookies_content = base64.b64decode(cookies_file)
        cookies_path = os.path.join(workspace_path, 'cookies_shopee.json')
        with open(cookies_path, 'wb') as f:
            f.write(cookies_content)

        # Copy Python scripts
        current_dir = os.path.dirname(os.path.abspath(__file__))
        scripts_dir = os.path.join(current_dir, '..', 'scripts')
        scripts = [
            'ads_cpc.py', 'ads_live_local.py', 'booking_local.py',
            'laban_local.py', 'live_product.py', 'order_local.py', 'video_product.py',
            'run_shopee_scripts.sh'
        ]

        for script in scripts:
            source_path = os.path.join(scripts_dir, script)
            dest_path = os.path.join(workspace_path, script)
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                # Make shell script executable
                if script.endswith('.sh'):
                    os.chmod(dest_path, 0o755)

    def action_undeploy_workspace(self):
        """Undeploy workspace for this shop"""
        self.ensure_one()
        if not self.workspace_path:
            raise UserError('Workspace has not been deployed!')

        # Remove workspace directory
        self._delete_workspace(self.workspace_path)

        # Clear workspace path
        self.workspace_path = None

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Workspace undeployed successfully!',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _delete_workspace(self, workspace_path):
        """Delete workspace directory"""
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path)

    def action_redeploy_workspace(self):
        """Redeploy workspace for this shop"""
        self.ensure_one()
        if not self.workspace_path:
            raise UserError('Workspace has not been deployed!')
        self._create_workspace(self.workspace_path, self.cookies_file)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Workspace redeployed successfully!',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_import_downloaded_data(self):
        self.ensure_one()
        if not self.workspace_path:
            raise UserError('Workspace has not been deployed!')
        total_imported = self.env['shopee.report.mixin']._import_workspace_downloaded_data({
            'shop_id': self.id,
            'workspace_path': self.workspace_path
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Imported {total_imported} records successfully!',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def unlink(self):
        """Override unlink method to undeploy workspace"""
        workspace_paths = self.mapped('workspace_path')
        res = super(ShopeeShop, self).unlink()
        for workspace_path in workspace_paths:
            self._delete_workspace(workspace_path)
        return res
