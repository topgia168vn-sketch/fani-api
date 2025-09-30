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

WAVE_SHIPPING_DATETIME_FIELDS = ['created']

WAVE_SHIPPING_TO_STRING_FIELDS = ['companyId', 'waveId']



class JstWaveShipping(models.Model):
    _name = 'jst.wave.shipping'
    _description = 'JST Wave Shipping'
    _rec_name = 'waveId'
    _order = 'created desc, waveId desc'


    # fields from jst data
    companyId = fields.Char("Company ID", index=True)
    waveId = fields.Char("Wave ID", index=True)
    status = fields.Char("Status", index=True)
    statusDisplay = fields.Char("Status Display")
    waveType = fields.Char("Wave Type", index=True)
    waveTypeDisplay = fields.Char("Wave Type Display")
    linkCoId = fields.Integer("Link Company ID", index=True)
    linkCompanyName = fields.Char("Link Company Name")
    skuCount = fields.Integer("SKU Count")
    skuQty = fields.Integer("SKU Qty")
    orderQty = fields.Integer("Order Qty")
    created = fields.Datetime("Created", index=True)


    # Fields link to odoo
    # waveItems link to model 'jst.wave.shipping.item'
    odoo_wave_shipping_item_ids = fields.One2many(
        'jst.wave.shipping.item',
        'odoo_wave_shipping_id',
        string='Wave Shipping Items',
        help="Related wave shipping items"
    )
    # waveInouts link to model 'jst.wave.inout'
    odoo_wave_inout_ids = fields.One2many(
        'jst.wave.inout',
        'odoo_wave_shipping_id',
        string='Wave Inouts',
        help="Related inouts"
    )

    odoo_inout_ids = fields.Many2many(
        'jst.stock.inout',
        string='Inouts',
        help="Related inouts",
        index=True,
        compute='_compute_odoo_inout_ids', store=True
    )

    # raw data
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    @api.depends('odoo_wave_inout_ids.odoo_inout_id')
    def _compute_odoo_inout_ids(self):
        """
        Compute odoo inout ids
        """
        for wave in self:
            wave.odoo_inout_ids = [(6, 0, wave.odoo_wave_inout_ids.odoo_inout_id.ids)]

    def _sync_wave_shippings(self, requestModel, pageIndex=1):
        """
        Sync wave shippings from JST API
        docs:
            https://www.showdoc.com.cn/jsterp/11558582060517166
            https://www.showdoc.com.cn/jsterp/11558582134939442
        """
        if not requestModel:
            _logger.info("Sync JST Wave Shipping: Không truyền tham số requestModel")
            return
        start_dt = datetime.now()
        _logger.info("Sync JST Wave Shipping: Bắt đầu đồng bộ wave shippings ...")
        all_waveIds = []
        while True:
            body_data = {
                "requestModel": requestModel,
                "dataPage": {
                    "pageSize": 500,
                    "pageIndex": pageIndex
                }
            }
            resp_data = self.env['res.config.settings']._call_api_jst("/api/wave/GetWaves", body_data)

            if not resp_data.get('success'):
                _logger.error("Sync JST Wave Shipping: Error (Get Wave Shippings): %s", resp_data.get('message'))
                break

            data = resp_data.get('data') or []
            if data:
                # Lấy danh sách waveIds
                waveId_list = [item.get("waveId", 0) for item in data]
                all_waveIds += waveId_list

                # Check dataPage
                dp = resp_data.get('dataPage') or {}
                if dp.get('isLast', True):
                    break
                pageIndex = dp.get('pageIndex', pageIndex) + 1
            else:
                break
        
        total_waveIds = len(all_waveIds)
        _logger.info("Sync JST Wave Shipping: Cần đồng bộ %s wave shippings ...", total_waveIds)
        
        # Đồng bộ chi tiết 200 wave 1 lần đến khi kết thúc
        if all_waveIds:
            while all_waveIds:
                check_dt_start = datetime.now()
                self._sync_wave_shippings_detail(all_waveIds[:200])
                check_dt_end = datetime.now()
                _logger.info("Sync JST Wave Shipping: Đã đồng bộ %s wave shippings -> %s (s)", len(all_waveIds[:200]), (check_dt_end-check_dt_start).total_seconds())
                all_waveIds = all_waveIds[200:] # Bỏ 200 phần tử đầu tiên

        end_dt = datetime.now()
        _logger.info("Sync JST Wave Shipping: Kết thúc đồng bộ wave shippings -> %s wave shippings-> %s (s)", total_waveIds, (end_dt - start_dt).total_seconds())

    def _sync_wave_shippings_detail(self, waveIds):
        """
        Sync wave shippings detail from JST API
        """
        # Tối đa 200 waves 1 lần
        body_data = {
            'waveIds': waveIds,
            'HasWaveItems': True,
            'HasWaveInouts': True,
            'HasWaveInoutItems': True
        }
        resp_data = self.env['res.config.settings']._call_api_jst("/api/wave/GetWaveDetail", body_data)
        
        # Call API không thành công
        if not resp_data.get('success'):
            _logger.error("Sync JST Wave Shipping: Error (Get Wave Shippings Detail): %s", resp_data.get('message'))
            return
        
        data = resp_data.get('data') or []
        if data:
            self._update_wave_shippings(data)
    
    def _update_wave_shippings(self, data):
        """
        Update wave shippings from JST API
        """
        # Lấy danh sách waveIds từ data sync
        wave_ids_incoming = [str(line.get('waveId')) for line in data if line.get('waveId')]

        # Tìm trong DB các wave đã tồn tại (chỉ load id + waveId)
        existing_waves = self.sudo().search_read(
            domain=[('waveId', 'in', wave_ids_incoming)],
            fields=['id', 'waveId']
        )
        existing_waves_map = {o['waveId']: o['id'] for o in existing_waves}

        new_vals_list = []
        update_vals_list = []
        map_fields = self._map_fields()
        item_map_fields = self.env['jst.wave.shipping.item']._map_fields()


        # Lấy danh sách inout ids từ data
        inoutId_list = []
        for line in data:
            waveInouts = line.get('waveInouts', [])
            if waveInouts:  # Check if waveInouts is not None
                for waveInout in waveInouts:
                    waveInout_inoput_id = waveInout.get('inoutId', False)
                    if waveInout_inoput_id:
                        inoutId_list.append(str(waveInout_inoput_id))
        
        existing_inouts = self.env['jst.stock.inout'].sudo().search_read(
            domain=[('inoutId', 'in', inoutId_list)],
            fields=['id', 'inoutId']
        )
        existing_inouts_map = {o['inoutId']: o['id'] for o in existing_inouts}


        # dict_inout_ids_to_sync = {}
        # Duyệt qua data của từng JST Wave Shipping
        for line in data:

            wave_id = line.get('waveId', 0)
            if not wave_id:
                continue
            wave_id_str = str(wave_id)

            jst_wave = {
                'raw_payload': line
            }
            # Map field - value chính của model
            for key, value in line.items():
                field_key = map_fields.get(key)
                if field_key:
                    if field_key in WAVE_SHIPPING_DATETIME_FIELDS:
                        value_dt = datetime.fromtimestamp(value, timezone.utc).replace(tzinfo=None) if value else False
                        jst_wave[field_key] = value_dt
                    elif field_key in WAVE_SHIPPING_TO_STRING_FIELDS:
                        jst_wave[field_key] = str(value)
                    else:
                        jst_wave[field_key] = value

            # Chuẩn hóa key-data của JST Wave Shipping Items
            wave_items_data = []
            for item in line.get('waveItems', []):
                jst_wave_shipping_item = {}
                for key, value in item.items():
                    field_key = item_map_fields.get(key)
                    if field_key:
                        jst_wave_shipping_item[field_key] = value
                if jst_wave_shipping_item:
                    wave_items_data.append(jst_wave_shipping_item)
            
            # Chuẩn hóa key-data của JST Wave Inouts
            wave_inouts_data = []
            waveInouts = line.get('waveInouts', [])
            if waveInouts:  # Check if waveInouts is not None
                for inout in waveInouts:
                    inoutId = inout.get('inoutId')
                    inoutId_str = str(inoutId) if inoutId else False
                    odoo_inout_id = existing_inouts_map.get(inoutId_str, False)
                    wave_inouts_data.append({
                        'odoo_inout_id': odoo_inout_id,
                        'inoutId': inoutId_str if inoutId_str else False,
                        'orderId': str(inout.get('orderId')) if inout.get('orderId') else False
                    })

            # Update wave đã tồn tại
            if wave_id_str in existing_waves_map:
                # wave items (các wave items cũ đã bị xóa)
                jst_wave['odoo_wave_shipping_item_ids'] = [(0, 0, wi) for wi in wave_items_data]
                # wave inouts (các wave inouts cũ đã bị xóa)
                jst_wave['odoo_wave_inout_ids'] = [(0, 0, wi) for wi in wave_inouts_data]
                update_vals_list.append((existing_waves_map[wave_id_str], jst_wave))
            
            # Chưa đồng bộ: tạo mới
            else:
                # wave items (các wave items cũ đã bị xóa)
                jst_wave['odoo_wave_shipping_item_ids'] = [(0, 0, wi) for wi in wave_items_data]
                # wave inouts (các wave inouts cũ đã bị xóa)
                jst_wave['odoo_wave_inout_ids'] = [(0, 0, wi) for wi in wave_inouts_data]
                new_vals_list.append(jst_wave)
        
        # search tất cả wave items và xóa thay vì dùng lệnh (5, 0, 0), giúp giảm update 200 waves từ 50s xuống còn khoảng dưới 5s
        jst_wave_items_remove = self.env['jst.wave.shipping.item'].search([('waveId', 'in', wave_ids_incoming)])
        if jst_wave_items_remove:
            jst_wave_items_remove.unlink()
        
        # search tất cả wave inouts và xóa thay vì dùng lệnh (5, 0, 0), giúp giảm update 200 waves từ 50s xuống còn khoảng dưới 5s
        jst_wave_inouts_remove = self.env['jst.wave.inout'].search([('waveId', 'in', wave_ids_incoming)])
        if jst_wave_inouts_remove:
            jst_wave_inouts_remove.unlink()
        
        with self.env.cr.savepoint():
            # Create new waves
            if new_vals_list:
                self.sudo().create(new_vals_list)
            # Update waves
            for wave_id, vals in update_vals_list:
                wave = self.browse(wave_id)
                wave.sudo().write(vals)


    def _map_fields(self):
        """
        Map fields from JST API to Odoo fields
        """
        return {
            'companyId': 'companyId',
            'waveId': 'waveId',
            'status': 'status',
            'statusDisplay': 'statusDisplay',
            'waveType': 'waveType',
            'waveTypeDisplay': 'waveTypeDisplay',
            'linkCoId': 'linkCoId',
            'linkCompanyName': 'linkCompanyName',
            'skuCount': 'skuCount',
            'skuQty': 'skuQty',
            'orderQty': 'orderQty',
            'created': 'created',
        }


class JstWaveInout(models.Model):
    _name = 'jst.wave.inout'
    _description = 'JST Wave Inout'

    # fields link to odoo
    odoo_wave_shipping_id = fields.Many2one(
        'jst.wave.shipping',
        string='Wave Shipping',
        help="Related wave shipping",
        index=True,
        ondelete='cascade'
    )
    waveId = fields.Char(related='odoo_wave_shipping_id.waveId', string='Wave ID', store=True, index=True)

    # nếu chưa có phiếu thì tạm thời bỏ qua, cron sẽ chạy để map lại sau
    odoo_inout_id = fields.Many2one(
        'jst.stock.inout',
        string='Inout',
        help="Related inout",
        index=True
    )

    # fields from jst data
    inoutId = fields.Char("Inout ID")
    orderId = fields.Integer("Order ID")


class JstWaveShippingItem(models.Model):
    _name = 'jst.wave.shipping.item'
    _description = 'JST Wave Shipping Item'

    odoo_wave_shipping_id = fields.Many2one(
        'jst.wave.shipping',
        string='Wave Shipping',
        help="Related wave shipping",
        index=True,
        ondelete='cascade'
    )
    waveId = fields.Char(related='odoo_wave_shipping_id.waveId', string='Wave ID', store=True, index=True)

    skuId = fields.Char("SKU ID")
    skuName = fields.Char("SKU Name")
    qty = fields.Integer("Quantity")

    def _map_fields(self):
        """
        Map fields from JST API to Odoo fields
        """
        return {
            'skuId': 'skuId',
            'skuName': 'skuName',
            'qty': 'qty',
        }