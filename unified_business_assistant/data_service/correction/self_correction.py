import logging
import sqlite3
from typing import Any, List, Optional, Tuple

from db.connection import db_manager
from safety.validator import SQLSafetyValidator
from sql.generator import sql_generator

logger = logging.getLogger("data_service.self_correction")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class SelfCorrectionEngine:
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts

    def execute_with_self_correction(
        self,
        question: str,
        initial_sql: str,
        limit: int = 100,
        request_id: Optional[str] = None,
    ) -> Tuple[List[str], List[List[Any]], Optional[str], bool, Optional[str], List[dict]]:
        req_prefix = f"[{request_id or 'REQ'}]"
        attempt_logs = []
        current_sql = initial_sql
        last_error = None

        for attempt in range(1, self.max_attempts + 1):
            attempt_record = {"attempt": attempt, "sql": current_sql, "status": "pending"}
            logger.info("%s Attempt %d/%d: %s", req_prefix, attempt, self.max_attempts, current_sql)

            try:
                _, validated_sql, _ = SQLSafetyValidator.validate(current_sql)
            except Exception as safety_exc:
                logger.error("%s Attempt %d blocked by validator: %s", req_prefix, attempt, safety_exc)
                attempt_record["status"] = "security_blocked"
                attempt_record["error"] = str(safety_exc)
                attempt_logs.append(attempt_record)
                return [], [], current_sql, False, str(safety_exc), attempt_logs

            current_sql = validated_sql

            try:
                columns, rows, duration_ms = db_manager.execute_query(sql=current_sql, max_rows=limit)
                attempt_record["status"] = "success"
                attempt_record["duration_ms"] = duration_ms
                attempt_record["row_count"] = len(rows)
                attempt_logs.append(attempt_record)
                return columns, rows, current_sql, True, None, attempt_logs

            except (sqlite3.OperationalError, sqlite3.DatabaseError) as db_exc:
                last_error = str(db_exc)
                attempt_record["status"] = "db_error"
                attempt_record["error"] = last_error
                attempt_logs.append(attempt_record)
                logger.warning("%s Attempt %d failed: %s", req_prefix, attempt, last_error)

                if attempt >= self.max_attempts:
                    break

                repaired_sql, rep_ok, _ = sql_generator.correct_sql(
                    question=question,
                    failed_sql=current_sql,
                    db_error=last_error,
                )
                if not rep_ok or not repaired_sql:
                    break

                current_sql = repaired_sql

        user_safe_error = f"Database query execution failed after {len(attempt_logs)} attempt(s): {last_error}"
        return [], [], current_sql, False, user_safe_error, attempt_logs


correction_engine = SelfCorrectionEngine(max_attempts=3)
