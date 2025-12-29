# Peak Load Demand Monitoring System (RPA Edition)

## Overview

ระบบติดตาม Peak Load Demand แบบอัตโนมัติโดยใช้ Web Scraping (RPA) เพื่อดึงข้อมูลจาก PEA AMR Website

รองรับการติดตามพร้อมกัน **4 โรงงาน** โดยไม่ต้องติดตั้งอุปกรณ์ IoT เพิ่มเติม

---

## 🚀 Quick Start

### 1. ติดตั้ง Dependencies

```bash
cd d:\Development\Projects\Peak-Load-Demand-Monitoring\src\backend
pip install -r requirements.txt
playwright install chromium
```

### 2. ตั้งค่า Credentials

สร้างไฟล์ `.env` ในโฟลเดอร์โปรเจค:

```bash
cd d:\Development\Projects\Peak-Load-Demand-Monitoring
copy .env.example .env
```

จากนั้นแก้ไขไฟล์ `.env` และใส่ข้อมูลจริงของทั้ง 4 โรงงาน:

```env
# Plant 1
PEA_PLANT1_USERNAME=0200xxxxxxxxxx
PEA_PLANT1_PASSWORD=your_actual_password

# Plant 2
PEA_PLANT2_USERNAME=0200xxxxxxxxxx
PEA_PLANT2_PASSWORD=your_actual_password

# Plant 3
PEA_PLANT3_USERNAME=0200xxxxxxxxxx
PEA_PLANT3_PASSWORD=your_actual_password

# Plant 4
PEA_PLANT4_USERNAME=0200xxxxxxxxxx
PEA_PLANT4_PASSWORD=your_actual_password
```

### 3. ทดสอบ Configuration

```bash
cd src\backend
python config.py
```

คุณจะเห็นสถานะของทั้ง 4 plants ที่ตั้งค่าไว้

### 4. ทดสอบ Web Scraper (จำเป็นต้องอัพเดท Selectors ก่อน)

```bash
python pea_scraper.py
```

---

## 📁 โครงสร้างโปรเจค

```
Peak-Load-Demand-Monitoring/
├── .env                    # ⚠️ ความลับ - อย่า commit!
├── .env.example           # Template สำหรับ .env
├── .gitignore            # ป้องกัน .env หลุด
├── README.md             # เอกสารนี้
├── implementation_plan.md # แผนการพัฒนา
├── task.md               # รายการงาน
│
├── src/
│   ├── backend/
│   │   ├── main.py           # FastAPI Server (Simulation + Real Data)
│   │   ├── config.py         # Configuration Manager ✨ NEW
│   │   ├── pea_scraper.py    # PEA AMR Web Scraper ✨ NEW
│   │   └── requirements.txt  # Python dependencies
│   │
│   └── frontend/
│       ├── index.html        # Dashboard UI
│       ├── app.js           # Frontend Logic
│       └── style.css        # Styling
│
└── docs/
    └── FOLDER_STRUCTURE.md
```

---

## 🔧 Configuration Files

### `.env` (Secret - Never Commit!)

ใช้เก็บ passwords และ sensitive data

### `config.py`

- โหลดค่าจาก `.env`
- จัดการ configuration ของทั้ง 4 plants
- ตรวจสอบว่า plant ไหนตั้งค่าครบแล้ว

### `pea_scraper.py`

- ล็อกอินเข้า PEA AMR website
- ดึงข้อมูล current demand (kW)
- รองรับ 4 plants พร้อมกัน (concurrent scraping)
- มี circuit breaker ป้องกัน account lock

---

## ⚙️ System Modes

### 1. Simulation Mode (Default)

ใช้ข้อมูลจำลอง - เหมาะสำหรับทดสอบ dashboard

```bash
# ใน .env
DATA_SOURCE=simulation
```

### 2. Live PEA AMR Mode

ใช้ข้อมูลจริงจาก PEA website

```bash
# ใน .env
DATA_SOURCE=pea_amr
```

---

## 🔐 Security Features

1. **Credential Protection**:

   - `.env` ถูก git-ignore ไม่ขึ้น repository
   - ไม่มี password ฝังในโค้ด

2. **Anti-Bot Protection**:

   - Random delays (5-15 วินาที) เลียนแบบมนุษย์
   - Realistic user-agent
   - Circuit breaker (หยุดหลัง 3 ครั้งที่ล็อกอินผิด)

3. **Rate Limiting**:
   - Scrape ทุก 15 นาที (ตาม interval ของ PEA)
   - ไม่ spamming server

---

## 📊 API Endpoints

### Current Features

- `GET /` - Health check
- `GET /api/status` - Factory status (Live/Simulation)
- `GET /api/plants/live` - Force live scrape trigger
- `GET /api/history/readings` - Historical data access
- `GET /api/summary/monthly` - Peak reduction analytics

### Database

ระบบใช้ **SQLite** (`energy_data.db`) ในการเก็บข้อมูลประวัติ:

- บันทึกข้อมูลทุกครั้งที่มีการ Scrape
- คำนวณ Monthly/Yearly Summary อัตโนมัติ

### Upcoming

- `GET /api/export/excel` - Download reports
- Frontend Analytics Dashboard

---

## 🎯 Next Steps

### Phase 2.2: Update PEA Website Selectors

**⚠️ CRITICAL: ต้องตรวจสอบ PEA AMR website structure จริงๆ**

1. เปิด PEA AMR website ในเบราว์เซอร์
2. ใช้ Developer Tools (F12) ดู HTML structure
3. อัพเดท selectors ใน `pea_scraper.py`:

```python
# ตัวอย่างที่ต้องแก้:
await self.page.fill('input[name="username"]', ...)  # ← แก้ selector
await self.page.fill('input[name="password"]', ...)  # ← แก้ selector
await self.page.click('button[type="submit"]')       # ← แก้ selector
```

4. ทดสอบจริงด้วย: `python pea_scraper.py`

### Phase 2.3: Backend Integration

- เชื่อม scraper เข้ากับ `main.py`
- สร้าง scheduled task (ทุก 15 นาที)
- สลับระหว่าง simulation/real data

### Phase 2.4: Frontend Updates

- แสดง "Data Source" badge
- แสดง "Last Updated" timestamp
- Error notifications

---

## 📝 Documentation

- **[Implementation Plan](implementation_plan.md)**: แผนการพัฒนาระบบ
- **[Task List](task.md)**: ติดตามความคืบหน้า
- **[Agent Instructions](agent.md)**: คำแนะนำสำหรับ AI Agent

---

## ⚠️ Important Notes

### Data Latency

ข้อมูลบน PEA AMR **ไม่ใช่ real-time แบบทันที** มักจะมีดีเลย์ 15-30 นาที

ระบบนี้จะช่วย:

- ✅ เฝ้าระวังแนวโน้มอัตโนมัติ
- ✅ แจ้งเตือนก่อนเกิน control line
- ❌ ไม่สามารถควบคุมแบบ real-time วินาทีต่อวินาที

### CAPTCHA Handling

ถ้า PEA มี CAPTCHA:

- ระบบจะตรวจจับและแจ้งเตือน
- อาจต้อง manual intervention
- หรือใช้ CAPTCHA solving API (เสียค่าใช้จ่าย)

---

## 🛡️ Security Checklist

ก่อน commit code ตรวจสอบเสมอ:

```bash
# ตรวจว่า .env ไม่ขึ้น Git
git status

# ค้นหา password ที่หลุด (ต้องไม่มี)
grep -r "password" src/
```

---

## 🚨 Current Status

- ✅ Configuration system ready
- ✅ Multi-plant scraper structure complete
- ⚠️ **Need PEA website selectors** (ต้องอัพเดทก่อนใช้งานจริง)
- ⏳ Backend integration pending
- ⏳ Frontend updates pending

---

## 📞 Support

- **Project**: Peak Load Demand Monitoring
- **Last Updated**: 2025-12-28
- **AI Agent**: Antigravity
