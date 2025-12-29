"""
Database Viewer - Simple tool to view SQLite database in table format
Usage: python view_db.py [options]
"""

import sqlite3
import sys
from datetime import datetime
from typing import List, Dict
from database import get_db


class DatabaseViewer:
    """Simple database viewer with formatted table output"""

    def __init__(self, db_path: str = "energy_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.db_path = db_path

    def print_table(self, rows: List[sqlite3.Row], title: str = ""):
        """Print rows in formatted table"""
        if not rows:
            print(f"\n📋 {title}")
            print("   (No data)")
            return

        # Get column names
        columns = rows[0].keys()

        # Calculate column widths
        widths = {}
        for col in columns:
            widths[col] = len(col)
            for row in rows:
                val = str(row[col]) if row[col] is not None else "NULL"
                widths[col] = max(widths[col], len(val))

        # Print title
        if title:
            print(f"\n📋 {title}")

        # Print header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        separator = "-+-".join("-" * widths[col] for col in columns)

        print(" " + header)
        print(" " + separator)

        # Print rows
        for row in rows:
            values = []
            for col in columns:
                val = str(row[col]) if row[col] is not None else "NULL"
                values.append(val.ljust(widths[col]))
            print(" " + " | ".join(values))

        print(f"\n   Total: {len(rows)} rows\n")

    def show_stats(self):
        """Show database statistics"""
        db = get_db()
        stats = db.get_stats()

        print("\n" + "=" * 60)
        print("📊 DATABASE STATISTICS")
        print("=" * 60)
        print(f"  Database Path: {stats['db_path']}")
        print(f"  Total Readings: {stats['total_readings']:,}")
        print(f"  Monthly Summaries: {stats['monthly_summaries']}")
        print(f"  Yearly Summaries: {stats['yearly_summaries']}")

        if stats["oldest_reading"]:
            print(f"  Oldest Reading: {stats['oldest_reading']}")
        if stats["newest_reading"]:
            print(f"  Newest Reading: {stats['newest_reading']}")

        print("=" * 60)

    def show_tables(self):
        """List all tables"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = cursor.fetchall()

        print("\n📚 TABLES:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   • {table[0]:<30} ({count:,} rows)")

    def show_latest_readings(self, limit: int = 10):
        """Show latest energy readings"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                plant_id,
                plant_name,
                timestamp,
                current_kw,
                rate_a_kw,
                rate_b_kw,
                rate_c_kw,
                is_peak_time,
                control_line,
                source
            FROM energy_readings
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        self.print_table(rows, f"Latest {limit} Energy Readings")

    def show_monthly_summaries(self, limit: int = 10):
        """Show monthly peak summaries"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT 
                plant_id,
                plant_name,
                year,
                month,
                max_demand_kw,
                avg_demand_kw,
                control_line,
                times_exceeded,
                utilization_pct,
                compliance_score
            FROM monthly_peak_summary
            ORDER BY year DESC, month DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()
        self.print_table(rows, f"Latest {limit} Monthly Summaries")

    def show_plant_summary(self, plant_id: str):
        """Show summary for specific plant"""
        cursor = self.conn.cursor()

        # Latest reading
        cursor.execute(
            """
            SELECT * FROM energy_readings
            WHERE plant_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (plant_id,),
        )
        latest = cursor.fetchall()
        if latest:
            self.print_table(latest, f"Latest Reading - Plant {plant_id}")

        # Recent readings
        cursor.execute(
            """
            SELECT 
                timestamp,
                current_kw,
                rate_a_kw,
                rate_b_kw,
                rate_c_kw,
                is_peak_time
            FROM energy_readings
            WHERE plant_id = ?
            ORDER BY timestamp DESC
            LIMIT 5
        """,
            (plant_id,),
        )
        readings = cursor.fetchall()
        if readings:
            self.print_table(readings, f"Recent Readings - Plant {plant_id}")

    def interactive_menu(self):
        """Interactive menu"""
        while True:
            print("\n" + "=" * 60)
            print("🔍 DATABASE VIEWER - Interactive Menu")
            print("=" * 60)
            print("  1. Show Statistics")
            print("  2. List Tables")
            print("  3. Show Latest Readings")
            print("  4. Show Monthly Summaries")
            print("  5. Show Plant Summary (by ID)")
            print("  6. Custom Query")
            print("  0. Exit")
            print("=" * 60)

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self.show_stats()
            elif choice == "2":
                self.show_tables()
            elif choice == "3":
                limit = input("How many rows? [10]: ").strip() or "10"
                self.show_latest_readings(int(limit))
            elif choice == "4":
                limit = input("How many months? [10]: ").strip() or "10"
                self.show_monthly_summaries(int(limit))
            elif choice == "5":
                plant_id = input("Plant ID: ").strip()
                if plant_id:
                    self.show_plant_summary(plant_id)
            elif choice == "6":
                query = input("SQL Query: ").strip()
                if query:
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        self.print_table(rows, "Query Results")
                    except Exception as e:
                        print(f"❌ Error: {e}")
            elif choice == "0":
                print("\n👋 Goodbye!\n")
                break
            else:
                print("❌ Invalid option")

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Main function"""
    viewer = DatabaseViewer()

    if len(sys.argv) > 1:
        # Command line mode
        cmd = sys.argv[1].lower()

        if cmd == "stats":
            viewer.show_stats()
        elif cmd == "tables":
            viewer.show_tables()
        elif cmd == "readings":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            viewer.show_latest_readings(limit)
        elif cmd == "monthly":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            viewer.show_monthly_summaries(limit)
        elif cmd == "plant":
            if len(sys.argv) > 2:
                viewer.show_plant_summary(sys.argv[2])
            else:
                print("Usage: python view_db.py plant <plant_id>")
        elif cmd == "help":
            print("\n📖 Database Viewer - Help")
            print("\nUsage:")
            print("  python view_db.py              # Interactive menu")
            print("  python view_db.py stats        # Show statistics")
            print("  python view_db.py tables       # List tables")
            print("  python view_db.py readings [N] # Show N latest readings")
            print("  python view_db.py monthly [N]  # Show N monthly summaries")
            print("  python view_db.py plant <ID>   # Show plant summary")
            print()
        else:
            print(f"Unknown command: {cmd}")
            print("Use 'python view_db.py help' for usage")
    else:
        # Interactive mode
        try:
            viewer.interactive_menu()
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")

    viewer.close()


if __name__ == "__main__":
    main()
