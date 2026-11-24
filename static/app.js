/* Lab 04 — draw plots from the JSON produced by the real ngspice run.
   No physics is computed here: only mapping numbers to SVG coordinates. */
(function () {
  "use strict";

  const COLORS = ["#0c8078", "#c2672e", "#2f6fa8", "#8a5aa8"];
  const SVG_NS = "http://www.w3.org/2000/svg";

  function el(name, attrs, text) {
    const node = document.createElementNS(SVG_NS, name);
    Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function tickLabel(value, scale) {
    const abs = Math.abs(value);
    if (abs >= 1e9) return (value / 1e9).toPrecision(3) + "G";
    if (abs >= 1e6) return (value / 1e6).toPrecision(3) + "M";
    if (abs >= 1e3) return (value / 1e3).toPrecision(3) + "k";
    if (scale === "log") return Number(value.toPrecision(3)).toString();
    if (abs !== 0 && abs < 0.01) return value.toExponential(1);
    return Number(value.toPrecision(3)).toString();
  }

  function makeScale(values, log, range) {
    const clean = values.filter((v) => Number.isFinite(v) && (!log || v > 0));
    let min = Math.min(...clean);
    let max = Math.max(...clean);
    if (!Number.isFinite(min) || !Number.isFinite(max)) { min = 0; max = 1; }
    if (min === max) { const pad = Math.abs(min) * 0.1 || 1; min -= pad; max += pad; }
    const lo = log ? Math.log10(min) : min;
    const hi = log ? Math.log10(max) : max;
    return {
      project(value) {
        const v = log ? Math.log10(value) : value;
        return range[0] + ((v - lo) / (hi - lo)) * (range[1] - range[0]);
      },
      ticks(count) {
        const out = [];
        for (let i = 0; i < count; i++) {
          const raw = lo + ((hi - lo) * i) / (count - 1);
          out.push(log ? Math.pow(10, raw) : raw);
        }
        return out;
      },
    };
  }

  function renderChart(spec) {
    const card = document.createElement("div");
    card.className = "chart-card";
    const title = document.createElement("h4");
    title.textContent = spec.title || "Plot";
    card.appendChild(title);

    const width = 760;
    const height = 300;
    const pad = { left: 72, right: 20, top: 18, bottom: 58 };
    const xRange = [pad.left, width - pad.right];
    const yRange = [height - pad.bottom, pad.top];
    const svg = el("svg", { viewBox: `0 0 ${width} ${height}`, role: "img",
      "aria-label": `${spec.title}: ${spec.x_label} vs ${spec.y_label}` });

    const active = (spec.series || []).filter((s) => s.points && s.points.length);
    const xValues = [];
    const yValues = [];
    active.forEach((s) => s.points.forEach((p) => { xValues.push(p[0]); yValues.push(p[1]); }));
    const logX = spec.x_scale === "log";
    const sx = makeScale(xValues, logX, xRange);
    const sy = makeScale(yValues, false, yRange);

    sy.ticks(5).forEach((v) => {
      const y = sy.project(v);
      svg.appendChild(el("line", { x1: xRange[0], x2: xRange[1], y1: y, y2: y,
        stroke: "#e2ebf3", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: xRange[0] - 8, y: y + 4, "text-anchor": "end",
        fill: "#546d83", "font-size": 11 }, tickLabel(v, "linear")));
    });
    sx.ticks(6).forEach((v) => {
      const x = sx.project(v);
      svg.appendChild(el("line", { x1: x, x2: x, y1: yRange[1], y2: yRange[0],
        stroke: "#eef3f7", "stroke-width": 1 }));
      svg.appendChild(el("text", { x: x, y: yRange[0] + 18, "text-anchor": "middle",
        fill: "#546d83", "font-size": 11 }, tickLabel(v, spec.x_scale)));
    });

    svg.appendChild(el("line", { x1: xRange[0], x2: xRange[1], y1: yRange[0], y2: yRange[0],
      stroke: "#486275", "stroke-width": 1.5 }));
    svg.appendChild(el("line", { x1: xRange[0], x2: xRange[0], y1: yRange[1], y2: yRange[0],
      stroke: "#486275", "stroke-width": 1.5 }));
    svg.appendChild(el("text", { x: (xRange[0] + xRange[1]) / 2, y: height - 12,
      "text-anchor": "middle", fill: "#17344b", "font-size": 12 }, spec.x_label || ""));
    svg.appendChild(el("text", { x: 14, y: (yRange[0] + yRange[1]) / 2,
      "text-anchor": "middle", fill: "#17344b", "font-size": 12,
      transform: `rotate(-90 14 ${(yRange[0] + yRange[1]) / 2})` }, spec.y_label || ""));

    active.forEach((series, index) => {
      const color = COLORS[index % COLORS.length];
      const points = series.points
        .filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]) && (!logX || p[0] > 0))
        .map((p) => `${sx.project(p[0]).toFixed(2)},${sy.project(p[1]).toFixed(2)}`)
        .join(" ");
      svg.appendChild(el("polyline", { points: points, fill: "none", stroke: color,
        "stroke-width": 2, "stroke-linejoin": "round" }));
    });
    card.appendChild(svg);

    if (active.length) {
      const legend = document.createElement("div");
      legend.className = "chart-legend";
      active.forEach((series, index) => {
        const item = document.createElement("span");
        item.style.setProperty("--line-color", COLORS[index % COLORS.length]);
        item.textContent = series.name || `Series ${index + 1}`;
        legend.appendChild(item);
      });
      card.appendChild(legend);
    }
    return card;
  }

  function drawPlots() {
    // One page can host several runs (B6) or two viewport panels (B8).
    document.querySelectorAll('script[type="application/json"][id^="sim-plot-data"]')
      .forEach((dataNode) => {
        const target = document.getElementById(
          dataNode.id.replace("sim-plot-data", "sim-charts")
        );
        if (!target || target.childElementCount) return;
        try {
          const specs = JSON.parse(dataNode.textContent);
          specs.forEach((spec) => target.appendChild(renderChart(spec)));
        } catch (error) {
          const note = document.createElement("p");
          note.className = "error";
          note.textContent = "ไม่สามารถวาดกราฟจากข้อมูลที่ส่งมาได้";
          target.appendChild(note);
        }
      });
  }

  function markRunning() {
    const form = document.getElementById("sim-form");
    const status = document.getElementById("sim-status");
    if (!form || !status) return;
    form.addEventListener("submit", () => {
      status.textContent = "Simulation status: running…";
      status.className = "chip";
    });
  }

  document.addEventListener("DOMContentLoaded", () => { markRunning(); drawPlots(); });
})();
