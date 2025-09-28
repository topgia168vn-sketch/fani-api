import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Fields cần check từ ORDER_DATETIME_FIELDS
DATETIME_FIELDS_TO_FIX = [
    'orderTime',
    'sendTime', 
    'created',
    'jst_modified',
    'payTime',
    'finalPayTime',
    'presendSendTime',
    'signTime',
    'EndDeliveryTime',
    'EndPickupTime'
]
ORDER_LINE_DATETIME_FIELDS = ['created', 'itemSendDate']


def migrate(cr, version):
    """
    Check và sửa lại giá trị về NULL nếu thời gian nhỏ hơn năm 2000
    """
    _logger.info("Starting JST Sale Order datetime fields migration...")
    for field in DATETIME_FIELDS_TO_FIX:
        try:
            cr.execute(f"""
                UPDATE jst_sale_order
                SET "{field}" = NULL
                WHERE "{field}" IS NOT NULL
                AND "{field}" < '2000-01-01 00:00:00'::timestamp;
            """)
        except Exception as e:
            _logger.error(f"Error fixing field '{field}': {str(e)}")
            continue
    _logger.info("Starting JST Sale Order Line datetime fields migration...")
    for field in ORDER_LINE_DATETIME_FIELDS:
        try:
            cr.execute(f"""
                UPDATE jst_sale_order_line
                SET "{field}" = NULL
                WHERE "{field}" IS NOT NULL
                AND "{field}" < '2000-01-01 00:00:00'::timestamp;
            """)
        except Exception as e:
            _logger.error(f"Error fixing field '{field}': {str(e)}")
            continue
