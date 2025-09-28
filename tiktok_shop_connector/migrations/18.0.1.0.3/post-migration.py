import logging

_logger = logging.getLogger(__name__)


def _fill_tiktok_order_new_fields(cr):
    """
    Fill giá trị cho các trường mới của tiktok.order từ raw_payload bằng SQL thuần
    """
    _logger.info("Starting to fill new fields for tiktok.order from raw_payload...")

    # Count total records first
    cr.execute("SELECT COUNT(*) FROM tiktok_order WHERE raw_payload IS NOT NULL")
    total_count = cr.fetchone()[0]
    _logger.info(f"Found {total_count} orders to process")

    # Update all new fields in one query
    _logger.info("Updating all new fields...")
    cr.execute("""
        UPDATE tiktok_order
        SET
            -- Recipient information
            recipient_name = raw_payload->'recipient_address'->>'name',
            recipient_first_name = raw_payload->'recipient_address'->>'first_name',
            recipient_last_name = raw_payload->'recipient_address'->>'last_name',
            recipient_first_name_local_script = raw_payload->'recipient_address'->>'first_name_local_script',
            recipient_last_name_local_script = raw_payload->'recipient_address'->>'last_name_local_script',
            recipient_phone = raw_payload->'recipient_address'->>'phone_number',
            recipient_region_code = raw_payload->'recipient_address'->>'region_code',
            recipient_postal_code = raw_payload->'recipient_address'->>'postal_code',
            recipient_post_town = raw_payload->'recipient_address'->>'post_town',
            recipient_address_line1 = raw_payload->'recipient_address'->>'address_line1',
            recipient_address_line2 = raw_payload->'recipient_address'->>'address_line2',
            recipient_address_line3 = raw_payload->'recipient_address'->>'address_line3',
            recipient_address_line4 = raw_payload->'recipient_address'->>'address_line4',
            -- Payment amounts
            payment_currency = raw_payload->'payment'->>'currency',
            payment_sub_total = CASE
                WHEN raw_payload->'payment'->>'sub_total' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'sub_total')::numeric
                ELSE NULL
            END,
            payment_shipping_fee = CASE
                WHEN raw_payload->'payment'->>'shipping_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_fee')::numeric
                ELSE NULL
            END,
            payment_seller_discount = CASE
                WHEN raw_payload->'payment'->>'seller_discount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'seller_discount')::numeric
                ELSE NULL
            END,
            payment_platform_discount = CASE
                WHEN raw_payload->'payment'->>'platform_discount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'platform_discount')::numeric
                ELSE NULL
            END,
            payment_total_amount = CASE
                WHEN raw_payload->'payment'->>'total_amount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'total_amount')::numeric
                ELSE NULL
            END,
            payment_original_total_product_price = CASE
                WHEN raw_payload->'payment'->>'original_total_product_price' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'original_total_product_price')::numeric
                ELSE NULL
            END,
            payment_original_shipping_fee = CASE
                WHEN raw_payload->'payment'->>'original_shipping_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'original_shipping_fee')::numeric
                ELSE NULL
            END,
            payment_shipping_fee_seller_discount = CASE
                WHEN raw_payload->'payment'->>'shipping_fee_seller_discount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_fee_seller_discount')::numeric
                ELSE NULL
            END,
            payment_shipping_fee_platform_discount = CASE
                WHEN raw_payload->'payment'->>'shipping_fee_platform_discount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_fee_platform_discount')::numeric
                ELSE NULL
            END,
            payment_shipping_fee_co_funded_discount = CASE
                WHEN raw_payload->'payment'->>'shipping_fee_co_funded_discount' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_fee_co_funded_discount')::numeric
                ELSE NULL
            END,
            payment_tax = CASE
                WHEN raw_payload->'payment'->>'tax' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'tax')::numeric
                ELSE NULL
            END,
            payment_small_order_fee = CASE
                WHEN raw_payload->'payment'->>'small_order_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'small_order_fee')::numeric
                ELSE NULL
            END,
            payment_shipping_fee_tax = CASE
                WHEN raw_payload->'payment'->>'shipping_fee_tax' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_fee_tax')::numeric
                ELSE NULL
            END,
            payment_product_tax = CASE
                WHEN raw_payload->'payment'->>'product_tax' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'product_tax')::numeric
                ELSE NULL
            END,
            payment_retail_delivery_fee = CASE
                WHEN raw_payload->'payment'->>'retail_delivery_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'retail_delivery_fee')::numeric
                ELSE NULL
            END,
            payment_buyer_service_fee = CASE
                WHEN raw_payload->'payment'->>'buyer_service_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'buyer_service_fee')::numeric
                ELSE NULL
            END,
            payment_handling_fee = CASE
                WHEN raw_payload->'payment'->>'handling_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'handling_fee')::numeric
                ELSE NULL
            END,
            payment_shipping_insurance_fee = CASE
                WHEN raw_payload->'payment'->>'shipping_insurance_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'shipping_insurance_fee')::numeric
                ELSE NULL
            END,
            payment_item_insurance_fee = CASE
                WHEN raw_payload->'payment'->>'item_insurance_fee' ~ '^[0-9]+\\.?[0-9]*$'
                THEN (raw_payload->'payment'->>'item_insurance_fee')::numeric
                ELSE NULL
            END
        WHERE raw_payload IS NOT NULL
    """)

    _logger.info("Completed filling new fields for tiktok.order")


def _fill_tiktok_order_line_new_fields(cr):
    """
    Fill giá trị cho các trường mới của tiktok.order.line từ raw_payload bằng SQL thuần
    """
    _logger.info("Starting to fill new fields for tiktok.order.line from parent order raw_payload...")

    # Count total records first
    cr.execute("""
        SELECT COUNT(*)
        FROM tiktok_order_line ol
        JOIN tiktok_order o ON ol.order_id = o.id
        WHERE o.raw_payload IS NOT NULL
    """)
    total_count = cr.fetchone()[0]
    _logger.info(f"Found {total_count} order lines to process")

    # Update all new fields in one query using CTE to match line items
    _logger.info("Updating all new fields...")
    cr.execute("""
        WITH line_item_data AS (
            SELECT
                ol.id as line_id,
                line_item->>'request_cancel_time' as request_cancel_time,
                line_item->>'delivery_time' as delivery_time,
                line_item->>'collection_time' as collection_time,
                line_item->>'cancel_time' as cancel_time,
                line_item->>'delivery_due_time' as delivery_due_time,
                line_item->>'collection_due_time' as collection_due_time,
                line_item->>'pick_up_cut_off_time' as pick_up_cut_off_time,
                line_item->>'fast_dispatch_sla_time' as fast_dispatch_sla_time,
                line_item->>'is_on_hold_order' as is_on_hold_order,
                line_item->>'sell_order_fee' as sell_order_fee
            FROM tiktok_order_line ol
            JOIN tiktok_order o ON ol.order_id = o.id
            CROSS JOIN LATERAL jsonb_array_elements(o.raw_payload->'line_items') AS line_item
            WHERE o.raw_payload IS NOT NULL
            AND o.raw_payload->'line_items' IS NOT NULL
            AND line_item->>'id' = ol.tiktok_id
        )
        UPDATE tiktok_order_line
        SET
            request_cancel_time = CASE
                WHEN lid.request_cancel_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.request_cancel_time::bigint)
                ELSE NULL
            END,
            delivery_time = CASE
                WHEN lid.delivery_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.delivery_time::bigint)
                ELSE NULL
            END,
            collection_time = CASE
                WHEN lid.collection_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.collection_time::bigint)
                ELSE NULL
            END,
            cancel_time = CASE
                WHEN lid.cancel_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.cancel_time::bigint)
                ELSE NULL
            END,
            delivery_due_time = CASE
                WHEN lid.delivery_due_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.delivery_due_time::bigint)
                ELSE NULL
            END,
            collection_due_time = CASE
                WHEN lid.collection_due_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.collection_due_time::bigint)
                ELSE NULL
            END,
            pick_up_cut_off_time = CASE
                WHEN lid.pick_up_cut_off_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.pick_up_cut_off_time::bigint)
                ELSE NULL
            END,
            fast_dispatch_sla_time = CASE
                WHEN lid.fast_dispatch_sla_time ~ '^[0-9]+$'
                THEN to_timestamp(lid.fast_dispatch_sla_time::bigint)
                ELSE NULL
            END,
            is_on_hold_order = CASE
                WHEN lid.is_on_hold_order = 'true' THEN true
                WHEN lid.is_on_hold_order = 'false' THEN false
                ELSE NULL
            END,
            sell_order_fee = CASE
                WHEN lid.sell_order_fee ~ '^[0-9]+\\.?[0-9]*$'
                THEN lid.sell_order_fee::numeric
                ELSE NULL
            END
        FROM line_item_data lid
        WHERE tiktok_order_line.id = lid.line_id
    """)

    _logger.info("Completed filling new fields for tiktok.order_line")


def migrate(cr, version):
    _fill_tiktok_order_new_fields(cr)
    _fill_tiktok_order_line_new_fields(cr)
