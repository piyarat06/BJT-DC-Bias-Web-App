# Validation Record — BJT Bias & CE Amplifier Simulator

บันทึกการตรวจสอบความถูกต้องของผลการคำนวณและผลจำลอง (ENG29 2121 · Lab 02 → Lab 04)
วันที่ตรวจ: 10 พฤศจิกายน 2569 (Lab 02/03), 24 พฤศจิกายน 2569 (Lab 04) · ผู้ตรวจ: นักศึกษา + AI agent

## 1. ค่าอ้างอิงอิสระ (คำนวณมือ) เทียบผลจากเว็บ

ชุดข้อมูลทดลองของ Lab: VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ,
RE=1 kΩ, β=100, VBE=0.70 V — คำนวณมือด้วยสมการ
VTH = VCC·R2/(R1+R2), RTH = R1·R2/(R1+R2),
IB = (VTH−VBE)/(RTH+(β+1)RE), IC = β·IB, IE = (β+1)·IB,
VE = IE·RE, VB = VE+VBE, VC = VCC−IC·RC, VCE = VC−VE

| ค่า | คำนวณมือ (อิสระ) | ผลจากเว็บ (`POST /calculate`) | ตรงกัน |
|---|---|---|---|
| VTH | 2.163934 V | 2.164 V | ✓ |
| RTH | 18.033 kΩ | 18.033 kΩ | ✓ |
| IB | 12.299 µA | 12.299 µA | ✓ |
| IC | 1.230 mA | 1.230 mA | ✓ |
| IE | 1.242 mA | 1.242 mA | ✓ |
| VE | 1.242 V | 1.242 V | ✓ |
| VB | 1.942 V | 1.942 V | ✓ |
| VC | 9.294 V | 9.294 V | ✓ |
| VCE | 8.052 V | 8.052 V | ✓ |

สรุป: ผลจาก Python Backend ตรงกับการคำนวณมืออย่างอิสระครบทุกค่า
ภายใต้แบบจำลอง Forward-Active เดียวกัน — VCE = 8.052 V > 0.2 V
และ VTH > VBE จึงอยู่ใน forward-active region จริง

## 2. ผล Automated Tests (รอบสุดท้าย)

คำสั่ง: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
(จาก repo root, venv ที่ติดตั้งจาก `requirements.txt`)

ผลรอบสุดท้าย (หลังเพิ่ม Lab 04): **Ran 69 tests — OK (ผ่านทั้งหมด)** —
17 `test_dc_bias.py` + 23 `test_web.py` (Lab 03 เดิม 40 ตัวยังผ่าน) +
20 `test_spice_engine.py` (รวม timeout/exit≠0/raw ว่าง) + 9 `test_simulator_web.py` (Lab 04)
- `tests/test_dc_bias.py` — 17 tests: ค่าอ้างอิง 9 ค่าของ Voltage-Divider,
  ตัวเลขสุดขั้ว (ตรวจ finite), validation 7 กรณี, ข้อความ error ระบุชื่อฟิลด์,
  ค่า inf/NaN ถูกปฏิเสธ, cutoff, ขอบเขต VTH==VBE, saturation **+ 8 tests
 ของ Fixed/Emitter** (ค่าอ้างอิง 2 วงจร, cutoff 2, saturation 2, validate RB/RE, inf/NaN)
- `tests/test_web.py` — 23 tests ผ่าน Flask test client: GET / ฟอร์มครบ
  7 ช่อง, POST คำนวณจริง, ค่าติดลบ, ค่าไม่ใช่ตัวเลข, ค่า inf (1e309),
  ช่องว่าง, ค่ามีช่องว่างรอบตัวเลข, warning cutoff และ saturation
  แสดงบนหน้าเว็บ **+ 13 tests ของหน้าเดียว/ส่วนต่อขยาย** (3 `<details>` ใน `/`,
  query param เปิดส่วนที่ขอ + fallback, redirect URL เก่า 302, POST ผลจริงของ 3 วงจร
  พร้อม `<details open>` ตรงส่วนที่ส่ง, default RB=470.0, RB ติดลบ/ว่าง,
  inf, cutoff, saturation, ค่าที่กรอกค้างหลัง error)

## 3. การทดลองบน Browser จริง (http://127.0.0.1:5000/)

| กรณีที่กรอก | สิ่งที่เห็นบนหน้าเว็บ | ผล |
|---|---|---|
| ค่า default → กด Calculate DC Bias | ตาราง DC Bias Results 9 ค่าพร้อมหน่วย, region = forward_active | ✓ |
| R1 = −5 | กล่องแดง "ข้อมูลไม่ถูกต้อง: R1 ต้องมากกว่า 0" หน้าไม่ล้ม (HTTP 200) | ✓ |
| VCC = abc | กล่องแดง "VCC ต้องเป็นตัวเลข เช่น 12" หน้าไม่ล้ม | ✓ |
| VCC = 1e309 (Python parse เป็น inf) | กล่องแดง "VCC ต้องเป็นจำนวนจำกัด (ห้าม inf หรือ NaN)" หน้าไม่ล้ม — จาก code review fix | ✓ |
| VCC=5, R2=1 (VTH=0.05 V < VBE) | region = cutoff + กล่องส้มเตือน "Cutoff: VTH ≤ VBE ทรานซิสเตอร์ไม่นำ …" | ✓ |
| VCC=1.2, R1=10, R2=100 (VCE≈0.06 V) | region = saturation + กล่องส้มเตือน "Saturation: VCE < 0.2 V … ไม่น่าเชื่อถือ" | ✓ |

## 4. Reproducibility

สร้าง venv ใหม่ทั้งหมด (`.venv-verify`) → `pip install -r requirements.txt`
→ รัน tests → 40/40 ผ่าน → ลบทิ้ง: ยืนยันว่าคนภายนอก clone repo แล้วทำตาม
README ได้ผลเหมือนกัน (เกณฑ์ A7) — ตรวจซ้ำหลังแก้ปัญหาจาก code review
และหลังเพิ่ม Fixed/Emitter Bias + รวมหน้าเดียว (มี tests เพิ่มเป็น 40 ตัว) ก่อนส่งมอบ

## 5. ข้อจำกัดของแบบจำลอง

- Forward-Active Approximation (β คงที่, VBE คงที่) — ไม่ใช่ SPICE
- กรณี cutoff: แสดง IB=IC=IE=0, VB=VTH (ไม่มีกระแสฐาน) พร้อม warning
- กรณี saturation: ค่าที่คำนวณตามสูตรยังแสดง แต่มี warning ว่าใช้เป็นผล
  จำลองที่เชื่อถือได้ไม่ได้

## 6. ส่วนต่อขยาย Fixed/Emitter Bias (17 พ.ย. 2569)

ชุดอ้างอิงคำนวณมือ: VCC=12 V, RB=470 kΩ, RC=2.2 kΩ, β=100, VBE=0.70 V
(เพิ่ม RE=1 kΩ สำหรับ Emitter) — ใช้ VTH=VCC, RTH=RB

| ค่า | Fixed (คำนวณมือ) | ผลจากเว็บ | Emitter (คำนวณมือ) | ผลจากเว็บ | ตรงกัน |
|---|---|---|---|---|---|
| IB | 24.043 µA | 24.043 µA | 19.790 µA | 19.790 µA | ✓ |
| IC | 2.404 mA | 2.404 mA | 1.979 mA | 1.979 mA | ✓ |
| IE | 2.428 mA | 2.428 mA | 1.999 mA | 1.999 mA | ✓ |
| VE | 0 V | 0 V | 1.999 V | 1.999 V | ✓ |
| VB | 0.700 V | 0.700 V | 2.699 V | 2.699 V | ✓ |
| VC | 6.711 V | 6.711 V | 7.646 V | 7.646 V | ✓ |
| VCE | 6.711 V | 6.711 V | 5.647 V | 5.647 V | ✓ |
| region | forward_active | forward_active | forward_active | forward_active | ✓ |

HTTP smoke test บน debug server (`http://127.0.0.1:5000/`, หลังรวมหน้าเดียว):
GET `/`, `/?circuit=fixed`, `/?circuit=emitter` → 200 และ `details_count=3` ทุกครั้ง ·
GET `/fixed` → 302 `/?circuit=fixed` · GET `/emitter` → 302 `/?circuit=emitter` ·
POST `/calculate` → มี `1.230` mA และเปิดส่วน Voltage-Divider ·
POST `/calculate-fixed` → มี `2.404` mA พร้อม `<details open>` ของ Fixed ·
POST `/calculate-emitter` → มี `1.979` mA และ `5.647` V พร้อมเปิดส่วน Emitter

กรณีตรวจเพิ่ม (test client + browser):
RB = −5 → `RB ต้องมากกว่า 0` · RB ว่าง → `RB ต้องเป็นตัวเลข` ·
`vcc = 1e309` → `VCC ต้องเป็นจำนวนจำกัด` · VCC=0.5 V → Cutoff warning ·
RB=10 kΩ → Saturation warning — ทุกกรณี HTTP 200 หน้าไม่ล้ม
(ข้อความ error/warning ค้างอยู่ใน **ส่วนที่ส่งเท่านั้น** หลังรวมหน้าเดียว)

จำนวน tests รวมหลังส่วนต่อขยาย + รวมหน้าเดียว + code review fix:
**40 tests (17 unit + 23 HTTP) — OK**

การตรวจเพิ่มจาก code review (17 พ.ย. 2569): หลัง POST วงจรใดวงจรหนึ่งด้วยค่า
`vcc=5, rc=3.3, beta=200, vbe=0.9` เฉพาะฟอร์มของวงจรนั้นที่ค้างค่า
(fixed ยังค้าง `rb` ที่ส่งด้วย) — ฟอร์มอีกสองส่วนกลับไปใช้ default `12.0 / 2.2 / 100.0 / 0.7`
ตามสเปค ผ่าน `test_post_entered_values_stay_in_submitted_section`

## 7. Lab 04 · Browser Acceptance B1–B8 (24 พฤศจิกายน 2569)

**Engine จริง:** `ngspice-47` (console binary `ngspice_con.exe`, portable copy ใน
`tools/ngspice/Spice64/bin/`) · **BJT model จริง:** `.MODEL QNPN NPN(IS=1e-14 BF=100 VAF=100 CJE=25p CJC=8p TF=0.4n)`
· **Server:** `http://127.0.0.1:5000/` (Flask dev server, เปิดใหม่หลังแก้ template)

**เครื่องมือที่ใช้จริง:** OpenCode **in-app browser** (`tabs.open/navigate`,
`snapshot`, `fill`, `check`, `press Enter`, `evaluate`, `screenshot`) — **ไม่ได้ใช้
Playwright MCP** เพราะไม่มี tool ตัวนั้นใน session นี้ จึงบันทึกตามชื่อ tool ที่รันจริง
ไม่แอบอ้างว่าเป็น Playwright

| Case | Method | Input | Expected/Reference | Observed | Evidence | Status |
|---|---|---|---|---|---|---|
| B1 Regression | เปิด Fixed → Emitter → Divider, fill ชุด Lab 3, กด Calculate | VCC=12, RB=470, RC=2.2, β=100, VBE=0.7 (+RE=1 สำหรับ Emitter) | IC/VCE ตรงตารางในข้อ 6 | Fixed IC 2.404 mA, VCE 6.711 V · Emitter IC 1.979 mA, VCE 5.647 V · Divider IC 1.230 mA, VCE 8.052 V · ทั้งสาม `forward_active` | browser snapshot/cell text หลัง POST `/calculate-fixed`, `/calculate-emitter`, `/calculate` | PASS |
| B2 DC SPICE | เลือก `DC · .op`, Fill ค่า reference, กด Run | VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, RL=10k, Cin=Cout=10µF, 10 mV/1 kHz | VB/VE/VC/VCE/IC จาก ngspice พร้อม model และ run status | VB 1.949 V · VE 1.289 V · VC 9.189 V · VCE 7.900 V · IC 1.278 mA · `Simulation status: success` · `Model: QNPN · … BF=100` · heading `ngspice 47 · DC` | ตารางผล + netlist/log ที่โชว์บนหน้า (log มี `ngspice-47`) | PASS |
| B3 Change RE | เปลี่ยนเฉพาะ `sim_re=2` แล้ว Run DC ซ้ำ | เหมือน B2 แต่ RE=2 kΩ | Operating point ต้องเปลี่ยน ไม่ใช่ค่าค้าง | netlist เปลี่ยนเป็น `RE n_e 0 2k` · VB 1.949→2.048 V · VE 1.289→1.405 V · IC 1.278→0.696 mA · VCE 7.900→9.065 V | ข้อความ netlist + ตารางก่อน/หลังจาก browser | PASS |
| B4 AC | เลือก `AC · .ac`, กด Run, อ่านกราฟ | ค่า reference, sweep 1 Hz–1 GHz | แกน Frequency (Hz), gain V/V, phase องศา, ข้อมูลจาก run จริง | Gain @1 kHz 1.75 V/V (4.86 dB), phase −179.9°, fL 2.00 Hz, fH 70.79 MHz · 2 SVG · 181 points/series · axis `Frequency (Hz)` / `Gain \|Vout/Vin\| (V/V)` / `Phase (degree)` | `sim-plot-data` (JSON array จาก server) + `svg` 2 อัน + log `.AC DEC 20 1 1G` | PASS |
| B5 Transient | เลือก `Transient · .tran`, Run ที่ 10 mV peak/1 kHz | amplitude=0.01, frequency=1000 | Vin/Vout ตามเวลา, มีหน่วย, สัญญาณกลับเฟส | Vin peak 10.00 mV · Vout peak 17.49 mV · gain 1.75 · `Phase relation: inverted` · axis Time (ms) / Voltage (mV) · 508 points/series | SVG 1 อันมี 2 polyline + legend `Vin Vout` + ตาราง summary | PASS |
| B6 Change Source | เปลี่ยน amplitude 0.01→0.03 แล้ว Run .tran; เปลี่ยน frequency 1000→5000 แล้ว Run ซ้ำ | amplitude/frequency ตามข้อความ | waveform/หน้าต่างเวลาต้องเปลี่ยนตาม input | amplitude: Vin 10.00→30.00 mV, Vout 17.49→52.48 mV, netlist `SIN(0 0.03 1000 0 0)` · frequency: window 5.000→1.000 ms, `SIN(0 0.01 5000 0 0)`, `.TRAN 2e-06 0.001` | ค่า input/netlist/summary ที่อ่านจากหน้าเว็บ 2 รอบ | PASS |
| B7 Invalid / Fail | ใส่ `sim_re=0` แล้ว Run | RE=0 | แจ้ง error, ไม่โชว์ success/กราฟเก่า | `การจำลองไม่สำเร็จ: RE ต้องมากกว่า 0` · `Simulation status: error` · ไม่มี `sim-plot-data` · ไม่มีตารางผล · ค่า RE=0 ค้างในฟอร์ม | browser snapshot หลัง POST `/simulate` | PASS |
| B8 UI | เปิด desktop full page และ iframe กว้าง 390 px (phone-width) แล้วสลับโหมด | AC results เหมือน B4 | กราฟ/หน่วย/ปุ่มอ่านง่าย ไม่ตัดเนื้อหา | desktop: chart SVG เต็มคอลัมน์ · mobile: viewport 368 px, `scrollWidth=368`, ไม่มี horizontal overflow, SVG กว้าง 284 px, ปุ่ม Run กว้าง 175 px อยู่ในจอ, mode=ac, status success | `docs/screenshots/B8-desktop-ac.png`, `docs/screenshots/B8-mobile-390.png` | PASS* |

\* B8 ใช้ **iframe ความกว้าง 390 CSS px ใน browser จริง** เพราะชุด browser tool ไม่มี
viewport/device emulation; ไม่ได้ทดสอบบนเครื่องโทรศัพท์จริง จึงไม่กล่าวอ้างว่าเป็น physical device test

Status `running` ก็ตรวจใน browser จริง: หลังส่ง submit event สถานะเปลี่ยนจาก
`Simulation status: success` → `Simulation status: running…` ก่อนที่ response จะมาถึง
(ต่อมาจะถูก render ใหม่เป็น success/error จาก server)

### หลักฐานว่ากราฟไม่ใช่ mock/hard-code

- ข้อมูลกราฟถูกส่งจาก server เป็น `<script id="sim-plot-data" type="application/json">`
  โดย parse มาจาก raw file ของ ngspice รอบนั้น (`analyze_ac`/`analyze_tran` ใน `spice_engine.py`)
- หน้าเว็บแสดง **netlist ที่ใช้รันจริง** และท้าย log ทุกครั้ง; เปลี่ยน RE/amplitude/frequency
  แล้ว netlist, summary และจุดกราฟเปลี่ยนตาม (B3/B6)
- เมื่อ input ผิด (B7) ไม่มี script กราฟและไม่มีตารางผลเลย ไม่มีการใช้ผลรอบเก่า
- **Issue ที่พบและแก้ไขระหว่างตรวจ B4:** ตอนแรก template ส่ง JSON เป็น object
  `{"charts": [...]}` ขณะที่ `static/app.js` คาด array → หน้าแสดงข้อความ
  `ไม่สามารถวาดกราฟจากข้อมูลที่ส่งมาได้` แม้ตัวเลขถูกต้อง แก้โดยส่ง array ตรงๆ
  และอัปเดต `tests/test_simulator_web.py` ให้ตรวจ shape นั้น แล้ว restart server
  และรัน B4 ใหม่จน SVG แสดง 2 อัน (PASS)

### ข้อจำกัด / สิ่งที่ยังไม่ทำ

- ไม่มี Starter Kit หรือโมเดลทรานซิสเตอร์จากอาจารย์ → ใช้ generic `QNPN` ตามที่ระบุข้างบน
  ผลจึงไม่ควรเทียบหลักกับผล Analytical `VBE=0.7 V` แบบ constant-VBE ของ Lab 03
- Scope Lab 04 v1 เฉพาะ CE Voltage-Divider; ยังไม่มี circuit editor, emitter bypass,
  FET, หรือ AC ของทุก bias mode
- ใช้ `git.exe` ที่มาพร้อม GitHub Desktop (ไม่ได้ติดตั้ง Git แยก) ในการ init/commit/push
  ไปยัง `https://github.com/piyarat06/BJT-DC-Bias-Web-App` — commit SHA ตามท้ายบันทึกนี้
- `tools/ngspice/` และ `.venv/` ถูก ignore ไม่ได้ commit ไบนารี/virtualenv ลง repo
