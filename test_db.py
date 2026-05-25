from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.ingest.nse_models import BoardMeeting, CorporateAction

engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')
Session = sessionmaker(bind=engine)
session = Session()

bms = session.query(BoardMeeting.symbol, BoardMeeting.broadcast_date).limit(5).all()
print("BoardMeetings:", bms)

cas = session.query(CorporateAction.symbol, CorporateAction.broadcast_date).limit(5).all()
print("CorporateActions:", cas)
