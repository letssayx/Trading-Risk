from sqlalchemy import create_engine, text
engine = create_engine('postgresql://jules@localhost/turtle_terminal')
with engine.connect() as conn:
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='board_meetings';"))
    cols = [r[0] for r in res.fetchall()]
    print("board_meetings columns:", cols)
