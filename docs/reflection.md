# Reflection — Lab 02

ชื่อ-สกุล: ................................................. วันที่: 10 พฤศจิกายน 2569

## คำถามรายบุคคลจาก Lab §10

**1. เหตุใดการเปิด `templates/index.html` ตรง ๆ (ผ่าน file://) จึงไม่เท่ากับการรัน Flask?**

เปิดตรง ๆ คือให้เบราว์เซอร์แสดงไฟล์เอง ไม่มี Flask ทำงาน — จะเห็น `{{ defaults.vcc }}` ดิ ๆ เพราะเป็น template syntax ของ Jinja2 ที่ต้องรอ Flask render เติมค่าให้ก่อน และกดปุ่ม Calculate ก็ไม่มีใครรับ เพราะ route `/calculate` มีอยู่เฉพาะตอน server รันอยู่

**2. ฟอร์มส่งข้อมูลไป Python อย่างไร?**

กด submit แล้วเบราว์เซอร์ส่ง HTTP POST ไปที่ `/calculate` โดยแนบค่าจาก input ทั้ง 7 ช่อง ไว้ใน request body (ดูได้ใน DevTools → Network) — Flask รับที่ฟังก์ชัน `calculate()` ใน `app.py` ผ่าน `request.form` แปลงเป็นตัวเลข แปลง kΩ→Ω แล้วเรียก `solve()` ใน `dc_bias.py` ก่อนส่งผลกลับมาเป็น HTML

**3. แก้สมการใน `dc_bias.py` แล้วต้องแก้ HTML หรือไม่? เพราะอะไร?**

ไม่ต้อง เพราะสมการทั้งหมดอยู่ใน `dc_bias.py` จุดเดียว ส่วน HTML ทำหน้าที่แสดงค่าที่ Python ส่งมาเท่านั้น — แก้สูตรที่ `dc_bias.py` แล้วผลบนเว็บเปลี่ยนตามทันที

**4. ทำไมผลใน region ที่แบบจำลองใช้ไม่ได้ (cutoff/saturation) จึงต้องมี Warning?**

แบบจำลอง Forward-Active ตั้งสมมติไว้ว่า IC = β·IB และ VBE คงที่ ซึ่งใช้ไม่ได้เมื่อ cutoff (VTH ≤ VBE → IB = 0 จริง) หรือ saturation (VCE < 0.2 V → IC ถูกจำกัดโดยวงจรภายนอก ไม่ใช่ β) — ถ้าไม่มี warning ผู้ใช้จะเชื่อตัวเลขที่เกินจริงแล้วเอาไปออกแบบวงจรต่อ ซึ่งอันตราย

## สิ่งที่ AI ช่วย / สิ่งที่ตรวจเอง

- **AI ช่วย**: เขียนโค้ดทั้งโปรเจกต์ตาม workflow (spec → plan → TDD) รวมถึง tests 40 ตัว, README และเอกสาร โดยเขียน test ก่อนเสมอ และแก้ตาม code review (เช่น ปิดช่องโหว่ค่า `1e309`/NaN)
- **ตรวจเอง**: อนุมัติ spec/plan ก่อนลงมือ, เปิดเว็บทดลองกรอกค่าเอง (default, ค่าผิด, ชุด cutoff/saturation), เทียบผลกับคำนวณมือ (ตรงครบ 9 ค่า) และ publish repo ขึ้น GitHub เอง

## ปัญหาที่เจอระหว่าง Lab และวิธีแก้

1. `python` ถูก Microsoft Store alias ยึด → ใช้ `py` และ `.venv\Scripts\python.exe` แทน
2. รัน test ด้วย `py` หลังมี flask แล้ว error `No module named 'flask'` → ต้องรันด้วย Python ใน venv เท่านั้น (แก้คำสั่งใน AGENTS.md)
3. code review พบว่า `1e309` (inf) ผ่าน validation → เพิ่ม `math.isfinite` พร้อม test ใหม่

## สิ่งที่อยากรู้ต่อ / ทำต่อใน Lab หน้า

- ได้เพิ่ม Fixed/Emitter Bias ลงใน `dc_bias.py` และรวมเป็นหน้าเดียว 3 ส่วนพับได้แล้ว (17 พ.ย. 2569)
- Lab 04 อยากเทียบผล forward-active approximation กับ SPICE จริง
