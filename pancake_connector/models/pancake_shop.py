import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

MAX_CONCURRENT_THREADS = 8


class PancakeShop(models.Model):
    _name = "pancake.shop"
    _inherit = ["pancake.api.mixin"]
    _description = "Pancake Shop"
    _rec_name = "name"
    _order = "name, id"

    # API key 'id' -> tránh đè id của Odoo
    pancake_id = fields.Char(
        string="Pancake ID",
        index=True,
        help="Field 'id' from Pancake API /shops"
    )
    name = fields.Char(
        string="Name",
        help="Field 'name' from Pancake API"
    )
    avatar_url = fields.Char(
        string="Avatar URL",
        help="Field 'avatar_url' from Pancake API"
    )

    # Mảng link_post_marketer giữ nguyên dạng JSON
    link_post_marketer = fields.Json(
        string="link_post_marketer (JSON)",
        help="Array 'link_post_marketer' from Pancake API"
    )

    # Lưu toàn bộ payload shop để lần vết
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON of the shop object as returned by Pancake"
    )

    # Quan hệ
    page_ids = fields.One2many(
        "pancake.page",
        "shop_id",
        string="Pages"
    )

    # Cron sync tracking
    last_cron_sync = fields.Datetime(
        string="Last Cron Sync",
        readonly=True,
        help="Last time this shop was synced by cron job"
    )

    # --- Cấu hình kết nối ---
    api_key = fields.Char(string="API Key", required=True, help="API key of this shop")

    _sql_constraints = [
        ("pancake_shop_uniq",
         "unique(pancake_id)",
         "Pancake shop must be unique by Pancake ID."),
    ]

    @api.model
    def _fetch_pages(self, shop):
        """
        Task function for fetching pages
        """
        data = shop._pancake_get(shop.api_key, "/shops")

        # API trả {"shops": [...], "success": true}
        shops = (data or {}).get("shops") or []
        if not shops:
            raise UserError(_("Pancake returned no shops for this API key"))

        # Nếu đã có pancake_id trên record → tìm đúng shop theo id.
        target = None
        if shop.pancake_id:
            for s in shops:
                if str(s.get("id")) == str(shop.pancake_id):
                    target = s
                    break
            if not target:
                raise UserError(_("Cannot find shop id %s in API response") % shop.pancake_id)
        else:
            # Chưa có → nếu chỉ có 1 shop, dùng luôn; nếu >1, bắt buộc người dùng nhập 'pancake_id' để xác định.
            if len(shops) == 1:
                target = shops[0]
            else:
                raise UserError(_(
                    "This API key returns multiple shops. Please fill the correct 'Pancake ID' "
                    "on this record first, then run again."
                ))

        # Cập nhật thông tin shop
        shop_vals = {
            "pancake_id": str(target.get("id")) if target.get("id") is not None else False,
            "name": target.get("name") or shop.name,
            "avatar_url": target.get("avatar_url"),
            "link_post_marketer": target.get("link_post_marketer"),
            "raw_payload": target,
        }
        shop.write(shop_vals)

        # Đồng bộ pages
        for p in (target.get("pages") or []):
            page_vals = {
                "pancake_id": str(p.get("id")) if p.get("id") is not None else False,
                "shop_id": shop.id,
                "name": p.get("name"),
                "platform": p.get("platform"),
                "settings": p.get("settings"),
                "raw_payload": p,
            }
            # unique(shop_id, pancake_id)
            dom = [("shop_id", "=", shop.id), ("pancake_id", "=", page_vals["pancake_id"])]
            shop._upsert("pancake.page", dom, page_vals)

        return True

    def action_fetch_pages(self):
        """
        Đồng bộ thông tin shop & pages từ Pancake.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self._fetch_pages(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Fetch Pages",
                self._fetch_pages,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )

    @api.model
    def _fetch_customers(self, shop):
        """
        Task function for fetching customers
        """
        return shop.env["pancake.customer"]._fetch_from_pancake(shop)

    def action_fetch_customers(self):
        """
        Đồng bộ danh sách Customers từ Pancake.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self._fetch_customers(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Fetch Customers",
                self._fetch_customers,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )

    @api.model
    def _fetch_orders(self, shop):
        """
        Task function for fetching orders
        """
        return shop.env["pancake.order"]._fetch_from_pancake(shop)

    def action_fetch_orders(self):
        """
        Đồng bộ Orders từ Pancake.
        - Single shop: chạy trực tiếp
        - Multiple shops: chạy đa luồng
        """
        if len(self) == 1:
            # Single shop - chạy trực tiếp
            return self._fetch_orders(self)
        else:
            # Multiple shops - chạy đa luồng
            return self._run_multi_thread_tasks(
                self,
                "Fetch Orders",
                self._fetch_orders,
                max_workers=min(len(self), MAX_CONCURRENT_THREADS)
            )

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
            shop = new_env['pancake.shop'].browse(shop_id)

            # Get the task function with the new environment
            _self = _self.with_env(new_env)
            task_func = task_func.__func__.__get__(_self, _self.__class__)

            try:
                _logger.info("Starting %s for shop: %s (ID: %s)", task_name, shop.name, shop.pancake_id)

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
                new_cr.rollback()
                return {
                    'shop_id': shop_id,
                    'shop_name': shop.name,
                    'status': 'error',
                    'task': task_name,
                    'error': str(e)
                }

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

    @api.model
    def _sync_all(self, shop):
        """
        Full sync task for a single shop (used by cron)
        """
        now = fields.Datetime.now()

        # Get shop's last sync time
        last_sync = shop.last_cron_sync

        # 1. Sync Shop & Pages (always full sync)
        shop.action_fetch_pages()

        # 2. Sync Customers (incremental if has last_sync)
        shop.env["pancake.customer"]._fetch_from_pancake(
            shop,
            updated_since=last_sync,
        )

        # 3. Sync Orders (incremental if has last_sync)
        shop.env["pancake.order"]._fetch_from_pancake(
            shop,
            updated_since=last_sync,
        )

        # Update last_cron_sync timestamp
        shop.last_cron_sync = now

        return True

    @api.model
    def _cron_sync_pancake_data(self):
        """
        Cron method: Đồng bộ tất cả dữ liệu từ Pancake mỗi 4 tiếng
        - Chạy đa luồng, mỗi shop 1 thread
        - Sử dụng last_cron_sync riêng cho từng shop
        - Nếu 1 shop lỗi, các shop khác vẫn chạy bình thường
        """
        _logger.info("Starting Pancake sync cron with multi-threading")

        # Lấy tất cả shops
        shops = self.search([])
        if not shops:
            _logger.warning("No shops found for sync")
            return

        # Sử dụng multi-threading framework
        self._run_multi_thread_tasks(
            shops,
            "Full Sync",
            self._sync_all,
            max_workers=MAX_CONCURRENT_THREADS,
            raise_error=False
        )
