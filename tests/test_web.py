import re
import unittest
from app import app

DEFAULTS_FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"}
FIXED_FORM = {"vcc": "12", "rb": "470", "rc": "2.2", "beta": "100", "vbe": "0.7"}
EMITTER_FORM = {**FIXED_FORM, "re": "1"}


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_index_returns_form(self):              # A1
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        # all seven inputs must exist with the exact names POST /calculate reads
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', text)
        self.assertIn("VCC", text)
        self.assertIn("Calculate DC Bias", text)

    def test_post_calculate_shows_result(self):        # A2 + A3
        resp = self.client.post("/calculate", data=DEFAULTS_FORM)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("1.230", text)   # IC = 1.230 mA
        self.assertIn("mA", text)

    def test_post_invalid_resistor_shows_error(self):  # A4
        form = dict(DEFAULTS_FORM, r1="-5")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("R1 ต้องมากกว่า 0", resp.data.decode("utf-8"))

    def test_post_non_numeric_value(self):              # A4
        form = dict(DEFAULTS_FORM, vcc="abc")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องเป็นตัวเลข", resp.data.decode("utf-8"))

    def test_post_non_finite_value(self):              # review fix: 1e309 -> inf
        form = dict(DEFAULTS_FORM, vcc="1e309")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("VCC", text)
        self.assertIn("จำนวนจำกัด", text)

    def test_post_empty_field(self):                   # A4
        form = dict(DEFAULTS_FORM, r2="")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("ต้องเป็นตัวเลข", resp.data.decode("utf-8"))

    def test_post_whitespace_number(self):
        form = dict(DEFAULTS_FORM, vcc=" 12 ")
        resp = self.client.post("/calculate", data=form)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("1.230", resp.data.decode("utf-8"))

    def test_cutoff_warning_displayed(self):           # A5
        form = dict(DEFAULTS_FORM, vcc="5", r1="100", r2="1")
        resp = self.client.post("/calculate", data=form)
        self.assertIn("Cutoff", resp.data.decode("utf-8"))

    def test_saturation_warning_displayed(self):        # A5
        form = {"vcc": "1.2", "r1": "10", "r2": "100", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"}
        resp = self.client.post("/calculate", data=form)
        self.assertIn("Saturation", resp.data.decode("utf-8"))


class TestFixedEmitterWeb(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def assert_open_section(self, text, title):
        self.assertRegex(text, rf'<details[^>]*\bopen\b[^>]*>\s*<summary>{title}</summary>')
        self.assertEqual(len(re.findall(r'<details[^>]*\bopen\b', text)), 1)

    def test_old_urls_redirect_to_single_page(self):
        for path, location in (("/fixed", "/?circuit=fixed"), ("/emitter", "/?circuit=emitter")):
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.headers["Location"], location)

    def test_query_param_opens_requested_section(self):
        for param, title in (("fixed", "Fixed Bias"), ("emitter", "Emitter Bias"), ("bogus", "Voltage-Divider Bias")):
            text = self.client.get(f"/?circuit={param}").data.decode("utf-8")
            self.assertEqual(text.count("<details"), 3)
            self.assert_open_section(text, title)

    def test_post_opens_submitted_section_and_shows_result(self):
        cases = (
            ("/calculate", DEFAULTS_FORM, "1.230", "Voltage-Divider Bias"),
            ("/calculate-fixed", FIXED_FORM, "2.404", "Fixed Bias"),
            ("/calculate-emitter", EMITTER_FORM, "1.979", "Emitter Bias"),
        )
        for route, form, number, title in cases:
            text = self.client.post(route, data=form).data.decode("utf-8")
            self.assertIn(number, text)
            self.assert_open_section(text, title)

    def test_single_page_defaults_for_all_circuits(self):
        text = self.client.get("/").data.decode("utf-8")
        for field, value in (("r1", "100.0"), ("r2", "22.0"), ("rb", "470.0"),
                             ("rc", "2.2"), ("re", "1.0"), ("beta", "100.0"), ("vbe", "0.7")):
            self.assertRegex(text, rf'name="{field}"\s+value="{re.escape(value)}"')

    def test_post_fixed_calculates_real_value(self):
        resp = self.client.post("/calculate-fixed", data=FIXED_FORM)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("2.404", text)
        self.assertIn("mA", text)
        self.assertIn("forward_active", text)

    def test_post_emitter_calculates_real_value(self):
        resp = self.client.post("/calculate-emitter", data=EMITTER_FORM)
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode("utf-8")
        self.assertIn("1.979", text)
        self.assertIn("5.647", text)

    def test_single_page_has_three_sections(self):
        text = self.client.get("/").data.decode("utf-8")
        self.assertEqual(text.count("<details"), 3)
        for title in ("Voltage-Divider Bias", "Fixed Bias", "Emitter Bias"):
            self.assertIn(f"<summary>{title}</summary>", text)
        for action in ("/calculate", "/calculate-fixed", "/calculate-emitter"):
            self.assertIn(f'action="{action}"', text)
        for field in ("vcc", "r1", "r2", "rb", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', text)
        self.assertNotIn('href="/fixed"', text)  # ไม่มีแถบ nav แล้ว

    def test_post_fixed_invalid_rb(self):
        resp = self.client.post("/calculate-fixed", data=dict(FIXED_FORM, rb="-5"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("RB ต้องมากกว่า 0", resp.data.decode("utf-8"))

    def test_post_blank_rb_shows_error(self):
        resp = self.client.post("/calculate-fixed", data=dict(FIXED_FORM, rb=""))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("RB ต้องเป็นตัวเลข", resp.data.decode("utf-8"))

    def test_post_error_repopulates_entered_value(self):
        resp = self.client.post("/calculate-fixed", data=dict(FIXED_FORM, rb=""))
        text = resp.data.decode("utf-8")
        self.assertRegex(text, r'name="rb"\s+value=""')  # blank stays blank, not default 470
        self.assertRegex(text, r'name="vcc"\s+value="12"')  # other fields keep what was sent

    def test_post_emitter_non_finite_vcc(self):
        resp = self.client.post("/calculate-emitter", data=dict(EMITTER_FORM, vcc="1e309"))
        text = resp.data.decode("utf-8")
        self.assertIn("VCC", text)
        self.assertIn("จำนวนจำกัด", text)

    def test_post_fixed_cutoff_warning(self):
        resp = self.client.post("/calculate-fixed", data=dict(FIXED_FORM, vcc="0.5"))
        self.assertIn("Cutoff", resp.data.decode("utf-8"))

    def test_post_emitter_saturation_warning(self):
        resp = self.client.post("/calculate-emitter", data=dict(EMITTER_FORM, rb="10"))
        self.assertIn("Saturation", resp.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
