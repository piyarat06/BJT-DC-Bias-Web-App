"""Lab 04 adapter: generate a CE amplifier netlist, run ngspice, parse results.

Pure engineering/process layer — no Flask, no HTML. All numerical inputs use
the form's friendly units (V, kΩ, µF, V peak, Hz); the netlist converts them
to the SPICE suffixes k/u. Every number shown to the user comes from the
ngspice run: node voltages are read from the raw file, and currents are
derived from those voltages with Ohm's law (explicitly labelled as derived).

External process rules followed here:
  * subprocess.run([...], shell=False) with an argument list
  * explicit timeout and a fresh TemporaryDirectory per run
  * validation before any text reaches the netlist
  * failure/empty output/timeout never return a success result
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

MODES = ("dc", "ac", "tran")
MODEL_NAME = "QNPN"
MODEL_CARD = ".MODEL QNPN NPN(IS=1e-14 BF=100 VAF=100 CJE=25p CJC=8p TF=0.4n)"
MODEL_SUMMARY = "QNPN · IS=1e-14, BF=100, VAF=100, CJE=25p, CJC=8p, TF=0.4n"

# Form units: V, kΩ, µF, V peak, Hz.
DEFAULT_PARAMS = {
    "vcc": 12.0, "r1": 100.0, "r2": 22.0, "rc": 2.2, "re": 1.0,
    "rl": 10.0, "cin": 10.0, "cout": 10.0,
    "amplitude": 0.01, "frequency": 1000.0,
}

FIELD_LABELS = {
    "vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC", "re": "RE",
    "rl": "RL", "cin": "CIN", "cout": "COUT",
    "amplitude": "Amplitude", "frequency": "Frequency",
}
POSITIVE_FIELDS = ("vcc", "r1", "r2", "rc", "re", "rl", "cin", "cout", "amplitude")

AC_F_START_HZ = 1.0
AC_F_STOP_HZ = 1.0e9
AC_POINTS_PER_DECADE = 20
TIMEOUT_SECONDS = 30


class SpiceError(Exception):
    """Validation, engine or parsing problem that must be shown as an error."""


def resolve_engine() -> str | None:
    """Locate the console ngspice executable.

    NGSPICE_EXECUTABLE is an explicit override: if set but invalid, return
    None instead of silently falling back to another engine. The project-local
    portable copy is checked before PATH so results are reproducible.
    """
    override = os.environ.get("NGSPICE_EXECUTABLE", "").strip()
    if override:
        path = Path(override)
        return str(path) if path.is_file() else None

    root = Path(__file__).resolve().parent
    for rel in (
        "tools/ngspice/Spice64/bin/ngspice_con.exe",
        "tools/ngspice/Spice64/bin/ngspice.exe",
    ):
        path = root / rel
        if path.is_file():
            return str(path)
    for name in ("ngspice_con", "ngspice"):
        found = shutil.which(name)
        if found:
            return found
    return None


def normalize_params(raw) -> dict:
    """Parse and validate form values before they can enter a netlist."""
    values = {}
    for key, label in FIELD_LABELS.items():
        text = str(raw.get(key, "") if hasattr(raw, "get") else "").strip()
        try:
            number = float(text)
        except ValueError:
            raise SpiceError(f"{label} ต้องเป็นตัวเลข เช่น 12")
        if not math.isfinite(number):
            raise SpiceError(f"{label} ต้องเป็นจำนวนจำกัด (ห้าม inf หรือ NaN)")
        values[key] = number

    for key in POSITIVE_FIELDS:
        if values[key] <= 0:
            raise SpiceError(f"{FIELD_LABELS[key]} ต้องมากกว่า 0")
    if values["amplitude"] > 1.0:
        raise SpiceError("Amplitude ต้องไม่เกิน 1 V (แบบจำลองสัญญาณเล็ก)")
    if values["frequency"] < 10.0 or values["frequency"] > 1.0e7:
        raise SpiceError("Frequency ต้องอยู่ระหว่าง 10 Hz ถึง 10 MHz")
    return values


def _num(value: float) -> str:
    return f"{value:.10g}"


def _kilo(value: float) -> str:
    return f"{_num(value)}k"


def _micro(value: float) -> str:
    return f"{_num(value)}u"


def _suffix(value: float) -> str:
    for scale, suffix in ((1e9, "G"), (1e6, "Meg"), (1e3, "k")):
        if abs(value) >= scale and value % scale == 0:
            return f"{_num(value / scale)}{suffix}"
    return _num(value)


def build_netlist(mode: str, params: dict) -> str:
    """Build one analysis per run so the raw file has a single, clear plot."""
    if mode not in MODES:
        raise SpiceError("โหมดการวิเคราะห์ไม่ถูกต้อง")

    p = params
    lines = [
        "* CE voltage-divider amplifier - ENG29 2121 Lab 04 (generated)",
        f"VCC vcc 0 DC {_num(p['vcc'])}",
        f"VIN n_in 0 DC 0 AC {_num(p['amplitude'])} "
        f"SIN(0 {_num(p['amplitude'])} {_num(p['frequency'])} 0 0)",
        f"R1 vcc n_b {_kilo(p['r1'])}",
        f"R2 n_b 0 {_kilo(p['r2'])}",
        f"RC vcc n_c {_kilo(p['rc'])}",
        f"RE n_e 0 {_kilo(p['re'])}",
        "Q1 n_c n_b n_e " + MODEL_NAME,
        f"CIN n_in n_b {_micro(p['cin'])}",
        f"COUT n_c n_out {_micro(p['cout'])}",
        f"RL n_out 0 {_kilo(p['rl'])}",
        MODEL_CARD,
    ]
    if mode == "dc":
        lines.append(".OP")
    elif mode == "ac":
        lines.append(f".AC DEC {AC_POINTS_PER_DECADE} "
                     f"{_suffix(AC_F_START_HZ)} {_suffix(AC_F_STOP_HZ)}")
    else:
        # Five periods, 100 steps per period: informative without a huge file.
        tstep = 1.0 / (p["frequency"] * 100.0)
        tstop = 5.0 / p["frequency"]
        lines.append(f".TRAN {_num(tstep)} {_num(tstop)} 0")
    lines.append(".END")
    return "\n".join(lines) + "\n"


def parse_raw(text: str) -> dict:
    """Parse ngspice's ASCII raw file into named variables and value rows."""
    lines = text.splitlines()

    def header_value(prefix: str) -> str:
        for line in lines:
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
        raise SpiceError("ไฟล์ผลลัพธ์ของ ngspice ไม่มีส่วนหัวที่คาดหวัง")

    try:
        nvars = int(header_value("No. Variables"))
        npoints = int(header_value("No. Points"))
    except ValueError:
        raise SpiceError("ไฟล์ผลลัพธ์ของ ngspice อ่านจำนวนตัวแปร/จุดไม่ได้")

    if "Values:" not in lines:
        raise SpiceError("ไฟล์ผลลัพธ์ของ ngspice ไม่มีข้อมูล Values")
    var_start = lines.index("Variables:") + 1
    value_start = lines.index("Values:") + 1
    variables = []
    for line in lines[var_start:value_start]:
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            variables.append(parts[1].lower())

    points = []
    current = []
    for line in lines[value_start:]:
        tokens = line.replace("\t", " ").split()
        if not tokens:
            continue
        if not current:
            tokens = tokens[1:]  # each point starts with its index
        current.extend(tokens)
        while len(current) >= nvars:
            chunk, current = current[:nvars], current[nvars:]
            row = []
            for token in chunk:
                if "," in token:  # complex result, e.g. "1.0,0.0"
                    real, imag = token.split(",", 1)
                    row.append(complex(float(real), float(imag)))
                else:
                    row.append(float(token))
            points.append(row)

    if len(points) != npoints or len(variables) != nvars:
        raise SpiceError("ข้อมูลจาก ngspice ไม่ครบตามจำนวนจุดที่ประกาศไว้")
    return {"variables": variables, "points": points}


def _index(raw: dict, name: str) -> int:
    try:
        return raw["variables"].index(name.lower())
    except ValueError:
        raise SpiceError(f"ngspice ไม่ได้ส่งออก {name}")


def _number(value) -> float:
    return value.real if isinstance(value, complex) else value


def _engine_version(text: str) -> str | None:
    match = re.search(r"ngspice-(\d+(?:\.\d+)?)", text)
    return match.group(1) if match else None


def _check_run(proc, log_text: str, raw_text: str) -> None:
    if proc.returncode != 0:
        detail = next((line.strip() for line in log_text.splitlines() if "Error" in line), "")
        raise SpiceError(f"ngspice รันไม่สำเร็จ (exit {proc.returncode}) {detail}".strip())
    if "Error on line" in log_text or "Simulation interrupted" in log_text:
        detail = next(line.strip() for line in log_text.splitlines() if "Error" in line)
        raise SpiceError(f"ngspice รันไม่สำเร็จ: {detail}")
    if not raw_text.strip():
        raise SpiceError("ngspice ไม่ได้เขียนไฟล์ผลลัพธ์ (raw file ว่าง)")


def _chart(title: str, x_label: str, y_label: str, name: str, points: list,
           x_scale: str = "linear") -> dict:
    return {
        "title": title,
        "x_label": x_label,
        "y_label": y_label,
        "x_scale": x_scale,
        "series": [{"name": name, "points": points}],
    }


def analyze_dc(raw: dict, params: dict) -> dict:
    """Read node voltages from the .op raw output and derive currents."""
    nodes = {}
    for name in ("v(vcc)", "v(n_b)", "v(n_c)", "v(n_e)", "v(n_out)", "i(vcc)"):
        nodes[name] = _number(raw["points"][0][_index(raw, name)])

    vb = nodes["v(n_b)"]
    ve, vc = nodes["v(n_e)"], nodes["v(n_c)"]
    vcc = params["vcc"]
    vce = vc - ve
    # mA because resistances are entered in kΩ.
    ib = (vcc - vb) / params["r1"] - vb / params["r2"]
    ic = (vcc - vc) / params["rc"]
    ie = ve / params["re"]

    if vb <= ve + 0.3:
        region, warnings = "cutoff", ["Cutoff: แรงดันเบสไม่พอให้ทรานซิสเตอร์นำ"]
    elif vce < 0.2:
        region, warnings = "saturation", ["Saturation: VCE ต่ำกว่า 0.2 V"]
    else:
        region, warnings = "forward_active", []

    summary = [
        {"label": "VB (base voltage)", "value": f"{vb:.3f} V"},
        {"label": "VE (emitter voltage)", "value": f"{ve:.3f} V"},
        {"label": "VC (collector voltage)", "value": f"{vc:.3f} V"},
        {"label": "VCE (collector-emitter)", "value": f"{vce:.3f} V"},
        {"label": "IB (base current)", "value": f"{ib * 1000:.3f} µA"},
        {"label": "IC (collector current)", "value": f"{ic:.3f} mA"},
        {"label": "IE (emitter current)", "value": f"{ie:.3f} mA"},
        {"label": "Supply current i(vcc)", "value": f"{-nodes['i(vcc)'] * 1000:.3f} mA"},
    ]
    notes = [
        "VB/VE/VC และ i(vcc) อ่านจาก node voltage/current ที่ ngspice เขียนใน raw file",
        "Derived from SPICE node voltages: IB/IC/IE อนุมานด้วยกฎของโอห์มจากแรงดันและ R",
        "ค่าชุดนี้เป็นผล SPICE (โมเดล QNPN) ไม่ใช่ผล Analytical จาก dc_bias.py",
    ]
    return {"summary": summary, "charts": [], "region": region,
            "warnings": warnings, "notes": notes, "phase_relation": None}


def analyze_ac(raw: dict, params: dict) -> dict:
    """Compute |Vout/Vin| and phase from the complex AC raw output."""
    fi, vi, vo = (_index(raw, name) for name in ("frequency", "v(n_in)", "v(n_out)"))
    sweep = []
    for point in raw["points"]:
        vin, vout = complex(point[vi]), complex(point[vo])
        if abs(vin) == 0:
            continue
        gain = abs(vout / vin)
        phase = math.degrees(math.atan2(vout.imag, vout.real)
                             - math.atan2(vin.imag, vin.real))
        if phase > 180:
            phase -= 360
        if phase <= -180:
            phase += 360
        sweep.append((_number(point[fi]), gain, phase))

    if not sweep:
        raise SpiceError("ngspice ไม่ได้ส่งข้อมูล AC ที่ใช้คำนวณ gain ได้")
    peak = max(row[1] for row in sweep)
    target = peak / math.sqrt(2.0)
    passing = [row[0] for row in sweep if row[1] >= target]
    f_low, f_high = min(passing), max(passing)
    low_text = (f"{f_low:.2f} Hz" if f_low > sweep[0][0] * 1.001
                else "not determined in sweep range")
    high_text = (f"{f_high / 1e6:.2f} MHz" if f_high < sweep[-1][0] * 0.999
                 else "not determined in sweep range")

    wanted = params["frequency"]
    near = min(sweep, key=lambda row: abs(math.log10(row[0]) - math.log10(wanted)))
    gain_db = 20 * math.log10(near[1]) if near[1] > 0 else -math.inf

    gain_points = [[f, g] for f, g, _ in sweep]
    phase_points = [[f, ph] for f, _, ph in sweep]
    charts = [
        _chart("Bode magnitude", "Frequency (Hz)", "Gain |Vout/Vin| (V/V)",
               "Gain (V/V)", gain_points, "log"),
        _chart("Bode phase", "Frequency (Hz)", "Phase (degree)",
               "Phase (°)", phase_points, "log"),
    ]
    summary = [
        {"label": "Gain @ source frequency", "value": f"{near[1]:.2f} V/V ({gain_db:.2f} dB)"},
        {"label": "Phase @ source frequency", "value": f"{near[2]:.1f} °"},
        {"label": "Midband gain", "value": f"{peak:.2f} V/V"},
        {"label": "fL (-3 dB)", "value": low_text},
        {"label": "fH (-3 dB)", "value": high_text},
        {"label": "Reference point", "value": "Vin = n_in (ก่อน Cin), Vout = n_out (หลัง Cout)"},
    ]
    notes = [
        "Gain และเฟสคำนวณจากค่า complex v(n_out)/v(n_in) ที่ ngspice ส่งออกใน raw file",
        "จุด -3 dB หาจาก gain สูงสุดในช่วง sweep เท่านั้น",
    ]
    return {"summary": summary, "charts": charts, "region": None,
            "warnings": [], "notes": notes, "phase_relation": None}


def analyze_tran(raw: dict, params: dict) -> dict:
    """Summarise the .tran raw output and downsample it for the browser."""
    ti, vi, vo = (_index(raw, name) for name in ("time", "v(n_in)", "v(n_out)"))
    points = raw["points"]
    t_end = _number(points[-1][ti])
    window = 5.0 / params["frequency"]
    start = max(0.0, t_end - window)
    selected = [p for p in points if _number(p[ti]) >= start]

    vin = [_number(p[vi]) * 1000.0 for p in selected]   # mV
    vout = [_number(p[vo]) * 1000.0 for p in selected]
    vin_peak = (max(vin) - min(vin)) / 2.0
    vout_peak = (max(vout) - min(vout)) / 2.0

    mean_in = sum(vin) / len(vin)
    mean_out = sum(vout) / len(vout)
    cov = sum((a - mean_in) * (b - mean_out) for a, b in zip(vin, vout))
    denom = math.sqrt(sum((a - mean_in) ** 2 for a in vin)
                      * sum((b - mean_out) ** 2 for b in vout))
    phase_relation = "inverted" if cov < 0 and denom > 0 else "non-inverted"

    stride = max(1, len(selected) // 600)
    series_in = [[_number(p[ti]) * 1000.0, v] for p, v in zip(selected, vin)][::stride]
    series_out = [[_number(p[ti]) * 1000.0, v] for p, v in zip(selected, vout)][::stride]
    chart = {
        "title": "Input / Output waveforms",
        "x_label": "Time (ms)",
        "y_label": "Voltage (mV)",
        "x_scale": "linear",
        "series": [
            {"name": "Vin", "points": series_in},
            {"name": "Vout", "points": series_out},
        ],
    }
    summary = [
        {"label": "Vin peak", "value": f"{vin_peak:.2f} mV"},
        {"label": "Vout peak", "value": f"{vout_peak:.2f} mV"},
        {"label": "Gain (peak)", "value": f"{vout_peak / vin_peak:.2f} V/V" if vin_peak else "n/a"},
        {"label": "Phase relation", "value": phase_relation},
        {"label": "Window shown", "value": f"{(t_end - start) * 1000.0:.3f} ms (last 5 periods)"},
    ]
    notes = [
        "Vin/Vout อ่านจาก v(n_in)/v(n_out) ใน raw file ของ ngspice .tran",
        "สัญญาณกลับเฟสตรวจจากสหสัมพันธ์ของ Vin/Vout ในหน้าต่าง 5 รอบ(last periods)",
    ]
    return {"summary": summary, "charts": [chart], "region": None,
            "warnings": [], "notes": notes, "phase_relation": phase_relation}


def run_simulation(mode: str, params: dict, engine: str | None = None) -> dict:
    """Execute one real ngspice analysis and return labelled, unit-bearing data."""
    params = normalize_params(params)
    engine = engine or resolve_engine()
    if not engine:
        raise SpiceError(
            "ไม่พบ ngspice — ติดตั้งโปรแกรมหรือตั้งค่า NGSPICE_EXECUTABLE "
            "ก่อนรันการจำลอง (ไม่มีการแสดงกราฟจำลองเมื่อไม่มี Engine)"
        )
    netlist = build_netlist(mode, params)

    with tempfile.TemporaryDirectory(prefix="bjt_spice_") as folder:
        work = Path(folder)
        cir, log, raw = work / "circuit.cir", work / "run.log", work / "run.raw"
        cir.write_text(netlist, encoding="utf-8")
        command = [engine, "-b", "-o", str(log), "-r", str(raw), str(cir)]
        try:
            proc = subprocess.run(
                command, cwd=work, capture_output=True, text=True,
                errors="replace", timeout=TIMEOUT_SECONDS, check=False,
            )
        except FileNotFoundError:
            raise SpiceError("ไม่พบไฟล์ ngspice ตาม path ที่ระบุ")
        except subprocess.TimeoutExpired:
            raise SpiceError(f"ngspice ใช้เวลาเกิน {TIMEOUT_SECONDS} วินาที จึงยุติการรัน")

        log_text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else (proc.stdout + proc.stderr)
        raw_text = raw.read_text(encoding="utf-8", errors="replace") if raw.exists() else ""
        _check_run(proc, log_text, raw_text)
        raw_data = parse_raw(raw_text)
        analysis = {"dc": analyze_dc, "ac": analyze_ac, "tran": analyze_tran}[mode](raw_data, params)

    version = _engine_version(raw_text) or _engine_version(log_text) or "unknown"
    return {
        "status": "success",
        "mode": mode,
        "engine": f"ngspice {version}",
        "model": MODEL_SUMMARY,
        "netlist": netlist,
        "log_excerpt": log_text[-1400:],
        "notes": analysis["notes"],
        "summary": analysis["summary"],
        "charts": analysis["charts"],
        "region": analysis["region"],
        "warnings": analysis["warnings"],
        "phase_relation": analysis["phase_relation"],
    }
