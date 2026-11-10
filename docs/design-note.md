# Design Note — BJT DC Bias Web App (Lab 02)

วิชา ENG29 2121 · Computer Programming for Electrical Engineers · 2/2569
สถานะ: **อนุมัติแล้ว** (ผ่านกระบวนการ Brainstorming ตาม Superpowers workflow)

## Intent / เป้าหมาย

สร้าง Flask Web Application ที่เล็กที่สุดแต่ใช้งานได้จริง สำหรับคำนวณ DC Operating Point
ของวงจร NPN Common-Emitter แบบ **Voltage-Divider Bias** — จบในคาบเดียว ได้คะแนนเต็ม
ตาม rubric 10 คะแนน และเป็นฐานให้ Lab ถัดไป (W3–W11) ต่อยอด

## Goals

- หน้าเดียว: ฟอร์มรับ `VCC, R1, R2, RC, RE, β, VBE` → กด Calculate → ตารางผล
- Python Backend คำนวณจริง (`dc_bias.py` แยกจาก web layer ไม่รู้จัก HTML/HTTP)
- ผลลัพธ์ `VB, VE, VC, VCE, IC` (+ `IB, IE, VTH, RTH`) พร้อมหน่วยกำกับ
- Validation: `R≤0, β≤0, VCC≤0, ค่าไม่ใช่ตัวเลข/ไม่ครบ` → error ชัดเจน หน้าไม่ล้ม
- Region warning: cutoff (`VTH ≤ VBE`) และ saturation (`VCE < 0.2 V`) — แจ้งว่า
  forward-active approximation ใช้ไม่ได้กับค่าชุดนี้
- Tests: ≥3 unit tests (engineering math) + ≥1 Flask test-client test
- เปิดใช้ผ่าน `http://127.0.0.1:5000/` ได้, commit ผ่าน GitHub Desktop

## Non-goals (ขอบเขต Week 2 — DC เท่านั้น)

- ไม่มี AC / small-signal / Bode plot / transient / signal generator
- ไม่มี bias types อื่น (Fixed Bias, Emitter Bias = Lab W3)
- ไม่มี SPICE/ngspice solver (Lab W4)
- ไม่มี FET, interactive schematic, overlay animation
- ไม่ต้องลอก UI จากภาพ concept ทุกพิกเซล

## Anti-goals (ถ้าเกิดถือว่าล้มเหลวแม้รันได้)

- Hardcode ค่าผลลัพธ์ใน HTML (ต้องคำนวณจากอินพุตจริงเสมอ)
- แสดงผลใน region ที่แบบจำลองใช้ไม่ได้โดยไม่มี warning
- Commit `.venv/` หรือ secrets ขึ้น GitHub

## Constraints

- โครงสร้างไฟล์ตามที่ Lab กำหนด: `app.py`, `dc_bias.py`, `templates/index.html`,
  `static/style.css`, `tests/`, `requirements.txt`, `README.md`
- เครื่องนี้เรียก Python ผ่าน **`py`** (คำสั่ง `python` ถูก Store alias ยึด) —
  README ต้องใช้คำสั่ง `py -m ...` ให้ตรงเครื่องจริง
- Commit/Push ทำผ่าน **GitHub Desktop** (นักศึกษาเป็นผู้กดเอง)
- Repo: `Documents\GitHub\BJT DC Bias Web App` (Initial commit มีแล้ว, ยังไม่ publish)

## Approaches ที่พิจารณา

| แนวทาง | เหตุผลที่ไม่เลือก/เลือก |
|---|---|
| **A. Flask multi-file server-rendered (เลือก)** | ตรงสเปค Lab ครบทุกเกณฑ์ (A1–A7), test ง่าย, จบในเวลา |
| B. Single-file app.py รวมทุกอย่าง | ละเมิดเกณฑ์ multi-file/แยก engineering logic — เสียคะแนน |
| C. SPA + AJAX fetch JSON | เพิ่ม JavaScript โดยไม่เพิ่มคะแนน, ทำ HTTP test ซับซ้อนขึ้น |
| D. ขยาย scope (AC, bias หลายแบบ) | ขัด scope Week 2 ชัดเจน เสี่ยงไม่จบในคาบ |

## การตัดสินใจ (call ของ AI เสนอ นักศึกษาอนุมัติ)

1. **UI ภาษาไทย + ศัพท์เทคนิคอังกฤษ** (VB, VE, "Calculate DC Bias") ตามบริบทรายวิชา
2. **หน่วยฟอร์ม:** แรงดันเป็น V, ตัวต้านทานเป็น kΩ (แปลงเป็น Ω ก่อนคำนวณใน backend), β ไม่มีหน่วย
3. **Server-rendered** `POST /calculate` — ไม่ใช้ JavaScript เพิ่ม
4. **ค่า default ในฟอร์ม** = ชุดข้อมูลทดลองของ Lab: VCC=12 V, R1=100 kΩ, R2=22 kΩ,
   RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V
5. **แสดงค่ากลาง** VTH, RTH, IB, IE ในหน้าผล เพื่อตรวจสอบย้อนสมการได้ (เกณฑ์ A3)
6. รับค่า `VBE` เป็นอินพุตจากฟอร์ม (ไม่ fix 0.7) ตามสเปค Lab

## สมการอ้างอิง (Forward-Active Approximation)

```
VTH = VCC · R2 / (R1 + R2)          RTH = R1·R2 / (R1 + R2)
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β·IB                           IE  = (β+1)·IB
VE  = IE·RE                          VB  = VE + VBE
VC  = VCC − IC·RC                    VCE = VC − VE
```

เกณฑ์ region: `VTH ≤ VBE` → Cutoff warning · `VCE < 0.2 V` → Saturation warning
(แสดงผลได้แต่ต้องมี warning ว่า approximation ใช้ไม่ได้)

## สิ่งที่เหลือให้ขั้น Build

- โครงร่างไฟล์/ฟังก์ชันจริง และลำดับงาน (อยู่ใน Implementation Plan ถัดไป)
