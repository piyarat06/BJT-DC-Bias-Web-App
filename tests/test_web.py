import unittest
from app import app

DEFAULTS_FORM = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2", "re": "1", "beta": "100", "vbe": "0.7"}


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


if __name__ == "__main__":
    unittest.main()
