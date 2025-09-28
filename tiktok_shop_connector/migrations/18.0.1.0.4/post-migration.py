import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migration script để populate tiktok.return.reason từ raw_payload của existing returns.
    Sử dụng pure SQL để xử lý hiệu quả với số lượng lớn.
    """
    _logger.info("Starting migration: Populate tiktok.return.reason from raw_payload")

    # Bước 1: Tạo tiktok.return.reason records từ unique return_reason + return_reason_text
    _logger.info("Step 1: Creating return reason records...")
    cr.execute("""
        INSERT INTO tiktok_return_reason (code, name, create_date, write_date)
        SELECT DISTINCT
            raw_payload->>'return_reason' as code,
            raw_payload->>'return_reason_text' as name,
            NOW() as create_date,
            NOW() as write_date
        FROM tiktok_return
        WHERE raw_payload IS NOT NULL
        AND raw_payload->>'return_reason' IS NOT NULL
        AND raw_payload->>'return_reason' != ''
        AND raw_payload->>'return_reason_text' IS NOT NULL
        AND raw_payload->>'return_reason_text' != ''
        ON CONFLICT (code) DO NOTHING
    """)

    created_reasons = cr.rowcount
    _logger.info(f"Created {created_reasons} new return reason records")

    # Bước 2: Update tiktok_return với return_reason_id
    _logger.info("Step 2: Linking returns to return reasons...")
    cr.execute("""
        UPDATE tiktok_return
        SET return_reason_id = trr.id
        FROM tiktok_return_reason trr
        WHERE tiktok_return.raw_payload->>'return_reason' = trr.code
        AND tiktok_return.raw_payload IS NOT NULL
        AND tiktok_return.raw_payload->>'return_reason' IS NOT NULL
        AND tiktok_return.raw_payload->>'return_reason' != ''
        AND tiktok_return.raw_payload->>'return_reason_text' IS NOT NULL
        AND tiktok_return.raw_payload->>'return_reason_text' != ''
    """)

    updated_returns = cr.rowcount
    _logger.info(f"Updated {updated_returns} return records with return_reason_id")
