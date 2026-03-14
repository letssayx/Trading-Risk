with open('backend/web/api/analysis_routes.py', 'r') as f:
    text = f.read()

# Fix pivot 1
old_pivot1 = """    df['net_long'] = df['fut_idx_long'] - df['fut_idx_short']

    pivot = df.pivot_table(index='date', columns='client_type', values='net_long', aggfunc='sum').fillna(0)
    pivot = pivot.reindex(pd.to_datetime(dates)).fillna(0)"""

new_pivot1 = """    df['net_long'] = df['fut_idx_long'] - df['fut_idx_short']

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
        pivot = pd.DataFrame(index=pd.to_datetime(dates))
"""

text = text.replace(old_pivot1, new_pivot1)

# Fix pivot 2
old_pivot2 = """    pivot = df.pivot_table(index='date', columns='category', values='net_value', aggfunc='sum').fillna(0)
    pivot = pivot.reindex(pd.to_datetime(dates)).fillna(0)"""

new_pivot2 = """    try:
        pivot = df.pivot_table(index='date', columns='category', values='net_value', aggfunc='sum').fillna(0)

        if not pivot.index.is_unique:
            pivot = pivot.groupby(level=0).sum()

        dt_dates = pd.to_datetime(dates)
        pivot.index = pd.to_datetime(pivot.index)
        pivot = pivot.reindex(dt_dates).fillna(0)
    except Exception as e:
        import logging
        logging.error(f"Error pivoting cash market flow: {e}")
        pivot = pd.DataFrame(index=pd.to_datetime(dates))"""

text = text.replace(old_pivot2, new_pivot2)

with open('backend/web/api/analysis_routes.py', 'w') as f:
    f.write(text)
