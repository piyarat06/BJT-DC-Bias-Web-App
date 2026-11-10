# Reflection — Lab 02

ชื่อ-สกุล: ................................................. วันที่: 10 พฤศจิกายน 2569

## คำถามรายบุคคลจาก Lab §10

**1. เหตุใดการเปิด `templates/index.html` ตรง ๆ (ผ่าน file://) จึงไม่เท่ากับ
การรัน Flask?**

เปิดไฟล์ตรง ๆ = ให้เบราว์เซอร์เป็นคนแสดงไฟล์เอง ไม่มี Flask อยู่ตรงกลาง
เลย เห็นผลทันทีสามอย่าง (1) บนหน้าจะโผล่ข้อความ `{{ defaults.vcc }}`
ดิ ๆ เพราะ `{{ ... }}` ไม่ใช่ภาษา HTML แต่เป็น template syntax ของ
Jinja2 ที่ต้องมีตัว render — คือ Flask — เติมค่าให้ก่อนส่งออกมาเป็น HTML
จริง (2) กดปุ่ม Calculate DC Bias ก็ไม่มีใครรับ เพราะฟอร์มส่ง POST ไปที่
route `/calculate` ซึ่งจะมีอยู่ได้ก็ต่อเมื่อมี server รันอยู่เท่านั้น และ
(3) ไม่มี Python ตัวไหนคำนวณสมการ DC bias ให้เลย — สรุปคือไฟล์ HTML ใน
โปรเจกต์นี้เป็นแค่ "หน้ากาก" ที่ต้องถูก render และป้อนข้อมูลโดย web
application เท่านั้น

**2. ฟอร์มส่งข้อมูลไป Python อย่างไร?**

ฟอร์มใน `templates/index.html` ประกาศไว้ว่า `<form method="post"
action="/calculate">` เมื่อกด submit เบราว์เซอร์จะรวมค่าจาก input ทั้ง 7
ช่อง (name = vcc, r1, r2, rc, re, beta, vbe) เป็น request body แบบ
form-encoded เช่น `vcc=12&r1=100&...` แล้วส่ง **HTTP POST** ไปที่ URL
`/calculate` — ดูได้จริงใน DevTools → Network ฝั่ง server มี
`@app.route("/calculate", methods=["POST"])` ใน `app.py` รับไว้ ข้อมูล
อยู่ใน `request.form` (dict) → `parse_form()` แปลงเป็นตัวเลข ตรวจความ
ถูกต้อง แปลงหน่วย kΩ→Ω → เรียก `solve()` ใน `dc_bias.py` คำนวณ → ได้
ผลลัพธ์ส่งกลับไป `render_template` เป็น HTML แล้วตอบกลับมาที่เบราว์เซอร์

**3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่? เพราะอะไร?**

ไม่ต้อง เพราะโปรเจกต์นี้แยก layer ไว้ชัด — สมการ DC bias ทั้งหมดอยู่ใน
`dc_bias.py` จุดเดียว ส่วน `templates/index.html` มีหน้าที่แสดงค่าจาก
ตัวแปรที่ Python ส่งมา (เช่น `result.vth`, `result.ic`) เท่านั้น ไม่มี
สมการฟิสิกส์ทำงานอยู่ในไฟล์ HTML ถ้าแก้สูตร IC ใน `dc_bias.py` ค่าที่
แสดงบนหน้าเว็บจะเปลี่ยนตามทันทีโดยไม่ต้องแตะ HTML เลย (มีข้อยกเว้น
เล็กน้อย: footer ของหน้ามีข้อความสมการอ้างอิงไว้อ่านประกอบ ถ้าสมการ
เปลี่ยนจริงก็ควรแก้ข้อความนั้นให้ตรง แต่นั่นคือแก้เอกสารอ้างอิง ไม่ใช่
แก้ logic) — ประโยชน์ของการแยกแบบนี้: แก้ physics ที่เดียวจบ, รัน test
วิศวกรรม (`test_dc_bias.py`) ได้โดยไม่ต้องเปิดเว็บ และแก้หน้าตาโดยไม่
เสี่ยงพังสมการ

**4. ทำไมผลใน region ที่แบบจำลองใช้ไม่ได้ (cutoff/saturation) จึงต้องมี
Warning?**

แบบจำลอง Forward-Active ตั้งสมมติฐานไว้ว่าทรานซิสเตอร์ทำงานใน active
region คือ IC ถูกควบคุมโดย IB ผ่าน IC = β·IB และ VBE คงที่ สมมติฐาน
นี้ใช้ไม่ได้สองกรณี (a) **cutoff**: ถ้า VTH ≤ VBE junction ฐาน–อิมิตเตอร์
ไม่ถูก forward-bias จริง IB จึงเป็น 0 จริง ๆ ไม่ใช่ค่าจากสูตร IB =
(VTH−VBE)/(...) โปรแกรมจึงตัดเป็น cutoff แสดง IB=IC=IE=0, VB=VTH,
VC=VCE=VCC และ (b) **saturation**: ถ้า VCE < 0.2 V กระแส IC จะถูกจำกัด
โดยวงจรภายนอก (RC, RE, VCC) ไม่ใช่โดย IB อีกต่อไป ค่าที่คำนวณตามสูตร
forward-active จึงเกินจริง — ถ้าไม่มี warning ผู้ใช้จะเห็นตารางตัวเลขที่
ดูสมบูรณ์แบบแล้วเอาไปใช้ออกแบบวงจร/เลือกค่า components ต่อโดยเข้าใจว่า
ถูกต้อง ซึ่งเป็นอันตรายในงานวิศวกรรมจริง warning จึงเป็นการบอกตรง ๆ ว่า
"ชุดค่านี้อยู่นอกขอบเขตที่แบบจำลองตั้งสมมติไว้ อย่าเชื่อตัวเลขตามตาราง"

## สิ่งที่ AI ช่วย / สิ่งที่ตรวจเอง

- **AI ช่วย** — เขียนโค้ดตามขั้นตอน workflow (brainstorm → spec → plan →
  TDD): `dc_bias.py`, `app.py`, template/CSS, automated tests 18 ตัว
  (เขียน test ก่อน ดู fail แล้วค่อยเขียนโค้ดให้ผ่านทุกครั้ง), README,
  AGENTS.md, validation record และแก้ตาม code review (เช่น ปิดช่องโหว่
  ค่า inf/NaN อย่าง `1e309` ที่เคยผ่าน validation)
- **ตัดสินใจและตรวจเอง** — อ่านและอนุมัติ spec + implementation plan ก่อน
 ให้ลงมือ, เลือกวิธี execute และวิธี commit เอง, เปิดเว็บจริงที่
  http://127.0.0.1:5000/ ทดลองกรอกค่าเอง (ชุด default, ค่าผิด R1=−5 /
  VCC=abc / VCC=1e309, ชุด cutoff, ชุด saturation), เทียบผลกับตาราง
  คำนวณมือใน `docs/validation.md` (ตรงกันครบ 9 ค่า), ตรวจ commit
  history และ publish repository ขึ้น GitHub ด้วย GitHub Desktop เอง

## ปัญหาที่เจอระหว่าง Lab และวิธีแก้

1. คำสั่ง `python` บนเครื่องถูก Microsoft Store alias ยึด (เรียกแล้วเด้งไป
   เปิด Store) → ใช้ `py` แทน และหลังสร้าง venv ใช้
   `.venv\Scripts\python.exe` ตรง ๆ — จดวิธีนี้ไว้ใน README และ AGENTS.md
2. Terminal ของ AI agent ตอนแรกยังไม่เห็นคำสั่ง Git (เพราะติดตั้ง Git
   ทีหลัง session เริ่ม) → ติดตั้ง Git แล้วเรียกผ่าน full path แทน
3. เคยเจอ test fail แบบเข้าใจผิด: รัน `py -m unittest ...` (Python ของ
   ระบบ) หลังมี dependency flask แล้ว → `ModuleNotFoundError: No module
   named 'flask'` เพราะ flask อยู่ใน `.venv` เท่านั้น → ต้องรันด้วย
   `.venv\Scripts\python.exe` เสมอ แล้วอัปเดตคำสั่งนี้ใน AGENTS.md ให้ถูก
4. จาก code review: ค่า `1e309` (Python parse เป็น inf) และ `nan` เคย
   ผ่าน validation ไปแสดงผลเป็น `inf/nan` โดยไม่มี warning → เพิ่ม
   `math.isfinite` check ที่ `_validate` พร้อม test ใหม่ 3 ตัว

## สิ่งที่อยากรู้ต่อ / ทำต่อใน Lab หน้า

- Lab 03 (bias แบบอื่น เช่น Fixed Bias, Emitter Bias): โครง `dc_bias.py`
  ปัจจุบันต่อยอดได้โดยเพิ่มฟังก์ชัน solve สำหรับแบบ bias ใหม่
- Lab 04 (SPICE): อยากรู้ว่าแบบจำลอง SPICE ต่างจาก forward-active
  approximation ที่ใช้ตรงไหน (เช่น VCE(sat) จริง, Early effect)
- งานเล็กที่เก็บไว้ทำต่อ: แสดงชื่อ region เป็นภาษาไทยบนหน้าเว็บ, ช่องที่
  ว่างหลัง error ไม่ควรถูกเติมค่า default กลับมา และ pin เวอร์ชัน flask
  (เช่น `flask~=3.1`) ถ้า lab หน้าต่อยอด repo เดิม
