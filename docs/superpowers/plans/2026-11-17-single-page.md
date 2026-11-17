# Single-Page Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** รวม 3 วงจร (Voltage-Divider, Fixed, Emitter) ไว้ในหน้า `/` หน้าเดียวแบบ `<details>` พับได้ โดยไม่ใช้ JavaScript และไม่เปลี่ยนผลคำนวณ

**Architecture:** ใช้ Flask server-rendered เดิม — `index.html` กลายเป็นหน้าเดียวที่มี 3 `<details>` แต่ละส่วนมีฟอร์ม POST ไป route เดิม (`/calculate`, `/calculate-fixed`, `/calculate-emitter`) แล้ว render `index.html` กลับด้วยตัวแปร `circuit` เพื่อเปิดเฉพาะส่วนที่ส่ง พร้อม `result`/`error`/`entered` เฉพาะ circuit นั้น ใช้ `_results.html` ร่วมเหมือนเดิม

**Tech Stack:** Python 3, Flask ≥3.0, Jinja2, unittest, venv `.venv`

**Spec:** `docs/superpowers/specs/2026-11-17-single-page-design.md`

## Global Constraints

- ไม่ใช้ JavaScript, dropdown ไดนามิก หรือการสลับฟิลด์แบบทันที
- ห้ามเปลี่ยน `dc_bias.py`, สมการ, validation, region, cutoff/saturation warning หรือค่าอ้างอิง (1.230 / 2.404 / 1.979 mA)
- หน่วยฟอร์ม: V, kΩ (แปลงเป็น Ω เฉพาะใน web layer เหมือนเดิม), β ไม่มีหน่วย
- ข้อความ error/warning เป็นภาษาไทย + ศัพท์เทคนิคอังกฤษ; ห้ามเปลี่ยนข้อความเดิม
- Runner: `.venv\Scripts\python.exe -m unittest discover -s tests -v` จาก repo root เท่านั้น
- Git ในเครื่องนี้ใช้พาธเต็ม `C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe`
- ทำงานบน `main` แบบ inline (ตามที่ตกลงไว้) commit เฉพาะ local; ผู้ใช้เป็นคน push ผ่าน GitHub Desktop
- ห้าม commit `.venv/`, `__pycache__/`, secrets

## Review Focus

- **หน้า `/` ต้องมีครบ 3 ส่วน** — ถ้าลืม `<summary>` หรือ form action ของวงจรใด วงจรนั้นหายจากหน้า → Task 1 `test_single_page_has_three_sections`
- **หลังกด Calculate ต้องเปิดเฉพาะส่วนที่ส่ง** — ถ้าเปิดทั้ง 3 หรือเปิดผิดส่วน users จะเห็นผลอยู่คนละที่ → Task 2 `test_post_opens_submitted_section_and_shows_result`
- **URL เก่า `/fixed`, `/emitter` ต้อง redirect ไม่ใช่ 404/500** — bookmarks และลิงก์ในเอกสารเดิมต้องยังใช้ได้ → Task 2 `test_old_urls_redirect_to_single_page`
- **ค่า default ของ RB ต้องโชว์ 470.0 ในหน้าเดียว** — ถ้าใช้ `DEFAULTS` เดิมที่ไม่มี key `rb` ช่อง RB จะว่าง → Task 2 `test_single_page_defaults_for_all_circuits`
- **error หลัง POST ต้องค้างค่าที่กรอกในส่วนที่ถูกต้อง** — ถ้า `entered` หลุดหรือไปตกส่วนอื่น users ต้องกรอกใหม่ทั้งฟอร์ม → Task 2 `test_post_error_repopulates_entered_value` (เดิม) + `test_post_opens_submitted_section_and_shows_result`
- **query param ผิด (`?circuit=bogus`) ต้องไม่พังหน้า** — ต้อง fallback ไป divider → Task 2 `test_query_param_opens_requested_section`

---

### Task 1: หน้าเดียว — โครงสร้าง 3 ส่วน + CSS

**Files:**
- Modify: `templates/index.html`, `static/style.css`, `tests/test_web.py`
- ไม่ลบ template เก่าใน task นี้ (route ยังใช้ `/fixed`, `/emitter` อยู่จนกว่าจะถึง Task 2)

**Interfaces:**
- Consumes: `result`, `error`, `entered`, `defaults`, `circuit` ที่ route ส่งเข้า `index.html` อยู่แล้ว
- Produces: `<details class="circuit">` จำนวน 3 อันใน `/` แต่ละอันมี `<summary>` ตามลำดับคือ `Voltage-Divider Bias`, `Fixed Bias`, `Emitter Bias` และฟอร์มที่ `action` ตามลำดับคือ `/calculate`, `/calculate-fixed`, `/calculate-emitter`; `<details>` ได้ attribute `open` เมื่อ `circuit` ตรงกับส่วนนั้น

- [ ] **Step 1: แทนที่ `test_nav_links_on_all_pages` ด้วย failing test ของหน้าเดียว**

ใน `tests/test_web.py` ลบ `test_nav_links_on_all_pages` แล้วเพิ่มใน `TestFixedEmitterWeb`:

```python
def test_single_page_has_three_sections(self):
    text = self.client.get("/").data.decode("utf-8")
    self.assertEqual(text.count("<details"), 3)
    for title in ("Voltage-Divider Bias", "Fixed Bias", "Emitter Bias"):
        self.assertIn(f"<summary>{title}</summary>", text)
    for action in ("/calculate", "/calculate-fixed", "/calculate-emitter"):
        self.assertIn(f'action="{action}"', text)
    for field in ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe"):
        self.assertIn(f'name="{field}"', text)
    self.assertNotIn('href="/fixed"', text)  # ไม่มีแถบ nav แล้ว
```

- [ ] **Step 2: รัน test file เพื่อยืนยัน RED**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: FAIL — `assertEqual(0, 3)` เพราะ `/` ยังไม่มี `<details>`

- [ ] **Step 3: เขียน `templates/index.html` ใหม่เป็น 3 ส่วน**

โครงสร้างที่ต้องได้ (ห้ามใช้ JS):
```
<main class="card">
  <h1>...</h1>
  <p class="subtitle">NPN Common Emitter · 3 bias circuits · แบบจำลอง Forward-Active ...</p>
  <details class="circuit" {% if circuit == 'divider' %}open{% endif %}>
    <summary>Voltage-Divider Bias</summary>
    {% if circuit == 'divider' and error %} ... error div เดิม ... {% endif %}
    <form method="post" action="/calculate"> 7 ช่อง vcc r1 r2 rc re beta vbe </form>
    {% if circuit == 'divider' %}{% include "_results.html" %}{% endif %}
  </details>
  <details class="circuit" {% if circuit == 'fixed' %}open{% endif %}>
    <summary>Fixed Bias</summary>
    {% if circuit == 'fixed' and error %} ... {% endif %}
    <form method="post" action="/calculate-fixed"> 5 ช่อง vcc rb rc beta vbe </form>
    {% if circuit == 'fixed' %}{% include "_results.html" %}{% endif %}
  </details>
  <details class="circuit" {% if circuit == 'emitter' %}open{% endif %}>
    <summary>Emitter Bias</summary>
    {% if circuit == 'emitter' and error %} ... {% endif %}
    <form method="post" action="/calculate-emitter"> 6 ช่อง vcc rb rc re beta vbe </form>
    {% if circuit == 'emitter' %}{% include "_results.html" %}{% endif %}
  </details>
  <footer> สมการอ้างอิงของทั้ง 3 วงจร (คงข้อความเดิมของแต่ละวงจร) </footer>
</main>
```
- ทุก input ใช้ `value="{{ entered.get('field', defaults.field) if entered is defined else defaults.field }}"` เหมือน commit `35721ed` (ช่องที่กรอกแล้ว error ต้องค้าง)
- ลบ `{% include "_nav.html" %}` ออกจาก `index.html` (แต่ยังไม่ลบไฟล์ `_nav.html`)
- Footer รวมสมการของทั้ง 3 วงจรจาก footer เดิมของ `index.html`, `fixed.html`, `emitter.html`

- [ ] **Step 4: แทนที่ CSS `.nav` ด้วย `.circuit`**

ใน `static/style.css` ลบ block `.nav`, `.nav a`, `.nav a:hover`, `.nav a.active` (บรรทัด 26–49) แล้วเพิ่ม:

```css
.circuit {
  border: 1px solid #d3e0ec;
  border-radius: 8px;
  margin: 14px 0;
  padding: 0 14px;
}

.circuit > summary {
  cursor: pointer;
  font-weight: 700;
  color: #103658;
  padding: 12px 0;
}

.circuit[open] > summary {
  border-bottom: 1px solid #e2ebf3;
  margin-bottom: 10px;
}
```

- [ ] **Step 5: รัน test file เพื่อยืนยัน GREEN**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: PASS ทุก test รวม 9 ตัวเดิมของ `TestWeb` และ tests ของ `TestFixedEmitterWeb` (ยกเว้น nav test ที่ถูกรีดแล้ว)

- [ ] **Step 6: รันชุด tests เต็ม**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS 37 tests (17 unit + 20 HTTP) — ถ้าล้มเหลวแปลว่า template กระทบ route เก่า ต้องแก้ก่อนไปต่อ

- [ ] **Step 7: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add templates/index.html static/style.css tests/test_web.py
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: combine three bias circuits into one collapsible page"
```

### Task 2: Routes ส่ง state ไปหน้าเดียว + redirect URL เก่า

**Files:**
- Modify: `app.py`, `tests/test_web.py`
- Delete: `templates/fixed.html`, `templates/emitter.html`, `templates/_nav.html`

**Interfaces:**
- Consumes: `index.html` จาก Task 1 (อ่าน `circuit`, `defaults`, `result`, `error`, `entered`), `DEFAULTS`, `FIXED_DEFAULTS`, `EMITTER_DEFAULTS`, `FORM_FIELDS*`, `parse_form`, `solve*` เดิมใน `app.py`
- Produces:
  - `ALL_DEFAULTS = {**DEFAULTS, **FIXED_DEFAULTS}` → มี key `vcc, r1, r2, rb, rc, re, beta, vbe` ค่าตามลำดับ `12.0, 100.0, 22.0, 470.0, 2.2, 1.0, 100.0, 0.70` (ค่า `re` ของ emitter เท่ากับ `DEFAULTS["re"]` อยู่แล้ว)
  - `GET /` อ่าน `circuit = request.args.get("circuit", "divider")` แล้ว fallback เป็น `"divider"` ถ้าไม่อยู่ใน `("divider", "fixed", "emitter")`
  - `GET /fixed` → `redirect("/?circuit=fixed")`, `GET /emitter` → `redirect("/?circuit=emitter")` (302)
  - POST ทั้ง 3 ตัว render `index.html` ด้วย `defaults=ALL_DEFAULTS` และ `circuit` ตรงกับ route

- [ ] **Step 1: เขียน failing tests ใน `tests/test_web.py`**

เพิ่ม `import re` ด้านบน แล้วแทนที่ `test_get_fixed_returns_form` และ `test_get_emitter_returns_form` ด้วย tests เหล่านี้ใน `TestFixedEmitterWeb` (เป็น method ใน class ทุกตัว):

```python
def assert_open_section(self, text, title):
    self.assertRegex(text, rf'<details[^>]*\bopen\b[^>]*>\s*<summary>{title}</summary>')
    self.assertEqual(len(re.findall(r'<details[^>]*\bopen\b', text)), 1)

def test_old_urls_redirect_to_single_page(self):
    for path, location in (("/fixed", "/?circuit=fixed"), ("/emitter", "/?circuit=emitter")):
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.headers["Location"], location)

def test_query_param_opens_requested_section(self):
    for param, title in (("fixed", "Fixed Bias"), ("emitter", "Emitter Bias"), ("bogus", "Voltage-Divider Bias")):
        text = self.client.get(f"/?circuit={param}").data.decode("utf-8")
        self.assertEqual(text.count("<details"), 3)
        self.assert_open_section(text, title)

def test_post_opens_submitted_section_and_shows_result(self):
    cases = (
        ("/calculate", DEFAULTS_FORM, "1.230", "Voltage-Divider Bias"),
        ("/calculate-fixed", FIXED_FORM, "2.404", "Fixed Bias"),
        ("/calculate-emitter", EMITTER_FORM, "1.979", "Emitter Bias"),
    )
    for route, form, number, title in cases:
        text = self.client.post(route, data=form).data.decode("utf-8")
        self.assertIn(number, text)
        self.assert_open_section(text, title)

def test_single_page_defaults_for_all_circuits(self):
    text = self.client.get("/").data.decode("utf-8")
    for field, value in (("r1", "100.0"), ("r2", "22.0"), ("rb", "470.0"),
                         ("rc", "2.2"), ("re", "1.0"), ("beta", "100.0"), ("vbe", "0.7")):
        self.assertRegex(text, rf'name="{field}"\s+value="{re.escape(value)}"')
```

- [ ] **Step 2: รัน test file เพื่อยืนยัน RED**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: FAIL — `GET /fixed` คืน 200 ไม่ใช่ 302 และ `/?circuit=fixed` ไม่เปิดส่วน fixed

- [ ] **Step 3: แก้ `app.py`**

- เปลี่ยน import เป็น `from flask import Flask, redirect, render_template, request`
- เพิ่ม `ALL_DEFAULTS = {**DEFAULTS, **FIXED_DEFAULTS}` หลัง `EMITTER_DEFAULTS`
- `index()` → อ่าน query param ตาม Interfaces แล้ว `render_template("index.html", defaults=ALL_DEFAULTS, circuit=circuit)`
- `fixed_page()` / `emitter_page()` → `redirect("/?circuit=fixed")` / `redirect("/?circuit=emitter")`
- ใน `calculate()`, `calculate_fixed()`, `calculate_emitter()`: เปลี่ยนทุก `render_template("index.html"/"fixed.html"/"emitter.html", defaults=...)` เป็น `render_template("index.html", defaults=ALL_DEFAULTS, circuit=<circuit ของ route นั้น>, ...)`
- **ห้ามแตะ** การ parse form, การคูณ 1000.0, การเรียก `solve*`, `entered` หรือข้อความ error
- อัปเดต docstring ด้านบนไฟล์ว่า `/` เป็นหน้าเดียวและ `/fixed`, `/emitter` เป็น redirect

- [ ] **Step 4: ลบ template ที่ไม่ใช้แล้ว**

ลบ `templates/fixed.html`, `templates/emitter.html`, `templates/_nav.html` (ตอนนี้ route ไม่ได้ render ไฟล์เหล่านี้แล้ว)

- [ ] **Step 5: รัน test file เพื่อยืนยัน GREEN**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -p "test_web.py" -v`
Expected: PASS ทุก test รวม `test_post_error_repopulates_entered_value` และ tests ของ cutoff/saturation เดิม

- [ ] **Step 6: รันชุด tests เต็ม**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS 39 tests (17 unit + 22 HTTP)

- [ ] **Step 7: HTTP smoke test บน debug server**

```powershell
$ErrorActionPreference='Stop'
foreach ($p in @('/', '/?circuit=fixed', '/?circuit=emitter')) {
  $r = Invoke-WebRequest -Uri "http://127.0.0.1:5000$p" -UseBasicParsing -TimeoutSec 10
  "GET $p = $($r.StatusCode); details_count=$([regex]::Matches($r.Content, '<details').Count)"
}
$body = @{vcc='12'; rb='470'; rc='2.2'; beta='100'; vbe='0.7'}
$r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/calculate-fixed' -Method Post -Body $body -UseBasicParsing -TimeoutSec 10
"fixed POST = $($r.StatusCode); has_2.404=$($r.Content -match '2\.404'); fixed_open=$($r.Content -match '(?s)<details[^>]*open[^>]*>\s*<summary>Fixed Bias</summary>')"
```
Expected: ทุก GET = 200 และ `details_count=3`, POST = 200 พร้อม `has_2.404=True` และ `fixed_open=True` (redirect 302 ตรวจใน test client แล้วที่ Step 5)

- [ ] **Step 8: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add -A app.py templates tests/test_web.py
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "feat: route all circuits through single page and redirect old URLs"
```

### Task 3: อัปเดตเอกสารให้ตรงหน้าเดียว

**Files:**
- Modify: `README.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
- ยืนยัน: จำนวน tests จริงจาก Task 2 Step 6

**Interfaces:**
- Consumes: route ใหม่, จำนวน tests 39 (17 unit + 22 HTTP), การลบ template 3 ไฟล์

- [ ] **Step 1: อัปเดต `README.md`**

- intro เปลี่ยนจาก "3 หน้า" เป็น "หน้าเดียว `/` แบ่งเป็น 3 ส่วนพับได้"
- ตาราง route: `GET /fixed` → redirect `/?circuit=fixed`, `GET /emitter` → redirect `/?circuit=emitter`, POST ทั้ง 3 ตัวยังอยู่
- โครงสร้างไฟล์: ลบ `fixed.html`, `emitter.html`, `_nav.html` ออกจากรายการ
- เปลี่ยน `37 tests` / `17 unit + 20 HTTP` เป็น `39 tests` / `17 unit + 22 HTTP` (ทุกที่ที่ปรากฏ)
- อัปเดตแถว A6 และแถวส่วนต่อขยายให้ mention หน้าเดียว

- [ ] **Step 2: อัปเดต `docs/design-note.md`**

เพิ่มหัวข้อ "รวมหน้า 17 พ.ย. 2569 (ต่อจากส่วนขยาย Fixed/Emitter)" ที่สรุป: หน้า `/` เดียว 3 `<details>`, ไม่ใช้ JS, `/fixed` `/emitter` redirect ไป query param, POST routes และ solver ไม่เปลี่ยน — ห้ามลบเนื้อหาเดิม

- [ ] **Step 3: อัปเดต `docs/validation.md`**

- เปลี่ยนจำนวน tests เป็น 39 และอธิบายว่า HTTP tests เพิ่มredirect/query-param/open-section
- เพิ่มผล smoke test: GET `/fixed`, `/emitter` → 302 · GET `/?circuit=fixed` → 200 และเปิดส่วน Fixed · POST `/calculate-fixed` → 2.404 mA พร้อม `<details open>` ของ Fixed
- คงตารางค่าอ้างอิงเดิมทั้งหมด

- [ ] **Step 4: อัปเดต `docs/reflection.md`**

เปลี่ยนข้อความ "เว็บ 3 หน้า" เป็น "หน้าเดียว 3 ส่วนพับได้" และเปลี่ยนจำนวน tests เป็น 39 — อย่าแก้ placeholder ชื่อ-สกุล

- [ ] **Step 5: ตรวจความสอดคล้อง**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: PASS 39 tests
Run: `grep` หา `37 tests`, `href="/fixed"`, `3 หน้า`, `_nav.html`, `fixed.html`, `emitter.html` ใน `README.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
Expected: ไม่พบ `37 tests` หรือ `href="/fixed"` เลย; คำว่า `3 หน้า` และชื่อ template เก่าอนุญาตให้เหลือได้เฉพาะในบริบทประวัติของ `docs/design-note.md` (ต้องมีหัวข้อใหม่ระบุว่ารวมเป็นหน้าเดียวแล้ว)

- [ ] **Step 6: Commit**

```powershell
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' add README.md docs
& 'C:\Users\b6821982\AppData\Local\Programs\Git\cmd\git.exe' commit -m "docs: describe single-page layout and redirects"
```
