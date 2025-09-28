import requests
import time
import hmac
import hashlib
import json
import logging
import traceback
import gc
from urllib.parse import urlencode
from secrets import token_urlsafe
from datetime import timedelta, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from odoo import api, models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MAX_CONCURRENT_THREADS = 8

class TiktokShop(models.Model):
    _name = "tiktok.shop"
    _description = "TikTok Shop"
    _order = 'name, id'
    _rec_name = "name"

    # ===== Endpoints =====
    _auth_base_url = "https://auth.tiktok-shops.com"
    _api_base_url = "https://open-api.tiktokglobalshop.com"

    name = fields.Char(required=True)
    shop_id = fields.Char(string="Shop ID", help="Shop ID that authorizes this app")
    shop_code = fields.Char()
    shop_cipher = fields.Char()

    region = fields.Selection([("us", "US"), ("non-us", "Non-US")], required=True, default="non-us")
    service_id = fields.Char(string="Service ID", required=True, groups="base.group_system")
    app_key = fields.Char(required=True, groups="base.group_system")
    app_secret = fields.Char(required=True, groups="base.group_system")
    redirect_uri = fields.Char(string="Redirect URI", required=True)

    access_token = fields.Char(groups="base.group_system")
    refresh_token = fields.Char(groups="base.group_system")
    expires_at = fields.Datetime()
    status = fields.Selection([("authorized", "Authorized"),
                               ("deauthorized", "Deauthorized")])
    oauth_state = fields.Char(string="OAuth State")
    raw_payload = fields.Json()

    sync_data_since = fields.Datetime(string="Sync Data Since",
                                      help="The starting moment that you want to sync data from.")

    # ===== Helpers =====
    def _token_valid(self):
        return bool(self.access_token and self.expires_at and
                    fields.Datetime.now() < self.expires_at - timedelta(minutes=5))

    @api.model
    def _convert_unix_to_datetime(self, unix_timestamp):
        """Convert Unix timestamp to Odoo datetime format."""
        if not unix_timestamp:
            return False
        try:
            return datetime.fromtimestamp(unix_timestamp)
        except (ValueError, TypeError):
            return False

    @api.model
    def _parse_number(self, value):
        """Parse number value from TikTok API response."""
        if not value:
            return 0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0

    @api.model
    def _get_current_locale(self):
        """
        Lấy locale được hỗ trợ dựa trên user language.
        Nếu không có trong danh sách hỗ trợ thì dùng en-US làm default.
        """
        # Danh sách locales được TikTok Shop hỗ trợ
        supported_locales = {
            'de_DE': 'de-DE',
            'en_GB': 'en-GB',
            'en_IE': 'en-IE',
            'en_US': 'en-US',
            'es_ES': 'es-ES',
            'es_MX': 'es-MX',
            'fr_FR': 'fr-FR',
            'id_ID': 'id-ID',
            'it_IT': 'it-IT',
            'ja_JP': 'ja-JP',
            'ms_MY': 'ms-MY',
            'pt_BR': 'pt-BR',
            'th_TH': 'th-TH',
            'vi_VN': 'vi-VN',
            'zh_CN': 'zh-CN',
        }

        # Lấy user language
        user_lang = self.env.user.lang or 'en_US'

        # Map user language với supported locale
        return supported_locales.get(user_lang, 'en-US')

    @api.model
    def _upsert(self, model_name, domain, values):
        """
        Helper method để upsert (update hoặc create) records.

        Args:
            model_name (str): Tên model (e.g., 'tiktok.product', 'tiktok.order')
            domain (list): Domain để search existing record
            values (dict): Values để write/create

        Returns:
            recordset: Record được update hoặc create
        """
        model = self.env[model_name]
        existing_record = model.search(domain, limit=1)

        if existing_record:
            existing_record.write(values)
        else:
            existing_record = model.create(values)

        return existing_record

    # ===== Multi-threading Framework =====
    @api.model
    def _execute_thread_task(self, shop_id, task_name, task_func, *args, **kwargs):
        """
        Execute a task for a single shop in a separate thread
        """
        # Create new environment for this thread
        with self.pool.cursor() as new_cr:
            _self = task_func.__self__
            context = dict(_self.env.context)
            new_env = api.Environment(new_cr, self.env.uid, context)
            shop = new_env['tiktok.shop'].browse(shop_id)

            # Get the task function with the new environment
            _self = _self.with_env(new_env)
            task_func = task_func.__func__.__get__(_self, _self.__class__)

            try:
                _logger.info("Starting %s for shop: %s (ID: %s)", task_name, shop.name, shop.shop_id)

                # Execute the task
                result = task_func(shop, *args, **kwargs)
                new_cr.commit()

                _logger.info("✓ %s completed for %s", task_name, shop.name)
                return {
                    'shop_id': shop_id,
                    'shop_name': shop.name,
                    'status': 'success',
                    'task': task_name,
                    'result': result
                }

            except Exception as e:
                _logger.error("✗ Failed %s for shop %s: %s", task_name, shop.name, str(e))
                _logger.error("Traceback: %s", traceback.format_exc())
                new_cr.rollback()

                return {
                    'shop_id': shop_id,
                    'shop_name': shop.name,
                    'status': 'error',
                    'task': task_name,
                    'error': str(e)
                }

            finally:
                # Cleanup memory
                new_cr.close()
                gc.collect()

    @api.model
    def _run_multi_thread_tasks(self, shops, task_name, task_func, max_workers=None, raise_error=True, *args, **kwargs):
        """
        Run tasks for multiple shops using multi-threading
        """
        if not shops:
            _logger.warning("No shops provided for %s", task_name)
            return []

        _logger.info("Starting %s for %s shops", task_name, len(shops))

        # Set default max_workers
        if max_workers is None:
            max_workers = min(len(shops), MAX_CONCURRENT_THREADS)

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks for each shop
            future_to_shop = {
                executor.submit(self._execute_thread_task, shop.id, task_name, task_func, *args, **kwargs): shop
                for shop in shops
            }

            # Collect results
            for future in as_completed(future_to_shop):
                shop = future_to_shop[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    _logger.error("✗ Thread for shop %s failed: %s", shop.name, str(e))
                    results.append({
                        'shop_id': shop.id,
                        'shop_name': shop.name,
                        'status': 'error',
                        'task': task_name,
                        'error': str(e)
                    })

        # Summary results
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        _logger.info("%s completed:", task_name)
        _logger.info("  ✓ Successful: %s shops", len(successful))
        _logger.info("  ✗ Failed: %s shops", len(failed))

        if successful:
            _logger.info("Successful shops: %s", [r['shop_name'] for r in successful])
        if failed:
            _logger.error("Failed shops: %s", [r['shop_name'] for r in failed])
            if raise_error:
                raise UserError(_(
                    "Failed to %s for some shops:\n"
                    "%s"
                ) % (
                    task_name,
                    "\n".join([f"- {r['shop_name']}: {r['error']}" for r in failed])
                ))

        return results

    # ===== OAuth flows =====
    def _exchange_authorization_code(self, auth_code: str):
        """POST token_exchange_path để lấy access/refresh token."""
        self.ensure_one()
        url = f"{self._auth_base_url}/api/v2/token/get"
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "auth_code": auth_code,
            "grant_type": "authorized_code",
        }
        r = requests.get(url, params=payload, timeout=30)
        if r.status_code != 200:
            raise UserError(_("Exchange code failed: %s") % r.text)

        response = r.json()

        # Check response code theo TikTok API format
        if response.get("code") != 0:
            error_msg = response.get("message", "Unknown error")
            raise UserError(_("TikTok API error: %s") % error_msg)

        data = response.get("data", {})
        if not data:
            raise UserError(_("No data in TikTok API response"))

        # access_token_expire_in là timestamp, cần convert sang datetime
        access_token_expire_timestamp = data.get("access_token_expire_in")
        if access_token_expire_timestamp:
            # Convert timestamp to datetime
            expires_at = self._convert_unix_to_datetime(access_token_expire_timestamp)
        else:
            # Fallback: 7 days from now
            expires_at = fields.Datetime.now() + timedelta(days=7)

        self.write({
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": expires_at,
            "name": data.get("seller_name"),
            "status": "authorized",
        })

    def _refresh_access_token(self):
        self.ensure_one()
        if not self.refresh_token:
            raise UserError(_("No refresh token"))
        url = f"{self._auth_base_url}/api/v2/token/refresh"
        payload = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        r = requests.get(url, params=payload, timeout=30)
        if r.status_code != 200:
            raise UserError(_("Refresh failed: %s") % r.text)

        response = r.json()

        # Check response code theo TikTok API format
        if response.get("code") != 0:
            error_msg = response.get("message", "Unknown error")
            raise UserError(_("TikTok API refresh error: %s") % error_msg)

        data = response.get("data", {})
        if not data:
            raise UserError(_("No data in TikTok API refresh response"))

        # access_token_expire_in là timestamp, cần convert sang datetime
        access_token_expire_timestamp = data.get("access_token_expire_in")
        if access_token_expire_timestamp:
            # Convert timestamp to datetime
            expires_at = self._convert_unix_to_datetime(access_token_expire_timestamp)
        else:
            # Fallback: 7 days from now
            expires_at = fields.Datetime.now() + timedelta(days=7)

        self.write({
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token") or self.refresh_token,  # giữ refresh token cũ nếu không có mới
            "expires_at": expires_at,
        })

    # ===== Request signing =====
    def _auth_params(self):
        """Các common params cần ký (ví dụ app_key, timestamp...)."""
        return {"app_key": self.app_key, "timestamp": str(int(time.time()))}  # seconds, not milliseconds

    def _sign(self, path, params, json_body=None):
        """
        HMAC-SHA256 sign theo TikTok API spec:
        1. Sort params alphabetically
        2. Concatenate param_name + param_value + json_body
        3. Append to path
        4. Prepend & append app secret
        5. HMAC-SHA256 encode
        """
        # Step 1-3: Create canonical string
        sorted_params = sorted(params.items())
        param_string = "".join(f"{k}{v}" for k, v in sorted_params)
        canonical = f"{path}{param_string}"

        # Thêm body vào canonical nếu có
        if isinstance(json_body, dict):
            canonical += json.dumps(json_body)

        # Step 4: Prepend & append app secret
        secret = (self.app_secret or "").encode()
        message = f"{secret.decode()}{canonical}{secret.decode()}".encode()

        # Step 5: HMAC-SHA256 encode
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    # ===== Generic API caller =====
    def _request(self, method, path, params=None, json_body=None, base_url=None, need_sign=True):
        """
        Gọi Shop Open API.
        - method: 'GET'/'POST'/...
        - path: '/api/xxx'
        - params: dict -> sẽ gộp thêm _auth_params() nếu need_sign
        - json_body: dict -> sẽ dùng để tính chữ ký (nếu spec yêu cầu)
        """
        self.ensure_one()
        if not self._token_valid():
            self._refresh_access_token()

        base = base_url or self._api_base_url
        url = f"{base}{path}"
        headers = {
            "x-tts-access-token": self.access_token,
            "Content-Type": "application/json"
        }

        params = dict(params or {})
        if need_sign:
            common = self._auth_params()
            for k, v in common.items():
                params.setdefault(k, v)
            params["sign"] = self._sign(path, params, json_body)

        r = requests.request(method=method, url=url, params=params, json=json_body, headers=headers, timeout=60)
        r.raise_for_status()
        response = r.json()
        if response.get("code") != 0:
            raise UserError(_("TikTok API error: %s") % response.get("message", "Unknown error"))
        return response.get("data", {})

    # ===== Actions =====
    def action_start_authorize(self):
        """Tạo URL authorize và redirect thẳng, không cần ir.actions.server."""
        self.ensure_one()
        # tạo state để đối chiếu khi callback (chống CSRF, identify record)
        state = f"{self.id}:{token_urlsafe(16)}"
        self.write({"oauth_state": state})

        if self.region == "us":
            auth_host = "services.us.tiktokshop.com"
        else:
            auth_host = "services.tiktokshop.com"
        params = {"service_id": self.service_id, "state": state}
        url = f"https://{auth_host}/open/authorize?{urlencode(params)}"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def action_sync_shop(self):
        """Sync shop info from TikTok API."""
        self.ensure_one()
        # Thay path & params đúng spec "Get Authorized Shops" ở Partner Center
        data = self._request("GET", "/authorization/202309/shops", params={})
        shop_info = data.get("shops", [])[0]
        self.write({
            "name": shop_info.get("name"),
            "shop_id": shop_info.get("id"),
            "shop_code": shop_info.get("code"),
            "shop_cipher": shop_info.get("cipher"),
            "raw_payload": shop_info,
        })

    # ===== Cron Jobs =====
    @api.model
    def _cron_refresh_tokens(self):
        """
        Cron job để tự động refresh access tokens trước khi hết hạn.
        """
        shops = self.search([
            ('status', '=', 'authorized'),
            ('refresh_token', '!=', False),
            ('access_token', '!=', False)
        ])

        if not shops:
            return

        for shop in shops:
            # Check nếu token sắp hết hạn (trong vòng 1 ngày)
            if shop.expires_at and shop.expires_at <= fields.Datetime.now() + timedelta(days=1):
                shop._refresh_access_token()

    @api.model
    def _get_last_cron_start(self, cron_xmlid):
        """
        Lấy thời gian mà cron đã chạy lần cuối.
        """
        last_cron_progress = self.env['ir.cron.progress'].search([
            ('cron_id', '=', self.env.ref(cron_xmlid).id),
            ('done', '=', 1)
        ], order='id desc', limit=1)
        if last_cron_progress:
            return last_cron_progress.create_date
        return None

    @api.model
    def _cron_sync_all_data(self):
        """
        Cron job để đồng bộ tất cả data của tất cả shops.
        Mỗi thread xử lý 1 shop hoàn chỉnh: products trước, orders sau.
        """
        _logger.info("Starting comprehensive data sync cron for all shops")

        # Lấy tất cả shops có access_token
        shops = self.search([('access_token', '!=', False)])

        if not shops:
            _logger.warning("No shops with valid access tokens found for data sync")
            return

        _logger.info(f"Found {len(shops)} shops for comprehensive data sync")

        # Chạy multi-thread cho tất cả shops, mỗi thread xử lý 1 shop hoàn chỉnh
        results = self._run_multi_thread_tasks(
            shops,
            "Cron Sync All Data",
            self.with_context(sync_from_cron=True)._cron_sync_all_data_for_shop,
            max_workers=min(len(shops), MAX_CONCURRENT_THREADS),
            raise_error=False
        )

        # Thống kê kết quả
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        _logger.info("Comprehensive data sync completed:")
        _logger.info(f"  ✓ Successful: {len(successful)} shops")
        _logger.info(f"  ✗ Failed: {len(failed)} shops")

        if successful:
            _logger.info(f"Successful shops: {[r['shop_name'] for r in successful]}")
        if failed:
            _logger.error(f"Failed shops: {[r['shop_name'] for r in failed]}")

        # Cập nhật progress sang done
        self.env['ir.cron']._notify_progress(done=1, remaining=0)

        # Trigger cron again nếu có shop cần trigger
        for result in results:
            if result.get('result', {}).get('should_trigger_cron'):
                _logger.info(f"Shop {result['shop_name']} needs to trigger cron again")
                cron = self.env.ref('tiktok_shop_connector.ir_cron_sync_tiktok_all_data')
                cron._trigger()
                break

        # Tổng kết
        _logger.info("=== COMPREHENSIVE DATA SYNC COMPLETED ===")
        _logger.info(f"Total: {len(successful)}/{len(shops)} shops successful")

        if len(failed) > 0:
            _logger.warning(f"Total failed operations: {len(failed)}")
        else:
            _logger.info("All operations completed successfully! 🎉")

    @api.model
    def _cron_sync_all_data_for_shop(self, shop):
        """
        Sync tất cả data cho 1 shop cụ thể.
        Thứ tự: Warehouses → Products → Orders → Returns.
        """
        shop.ensure_one()

        _logger.info(f"Shop {shop.name}: Starting comprehensive data sync")
        result = {}

        # Step 1: Sync Warehouses (thường không thay đổi thường xuyên)
        _logger.info(f"Shop {shop.name}: === STEP 1: SYNCING WAREHOUSES ===")
        result['warehouses'] = self.env['tiktok.warehouse']._sync_warehouses(shop)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Warehouses sync completed")

        # Step 2: Sync Products
        _logger.info(f"Shop {shop.name}: === STEP 2: SYNCING PRODUCTS ===")
        result['products'] = self.env['tiktok.product']._sync_products(shop, max_page=10)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Products sync completed")

        if result['products'].get('has_next_page'):
            result['should_trigger_cron'] = True
            return result

        # # Step 3: Sync Orders
        _logger.info(f"Shop {shop.name}: === STEP 3: SYNCING ORDERS ===")
        result['orders'] = self.env['tiktok.order']._sync_orders(shop, max_page=100)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Orders sync completed")

        if result['orders'].get('has_next_page'):
            result['should_trigger_cron'] = True
            return result

        # Step 4: Sync Returns
        _logger.info(f"Shop {shop.name}: === STEP 4: SYNCING RETURNS ===")
        result['returns'] = self.env['tiktok.return']._sync_returns(shop, max_page=100)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Returns sync completed")

        if result['returns'].get('has_next_page'):
            result['should_trigger_cron'] = True
            return result

        # Step 5: Sync Cancellations
        _logger.info(f"Shop {shop.name}: === STEP 5: SYNCING CANCELLATIONS ===")
        result['cancellations'] = self.env['tiktok.cancel']._sync_cancellations(shop, max_page=100)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Cancellations sync completed")

        if result['cancellations'].get('has_next_page'):
            result['should_trigger_cron'] = True
            return result

        _logger.info(f"Shop {shop.name}: 🎉 Comprehensive data sync completed successfully!")

        return result

    @api.model
    def _cron_sync_all_performance(self):
        """
        Cron job để đồng bộ tất cả performance analytics hàng ngày.
        Thứ tự: Product Performance → SKU Performance → Video Performance → Live Performance.
        """
        _logger.info("Starting performance analytics sync for all shops")

        shops = self.search([('access_token', '!=', False)])

        if not shops:
            _logger.warning("No shops with valid access tokens found for performance analytics sync")
            return

        _logger.info(f"Found {len(shops)} shops for performance analytics sync")

        # Chạy multi-thread cho tất cả shops
        results = self._run_multi_thread_tasks(
            shops,
            "Performance Analytics Sync",
            self.with_context(sync_from_cron=True)._cron_sync_all_performance_for_shop,
            max_workers=min(len(shops), MAX_CONCURRENT_THREADS),
            raise_error=False
        )

        # Thống kê kết quả
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']

        _logger.info("Performance analytics sync completed:")
        _logger.info(f"  ✓ Successful: {len(successful)} shops")
        _logger.info(f"  ✗ Failed: {len(failed)} shops")

        if successful:
            _logger.info(f"Successful shops: {[r['shop_name'] for r in successful]}")
        if failed:
            _logger.error(f"Failed shops: {[r['shop_name'] for r in failed]}")

        # Trigger cron again nếu có shop cần trigger
        for result in results:
            if result.get('result', {}).get('should_trigger_cron'):
                _logger.info(f"Shop {result['shop_name']} needs to trigger performance analytics cron again")
                cron = self.env.ref('tiktok_shop_connector.ir_cron_sync_tiktok_performance_analytics')
                cron._trigger()
                break

        _logger.info("=== PERFORMANCE ANALYTICS SYNC COMPLETED ===")

    @api.model
    def _cron_sync_all_performance_for_shop(self, shop):
        """
        Sync tất cả performance analytics cho 1 shop cụ thể.
        Thứ tự: Product Performance → SKU Performance → Video Performance → Live Performance.
        """
        shop.ensure_one()

        _logger.info(f"Shop {shop.name}: Starting comprehensive performance analytics sync")
        result = {}

        # Step 1: Sync Product Performance
        _logger.info(f"Shop {shop.name}: === STEP 1: SYNCING PRODUCT PERFORMANCE ===")
        result['product_performance'] = self.env['tiktok.product.performance']._sync_product_performance(shop)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Product performance sync completed")

        if result['product_performance'].get('has_more_dates'):
            result['should_trigger_cron'] = True
            return result

        # Step 2: Sync SKU Performance
        _logger.info(f"Shop {shop.name}: === STEP 2: SYNCING SKU PERFORMANCE ===")
        result['sku_performance'] = self.env['tiktok.sku.performance']._sync_sku_performance(shop)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ SKU performance sync completed")

        if result['sku_performance'].get('has_more_dates'):
            result['should_trigger_cron'] = True
            return result

        # Step 3: Sync Video Performance
        _logger.info(f"Shop {shop.name}: === STEP 3: SYNCING VIDEO PERFORMANCE ===")
        result['video_performance'] = self.env['tiktok.video.performance']._sync_video_performance(shop)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Video performance sync completed")

        if result['video_performance'].get('has_more_dates'):
            result['should_trigger_cron'] = True
            return result

        # Step 4: Sync Live Performance
        _logger.info(f"Shop {shop.name}: === STEP 4: SYNCING LIVE PERFORMANCE ===")
        result['live_performance'] = self.env['tiktok.live.performance']._sync_live_performance(shop)
        self.env.cr.commit()
        _logger.info(f"Shop {shop.name}: ✓ Live performance sync completed")

        if result['live_performance'].get('has_more_dates'):
            result['should_trigger_cron'] = True
            return result

        _logger.info(f"Shop {shop.name}: 🎉 Comprehensive performance analytics sync completed successfully!")

        return result

    @api.model
    def _cron_fill_missing_product_sku_relations(self):
        """
        Cron job để fill dữ liệu product_id/sku_id từ tiktok_product_id/tiktok_sku_id
        cho tất cả các model cần thiết.
        """
        _logger.info("=== STARTING MISSING PRODUCT/SKU RELATIONS FILL ===")

        total_filled = 0

        # Define model configurations
        model_configs = [
            {
                'model': 'tiktok.order.line',
                'name': 'Order Lines',
                'fill_product': False,
                'fill_sku': True,
                'sku_field': 'tiktok_sku_id'
            },
            {
                'model': 'tiktok.return.line',
                'name': 'Return Lines',
                'fill_product': False,
                'fill_sku': True,
                'sku_field': 'tiktok_sku_id'
            },
            {
                'model': 'tiktok.cancel.line',
                'name': 'Cancel Lines',
                'fill_product': False,
                'fill_sku': True,
                'sku_field': 'tiktok_sku_id'
            },
            {
                'model': 'tiktok.product.performance',
                'name': 'Product Performance',
                'fill_product': True,
                'fill_sku': False,
                'product_field': 'tiktok_product_id'
            },
            {
                'model': 'tiktok.sku.performance',
                'name': 'SKU Performance',
                'fill_product': False,
                'fill_sku': True,
                'sku_field': 'tiktok_sku_id'
            }
        ]

        # Process each model configuration
        for config in model_configs:
            _logger.info(f"Filling missing relations in {config['name']}...")
            filled = self._fill_model_relations(config)
            total_filled += filled
            _logger.info(f"✓ {config['name']}: {filled} records updated")

        _logger.info(f"✅ MISSING PRODUCT/SKU RELATIONS FILL COMPLETED - {total_filled} records updated")
        return total_filled

    def _fill_model_relations(self, config):
        """Fill missing product_id/sku_id for a specific model configuration."""
        model_name = config['model']
        filled = self.env[model_name].browse()

        if config['fill_sku']:
            domain = [
                ('sku_id', '=', False),
                (config['sku_field'], '!=', False)
            ]
            records = self.env[model_name].search(domain)
            for record in records:
                sku = self.env['tiktok.sku'].search([
                    ('tiktok_id', '=', record[config['sku_field']]),
                    ('shop_id', '=', record.shop_id.id)
                ], limit=1)
                if sku:
                    record.sku_id = sku.id
                    filled |= record

        elif config['fill_product']:
            domain = [
                ('product_id', '=', False),
                (config['product_field'], '!=', False)
            ]
            records = self.env[model_name].search(domain)
            for record in records:
                product = self.env['tiktok.product'].search([
                    ('tiktok_id', '=', record[config['product_field']]),
                    ('shop_id', '=', record.shop_id.id)
                ], limit=1)
                if product:
                    record.product_id = product.id
                    filled |= record

        return len(filled)
