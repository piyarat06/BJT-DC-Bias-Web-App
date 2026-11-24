# AGENTS.md — ข้อตกลงสำหรับ AI Coding Agent

โปรเจกต์: BJT Bias + CE Amplifier Simulator (ENG29 2121 · Lab 02 → Lab 04)

## หน้าที่ของแต่ละไฟล์

- `dc_bias.py` — **engineering logic ของ Lab 03**: stdlib เท่านั้น, หน่วย SI
  (V, Ω, A) เข้า/ออก, ห้าม import flask/jinja, ห้ามรู้จัก HTTP/HTML
- `spice_engine.py` — **adapter ของ Lab 04**: ตรวจ input, สร้าง netlist, เรียก
  ngspice ด้วย `subprocess.run([...], shell=False, timeout=...)`, อ่าน raw/log,
  แปลงเป็นผลพร้อมหน่วยและ chart spec — stdlib ล้วน, ห้าม import flask/jinja
- `app.py` — **web layer**: parse ฟอร์ม, แปลง kΩ→Ω สำหรับ `dc_bias.py`, dispatch
  `/simulate` ไป `spice_engine.py`, จัดการ error/status ที่แสดงต่อผู้ใช้
- `templates/index.html` — การแสดงผลเท่านั้น **ห้ามฝังสมการฟิสิกส์**
  (แก้สมการใน `dc_bias.py`/`spice_engine.py` ต้องไม่ต้องแก้ HTML)
- `static/app.js` — วาด SVG จาก JSON ที่ server ส่งมาเท่านั้น **ห้ามคำนวณฟิสิกส์
  หรือสร้างข้อมูลกราฟขึ้นเอง**, ห้ามใช้ mock/fallback เมื่อไม่มีข้อมูลจริง
- `static/style.css` — ความสวยงาม/การจัดหน้า
- `tests/` — `test_dc_bias.py`, `test_web.py` (Lab 03), `test_spice_engine.py`,
  `test_simulator_web.py` (Lab 04)

## กฎการทำงาน

1. **TDD**: เขียน failing test ก่อน ดูมัน fail แล้วค่อย implement (Red → Green → Refactor)
2. ก่อน commit ทุกครั้ง ต้องรัน
   `.venv\Scripts\python.exe -m unittest discover -s tests -v`
   (จาก repo root — flask ติดตั้งอยู่ใน `.venv` เท่านั้น) และผ่าน 100%
   (test ที่ใช้ ngspice จริงจะ skip เองถ้าไม่มี engine)
3. ภาษาของ UI และข้อความ error/warning คือ **ภาษาไทย** (ศัพท์เทคนิคเช่น
   VCC, Calculate DC Bias, Run Simulation ใช้อังกฤษได้)
4. ห้าม commit `.venv/`, `__pycache__/`, `.env`, `tools/ngspice/`, ไฟล์ 7z,
   credentials หรือไฟล์ run ชั่วคราว
5. **ต้องคงเส้นทาง DC Bias 3 แบบของ Lab 03 ไว้ครบ** — ห้ามลบ/เขียนทับสมการ
   หรือ tests เดิมเพื่อเพิ่ม simulator
6. ผลจาก ngspice กับผล Analytical **ต้องแยกป้ายที่มาให้ชัด** ห้ามนำตัวเลข
   จากโค้ด/ค่าอ้างอิงมาแสดงว่าเป็นผลรันจริง และห้ามแสดงกราฟเก่าเมื่อ run ล้มเหลว
7. ทุกการเพิ่ม/แก้พฤติกรรมต้องมี test ครอบพฤติกรรมนั้นเสมอ รวมกรณี
   validation, engine ไม่พบ, run fail, timeout, output ว่าง
8. Scope ปัจจุบันคือ **Lab 04 v1**: `.op/.ac/.tran` เฉพาะวงจร CE Voltage Divider
   อ้างอิง — ยังไม่ทำ FET, circuit editor, emitter bypass หรือ AC ทุก bias mode
9. โมเดล BJT ที่ใช้คือ `.MODEL QNPN NPN(IS=1e-14 BF=100 VAF=100 CJE=25p CJC=8p TF=0.4n)`
   (ไม่มี Starter Kit จากอาจารย์) ต้องระบุใน netlist/README ทุกครั้งที่เปลี่ยน
