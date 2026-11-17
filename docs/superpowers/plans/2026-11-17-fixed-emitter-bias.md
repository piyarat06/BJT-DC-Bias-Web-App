# Fixed + Emitter Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่มหน้า `/fixed` และ `/emitter` ที่คำนวณ DC Operating Point จริง ด้วย solver ใหม่ใน `dc_bias.py` โดยไม่เปลี่ยนพฤติกรรมของหน้า `/` เดิม

**Architecture:** ใช้โครงสร้าง server-rendered เดิม (Flask + Jinja2 ไม่มี JS) แยก engineering ไว้ใน `dc_bias.py`: `solve()` เดิมยังอยู่และเรียก helper ร่วมกับ `solve_fixed()` / `solve_emitter()` ใหม่ ส่วน web layer มี route ต่อหน้าใหม่และใช้ template partial ร่วมกันสำหรับแถบลิงก์และตารางผล

**Tech Stack:** Python 3, Flask ≥3.0, unittest, venv `.venv`

**Spec:** `docs/superpowers/specs/2026-11-17-fixed-emitter-bias-design.md`

## Global Constraints

- หน่วยฟอร์ม: V, kΩ (web layer คูณ 1000 ก่อนส่งเข้า solver), β ไม่มีหน่วย — solver รับ/คืน SI (V, Ω, A)
- ผลลัพธ์ต้องมี VTH, RTH, IB, IC, IE, VE, VB, VC, VCE พร้อมหน่วย; region/cutoff/saturation เหมือนเดิม
- ข้อความ error/warning เป็นภาษาไทย + ศัพท์เทคนิคอังกฤษ; ห้ามเปลี่ยนข้อความของ `/` เดิม
- สั่งรัน tests จาก repo root ด้วย `.venv\Scripts\python.exe -m unittest discover -s tests -v` เท่านั้น
- Git ในเครื่องนี้ต้องใช้พาธเต็ม `C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe`
- Commit เฉพาะ local (origin มีอยู่แล้ว แต่ผู้ใช้เป็นคน push ผ่าน GitHub Desktop)
- ห้าม commit `.venv/`, `__pycache__/`, secrets

## Review Focus

- **`/` เดิมต้องไม่เปลี่ยนผลหรือข้อความ** (refactor helper อาจทำให้ค่าคลาด) → Task 1 Step 5 รันชุดเดิม 18 tests เทียบผ่านทั้งหมด
- **RB ในฟอร์มเป็น kΩ** ถ้าไม่แปลงเป็น Ω ทุกกระแสจะผิด 1000× → Task 2 Step 4 ทดสอบ POST ด้วย `rb=470` แล้วได้ IC 2.404 mA
- **"Emitter Bias" หมายถึง RB จาก VCC + RE (emitter-feedback)** ไม่ใช่ voltage-divider ที่มี RE → Task 1 Step 1 ยึดค่าอ้างอิง IB = 19.790 µA
- **cutoff ต้องไม่โชว์ IB ติดลบ และต้องมี warning** ในสองวงจรใหม่ → Task 1 Step 1 ทดสอบ cutoff, Task 2 Step 4 ทดสอบ warning บนหน้าเว็บ
- **inf/NaN/ช่อง RB ว่างต้องเป็น error ไม่ใช่ `nan` mA** → Task 1 Step 1 ทดสอบ non-finite, Task 2 Step 4 ทดสอบ POST `rb=""` และ `vcc="1e309"`

---

### Task 1: Engineering solver สำหรับ Fixed และ Emitter Bias

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `DCBiasResult`, `SATURATION_THRESHOLD_V` จาก `dc_bias.py`, พฤติกรรมเดิมของ `solve(vcc, r1, r2, rc, re, beta, vbe)`
- Produces:
  - `solve_fixed(vcc: float, rb: float, rc: float, beta: float, vbe: float) -> DCBiasResult` (SI; ภายในใช้ `re = 0.0`)
  - `solve_emitter(vcc: float, rb: float, rc: float, re: float, beta: float, vbe: float) -> DCBiasResult` (SI)
  - ทั้งคู่ตั้ง `vth = vcc`, `rth = rb`, ใช้ helper ร่วมกับ `solve()` สำหรับคำนวณ IB/IC/IE/VE/VB/VC/VCE + region

- [ ] **Step 1: Write the failing tests in `tests/test_dc_bias.py`** — import `solve_fixed, solve_emitter` เพิ่ม และเพิ่ม class `TestFixedEmitter` ที่มี tests เหล่านี้ (ใช้ `assertAlmostEqual` พร้อม delta ตามที่ระบุ):
  - `test_fixed_reference_values`: `solve_fixed(12.0, 470e3, 2.2e3, 100.0, 0.70)` → `vth=12.0`, `rth=470000.0`, `ib=24.042553e-6` (delta 1e-11), `ic=2.404255e-3` (delta 1e-8), `ie=2.428298e-3` (delta 1e-8), `ve=0.0`, `vb=0.70`, `vc=6.710638` (delta 1e-5), `vce=6.710638`, `region="forward_active"`, `warnings=[]`
  - `test_emitter_reference_values`: `solve_emitter(12.0, 470e3, 2.2e3, 1e3, 100.0, 0.70)` → `rth=470000.0`, `ib=19.789842e-6`, `ic=1.978984e-3`, `ie=1.998774e-3`, `ve=1.998774`, `vb=2.698774`, `vc=7.646235`, `vce=5.647461` (delta เดียวกัน), region forward_active
  - `test_fixed_cutoff`: `solve_fixed(0.5, 470e3, 2.2e3, 100.0, 0.70)` → region `"cutoff"`, `ib=ic=ie=0.0`, `vb=0.5`, `vc=0.5`, `vce=0.5`, มี `"Cutoff"` ใน warnings
  - `test_emitter_cutoff`: `solve_emitter(0.5, 470e3, 2.2e3, 1e3, 100.0, 0.70)` → เดียวกัน
  - `test_fixed_saturation`: `solve_fixed(12.0, 10e3, 2.2e3, 100.0, 0.70)` → region `"saturation"`, `vce < 0.2`, มี `"Saturation"` ใน warnings
  - `test_emitter_saturation`: `solve_emitter(12.0, 10e3, 2.2e3, 1e3, 100.0, 0.70)` → เดียวกัน
  - `test_invalid_resistances_name_fields`: กรณี `rb=0`, `rb=-1`, `rc=0`, `beta=0`, `vbe=-0.1`, `vcc=0` ของ `solve_fixed` และ `re=0`, `re=-1` ของ `solve_emitter` → `ValueError` และข้อความมีชื่อฟิลด์ (`RB`/`RC`/`RE`/`β`/`VBE`/`VCC`)
  - `test_non_finite_inputs_rejected`: `float("inf")` และ `float("nan")` ใน `rb` ของ fixed และใน `re` ของ emitter → `ValueError` ที่มีคำว่า `"จำนวนจำกัด"`

- [ ] **Step 2: Run the test file to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_dc_bias.py" -v`
Expected: FAIL — `ImportError: cannot import name 'solve_fixed' from 'dc_bias'`

- [ ] **Step 3: Implement in `dc_bias.py`**

เพิ่ม `_require_finite(name, value)` (ย้าย logic ตรวจ `math.isfinite` จาก `_validate` มาเรียกใช้ ไม่เปลี่ยนข้อความเดิม) และ helper `_operating_point(vcc, vth, rth, rc, re, beta, vbe) -> DCBiasResult` ที่มีโค้ดคำนวณ IB/IC/IE/VE/VB/VC/VCE และ region เดิมทุกประการ (รวมข้อความ warning เดิม). ให้ `solve()` เรียก helper นี้ด้วย `vth, rth` เดิม. เพิ่ม `solve_fixed(...)` (ตรวจ finite/positive ของ VCC/RB/RC/β และ VBE ≥ 0 แล้วเรียก helper ด้วย `re=0.0`) และ `solve_emitter(...)` (ตรวจเพิ่ม RE > 0 แล้วเรียก helper). ห้ามแก้ค่าหรือข้อความที่ `solve()` เดิมคืน

- [ ] **Step 4: Run the test file to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_dc_bias.py" -v`
Expected: PASS (ทุก test ในไฟล์ รวมชุดเดิม)

- [ ] **Step 5: Run the whole existing suite to catch regressions**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS — 18 tests เดิมยังผ่านหมด (ความล้มเหลวใด ๆ แปลว่า refactor เปลี่ยนพฤติกรรมเดิม ต้องแก้ก่อนไปต่อ)

- [ ] **Step 6: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add dc_bias.py tests/test_dc_bias.py
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: add fixed and emitter bias solvers with tests"
```

### Task 2: Routes, templates และ UI สำหรับ 3 วงจร

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`, `tests/test_web.py`
- Create: `templates/_nav.html`, `templates/_results.html`, `templates/fixed.html`, `templates/emitter.html`

**Interfaces:**
- Consumes: `solve`, `solve_fixed`, `solve_emitter` จาก Task 1; `DEFAULTS`, `FORM_FIELDS`, `LABELS`, `parse_form` เดิมใน `app.py`
- Produces:
  - `FIXED_DEFAULTS = {"vcc": 12.0, "rb": 470.0, "rc": 2.2, "beta": 100.0, "vbe": 0.70}`
  - `EMITTER_DEFAULTS` = ค่าเดียวกัน + `"re": 1.0`
  - `FORM_FIELDS_FIXED = ("vcc", "rb", "rc", "beta", "vbe")`, `FORM_FIELDS_EMITTER = ("vcc", "rb", "rc", "re", "beta", "vbe")`
  - `parse_form(form, fields)` (เพิ่มพารามิเตอร์ `fields`; `/calculate` เรียกด้วย `FORM_FIELDS`)
  - GET `/fixed`, POST `/calculate-fixed`, GET `/emitter`, POST `/calculate-emitter`
  - `_nav.html` (ลิงก์ `/`, `/fixed`, `/emitter`), `_results.html` (ตารางผล 9 ค่า + region + warnings)

- [ ] **Step 1: Write the failing tests in `tests/test_web.py`**

เพิ่ม `FIXED_FORM = {"vcc": "12", "rb": "470", "rc": "2.2", "beta": "100", "vbe": "0.7"}` และ `EMITTER_FORM = {**FIXED_FORM, "re": "1"}` แล้วเพิ่ม tests:
  - `test_get_fixed_returns_form`: GET `/fixed` → 200, มี `name="vcc"`, `name="rb"`, `name="rc"`, `name="beta"`, `name="vbe"`, ไม่มี `name="r1"`/`name="r2"`, มี `"Calculate DC Bias"`
  - `test_get_emitter_returns_form`: GET `/emitter` → 200, มี `name="re"` เพิ่มจาก fixed
  - `test_post_fixed_calculates_real_value`: POST `/calculate-fixed` ด้วย `FIXED_FORM` → 200, มี `"2.404"` และ `"mA"` และ `"forward_active"`
  - `test_post_emitter_calculates_real_value`: POST `/calculate-emitter` ด้วย `EMITTER_FORM` → 200, มี `"1.979"` และ `"5.647"`
  - `test_nav_links_on_all_pages`: GET `/`, `/fixed`, `/emitter` → แต่ละหน้ามี `href="/"`, `href="/fixed"`, `href="/emitter"`
  - `test_post_fixed_invalid_rb`: `rb="-5"` → มี `"RB ต้องมากกว่า 0"`
  - `test_post_blank_rb_shows_error`: `rb=""` → มี `"RB ต้องเป็นตัวเลข"`
  - `test_post_emitter_non_finite_vcc`: `vcc="1e309"` → มี `"VCC"` และ `"จำนวนจำกัด"`
  - `test_post_fixed_cutoff_warning`: `vcc="0.5"` → มี `"Cutoff"`
  - `test_post_emitter_saturation_warning`: `rb="10"` → มี `"Saturation"`

- [ ] **Step 2: Run the test file to verify it fails**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: FAIL — `/fixed` คืน 404

- [ ] **Step 3: Add routes and defaults in `app.py`**

เพิ่ม LABELS ด้วย `"rb": "RB"`, เปลี่ยน `parse_form(form)` เป็น `parse_form(form, fields)` และอัปเดต `/calculate` เรียก `parse_form(request.form, FORM_FIELDS)` (พฤติกรรม/ข้อความเดิมเหมือนเดิม). เพิ่ม defaults/field tuples ตาม Interfaces และ route 4 ตัว: GET `/fixed` → render `fixed.html` ด้วย defaults; POST `/calculate-fixed` → เก็บ `entered`, แปลง kΩ→Ω (`rb`, `rc`, และ `re` ถ้ามี), เรียก `solve_fixed`, จับ `ValueError` → render พร้อม `error`; GET `/emitter` และ POST `/calculate-emitter` ทำแบบเดียวกับ `solve_emitter`

- [ ] **Step 4: Add templates and nav styling**

สร้าง `_results.html` แสดง warnings + region + ตาราง 9 ค่าจาก `result` (คัดลอกโครงสร้างจาก `index.html` และลบโค้ดซ้ำออกจาก `index.html`), สร้าง `_nav.html` เป็นลิงก์ 3 หน้าพร้อม class active ตาม circuit ที่ส่งเข้า, สร้าง `fixed.html` และ `emitter.html` ที่ include nav/results พร้อมฟอร์มชื่อฟิลด์และ action ตาม Interfaces และ footer สมการของวงจรนั้น. แก้ `index.html` ให้ include nav/results ด้วย (ห้ามเปลี่ยนข้อความ subtitle/footer เดิม). เพิ่ม CSS `.nav` ให้ลิงก์อยู่แถวเดียวกัน อ่านง่ายบนจอแคบ

- [ ] **Step 5: Run the test file to verify it passes**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: PASS (รวม 9 tests เดิมของ `/`)

- [ ] **Step 6: Run the whole suite**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS ทุก test (จำนวนรวมใหม่จะเป็นตัวเลขที่ใช้ใน Task 3)

- [ ] **Step 7: HTTP smoke test against the running debug server**

Run: PowerShell `Invoke-WebRequest` GET `/`, `/fixed`, `/emitter` → ทุกอัน status 200; POST `/calculate-fixed` ด้วย `FIXED_FORM` → 200 และ text มี `2.404`
Expected: ตรงตามที่ระบุ (debug server รีโหลดโค้ดเองอยู่แล้ว)

- [ ] **Step 8: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add app.py templates static/style.css tests/test_web.py
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: add fixed and emitter bias web pages"
```

### Task 3: อัปเดตเอกสารให้ตรง scope ใหม่

**Files:**
- Modify: `README.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: จำนวน tests จริงจาก Task 2 Step 6, ค่าอ้างอิงใน spec, route ใหม่ทั้ง 4 ตัว

- [ ] **Step 1: Update `README.md`**

เขียนintro ใหม่ให้ครบ 3 วงจร, เพิ่ม route ใหม่และค่า default ของ fixed (RB=470 kΩ) / emitter (RB=470 kΩ, RE=1 kΩ) ในหมวดการรัน, อัปเดตโครงสร้างไฟล์ (templates ใหม่), แทนที่จำนวน `18 tests` ด้วยจำนวนจริงจาก Task 2 Step 6, เพิ่มแถว A6/A7 หรือแถวใหม่สำหรับolver/route ใหม่ พร้อมชื่อ test ที่เพิ่ม

- [ ] **Step 2: Update `docs/design-note.md`**

ลบ "ไม่มี bias types อื่น (Fixed Bias, Emitter Bias = Lab W3)" ออกจาก Non-goals และเพิ่มหัวข้อ "ส่วนต่อขยาย 17 พ.ย. 2569" ที่สรุป 3 route ใหม่, สมการ VTH=VCC/RTH=RB, ค่า default, และลิงก์ไป spec ใหม่ (ห้ามลบเนื้อหา Lab 02 เดิม)

- [ ] **Step 3: Update `docs/validation.md`**

เพิ่มหัวข้อ 6 "Fixed/Emitter Bias" พร้อมตารางค่าคำนวณมือจาก spec (fixed IC=2.404 mA / VCE=6.711 V, emitter IC=1.979 mA / VCE=5.647 V), จำนวน tests ใหม่จาก Task 2 Step 6 และกรณี browser ใหม่ (RB ติดลบ, RB ว่าง, vcc=1e309, cutoff, saturation) — เก็บหัวข้อ 1–5 เดิมไว้

- [ ] **Step 4: Update `docs/reflection.md` แบบสั้น**

เปลี่ยน "tests 18 ตัว" เป็นจำนวนจริง, แก้บรรทัด "Lab 03 (bias แบบอื่น) ต่อยอดได้" เป็นข้อความสั้นว่าได้เพิ่ม Fixed/Emitter Bias แล้วใน repo นี้ (อย่าแก้ชื่อ-สกุลที่ยังเป็น placeholder)

- [ ] **Step 5: Verify docs against tests and HTTP**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS และตัวเลขที่เขียนใน README/validation/reflection ตรงกับผลที่รันได้

- [ ] **Step 6: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add README.md docs
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "docs: cover fixed and emitter bias expansion"
```
