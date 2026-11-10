# AGENTS.md — ข้อตกลงสำหรับ AI Coding Agent

โปรเจกต์: BJT DC Bias Web App (ENG29 2121 · Lab 02)

## หน้าที่ของแต่ละไฟล์

- `dc_bias.py` — **engineering logic ล้วน**: stdlib เท่านั้น, หน่วย SI
  (V, Ω, A) เข้า/ออก, ห้าม import flask/jinja, ห้ามรู้จัก HTTP/HTML
- `app.py` — **web layer**: parse ฟอร์ม, แปลงหน่วย kΩ→Ω, เรียก solve,
  จัดการ error/warning ที่แสดงต่อผู้ใช้
- `templates/index.html` — การแสดงผลเท่านั้น **ห้ามฝังสมการฟิสิกส์**
  (แก้สมการใน `dc_bias.py` ต้องไม่ต้องแก้ HTML)
- `static/style.css` — ความสวยงาม/การจัดหน้า
- `tests/` — `test_dc_bias.py` (วิศวกรรม) และ `test_web.py` (HTTP)

## กฎการทำงาน

1. **TDD**: เขียน failing test ก่อน ดูมัน fail แล้วค่อย implement
   (Red → Green → Refactor)
2. ก่อน commit ทุกครั้ง ต้องรัน
   `.venv\Scripts\python.exe -m unittest discover -s tests -v`
   (จาก repo root — flask ติดตั้งอยู่ใน `.venv` เท่านั้น คำสั่ง `py` ของระบบ
   จึง import flask ไม่ได้) และผ่าน 100%
3. ภาษาของ UI และข้อความ error/warning คือ **ภาษาไทย** (ศัพท์เทคนิค
   อังกฤษ เช่น VCC, Calculate DC Bias)
4. ห้าม commit `.venv/`, `__pycache__/`, `.env`, API keys หรือ credentials
5. Scope ของ Lab 02 คือ **DC Bias เท่านั้น** — ไม่เพิ่ม AC, transient,
   bias แบบอื่น หรือ SPICE solver (มาใน Lab ถัดไป)
6. เมื่อเพิ่ม/แก้พฤติกรรม → ต้องมี test ครอบพฤติกรรมนั้นเสมอ
