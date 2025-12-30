import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect("src/backend/energy_data.db")

    # Check Schema
    print("\n--- SCHEMA ---")
    schema = pd.read_sql("PRAGMA table_info(energy_readings)", conn)
    print(schema)

    # Check Data
    print("\n--- DATA (Head) ---")
    data = pd.read_sql("SELECT * FROM energy_readings LIMIT 5", conn)
    print(data)

    conn.close()
except Exception as e:
    print(f"Error: {e}")
