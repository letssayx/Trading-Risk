export DATABASE_URL=sqlite:///./test.db # Just to fake a DB to generate migration file
alembic revision --autogenerate -m "Add meeting_date to board_meetings"
