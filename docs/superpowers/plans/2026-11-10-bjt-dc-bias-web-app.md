# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** สร้าง Flask multi-file web app คำนวณ DC bias ของวงจร NPN Common-Emitter Voltage-Divider Bias พร้อม validation, region warnings และ automated tests จบในคาบเดียว

**Architecture:** Server-rendered Flask (ไม่มี JavaScript). `dc_bias.py` เป็น engineering module ล้วน (stdlib เท่านั้น, หน่วย SI, ไม่รู้จัก HTTP/HTML) — `app.py` parse ฟอร์ม + แปลงหน่วย kΩ→Ω แล้วเรียก solve — `templates/index.html` + `static/style.css` ดูแลการแสดงผล

**Tech Stack:** Python 3.14 (เรียกผ่าน `py`), Flask ≥3.0 (dependency เดียว), unittest (stdlib)

**Spec:** `docs/design-note.md` (อนุมัติแล้ว) — plan นี้อ้างจาก spec เสมอ

## Global Constraints

- ทุกคำสั่งรันบนเครื่องนี้ใช้ **`py`** แทน `python` (คำสั่ง `python` ถูก Store alias ยึด)
- รัน tests ด้วย `py -m unittest discover -s tests -v` จาก **repo root** เท่านั้น (จำกัด: ห้าม pytest)
- `dc_bias.py` ใช้ stdlib เท่านั้น ห้าม import flask/jinja — รับ/คืนหน่วย SI (V, Ω, A)
- Flask เป็น third-party dependency เดียว (`requirements.txt` มีบรรทัดเดียว)
- User-facing copy เป็นภาษาไทย (ศัพท์เทคนิคอังกฤษ) — ข้อความ exact ปักไว้ในแต่ละ task แล้ว
- Commit ทำผ่าน **GitHub Desktop** โดยนักศึกษา (หรือตามวิธีที่เลือกตอน review plan) — ข้อความ commit ใช้รูปแบบ `feat:`/`test:`/`docs:`
- ห้าม commit `.venv/`, `__pycache__/`, `.env`
- ก่อน commit ทุกครั้ง: tests ผ่าน 100% ก่อนเท่านั้น
- Repo root: `C:\Users\b6821982\Documents\GitHub\BJT DC Bias Web App\`

## Review Focus

อินพุต 5 กลุ่มที่ spec ไม่ได้ระบุชัดแต่ผู้ใช้จริงมักเจอ — แต่ละบรรทัดมี test ปักอยู่ใน task เจ้าของโค้ดแล้ว:

1. ช่องฟอร์มว่างเปล่า → error ชัด หน้าไม่ล้ม — Task 4 `test_post_empty_field`
2. กรอกข้อความ ("abc") → error ชัด หน้าไม่ล้ม — Task 4 `test_post_non_numeric_value`
3. ตัวเลขมีช่องว่างล้อม (" 12 ") → ยอมรับ คำนวณได้ปกติ — Task 4 `test_post_whitespace_number`
4. `VTH == VBE` พอดี (ขอบเขต cutoff) → ถือว่า cutoff — Task 3 `test_cutoff_boundary_vth_equals_vbe`
5. ตัวต้านทานค่าสุดขั้ว (1 GΩ) → ไม่ crash ผลลัพธ์เป็นเลข finite — Task 1 `test_extreme_resistors_no_crash`

---

### Task 1: DC Bias Solver — ค่าอ้างอิงและโครงสร้างผลลัพธ์

**Files:**
- Create: `dc_bias.py`
- Create: `tests/test_dc_bias.py`
- Create: `.gitignore` (fold setup ของทั้ง repo มาที่นี่)

**Interfaces:**
- Consumes: ไม่มี (module แรก)
- Produces: `DCBiasResult` (dataclass) ฟิลด์ `vth, rth, ib, ic, ie, ve, vb, vc, vce: float` + `region: str` + `warnings: list[str]` และ `solve(vcc, r1, r2, rc, re, beta, vbe) -> DCBiasResult` — หน่วย SI ทั้งเข้าและออก. Task 3 เติม branch cutoff/saturation ใน solve เดิม; Task 4 เรียก solve จาก app.py

- [ ] **Step 1: เขียน failing tests** — `tests/test_dc_bias.py`:

```python
import unittest
from dc_bias import solve

class TestSolveReferenceValues(unittest.TestCase):
    """ค่าอ้างอิงคำนวณมืออย่างอิสระ (Lab §06): VCC=12V R1=100k R2=22k
    RC=2.2k RE=1k beta=100 VBE=0.70V หน่วย SI ทั้งหมด"""

    def test_solve_reference_values(self):
        r = solve(12.0, 100_000.0, 22_000.0, 2_200.0, 1_000.0, 100.0, 0.70)
        self.assertAlmostEqual(r.vth, 2.163934, delta=1e-4)
        self.assertAlmostEqual(r.rth, 18032.787, delta=0.05)
        self.assertAlmostEqual(r.ib, 1.22986e-5, delta=2e-9)
        self.assertAlmostEqual(r.ic, 1.22986e-3, delta=2e-7)
        self.assertAlmostEqual(r.ie, 1.24216e-3, delta=2e-7)
        self.assertAlmostEqual(r.ve, 1.242161, delta=1e-4)
        self.assertAlmostEqual(r.vb, 1.942161, delta=1e-4)
        self.assertAlmostEqual(r.vc, 9.294304, delta=1e-4)
        self.assertAlmostEqual(r.vce, 8.052144, delta=1e-4)
        self.assertEqual(r.region, "forward_active")
        self.assertEqual(r.warnings, [])

    def test_extreme_resistors_no_crash(self):
        r = solve(12.0, 1e9, 1e9, 1e6, 1e6, 100.0, 0.7)
        for name in ("vth", "rth", "ib", "ic", "ie", "ve", "vb", "vc", "vce"):
            self.assertTrue(getattr(r, name) == getattr(r, name), f"{name} ไม่ใช่ finite number")
```

- [ ] **Step 2: รันเพื่อยืนยันว่า fail** — `py -m unittest discover -s tests -v` จาก repo root
Expected: FAIL/ERROR `ModuleNotFoundError: No module named 'dc_bias'`

- [ ] **Step 3: Implement `dc_bias.py`** — โครงสร้าง:

```python
from dataclasses import dataclass, field

@dataclass
class DCBiasResult:
    vth: float; rth: float; ib: float; ic: float; ie: float
    ve: float; vb: float; vc: float; vce: float
    region: str          # "forward_active" | "cutoff" | "saturation"
    warnings: list = field(default_factory=list)

def solve(vcc, r1, r2, rc, re, beta, vbe) -> DCBiasResult:
    # VTH = vcc*r2/(r1+r2); RTH = r1*r2/(r1+r2)
    # IB = (VTH-VBE)/(RTH+(beta+1)*re); IC=beta*IB; IE=(beta+1)*IB
    # VE=IE*re; VB=VE+vbe; VC=vcc-IC*rc; VCE=VC-VE
    # ใน task นี้: region="forward_active", warnings=[] เสมอ (branch ตัดสินอยู่ Task 3)
    # validation อยู่ Task 2
```

สูตรวิศวกรรมตาม spec เป๊ะ ๆ — ตัวเลขทดสอบตรวจความถูกต้องให้

- [ ] **Step 4: รัน tests ให้ผ่าน** — `py -m unittest discover -s tests -v` → Expected: 2 tests PASS
- [ ] **Step 5: Commit** — ข้อความ: `feat: dc_bias solver with reference-value tests`
  ไฟล์: `dc_bias.py`, `tests/test_dc_bias.py`, `.gitignore` (บรรทัด: `.venv/`, `__pycache__/`, `*.pyc`, `.env`)

### Task 2: Input Validation — ค่าหลักการต้องถูกก่อนคำนวณ

**Files:**
- Modify: `dc_bias.py` (ต้น `solve`)
- Test: `tests/test_dc_bias.py` (เพิ่ม class)

**Interfaces:**
- Consumes: `solve()` จาก Task 1
- Produces: `solve()` raises `ValueError` ข้อความไทย เมื่อ `vcc<=0`, ตัวต้านทานใด ๆ `<=0`, `beta<=0`, `vbe<0` — Task 4 จะ catch `ValueError` ตัวนี้แสดงบนหน้าเว็บ

- [ ] **Step 1: เขียน failing tests** — เพิ่มใน `tests/test_dc_bias.py`:

```python
class TestValidation(unittest.TestCase):
    def test_invalid_inputs_raise_value_error(self):
        cases = [
            ((0.0, 100e3, 22e3, 2.2e3, 1e3, 100.0, 0.7), "VCC"),
            ((12.0, 0.0, 22e3, 2.2e3, 1e3, 100.0, 0.7), "R1"),
            ((12.0, 100e3, -5.0, 2.2e3, 1e3, 100.0, 0.7), "R2"),
            ((12.0, 100e3, 22e3, 0.0, 1e3, 100.0, 0.7), "RC"),
            ((12.0, 100e3, 22e3, 2.2e3, -1.0, 100.0, 0.7), "RE"),
            ((12.0, 100e3, 22e3, 2.2e3, 1e3, 0.0, 0.7), "β"),
            ((12.0, 100e3, 22e3, 2.2e3, 1e3, 100.0, -0.1), "VBE"),
        ]
        for args, name in cases:
            with self.subTest(field=name):
                with self.assertRaises(ValueError):
                    solve(*args)

    def test_error_message_names_the_field(self):
        with self.assertRaises(ValueError) as ctx:
            solve(12.0, 0.0, 22e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertIn("R1", str(ctx.exception))
```

- [ ] **Step 2: รันให้ fail** — Expected: ทั้ง 2 tests FAIL (ยังไม่ raise)
- [ ] **Step 3: Implement** — ที่ต้น `solve` เรียก `_validate(vcc, r1, r2, rc, re, beta, vbe)`:
  helper `_require_positive(name: str, value: float)` raise `ValueError(f"{name} ต้องมากกว่า 0")`; `VBE` ใช้ `ValueError("VBE ต้องไม่ติดลบ")`; ลำดับตรวจ VCC, R1, R2, RC, RE, β, VBE (β ใช้ชื่อ "β" ในข้อความ)
- [ ] **Step 4: รันให้ผ่าน** — ทุก test PASS (รวมของ Task 1 ยังผ่าน)
- [ ] **Step 5: Commit** — `feat: input validation with Thai error messages`

### Task 3: Region Warnings — Cutoff / Saturation

**Files:**
- Modify: `dc_bias.py` (branch ใน `solve`)
- Test: `tests/test_dc_bias.py` (เพิ่ม class)

**Interfaces:**
- Consumes: `solve()` จาก Task 2
- Produces: branch ตัดสิน region — กติกา: `VTH <= VBE` → cutoff (IB=IC=IE=0, VE=0, **VB=VTH**, VC=VCC, VCE=VCC) · หลังคำนวณ `VCE < 0.2` → saturation (แสดงค่าตามสูตรได้ แต่ต้องมี warning) · วิธีอื่น → forward_active. `warnings` เป็น list ข้อความไทย (copy ปักด้านล่าง)

- [ ] **Step 1: เขียน failing tests**:

```python
class TestRegionWarnings(unittest.TestCase):
    def test_cutoff_region(self):
        # VCC=5, R1=100k, R2=1k -> VTH = 0.0495 V <= 0.7 V
        r = solve(5.0, 100e3, 1e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0); self.assertEqual(r.ic, 0.0)
        self.assertAlmostEqual(r.vb, 0.049505, delta=1e-6)
        self.assertAlmostEqual(r.vc, 5.0, delta=1e-9)
        self.assertTrue(any("Cutoff" in w for w in r.warnings))

    def test_cutoff_boundary_vth_equals_vbe(self):
        # VCC=1.4, R1=R2=1k -> VTH = 0.7 V == VBE
        r = solve(1.4, 1e3, 1e3, 1e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "cutoff")

    def test_saturation_region(self):
        # VCC=1.2, R1=10k, R2=100k, RC=2.2k, RE=1k, beta=100 -> VCE ~ 0.06 V
        r = solve(1.2, 10e3, 100e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.2)
        self.assertTrue(any("Saturation" in w for w in r.warnings))
```

- [ ] **Step 2: รันให้ fail** — Expected: 3 tests FAIL (region ยังเป็น forward_active เสมอ)
- [ ] **Step 3: Implement** — ใน `solve` หลัง validation:
  1) คำนวณ VTH/RTH → `if vth <= vbe:` คืน DCBiasResult แบบ cutoff พร้อม warning `"Cutoff: VTH ≤ VBE ทรานซิสเตอร์ไม่นำ (IB = 0) — แบบจำลอง Forward-Active ใช้ไม่ได้กับค่าที่ป้อน"`
  2) คำนวณตามสูตรปกติ → `if vce < SATURATION_THRESHOLD_V (0.2):` region="saturation" + warning `"Saturation: VCE < 0.2 V — ค่าที่คำนวณด้วยแบบจำลอง Forward-Active ไม่น่าเชื่อถือ"` (ยังแสดงค่าตามสูตรทั้งหมด)
  3) ไม่เข้าเงื่อนไขไหน → forward_active, warnings=[]
- [ ] **Step 4: รันให้ผ่าน** — ทุก test PASS
- [ ] **Step 5: Commit** — `feat: cutoff and saturation region warnings`

### Task 4: Flask Web App — Routes, Template, CSS

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`, `requirements.txt`, `tests/test_web.py`

**Interfaces:**
- Consumes: `solve()`, `DCBiasResult` จาก Task 1–3
- Produces: `app` (Flask instance), `DEFAULTS` dict `{"vcc": 12.0, "r1": 100.0, "r2": 22.0, "rc": 2.2, "re": 1.0, "beta": 100.0, "vbe": 0.70}` (หน่วยฟอร์ม: V, kΩ), `parse_form(form) -> dict[str, float]` (คืนหน่วยฟอร์ม ยังไม่แปลง kΩ), routes: `GET /` และ `POST /calculate`

- [ ] **Step 1: เขียน failing tests** — `tests/test_web.py`:

```python
import unittest
from app import app

DEFAULTS_FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"}

class TestWeb(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):              # A1
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("VCC", text); self.assertIn("Calculate DC Bias", text)

    def test_post_calculate_shows_result(self):        # A2 + A3
        resp = self.client.post("/calculate", data=DEFAULTS_FORM)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("1.230", text)   # IC = 1.230 mA
        self.assertIn("mA", text)

    def test_post_invalid_resistor_shows_error(self):  # A4
        form = dict(DEFAULTS_FORM, r1="-5")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("R1 ต้องมากกว่า 0", resp.data.decode("utf-8"))

    def test_post_non_numeric_value(self):              # A4
        form = dict(DEFAULTS_FORM, vcc="abc")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องเป็นตัวเลข", resp.data.decode("utf-8"))

    def test_post_empty_field(self):                   # A4
        form = dict(DEFAULTS_FORM, r2="")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องเป็นตัวเลข", resp.data.decode("utf-8"))

    def test_post_whitespace_number(self):
        form = dict(DEFAULTS_FORM, vcc=" 12 ")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1.230", resp.data.decode("utf-8"))

    def test_cutoff_warning_displayed(self):           # A5
        form = dict(DEFAULTS_FORM, vcc="5", r1="100", r2="1")
        resp = self.client.post("/calculate", data=form)
        self.assertIn("Cutoff", resp.data.decode("utf-8"))

    def test_saturation_warning_displayed(self):        # A5
        form = {"vcc": "1.2", "r1": "10", "r2": "100", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"}
        resp = self.client.post("/calculate", data=form)
        self.assertIn("Saturation", resp.data.decode("utf-8"))
```

- [ ] **Step 2: รันให้ fail** — Expected: ERROR `ModuleNotFoundError: No module named 'app'`
- [ ] **Step 3: สร้าง venv + ติดตั้ง flask** — จาก repo root:
  `py -m venv .venv` → `.venv\Scripts\python.exe -m pip install flask` → เขียน `requirements.txt` บรรทัดเดียว: `flask>=3.0`
- [ ] **Step 4: Implement `app.py`**:
  - `LABELS = {"vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC", "re": "RE", "beta": "β", "vbe": "VBE"}`
  - `parse_form(form)`: ทุก field `.strip()` แล้ว `float()` — ValueError → `raise ValueError(f"{LABELS[name]} ต้องเป็นตัวเลข เช่น 12")`
  - `GET /` → `render_template("index.html", defaults=DEFAULTS)`
  - `POST /calculate` → try parse → `solve(vcc, r1*1000, r2*1000, rc*1000, re*1000, beta, vbe)` (แปลง kΩ→Ω ตรงนี้) → render พร้อม `result`; catch `ValueError` ทั้งของ parse และ solve → render พร้อม `error=str(e)` และค่าที่ผู้ใช้กรอกค้างไว้, status 200 เสมอ
- [ ] **Step 5: Implement `templates/index.html`** — หน้าเดียว: `<html lang="th">`, form POST `/calculate` (input `name` ตรง keys ของ DEFAULTS, `value="{{ defaults.x }}`, `step="any"`, `inputmode="decimal"`), ปุ่ม `Calculate DC Bias`, กล่อง error สีแดง, กล่อง warning สีส้ม (วน `result.warnings`), ตารางผล 2 คอลัมน์ (ชื่อค่า + หน่วย):
  VTH `{{ "%.3f"|format(result.vth) }} V` · RTH `{{ "%.3f"|format(result.rth/1000) }} kΩ` · IB `{{ "%.3f"|format(result.ib*1e6) }} µA` · IC `{{ "%.3f"|format(result.ic*1000) }} mA` · IE `{{ "%.3f"|format(result.ie*1000) }} mA` · VE/VB/VC/VCE `{{ "%.3f"|format(...) }} V` และแถบ region + ท้ายหน้าแสดงสมการอ้างอิง
- [ ] **Step 6: Implement `static/style.css`** — โครงง่าย: card กลางจอ, ตารางมีเส้น, กล่อง error/warning มีสี, responsive; link ผ่าน `{{ url_for('static', filename='style.css') }}`
- [ ] **Step 7: รัน tests ให้ผ่าน** — `.venv\Scripts\python.exe -m unittest discover -s tests -v` → ทุก test PASS (10 ตัวรวม Task 1–3)
- [ ] **Step 8: เปิดจริงใน browser ตรวจด้วยตา** — `.venv\Scripts\python.exe -m flask --app app run --debug` → เปิด `http://127.0.0.1:5000/` → กด Calculate ด้วยค่า default → เห็นผล + ลองกรอก R1 = -5 เห็น error
- [ ] **Step 9: Commit** — `feat: flask web app with form, results, errors and warnings`
  ไฟล์: `app.py`, `templates/index.html`, `static/style.css`, `requirements.txt`, `tests/test_web.py`

### Task 5: Packaging — README, AGENTS.md

**Files:**
- Create: `README.md`, `AGENTS.md`

**Interfaces:**
- Consumes: โครงสร้างไฟล์และคำสั่งจริงจาก Task 1–4
- Produces: เอกสารที่คนภายนอก clone แล้วรันตามได้ (เกณฑ์ A7)

- [ ] **Step 1: เขียน `README.md`** — หัวข้อบังคับ: คำอธิบายโปรเจกต์ + สมมติฐาน forward-active · โครงสร้างไฟล์ · ขั้นตอนติดตั้ง/รัน **ด้วย `py` ให้ตรงเครื่อง Windows**: `py -m venv .venv` → `.venv\Scripts\Activate.ps1` (PowerShell) → `python -m pip install -r requirements.txt` → `python -m flask --app app run --debug` → เปิด `http://127.0.0.1:5000/` · รัน tests: `py -m unittest discover -s tests -v` · ตาราง mapping เกณฑ์ A1–A7 → ไฟล์/test ที่พิสูจน์ · หมายเหตุ debug server เฉพาะเครื่องพัฒนา
- [ ] **Step 2: เขียน `AGENTS.md`** — ข้อตกลงสั้น ๆ: หน้าที่ไฟล์ (dc_bias ล้วนวิศวกรรม / app.py เรื่อง web / template ไม่ฝังสมการ), TDD + `py -m unittest` ก่อน commit เสมอ, ภาษา UI ไทย, ห้าม commit `.venv/`
- [ ] **Step 3: ตรวจ reproducibility ตาม README** — สร้าง venv ใหม่ `.venv-verify` → install จาก `requirements.txt` → รัน tests ผ่าน → ลบ `.venv-verify` — ถ้าขั้นใดติดขัดแก้ README ให้ตรงความจริง
- [ ] **Step 4: Commit** — `docs: README with py-based setup and AGENTS conventions`

### Task 6: Verification Docs + ส่งมอบ

**Files:**
- Create: `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: ผลรันจริงจาก Task 4–5
- Produces: หลักฐานตรวจรับ (rubric: Review Code, README, Reflection)

- [ ] **Step 1: เขียน `docs/validation.md`** — ตารางเทียบ "คำนวณมืออิสระ vs ผลจากเว็บ" ด้วยชุดข้อมูล Lab (9 ค่า: VTH…VCE), ผล test run ล่าสุด (จำนวน tests ผ่าน), ตารางทดลอง error/warning (R1=-5, vcc=abc, ชุด cutoff, ชุด saturation) พร้อมผลที่เห็นจริงบน browser
- [ ] **Step 2: เขียน `docs/reflection.md`** — โครงคำถามชวนคิดให้นักศึกษาเติมเอง (ภาษาไทย): 4 คำถามรายบุคคลจาก Lab §10 (ทำไมเปิด index.html ตรง ๆ ≠ รัน Flask ฯลฯ) + สิ่งที่ AI ช่วย/สิ่งที่ตรวจเอง + ปัญหาที่เจอและวิธีแก้
- [ ] **Step 3: รัน tests รอบสุดท้าย** — `py -m unittest discover -s tests -v` → ทุกตัว PASS — บันทึงผลลง validation.md
- [ ] **Step 4: Commit** — `docs: validation record and reflection scaffold`
- [ ] **Step 5: ส่งมอบฝั่งผู้ใช้** — นักศึกษาเปิด GitHub Desktop → publish repository → ส่ง URL + commit SHA ทาง Moodle

---

## Execution Notes

- Repo เป็น greenfield (initial commit เดียว ไม่มีงานค้าง) — **ไม่ต้องสร้าง worktree** แยก
- `py -m unittest discover -s tests -v` รันจาก repo root เสมอ (module `dc_bias`/`app` import ได้เพราะ `-m` ใส่ cwd ใน sys.path)
- Tests ก่อน venv (Task 1–3) ใช้ `py` ตรง ๆ; หลังสร้าง venv (Task 4+) ใช้ `.venv\Scripts\python.exe -m unittest discover -s tests -v`
