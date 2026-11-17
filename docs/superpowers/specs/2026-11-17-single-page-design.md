# Design Note — รวม 3 วงจรเป็นหน้าเดียว (Single-Page Layout)

วันที่: 17 พฤศจิกายน 2569 · วิชา ENG29 2121 · สถานะ: รออนุมัติจากเจ้าของงาน

## Intent / เป้าหมาย

เปลี่ยน UI จาก 3 หน้า (`/`, `/fixed`, `/emitter`) เป็น **หน้าเดียว `/`** ที่มีทั้ง
Voltage-Divider, Fixed และ Emitter Bias อยู่ในหน้าเดียวกัน โดยยังไม่ใช้ JavaScript
และยังคำนวณด้วย solver เดิมทุกประการ

## Goals

- `/` เป็นหน้าเดียวที่มี 3 ส่วนแบบ `<details>` พับได้: Voltage-Divider / Fixed / Emitter
- แต่ละส่วนมีฟอร์มของตัวเอง + ปุ่ม Calculate + ตารางผลของวงจรนั้น
- หลังกด Calculate ให้เปิด (`open`) เฉพาะส่วนที่เพิ่งส่ง และแสดงผล/error ใต้ส่วนนั้น
- URL เก่า `/fixed`, `/emitter` ยังใช้ได้ → redirect ไป `/?circuit=fixed` /
  `/?circuit=emitter` เพื่อไม่ให้ลิงก์หรือ bookmarks เดิมเสีย
- โค้ด/ผลลัพธ์/ข้อความ error-warning เดิมยังเหมือนเดิม รวมถึงการค้างค่าที่กรอกหลัง error

## Non-goals / Anti-goals

- ไม่เพิ่ม JavaScript, dropdown แบบไดนามิก หรือการสลับฟิลด์แบบทันที
- ไม่เปลี่ยนสมการ, validation, region, cutoff/saturation warning หรือค่าอ้างอิง
  (1.230 / 2.404 / 1.979 mA)
- ไม่เพิ่ม AC/small-signal/transient/SPICE/FET/วงจรอื่น
- ไม่คำนวณทั้ง 3 วงจรพร้อมกัน — กด Calculate ส่วนไหนได้ผลส่วนนั้น

## Design รายละเอียด

### Layout (templates/index.html)

```
<main class="card">
  <h1>BJT DC Bias Calculator</h1>
  <details open?>  ← divider
    <summary>Voltage-Divider Bias</summary>
    [error เฉพาะ divider]
    <form action="/calculate"> ... 7 ช่อง ... </form>
    [results เฉพาะ divider]
  </details>
  <details open?>  ← fixed
    <summary>Fixed Bias</summary>
    [error เฉพาะ fixed]
    <form action="/calculate-fixed"> ... 5 ช่อง ... </form>
    [results เฉพาะ fixed]
  </details>
  <details open?>  ← emitter
    <summary>Emitter Bias</summary>
    [error เฉพาะ emitter]
    <form action="/calculate-emitter"> ... 6 ช่อง ... </form>
    [results เฉพาะ emitter]
  </details>
  <footer> สมการอ้างอิงของทั้ง 3 วงจร </footer>
</main>
```

- `<details>` ได้ `open` เฉพาะเมื่อ `circuit` ตรงกับส่วนนั้น
- ใช้ `_results.html` ร่วมทุกส่วน (ไม่ต้องแก้ partial นี้)
- ลบ `templates/fixed.html`, `templates/emitter.html`, `templates/_nav.html`
  (ไม่มีหน้า/แถบลิงก์แยกแล้ว)
- CSS: แทนที่ `.nav` ด้วย `.circuit` (ระยะห่างระหว่างส่วน, สไตล์ `<summary>`)

### Routes (app.py)

| Route | พฤติกรรมใหม่ |
|---|---|
| `GET /` | render `index.html` โดย `circuit = request.args.get("circuit", "divider")` |
| `GET /fixed` | `redirect("/?circuit=fixed")` (302) |
| `GET /emitter` | `redirect("/?circuit=emitter")` (302) |
| `POST /calculate` | คำนวณ divider เหมือนเดิม → render `index.html` พร้อม `circuit="divider"`, `result`, `entered` |
| `POST /calculate-fixed` | เหมือนเดิม → render `index.html` พร้อม `circuit="fixed"` |
| `POST /calculate-emitter` | เหมือนเดิม → render `index.html` พร้อม `circuit="emitter"` |

### State ส่งเข้า template

- `circuit`: `"divider" | "fixed" | "emitter"` — ใช้เปิด `<details>` และเลือกว่าส่วนไหนแสดงผล
- `result`, `error`, `entered`: มีค่าเฉพาะ circuit ที่เพิ่ง submit
  ส่วนอื่นใช้ `defaults` และไม่แสดง result/error
- ฟอร์มแต่ละส่วนใช้ `entered.get('field', defaults.field) if entered is defined else defaults.field`
  เหมือนวิธีที่แก้ไว้ใน commit `35721ed`

### ไฟล์ที่เปลี่ยน

- Modify: `app.py`, `templates/index.html`, `static/style.css`,
  `tests/test_web.py`, `README.md`, `docs/design-note.md`,
  `docs/validation.md`, `docs/reflection.md`
- Delete: `templates/fixed.html`, `templates/emitter.html`, `templates/_nav.html`
- ไม่เปลี่ยน: `dc_bias.py`, `templates/_results.html`

### Tests

- แทนที่ `test_nav_links_on_all_pages` ด้วย test ที่ `/` มี `<summary>` 3 อัน,
  มี form action ครบ 3 ตัว และมีช่อง `vcc/r1/r2/rb/rc/re/beta/vbe`
- GET `/fixed`, `/emitter` → 302 พร้อม `Location` ไป `/?circuit=...`
- POST ทั้ง 3 route → 200, ตัวเลขอ้างอิงถูกต้อง, `<details>` ของ circuit นั้นมี `open`
- tests เดิมเรื่อง validation/inf/NaN/cutoff/saturation/ค้างค่าหลัง error ยังผ่านหมด

## สิ่งที่เหลือให้ขั้น Build

เขียน plan แยก task (TDD) → รันชุด tests เต็ม → HTTP smoke test →
อัปเดต docs → commit local แล้วให้เจ้าของงาน push ผ่าน GitHub Desktop
