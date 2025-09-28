import time
import hashlib
import requests
import json
import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import timedelta
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    # TikTok Business API Configuration Fields
    tiktok_app_id = fields.Char(
        string='TikTok App ID',
        config_parameter='tiktok_business.app_id',
        help='App ID từ TikTok for Developers'
    )
    
    tiktok_client_secret = fields.Char(
        string='TikTok Client Secret',
        config_parameter='tiktok_business.client_secret',
        help='Client Secret từ TikTok for Developers'
    )
