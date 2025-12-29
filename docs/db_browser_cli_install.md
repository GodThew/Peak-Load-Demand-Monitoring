# 🚀 DB Browser for SQLite - คำสั่งติดตั้งผ่าน Command Line

**เวอร์ชัน**: 3.13.1 (64-bit Windows)  
**วันที่**: 2025-12-29

---

## ✅ **วิธีที่ 1: ใช้ winget (แนะนำ - Windows 10/11)**

### ติดตั้งแบบปกติ (มี UAC prompt):

```powershell
winget install --id DBBrowserForSQLite.DBBrowserForSQLite
```

### ติดตั้งแบบ Silent (ไม่ต้องกด Next):

```powershell
winget install --id DBBrowserForSQLite.DBBrowserForSQLite `
  --silent `
  --accept-package-agreements `
  --accept-source-agreements
```

**หมายเหตุ:** ต้องรัน PowerShell **As Administrator** และอนุมัติ UAC dialog

---

## 🔽 **วิธีที่ 2: ดาวน์โหลด + ติดตั้งด้วย Command (เร็วที่สุด)**

### Step 1: ดาวน์โหลดไฟล์ .msi

```powershell
# สร้างโฟลเดอร์ชั่วคราว
$downloadPath = "$env:TEMP\DBBrowser.msi"

# ดาวน์โหลด (v3.13.1)
Invoke-WebRequest -Uri "https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v3.13.1/DB.Browser.for.SQLite-v3.13.1-win64.msi" -OutFile $downloadPath

Write-Host "Downloaded to: $downloadPath"
```

### Step 2: ติดตั้งแบบ Silent

```powershell
# ติดตั้งแบบไม่มี UI (Silent)
Start-Process msiexec.exe -ArgumentList "/i `"$downloadPath`" /quiet /qn" -Wait

Write-Host "Installation completed!"
```

### Step 3: ตรวจสอบการติดตั้ง

```powershell
# หา path ที่ติดตั้ง
$programPath = "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"

if (Test-Path $programPath) {
    Write-Host "✅ Installed successfully at: $programPath"
} else {
    Write-Host "❌ Installation failed"
}
```

---

## 📦 **วิธีที่ 3: ใช้ Chocolatey**

### ติดตั้ง Chocolatey (ถ้ายังไม่มี):

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### ติดตั้ง DB Browser:

```powershell
choco install sqlitebrowser -y
```

---

## 🎯 **คำสั่งเดียวจบ (แนะนำที่สุด!)**

Copy & Paste คำสั่งนี้ใน **PowerShell (Run as Administrator)**:

```powershell
# ดาวน์โหลดและติดตั้งอัตโนมัติ
$url = "https://github.com/sqlitebrowser/sqlitebrowser/releases/download/v3.13.1/DB.Browser.for.SQLite-v3.13.1-win64.msi"
$output = "$env:TEMP\DBBrowser.msi"

Write-Host "⬇️  Downloading DB Browser for SQLite..."
Invoke-WebRequest -Uri $url -OutFile $output

Write-Host "📦 Installing..."
Start-Process msiexec.exe -ArgumentList "/i `"$output`" /quiet /qn" -Wait

Write-Host "🧹 Cleaning up..."
Remove-Item $output

Write-Host "✅ Installation completed!"
Write-Host "📍 Location: C:\Program Files\DB Browser for SQLite\"
```

---

## 🚀 **เปิดโปรแกรมหลังติดตั้ง**

```powershell
# เปิด DB Browser
& "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"

# หรือเปิดพร้อม database file
& "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe" "d:\Development\Projects\Peak-Load-Demand-Monitoring\src\backend\energy_data.db"
```

---

## 🔍 **ตรวจสอบว่าติดตั้งแล้วหรือยัง**

```powershell
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
    Where-Object {$_.DisplayName -like "*DB Browser*"} |
    Select-Object DisplayName, DisplayVersion, InstallLocation
```

---

## ⚠️ **Troubleshooting**

### ปัญหา: UAC Prompt ถูก Cancel

**แก้ไข**: รัน PowerShell **As Administrator**

### ปัญหา: Error 1602 (Installation cancelled)

**แก้ไข**: ใช้ต้องคำสั่งทีละ step (วิธีที่ 2)

### ปัญหา: Download ช้า

**แก้ไข**: ดาวน์โหลดด้วย browser แล้วติดตั้งด้วย msiexec:

```powershell
msiexec /i "C:\Users\YourUser\Downloads\DB.Browser.for.SQLite-v3.13.1-win64.msi" /quiet
```

---

## 📝 **สรุป**

| วิธี                   | ความเร็ว   | ง่าย       | Silent |
| ---------------------- | ---------- | ---------- | ------ |
| **winget**             | ⭐⭐⭐     | ⭐⭐⭐⭐⭐ | ✅     |
| **Download + msiexec** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐   | ✅     |
| **Chocolatey**         | ⭐⭐⭐⭐   | ⭐⭐⭐     | ✅     |

**แนะนำ**: ใช้ **"คำสั่งเดียวจบ"** (วิธีที่ 2) - เร็วและไม่มี prompt!

---

## ✅ **ตรวจสอบหลังติดตั้ง**

```powershell
# ตรวจว่าติดตั้งสำเร็จ
Test-Path "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"

# เปิดโปรแกรม
Start-Process "C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe"
```
