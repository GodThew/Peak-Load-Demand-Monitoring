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

- [ ] **Prototype Scraper**:
  - [ ] Install Playwright/Selenium
  - [ ] Implement Login Logic with Safe Credential Storage (`.env`)
  - [ ] Handle Session/CAPTCHA
- [ ] **Data Extraction**:
  - [ ] Parse "Load Profile" table for 15-min intervals
  - [ ] Extract current Demand value
- [ ] **Dashboard Integration**:
  - [ ] Connect Crawler data to existing Dashboard UI

## Phase 3: Integration & Alerting

- [ ] Database Setup (SQLite/JSON for local storage)
- [ ] Line Notify Integration (Critical Alerting)
- [ ] Automated Scheduler (Run every 15 mins)

## Deprecated / Alternative (Phase 2 Old)

- [x] Create Mock Data Generator (Simulation)
- [x] Build Basic Real-time Dashboard (Skeleton Code)
- [ ] Modbus/IoT Ingestion (Cancelled due to hardware constraints)
