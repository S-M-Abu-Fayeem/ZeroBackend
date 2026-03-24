import os
import time

from models import db_connection, setup_database


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    should_bootstrap = _to_bool(os.getenv("AUTO_SETUP_DATABASE_ON_START", "true"))
    if not should_bootstrap:
        print("AUTO_SETUP_DATABASE_ON_START is false. Skipping database bootstrap.")
        return 0

    retries = int(os.getenv("DB_BOOTSTRAP_RETRIES", "10"))
    retry_delay_seconds = int(os.getenv("DB_BOOTSTRAP_RETRY_DELAY", "3"))

    for attempt in range(1, retries + 1):
        try:
            print(f"Bootstrapping database (attempt {attempt}/{retries})...")
            db_connection.create_pool()
            setup_database()
            print("Database bootstrap completed successfully.")
            return 0
        except Exception as exc:
            print(f"Database bootstrap failed on attempt {attempt}: {exc}")
            if attempt == retries:
                return 1
            time.sleep(retry_delay_seconds)
        finally:
            try:
                db_connection.close_pool()
            except Exception:
                pass

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
