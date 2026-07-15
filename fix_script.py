with open("backend/ingest/tasks.py", "r") as f:
    content = f.read()

with open("extracted_task.py", "r") as f:
    task_code = f.read()

decorator = "@shared_task(bind=True, max_retries=3, acks_late=True, reject_on_worker_lost=True)\n"

# Insert the task before `def run_mwpl_analysis_task`
insert_index = content.find("@shared_task(bind=True, acks_late=True)\ndef run_mwpl_analysis_task")

new_content = content[:insert_index] + decorator + task_code + "\n" + content[insert_index:]

with open("backend/ingest/tasks.py", "w") as f:
    f.write(new_content)
