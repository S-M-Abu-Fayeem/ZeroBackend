from decimal import Decimal

def _ensure_cleaner_withdrawals_table(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cleaner_withdrawals (
            id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
            cleaner_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            amount DECIMAL(12,2) NOT NULL,
            method VARCHAR(20) NOT NULL,
            destination_account VARCHAR(120) NOT NULL,
            reference_code VARCHAR(80),
            note TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'PROCESSED',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            created_by VARCHAR(36) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_cleaner_withdrawals_cleaner_requested
        ON cleaner_withdrawals(cleaner_id, requested_at DESC)
    """)


def _to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


