import sqlite3

# Connect to database
conn = sqlite3.connect("src/backend/energy_data.db")
cursor = conn.cursor()

print("🗑️  Cleaning energy_readings table...")

# Count before
cursor.execute("SELECT COUNT(*) FROM energy_readings")
count_before = cursor.fetchone()[0]
print(f"Before: {count_before} records")

# Delete all records (since these are just test data)
cursor.execute("DELETE FROM energy_readings")
conn.commit()

# Count after
cursor.execute("SELECT COUNT(*) FROM energy_readings")
count_after = cursor.fetchone()[0]
print(f"After: {count_after} records")

print(f"✅ Deleted {count_before - count_after} records")

# Reset auto-increment (optional, for cleaner IDs)
cursor.execute("DELETE FROM sqlite_sequence WHERE name='energy_readings'")
conn.commit()

conn.close()
print("✅ Database cleaned successfully!")
