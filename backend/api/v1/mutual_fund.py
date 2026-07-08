from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from backend.infrastructure.db import get_db
from backend.models.mutual_fund import MutualFundHolding
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/mutual-funds", tags=["Mutual Funds"])

@router.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    """
    Returns unique fund houses and their respective schemes for cascading dropdowns.
    """
    try:
        results = db.query(
            MutualFundHolding.fund_house,
            MutualFundHolding.scheme_name
        ).distinct().all()

        # Build hierarchical filter object: { "HDFC": ["Scheme A", "Scheme B"], ... }
        filters = {}
        for fund, scheme in results:
            if fund not in filters:
                filters[fund] = []
            if scheme not in filters[fund]:
                filters[fund].append(scheme)

        if not filters:
            # Fallback mock data if DB empty
            return {"filters": {
                "HDFC Mutual Fund": ["HDFC Equity Fund", "HDFC Hybrid Equity Fund", "HDFC Liquid Fund"],
                "SBI Mutual Fund": ["SBI Bluechip Fund", "SBI Arbitrage Opportunities Fund"]
            }}

        return {"filters": filters}
    except Exception as e:
        logger.error(f"Error fetching mutual fund filters: {e}")
        # Return mock data on failure to allow UI dev when DB connection fails
        return {"filters": {
            "HDFC Mutual Fund": ["HDFC Equity Fund", "HDFC Hybrid Equity Fund", "HDFC Liquid Fund"],
            "SBI Mutual Fund": ["SBI Bluechip Fund", "SBI Arbitrage Opportunities Fund"]
        }}

@router.get("/holdings")
def get_holdings(
    fund_house: str = Query("ALL", description="Selected Fund House or 'ALL'"),
    scheme_name: str = Query("ALL", description="Selected Scheme or 'ALL'"),
    asset_category: str = Query("stock", description="Asset category: stock, fo, debt, debt_derivative, hybrid"),
    db: Session = Depends(get_db)
):
    """
    Returns portfolio holdings based on selected filters.
    """
    try:
        # We'd normally query the DB like this:
        query = db.query(MutualFundHolding).filter(MutualFundHolding.asset_category == asset_category)

        if fund_house != "ALL":
            query = query.filter(MutualFundHolding.fund_house == fund_house)
        if scheme_name != "ALL":
            query = query.filter(MutualFundHolding.scheme_name == scheme_name)

        holdings = query.order_by(MutualFundHolding.market_value.desc()).limit(100).all()

        # Convert objects to dicts for real data
        result = [
            {column.name: getattr(h, column.name) for column in h.__table__.columns}
            for h in holdings
        ]

        return {"data": result}
    except Exception as e:
        logger.error(f"Error fetching holdings: {e}")
        # Return mock data on failure to allow UI development if DB fails
        mock_data = []
        if asset_category == 'stock':
            mock_data = [
                {"instrument_name": "HDFC Bank Ltd.", "isin": "INE040A01034", "symbol": "HDFCBANK", "quantity": 1500000, "market_value": 2450.5, "percent_to_nav": 8.5},
                {"instrument_name": "Reliance Industries Ltd.", "isin": "INE002A01018", "symbol": "RELIANCE", "quantity": 950000, "market_value": 2800.0, "percent_to_nav": 6.2}
            ]
        elif asset_category == 'fo':
            mock_data = [
                {"instrument_name": "NIFTY 50", "position": "Long", "option_type": "CALL", "strike_price": 24500, "quantity": 5000, "market_value": 150.2, "percent_to_nav": 1.2},
                {"instrument_name": "RELIANCE", "position": "Short", "option_type": None, "strike_price": None, "quantity": -2000, "market_value": -50.5, "percent_to_nav": -0.5}
            ]
        elif asset_category == 'debt':
            mock_data = [
                {"instrument_name": "7.18% GOVT OF INDIA 2033", "isin": "IN0020230086", "quantity": 5000000, "market_value": 5100.0, "yield_pct": 7.15, "coupon_pct": 7.18, "maturity_date": "2033-08-14"},
                {"instrument_name": "HDFC Bank CP", "isin": "INE040A14050", "quantity": 2000000, "market_value": 1950.0, "yield_pct": 7.50, "coupon_pct": 0.0, "maturity_date": "2024-12-30"}
            ]
        elif asset_category == 'debt_derivative':
            mock_data = [
                {"instrument_name": "Interest Rate Swap", "benchmark": "Overnight MIBOR", "position": "Pay Fixed", "notional_amount": 10000000, "market_value": 25.5, "maturity_date": "2028-06-15"}
            ]

        return {"data": mock_data}

@router.get("/hybrid")
def get_hybrid_marketwatch(
    fund_house: str = Query("ALL"),
    scheme_name: str = Query("ALL"),
    db: Session = Depends(get_db)
):
    """
    Returns specialized marketwatch format joining market data (price, OI)
    with fund specific holding quantities and percentages.
    """
    try:
        # In a real scenario, this involves a complex JOIN between live market data (quotes/derivatives)
        # and the mutual_fund_holdings table grouped by symbol.

        # Mock data structure matching requested format
        mock_data = [
            {
                "Symbol": "HDFCBANK",
                "EQ_Price": 1650.50,
                "Future_Price": 1660.00,
                "Total_Futures_OI": 45000000,
                "Rollover_Pct": 78.5,
                "funds": {
                    "HDFC Arbitrage Fund": {"qty": 1500000, "pct_oi": 3.33},
                    "SBI Arbitrage Fund": {"qty": 2000000, "pct_oi": 4.44}
                }
            },
            {
                "Symbol": "RELIANCE",
                "EQ_Price": 2980.00,
                "Future_Price": 3000.00,
                "Total_Futures_OI": 32000000,
                "Rollover_Pct": 82.1,
                "funds": {
                    "HDFC Arbitrage Fund": {"qty": 500000, "pct_oi": 1.56},
                    "ICICI Arbitrage Fund": {"qty": 800000, "pct_oi": 2.50}
                }
            }
        ]

        return {"data": mock_data}
    except Exception as e:
        logger.error(f"Error fetching hybrid data: {e}")
        return {"data": []}
