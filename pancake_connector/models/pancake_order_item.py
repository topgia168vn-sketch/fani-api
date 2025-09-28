from odoo import fields, models


class PancakeOrderItem(models.Model):
    _name = "pancake.order.item"
    _description = "Pancake Order Item"
    _rec_name = "name"
    _order = "id"

    order_id = fields.Many2one(
        "pancake.order",
        string="Order",
        required=True,
        index=True,
        ondelete="cascade"
    )

    # Thông tin sản phẩm/mẫu mã
    product_id_ext = fields.Char(
        string="Product ID (Ext)",
        index=True,
        help="Field 'product_id' from items[]"
    )
    variation_id_ext = fields.Char(
        string="Variation ID (Ext)",
        index=True,
        help="Field 'variation_id' from items[]"
    )

    # Thông tin hiển thị
    name = fields.Char(string="Name", help="Product/Variation display name if available")
    sku = fields.Char(string="SKU", help="SKU if present in variation_info")

    # Số lượng, giá, giảm (đơn vị: đồng)
    quantity = fields.Integer(string="Quantity", help="Field 'quantity'")
    price = fields.Integer(string="Price", help="Unit price (integer, VND)")
    discount_each_product = fields.Integer(string="Discount Each Product", help="Field 'discount_each_product'")
    is_discount_percent = fields.Boolean(string="Is Discount Percent", help="Field 'is_discount_percent'")
    subtotal = fields.Integer(string="Subtotal", help="Derived/if provided")
    total = fields.Integer(string="Total", help="Derived/if provided")

    # Cờ & nhóm ĐVT & loại cấu thành/bonus/wholesale
    measure_group_id = fields.Integer(string="Measure Group ID", help="Field 'measure_group_id'")
    is_bonus_product = fields.Boolean(string="Is Bonus Product", help="Field 'is_bonus_product'")
    is_composite = fields.Boolean(string="Is Composite", help="Field 'is_composite'")
    is_wholesale = fields.Boolean(string="Is Wholesale", help="Field 'is_wholesale'")
    note = fields.Char(string="Note", help="Field 'note' / 'note_product' if needed")

    # JSON chi tiết
    variation_info_json = fields.Json(
        string="Variation Info (JSON)",
        help="Field 'variation_info' from items[]"
    )
    components_json = fields.Json(
        string="Components (JSON)",
        help="Field 'components' from items[] (for composite/bundle/combo)"
    )

    # Lưu nguyên payload item để lần vết
    raw_payload = fields.Json(
        string="Raw Payload",
        help="Full JSON of items[] element"
    )
