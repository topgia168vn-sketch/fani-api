from datetime import timedelta, datetime, date, timezone
import time
import hashlib
import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

JST_API_URL = "https://asiaopenapi.jsterp.com"

class JstUser(models.Model):
    _name = 'jst.user'
    _description = 'JST User'
    _rec_name = 'userName'

    userName = fields.Char("User Name")
    userId = fields.Char("User ID")
    isAdmin = fields.Boolean("Is Admin")


    def action_sync_jst_users(self):
        """
        Sync JST Users
        Solution:
            1. Query all user ids from jst_sale_order table
                - by column 'salesman'
                - where salesman is not empty
            2. Call API /api/User/GetUsers with params:
                - userIds: list of user ids
            3. Get data from API
            4. Create/Update users
        """
        # 1. Query all user ids from jst_sale_order table
        self.env.cr.execute("SELECT DISTINCT salesman FROM jst_sale_order WHERE salesman IS NOT NULL")
        user_data = self.env.cr.fetchall()
        user_ids = [user_id[0] for user_id in user_data if user_id[0]]
        # 2. Call API /api/User/GetUsers with params:
        body_data = {
            "userIds": user_ids
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/Global/GetByUserId", body_data)
        if resp_data.get('success'):
            data_list = resp_data.get('data') or []


            synced_users = self.env['jst.user'].search([])
            synced_user_ids = synced_users.mapped('userId')
            
            new_vals_list = []
            for data in data_list:

                if data.get('userId') in synced_user_ids:
                    user = synced_users.filtered(lambda r: r.userId == data.get('userId'))
                    user.write(data)
                else:
                    new_vals_list.append(data)
            if new_vals_list:
                self.env['jst.user'].sudo().create(new_vals_list)
