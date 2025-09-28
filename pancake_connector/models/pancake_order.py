import logging
from datetime import datetime
from odoo import fields, models, _

_logger = logging.getLogger(__name__)


class PancakeOrder(models.Model):
    _name = "pancake.order"
    _description = "Pancake Order"
    _rec_name = "pancake_id"
    _order = "inserted_at desc, id desc"

    # API 'id' (integer/string tùy cấu hình) -> tránh trùng id Odoo
    pancake_id = fields.Char(
        string="Pancake Order ID",
        required=True,
        index=True,
        help="Field 'id' from API (Thông tin đơn hàng)"
    )
    system_id = fields.Integer(
        string="System ID",
        help="Field 'system_id' from API"
    )

    # Liên kết
    shop_id = fields.Many2one(
        "pancake.shop",
        string="Shop",
        required=True,
        index=True,
        ondelete="cascade",
        help="Field 'shop_id' from API"
    )
    page_id = fields.Many2one(
        "pancake.page",
        string="Page",
        index=True,
        ondelete="set null",
        help="Field 'page_id' from API"
    )
    customer_id = fields.Many2one(
        "pancake.customer",
        string="Customer",
        index=True,
        ondelete="set null",
        help="Map from 'customer.id' in API (customer block 1.1)"
    )

    # Trạng thái & phân loại
    status = fields.Selection([
        ('0', 'New'),
        ('1', 'Confirmed'),
        ('2', 'Shipped'),
        ('3', 'Received'),
        ('4', 'Returning'),
        ('5', 'Returned'),
        ('6', 'Cancelled'),
        ('7', 'Deleted'),
        ('8', 'Packing'),
        ('9', 'Waiting for Delivery'),
        ('11', 'Waiting for Goods'),
        ('12', 'Waiting to Print'),
        ('13', 'Printed'),
        ('15', 'Partially Returned'),
        ('16', 'Payment Collected'),
        ('17', 'Waiting for Confirmation'),
        ('20', 'Ordered'),
    ], string="Status", help="Order status (see 'Trạng thái đơn hàng')")
    sub_status = fields.Selection([
        ('1', 'Needs Processing'),
        ('2', 'Processed'),
        ('3', 'Responded'),
    ], string="Sub Status", help="Field 'sub_status' (1.7) - Lý do chậm trễ giao hàng")
    is_livestream = fields.Boolean(string="Is Livestream", help="Field 'is_livestream'")
    is_live_shopping = fields.Boolean(string="Is Live Shopping", help="Field 'is_live_shopping'")
    is_smc = fields.Boolean(string="Is SMC", help="Field 'is_smc' (Messenger commerce)")
    is_from_ecommerce = fields.Boolean(string="Is From E-commerce", help="Field 'is_from_ecommerce'")
    is_linked_partner = fields.Boolean(string="Is Linked Partner", help="Field 'is_linked_partner'")
    received_at_shop = fields.Boolean(string="Received At Shop", help="Field 'received_at_shop' (bán tại quầy)")

    # Nguồn đơn / quảng cáo / bài viết
    account = fields.Char(string="Account", help="Field 'account' (mã nguồn đơn)")
    account_name = fields.Char(string="Account Name", help="Field 'account_name'")
    order_sources = fields.Char(string="Order Sources", help="Field 'order_sources'")
    ads_source = fields.Char(string="Ads Source", help="Field 'ads_source'")
    post_id = fields.Char(string="Post ID", help="Field 'post_id'")

    # Kho hàng / vận chuyển
    warehouse_id = fields.Char(string="Warehouse ID", help="Field 'warehouse_id'")
    warehouse_info = fields.Json(string="Warehouse Info (JSON)", help="Field 'warehouse_info'")
    shipping_fee = fields.Integer(string="Shipping Fee", help="Field 'shipping_fee'")
    partner_fee = fields.Integer(string="Partner Fee", help="Field 'partner_fee'")
    cod = fields.Integer(string="COD", help="Field 'cod' (tổng cần thu)")
    customer_pay_fee = fields.Boolean(string="Customer Pay Fee", help="Field 'customer_pay_fee'")

    # Tiền & chiết khấu & phụ phí (đơn vị: đồng, dùng số nguyên)
    total_discount = fields.Integer(string="Total Discount", help="Field 'total_discount'")
    discount = fields.Integer(string="Discount", help="Field 'discount'")
    discount_by_customer_level = fields.Integer(string="Discount by Customer Level", help="Field 'discount_by_customer_level'")
    surcharge = fields.Integer(string="Surcharge", help="Field 'surcharge'")
    cost_surcharge = fields.Integer(string="Cost Surcharge", help="Field 'cost_surcharge'")
    tax = fields.Integer(string="Tax", help="Field 'tax'")

    # Phương thức thanh toán (tổng theo kênh) + chuyển khoản
    cash = fields.Integer(string="Cash", help="Field 'cash'")
    transfer_money = fields.Integer(string="Transfer Money", help="Field 'transfer_money'")
    charged_by_card = fields.Integer(string="Charged by Card", help="Field 'charged_by_card'")
    charged_by_momo = fields.Integer(string="Charged by MOMO", help="Field 'charged_by_momo'")
    charged_by_vnpay = fields.Integer(string="Charged by VNPAY", help="Field 'charged_by_vnpay'")
    charged_by_qrpay = fields.Integer(string="Charged by QRPAY", help="Field 'charged_by_qrpay'")
    charged_by_fundiin = fields.Integer(string="Charged by Fundiin", help="Field 'charged_by_fundiin'")
    charged_by_kredivo = fields.Integer(string="Charged by Kredivo", help="Field 'charged_by_kredivo'")
    bank_payments = fields.Json(string="Bank Payments (JSON)", help="Field 'bank_payments'")
    bank_transfer_images = fields.Json(string="Bank Transfer Images (JSON)", help="Field 'bank_transfer_images'")

    # Khách hàng nhận hàng + liên hệ
    bill_full_name = fields.Char(string="Bill Full Name", help="Field 'bill_full_name'")
    bill_email = fields.Char(string="Bill Email", help="Field 'bill_email'")
    duplicated_phone = fields.Boolean(string="Duplicated Phone", help="Field 'duplicated_phone'")
    duplicated_customer = fields.Boolean(string="Duplicated Customer", help="Field 'duplicated_customer'")

    # Thông tin nhân sự liên quan
    creator_id = fields.Char(string="Creator ID", help="Field 'creator_id'")
    creator = fields.Json(string="Creator (JSON)", help="Field 'creator'")
    last_editor_id = fields.Char(string="Last Editor ID", help="Field 'last_editor_id'")
    last_editor = fields.Json(string="Last Editor (JSON)", help="Field 'last_editor'")
    assigning_seller_id = fields.Char(string="Assigning Seller ID", help="Field 'assigning_seller_id'")
    assigning_seller = fields.Json(string="Assigning Seller (JSON)", help="Field 'assigning_seller'")
    assigning_care_id = fields.Char(string="Assigning Care ID", help="Field 'assigning_care_id'")
    assigning_care = fields.Json(string="Assigning Care (JSON)", help="Field 'assigning_care'")
    marketer = fields.Json(string="Marketer (JSON)", help="Field 'marketer'")
    pke_mkter = fields.Char(string="PK Marketer", help="Field 'pke_mkter'")
    viewing = fields.Json(string="Viewing (JSON)", help="Field 'viewing'")

    # Thông tin vận chuyển & khuyến mãi (để JSON theo yêu cầu)
    partner = fields.Json(string="Partner (JSON)", help="Block 'partner (1.3)'")
    shipping_address_json = fields.Json(string="Shipping Address (JSON)", help="Block 'shipping_address (1.5)'")
    activated_combo_products = fields.Json(string="Activated Combo Products (JSON)", help="Field 'activated_combo_products'")
    activated_promotion_advances_json = fields.Json(string="Activated Promotion Advances (JSON)", help="Block 'activated_promotion_advances (1.6)'")
    tags_json = fields.Json(string="Tags (JSON)", help="Block 'tags (1.2)'")
    order_currency = fields.Char(string="Order Currency", help="Field 'order_currency'")
    einvoices = fields.Json(string="E-invoices (JSON)", help="Field 'einvoices'")

    # Thời gian & lịch sử
    inserted_at = fields.Datetime(string="Inserted At", help="Field 'inserted_at'")
    updated_at = fields.Datetime(string="Updated At", help="Field 'updated_at'")
    last_update_status_at = fields.Datetime(string="Last Update Status At", help="Field 'last_update_status_at'")
    time_assign_care = fields.Datetime(string="Time Assign Care", help="Field 'time_assign_care'")
    time_send_partner = fields.Datetime(string="Time Send Partner", help="Field 'time_send_partner'")
    estimate_delivery_date = fields.Datetime(string="Estimate Delivery Date", help="Field 'estimate_delivery_date'")
    status_history = fields.Json(string="Status History (JSON)", help="Field 'status_history'")
    histories = fields.Json(string="Histories (JSON)", help="Field 'histories'")

    # Khác
    note = fields.Text(string="Note", help="Field 'note' (ghi chú nội bộ)")
    note_print = fields.Text(string="Note Print", help="Field 'note_print'")
    note_image = fields.Json(string="Note Image (JSON)", help="Field 'note_image'")
    custom_id = fields.Char(string="Custom ID", help="Field 'custom_id'")
    order_returned_ids = fields.Char(string="Order Returned IDs", help="Field 'order_returned_ids'")
    returned_reason = fields.Char(string="Returned Reason", help="Field 'returned_reason'")
    link_confirm_order = fields.Char(string="Link Confirm Order", help="Field 'link_confirm_order'")

    # Toàn bộ payload đơn (để lần vết đầy đủ)
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON order object as returned by API"
    )

    # Quan hệ
    item_ids = fields.One2many(
        "pancake.order.item",
        "order_id",
        string="Items"
    )

    _sql_constraints = [
        ("pancake_order_shop_pancake_id_uniq",
         "unique(shop_id, pancake_id)",
         "Order must be unique by (Shop, Pancake ID)."),
    ]

    def _fetch_from_pancake(self, shop, updated_since=None, page_size=30, max_pages=None, extra_params=None):
        """
        Private method: Đồng bộ Orders từ Pancake:
        - Phân trang với page_size (mặc định 30, tối đa 100).
        - Incremental nếu truyền updated_since (dùng start_time_updated_at).
        - Map customer/page nếu tìm được; nếu không thì để trống.
        - Các block phức tạp (shipping_address, promotion_advances, tags, payments...) để JSON theo thiết kế.
        - Items: xóa hết items cũ của order rồi tạo lại theo payload mới (đơn giản & luôn đúng).

        extra_params: dict các filter bổ sung (vd: {"status": 20})
        """
        OrderItem = self.env["pancake.order.item"].sudo()
        Page = self.env["pancake.page"].sudo()
        Customer = self.env["pancake.customer"].sudo()

        if not shop.pancake_id:
            raise ValueError(_("Shop %s missing pancake_id, fetch pages first.") % shop.display_name)

        page_number = 1
        total_imported = 0
        orders = self.env["pancake.order"].browse()
        while True:
            params = {"page_number": page_number, "page_size": page_size}
            if updated_since:
                if isinstance(updated_since, datetime):
                    # Convert to Unix timestamp (seconds)
                    updated_timestamp = int(updated_since.timestamp())
                else:
                    # Assume it's already a timestamp
                    updated_timestamp = int(updated_since)
                params["updateStatus"] = "updated_at"  # type: ignore
                params["startDateTime"] = updated_timestamp
            if extra_params:
                params.update(extra_params)

            payload = shop._pancake_get(shop.api_key, f"/shops/{shop.pancake_id}/orders", params=params)
            data = (payload or {}).get("data") or []
            if not data:
                break

            for it in data:
                # Resolve page_id (Many2one) từ order.page_id (mã bên Pancake)
                page_rec_id = False
                if it.get("page_id"):
                    page_rec = Page.search([
                        ("shop_id", "=", shop.id),
                        ("pancake_id", "=", str(it.get("page_id")))
                    ], limit=1)
                    page_rec_id = page_rec.id or False

                # Resolve customer_id nếu payload có block customer và id
                cust_rec_id = False
                cust_block = it.get("customer") or {}
                if cust_block.get("id"):
                    cust_rec = Customer.search([
                        ("shop_id", "=", shop.id),
                        ("pancake_id", "=", str(cust_block.get("id")))
                    ], limit=1)
                    cust_rec_id = cust_rec.id or False

                # Map các field đã định nghĩa trong model pancake.order
                vals = {
                    "pancake_id": str(it.get("id")),
                    "system_id": it.get("system_id"),
                    "shop_id": shop.id,
                    "page_id": page_rec_id,
                    "customer_id": cust_rec_id,

                    "status": str(it.get("status")) if it.get("status") is not None else False,
                    "sub_status": str(it.get("sub_status")) if it.get("sub_status") is not None else False,
                    "is_livestream": it.get("is_livestream"),
                    "is_live_shopping": it.get("is_live_shopping"),
                    "is_smc": it.get("is_smc"),
                    "is_from_ecommerce": it.get("is_from_ecommerce"),
                    "is_linked_partner": it.get("is_linked_partner"),
                    "received_at_shop": it.get("received_at_shop"),

                    "account": it.get("account"),
                    "account_name": it.get("account_name"),
                    "order_sources": it.get("order_sources"),
                    "ads_source": it.get("ads_source"),
                    "post_id": it.get("post_id"),

                    "warehouse_id": it.get("warehouse_id"),
                    "warehouse_info": it.get("warehouse_info"),
                    "shipping_fee": it.get("shipping_fee"),
                    "partner_fee": it.get("partner_fee"),
                    "cod": it.get("cod"),
                    "customer_pay_fee": it.get("customer_pay_fee"),

                    "total_discount": it.get("total_discount"),
                    "discount": it.get("discount"),
                    "discount_by_customer_level": it.get("discount_by_customer_level"),
                    "surcharge": it.get("surcharge"),
                    "cost_surcharge": it.get("cost_surcharge"),
                    "tax": it.get("tax"),

                    "cash": it.get("cash"),
                    "transfer_money": it.get("transfer_money"),
                    "charged_by_card": it.get("charged_by_card"),
                    "charged_by_momo": it.get("charged_by_momo"),
                    "charged_by_vnpay": it.get("charged_by_vnpay"),
                    "charged_by_qrpay": it.get("charged_by_qrpay"),
                    "charged_by_fundiin": it.get("charged_by_fundiin"),
                    "charged_by_kredivo": it.get("charged_by_kredivo"),
                    "bank_payments": it.get("bank_payments"),
                    "bank_transfer_images": it.get("bank_transfer_images"),

                    "bill_full_name": it.get("bill_full_name"),
                    "bill_email": it.get("bill_email"),
                    "duplicated_phone": it.get("duplicated_phone"),
                    "duplicated_customer": it.get("duplicated_customer"),

                    "creator_id": it.get("creator_id"),
                    "creator": it.get("creator"),
                    "last_editor_id": it.get("last_editor_id"),
                    "last_editor": it.get("last_editor"),
                    "assigning_seller_id": it.get("assigning_seller_id"),
                    "assigning_seller": it.get("assigning_seller"),
                    "assigning_care_id": it.get("assigning_care_id"),
                    "assigning_care": it.get("assigning_care"),
                    "marketer": it.get("marketer"),
                    "pke_mkter": it.get("pke_mkter"),
                    "viewing": it.get("viewing"),

                    # JSON blocks theo yêu cầu
                    "partner": it.get("partner"),
                    "shipping_address_json": it.get("shipping_address"),
                    "activated_combo_products": it.get("activated_combo_products"),
                    "activated_promotion_advances_json": it.get("activated_promotion_advances"),
                    "tags_json": it.get("tags"),
                    "order_currency": it.get("order_currency"),
                    "einvoices": it.get("einvoices"),

                    # Times (parse bằng helper)
                    "inserted_at": shop._parse_dt(it.get("inserted_at")),
                    "updated_at": shop._parse_dt(it.get("updated_at")),
                    "last_update_status_at": shop._parse_dt(it.get("last_update_status_at")),
                    "time_assign_care": shop._parse_dt(it.get("time_assign_care")),
                    "time_send_partner": shop._parse_dt(it.get("time_send_partner")),
                    "estimate_delivery_date": shop._parse_dt(it.get("estimate_delivery_date")),
                    "status_history": it.get("status_history"),
                    "histories": it.get("histories"),

                    "note": it.get("note"),
                    "note_print": it.get("note_print"),
                    "note_image": it.get("note_image"),
                    "custom_id": it.get("custom_id"),
                    "order_returned_ids": it.get("order_returned_ids"),
                    "returned_reason": it.get("returned_reason"),
                    "link_confirm_order": it.get("link_confirm_order"),

                    # Toàn bộ payload để lần vết
                    "raw_payload": it,
                }

                # Upsert Order theo (shop_id, pancake_id)
                dom = [("shop_id", "=", shop.id), ("pancake_id", "=", vals["pancake_id"])]
                order_rec = shop._upsert("pancake.order", dom, vals)
                orders |= order_rec

                # ---- Sync Items: xóa cũ, tạo mới ----
                # (Đơn giản & luôn đúng với payload hiện tại)
                order_rec.item_ids.unlink()
                for item in (it.get("items") or []):
                    item_vals = {
                        "order_id": order_rec.id,
                        "product_id_ext": str(item.get("product_id")) if item.get("product_id") is not None else False,
                        "variation_id_ext": str(item.get("variation_id")) if item.get("variation_id") is not None else False,

                        "name": item.get("name"),
                        "sku": item.get("sku"),

                        "quantity": item.get("quantity"),
                        "price": item.get("price"),
                        "discount_each_product": item.get("discount_each_product"),
                        "is_discount_percent": item.get("is_discount_percent"),
                        "subtotal": item.get("subtotal"),
                        "total": item.get("total"),

                        "measure_group_id": item.get("measure_group_id"),
                        "is_bonus_product": item.get("is_bonus_product"),
                        "is_composite": item.get("is_composite"),
                        "is_wholesale": item.get("is_wholesale"),
                        "note": item.get("note") or item.get("note_product"),

                        "variation_info_json": item.get("variation_info"),
                        "components_json": item.get("components"),

                        "raw_payload": item,
                    }
                    OrderItem.create(item_vals)

            total_imported += len(data)

            # Điều hướng phân trang
            meta = (payload or {}).get("meta") or {}
            total = meta.get("total")
            page_size_actual = meta.get("page_size") or page_size
            if total and page_number * page_size_actual >= total:
                break
            page_number += 1
            if max_pages and page_number > max_pages:
                break

        _logger.info("Fetched %s orders for shop %s", total_imported, shop.name)
        return orders
