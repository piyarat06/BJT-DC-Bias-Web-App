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

ผล: **Ran 15 tests — OK (ผ่านทั้งหมด)**
- `tests/test_dc_bias.py` — 7 tests: ค่าอ้างอิง 9 ค่า, ตัวเลขสุดขั้ว,
  validation 7 กรณี, ข้อความ error ระบุชื่อฟิลด์, cutoff, ขอบเขต
  VTH==VBE, saturation
- `tests/test_web.py` — 8 tests ผ่าน Flask test client: GET /, POST
  คำนวณจริง, ค่าติดลบ, ค่าไม่ใช่ตัวเลข, ช่องว่าง, ค่ามีช่องว่างรอบ
  ตัวเลข, warning cutoff และ saturation แสดงบนหน้าเว็บ

## 3. การทดลองบน Browser จริง (http://127.0.0.1:5000/)

| กรณีที่กรอก | สิ่งที่เห็นบนหน้าเว็บ | ผล |
|---|---|---|
| ค่า default → กด Calculate DC Bias | ตาราง DC Bias Results 9 ค่าพร้อมหน่วย, region = forward_active | ✓ |
| R1 = −5 | กล่องแดง "ข้อมูลไม่ถูกต้อง: R1 ต้องมากกว่า 0" หน้าไม่ล้ม (HTTP 200) | ✓ |
| VCC = abc | กล่องแดง "VCC ต้องเป็นตัวเลข เช่น 12" หน้าไม่ล้ม | ✓ |
| VCC=5, R2=1 (VTH=0.05 V < VBE) | region = cutoff + กล่องส้มเตือน "Cutoff: VTH ≤ VBE ทรานซิสเตอร์ไม่นำ …" | ✓ |
| VCC=1.2, R1=10, R2=100 (VCE≈0.06 V) | region = saturation + กล่องส้มเตือน "Saturation: VCE < 0.2 V … ไม่น่าเชื่อถือ" | ✓ |

## 4. Reproducibility

สร้าง venv ใหม่ทั้งหมด (`.venv-verify`) → `pip install -r requirements.txt`
→ รัน tests → 15/15 ผ่าน → ลบทิ้ง: ยืนยันว่าคนภายนอก clone repo แล้วทำตาม
README ได้ผลเหมือนกัน (เกณฑ์ A7)

## 5. ข้อจำกัดของแบบจำลอง

- Forward-Active Approximation (β คงที่, VBE คงที่) — ไม่ใช่ SPICE
- กรณี cutoff: แสดง IB=IC=IE=0, VB=VTH (ไม่มีกระแสฐาน) พร้อม warning
- กรณี saturation: ค่าที่คำนวณตามสูตรยังแสดง แต่มี warning ว่าใช้เป็นผล
  จำลองที่เชื่อถือได้ไม่ได้
