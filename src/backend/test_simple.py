"""
Simple test script for PEA scraper with better error reporting
Tests login for ONE plant only to get clear output
"""

import asyncio
import sys
from config import Config, PlantConfig
from pea_scraper import PEAScraper


async def test_single_plant():
    """Test scraper with first configured plant only"""
    plants = Config.get_all_plants()

    if not plants:
        print("❌ No plants configured in .env file")
        return False

    # Test with first plant only
    plant = plants[0]
    print(f"Testing scraper with: {plant.name}")
    print(f"Username: {plant.username}")
    print(f"Control Line: {plant.control_line} kW")
    print("=" * 60)

    scraper = PEAScraper(plant)

    try:
        print("\n📍 Step 1: Initializing browser...")
        await scraper.initialize()
        print("✅ Browser initialized")

        print("\n📍 Step 2: Attempting login...")
        success = await scraper.login()

        if success:
            print("✅ Login successful!")
            print(f"Current URL: {scraper.page.url}")

            # Try to get page title
            title = await scraper.page.title()
            print(f"Page Title: {title}")

            print("\n📍 Step 3: Attempting data extraction...")
            try:
                data = await scraper.get_current_demand()
                print("✅ Data extracted successfully!")
                print(f"\nExtracted Data:")
                print(f"  Plant: {data['plant_name']}")
                print(f"  Current Demand: {data['current_kw']} kW")
                print(f"  Control Line: {data['control_line']} kW")
                print(f"  Timestamp: {data['timestamp']}")
                print(f"  Scraped At: {data['scraped_at']}")

                utilization = (data["current_kw"] / data["control_line"]) * 100
                print(f"  Utilization: {utilization:.1f}%")

                if utilization >= 90:
                    print("  ⚠️  WARNING: Near control line!")
                elif utilization >= 100:
                    print("  🚨 CRITICAL: Exceeded control line!")
                else:
                    print("  ✅ Normal operation")

                return True

            except Exception as e:
                print(f"❌ Data extraction failed: {e}")
                print(f"   Error type: {type(e).__name__}")

                # Try to capture screenshot for debugging
                try:
                    screenshot_path = "error_screenshot.png"
                    await scraper.page.screenshot(path=screenshot_path)
                    print(f"   Screenshot saved to: {screenshot_path}")
                except:
                    pass

                return False
        else:
            print("❌ Login failed")
            return False

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        print("\n📍 Step 4: Cleanup...")
        await scraper.close()
        print("✅ Browser closed")


if __name__ == "__main__":
    print("=" * 60)
    print("PEA AMR Scraper - Single Plant Test")
    print("=" * 60 + "\n")

    result = asyncio.run(test_single_plant())

    print("\n" + "=" * 60)
    if result:
        print("✅ TEST PASSED - Scraper is working!")
        sys.exit(0)
    else:
        print("❌ TEST FAILED - Check errors above")
        sys.exit(1)
