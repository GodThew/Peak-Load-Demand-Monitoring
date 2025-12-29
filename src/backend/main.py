import os
import sys
import asyncio
import random
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Fix for Windows + Playwright + uvicorn compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import scraper, config, and database
from pea_scraper import MultiPlantScraper, DataExtractionError
from config import Config
from database import get_db

app = FastAPI(title="Peak Load Demand Monitoring API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlantData(BaseModel):
    """Plant/Factory energy data"""

    id: str
    name: str
    type: str  # "TOU" or "TOD"
    current_kw: float
    control_line: float
    status: str  # "NORMAL", "WARNING", "CRITICAL"
    is_peak_time: bool
    # Additional fields for live data
    rate_a_kw: Optional[float] = None
    rate_b_kw: Optional[float] = None
    rate_c_kw: Optional[float] = None
    timestamp: Optional[str] = None  # PEA timestamp
    scraped_at: Optional[str] = None  # Our scrape time
    source: str = "simulation"  # "pea_amr" or "simulation"


class HealthStatus(BaseModel):
    """System health status"""

    system_mode: str
    scraper_initialized: bool
    cache_age_seconds: Optional[int] = None
    last_scrape_success: Optional[bool] = None
    configured_plants: int


# Global configuration
SYSTEM_MODE = Config.SYSTEM_MODE
CACHE_DURATION = Config.CACHE_DURATION_SECONDS

# Global state
scraper_instance: Optional[MultiPlantScraper] = None
live_data_cache: Dict[str, Dict] = {}
cache_timestamp: Optional[datetime] = None
last_scrape_success: bool = True

# Database instance
db = None

# Simulation state (fallback)
simulation_state: Dict[str, PlantData] = {}

# Mock factory configuration (for simulation mode)
FACTORIES = [
    {"id": "1", "name": "Factory 1 (Main)", "type": "TOU", "control_line": 2000.0},
    {"id": "2", "name": "Factory 2 (Ext)", "type": "TOU", "control_line": 1500.0},
    {"id": "3", "name": "Factory 3 (Aux)", "type": "TOU", "control_line": 800.0},
    {"id": "4", "name": "Factory 4 (Old)", "type": "TOD", "control_line": 1200.0},
]


def is_on_peak_tou(now: datetime) -> bool:
    """TOU On-Peak: Mon-Fri 09:00 - 22:00"""
    if now.weekday() >= 5:  # Sat, Sun
        return False
    return time(9, 0) <= now.time() <= time(22, 0)


def is_on_peak_tod(now: datetime) -> bool:
    """TOD On-Peak: 18:00 - 21:30 every day"""
    return time(18, 0) <= now.time() <= time(21, 30)


def simulate_load(factory_conf: dict, current_val: float) -> float:
    """Random walk simulation logic"""
    change = random.uniform(-20, 30)
    new_val = current_val + change

    max_val = factory_conf["control_line"] * 1.2
    if new_val < 0:
        new_val = 0
    if new_val > max_val:
        new_val = max_val

    return round(new_val, 2)


def calculate_status(current_kw: float, control_line: float) -> str:
    """Calculate status based on percentage of control line"""
    percent = current_kw / control_line

    if percent >= 1.0:
        return "CRITICAL"
    elif percent >= 0.90:
        return "WARNING"
    else:
        return "NORMAL"


async def scrape_live_data():
    """Background task to scrape live data periodically"""
    global live_data_cache, cache_timestamp, last_scrape_success

    while True:
        try:
            if scraper_instance:
                print(
                    f"[Live Scraper] Scraping data at {datetime.now().isoformat()}..."
                )
                results = await scraper_instance.scrape_all()

                if results:
                    # Update cache
                    live_data_cache = {item["plant_id"]: item for item in results}
                    cache_timestamp = datetime.now()
                    last_scrape_success = True
                    print(f"[Live Scraper] ✅ Cached {len(results)} plant(s)")

                    # Save to database
                    if db:
                        try:
                            saved = 0
                            for item in results:
                                db_data = {
                                    "plant_id": item.get("plant_id"),
                                    "plant_name": item.get("plant_name"),
                                    "timestamp": item.get("timestamp"),
                                    "current_kw": item.get("current_kw"),
                                    "rate_a_kw": item.get("rate_a_kw", 0),
                                    "rate_b_kw": item.get("rate_b_kw", 0),
                                    "rate_c_kw": item.get("rate_c_kw", 0),
                                    "is_peak_time": True,  # Will calculate properly later
                                    "control_line": item.get("control_line"),
                                    "plant_type": None,  # From config if needed
                                    "scraped_at": item.get("scraped_at"),
                                    "source": item.get("source", "pea_amr"),
                                }
                                if db.insert_reading(db_data):
                                    saved += 1
                            if saved > 0:
                                print(f"[Database] ✅ Saved {saved} readings")
                        except Exception as e:
                            print(f"[Database] ⚠️  Error: {e}")
                else:
                    print("[Live Scraper] ⚠️  No data returned from scraper")
                    last_scrape_success = False

        except Exception as e:
            print(f"[Live Scraper] ❌ Error: {str(e)}")
            last_scrape_success = False

        # Wait for cache duration before next scrape
        await asyncio.sleep(CACHE_DURATION)


async def run_simulation():
    """Background simulation (fallback/testing)"""
    while True:
        now = datetime.now()
        for f in FACTORIES:
            fid = f["id"]

            if fid in simulation_state:
                # Update KW
                simulation_state[fid].current_kw = simulate_load(
                    f, simulation_state[fid].current_kw
                )

                # Check Peak Time
                if f["type"] == "TOU":
                    is_peak = is_on_peak_tou(now)
                else:
                    is_peak = is_on_peak_tod(now)

                simulation_state[fid].is_peak_time = is_peak

                # Update status
                simulation_state[fid].status = calculate_status(
                    simulation_state[fid].current_kw, simulation_state[fid].control_line
                )

        await asyncio.sleep(1)  # Update every second


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global scraper_instance

    print(f"🚀 Starting Peak Load Monitoring API")
    print(f"📊 System Mode: {SYSTEM_MODE}")
    print(f"🔄 Cache Duration: {CACHE_DURATION} seconds")

    # Initialize database
    global db
    db = get_db()
    stats = db.get_stats()
    print(f"✅ Database ready - {stats['total_readings']} readings stored")

    # Initialize simulation state (always available as fallback)
    for f in FACTORIES:
        simulation_state[f["id"]] = PlantData(
            id=f["id"],
            name=f["name"],
            type=f["type"],
            current_kw=f["control_line"] * 0.5,
            control_line=f["control_line"],
            status="NORMAL",
            is_peak_time=False,
            source="simulation",
        )

    # Start simulation background task
    asyncio.create_task(run_simulation())
    print("✅ Simulation engine started")

    # Initialize live scraper if in live mode
    if SYSTEM_MODE == "live":
        try:
            scraper_instance = MultiPlantScraper()
            await scraper_instance.initialize_all()

            # Start live scraping background task
            asyncio.create_task(scrape_live_data())
            print("✅ Live scraper initialized")

        except Exception as e:
            print(f"⚠️  Failed to initialize scraper: {str(e)}")
            print("⚠️  Falling back to simulation mode")

    print("🎯 System ready!")


def get_live_plant_data() -> List[PlantData]:
    """Get plant data from live cache"""
    global cache_timestamp

    # Check if cache is valid
    if cache_timestamp:
        age = (datetime.now() - cache_timestamp).total_seconds()
        if age > CACHE_DURATION * 2:  # Cache expired (2x duration)
            print(f"[API] ⚠️  Cache expired ({age}s old)")
            return None

    if not live_data_cache:
        return None

    # Convert cache to PlantData objects
    plants = []
    now = datetime.now()

    for plant_id, data in live_data_cache.items():
        # Determine peak time based on type
        plant_type = data.get("plant_type", "TOU")
        if plant_type == "TOU":
            is_peak = is_on_peak_tou(now)
        else:
            is_peak = is_on_peak_tod(now)

        # Calculate status
        current_kw = data.get("current_kw", 0)
        control_line = data.get("control_line", 1000)
        status = calculate_status(current_kw, control_line)

        plants.append(
            PlantData(
                id=plant_id,
                name=data.get("plant_name", f"Plant {plant_id}"),
                type=plant_type,
                current_kw=current_kw,
                control_line=control_line,
                status=status,
                is_peak_time=is_peak,
                rate_a_kw=data.get("rate_a_kw"),
                rate_b_kw=data.get("rate_b_kw"),
                rate_c_kw=data.get("rate_c_kw"),
                timestamp=data.get("timestamp"),
                scraped_at=data.get("scraped_at"),
                source="pea_amr",
            )
        )

    return plants


@app.get("/api/status", response_model=List[PlantData])
async def get_status():
    """Get current status of all plants"""

    # If in live mode, try to get live data first
    if SYSTEM_MODE == "live":
        live_data = get_live_plant_data()
        if live_data:
            return live_data
        else:
            print("[API] ⚠️  Live data not available, using simulation")

    # Fallback to simulation
    return list(simulation_state.values())


@app.get("/api/plants/live", response_model=List[Dict])
async def get_live_data_now():
    """Force immediate live data fetch (bypass cache)"""

    if SYSTEM_MODE != "live":
        raise HTTPException(status_code=400, detail="System is in simulation mode")

    if not scraper_instance:
        raise HTTPException(status_code=503, detail="Scraper not initialized")

    try:
        results = await scraper_instance.scrape_all()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")


@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    """System health check"""

    cache_age = None
    if cache_timestamp:
        cache_age = int((datetime.now() - cache_timestamp).total_seconds())

    return HealthStatus(
        system_mode=SYSTEM_MODE,
        scraper_initialized=scraper_instance is not None,
        cache_age_seconds=cache_age,
        last_scrape_success=last_scrape_success,
        configured_plants=Config.get_configured_plant_count(),
    )


@app.get("/")
async def root():
    """API root"""
    return {
        "message": "Peak Load Demand Monitoring API",
        "mode": SYSTEM_MODE,
        "status": "running",
    }


# ==================== HISTORY & ANALYTICS ENDPOINTS ====================


@app.get("/api/history/readings", response_model=List[Dict])
async def get_history_readings(
    plant_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 1000,
):
    """Get historical raw readings"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    # Default to last 24 hours if not specified
    if not start:
        start = (datetime.now() - timedelta(days=1)).isoformat()
    if not end:
        end = datetime.now().isoformat()

    return db.get_readings(plant_id, start, end, limit)


@app.get("/api/summary/monthly/{year}/{month}", response_model=Dict)
async def get_monthly_summary(year: int, month: int, plant_id: Optional[str] = None):
    """Get monthly peak demand summary"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    if plant_id:
        # Get specific plant
        summary = db.get_monthly_summary(plant_id, year, month)
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        return summary
    else:
        # Get all plants
        summaries = {}
        for f in FACTORIES:
            pid = f["id"]
            s = db.get_monthly_summary(pid, year, month)
            if s:
                summaries[pid] = s
        return {"year": year, "month": month, "plants": summaries}


@app.get("/api/summary/yearly/{year}", response_model=Dict)
async def get_yearly_summary(year: int, plant_id: Optional[str] = None):
    """Get yearly summary"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    if plant_id:
        summary = db.get_yearly_summary(plant_id, year)
        if not summary:
            # Try to calculate on the fly if not exists (rudimentary)
            pass
        return summary if summary else {}
    else:
        summaries = {}
        for f in FACTORIES:
            pid = f["id"]
            s = db.get_yearly_summary(pid, year)
            if s:
                summaries[pid] = s
        return {"year": year, "plants": summaries}


@app.post("/api/admin/force-aggregation/{year}/{month}")
async def force_aggregation(year: int, month: int):
    """Admin: Force calculation of monthly summaries"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    results = []
    for f in FACTORIES:
        s = db.calculate_monthly_summary(f["id"], year, month)
        results.append(s)

    return {"message": "Aggregation complete", "results": results}
