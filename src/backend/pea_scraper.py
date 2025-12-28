"""
PEA AMR Web Scraper
Automated data extraction from PEA AMR website for energy demand monitoring
"""

import asyncio
import random
from datetime import datetime
from typing import Dict, Optional, List
from playwright.async_api import (
    async_playwright,
    Browser,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from config import Config, PlantConfig


class PEAScraperError(Exception):
    """Base exception for scraper errors"""

    pass


class LoginFailedError(PEAScraperError):
    """Raised when login fails"""

    pass


class DataExtractionError(PEAScraperError):
    """Raised when data extraction fails"""

    pass


class PEAScraper:
    """Web scraper for PEA AMR website"""

    def __init__(self, plant: PlantConfig):
        self.plant = plant
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self.login_attempts = 0
        self.last_data: Optional[Dict] = None

    async def initialize(self):
        """Initialize browser instance"""
        playwright = await async_playwright().start()

        # Launch browser in headless mode
        self.browser = await playwright.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )

        # Create context with realistic settings
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        self.page = await context.new_page()

    async def _human_delay(self, min_sec: int = None, max_sec: int = None):
        """Random delay to simulate human behavior"""
        min_sec = min_sec or Config.MIN_DELAY_SECONDS
        max_sec = max_sec or Config.MAX_DELAY_SECONDS
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def login(self) -> bool:
        """
        Login to PEA AMR website
        Returns True if successful, raises LoginFailedError if failed
        """
        if self.login_attempts >= Config.MAX_LOGIN_RETRIES:
            raise LoginFailedError(
                f"Circuit breaker triggered: {Config.MAX_LOGIN_RETRIES} failed login attempts"
            )

        try:
            print(
                f"[{self.plant.name}] Attempting login... (Attempt {self.login_attempts + 1}/{Config.MAX_LOGIN_RETRIES})"
            )

            # Navigate to login page
            await self.page.goto(
                Config.PEA_AMR_LOGIN_URL, timeout=Config.REQUEST_TIMEOUT_SECONDS * 1000
            )
            await self._human_delay(2, 4)

            # Updated with AMRWEB selectors (2025-12-28)
            # Page: https://www.amr.pea.co.th/AMRWEB/Index.aspx

            # Fill username
            await self.page.fill("#txtUsername", self.plant.username)
            await self._human_delay(1, 2)

            # Fill password
            await self.page.fill("#txtPassword", self.plant.password)
            await self._human_delay(1, 2)

            # Click login button
            await self.page.click("#btnOK")
            await self._human_delay(3, 5)

            # Check if login was successful
            # After successful login, PEA redirects to: https://www.amr.pea.co.th/AMRWEB/Index.aspx
            current_url = self.page.url

            if "AMRWEB/Index.aspx" in current_url or "amrweb" in current_url.lower():
                self.is_logged_in = True
                self.login_attempts = 0  # Reset on success
                print(f"[{self.plant.name}] ✅ Login successful")
                print(f"[{self.plant.name}] Dashboard URL: {current_url}")
                return True
            else:
                self.login_attempts += 1
                print(
                    f"[{self.plant.name}] ❌ Login failed - Current URL: {current_url}"
                )
                raise LoginFailedError(f"Login failed for {self.plant.name}")

        except PlaywrightTimeoutError:
            self.login_attempts += 1
            raise LoginFailedError(f"Login timeout for {self.plant.name}")
        except Exception as e:
            self.login_attempts += 1
            raise LoginFailedError(f"Login error for {self.plant.name}: {str(e)}")

    async def navigate_to_daily_load_profile(self):
        """Navigate to daily load profile page and configure kW report"""
        if not self.is_logged_in:
            raise PEAScraperError("Not logged in")

        try:
            print(f"[{self.plant.name}] Navigating to Load Profile...")

            # Click "โหลด�โปรไฟล์" (Load Profile) menu
            load_profile_menu = await self.page.query_selector(
                'span.menuheader:has-text("โหลดโปรไฟล์")'
            )
            if load_profile_menu:
                await load_profile_menu.click()
                await self._human_delay(1, 2)

            # Click "รายเดือน" (Monthly) submenu
            monthly_menu = await self.page.query_selector('span:has-text("รายเดือน")')
            if monthly_menu:
                await monthly_menu.click()
                await self._human_delay(2, 3)

            print(f"[{self.plant.name}] Extracting report parameters...")

            # Access iframe to extract dynamic parameters
            iframe = await self.page.query_selector("#frmMain")
            if not iframe:
                raise DataExtractionError("Form iframe not found")

            frame_content = await iframe.content_frame()
            if not frame_content:
                raise DataExtractionError("Could not access iframe content")

            await self._human_delay(1, 2)

            # Extract required parameters from the form page URL
            iframe_url = await frame_content.evaluate("window.location.href")
            print(f"[{self.plant.name}] Form page URL: {iframe_url}")

            # Parse parameters from URL (format: selMonthlyProfile.aspx?CustCode=XXX&Custid=YYY)
            import urllib.parse
            from datetime import datetime

            parsed_url = urllib.parse.urlparse(iframe_url)
            params = urllib.parse.parse_qs(parsed_url.query)

            custid = params.get("Custid", [None])[0]
            custcode = params.get("CustCode", [None])[0]

            # Also extract PeaNo and MeterPoint from form
            form_params = await frame_content.evaluate("""
                () => {
                    const ddlMeter = document.getElementById('ddlMeter');
                    return {
                        peaNo: ddlMeter ? ddlMeter.value : null,
                        meterPoint: ddlMeter ? ddlMeter.options[ddlMeter.selectedIndex]?.getAttribute('data-meter-point') : null
                    };
                }
            """)

            pea_no = form_params.get("peaNo") or params.get("PeaNo", [None])[0]

            # Get current month (Buddhist year)
            now = datetime.now()
            buddhist_year = now.year + 543
            current_month = now.month
            rep_date = f"01/{current_month:02d}/{buddhist_year}"

            # Build direct URL to report
            report_params = {
                "Custid": custid,
                "CustCode": custcode,
                "PeaNo": pea_no,
                "MeterPoint": "202485",  # This seems constant based on browser agent
                "SumMeter": "0",
                "RepDate": rep_date,
                "GrphType": "Line",
                "DataType": "0",  # 0=Data only, 1=Graph, 2=Both
                "RepType": "kW",
                "RateType": "",
                "SumType": "0",  # 0=15min, 1=Daily
                "SubSys": "0",
                "RoundType": "0",  # 0=Normal month, 1=Billing cycle
            }

            report_url = f"https://www.amr.pea.co.th/AMRWEB/showMonthlyProfile.aspx?{urllib.parse.urlencode(report_params)}"

            print(f"[{self.plant.name}] Navigating directly to report...")
            print(f"[{self.plant.name}] Report URL: {report_url[:100]}...")

            # Navigate iframe directly to the report
            await frame_content.goto(report_url)
            await self._human_delay(5, 7)

            print(f"[{self.plant.name}] ✅ Report loaded via direct URL")

        except Exception as e:
            raise DataExtractionError(f"Failed to navigate to load profile: {str(e)}")

    async def get_current_demand(self) -> Dict:
        """
        Extract current demand data from PEA AMR
        Returns dict with: current_kw, timestamp, raw_data
        """
        if not self.is_logged_in:
            await self.login()

        try:
            await self.navigate_to_daily_load_profile()

            print(f"[{self.plant.name}] Extracting data from iframe...")

            # Wait longer for iframe to load and DATA to populate
            await self._human_delay(7, 10)

            # Access iframe containing the report data
            iframe = await self.page.query_selector("#frmMain")
            if not iframe:
                raise DataExtractionError("Report iframe not found")

            iframe_content = await iframe.content_frame()
            if not iframe_content:
                raise DataExtractionError("Could not access iframe content")

            # Wait for data table to actually load (not just form table)
            # Keep checking until we find a table with actual data
            print(f"[{self.plant.name}] Waiting for data table to load...")
            data_table_loaded = False
            max_attempts = 15  # Try for up to 30 seconds

            for attempt in range(max_attempts):
                await asyncio.sleep(2)
                tables = await iframe_content.query_selector_all("table")

                for table in tables:
                    text = await table.inner_text()
                    # Check if this table has actual data (contains RATE or timestamps)
                    if ("RATE A" in text or "RATE B" in text or "RATE C" in text) and (
                        "01/" in text or "02/" in text or "28/" in text
                    ):
                        data_table_loaded = True
                        print(
                            f"[{self.plant.name}] ✅ Data table loaded after {(attempt + 1) * 2}s"
                        )
                        break

                if data_table_loaded:
                    break

                if attempt < max_attempts - 1:
                    print(
                        f"[{self.plant.name}] Still waiting for data... ({(attempt + 1) * 2}s)"
                    )

            if not data_table_loaded:
                print(
                    f"[{self.plant.name}] ⚠️ Data table may not have loaded, proceeding anyway..."
                )

            # Check for nested iframes
            nested_iframes = await iframe_content.query_selector_all("iframe")
            if len(nested_iframes) > 0:
                print(
                    f"[{self.plant.name}] Found {len(nested_iframes)} nested iframe(s), checking first one..."
                )
                # Try to access data from nested iframe
                nested_frame = await nested_iframes[0].content_frame()
                if nested_frame:
                    iframe_content = nested_frame
                    await asyncio.sleep(2)

            # Find table containing "RATE A" or any table with timestamps
            tables = await iframe_content.query_selector_all("table")
            print(f"[{self.plant.name}] Found {len(tables)} tables in iframe")

            target_table = None

            # Try to find table with actual DATA (not form tables)
            # Data tables should have:
            # 1. Many rows (more than 5-10) OR
            # 2. Contain date/time patterns OR
            # 3. Contain "RATE A" text
            for i, table in enumerate(tables):
                text = await table.inner_text()
                rows = await table.query_selector_all("tr")

                print(
                    f"[{self.plant.name}] Table {i + 1}: {len(rows)} rows, preview: {text[:80]}..."
                )

                # Skip form tables (usually have < 10 rows and contain ":*" or "รายงาน")
                is_form_table = ("รายงาน :*" in text or "กรุณาเลือก" in text) and len(
                    rows
                ) < 10

                if is_form_table:
                    print(f"[{self.plant.name}]   -> Skipping form table")
                    continue

                # Look for data tables
                has_rate = "RATE A" in text or "RATE" in text
                has_date = "/" in text and any(c.isdigit() for c in text)
                has_many_rows = len(rows) > 10

                if has_rate or has_date or has_many_rows:
                    target_table = table
                    print(
                        f"[{self.plant.name}] ✅ Found target DATA table (#{i + 1}, {len(rows)} rows)"
                    )
                    break

            if not target_table:
                # Fallback: use largest table
                max_rows = 0
                for table in tables:
                    rows = await table.query_selector_all("tr")
                    if len(rows) > max_rows:
                        max_rows = len(rows)
                        target_table = table
                if target_table:
                    print(f"[{self.plant.name}] Using largest table ({max_rows} rows)")

            if not target_table:
                raise DataExtractionError(
                    f"Data table not found in report ({len(tables)} tables checked)"
                )

            # Get all rows
            rows = await target_table.query_selector_all("tr")
            print(f"[{self.plant.name}] Found {len(rows)} rows in table")

            # Extract last row with valid data (skip header and empty rows)
            latest_data = None
            for i, row in enumerate(reversed(rows)):
                cells = await row.query_selector_all("td, th")
                if len(cells) > 0:
                    cell_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        cell_texts.append(text.strip())

                    # Debug: print first few rows
                    if i < 5:  # Show last 5 rows
                        print(f"[{self.plant.name}] Row {len(rows) - i}: {cell_texts}")

                    # Check if this row has timestamp AND actual data
                    # Formats: "dd/mm/yyyy HH.MM", "HH.MM", or contains numbers and "/"
                    if len(cell_texts) >= 2 and cell_texts[0]:
                        # More flexible timestamp detection
                        has_slash = "/" in cell_texts[0]
                        has_colon_or_dot = "." in cell_texts[0] or ":" in cell_texts[0]
                        has_numbers = any(c.isdigit() for c in cell_texts[0])

                        # Check if any of the data cells (Rate A/B/C) have values
                        has_kw_data = any(
                            cell_texts[j].strip() and cell_texts[j].strip() != ""
                            for j in range(1, min(len(cell_texts), 4))
                        )

                        if (
                            has_numbers
                            and (has_slash or has_colon_or_dot)
                            and has_kw_data
                        ):
                            latest_data = cell_texts
                            print(
                                f"[{self.plant.name}] ✅ Found data row: {cell_texts[:4]}"
                            )
                            break

            if not latest_data:
                raise DataExtractionError(
                    f"No valid data found in table ({len(rows)} rows checked)"
                )

            # Parse data
            # Format: [timestamp, Rate A kW, Rate B kW, Rate C kW]
            timestamp_str = latest_data[0]  # e.g., "28/12/2025 20.45"
            rate_a_kw = (
                self._parse_demand_value(latest_data[1]) if len(latest_data) > 1 else 0
            )
            rate_b_kw = (
                self._parse_demand_value(latest_data[2]) if len(latest_data) > 2 else 0
            )
            rate_c_kw = (
                self._parse_demand_value(latest_data[3]) if len(latest_data) > 3 else 0
            )

            # Use Rate C as current demand (typically the active rate)
            # Or could use max of all rates
            current_kw = max(rate_a_kw, rate_b_kw, rate_c_kw)

            data = {
                "plant_id": self.plant.id,
                "plant_name": self.plant.name,
                "current_kw": current_kw,
                "rate_a_kw": rate_a_kw,
                "rate_b_kw": rate_b_kw,
                "rate_c_kw": rate_c_kw,
                "control_line": self.plant.control_line,
                "timestamp": timestamp_str,
                "scraped_at": datetime.now().isoformat(),
                "source": "pea_amr",
            }

            self.last_data = data
            print(
                f"[{self.plant.name}] ✅ Data extracted: {current_kw} kW (@ {timestamp_str})"
            )
            print(
                f"[{self.plant.name}]    Rate A: {rate_a_kw}, Rate B: {rate_b_kw}, Rate C: {rate_c_kw}"
            )

            return data

        except Exception as e:
            raise DataExtractionError(
                f"Failed to extract data for {self.plant.name}: {str(e)}"
            )

    async def get_load_profile(self, hours: int = 24) -> List[Dict]:
        """
        Extract historical load profile data
        Returns list of 15-minute interval readings
        """
        if not self.is_logged_in:
            await self.login()

        try:
            await self.navigate_to_load_profile()

            # TODO: Implement based on actual website table structure
            # This is a placeholder

            intervals = []
            # Example: extract table rows
            # rows = await self.page.query_selector_all('table.load-profile tbody tr')
            # for row in rows:
            #     # Parse each row...
            #     pass

            return intervals

        except Exception as e:
            raise DataExtractionError(f"Failed to extract load profile: {str(e)}")

    def _parse_demand_value(self, text: str) -> float:
        """Parse demand value from text (handles commas, units, etc.)"""
        # Remove common text like "kW", commas, spaces
        cleaned = text.replace("kW", "").replace("KW", "").replace(",", "").strip()

        # Return 0 for empty values
        if not cleaned or cleaned == "":
            return 0.0

        try:
            return float(cleaned)
        except ValueError:
            raise DataExtractionError(f"Could not parse demand value: {text}")

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            self.is_logged_in = False
            print(f"[{self.plant.name}] Browser closed")


class MultiPlantScraper:
    """Manager for multiple plant scrapers"""

    def __init__(self):
        self.scrapers: Dict[str, PEAScraper] = {}

    async def initialize_all(self):
        """Initialize scrapers for all configured plants"""
        plants = Config.get_all_plants()

        if not plants:
            print("⚠️  No plants configured. Please check .env file.")
            return

        print(f"Initializing {len(plants)} plant scrapers...")

        for plant in plants:
            scraper = PEAScraper(plant)
            await scraper.initialize()
            self.scrapers[plant.id] = scraper

        print(f"✅ Initialized {len(self.scrapers)} scrapers")

    async def scrape_all(self) -> List[Dict]:
        """Scrape data from all plants concurrently"""
        if not self.scrapers:
            await self.initialize_all()

        tasks = []
        for plant_id, scraper in self.scrapers.items():
            tasks.append(scraper.get_current_demand())

        # Run all scrapers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out errors
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(
                    f"❌ Error scraping plant {list(self.scrapers.keys())[i]}: {result}"
                )
            else:
                valid_results.append(result)

        return valid_results

    async def close_all(self):
        """Close all scrapers"""
        for scraper in self.scrapers.values():
            await scraper.close()
        self.scrapers.clear()


# Test function
async def test_scraper():
    """Test the scraper with configured plants"""
    scraper_manager = MultiPlantScraper()

    try:
        await scraper_manager.initialize_all()

        print("\n" + "=" * 50)
        print("Testing data extraction...")
        print("=" * 50 + "\n")

        results = await scraper_manager.scrape_all()

        print("\n" + "=" * 50)
        print(f"Results: {len(results)} plants")
        print("=" * 50 + "\n")

        for data in results:
            print(f"Plant: {data['plant_name']}")
            print(f"  Current: {data['current_kw']} kW")
            print(f"  Control Line: {data['control_line']} kW")
            print(
                f"  Utilization: {(data['current_kw'] / data['control_line'] * 100):.1f}%"
            )
            print()

    finally:
        await scraper_manager.close_all()


if __name__ == "__main__":
    print("PEA AMR Web Scraper - Test Mode\n")
    asyncio.run(test_scraper())
