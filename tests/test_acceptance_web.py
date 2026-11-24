"""HTTP tests for the one-tab-per-case Lab 04 acceptance evidence pages."""

import json
import re
import unittest

import app as flask_app


class TestAcceptancePages(unittest.TestCase):
    def setUp(self):
        flask_app.app.testing = True
        self.client = flask_app.app.test_client()

    def _plot_payloads(self, html):
        nodes = re.findall(
            r'<script id="(sim-plot-data[^"]*)" type="application/json">(.*?)</script>',
            html, re.S,
        )
        return [(node_id, json.loads(raw)) for node_id, raw in nodes]

    def test_index_links_all_cases(self):
        response = self.client.get("/acceptance")
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        for case in ("b2", "b3", "b4", "b5", "b6", "b7", "b8"):
            self.assertIn(f"/acceptance/{case}", text)

    def test_unknown_case_is_404(self):
        self.assertEqual(self.client.get("/acceptance/b99").status_code, 404)

    def test_b2_real_dc_result(self):
        text = self.client.get("/acceptance/b2").get_data(as_text=True)
        self.assertIn("B2", text)
        self.assertIn("Simulation status: success", text)
        self.assertIn("VB (base voltage)", text)
        self.assertIn("1.949 V", text)
        self.assertIn("RE n_e 0 1k", text)
        self.assertIn("QNPN", text)
        self.assertEqual(self._plot_payloads(text), [])

    def test_b3_uses_changed_re(self):
        text = self.client.get("/acceptance/b3").get_data(as_text=True)
        self.assertIn("RE n_e 0 2k", text)
        self.assertIn("0.696 mA", text)
        self.assertIn("RE=1 kΩ → 2 kΩ", text)

    def test_b4_two_bode_charts(self):
        text = self.client.get("/acceptance/b4").get_data(as_text=True)
        payloads = self._plot_payloads(text)
        self.assertEqual(len(payloads), 1)
        charts = payloads[0][1]
        self.assertIsInstance(charts, list)
        self.assertEqual(len(charts), 2)
        self.assertEqual(charts[0]["x_label"], "Frequency (Hz)")
        self.assertEqual(charts[1]["y_label"], "Phase (degree)")
        self.assertIn("1.75 V/V (4.86 dB)", text)

    def test_b5_transient_waveform(self):
        text = self.client.get("/acceptance/b5").get_data(as_text=True)
        payloads = self._plot_payloads(text)
        self.assertEqual(len(payloads), 1)
        charts = payloads[0][1]
        self.assertEqual(len(charts), 1)
        self.assertEqual([s["name"] for s in charts[0]["series"]], ["Vin", "Vout"])
        self.assertIn("inverted", text)

    def test_b6_shows_both_source_changes(self):
        text = self.client.get("/acceptance/b6").get_data(as_text=True)
        self.assertEqual(text.count('class="accept-run"'), 2)
        self.assertIn("SIN(0 0.03 1000 0 0)", text)
        self.assertIn("SIN(0 0.01 5000 0 0)", text)
        self.assertIn("52.48 mV", text)
        self.assertIn("1.000 ms", text)
        payload_ids = [node_id for node_id, _ in self._plot_payloads(text)]
        self.assertEqual(payload_ids, ["sim-plot-data-run1", "sim-plot-data-run2"])

    def test_b7_error_has_no_success_or_plots(self):
        text = self.client.get("/acceptance/b7").get_data(as_text=True)
        self.assertIn("Simulation status: error", text)
        self.assertIn("RE ต้องมากกว่า 0", text)
        self.assertNotIn("Simulation status: success", text)
        self.assertEqual(self._plot_payloads(text), [])

    def test_b8_has_desktop_and_mobile_chart_targets(self):
        text = self.client.get("/acceptance/b8").get_data(as_text=True)
        payload_ids = [node_id for node_id, _ in self._plot_payloads(text)]
        self.assertIn("sim-plot-data-desktop", payload_ids)
        self.assertIn("sim-plot-data-mobile", payload_ids)
        self.assertIn('id="sim-charts-desktop"', text)
        self.assertIn('id="sim-charts-mobile"', text)
        self.assertIn("390", text)

    def test_app_js_renders_every_plot_node(self):
        source = (flask_app.app.root_path + "/static/app.js")
        with open(source, encoding="utf-8") as handle:
            js = handle.read()
        self.assertIn('id^="sim-plot-data"', js)
        self.assertIn('replace("sim-plot-data", "sim-charts")', js)


if __name__ == "__main__":
    unittest.main()
