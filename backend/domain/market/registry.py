from typing import List, Optional
from backend.domain.market.schemas import InstrumentSchema

class MarketRegistry:
    def __init__(self, db_session=None):
        self.db_session = db_session

    def search_instruments(self, query: str) -> List[InstrumentSchema]:
        """
        Fuzzy search for instruments using trigram similarity (mocked).
        In prod, this would execute:
        SELECT * FROM instruments WHERE symbol % :query ORDER BY similarity(symbol, :query) DESC
        """
        print(f"Searching Market Registry for: {query}")

        # Mock Response
        if "NIFTY" in query.upper():
            return [
                InstrumentSchema(
                    turtle_id="NIFTY_FUT_NEAR",
                    symbol="NIFTY",
                    exchange="NSE",
                    exchange_mapping={"NSE": "NIFTY23DECFUT"}
                )
            ]
        return []

    def register_instrument(self, instrument: InstrumentSchema):
        """
        Registers a new instrument in the system.
        """
        print(f"Registering Instrument: {instrument.turtle_id}")
        # In prod: session.add(InstrumentModel(...)); session.commit()
