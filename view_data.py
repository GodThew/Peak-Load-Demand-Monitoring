import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect("src/backend/energy_data.db")

print("=" * 80)
print("📊 ENERGY DATA VIEWER")
print("=" * 80)

# Show all tables
print("\n📁 Available Tables:")
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(tables)

# View energy_readings
print("\n⚡ ENERGY READINGS (Latest 10 records):")
print("-" * 80)
try:
    df = pd.read_sql(
        """
        SELECT id, plant_id, timestamp, current_kw, 
               is_peak_time, plant_name, source
        FROM energy_readings 
        ORDER BY timestamp DESC 
        LIMIT 10
    """,
        conn,
    )

    if len(df) > 0:
        print(df.to_string(index=False))
        print(f"\n✅ Total records: {len(df)}")
    else:
        print("⚠️  No data found")
except Exception as e:
    print(f"❌ Error: {e}")

# View monthly summary
print("\n\n📅 MONTHLY PEAK SUMMARY:")
print("-" * 80)
try:
    df_monthly = pd.read_sql(
        """
        SELECT plant_id, plant_name, year, month, 
               max_demand_kw, control_line, times_exceeded
        FROM monthly_peak_summary 
        ORDER BY year DESC, month DESC 
        LIMIT 10
    """,
        conn,
    )

    if len(df_monthly) > 0:
        print(df_monthly.to_string(index=False))
    else:
        print("⚠️  No data found (table is empty)")
except Exception as e:
    print(f"❌ Error: {e}")

conn.close()
print("\n" + "=" * 80)
