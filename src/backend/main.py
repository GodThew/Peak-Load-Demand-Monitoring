import asyncio
import random
from datetime import datetime, time
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FactoryState(BaseModel):
    id: str
    name: str
    type: str  # "TOU" or "TOD"
    current_kw: float
    control_line: float
    status: str  # "NORMAL", "WARNING", "CRITICAL"
    is_peak_time: bool


# Configuration
FACTORIES = [
    {"id": "f1", "name": "Factory 1 (Main)", "type": "TOU", "control_line": 2000.0},
    {"id": "f2", "name": "Factory 2 (Ext)", "type": "TOU", "control_line": 1500.0},
    {"id": "f3", "name": "Factory 3 (Aux)", "type": "TOU", "control_line": 800.0},
    {"id": "f4", "name": "Factory 4 (Old)", "type": "TOD", "control_line": 1200.0},
]

# Shared state
simulation_state: Dict[str, FactoryState] = {}


def is_on_peak_tou(now: datetime) -> bool:
    # TOU On-Peak: Mon-Fri 09:00 - 22:00
    if now.weekday() >= 5:  # Sat, Sun
        return False
    return time(9, 0) <= now.time() <= time(22, 0)


def is_on_peak_tod(now: datetime) -> bool:
    # TOD On-Peak: Mon-Fri 18:30 - 21:30 (Example rule, adaptable)
    # Actually TOD usually has wider range, but let's use a standard simplified rule for demo
    # PEA TOD: On Peak = 18.00-21.30 every day
    return time(18, 00) <= now.time() <= time(21, 30)


def simulate_load(factory_conf: dict, current_val: float) -> float:
    """Random walk simulation logic"""
    change = random.uniform(-20, 30)  # Drift upwards slightly to simulate work day
    new_val = current_val + change

    # Boundary checks
    max_val = factory_conf["control_line"] * 1.2
    if new_val < 0:
        new_val = 0
    if new_val > max_val:
        new_val = max_val

    return round(new_val, 2)


@app.on_event("startup")
async def startup_event():
    # Initialize state
    for f in FACTORIES:
        simulation_state[f["id"]] = FactoryState(
            id=f["id"],
            name=f["name"],
            type=f["type"],
            current_kw=f["control_line"] * 0.5,  # Start at 50%
            control_line=f["control_line"],
            status="NORMAL",
            is_peak_time=False,
        )
    # Start background simulation task
    asyncio.create_task(run_simulation())


async def run_simulation():
    while True:
        now = datetime.now()
        for f in FACTORIES:
            fid = f["id"]
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

            # Check Status vs Control Line
            # We care most if it's high AND during peak time (usually),
            # but Demand control usually applies to the max peak of the month
            # regardless of time for some tariff parts, BUT for TOU/TOD we specifically want to avoid On-Peak usage.

            # Simple Logic: Warn if > 90% of Control Line
            percent = (
                simulation_state[fid].current_kw / simulation_state[fid].control_line
            )

            if percent >= 1.0:
                simulation_state[fid].status = "CRITICAL"
            elif percent >= 0.90:
                simulation_state[fid].status = "WARNING"
            else:
                simulation_state[fid].status = "NORMAL"

        await asyncio.sleep(1)  # Update every second


@app.get("/api/status")
async def get_status():
    return list(simulation_state.values())


@app.get("/")
async def root():
    return {"message": "Energy Simulation API is running"}
