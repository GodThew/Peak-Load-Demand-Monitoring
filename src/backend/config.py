"""
Configuration Manager for PEA AMR Web Scraper
Loads environment variables and provides configuration for multi-plant setup
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PlantConfig:
    """Configuration for a single plant/factory"""

    def __init__(self, plant_id: str):
        self.id = plant_id
        self.username = os.getenv(f"PEA_PLANT{plant_id}_USERNAME")
        self.password = os.getenv(f"PEA_PLANT{plant_id}_PASSWORD")
        self.name = os.getenv(f"PEA_PLANT{plant_id}_NAME", f"Plant {plant_id}")
        self.type = os.getenv(f"PEA_PLANT{plant_id}_TYPE", "TOU")
        self.control_line = float(
            os.getenv(f"PEA_PLANT{plant_id}_CONTROL_LINE", "1000.0")
        )

    def is_configured(self) -> bool:
        """Check if plant has valid credentials"""
        return bool(self.username and self.password)

    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding password)"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "control_line": self.control_line,
            "is_configured": self.is_configured(),
        }


class Config:
    """Global configuration"""

    # System settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DATA_SOURCE = os.getenv("DATA_SOURCE", "simulation")  # "simulation" or "pea_amr"

    # Scraper settings
    SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "15"))
    MAX_LOGIN_RETRIES = int(os.getenv("MAX_LOGIN_RETRIES", "3"))
    REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    MIN_DELAY_SECONDS = int(os.getenv("MIN_DELAY_SECONDS", "5"))
    MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "15"))

    # Line Notify
    LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")

    # PEA AMR URLs (Updated 2025-12-28 per user instruction)
    PEA_AMR_BASE_URL = "https://www.amr.pea.co.th"
    PEA_AMR_LOGIN_URL = f"{PEA_AMR_BASE_URL}/AMRWEB/Index.aspx"

    @staticmethod
    def get_all_plants() -> List[PlantConfig]:
        """Get configuration for all plants (1-4)"""
        plants = []
        for i in range(1, 5):  # Plant 1 to 4
            plant = PlantConfig(str(i))
            if plant.is_configured():
                plants.append(plant)
        return plants

    @staticmethod
    def get_configured_plant_count() -> int:
        """Get number of configured plants"""
        return len(Config.get_all_plants())


# Export for easy import
config = Config()


if __name__ == "__main__":
    # Test configuration
    print("=== Configuration Status ===")
    print(f"Data Source: {config.DATA_SOURCE}")
    print(f"Configured Plants: {config.get_configured_plant_count()}/4")
    print()

    for plant in config.get_all_plants():
        print(f"Plant {plant.id}: {plant.name}")
        print(f"  Type: {plant.type}")
        print(f"  Control Line: {plant.control_line} kW")
        print(f"  Has Credentials: {plant.is_configured()}")
        print()
