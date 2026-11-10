import unittest
from dc_bias import solve


class TestSolveReferenceValues(unittest.TestCase):
    """ค่าอ้างอิงคำนวณมืออย่างอิสระ (Lab §06): VCC=12V R1=100k R2=22k
    RC=2.2k RE=1k beta=100 VBE=0.70V หน่วย SI ทั้งหมด"""

    def test_solve_reference_values(self):
        r = solve(12.0, 100_000.0, 22_000.0, 2_200.0, 1_000.0, 100.0, 0.70)
        self.assertAlmostEqual(r.vth, 2.163934, delta=1e-4)
        self.assertAlmostEqual(r.rth, 18032.787, delta=0.05)
        self.assertAlmostEqual(r.ib, 1.22986e-5, delta=2e-9)
        self.assertAlmostEqual(r.ic, 1.22986e-3, delta=2e-7)
        self.assertAlmostEqual(r.ie, 1.24216e-3, delta=2e-7)
        self.assertAlmostEqual(r.ve, 1.242161, delta=1e-4)
        self.assertAlmostEqual(r.vb, 1.942161, delta=1e-4)
        self.assertAlmostEqual(r.vc, 9.294304, delta=1e-4)
        self.assertAlmostEqual(r.vce, 8.052144, delta=1e-4)
        self.assertEqual(r.region, "forward_active")
        self.assertEqual(r.warnings, [])

    def test_extreme_resistors_no_crash(self):
        r = solve(12.0, 1e9, 1e9, 1e6, 1e6, 100.0, 0.7)
        for name in ("vth", "rth", "ib", "ic", "ie", "ve", "vb", "vc", "vce"):
            self.assertTrue(getattr(r, name) == getattr(r, name), f"{name} ไม่ใช่ finite number")


class TestValidation(unittest.TestCase):
    def test_invalid_inputs_raise_value_error(self):
        cases = [
            ((0.0, 100e3, 22e3, 2.2e3, 1e3, 100.0, 0.7), "VCC"),
            ((12.0, 0.0, 22e3, 2.2e3, 1e3, 100.0, 0.7), "R1"),
            ((12.0, 100e3, -5.0, 2.2e3, 1e3, 100.0, 0.7), "R2"),
            ((12.0, 100e3, 22e3, 0.0, 1e3, 100.0, 0.7), "RC"),
            ((12.0, 100e3, 22e3, 2.2e3, -1.0, 100.0, 0.7), "RE"),
            ((12.0, 100e3, 22e3, 2.2e3, 1e3, 0.0, 0.7), "β"),
            ((12.0, 100e3, 22e3, 2.2e3, 1e3, 100.0, -0.1), "VBE"),
        ]
        for args, name in cases:
            with self.subTest(field=name):
                with self.assertRaises(ValueError):
                    solve(*args)

    def test_error_message_names_the_field(self):
        with self.assertRaises(ValueError) as ctx:
            solve(12.0, 0.0, 22e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertIn("R1", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
