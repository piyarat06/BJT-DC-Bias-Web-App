"""Flask application: BJT DC Bias Web App (ENG29 2121 Lab 02).

Web layer only — every engineering equation lives in dc_bias.py.
Form units: voltages in V, resistances in kΩ, beta unitless.

One page at / holds all three circuits as collapsible sections:
  /  → Voltage-Divider (POST /calculate), Fixed (POST /calculate-fixed),
       Emitter (POST /calculate-emitter)
  /fixed and /emitter redirect to /?circuit=... for old bookmarks.
"""

from flask import Flask, redirect, render_template, request

from dc_bias import solve, solve_emitter, solve_fixed

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


if __name__ == "__main__":
    app.run(debug=True)
