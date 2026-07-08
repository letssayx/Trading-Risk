# Database Migration Script

To apply the database changes for the new `MutualFundHolding` table, please run the following command in your local environment where your TimescaleDB Docker container is accessible:

```bash
PYTHONPATH=. alembic revision --autogenerate -m "Add mutual_fund_holdings table"
PYTHONPATH=. alembic upgrade head
```

If you do not have Alembic configured locally, you can create the table manually with this SQL:

```sql
CREATE TABLE mutual_fund_holdings (
    id UUID PRIMARY KEY,
    report_date DATE NOT NULL,
    fund_house VARCHAR NOT NULL,
    scheme_name VARCHAR NOT NULL,
    asset_category VARCHAR NOT NULL,
    symbol VARCHAR,
    isin VARCHAR,
    instrument_name VARCHAR,
    quantity FLOAT,
    market_value FLOAT,
    percent_to_nav FLOAT,
    position VARCHAR,
    strike_price FLOAT,
    option_type VARCHAR,
    maturity_date DATE,
    yield_pct FLOAT,
    coupon_pct FLOAT,
    benchmark VARCHAR,
    notional_amount FLOAT
);
CREATE INDEX ix_mutual_fund_holdings_report_date ON mutual_fund_holdings (report_date);
CREATE INDEX ix_mutual_fund_holdings_fund_house ON mutual_fund_holdings (fund_house);
CREATE INDEX ix_mutual_fund_holdings_scheme_name ON mutual_fund_holdings (scheme_name);
CREATE INDEX ix_mutual_fund_holdings_asset_category ON mutual_fund_holdings (asset_category);
CREATE INDEX ix_mutual_fund_holdings_symbol ON mutual_fund_holdings (symbol);
CREATE INDEX ix_mutual_fund_holdings_isin ON mutual_fund_holdings (isin);
```
