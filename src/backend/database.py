"""
Database Manager for Peak Load Demand Monitoring
Handles SQLite storage for historical energy data and analytics
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import json


class Database:
    """SQLite database manager for energy readings and summaries"""

    def __init__(self, db_path: str = "energy_data.db"):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Table 1: Raw energy readings (15-min intervals)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS energy_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    
                    -- PEA Data
                    current_kw REAL NOT NULL,
                    rate_a_kw REAL DEFAULT 0,
                    rate_b_kw REAL DEFAULT 0,
                    rate_c_kw REAL DEFAULT 0,
                    
                    -- Context
                    is_peak_time BOOLEAN,
                    control_line REAL,
                    plant_type TEXT,
                    plant_name TEXT,
                    
                    -- Metadata
                    scraped_at DATETIME,
                    source TEXT DEFAULT 'pea_amr',
                    
                    -- Unique constraint
                    UNIQUE(plant_id, timestamp)
                )
            """)

            # Indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_plant_timestamp 
                ON energy_readings(plant_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON energy_readings(timestamp DESC)
            """)

            # Table 2: Monthly peak summaries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monthly_peak_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id TEXT NOT NULL,
                    plant_name TEXT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    
                    -- Peak Metrics
                    max_demand_kw REAL,
                    max_demand_timestamp DATETIME,
                    avg_demand_kw REAL,
                    min_demand_kw REAL,
                    
                    -- Peak Time Analysis
                    max_peak_time_kw REAL,
                    avg_peak_time_kw REAL,
                    peak_time_hours INTEGER,
                    
                    -- Control Line Compliance
                    control_line REAL,
                    times_exceeded INTEGER,
                    max_excess_kw REAL,
                    avg_excess_kw REAL,
                    
                    -- Reduction Metrics
                    previous_month_peak REAL,
                    reduction_vs_previous_kw REAL,
                    reduction_vs_previous_pct REAL,
                    reduction_vs_control_kw REAL,
                    reduction_vs_control_pct REAL,
                    
                    -- Calculated metrics
                    utilization_pct REAL,
                    compliance_score REAL,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(plant_id, year, month)
                )
            """)

            # Table 3: Yearly summaries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS yearly_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plant_id TEXT NOT NULL,
                    plant_name TEXT,
                    year INTEGER NOT NULL,
                    
                    -- Annual Peak
                    max_demand_kw REAL,
                    max_demand_month INTEGER,
                    max_demand_timestamp DATETIME,
                    
                    -- Averages
                    avg_monthly_peak_kw REAL,
                    avg_demand_kw REAL,
                    
                    -- Yearly Metrics
                    total_violations INTEGER,
                    avg_reduction_vs_control_pct REAL,
                    best_month_reduction_kw REAL,
                    worst_month_reduction_kw REAL,
                    
                    -- Targets
                    control_line REAL,
                    achieved_target BOOLEAN,
                    
                    -- Year-over-Year
                    previous_year_peak REAL,
                    yoy_reduction_kw REAL,
                    yoy_reduction_pct REAL,
                    
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(plant_id, year)
                )
            """)

            print(f"✅ Database initialized: {self.db_path}")

    # ==================== INSERT OPERATIONS ====================

    def insert_reading(self, data: Dict) -> bool:
        """Insert a single energy reading"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO energy_readings 
                    (plant_id, timestamp, current_kw, rate_a_kw, rate_b_kw, rate_c_kw,
                     is_peak_time, control_line, plant_type, plant_name, scraped_at, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data.get("plant_id"),
                        data.get("timestamp"),
                        data.get("current_kw"),
                        data.get("rate_a_kw", 0),
                        data.get("rate_b_kw", 0),
                        data.get("rate_c_kw", 0),
                        data.get("is_peak_time", False),
                        data.get("control_line"),
                        data.get("plant_type"),
                        data.get("plant_name"),
                        data.get("scraped_at"),
                        data.get("source", "pea_amr"),
                    ),
                )
                return True
        except Exception as e:
            print(f"❌ Error inserting reading: {e}")
            return False

    def insert_readings_batch(self, readings: List[Dict]) -> int:
        """Insert multiple readings in a single transaction"""
        inserted = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for data in readings:
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO energy_readings 
                        (plant_id, timestamp, current_kw, rate_a_kw, rate_b_kw, rate_c_kw,
                         is_peak_time, control_line, plant_type, plant_name, scraped_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            data.get("plant_id"),
                            data.get("timestamp"),
                            data.get("current_kw"),
                            data.get("rate_a_kw", 0),
                            data.get("rate_b_kw", 0),
                            data.get("rate_c_kw", 0),
                            data.get("is_peak_time", False),
                            data.get("control_line"),
                            data.get("plant_type"),
                            data.get("plant_name"),
                            data.get("scraped_at"),
                            data.get("source", "pea_amr"),
                        ),
                    )
                    inserted += 1
                print(f"✅ Inserted {inserted} readings")
                return inserted
        except Exception as e:
            print(f"❌ Error batch inserting: {e}")
            return inserted

    # ==================== QUERY OPERATIONS ====================

    def get_readings(
        self, plant_id: str, start_date: str, end_date: str, limit: int = 1000
    ) -> List[Dict]:
        """Get readings for a plant within date range"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM energy_readings
                WHERE plant_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                LIMIT ?
            """,
                (plant_id, start_date, end_date, limit),
            )

            return [dict(row) for row in cursor.fetchall()]

    def get_latest_reading(self, plant_id: str) -> Optional[Dict]:
        """Get most recent reading for a plant"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM energy_readings
                WHERE plant_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """,
                (plant_id,),
            )

            row = cursor.fetchone()
            return dict(row) if row else None

    def get_daily_peak(self, plant_id: str, date: str) -> Optional[Dict]:
        """Get peak demand for a specific day"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM energy_readings
                WHERE plant_id = ? 
                AND DATE(timestamp) = DATE(?)
                ORDER BY current_kw DESC
                LIMIT 1
            """,
                (plant_id, date),
            )

            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== AGGREGATION OPERATIONS ====================

    def calculate_monthly_summary(self, plant_id: str, year: int, month: int) -> Dict:
        """Calculate and store monthly summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Get date range for the month
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            # Calculate metrics
            cursor.execute(
                """
                SELECT 
                    plant_name,
                    MAX(current_kw) as max_demand_kw,
                    AVG(current_kw) as avg_demand_kw,
                    MIN(current_kw) as min_demand_kw,
                    MAX(CASE WHEN is_peak_time = 1 THEN current_kw END) as max_peak_time_kw,
                    AVG(CASE WHEN is_peak_time = 1 THEN current_kw END) as avg_peak_time_kw,
                    SUM(CASE WHEN is_peak_time = 1 THEN 1 ELSE 0 END) / 4 as peak_time_hours,
                    MAX(control_line) as control_line,
                    SUM(CASE WHEN current_kw > control_line THEN 1 ELSE 0 END) as times_exceeded,
                    MAX(current_kw - control_line) as max_excess_kw,
                    AVG(CASE WHEN current_kw > control_line THEN current_kw - control_line END) as avg_excess_kw
                FROM energy_readings
                WHERE plant_id = ? AND timestamp >= ? AND timestamp < ?
            """,
                (plant_id, start_date, end_date),
            )

            result = cursor.fetchone()
            if not result or not result["max_demand_kw"]:
                print(f"⚠️  No data found for {plant_id} {year}-{month:02d}")
                return {}

            # Get previous month peak for comparison
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1

            cursor.execute(
                """
                SELECT max_demand_kw FROM monthly_peak_summary
                WHERE plant_id = ? AND year = ? AND month = ?
            """,
                (plant_id, prev_year, prev_month),
            )

            prev_row = cursor.fetchone()
            previous_month_peak = prev_row["max_demand_kw"] if prev_row else None

            # Calculate reductions
            max_kw = result["max_demand_kw"]
            control_line = result["control_line"] or 0

            reduction_vs_control_kw = control_line - max_kw if control_line > 0 else 0
            reduction_vs_control_pct = (
                (reduction_vs_control_kw / control_line * 100)
                if control_line > 0
                else 0
            )

            reduction_vs_previous_kw = (
                (previous_month_peak - max_kw) if previous_month_peak else 0
            )
            reduction_vs_previous_pct = (
                (reduction_vs_previous_kw / previous_month_peak * 100)
                if previous_month_peak
                else 0
            )

            utilization_pct = (max_kw / control_line * 100) if control_line > 0 else 0
            compliance_score = 100 - utilization_pct if utilization_pct <= 100 else 0

            # Get timestamp of max demand
            cursor.execute(
                """
                SELECT timestamp FROM energy_readings
                WHERE plant_id = ? AND timestamp >= ? AND timestamp < ?
                ORDER BY current_kw DESC LIMIT 1
            """,
                (plant_id, start_date, end_date),
            )
            max_timestamp = cursor.fetchone()["timestamp"]

            # Insert or update summary
            summary = {
                "plant_id": plant_id,
                "plant_name": result["plant_name"],
                "year": year,
                "month": month,
                "max_demand_kw": max_kw,
                "max_demand_timestamp": max_timestamp,
                "avg_demand_kw": result["avg_demand_kw"],
                "min_demand_kw": result["min_demand_kw"],
                "max_peak_time_kw": result["max_peak_time_kw"],
                "avg_peak_time_kw": result["avg_peak_time_kw"],
                "peak_time_hours": result["peak_time_hours"],
                "control_line": control_line,
                "times_exceeded": result["times_exceeded"],
                "max_excess_kw": max(0, result["max_excess_kw"] or 0),
                "avg_excess_kw": result["avg_excess_kw"] or 0,
                "previous_month_peak": previous_month_peak,
                "reduction_vs_previous_kw": reduction_vs_previous_kw,
                "reduction_vs_previous_pct": reduction_vs_previous_pct,
                "reduction_vs_control_kw": reduction_vs_control_kw,
                "reduction_vs_control_pct": reduction_vs_control_pct,
                "utilization_pct": utilization_pct,
                "compliance_score": compliance_score,
            }

            cursor.execute(
                """
                INSERT OR REPLACE INTO monthly_peak_summary 
                (plant_id, plant_name, year, month, max_demand_kw, max_demand_timestamp,
                 avg_demand_kw, min_demand_kw, max_peak_time_kw, avg_peak_time_kw,
                 peak_time_hours, control_line, times_exceeded, max_excess_kw, avg_excess_kw,
                 previous_month_peak, reduction_vs_previous_kw, reduction_vs_previous_pct,
                 reduction_vs_control_kw, reduction_vs_control_pct, utilization_pct, compliance_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                tuple(summary.values()),
            )

            print(f"✅ Monthly summary created for {plant_id} {year}-{month:02d}")
            return summary

    def get_monthly_summary(
        self, plant_id: str, year: int, month: int
    ) -> Optional[Dict]:
        """Get existing monthly summary or calculate if not exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM monthly_peak_summary
                WHERE plant_id = ? AND year = ? AND month = ?
            """,
                (plant_id, year, month),
            )

            row = cursor.fetchone()
            if row:
                return dict(row)

            # If not exists, try to calculate it
            return self.calculate_monthly_summary(plant_id, year, month)

    def get_yearly_summary(self, plant_id: str, year: int) -> Optional[Dict]:
        """Get or calculate yearly summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM yearly_summary
                WHERE plant_id = ? AND year = ?
            """,
                (plant_id, year),
            )

            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== UTILITY OPERATIONS ====================

    def cleanup_old_data(self, days_to_keep: int = 180):
        """Delete raw readings older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM energy_readings
                WHERE timestamp < ?
            """,
                (cutoff_date,),
            )

            deleted = cursor.rowcount
            print(
                f"🗑️  Cleaned up {deleted} old readings (older than {days_to_keep} days)"
            )
            return deleted

    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM energy_readings")
            reading_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM monthly_peak_summary")
            monthly_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM yearly_summary")
            yearly_count = cursor.fetchone()["count"]

            cursor.execute("""
                SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest 
                FROM energy_readings
            """)
            date_range = cursor.fetchone()

            return {
                "total_readings": reading_count,
                "monthly_summaries": monthly_count,
                "yearly_summaries": yearly_count,
                "oldest_reading": date_range["oldest"],
                "newest_reading": date_range["newest"],
                "db_path": self.db_path,
            }


# Singleton instance
_db_instance = None


def get_db() -> Database:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # Test database
    db = Database("test_energy.db")

    # Test insert
    test_data = {
        "plant_id": "1",
        "plant_name": "Test Plant",
        "timestamp": datetime.now().isoformat(),
        "current_kw": 500.0,
        "rate_a_kw": 0,
        "rate_b_kw": 0,
        "rate_c_kw": 500.0,
        "is_peak_time": True,
        "control_line": 2000.0,
        "plant_type": "TOU",
        "scraped_at": datetime.now().isoformat(),
        "source": "test",
    }

    db.insert_reading(test_data)
    print("✅ Test insert successful")

    # Test query
    stats = db.get_stats()
    print(f"📊 Database stats: {stats}")
