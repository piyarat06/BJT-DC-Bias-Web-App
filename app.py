"""Flask application: BJT Bias + CE Amplifier Simulator (ENG29 2121 Lab 02 → 04).

Web layer only — analytical equations live in dc_bias.py, ngspice work in spice_engine.py.
Form units: voltages in V, resistances in kΩ, beta unitless.

One page at / holds all three circuits as collapsible sections:
  /  → Voltage-Divider (POST /calculate), Fixed (POST /calculate-fixed),
       Emitter (POST /calculate-emitter)
  /fixed and /emitter redirect to /?circuit=... for old bookmarks.
Lab 04 adds POST /simulate for real ngspice .op/.ac/.tran runs.
"""

from flask import Flask, abort, redirect, render_template, request

from dc_bias import solve, solve_emitter, solve_fixed
from spice_engine import (
    MODEL_SUMMARY,
    MODES as SIM_MODES,
    SpiceError,
    normalize_params,
    resolve_engine,
    run_simulation,
)

app = Flask(__name__)

# Default values = the lab's reference dataset (form units: V, kΩ)
DEFAULTS = {
    "vcc": 12.0,
    "r1": 100.0,
    "r2": 22.0,
    "rc": 2.2,
    "re": 1.0,
    "beta": 100.0,
    "vbe": 0.70,
}

# The two extra circuits are designed to stay comfortably forward-active.
FIXED_DEFAULTS = {
    "vcc": 12.0,
    "rb": 470.0,
    "rc": 2.2,
    "beta": 100.0,
    "vbe": 0.70,
}
EMITTER_DEFAULTS = {**FIXED_DEFAULTS, "re": 1.0}

# All form fields on the single page read from one defaults map.
ALL_DEFAULTS = {**DEFAULTS, **FIXED_DEFAULTS}

LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rb": "RB",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

FORM_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")
FORM_FIELDS_FIXED = ("vcc", "rb", "rc", "beta", "vbe")
FORM_FIELDS_EMITTER = ("vcc", "rb", "rc", "re", "beta", "vbe")

CIRCUITS = ("divider", "fixed", "emitter")

# Lab 04 simulator form (values shown in the browser; units: V, kΩ, µF, Hz).
SIM_DEFAULTS = {
    "sim_vcc": 12.0, "sim_r1": 100.0, "sim_r2": 22.0, "sim_rc": 2.2,
    "sim_re": 1.0, "sim_rl": 10.0, "sim_cin": 10.0, "sim_cout": 10.0,
    "sim_amplitude": 0.01, "sim_frequency": 1000.0,
}
SIM_FIELDS = tuple(SIM_DEFAULTS)
SIM_PARAM_DEFAULTS = {name[4:]: value for name, value in SIM_DEFAULTS.items()}

# One-tab-per-case evidence pages for B2–B8. Inputs/expected text are metadata;
# every number in the rendered result still comes from a fresh ngspice run.
COMMON_PARAMS = [
    ("VCC", "12 V"), ("R1", "100 kΩ"), ("R2", "22 kΩ"), ("RC", "2.2 kΩ"),
    ("RE", "1 kΩ"), ("RL", "10 kΩ"), ("CIN / COUT", "10 µF / 10 µF"),
]
SOURCE_1KHZ = [("Vin amplitude", "10 mV peak"), ("Frequency", "1 kHz")]

ACCEPTANCE_CASES = {
    "b2": {
        "title": "DC Operating Point (.op)",
        "subtitle": "รัน .op ด้วยชุดค่าอ้างอิง Lab 04 และแสดงผลจาก ngspice โดยตรง",
        "runs": [{
            "label": "Reference DC operating point",
            "mode": "dc",
            "overrides": {},
            "inputs": COMMON_PARAMS,
            "expected": "VB / VE / VC / VCE / IC เป็นผลจาก SPICE รอบนี้ พร้อม model และ engine",
        }],
    },
    "b3": {
        "title": "เปลี่ยน RE → Operating Point ต้องเปลี่ยน",
        "subtitle": "เปลี่ยนเฉพาะ RE จาก 1 kΩ เป็น 2 kΩ แล้วรัน .op ซ้ำ",
        "runs": [{
            "label": "RE=1 kΩ → 2 kΩ",
            "mode": "dc",
            "overrides": {"re": 2.0},
            "inputs": COMMON_PARAMS[:4] + [("RE", "2 kΩ (เปลี่ยนจาก 1 kΩ)")]
            + COMMON_PARAMS[5:],
            "expected": "Netlist ต้องเป็น RE n_e 0 2k และ IC/VCE ต้องเปลี่ยนจากรอบอ้างอิง",
        }],
    },
    "b4": {
        "title": "AC Sweep · Bode Gain / Phase",
        "subtitle": "สแกน 1 Hz–1 GHz แล้ววาดกราฟจากข้อมูล complex ที่ ngspice ส่งออก",
        "runs": [{
            "label": ".ac 1 Hz → 1 GHz",
            "mode": "ac",
            "overrides": {},
            "inputs": COMMON_PARAMS + SOURCE_1KHZ,
            "expected": "แกน Frequency (Hz), gain V/V, phase องศา และค่า @1 kHz จากรันจริง",
        }],
    },
    "b5": {
        "title": "Transient · Vin / Vout ตามเวลา",
        "subtitle": "รัน .tran ที่ 10 mV peak / 1 kHz แล้วดูสัญญาณกลับเฟส",
        "runs": [{
            "label": ".tran @ 10 mV, 1 kHz",
            "mode": "tran",
            "overrides": {},
            "inputs": COMMON_PARAMS + SOURCE_1KHZ,
            "expected": "กราฟ Vin/Vout มีหน่วย mV–ms และความสัมพันธ์ inverted",
        }],
    },
    "b6": {
        "title": "เปลี่ยนแหล่งสัญญาณ → Waveform ต้องเปลี่ยน",
        "subtitle": "รัน .tran สองรอบ: เปลี่ยน amplitude ก่อน แล้วเปลี่ยน frequency",
        "runs": [
            {
                "label": "เปลี่ยน amplitude 10 mV → 30 mV",
                "mode": "tran",
                "overrides": {"amplitude": 0.03},
                "inputs": COMMON_PARAMS + [
                    ("Vin amplitude", "30 mV peak (เปลี่ยนจาก 10 mV)"),
                    ("Frequency", "1 kHz (คงเดิม)"),
                ],
                "expected": "SIN(0 0.03 1000 0 0) และ Vout peak ต้องเพิ่มตาม amplitude",
            },
            {
                "label": "เปลี่ยน frequency 1 kHz → 5 kHz",
                "mode": "tran",
                "overrides": {"frequency": 5000.0},
                "inputs": COMMON_PARAMS + [
                    ("Vin amplitude", "10 mV peak (กลับค่าเดิม)"),
                    ("Frequency", "5 kHz (เปลี่ยนจาก 1 kHz)"),
                ],
                "expected": "SIN(0 0.01 5000 0 0) และหน้าต่างเวลาต้องเหลือ 1.000 ms",
            },
        ],
    },
    "b7": {
        "title": "Input ผิด → แจ้ง error ไม่โชว์ผลเก่า",
        "subtitle": "ใส่ RE=0 แล้วกดรัน ต้องถูกปฏิเสธก่อนเรียก ngspice",
        "runs": [{
            "label": "RE = 0 kΩ (invalid)",
            "invalid": {"re": 0.0},
            "inputs": COMMON_PARAMS[:4] + [("RE", "0 kΩ (invalid)")]
            + COMMON_PARAMS[5:] + SOURCE_1KHZ,
            "expected": "Simulation status: error, ข้อความ RE ต้องมากกว่า 0, ไม่มีกราฟ/ตารางผล",
        }],
    },
    "b8": {
        "title": "UI อ่านง่ายบน Desktop และความกว้างมือถือ",
        "subtitle": "ผล AC ชุดเดียวกัน แสดงในคอลัมน์เต็มจอและกรอบ 390 CSS px",
        "views": [("desktop", "Desktop · full width"), ("mobile", "Mobile · 390 CSS px")],
        "runs": [{
            "label": ".ac results แสดงในสองความกว้าง",
            "mode": "ac",
            "overrides": {},
            "inputs": COMMON_PARAMS + SOURCE_1KHZ,
            "expected": "กราฟ/หน่วย/ปุ่มอ่านได้ ไม่มี horizontal overflow ในกรอบ 390 px",
        }],
    },
}


def _acceptance_runs(case_id):
    """Build real simulation results (or a real validation error) for one case."""
    case = ACCEPTANCE_CASES[case_id]
    runs = []
    for config in case["runs"]:
        run = {key: config[key] for key in ("label", "inputs", "expected")}
        try:
            params = normalize_params({**SIM_PARAM_DEFAULTS, **config.get("overrides", {}),
                                       **config.get("invalid", {})})
        except SpiceError as exc:
            run["error"] = str(exc)
        else:
            run["sim"] = run_simulation(config["mode"], params)
        runs.append(run)
    return runs


@app.context_processor
def inject_simulator_context():
    """Make simulator defaults/status available to every render_template call."""
    return {
        "sim_defaults": SIM_DEFAULTS,
        "sim_engine": resolve_engine(),
        "sim_model": MODEL_SUMMARY,
        "sim_modes": SIM_MODES,
    }


def _engine_params(form):
    """Strip the sim_ prefix, then validate in the engineering adapter."""
    raw = {name[4:]: (form.get(name) or "") for name in SIM_FIELDS}
    return normalize_params(raw)


def parse_form(form, fields):
    """Convert the named form fields to float (form units, kΩ not yet converted).

    Raises ValueError with a Thai message when a field is missing,
    empty, or not a number.
    """
    values = {}
    for name in fields:
        raw = (form.get(name) or "").strip()
        try:
            values[name] = float(raw)
        except ValueError:
            raise ValueError(f"{LABELS[name]} ต้องเป็นตัวเลข เช่น 12")
    return values


@app.route("/")
def index():
    circuit = request.args.get("circuit", "divider")
    if circuit not in CIRCUITS:
        circuit = "divider"
    return render_template("index.html", defaults=ALL_DEFAULTS, circuit=circuit)


@app.route("/calculate", methods=["POST"])
def calculate():
    entered = {name: (request.form.get(name) or "") for name in FORM_FIELDS}
    try:
        values = parse_form(request.form, FORM_FIELDS)
        result = solve(
            vcc=values["vcc"],
            r1=values["r1"] * 1000.0,   # kΩ -> Ω
            r2=values["r2"] * 1000.0,
            rc=values["rc"] * 1000.0,
            re=values["re"] * 1000.0,
            beta=values["beta"],
            vbe=values["vbe"],
        )
    except ValueError as exc:
        return render_template(
            "index.html", defaults=ALL_DEFAULTS, circuit="divider",
            error=str(exc), entered=entered
        )
    return render_template(
        "index.html", defaults=ALL_DEFAULTS, circuit="divider",
        result=result, entered=entered
    )


@app.route("/fixed")
def fixed_page():
    return redirect("/?circuit=fixed")


@app.route("/calculate-fixed", methods=["POST"])
def calculate_fixed():
    entered = {name: (request.form.get(name) or "") for name in FORM_FIELDS_FIXED}
    try:
        values = parse_form(request.form, FORM_FIELDS_FIXED)
        result = solve_fixed(
            vcc=values["vcc"],
            rb=values["rb"] * 1000.0,   # kΩ -> Ω
            rc=values["rc"] * 1000.0,
            beta=values["beta"],
            vbe=values["vbe"],
        )
    except ValueError as exc:
        return render_template(
            "index.html", defaults=ALL_DEFAULTS, circuit="fixed",
            error=str(exc), entered=entered
        )
    return render_template(
        "index.html", defaults=ALL_DEFAULTS, circuit="fixed",
        result=result, entered=entered
    )


@app.route("/emitter")
def emitter_page():
    return redirect("/?circuit=emitter")


@app.route("/calculate-emitter", methods=["POST"])
def calculate_emitter():
    entered = {name: (request.form.get(name) or "") for name in FORM_FIELDS_EMITTER}
    try:
        values = parse_form(request.form, FORM_FIELDS_EMITTER)
        result = solve_emitter(
            vcc=values["vcc"],
            rb=values["rb"] * 1000.0,   # kΩ -> Ω
            rc=values["rc"] * 1000.0,
            re=values["re"] * 1000.0,
            beta=values["beta"],
            vbe=values["vbe"],
        )
    except ValueError as exc:
        return render_template(
            "index.html", defaults=ALL_DEFAULTS, circuit="emitter",
            error=str(exc), entered=entered
        )
    return render_template(
        "index.html", defaults=ALL_DEFAULTS, circuit="emitter",
        result=result, entered=entered
    )


@app.route("/simulate", methods=["POST"])
def simulate():
    """Run one real ngspice analysis and render only that run's results."""
    entered = {name: (request.form.get(name) or "") for name in SIM_FIELDS}
    mode = request.form.get("mode", "dc")
    if mode not in SIM_MODES:
        mode = "dc"
    try:
        params = _engine_params(request.form)
        simulation = run_simulation(mode, params)
    except SpiceError as exc:
        return render_template(
            "index.html", defaults=ALL_DEFAULTS, circuit="simulator",
            sim_entered=entered, sim_mode=mode, sim_error=str(exc),
        )
    return render_template(
        "index.html", defaults=ALL_DEFAULTS, circuit="simulator",
        sim_entered=entered, sim_mode=mode, sim=simulation,
    )


@app.route("/acceptance")
def acceptance_index():
    """Index of screenshot-ready Lab 04 evidence tabs."""
    return render_template(
        "acceptance.html", case_id=None, case=None, runs=[],
        cases=ACCEPTANCE_CASES,
    )


@app.route("/acceptance/<case_id>")
def acceptance_case(case_id):
    """Open one real run (or one real validation error) for B2–B8."""
    case_id = case_id.lower()
    if case_id not in ACCEPTANCE_CASES:
        abort(404)
    return render_template(
        "acceptance.html",
        case_id=case_id,
        case=ACCEPTANCE_CASES[case_id],
        runs=_acceptance_runs(case_id),
        cases=ACCEPTANCE_CASES,
    )


if __name__ == "__main__":
    app.run(debug=True)
