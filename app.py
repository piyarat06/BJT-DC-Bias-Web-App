"""Flask application: BJT DC Bias Web App (ENG29 2121 Lab 02).

Web layer only — every engineering equation lives in dc_bias.py.
Form units: voltages in V, resistances in kΩ, beta unitless.
"""

from flask import Flask, render_template, request

from dc_bias import solve

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

LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

FORM_FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")


def parse_form(form):
    """Convert every form field to float (form units, kΩ not yet converted).

    Raises ValueError with a Thai message when a field is missing,
    empty, or not a number.
    """
    values = {}
    for name in FORM_FIELDS:
        raw = (form.get(name) or "").strip()
        try:
            values[name] = float(raw)
        except ValueError:
            raise ValueError(f"{LABELS[name]} ต้องเป็นตัวเลข เช่น 12")
    return values


@app.route("/")
def index():
    return render_template("index.html", defaults=DEFAULTS)


@app.route("/calculate", methods=["POST"])
def calculate():
    entered = {name: (request.form.get(name) or "") for name in FORM_FIELDS}
    try:
        values = parse_form(request.form)
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
            "index.html", defaults=DEFAULTS, error=str(exc), entered=entered
        )
    return render_template("index.html", defaults=DEFAULTS, result=result, entered=entered)


if __name__ == "__main__":
    app.run(debug=True)
