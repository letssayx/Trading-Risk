import alembic.config

alembicArgs = [
    '--raiseerr',
    '-c', 'backend/alembic.ini',
    'upgrade', 'head',
]

try:
    alembic.config.main(argv=alembicArgs)
    print("Migration upgraded to head.")
except Exception as e:
    print(f"Error during migration: {e}")
