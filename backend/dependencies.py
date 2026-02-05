from datetime import datetime, date
from backend.domain.instruments.option import OptionContract, OptionType, OptionStyle
from backend.domain.instruments.asset import UnderlyingAsset
from backend.domain.market.snapshot import MarketSnapshot, InstrumentSnapshot
from backend.domain.market.state import MarketState, SentimentSignal
from backend.orchestration.pipelines.executor import Executor

def get_mock_context():
    asset = UnderlyingAsset(symbol="NIFTY", name="Nifty 50", asset_class="Index")
    option = OptionContract(
        id="NIFTY-ATM", symbol="NIFTY 19500 CE", exchange="NSE", currency="INR",
        contract_size=50, tick_size=0.05, expiry=date(2023, 12, 28),
        strike=19500.0, option_type=OptionType.CALL, style=OptionStyle.EUROPEAN, underlying=asset
    )
    snap = InstrumentSnapshot(
        instrument=option, timestamp=datetime.now(), price=150.0,
        greeks={"delta": 0.5, "gamma": 0.002, "vega": 12.0},
        metadata={"underlying_price": 19500.0}
    )
    market = MarketSnapshot(id="MKT-LIVE-01", timestamp=datetime.now(), instruments={option.id: snap})
    state = MarketState(
        name="Institutional Accumulation",
        timestamp=datetime.now(),
        sentiment=SentimentSignal.BULLISH
    )

    return {
        "current_market": market,
        "current_state": state
    }

def get_executor():
    context = get_mock_context()
    return Executor(context)
