import re

with open("backend/web/api/analysis_routes.py", "r") as f:
    content = f.read()

# Replace the part defining df in get_participant_oi
new_df = """    df = pd.DataFrame([{
        'date': r.trade_date,
        'client_type': r.client_type,
        'fut_idx_net': r.future_index_long - r.future_index_short,
        'fut_stk_net': r.future_stock_long - r.future_stock_short,
        'opt_idx_net': (r.option_index_call_long - r.option_index_call_short) + (r.option_index_put_long - r.option_index_put_short),
        'opt_stk_net': (r.option_stock_call_long - r.option_stock_call_short) + (r.option_stock_put_long - r.option_stock_put_short)
    } for r in records])

    if df.empty:
         today = date.today()
         dummy_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
         return {
             "dates": dummy_dates,
             "fii_fut_idx": np.random.randint(-50000, 50000, days).tolist(),
             "fii_fut_stk": np.random.randint(-50000, 50000, days).tolist(),
             "fii_opt_idx": np.random.randint(-50000, 50000, days).tolist(),
             "fii_opt_stk": np.random.randint(-50000, 50000, days).tolist(),
             "pro_fut_idx": np.random.randint(-30000, 30000, days).tolist(),
             "client_fut_idx": np.random.randint(-80000, 80000, days).tolist(),
             "nifty_close": np.random.uniform(20000, 22000, days).tolist()
         }

    # Handle pandas duplicate index/axis reindex issues
    try:
        pivot_idx = df.pivot_table(index='date', columns='client_type', values='fut_idx_net', aggfunc='sum').fillna(0)
        pivot_stk = df.pivot_table(index='date', columns='client_type', values='fut_stk_net', aggfunc='sum').fillna(0)
        pivot_opt_idx = df.pivot_table(index='date', columns='client_type', values='opt_idx_net', aggfunc='sum').fillna(0)
        pivot_opt_stk = df.pivot_table(index='date', columns='client_type', values='opt_stk_net', aggfunc='sum').fillna(0)

        if not pivot_idx.index.is_unique:
            pivot_idx = pivot_idx.groupby(level=0).sum()
            pivot_stk = pivot_stk.groupby(level=0).sum()
            pivot_opt_idx = pivot_opt_idx.groupby(level=0).sum()
            pivot_opt_stk = pivot_opt_stk.groupby(level=0).sum()

        dt_dates = pd.to_datetime(dates)
        pivot_idx.index = pd.to_datetime(pivot_idx.index)
        pivot_stk.index = pd.to_datetime(pivot_stk.index)
        pivot_opt_idx.index = pd.to_datetime(pivot_opt_idx.index)
        pivot_opt_stk.index = pd.to_datetime(pivot_opt_stk.index)

        pivot_idx = pivot_idx.reindex(dt_dates).fillna(0)
        pivot_stk = pivot_stk.reindex(dt_dates).fillna(0)
        pivot_opt_idx = pivot_opt_idx.reindex(dt_dates).fillna(0)
        pivot_opt_stk = pivot_opt_stk.reindex(dt_dates).fillna(0)
    except Exception as e:
        import logging
        logging.error(f"Error pivoting participant oi: {e}")
        pivot_idx = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_stk = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_idx = pd.DataFrame(index=pd.to_datetime(dates))
        pivot_opt_stk = pd.DataFrame(index=pd.to_datetime(dates))"""

old_df = """    df = pd.DataFrame([{
        'date': r.trade_date,
        'client_type': r.client_type,
        'fut_idx_long': r.future_index_long,
        'fut_idx_short': r.future_index_short
    } for r in records])

    if df.empty:
         today = date.today()
         dummy_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
         return {
             "dates": dummy_dates,
             "fii_net_long": np.random.randint(-50000, 50000, days).tolist(),
             "pro_net_long": np.random.randint(-30000, 30000, days).tolist(),
             "client_net_long": np.random.randint(-80000, 80000, days).tolist(),
             "nifty_close": np.random.uniform(20000, 22000, days).tolist()
         }

    df['net_long'] = df['fut_idx_long'] - df['fut_idx_short']

    # Handle pandas duplicate index/axis reindex issues
    # Ensure dates is exactly datetime format before reindexing
    try:
        pivot = df.pivot_table(index='date', columns='client_type', values='net_long', aggfunc='sum').fillna(0)

        # Ensure dates index is unique and datetime type
        if not pivot.index.is_unique:
            pivot = pivot.groupby(level=0).sum()

        dt_dates = pd.to_datetime(dates)
        pivot.index = pd.to_datetime(pivot.index)

        pivot = pivot.reindex(dt_dates).fillna(0)
    except Exception as e:
        import logging
        logging.error(f"Error pivoting participant oi: {e}")
        # fallback safe
        pivot = pd.DataFrame(index=pd.to_datetime(dates))"""

content = content.replace(old_df, new_df)

old_ret = """    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot.index],
        "fii_net_long": pivot.get('FII', pd.Series(0, index=pivot.index)).tolist(),
        "pro_net_long": pivot.get('PRO', pd.Series(0, index=pivot.index)).tolist(),
        "client_net_long": pivot.get('Client', pd.Series(0, index=pivot.index)).tolist(),
        "nifty_close": nifty_close_list
    }"""

new_ret = """    return {
        "dates": [d.strftime('%Y-%m-%d') for d in pivot_idx.index],
        "fii_fut_idx": pivot_idx.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_fut_stk": pivot_stk.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_idx": pivot_opt_idx.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "fii_opt_stk": pivot_opt_stk.get('FII', pd.Series(0, index=pivot_idx.index)).tolist(),
        "pro_fut_idx": pivot_idx.get('PRO', pd.Series(0, index=pivot_idx.index)).tolist(),
        "client_fut_idx": pivot_idx.get('Client', pd.Series(0, index=pivot_idx.index)).tolist(),
        "nifty_close": nifty_close_list
    }"""

content = content.replace(old_ret, new_ret)

with open("backend/web/api/analysis_routes.py", "w") as f:
    f.write(content)
