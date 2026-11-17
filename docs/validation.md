# Validation Record — BJT DC Bias Web App

บันทึกการตรวจสอบความถูกต้องของผลการคำนวณ (ENG29 2121 · Lab 02)
วันที่ตรวจ: 10 พฤศจิกายน 2569 · ผู้ตรวจ: นักศึกษา + AI agent

## 1. ค่าอ้างอิงอิสระ (คำนวณมือ) เทียบผลจากเว็บ

ชุดข้อมูลทดลองของ Lab: VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V — คำนวณมือด้วยสมการ
VTH = VCC·R2/(R1+R2), RTH = R1·R2/(R1+R2),
IB = (VTH−VBE)/(RTH+(β+1)RE), IC = β·IB, IE = (β+1)·IB,
VE = IE·RE, VB = VE+VBE, VC = VCC−IC·RC, VCE = VC−VE

| ค่า | คำนวณมือ (อิสระ) | ผลจากเว็บ (`POST /calculate`) | ตรงกัน |
|---|---|---|---|
| VTH | 2.163934 V | 2.164 V | ✓ |
| RTH | 18.033 kΩ | 18.033 kΩ | ✓ |
| IB | 12.299 µA | 12.299 µA | ✓ |
| IC | 1.230 mA | 1.230 mA | ✓ |
| IE | 1.242 mA | 1.242 mA | ✓ |
| VE | 1.242 V | 1.242 V | ✓ |
| VB | 1.942 V | 1.942 V | ✓ |
| VC | 9.294 V | 9.294 V | ✓ |
| VCE | 8.052 V | 8.052 V | ✓ |

สรุป: ผลจาก Python Backend ตรงกับการคำนวณมืออย่างอิสระครบทุกค่า
ภายใต้แบบจำลอง Forward-Active เดียวกัน — VCE = 8.052 V > 0.2 V
และ VTH > VBE จึงอยู่ใน forward-active region จริง

## 2. ผล Automated Tests (รอบสุดท้าย)

คำสั่ง: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
(จาก repo root, venv ที่ติดตั้งจาก `requirements.txt`)

ผล (หลังเพิ่ม Fixed/Emitter + รวมหน้าเดียว + code review fix): **Ran 40 tests — OK (ผ่านทั้งหมด)**
- `tests/test_dc_bias.py` — 17 tests: ค่าอ้างอิง 9 ค่าของ Voltage-Divider,
  ตัวเลขสุดขั้ว (ตรวจ finite), validation 7 กรณี, ข้อความ error ระบุชื่อฟิลด์,
  ค่า inf/NaN ถูกปฏิเสธ, cutoff, ขอบเขต VTH==VBE, saturation **+ 8 tests
 ของ Fixed/Emitter** (ค่าอ้างอิง 2 วงจร, cutoff 2, saturation 2, validate RB/RE, inf/NaN)
- `tests/test_web.py` — 23 tests ผ่าน Flask test client: GET / ฟอร์มครบ
  7 ช่อง, POST คำนวณจริง, ค่าติดลบ, ค่าไม่ใช่ตัวเลข, ค่า inf (1e309),
  ช่องว่าง, ค่ามีช่องว่างรอบตัวเลข, warning cutoff และ saturation
  แสดงบนหน้าเว็บ **+ 13 tests ของหน้าเดียว/ส่วนต่อขยาย** (3 `<details>` ใน `/`,
  query param เปิดส่วนที่ขอ + fallback, redirect URL เก่า 302, POST ผลจริงของ 3 วงจร
  พร้อม `<details open>` ตรงส่วนที่ส่ง, default RB=470.0, RB ติดลบ/ว่าง,
  inf, cutoff, saturation, ค่าที่กรอกค้างหลัง error)

## 3. การทดลองบน Browser จริง (http://127.0.0.1:5000/)

| กรณีที่กรอก | สิ่งที่เห็นบนหน้าเว็บ | ผล |
|---|---|---|
| ค่า default → กด Calculate DC Bias | ตาราง DC Bias Results 9 ค่าพร้อมหน่วย, region = forward_active | ✓ |
| R1 = −5 | กล่องแดง "ข้อมูลไม่ถูกต้อง: R1 ต้องมากกว่า 0" หน้าไม่ล้ม (HTTP 200) | ✓ |
| VCC = abc | กล่องแดง "VCC ต้องเป็นตัวเลข เช่น 12" หน้าไม่ล้ม | ✓ |
| VCC = 1e309 (Python parse เป็น inf) | กล่องแดง "VCC ต้องเป็นจำนวนจำกัด (ห้าม inf หรือ NaN)" หน้าไม่ล้ม — จาก code review fix | ✓ |
| VCC=5, R2=1 (VTH=0.05 V < VBE) | region = cutoff + กล่องส้มเตือน "Cutoff: VTH ≤ VBE ทรานซิสเตอร์ไม่นำ …" | ✓ |
| VCC=1.2, R1=10, R2=100 (VCE≈0.06 V) | region = saturation + กล่องส้มเตือน "Saturation: VCE < 0.2 V … ไม่น่าเชื่อถือ" | ✓ |

## 4. Reproducibility

สร้าง venv ใหม่ทั้งหมด (`.venv-verify`) → `pip install -r requirements.txt`
→ รัน tests → 40/40 ผ่าน → ลบทิ้ง: ยืนยันว่าคนภายนอก clone repo แล้วทำตาม
README ได้ผลเหมือนกัน (เกณฑ์ A7) — ตรวจซ้ำหลังแก้ปัญหาจาก code review
และหลังเพิ่ม Fixed/Emitter Bias + รวมหน้าเดียว (มี tests เพิ่มเป็น 40 ตัว) ก่อนส่งมอบ

## 5. ข้อจำกัดของแบบจำลอง

- Forward-Active Approximation (β คงที่, VBE คงที่) — ไม่ใช่ SPICE
- กรณี cutoff: แสดง IB=IC=IE=0, VB=VTH (ไม่มีกระแสฐาน) พร้อม warning
- กรณี saturation: ค่าที่คำนวณตามสูตรยังแสดง แต่มี warning ว่าใช้เป็นผล
  จำลองที่เชื่อถือได้ไม่ได้

## 6. ส่วนต่อขยาย Fixed/Emitter Bias (17 พ.ย. 2569)

ชุดอ้างอิงคำนวณมือ: VCC=12 V, RB=470 kΩ, RC=2.2 kΩ, β=100, VBE=0.70 V
(เพิ่ม RE=1 kΩ สำหรับ Emitter) — ใช้ VTH=VCC, RTH=RB

| ค่า | Fixed (คำนวณมือ) | ผลจากเว็บ | Emitter (คำนวณมือ) | ผลจากเว็บ | ตรงกัน |
|---|---|---|---|---|---|
| IB | 24.043 µA | 24.043 µA | 19.790 µA | 19.790 µA | ✓ |
| IC | 2.404 mA | 2.404 mA | 1.979 mA | 1.979 mA | ✓ |
| IE | 2.428 mA | 2.428 mA | 1.999 mA | 1.999 mA | ✓ |
| VE | 0 V | 0 V | 1.999 V | 1.999 V | ✓ |
| VB | 0.700 V | 0.700 V | 2.699 V | 2.699 V | ✓ |
| VC | 6.711 V | 6.711 V | 7.646 V | 7.646 V | ✓ |
| VCE | 6.711 V | 6.711 V | 5.647 V | 5.647 V | ✓ |
| region | forward_active | forward_active | forward_active | forward_active | ✓ |

HTTP smoke test บน debug server (`http://127.0.0.1:5000/`, หลังรวมหน้าเดียว):
GET `/`, `/?circuit=fixed`, `/?circuit=emitter` → 200 และ `details_count=3` ทุกครั้ง ·
GET `/fixed` → 302 `/?circuit=fixed` · GET `/emitter` → 302 `/?circuit=emitter` ·
POST `/calculate` → มี `1.230` mA และเปิดส่วน Voltage-Divider ·
POST `/calculate-fixed` → มี `2.404` mA พร้อม `<details open>` ของ Fixed ·
POST `/calculate-emitter` → มี `1.979` mA และ `5.647` V พร้อมเปิดส่วน Emitter

กรณีตรวจเพิ่ม (test client + browser):
RB = −5 → `RB ต้องมากกว่า 0` · RB ว่าง → `RB ต้องเป็นตัวเลข` ·
`vcc = 1e309` → `VCC ต้องเป็นจำนวนจำกัด` · VCC=0.5 V → Cutoff warning ·
RB=10 kΩ → Saturation warning — ทุกกรณี HTTP 200 หน้าไม่ล้ม
(ข้อความ error/warning ค้างอยู่ใน **ส่วนที่ส่งเท่านั้น** หลังรวมหน้าเดียว)

จำนวน tests รวมหลังส่วนต่อขยาย + รวมหน้าเดียว + code review fix:
**40 tests (17 unit + 23 HTTP) — OK**

การตรวจเพิ่มจาก code review (17 พ.ย. 2569): หลัง POST วงจรใดวงจรหนึ่งด้วยค่า
`vcc=5, rc=3.3, beta=200, vbe=0.9` เฉพาะฟอร์มของวงจรนั้นที่ค้างค่า
(fixed ยังค้าง `rb` ที่ส่งด้วย) — ฟอร์มอีกสองส่วนกลับไปใช้ default `12.0 / 2.2 / 100.0 / 0.7`
ตามสเปค ผ่าน `test_post_entered_values_stay_in_submitted_section`
