from sqlalchemy import Column, String, Integer, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid
from backend.domain.market.models import Base

class ParticipantPosition(Base):
    """
    Stores Participant-Wise Open Interest (NSE).
    Partitioned by 'time' in TimescaleDB.
    """
    __tablename__ = 'participant_positions'

    # Composite PK: Time + Participant Type + Instrument Type
    time = Column(DateTime(timezone=True), primary_key=True)
    participant_type = Column(String(20), primary_key=True) # FII, DII, PRO, CLIENT
    instrument_type = Column(String(20), primary_key=True) # INDEX_FUT, STOCK_FUT, INDEX_OPT_CALL, etc.

    # Data
    long_contracts = Column(BigInteger)
    short_contracts = Column(BigInteger)
    net_contracts = Column(BigInteger) # Calculated
