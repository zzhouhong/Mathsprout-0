import sqlite3, os
db_path = os.path.join(os.path.dirname(__file__), "mathsprout.db")
print(f"DB size: {os.path.getsize(db_path)} bytes")
conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {tables}")
conn.close()
