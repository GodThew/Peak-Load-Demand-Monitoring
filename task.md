# Peak Load Demand Monitoring Project

## Phase 0: Project Governance (Active)

### Definition of Ready (DoR) - Check before starting Phase 2 tasks

- [x] **Requirement**: Clearly defined user need? (Manual Meter Reading from PEA Website)
- [x] **Analysis**: Impact on `src/` analyzed? (Pivot to Python Selenium/Playwright)
- [x] **Research**: Necessary docs/libs reviewed? (PEA AMR Website)
- [x] **Task Breakdown**: Subtasks listed below?

### Prerequisites

- [x] Git Installed
- [ ] GitHub CLI Installed (Manual Installation Required)
- [x] Directory Structure Organized
- [x] **Security Setup**: `.gitignore` and `.env` template created

## Phase 1: Conceptual Design & Planning

- [x] Define System Architecture (Revised: Web Crawler/RPA Strategy)
- [x] Create Implementation Plan/Proposal (Updated to "Hardware-less" approach)
- [x] Setup Basic Project Structure

## Phase 2: Web Crawler Implementation (New Direction)

- [x] **Prototype Scraper**:
  - [x] Install Playwright/Selenium
  - [x] Implement Login Logic with Safe Credential Storage (`.env`)
  - [x] Handle Session/CAPTCHA (Basic detection implemented)
- [x] **Data Extraction**:
  - [x] Parse "Load Profile" table for 15-min intervals
  - [x] Extract current Demand value (Rate A/B/C)
- [x] **Backend Integration**:
  - [x] Connect Scraper to FastAPI (`main.py`)
  - [x] Background scraping task (every 15 mins)
  - [x] Dual mode: Simulation + Live PEA data

## Phase 3: Integration & Alerting

- [x] Database Setup (SQLite with `database.py`)
- [x] Historical data storage and retrieval
- [x] Monthly/Yearly summary calculations
- [ ] **Line Notify Integration** (Critical Alerting) - Pending
- [/] **Frontend Dashboard Updates** (In Progress):
  - [ ] Data source badge (Live/Simulation)
  - [ ] Last updated timestamp display
  - [ ] Real-time data visualization

## Deprecated / Alternative (Phase 2 Old)

- [x] Create Mock Data Generator (Simulation)
- [x] Build Basic Real-time Dashboard (Skeleton Code)
- [ ] Modbus/IoT Ingestion (Cancelled due to hardware constraints)
