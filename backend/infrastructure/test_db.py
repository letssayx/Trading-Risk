import sqlite3
from backend.infrastructure.db import engine, Base
# Skip full schema creation for sqlite if it fails on composite PK
# Just need some tables for testing FII data
