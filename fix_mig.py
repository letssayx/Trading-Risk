with open('alembic/versions/create_eq_vol_deliv_cols.py', 'r') as f:
    text = f.read()

text = text.replace('\\"\\"\\"', '\"\"\"')

with open('alembic/versions/create_eq_vol_deliv_cols.py', 'w') as f:
    f.write(text)
print("Fixed syntax error")
