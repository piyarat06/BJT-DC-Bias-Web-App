# Reflection — Lab 02

> ✍️ **ร่างคำตอบโดย AI จากเหตุการณ์จริงทั้งหมดในการทำ Lab นี้** —
> อ่านทำความเข้าใจ แล้ว**ปรับเป็นคำพูดของตนเอง**ก่อนส่ง
> (ทุกข้อเทียบกับโค้ดจริงใน repo แล้วเป็นจริงทั้งหมด)

ชื่อ-สกุล: ................................................. วันที่: 10 พฤศจิกายน 2569

## คำถามรายบุคคลจาก Lab §10

**1. เหตุใดการเปิด `templates/index.html` ตรง ๆ (ผ่าน file://) จึงไม่เท่ากับ
การรัน Flask?**

ตอนเปิดไฟล์ตรง ๆ ผ่าน file:// ผู้ที่ "แสดง" ไฟล์คือเบราว์เซอร์เอง โดยไม่มี
Flask อยู่ตรงกลาง ผลคือ (1) จะเห็นข้อความ `{{ defaults.vcc }}` ดิ ๆ บนหน้า
เพราะ `{{ ... }}` ไม่ใช่ภาษา HTML แต่เป็น template syntax ของ Jinja2 ซึ่ง
ต้องมีตัว render (คือ Flask) เติมค่าให้ก่อนส่งออกมาเป็น HTML จริง (2) กดปุ่ม
Calculate DC Bias ก็ไม่มีใครรับ เพราะฟอร์มส่ง POST ไปที่ route `/calculate`
ซึ่งจะมีอยู่ได้ก็ต่อเมื่อมี server รันอยู่เท่านั้น และ (3) ไม่มี Python ที่ไหน
คำนวณสมการ DC bias ให้เลย — สรุปคือไฟล์ HTML เป็นแค่ "หน้ากาก" ที่ต้องถูก
render และป้อนข้อมูลโดย web application เท่านั้น

**2. ฟอร์มส่งข้อมูลไป Python อย่างไร?**

ใน `templates/index.html` ฟอร์มประกาศไว้ว่า `<form method="post"
action="/calculate">` เมื่อกดปุ่ม submit เบราว์เซอร์จะสร้าง **HTTP POST
request** โดยเอาค่าจาก `<input>` ทั้ง 7 ช่อง (name = vcc, r1, r2, rc, re,
beta, vbe) บรรจุลง request body ในรูปแบบ form-encoded (เช่น
`vcc=12&r1=100&...`) ส่งไปที่ URL `/calculate` — ดูได้จริงใน DevTools →
Network ฝั่ง Flask มี `@app.route("/calculate", methods=["POST"])` ทำให้
ฟังก์ชัน `calculate()` ใน `app.py` รับ request นี้ โดยข้อมูลอยู่ใน
`request.form` (dict) → `parse_form()` แปลงเป็นตัวเลข ตรวจความถูกต้อง
และแปลงหน่วย kΩ→Ω → เรียก `solve()` ใน `dc_bias.py` คำนวณ → ส่งผลกลับ
ไป `render_template` เป็น HTML แล้วตอบ response กลับมาที่เบราว์เซอร์

**3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่? เพราะอะไร?**

ไม่ต้อง เพราะโปรเจกต์นี้แยก layer ไว้ชัด: `templates/index.html` มีหน้าที่
"แสดงผล" เท่านั้น — มันแสดงค่าจากตัวแปรที่ Python ส่งมา (เช่น
`result.vth`, `result.ic`) แต่ไม่มีสมการฟิสิกส์ใดทำงานอยู่ในไฟล์ HTML สมการ
DC bias ทั้งหมดอยู่ใน `dc_bias.py` จุดเดียว ถ้าแก้สูตร IC ใน `dc_bias.py`
ค่าที่แสดงบนหน้าเว็บจะเปลี่ยนตามทันทีโดยไม่ต้องแตะ HTML (ข้อยกเว้นเล็กน้อย:
footer ของหน้ามี "ข้อความ" สมการอ้างอิงไว้อ่านประกอบ ซึ่งเป็น display-only —
ถ้าสมการเปลี่ยนจริงก็ควรอัปเดตข้อความนั้นให้ตรง แต่นั่นคือแก้เอกสาร
อ้างอิง ไม่ใช่แก่ logic) — ประโยชน์ของการแยกแบบนี้คือ แก้ physics ที่เดียว,
test วิศวกรรม (`test_dc_bias.py`) รันได้โดยไม่ต้องเปิดเว็บ และแก้หน้าตา
โดยไม่มีความเสี่ยงพังสมการ

**4. ทำไมผลใน region ที่แบบจำลองใช้ไม่ได้ (cutoff/saturation) จึงต้องมี
Warning?**

แบบจำลอง Forward-Active ตั้งสมมติฐานไว้ว่าทรานซิสเตอร์นำกระแสใน active
region คือ IB เป็นตัวควบคุม IC ผ่านสูตร IC = β·IB และ VBE คงที่ สมมติฐาน
นี้พังเมื่อ (a) **cutoff**: VTH ≤ VBE ทำให้ junction ฐาน–อิมิตเตอร์ไม่ถูก
forward-bias จริง IB จึงเป็น 0 จริง ๆ ไม่ใช่ค่าจากสูตร IB =
(VTH−VBE)/(...) — โปรแกรมจึงตัดสินเป็น cutoff แสดง IB=IC=IE=0, VB=VTH,
VC=VCE=VCC และ (b) **saturation**: VCE < 0.2 V ทำให้ IC ถูกจำกัดด้วย
วงจรภายนอก (RC, RE, VCC) ไม่ใช่ด้วย IB อีกต่อไป — ค่าที่คำนวณตามสูตร
forward-active จึงเกินจริง ถ้าไม่มี warning ผู้ใช้จะเห็นตารางตัวเลขที่ดู
สมบูรณ์แบบแล้วเอาไปใช้ออกแบบ/เลือกค่า components ต่อโดยเข้าใจว่าถูก
ต้อง ซึ่งเป็นอันตรายในงานวิศวกรรมจริง — warning คือการบอกตรง ๆ ว่า
"ชุดค่านี้อยู่นอกขอบเขตที่แบบจำลองนี้ตั้งสมมติไว้ อย่าเชื่อตัวเลขตามตาราง"

## สิ่งที่ AI ช่วย / สิ่งที่ตรวจเอง

- **AI ช่วย** (ทำงานเป็นขั้นตอนตาม workflow: brainstorm → spec → plan →
  TDD): เขียน `dc_bias.py`, `app.py`, template/CSS, automated tests ทั้ง
  18 ตัว (เขียน test ก่อน ดูมัน fail แล้วค่อยเขียนโค้ดให้ผ่าน), README,
  AGENTS.md, validation record และแก้ปัญหาจาก code review (เช่น ปิดช่องโหว่
  ค่า inf/NaN อย่าง `1e309` ที่เคยผ่าน validation) — ทุก commit มีการรัน
  test ให้ผ่านก่อนเสมอ
- **ตรวจเอง**: อนุมัติ spec และแผนก่อนลงมือ, เทียบผลลัพธ์กับการคำนวณมือ
  (ตารางใน `docs/validation.md` — 9 ค่าตรงกันหมด), เปิดเว็บจริงที่
  http://127.0.0.1:5000/ ลองกรอกทั้งชุด default, ค่าผิด (R1=−5, VCC=abc,
  VCC=1e309), ชุด cutoff และชุด saturation, อ่าน diff/history ผ่าน GitHub
  Desktop และเป็นผู้ publish repository ขึ้น GitHub เอง

## ปัญหาที่เจอระหว่าง Lab และวิธีแก้

1. คำสั่ง `python` บนเครื่องนี้ถูก Microsoft Store alias ยึด (เรียกแล้วเด้ง
   ไปเปิด Store) → ใช้ `py` แทน และหลังสร้าง venv ใช้
   `.venv\Scripts\python.exe` ตรง ๆ — บันทึกวิธีนี้ไว้ใน README และ AGENTS.md
2. ตอนแรก terminal ของ AI agent ยังไม่เห็นคำสั่ง Git (ติดตั้ง Git ทีหลัง
   เริ่ม session) → ติดตั้ง Git ก่อน แล้วเรียกผ่าน full path
   `...\Git\cmd\git.exe` ใน session นั้น
3. false alarm เรื่อง test fail: รัน `py -m unittest ...` (Python ของระบบ)
   หลังมี dependency flask แล้ว → `ModuleNotFoundError: No module named
   'flask'` เพราะ flask ติดตั้งอยู่ใน `.venv` เท่านั้น → แก้โดยรัน test
   ด้วย `.venv\Scripts\python.exe` เสมอ และอัปเดตคำสั่งนี้ใน AGENTS.md
4. จาก code review: ค่า `1e309` (ที่ Python parse เป็น inf) และ `nan` เคย
   ผ่าน validation ไปแสดงผลเป็น `inf/nan` โดยไม่มี warning → เพิ่ม
   `math.isfinite` check ที่ `_validate` พร้อม test ใหม่ 3 ตัว

## สิ่งที่อยากรู้ต่อ / ทำต่อใน Lab หน้า

- Lab 03 (bias แบบอื่น เช่น Fixed Bias, Emitter Bias): โครง `dc_bias.py`
  ปัจจุบันต่อยอดได้โดยเพิ่มฟังก์ชัน solve สำหรับแบบ bias ใหม่ ๆ
- Lab 04 (SPICE): อยากรู้ว่าแบบจำลอง SPICE ต่างจาก forward-active
  approximation ที่ใช้ตรงไหน (เช่น ค่า VCE(sat) จริง, Early effect)
- งานเล็กที่เก็บไว้ทำต่อ: แสดงชื่อ region เป็นภาษาไทยบนหน้าเว็บ, ช่องที่
  ว่างหลัง error ไม่ควรถูกเติมค่า default กลับมา, และ pin เวอร์ชัน flask
  (เช่น `flask~=3.1`) ถ้า lab หน้าต่อยอด repo เดิม
