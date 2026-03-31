# The fallback looks reasonable, it tries `historical_index_data`, then `bhavcopy_eq`, then `bhavcopy_fo`.
# But `DISTINCT ON` requires the `ORDER BY` to start with the same column, so `ORDER BY trade_date DESC, expiry_date ASC` is valid.
# Wait, `DISTINCT ON (trade_date) trade_date, close_price` but `ORDER BY trade_date DESC`?
# In PostgreSQL, `DISTINCT ON` expression must match the leftmost `ORDER BY` expression.
# So `ORDER BY trade_date DESC` is fine.

# BUT why did the Volatility Analysis tab load empty?
# Let's check the API response for `NIFTY` in `get_pre_expiry_action` by running it via python.
