# BJT DC Bias Web App — ENG29 2121 Lab 02

Web Application สำหรับคำนวณ **DC Operating Point** ของวงจรขยาย
NPN Common-Emitter แบบ **Voltage-Divider Bias** — พัฒนาด้วย Python/Flask
ตามข้อกำหนดของวิชา ENG29 2121 (Computer Programming for Electrical
Engineers) ภาค 2/2569 Lab 02

## สมมติฐานการคำนวณ

ใช้ **Forward-Active Approximation**: β คงที่ (ไม่ขึ้นกับ IC) และ VBE คงที่
(รับค่าจากผู้ใช้ ปกติ ≈ 0.7 V) โดยไม่สน effects อื่น (Early effect,
resistance ของ junction ฯลฯ) — **ถ้าค่าที่ป้อนทำให้วงจรอยู่นอก
forward-active region** (Cutoff: VTH ≤ VBE หรือ Saturation: VCE < 0.2 V)
โปรแกรมจะแสดงค่าพร้อม Warning ว่าผลลัพธ์ไม่น่าเชื่อถือภายใต้แบบจำลองนี้

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes: GET / และ POST /calculate (parse + แปลงหน่วย kΩ→Ω)
├── dc_bias.py              # engineering module: สมการ DC bias + validation + region (ไม่รู้จัก HTML/HTTP)
├── templates/index.html    # ฟอร์มอินพุต + ตารางผลลัพธ์ (Jinja2)
├── static/style.css        # การแสดงผล
├── tests/
│   ├── test_dc_bias.py     # unit tests สมการวิศวกรรม (9 tests)
│   └── test_web.py         # Flask HTTP tests ผ่าน test client (9 tests)
├── requirements.txt        # flask>=3.0
├── README.md               # เอกสารนี้
├── AGENTS.md               # ข้อตกลงสำหรับ AI coding agent
└── docs/                   # design-note, validation, reflection
```

## การติดตั้งและรัน (Windows — ใช้ `py`)

> บนเครื่องที่คำสั่ง `python` ถูก Microsoft Store alias ยึดไว้ ให้ใช้ `py`
> แทน (เช่นเครื่องห้อง Lab) ทุกคำสั่งด้านล่างรันจาก **root ของ repository**

1. สร้างและเปิดใช้ virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

2. ติดตั้ง dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. รันเว็บ (debug server สำหรับพัฒนา):

```powershell
python -m flask --app app run --debug
```

4. เปิด browser ไปที่ **http://127.0.0.1:5000/** → กรอกค่า → กด
   **Calculate DC Bias**

## การรัน Automated Tests

จาก root ของ repository (venv ยังเปิดอยู่ หรือใช้ `.venv\Scripts\python.exe`):

```powershell
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 18 tests ... OK`
(test_dc_bias 9 ตัว + test_web 9 ตัว)

## ข้อมูลทดลองอ้างอิง

VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100,
VBE = 0.70 V → VTH = 2.164 V, RTH = 18.033 kΩ, IB = 12.299 µA,
IC = 1.230 mA, IE = 1.242 mA, VE = 1.242 V, VB = 1.942 V, VC = 9.294 V,
VCE = 8.052 V (forward-active)

## การทำงานตามเกณฑ์ตรวจรับ A1–A7

| เกณฑ์ | สิ่งที่พิสูจน์ | ที่อยู่ |
|---|---|---|
| A1 · GET / | HTTP 200 + ฟอร์มครบ 7 ช่อง | `test_web.py::test_get_index_returns_form` |
| A2 · POST /calculate | Python คำนวณจริง ไม่มีค่าฮาร์ดโคด | `test_web.py::test_post_calculate_shows_result` |
| A3 · Engineering reference | ผลตรงการคำนวณมืออิสระ | `test_dc_bias.py::test_solve_reference_values` |
| A4 · Validation | R≤0/β≤0/ไม่ใช่ตัวเลข/inf/NaN/ช่องว่าง → error ไม่ล้ม | `test_dc_bias.py::TestValidation`, `test_web.py::test_post_*` |
| A5 · Region warnings | Cutoff/Saturation แสดง Warning | `test_dc_bias.py::TestRegionWarnings`, `test_web.py::test_*_warning_displayed` |
| A6 · Tests | 9 unit + 9 HTTP = 18 tests ผ่านหมด | คำสั่งรัน tests ด้านบน |
| A7 · Reproducibility | clone → ติดตั้ง → รัน → tests ตาม README นี้ | ขั้นตอนด้านบน |

## หมายเหตุความปลอดภัย

- Flask debug server ใช้เฉพาะการพัฒนาบนเครื่องตัวเอง — ห้ามเปิดให้เครือข่าย
  สาธารณะ
- ห้าม commit `.venv/`, `__pycache__/`, `.env` (มี `.gitignore` กันไว้แล้ว)
