# BJT DC Bias Web App — ENG29 2121 Lab 02

Web Application สำหรับคำนวณ **DC Operating Point** ของวงจรขยาย
NPN Common-Emitter 3 แบบ: **Voltage-Divider Bias**, **Fixed Bias** และ
**Emitter Bias (emitter-feedback)** — พัฒนาด้วย Python/Flask ตามข้อกำหนด
ของวิชา ENG29 2121 (Computer Programming for Electrical Engineers)
ภาค 2/2569 Lab 02 (สองวงจรหลังเป็นส่วนต่อขยายเมื่อ 17 พ.ย. 2569)

หน้าเว็บเป็น **หน้าเดียว `/` แบ่งเป็น 3 ส่วนพับได้** (`<details>`) ไม่ใช้ JavaScript:
แต่ละส่วนมีฟอร์มและตารางผลของตัวเอง กด Calculate ส่วนไหนก็เปิดส่วนนั้น
URL เก่า `/fixed` และ `/emitter` ยังใช้ได้ โดย redirect ไป `/?circuit=fixed`
และ `/?circuit=emitter` (รวมหน้าเมื่อ 17 พ.ย. 2569)

## สมมติฐานการคำนวณ

ใช้ **Forward-Active Approximation**: β คงที่ (ไม่ขึ้นกับ IC) และ VBE คงที่
(รับค่าจากผู้ใช้ ปกติ ≈ 0.7 V) โดยไม่สน effects อื่น (Early effect,
resistance ของ junction ฯลฯ) — **ถ้าค่าที่ป้อนทำให้วงจรอยู่นอก
forward-active region** (Cutoff: VTH ≤ VBE หรือ Saturation: VCE < 0.2 V)
โปรแกรมจะแสดงค่าพร้อม Warning ว่าผลลัพธ์ไม่น่าเชื่อถือภายใต้แบบจำลองนี้

## โครงสร้างไฟล์

```
BJT DC Bias Web App/
├── app.py                  # Flask routes หน้าเดียว (GET / + 3 POST /calculate* + redirect /fixed , /emitter)
├── dc_bias.py              # engineering module: solve/solve_fixed/solve_emitter + validation + region (ไม่รู้จัก HTML/HTTP)
├── templates/
│   ├── index.html          # หน้าเดียว: 3 <details> (Voltage-Divider / Fixed / Emitter) แต่ละส่วนมีฟอร์มของตัวเอง
│   └── _results.html       # warning + region + ตารางผล 9 ค่า (include ร่วมทุกส่วน)
├── static/style.css        # การแสดงผล (รวม .circuit แทน .nav)
├── tests/
│   ├── test_dc_bias.py     # unit tests สมการวิศวกรรม (17 tests)
│   └── test_web.py         # Flask HTTP tests ผ่าน test client (22 tests)
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

4. เปิด browser ที่ **http://127.0.0.1:5000/** แล้วกดหัวข้อส่วนที่ต้องการ
   ( Voltage-Divider / Fixed / Emitter ) เพื่อขยายฟอร์ม:

| ส่วนในหน้าเดียว `/` | ฟอร์ม | Route POST | ค่า default |
|---|---|---|---|
| **Voltage-Divider Bias** (`/`) | VCC, R1, R2, RC, RE, β, VBE | `/calculate` | 12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, 100, 0.70 V |
| **Fixed Bias** (`/?circuit=fixed`, `/fixed` redirect) | VCC, RB, RC, β, VBE | `/calculate-fixed` | 12 V, RB 470 kΩ, RC 2.2 kΩ, 100, 0.70 V |
| **Emitter Bias** (`/?circuit=emitter`, `/emitter` redirect) | VCC, RB, RC, RE, β, VBE | `/calculate-emitter` | 12 V, RB 470 kΩ, RC 2.2 kΩ, RE 1 kΩ, 100, 0.70 V |

กรอกค่าแล้วกด **Calculate DC Bias** — ผลลัพธ์แสดงเป็นตารางพร้อม region
ใต้ส่วนที่กด (ส่วนนั้นจะเปิดอัตโนมัติ ส่วนอื่นยังพับอยู่)

สมการของ Fixed Bias: `IB = (VCC−VBE)/RB`, `VE = 0`, `VCE = VC`
ของ Emitter Bias: `IB = (VCC−VBE)/(RB+(β+1)RE)`, `VE = IE·RE`
ทั้งสองใช้ `VTH = VCC`, `RTH = RB` และเช็ค cutoff/saturation เหมือนส่วน Voltage-Divider

## การรัน Automated Tests

จาก root ของ repository (venv ยังเปิดอยู่ หรือใช้ `.venv\Scripts\python.exe`):

```powershell
python -m unittest discover -s tests -v
```

ผลที่คาดหวัง: `Ran 39 tests ... OK`
(test_dc_bias 17 ตัว + test_web 22 ตัว)

## ข้อมูลทดลองอ้างอิง

VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100,
VBE = 0.70 V → VTH = 2.164 V, RTH = 18.033 kΩ, IB = 12.299 µA,
IC = 1.230 mA, IE = 1.242 mA, VE = 1.242 V, VB = 1.942 V, VC = 9.294 V,
VCE = 8.052 V (forward-active)

ชุดอ้างอิงวงจรใหม่ (VCC = 12 V, RB = 470 kΩ, RC = 2.2 kΩ, β = 100, VBE = 0.70 V):
- Fixed Bias → IB = 24.043 µA, IC = 2.404 mA, VE = 0 V, VCE = 6.711 V
- Emitter Bias (RE = 1 kΩ) → IB = 19.790 µA, IC = 1.979 mA,
  VE = 1.999 V, VCE = 5.647 V

## การทำงานตามเกณฑ์ตรวจรับ A1–A7

| เกณฑ์ | สิ่งที่พิสูจน์ | ที่อยู่ |
|---|---|---|
| A1 · GET / | HTTP 200 + ฟอร์มครบ 7 ช่อง | `test_web.py::test_get_index_returns_form` |
| A2 · POST /calculate | Python คำนวณจริง ไม่มีค่าฮาร์ดโคด | `test_web.py::test_post_calculate_shows_result` |
| A3 · Engineering reference | ผลตรงการคำนวณมืออิสระ | `test_dc_bias.py::test_solve_reference_values` |
| A4 · Validation | R≤0/β≤0/ไม่ใช่ตัวเลข/inf/NaN/ช่องว่าง → error ไม่ล้ม | `test_dc_bias.py::TestValidation`, `test_web.py::test_post_*` |
| A5 · Region warnings | Cutoff/Saturation แสดง Warning | `test_dc_bias.py::TestRegionWarnings`, `test_web.py::test_*_warning_displayed` |
| A6 · Tests | 17 unit + 22 HTTP = 39 tests ผ่านหมด | คำสั่งรัน tests ด้านบน |
| A7 · Reproducibility | clone → ติดตั้ง → รัน → tests ตาม README นี้ | ขั้นตอนด้านบน |
| ส่วนต่อขยาย · Solver | Fixed/Emitter ตรงค่าคำนวณมือ + validation + cutoff/saturation | `test_dc_bias.py::TestFixedEmitter` |
| ส่วนต่อขยาย · หน้าเดียว 3 ส่วน | 3 `<details>` ใน `/`, เปิดเฉพาะส่วนที่ POST, query param, redirect URL เก่า, error/warning ค้างค่า | `test_web.py::TestFixedEmitterWeb` |

## หมายเหตุความปลอดภัย

- Flask debug server ใช้เฉพาะการพัฒนาบนเครื่องตัวเอง — ห้ามเปิดให้เครือข่าย
  สาธารณะ
- ห้าม commit `.venv/`, `__pycache__/`, `.env` (มี `.gitignore` กันไว้แล้ว)
