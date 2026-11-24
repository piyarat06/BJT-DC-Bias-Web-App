# BJT Bias & CE Amplifier Simulator — ENG29 2121 Lab 02 + Lab 04

Flask Web App ที่ต่อยอดจาก **Lab 02 (BJT DC Bias)** ไปเป็น **Lab 04 · BJT CE Amplifier Simulator v1**

- หน้าเดียว `/` มี **3 ส่วนพับได้** สำหรับ DC Bias แบบ Analytical เดิม
  (Voltage-Divider / Fixed / Emitter) — **ยังทำงานเหมือนเดิม 100%**
- เพิ่มส่วน **CE Amplifier Simulator** ที่รัน **ngspice จริง** 3 โหมด:
  `.op` (DC), `.ac` (Bode gain/phase), `.tran` (Vin/Vout ตามเวลา)
- ผลที่แสดงมีป้ายที่มาชัดเจน: **SPICE results** แยกจาก **Analytical reference**
  และแสดง engine/model/netlist/log ประกอบทุกครั้ง ไม่มีกราฟหรือตัวเลขฮาร์ดโคด

## สิ่งที่ใช้ / ไม่ได้ใช้

ใช้: Flask + Jinja, Python `subprocess`, ngspice 47 (exe แบบ console), SVG ที่วาดจาก
ข้อมูลที่ ngspice ส่งออกจริง (ไม่มี chart library เพิ่มเติม)

ไม่ได้ใช้ (และไม่แอบอ้าง): Starter Kit จากอาจารย์ (ไม่มีไฟล์แนบ), โมเดลทรานซิสเตอร์
เฉพาะรุ่นจากใบงาน, Impeccable skill, Playwright MCP — ดู `docs/validation.md` สำหรับ
สถานะที่ตรวจจริง/ไม่ได้ตรวจ

## โครงสร้างไฟล์

```
BJT-DC-Bias-Web-App/
├── app.py                  # Flask routes: / , 3 × /calculate* , /simulate , redirect /fixed /emitter
├── dc_bias.py              # Lab 03 engineering: solve/solve_fixed/solve_emitter (ไม่เปลี่ยนสมการ)
├── spice_engine.py         # Lab 04: validate → netlist → subprocess ngspice → parse raw → results+charts
├── templates/
│   ├── index.html          # 3 <details> ของ Lab 03 + <section> simulator ของ Lab 04
│   └── _results.html       # ตารางผล Analytical (ใช้ร่วม 3 ส่วนเดิม)
├── static/
│   ├── style.css           # styling เดิม + simulator/chips/charts
│   └── app.js              # วาด SVG จาก JSON ที่ server ส่งมา (ไม่คำนวณฟิสิกส์)
├── tests/
│   ├── test_dc_bias.py     # 17 tests (Lab 03)
│   ├── test_web.py         # 23 tests (Lab 03)
│   ├── test_spice_engine.py# validation/netlist/parser + real ngspice integration
│   └── test_simulator_web.py# /simulate route, error state, provenance, chart data
├── requirements.txt        # flask>=3.0 (ngspice เป็นโปรแกรมภายนอก ไม่ใช่ pip package)
├── AGENTS.md               # ข้อตกลงสำหรับ AI coding agent (อัปเดตเป็น Lab 04)
└── docs/
    ├── design-note.md, validation.md, reflection.md
    └── superpowers/        # plan/spec เดิมของ Lab 03
```

## ติดตั้งและรัน (Windows — ใช้ `py`)

> เครื่องที่ `python` ถูก Microsoft Store alias ยึดไว้ ให้ใช้ `py` เพื่อสร้าง venv
> แล้วใช้ `.venv\Scripts\python.exe` รันคำสั่งต่อไปนี้จาก root ของ repository

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app run --host 127.0.0.1 --port 5000
```

เปิด **http://127.0.0.1:5000/**

### ngspice (external engine)

โค้ดค้นหา engine ตามลำดับ:

1. environment variable `NGSPICE_EXECUTABLE` (ถ้าตั้งแต่ path ผิดจะแจ้ง error ทันที)
2. `tools/ngspice/Spice64/bin/ngspice_con.exe` ( portable copy — ใช้เวอร์ชัน 47
   ดาวน์โหลดจาก <https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/> )
3. `ngspice_con` / `ngspice` จาก `PATH`

`tools/ngspice/` ถูกกันไว้ใน `.gitignore` (ไม่ commit ไบนารี) — บนเครื่องอื่นให้ติดตั้ง
ngspice แล้วเติมลง `PATH` หรือตั้ง `NGSPICE_EXECUTABLE`

## ใช้งาน

### DC Bias เดิม (Lab 03)

กดหัวข้อ Voltage-Divider / Fixed / Emitter แล้วกด **Calculate DC Bias** ผลและ region
แสดงใต้ส่วนที่กดเหมือนเดิม `/fixed` และ `/emitter` ยัง redirect ไป query param เดิม

### CE Amplifier Simulator (Lab 04)

เลื่อนลงไปส่วน **CE Amplifier Simulator** เลือก `DC · .op` / `AC · .ac` /
`Transient · .tran` กรอกค่าวงจรและแหล่งสัญญาณแล้วกด **Run Simulation**

| ฟอร์ม | Default | หน่วย |
|---|---|---|
| VCC, R1, R2, RC, RE, RL | 12, 100, 22, 2.2, 1, 10 | V, kΩ |
| CIN, COUT | 10, 10 | µF |
| Amplitude (Vin peak), Frequency | 0.01, 1000 | V peak, Hz |

ผลที่แสดง:

- **DC**: VB/VE/VC/VCE, IB/IC/IE, `i(vcc)` + region — node voltages อ่านจาก raw file
  ส่วนกระแสอนุมานด้วยกฎของโอห์ม (มีป้าย `Derived from SPICE node voltages`)
- **AC**: gain `|Vout/Vin|`, phase (องศา), fL/fH ที่จุด −3 dB, reference point
  (`Vin = n_in` ก่อน Cin, `Vout = n_out` หลัง Cout) + กราฟ Bode 2 แผน
- **Transient**: Vin/Vout peak, gain, ความสัมพันธ์เฟส (inverted), กราฟเวลา (ms) vs
  แรงดัน (mV) — สัญญาณเปลี่ยนตาม amplitude/frequency ที่ป้อน
- ทุกโหมด: status, engine version, model, netlist ที่ใช้รันจริง, ท้าย ngspice log

ข้อผิดพลาด (engine ไม่พบ, input ผิด, run fail, timeout, raw ว่าง) → แสดง error
**และไม่มีการแสดงผล/กราฟจากรอบเก่า**

## โมเดล BJT ที่ใช้ (สำคัญ)

ไม่มี Starter Kit จากอาจารย์ จึงใช้โมเดลอ้างอิงที่ระบุพารามิเตอร์ไว้ใน netlist ทุกครั้ง:

```
.MODEL QNPN NPN(IS=1e-14 BF=100 VAF=100 CJE=25p CJC=8p TF=0.4n)
```

BF=100 ใกล้เคียง β=100 ของชุดข้อมูล Lab 03 แต่ **ไม่ใช่แบบจำลอง VBE คงที่**
จึงไม่บังคับให้ตัวเลขเท่ากันทุกหลัก ผล SPICE กับผล Analytical ต้องอ่านแยกกันเสมอ

## ตัวเลขจากการรันจริงในเครื่องนี้ (ngspice 47, ค่า default)

| โหมด | ผล |
|---|---|
| DC `.op` | VB 1.949 V, VE 1.289 V, VC 9.189 V, VCE 7.900 V, IB 11.913 µA, IC 1.278 mA, `i(vcc)` 1.378 mA |
| AC `.ac` | Gain @1 kHz 1.75 V/V (4.86 dB), phase −179.9°, fL 2.00 Hz, fH 70.79 MHz |
| Transient `.tran` | Vin peak 10.00 mV, Vout peak 17.49 mV, gain 1.75 V/V, inverted, หน้าต่าง 5 ms |

ตัวเลข Lab 03 (Analytical) สำหรับเทียบ: VTH 2.164 V, RTH 18.033 kΩ,
IB 12.299 µA, IC 1.230 mA, IE 1.242 mA, VE 1.242 V, VB 1.942 V,
VC 9.294 V, VCE 8.052 V

## แท็ปหลักฐานแคปส่งอาจารย์ (B2–B8)

เปิด `http://127.0.0.1:5000/acceptance` แล้วเลือกข้อ หรือเปิดตรงได้เลย:

- `/acceptance/b2` DC `.op`
- `/acceptance/b3` เปลี่ยน RE 1→2 kΩ
- `/acceptance/b4` AC Bode gain/phase
- `/acceptance/b5` Transient 10 mV / 1 kHz
- `/acceptance/b6` Transient 2 รอบ (เปลี่ยน amplitude และ frequency) ในแท็ปเดียว
- `/acceptance/b7` input ผิด (RE=0) → error ไม่มีกราฟ
- `/acceptance/b8` ผล AC เดียวกันแสดงทั้ง desktop และกรอบ 390 CSS px

ทุก URL รัน ngspice ใหม่เมื่อเปิด และแสดง input/expected/ผล/netlist/log แยกตามข้อ
ภาพแคปอยู่ใน `docs/screenshots/B2-dc.png` … `B8-ui.png` (รายละเอียดใน `docs/validation.md` ข้อ 8)

## Automated Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

ผลที่คาดหวัง: **Ran 79 tests ... OK**
(17 dc_bias + 23 web เดิม + 20 spice_engine + 9 simulator_web + 10 acceptance_web)
ถ้าไม่มี ngspice การรันจริง 5–6 ตัวจะถูก `skip` อัตโนมัติ (ไม่ใช่ FAIL)

## ความปลอดภัย / ข้อควรระวัง

- ใช้ Flask development server เฉพาะเครื่องตัวเอง ห้ามเปิดสู่สาธารณะ
- `subprocess.run([...], shell=False)` + `timeout=30` + temp dir ต่อรอบ
- ตรวจ input ก่อนสร้าง netlist เสมอ ไม่มีข้อความจากฟอร์มเข้า command โดยตรง
- ห้าม commit `.venv/`, `__pycache__/`, `.env`, `tools/ngspice/`, ไฟล์ 7z หรือ run ชั่วคราว
