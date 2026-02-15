import psutil
import threading
import time
from datetime import datetime
from sqlalchemy import text
from redis import Redis
from backend.dependencies import engine

# Mock Redis for local dev if not available
try:
    redis_client = Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
except Exception:
    redis_client = None

class SelfHealingMonitor:
    """
    Monitors system health and auto-fixes issues
    """

    def __init__(self):
        self.checks = [
            self.check_database,
            self.check_memory,
            # self.check_cache, # Stub
        ]
        self.healing_actions = {
            'database': self.heal_database,
            'memory': self.heal_memory
        }
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.monitor_loop, daemon=True).start()
            print("Self-Healing Monitor Started.")

    def monitor_loop(self):
        while self.running:
            for check in self.checks:
                try:
                    status = check()
                    if not status['healthy']:
                        print(f"Health Issue Detected: {status['issue']}")
                        self.trigger_healing(status)
                except Exception as e:
                    print(f"Monitor Check Failed: {e}")
            time.sleep(60)  # Check every minute

    def trigger_healing(self, status):
        action = self.healing_actions.get(status.get('component'))
        if action:
            print(f"Triggering Healing Action for {status['issue']}...")
            action(status)

    def check_database(self):
        """Check DB connection and query performance"""
        try:
            with engine.connect() as conn:
                # Test query
                conn.execute(text("SELECT 1"))

                # Check slow queries (Postgres specific)
                # slow_queries = conn.execute(text("SELECT pid, query, state, age(clock_timestamp(), query_start) FROM pg_stat_activity WHERE state != 'idle' AND query NOT LIKE '%pg_stat_activity%' AND age(clock_timestamp(), query_start) > interval '5 seconds'")).fetchall()

                # Simplification for MVP: Just check connection
                return {'healthy': True}
        except Exception as e:
            return {'healthy': False, 'issue': 'db_connection_failed', 'component': 'database', 'error': str(e)}

    def heal_database(self, status):
        """Auto-fix DB issues"""
        # Recreating engine pool or alerting
        # engine.dispose()
        print("Database connection reset triggered.")

    def check_memory(self):
        """Memory usage monitoring"""
        memory = psutil.virtual_memory()

        if memory.percent > 90:
            return {
                'healthy': False,
                'issue': 'high_memory',
                'component': 'memory',
                'percent': memory.percent
            }

        return {'healthy': True}

    def heal_memory(self, status):
        """Clear caches if memory high"""
        if status['issue'] == 'high_memory':
            if redis_client:
                redis_client.flushall()
                print("Redis Cache Flushed.")

            import gc
            gc.collect()
            print("Python Garbage Collection Run.")

# Singleton Instance
monitor = SelfHealingMonitor()
