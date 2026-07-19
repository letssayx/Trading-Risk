import sys

filepath = 'backend/ingest/tasks.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if 'completed_map = {}' in line:
        start_idx = i
    if '@shared_task' in line and 'import_nse_latest' in line:
        end_idx = i - 1
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found block from {start_idx} to {end_idx}")

    # We will replace this section with the proper while loop for import_nse_range
    new_logic = """        db = SessionLocal()
        try:
            from backend.ingest.nse_models import ImportLog
            from sqlalchemy import and_

            logs = db.query(ImportLog).filter(
                and_(
                    ImportLog.date >= start_date,
                    ImportLog.date <= end_date,
                    ImportLog.status == 'SUCCESS'
                )
            ).all()

            for log in logs:
                if log.date not in completed_map:
                    completed_map[log.date] = set()
                completed_map[log.date].add(log.pattern)
        except Exception as e:
            logger.warning(f"Could not pre-fetch import logs: {e}")
        finally:
            db.close()

        from datetime import timedelta

        while current_date <= end_date:
            handle_pause()
            if is_cancelled():
                results.append(f"Task cancelled at date {current_date}")
                break

            # Skip weekends (NSE is closed, except for rare special sessions which we'll ignore for bulk)
            if current_date.weekday() >= 5 and not force:
                logger.info(f"Skipping weekend: {current_date}")
                current_date += timedelta(days=1)
                processed_days += 1
                self.update_state(state='PROGRESS', meta={
                    'current_date': current_date.strftime("%Y-%m-%d"),
                    'progress': int((processed_days / total_days) * 100),
                    'message': f"Skipped weekend {current_date - timedelta(days=1)}"
                })
                continue

            patterns_to_run = []
            if force:
                patterns_to_run = target_patterns
            else:
                completed_for_date = completed_map.get(current_date, set())
                for pat in target_patterns:
                    if pat not in completed_for_date:
                        patterns_to_run.append(pat)

            if not patterns_to_run:
                logger.info(f"All requested patterns already completed for {current_date}. Skipping.")
                results.append(f"{current_date}: Already completed")
            else:
                self.update_state(state='PROGRESS', meta={
                    'current_date': current_date.strftime("%Y-%m-%d"),
                    'progress': int((processed_days / total_days) * 100),
                    'message': f"Importing {current_date} ({len(patterns_to_run)} patterns)..."
                })

                try:
                    res = importer.import_date(current_date, patterns_to_run, force=force)
                    results.append(f"{current_date}: {res}")
                except Exception as e:
                    logger.error(f"Error importing {current_date}: {e}")
                    results.append(f"{current_date}: ERROR - {str(e)}")

            current_date += timedelta(days=1)
            processed_days += 1

            self.update_state(state='PROGRESS', meta={
                'current_date': current_date.strftime("%Y-%m-%d"),
                'progress': int((processed_days / total_days) * 100),
                'message': f"Completed {current_date - timedelta(days=1)}"
            })

        # Clear Active Task
        clear_active_task(self.request.id)

        return f"Range import finished: {start_date} to {end_date}. Details: {len(results)} days processed."
    except Exception as e:
        logger.error(f"Error in range import: {e}")
        clear_active_task(self.request.id)
        raise

"""
    lines[start_idx:end_idx] = [new_logic]

    with open(filepath, 'w') as f:
        f.writelines(lines)
    print("Patched tasks.py")
else:
    print("Could not find start or end index.")
