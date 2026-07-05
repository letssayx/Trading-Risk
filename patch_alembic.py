with open('alembic/versions/018_fix_corp_actions_bm_constraints.py', 'r') as f:
    content = f.read()

content = content.replace("revision = '018_fix_corp_actions_bm_constraints'", "revision = '018_fix_corp_actions'")
content = content.replace("down_revision = '017_add_uq_historical_atm_iv_unique'", "down_revision = '017_uq_atm_iv'")

with open('alembic/versions/018_fix_corp_actions_bm_constraints.py', 'w') as f:
    f.write(content)
