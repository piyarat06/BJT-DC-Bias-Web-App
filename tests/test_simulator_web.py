"""Lab 4 browser-layer tests: simulator section, routes and error states."""

import json
import re
import unittest

from app import app
import spice_engine as se

SIM_FORM = {
    "mode": "dc",
    "sim_vcc": "12", "sim_r1": "100", "sim_r2": "22", "sim_rc": "2.2",
    "sim_re": "1", "sim_rl": "10", "sim_cin": "10", "sim_cout": "10",
    "sim_amplitude": "0.01", "sim_frequency": "1000",
}
ENGINE = se.resolve_engine()


def plot_json(text):
    match = re.search(r'<script id="sim-plot-data" type="application/json">(.*?)</script>', text, re.S)
    return json.loads(match.group(1)) if match else None


class TestSimulatorPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_contains_simulator_section_and_inputs(self):
        text = self.client.get("/").data.decode("utf-8")
        self.assertIn("CE Amplifier Simulator", text)
        for field in SIM_FORM:
            self.assertIn(f'name="{field}"', text)
        self.assertIn('action="/simulate"', text)
        self.assertIn('value="dc"', text)
        self.assertIn('value="ac"', text)
        self.assertIn('value="tran"', text)
        self.assertIn("Model: QNPN", text)

    def test_regression_three_bias_sections_still_present(self):
        text = self.client.get("/").data.decode("utf-8")
        self.assertEqual(text.count("<details"), 3)
        self.assertEqual(len(re.findall(r"<details[^>]*\bopen\b", text)), 1)


class TestSimulatorErrors(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_invalid_re_shows_error_and_no_success(self):
        text = self.client.post("/simulate", data=dict(SIM_FORM, sim_re="0")).data.decode("utf-8")
        self.assertIn("RE ต้องมากกว่า 0", text)
        self.assertNotIn("Simulation status: success", text)
        self.assertIsNone(plot_json(text))

    def test_unknown_mode_falls_back_to_dc(self):
        text = self.client.post("/simulate", data=dict(SIM_FORM, mode="bogus")).data.decode("utf-8")
        self.assertIn("Simulation status: success" if ENGINE else "Engine not available", text)

    def test_engine_missing_gives_clean_error(self):
        # Simulate an environment without ngspice, without reloading modules.
        from unittest.mock import patch
        with patch("spice_engine.resolve_engine", return_value=None):
            text = self.client.post("/simulate", data=SIM_FORM).data.decode("utf-8")
        self.assertIn("ไม่พบ", text)
        self.assertNotIn("Simulation status: success", text)


@unittest.skipUnless(ENGINE, "ngspice not installed on this machine")
class TestSimulatorRealRuns(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dc_post_shows_engine_provenance(self):
        text = self.client.post("/simulate", data=SIM_FORM).data.decode("utf-8")
        self.assertIn("Simulation status: success", text)
        self.assertIn("ngspice", text)
        self.assertIn("VB (base voltage)", text)
        self.assertIn(".MODEL QNPN", text)
        self.assertIn("Derived from SPICE node voltages", text)

    def test_ac_post_shows_bode_data(self):
        text = self.client.post("/simulate", data=dict(SIM_FORM, mode="ac")).data.decode("utf-8")
        self.assertIn("Gain @ source frequency", text)
        self.assertIn("Phase @ source frequency", text)
        plot = plot_json(text)
        self.assertIsNotNone(plot)
        # app.js iterates this array directly; a wrapper would silently break rendering.
        self.assertIsInstance(plot, list)
        self.assertEqual(len(plot), 2)
        self.assertEqual(plot[0]["x_label"], "Frequency (Hz)")
        self.assertGreater(len(plot[0]["series"][0]["points"]), 100)

    def test_tran_post_changes_when_amplitude_changes(self):
        quiet = plot_json(self.client.post("/simulate", data=dict(SIM_FORM, mode="tran")).data.decode("utf-8"))
        loud = plot_json(self.client.post("/simulate", data=dict(SIM_FORM, mode="tran", sim_amplitude="0.03")).data.decode("utf-8"))
        self.assertIsNotNone(quiet)
        self.assertIsInstance(quiet, list)
        self.assertEqual(len(quiet[0]["series"]), 2)
        self.assertEqual(quiet[0]["x_label"], "Time (ms)")
        self.assertNotEqual(quiet[0]["series"][0]["points"],
                            loud[0]["series"][0]["points"])

    def test_changing_re_changes_dc_result(self):
        a = self.client.post("/simulate", data=SIM_FORM).data.decode("utf-8")
        b = self.client.post("/simulate", data=dict(SIM_FORM, sim_re="2")).data.decode("utf-8")
        self.assertNotEqual(a, b)
        self.assertIn("Simulation status: success", b)


if __name__ == "__main__":
    unittest.main()
