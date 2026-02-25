"""
backend/nselib/__init__.py
"""
from .lib import NseSession
from .capital_market import CapitalMarket
from .derivatives import Derivatives

class NSELibClient:
    """
    Unified client for NSE data access.
    """
    def __init__(self):
        self.session = NseSession()
        self.capital_market = CapitalMarket(self.session)
        self.derivatives = Derivatives(self.session)

    def get_bhavcopy_eq(self, trade_date):
        return self.capital_market.bhav_copy_equities(trade_date)

    def get_bhavcopy_fo(self, trade_date):
        return self.derivatives.fno_bhav_copy(trade_date)

    def get_bulk_deals(self, trade_date):
        return self.capital_market.bulk_deal_data(trade_date)

    def get_block_deals(self, trade_date):
        return self.capital_market.block_deals_data(trade_date)

    def get_fao_participant_oi(self, trade_date):
        return self.derivatives.participant_wise_open_interest(trade_date)

    def get_fii_derivatives_stats(self, trade_date):
        return self.derivatives.fii_derivatives_statistics(trade_date)

    def get_fo_volatility(self, trade_date):
        return self.derivatives.fo_volatility(trade_date)

    def get_mto_delivery(self, trade_date):
        return self.capital_market.deliverable_position_data(trade_date)

    def get_mwpl(self, trade_date):
        return self.capital_market.market_watch_all_indices(trade_date)
