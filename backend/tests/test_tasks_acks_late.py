from backend.ingest.tasks import import_nse_date, import_nse_range, import_nse_latest, prepare_morning_data_task, generate_morning_report_task

def test_tasks_have_acks_late():
    assert import_nse_date.acks_late is True
    assert import_nse_range.acks_late is True
    assert import_nse_latest.acks_late is True
    assert prepare_morning_data_task.acks_late is True
    assert generate_morning_report_task.acks_late is True
