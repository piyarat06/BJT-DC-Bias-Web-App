"""Lab 4 tests for the ngspice adapter.

The pure functions (validation, netlist, raw parser) are always tested.
Tests that really execute ngspice are skipped when the engine is not present,
so the repository remains testable without the external solver installed.
"""

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

import spice_engine as se

ENGINE = se.resolve_engine()


class TestValidation(unittest.TestCase):
    def test_defaults_are_valid(self):
        params = se.normalize_params(dict(se.DEFAULT_PARAMS))
        self.assertAlmostEqual(params["vcc"], 12.0)
        self.assertAlmostEqual(params["amplitude"], 0.01)

    def test_re_zero_rejected(self):
        with self.assertRaises(se.SpiceError) as ctx:
            se.normalize_params(dict(se.DEFAULT_PARAMS, re="0"))
        self.assertIn("RE", str(ctx.exception))

    def test_negative_capacitor_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.normalize_params(dict(se.DEFAULT_PARAMS, cin="-1"))

    def test_amplitude_zero_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.normalize_params(dict(se.DEFAULT_PARAMS, amplitude="0"))

    def test_frequency_out_of_range_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.normalize_params(dict(se.DEFAULT_PARAMS, frequency="-1000"))

    def test_non_numeric_rejected_without_reaching_netlist(self):
        with self.assertRaises(se.SpiceError) as ctx:
            se.normalize_params(dict(se.DEFAULT_PARAMS, rc="1; rm -rf /"))
        self.assertIn("ตัวเลข", str(ctx.exception))

    def test_infinite_value_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.normalize_params(dict(se.DEFAULT_PARAMS, vcc="1e309"))


class TestNetlist(unittest.TestCase):
    def setUp(self):
        self.params = se.normalize_params(dict(se.DEFAULT_PARAMS))

    def test_dc_netlist_has_op_and_reference_values(self):
        net = se.build_netlist("dc", self.params)
        self.assertIn(".OP", net)
        self.assertNotIn(".AC", net)
        self.assertNotIn(".TRAN", net)
        self.assertIn("VCC vcc 0 DC 12", net)
        self.assertIn("R1 vcc n_b 100k", net)
        self.assertIn("R2 n_b 0 22k", net)
        self.assertIn("RC vcc n_c 2.2k", net)
        self.assertIn("RE n_e 0 1k", net)
        self.assertIn("RL n_out 0 10k", net)
        self.assertIn("CIN n_in n_b 10u", net)
        self.assertIn("COUT n_c n_out 10u", net)
        self.assertIn("SIN(0 0.01 1000 0 0)", net)
        self.assertIn(".MODEL QNPN NPN", net)
        self.assertIn("BF=100", net)
        self.assertTrue(net.rstrip().endswith(".END"))

    def test_ac_netlist_uses_ac_analysis(self):
        net = se.build_netlist("ac", self.params)
        self.assertIn(".AC DEC 20 1 1G", net)
        self.assertNotIn(".OP", net)
        self.assertNotIn(".TRAN", net)

    def test_tran_netlist_time_step_tracks_source_frequency(self):
        low = se.build_netlist("tran", self.params)
        fast = se.build_netlist("tran", dict(self.params, frequency=10000.0))
        self.assertIn(".TRAN", low)
        self.assertIn(".TRAN", fast)
        self.assertIn("0.005", low)          # 5 periods of 1 kHz
        self.assertIn("0.0005", fast)        # 5 periods of 10 kHz
        self.assertNotEqual(low, fast)

    def test_unknown_mode_rejected(self):
        with self.assertRaises(se.SpiceError):
            se.build_netlist("bogus", self.params)


class TestRawParser(unittest.TestCase):
    SAMPLE = """Title: synthetic
Plotname: AC Analysis
Flags: complex
No. Variables: 3
No. Points: 2
Variables:
\t0\tfrequency\tfrequency
\t1\tv(n_in)\tvoltage
\t2\tv(n_out)\tvoltage
Values:
0\t1.000000000000000e+00,0.000000000000000e+00
\t1.000000000000000e-02,0.000000000000000e+00
\t-1.000000000000000e-02,0.000000000000000e-02
1\t1.000000000000000e+03,0.000000000000000e+00
\t1.000000000000000e-02,0.000000000000000e+00
\t1.750000000000000e-02,0.000000000000000e-02
"""

    def test_parse_complex_raw(self):
        raw = se.parse_raw(self.SAMPLE)
        self.assertEqual(raw["variables"], ["frequency", "v(n_in)", "v(n_out)"])
        self.assertEqual(len(raw["points"]), 2)
        first = raw["points"][0]
        self.assertAlmostEqual(first[0].real, 1.0)
        self.assertAlmostEqual(first[1].real, 0.01)
        self.assertAlmostEqual(first[2].real, -0.01)
        self.assertIsInstance(first[0], complex)

    def test_truncated_raw_raises(self):
        with self.assertRaises(se.SpiceError):
            se.parse_raw(self.SAMPLE.replace("1.750000000000000e-02,0.000000000000000e-02", ""))


class TestRunFailures(unittest.TestCase):
    """Engine problems must become errors, never a stale/success result."""

    def setUp(self):
        self.params = se.normalize_params(dict(se.DEFAULT_PARAMS))
        self.engine = "fake-ngspice"

    def test_timeout_is_error(self):
        error = subprocess.TimeoutExpired(cmd=self.engine, timeout=se.TIMEOUT_SECONDS)
        with patch("spice_engine.subprocess.run", side_effect=error):
            with self.assertRaises(se.SpiceError) as ctx:
                se.run_simulation("dc", self.params, engine=self.engine)
        self.assertIn("เกิน", str(ctx.exception))

    def test_nonzero_exit_is_error(self):
        def fake_run(command, **kwargs):
            log = Path(command[command.index("-o") + 1])
            log.write_text("Error on line 3: bad netlist\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 1, "", "")

        with patch("spice_engine.subprocess.run", side_effect=fake_run):
            with self.assertRaises(se.SpiceError) as ctx:
                se.run_simulation("dc", self.params, engine=self.engine)
        self.assertIn("exit 1", str(ctx.exception))

    def test_empty_raw_file_is_error(self):
        def fake_run(command, **kwargs):
            log = Path(command[command.index("-o") + 1])
            raw = Path(command[command.index("-r") + 1])
            log.write_text("ngspice-47\n", encoding="utf-8")
            raw.write_text("", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("spice_engine.subprocess.run", side_effect=fake_run):
            with self.assertRaises(se.SpiceError) as ctx:
                se.run_simulation("dc", self.params, engine=self.engine)
        self.assertIn("raw file ว่าง", str(ctx.exception))


@unittest.skipUnless(ENGINE, "ngspice not installed on this machine")
class TestRealSimulation(unittest.TestCase):
    def setUp(self):
        self.params = se.normalize_params(dict(se.DEFAULT_PARAMS))

    def test_dc_operating_point_comes_from_ngspice(self):
        run = se.run_simulation("dc", self.params, engine=ENGINE)
        self.assertEqual(run["status"], "success")
        self.assertIn("ngspice", run["engine"])
        by_label = {row["label"]: row["value"] for row in run["summary"]}
        vb = float(by_label["VB (base voltage)"].split()[0])
        vc = float(by_label["VC (collector voltage)"].split()[0])
        ic = float(by_label["IC (collector current)"].split()[0])
        self.assertGreater(vb, 1.5)
        self.assertLess(vb, 2.5)
        self.assertGreater(vc, 7.0)
        self.assertLess(vc, 11.0)
        self.assertGreater(ic, 1.0)
        self.assertLess(ic, 2.0)
        self.assertIn("i(vcc)", run["netlist"] + run["log_excerpt"] + " ".join(run["notes"]))

    def test_ac_gain_and_phase_are_from_real_sweep(self):
        run = se.run_simulation("ac", self.params, engine=ENGINE)
        self.assertEqual(run["status"], "success")
        summary = {row["label"]: row["value"] for row in run["summary"]}
        gain = float(summary["Gain @ source frequency"].split()[0])
        phase = float(summary["Phase @ source frequency"].split()[0])
        self.assertGreater(gain, 1.0)
        self.assertLess(gain, 3.0)
        self.assertLess(phase, -150.0)  # common emitter inverts the signal
        chart = run["charts"][0]
        self.assertEqual(chart["x_label"], "Frequency (Hz)")
        self.assertGreater(len(chart["series"][0]["points"]), 100)

    def test_transient_waveform_and_source_change(self):
        run = se.run_simulation("tran", self.params, engine=ENGINE)
        self.assertEqual(run["status"], "success")
        summary = {row["label"]: row["value"] for row in run["summary"]}
        vin = float(summary["Vin peak"].split()[0])
        vout = float(summary["Vout peak"].split()[0])
        self.assertAlmostEqual(vin, 10.0, delta=1.0)   # mV
        self.assertGreater(vout, 5.0)
        self.assertEqual(run["phase_relation"], "inverted")
        chart = run["charts"][0]
        self.assertEqual(chart["x_label"], "Time (ms)")
        self.assertEqual(len(chart["series"]), 2)

        louder = se.run_simulation("tran", dict(self.params, amplitude=0.02), engine=ENGINE)
        louder_summary = {row["label"]: row["value"] for row in louder["summary"]}
        louder_vout = float(louder_summary["Vout peak"].split()[0])
        self.assertGreater(louder_vout, vout * 1.5)

    def test_engine_failure_is_not_reported_as_success(self):
        with self.assertRaises(se.SpiceError):
            se.run_simulation("dc", dict(self.params, re=0.0), engine=ENGINE)
        with self.assertRaises(se.SpiceError):
            se.run_simulation("dc", self.params, engine="C:\\definitely\\not\\ngspice.exe")


if __name__ == "__main__":
    unittest.main()
