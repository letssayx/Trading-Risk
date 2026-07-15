+++ b/backend/ingest/tasks.py
@@ -0,0 +1,702 @@
+from celery import shared_task
+from celery.utils.log import get_task_logger
+from datetime import datetime, timedelta
+from typing import List, Optional
+
+from backend.ingest.nse_importer import NSEDataImporter
+from backend.ingest.date_utils import NSEHolidayCalendar
+from backend.ingest.nse_models import ImportLog
+from backend.infrastructure.db import SessionLocal
+import redis
+import os
+
+logger = get_task_logger(__name__)
+
+
+def check_pause_flag(task_id: str) -> bool:
+    import redis
+    import os
+    try:
+        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
+        r = redis.from_url(redis_url)
+        return r.exists(f"pause_task_{task_id}") > 0
+    except Exception:
+        return False
+
+
+def set_active_task(task_id: str):
+    try:
+        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
+        r = redis.from_url(redis_url)
+        r.set("active_import_task_id", task_id)
+    except Exception:
+        pass
+
+def clear_active_task(task_id: str):
+    try:
+        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
+        r = redis.from_url(redis_url)
+        # Only delete if it's the current task
+        curr = r.get("active_import_task_id")
+        if curr and curr.decode('utf-8') == task_id:
+            r.delete("active_import_task_id")
+    except Exception:
+        pass
+
+def check_cancel_flag(task_id: str) -> bool:
+    try:
+        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
+        r = redis.from_url(redis_url)
+        return r.exists(f"cancel_task_{task_id}") > 0
+    except Exception:
+        return False
+
+# Use shared_task decorator for integration with main Celery app
+@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.import_nse_date')
+def import_nse_date(self, date_str: str, patterns: Optional[List[str]] = None, force: bool = False, include_non_fo: bool = False, specific_symbol: Optional[str] = None):
+    """Import NSE data for a specific date."""
+    set_active_task(self.request.id)
+
+    # Progress callback to update Celery state
+    def progress_callback(progress_dict: dict):
+        self.update_state(state='PROGRESS', meta=progress_dict)
+        handle_pause()
+        logger.info(f"Task Progress: {progress_dict}")
+        handle_pause()
+
+    def is_cancelled():
+        return check_cancel_flag(self.request.id)
+
+    def handle_pause():
+        import time
+        if check_pause_flag(self.request.id):
+            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
+            while check_pause_flag(self.request.id):
+                if is_cancelled():
+                    break
+                time.sleep(5)
+            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})
+
+    try:
+        if isinstance(date_str, str):
+            trade_date = datetime.strptime(date_str, "%Y-%m-%d").date()
+        else:
+            trade_date = date_str
+
+        logger.info(f"Starting import for {trade_date}")
+        importer = NSEDataImporter()
+        result = importer.import_date(
+            trade_date,
+            patterns=patterns,
+            force=force,
+            progress_callback=progress_callback,
+            check_cancel=is_cancelled,
+            include_non_fo=include_non_fo,
+            specific_symbol=specific_symbol
+        )
+        if result.get('status') == 'ABORTED':
+            self.update_state(state='REVOKED', meta={'exc_type': 'Abort', 'exc_message': 'Aborted by user'})
+            return {"status": "ABORTED"}
+        clear_active_task(self.request.id)
+        return result
+
+    except Exception as exc:
+        if self.request.retries >= self.max_retries:
+            err_msg = str(exc)
+            logger.error(f"Max retries exceeded for date import: {err_msg}")
+            self.update_state(state='FAILURE', meta={"exc_type": "Exception", "exc_message": f"Date Import Failed: {err_msg}"})
+            raise Exception(f"Date Import Failed: {err_msg}")
+
+        logger.error(f"Import failed: {exc}. Retrying... ({self.request.retries}/3)")
+        self.retry(exc=Exception(str(exc)), countdown=60)  # Convert complex exceptions to string explicitly before retry
+
+from celery import shared_task
+
+@shared_task(bind=True, acks_late=True, name="evaluate_ai_predictions")
+def evaluate_ai_predictions(self):
+    """
+    Background worker that runs (e.g., at 9:15 AM) to evaluate all pending AI predictions
+    by fetching the latest actual opening price and calculating accuracy.
+    """
+    from backend.infrastructure.db import SessionLocal
+    from backend.ingest.nse_models import AIPrediction, BhavcopyEQ
+    from sqlalchemy import select, desc
+
+    db = SessionLocal()
+    try:
+        # Find all predictions without an actual_price
+        pending = db.query(AIPrediction).filter(AIPrediction.actual_price.is_(None)).all()
+        updated_count = 0
+
+        for pred in pending:
+            # Look up the latest open price for the ticker
+            latest_eq = db.execute(
+                select(BhavcopyEQ.open_price)
+                .filter(BhavcopyEQ.symbol == pred.ticker)
+                .order_by(desc(BhavcopyEQ.trade_date))
+                .limit(1)
+            ).scalar_one_or_none()
+
+            if latest_eq:
+                pred.actual_price = latest_eq
+                updated_count += 1
+
+        if updated_count > 0:
+            db.commit()
+
+        return {"status": "SUCCESS", "evaluated_count": updated_count}
+    except Exception as e:
+        db.rollback()
+        raise e
+    finally:
+        db.close()
+
+
+@shared_task(bind=True, max_retries=3, acks_late=True, name='backend.ingest.tasks.retry_failed_imports')
+def retry_failed_imports(self, pattern: str):
+    """Retry all failed dates for a specific table pattern."""
+    set_active_task(self.request.id)
+
+    def is_cancelled():
+        return check_cancel_flag(self.request.id)
+
+    def handle_pause():
+        import time
+        if check_pause_flag(self.request.id):
+            self.update_state(state='PROGRESS', meta={'status': 'PAUSED', 'message': 'Task is paused. Waiting to resume...'})
+            while check_pause_flag(self.request.id):
+                if is_cancelled():
+                    break
+                time.sleep(5)
+            self.update_state(state='PROGRESS', meta={'status': 'RESUMED', 'message': 'Task resumed.'})
+
+    try:
+        from backend.infrastructure.db import SessionLocal
+        from backend.models.audit import SystemLog
+
+        db = SessionLocal()
+
+        # In the audit logs, successful jobs record "Imported <pattern> for <date>"
+        # Failed jobs record "Failed to import <pattern> for <date>" or similar,
+        # but in our frontend stats endpoint we use the fact that they have level='ERROR'.
+        # However, a cleaner way is just to rely on the backend stats query logic or query the DB directly.
+        # But for robustness, we can just fetch all dates that have an ERROR for this pattern
+        # and do NOT have a subsequent SUCCESS.
+
+        from sqlalchemy import text
+        # Simplest approach: Query the exact same `get_import_stats` SQL logic, or just a custom SQL
+        sql = text("""
+            SELECT DISTINCT (meta_data->>'date')::date AS error_date
+            FROM system_logs
+            WHERE source = 'Importer'
+            AND level = 'ERROR'
+            AND meta_data->>'pattern' = :pattern
+            AND (meta_data->>'date') IS NOT NULL
+            AND NOT EXISTS (
+                SELECT 1 FROM system_logs success_logs
+                WHERE success_logs.source = 'Importer'
+                AND success_logs.level = 'INFO'
+                AND success_logs.meta_data->>'pattern' = :pattern
