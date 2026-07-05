import re

with open('backend/web/api/nse_routes.py', 'r') as f:
    content = f.read()

# Add a force-kill-all route so the user doesn't need task_id
patch = """
@router.post("/ingest/import/force-kill-all")
async def force_kill_all_import_tasks():
    \"\"\"
    Forcefully Terminate ALL running Celery tasks.
    \"\"\"
    try:
        from backend.celery_worker import app as celery_app
        # This will forcefully kill all active tasks
        i = celery_app.control.inspect()
        active_tasks = i.active()
        killed = 0
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    celery_app.control.revoke(task['id'], terminate=True, signal='SIGKILL')
                    killed += 1
        return {"success": True, "message": f"Forcefully terminated {killed} tasks."}
    except Exception as e:
        logger.error(f"Failed to force kill all tasks: {e}")
        raise HTTPException(status_code=500, detail={"message": "Failed to force kill all tasks", "error": str(e)})
"""

if "force_kill_all_import_tasks" not in content:
    content = content.replace("@router.post(\"/ingest/import/force-kill/{task_id}\")", patch + "\n@router.post(\"/ingest/import/force-kill/{task_id}\")")
    with open('backend/web/api/nse_routes.py', 'w') as f:
        f.write(content)
