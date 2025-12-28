"""
Debug version of test script - saves URL and screenshot for analysis
"""

import asyncio
import sys
from datetime import datetime
from config import Config, PlantConfig
from pea_scraper import PEAScraper


async def debug_login():
    """Test login and save debugging info"""
    plants = Config.get_all_plants()

    if not plants:
        print("❌ No plants configured")
        return False

    plant = plants[0]
    print(f"Testing: {plant.name}")
    print(f"Username: {plant.username}\n")

    scraper = PEAScraper(plant)

    try:
        await scraper.initialize()
        print("✅ Browser initialized\n")

        # Navigate to login
        print(f"Navigating to: {Config.PEA_AMR_LOGIN_URL}")
        await scraper.page.goto(Config.PEA_AMR_LOGIN_URL, timeout=30000)
        await asyncio.sleep(3)

        print(f"Before login URL: {scraper.page.url}\n")

        # Fill form
        print("Filling username...")
        await scraper.page.fill("#commonWorkArea_txt_common_login_user", plant.username)
        await asyncio.sleep(2)

        print("Filling password...")
        await scraper.page.fill(
            "#commonWorkArea_txt_common_login_password", plant.password
        )
        await asyncio.sleep(2)

        # Screenshot before Click
        await scraper.page.screenshot(path="debug_before_login.png")
        print("Screenshot saved: debug_before_login.png\n")

        # Click login
        print("Clicking login button...")
        await scraper.page.click("#btn_common_login_submit")
        await asyncio.sleep(8)  # Wait longer for redirect

        # After login
        after_url = scraper.page.url
        print(f"\n{'=' * 60}")
        print(f"AFTER LOGIN URL: {after_url}")
        print(f"{'=' * 60}\n")

        # Save to file
        with open("debug_login_url.txt", "w", encoding="utf-8") as f:
            f.write(f"Login Test - {datetime.now()}\n")
            f.write(f"Plant: {plant.name}\n")
            f.write(f"Username: {plant.username}\n")
            f.write(f"Before: {Config.PEA_AMR_LOGIN_URL}\n")
            f.write(f"After: {after_url}\n")
            f.write(f"\nContains 'AMRWEB': {'AMRWEB' in after_url}\n")
            f.write(f"Contains 'amrweb' (lower): {'amrweb' in after_url.lower()}\n")
            f.write(f"Contains 'Index.aspx': {'Index.aspx' in after_url}\n")

        print("✅ Debug info saved to: debug_login_url.txt")

        # Screenshot after
        await scraper.page.screenshot(path="debug_after_login.png")
        print("✅ Screenshot saved: debug_after_login.png")

        # Page title
        title = await scraper.page.title()
        print(f"\nPage Title: {title}")

        # Check success
        if "AMRWEB" in after_url or "amrweb" in after_url.lower():
            print("\n✅ LOGIN SUCCESS - URL matches expected pattern!")
            return True
        elif "login" in after_url.lower():
            print("\n❌ STILL ON LOGIN PAGE - Login failed or wrong credentials")
            return False
        else:
            print(f"\n⚠️  UNKNOWN STATE - Unexpected URL: {after_url}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        await scraper.close()


if __name__ == "__main__":
    print("=" * 60)
    print("PEA AMR - Debug Login Test")
    print("=" * 60 + "\n")

    result = asyncio.run(debug_login())

    print("\n" + "=" * 60)
    if result:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
        print("Check debug_login_url.txt and screenshots for details")
    print("=" * 60)
