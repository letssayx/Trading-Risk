import os
import redis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def aggressive_kill():
    logger.info("Connecting to Redis to clear task queues...")
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)

        # Clear specific application keys
        r.delete("active_import_task_id")
        r.delete("celery")
        r.delete("unacked")
        r.delete("unacked_index")

        # You can also run flushdb to clear absolutely everything in this redis DB
        # r.flushdb()
        logger.info("Successfully cleared Celery queues from Redis.")
    except Exception as e:
        logger.error(f"Failed to clear Redis: {e}")

    logger.info("Sending SIGKILL to all Celery worker processes...")
    # Kill any python process containing the word celery (broader match)
    result = os.system("pkill -9 -f celery")
    if result == 0:
        logger.info("Successfully killed Celery processes.")
    else:
        logger.info("No active Celery processes found to kill (or already killed).")

    print("\n--- DONE ---")
    print("All tasks have been forcibly killed and queues cleared.")
    print("You can now safely start Celery again without old tasks resuming.")

if __name__ == "__main__":
    aggressive_kill()
