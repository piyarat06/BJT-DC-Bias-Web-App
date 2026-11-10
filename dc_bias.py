"""Engineering module: DC bias analysis for an NPN common-emitter
amplifier with voltage-divider bias, under the forward-active
approximation (constant beta, constant VBE).

Pure engineering logic: stdlib only, SI units in (V, ohm) and out (V, A).
This module knows nothing about HTTP or HTML.
"""

from dataclasses import dataclass, field


@dataclass
class DCBiasResult:
    """DC operating point. All voltages in V, all currents in A."""

    vth: float          # Thevenin voltage of the base divider [V]
    rth: float          # Thevenin resistance of the base divider [ohm]
    ib: float           # base current [A]
    ic: float           # collector current [A]
    ie: float           # emitter current [A]
    ve: float           # emitter voltage [V]
    vb: float           # base voltage [V]
    vc: float           # collector voltage [V]
    vce: float          # collector-emitter voltage [V]
    region: str         # "forward_active" | "cutoff" | "saturation"
    warnings: list = field(default_factory=list)


def _require_positive(name: str, value: float) -> None:
    """Raise ValueError (Thai message) when value <= 0."""
    if value <= 0:
        raise ValueError(f"{name} ต้องมากกว่า 0")


def _validate(vcc, r1, r2, rc, re, beta, vbe) -> None:
    """Check engineering sanity of inputs before computing."""
    _require_positive("VCC", vcc)
    _require_positive("R1", r1)
    _require_positive("R2", r2)
    _require_positive("RC", rc)
    _require_positive("RE", re)
    _require_positive("β", beta)
    if vbe < 0:
        raise ValueError("VBE ต้องไม่ติดลบ")


def solve(vcc, r1, r2, rc, re, beta, vbe) -> DCBiasResult:
    """Compute the DC operating point of a voltage-divider biased
    NPN common-emitter stage.

    Parameters (SI units): vcc [V], r1 r2 rc re [ohm], beta [-], vbe [V].
    Raises ValueError when any input is out of engineering range.
    """
    _validate(vcc, r1, r2, rc, re, beta, vbe)

    # Thevenin equivalent of the base divider
    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    # Forward-active approximation
    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    return DCBiasResult(
        vth=vth, rth=rth, ib=ib, ic=ic, ie=ie,
        ve=ve, vb=vb, vc=vc, vce=vce,
        region="forward_active",
        warnings=[],
    )
