"""Run DB migrations to add last_auto_log_json column"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import create_tables
create_tables()
print("DB tables created/updated OK")