# Design Note — Fixed Bias + Emitter Bias (เพิ่มเติมจาก Lab 02)

วันที่: 17 พฤศจิกายน 2569 · วิชา ENG29 2121 · สถานะ: อนุมัติโดยเจ้าของงาน (ขยาย scope จาก Lab 02)

## Intent / เป้าหมาย

ต่อยอดเว็บคำนวณ DC Bias ที่มีอยู่ (Voltage-Divider Bias) ให้คำนวณ Operating Point ของ
NPN Common-Emitter แบบ **Fixed Bias** และ **Emitter Bias (emitter-feedback with RB จาก VCC)**
ได้ด้วย โดยยังรันที่ `http://127.0.0.1:5000/` และยังใช้แบบจำลอง Forward-Active เดิม

## Goals

- เปิด `/` ได้เหมือนเดิมทุกประการ (ยอดเดิม 18 tests ต้องยังผ่าน)
- เพิ่มหน้า `/fixed` (ฟอร์ม VCC, RB, RC, β, VBE) และ `/emitter` (VCC, RB, RC, RE, β, VBE)
  พร้อม POST `/calculate-fixed` และ `/calculate-emitter` ที่คำนวณจริงใน backend
- ผลลัพธ์ชุดเดิม (VTH, RTH, IB, IC, IE, VE, VB, VC, VCE) แสดงครบ พร้อมหน่วย
- ใช้ VTH = VCC, RTH = RB สำหรับสองวงจรใหม่ (Thevenin ของแหล่งจ่าย + RB)
- ตรวจ cutoff (`VTH ≤ VBE`) และ saturation (`VCE < 0.2 V`) พร้อม warning ภาษาไทยแบบเดิม
- Validation: finite, R > 0, β > 0, VBE ≥ 0, ช่องว่าง/ตัวเลขไม่ถูกต้อง → error ระบุชื่อฟิลด์
- มีแถบลิงก์สลับ 3 วงจร, UI ไทย + ศัพท์เทคนิคอังกฤษ, ไม่ใช้ JavaScript
- อัปเดต tests, README, docs/design-note.md, docs/validation.md ให้ตรง scope ใหม่

## Non-goals / Anti-goals

- ไม่เพิ่ม AC/small-signal/transient/SPICE/FET/วงจรอื่นนอกเหนือ 3 แบบนี้
- ไม่เปลี่ยนสมการ/ผล/ข้อความ warning ของ Voltage-Divider เดิม
- ไม่ใช้ JS, ไม่ hardcode ผลลัพธ์, ไม่ commit `.venv/`

## Constraints

- โครงสร้างเดิม: `app.py`, `dc_bias.py`, `templates/`, `static/`, `tests/`, `requirements.txt`
- หน่วยฟอร์ม: แรงดัน V, ตัวต้านทาน kΩ (แปลงเป็น Ω ใน web layer), β ไม่มีหน่วย
- Runner: `.venv\Scripts\python.exe -m unittest discover -s tests -v` (system `py` ไม่มี Flask)
- Git: commit เฉพาะ local; นักศึกษาเป็นคน push ผ่าน GitHub Desktop

## Approaches ที่พิจารณา

| แนวทาง | เหตุผล |
|---|---|
| **A. 3 หน้า + 3 route (เลือก)** | ไม่กระทบ `/` เดิม, ฟอร์มชัดเจน, test แยกง่าย, ไม่ใช้ JS |
| B. หน้าเดียว + POST เลือกวงจร | หน้าเดียวแต่กด 2 ขั้นตอนและ render ตาม state ซับซ้อนกว่า |
| C. หน้าเดียว + dropdown + JS | ลื่นที่สุดแต่เพิ่ม JS ซึ่งขัดกับการตัดสินใจเดิม |

## สมการอ้างอิง (Forward-Active Approximation)

```
Fixed:   VTH = VCC, RTH = RB, RE = 0
Emitter: VTH = VCC, RTH = RB
IB  = (VTH − VBE) / (RTH + (β+1)·RE)
IC  = β·IB        IE = (β+1)·IB
VE  = IE·RE       VB = VE + VBE
VC  = VCC − IC·RC VCE = VC − VE
```

`Fixed` คือกรณี RE = 0 ของ `Emitter` จึงใช้ helper ร่วมกันได้
 cutoff → IB=IC=IE=0, VE=0, VB=VTH, VC=VCC, VCE=VCC

## ค่า default และค่าอ้างอิง (คำนวณมือ)

| วงจร | VCC | RB | RC | RE | β | VBE | IB | IC | IE | VE | VB | VC | VCE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Fixed | 12 V | 470 kΩ | 2.2 kΩ | — | 100 | 0.70 V | 24.043 µA | 2.404 mA | 2.428 mA | 0 V | 0.700 V | 6.711 V | 6.711 V |
| Emitter | 12 V | 470 kΩ | 2.2 kΩ | 1 kΩ | 100 | 0.70 V | 19.790 µA | 1.979 mA | 1.999 mA | 1.999 V | 2.699 V | 7.646 V | 5.647 V |

## สิ่งที่เหลือให้ขั้น Build

- แยก helper คำนวณ region ใช้ร่วมทั้ง 3 วงจร, เพิ่ม route/template/partial, tests, เอกสาร
- รันชุด tests เดิม + ใหม่ให้ผ่านหมดก่อนส่งมอบ
