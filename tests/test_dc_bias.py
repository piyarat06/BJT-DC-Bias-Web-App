import math
import unittest

from dc_bias import solve, solve_emitter, solve_fixed


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
            self.assertTrue(math.isfinite(getattr(r, name)), f"{name} ไม่ใช่ finite number")


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

    def test_non_finite_inputs_raise_value_error(self):
        # float("1e309") == inf and float("nan") == nan parse successfully,
        # so validation must reject them before they reach the equations.
        cases = [
            (float("inf"), 100e3, 22e3, 2.2e3, 1e3, 100.0, 0.7),
            (float("nan"), 100e3, 22e3, 2.2e3, 1e3, 100.0, 0.7),
            (12.0, float("inf"), 22e3, 2.2e3, 1e3, 100.0, 0.7),
            (12.0, 100e3, 22e3, 2.2e3, 1e3, float("inf"), 0.7),
            (12.0, 100e3, 22e3, 2.2e3, 1e3, 100.0, float("nan")),
        ]
        for args in cases:
            with self.subTest(first_arg=args[0]):
                with self.assertRaises(ValueError):
                    solve(*args)

    def test_non_finite_error_message_names_the_field(self):
        with self.assertRaises(ValueError) as ctx:
            solve(float("inf"), 100e3, 22e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertIn("VCC", str(ctx.exception))


class TestRegionWarnings(unittest.TestCase):
    def test_cutoff_region(self):
        # VCC=5, R1=100k, R2=1k -> VTH = 0.0495 V <= 0.7 V
        r = solve(5.0, 100e3, 1e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertAlmostEqual(r.vb, 0.049505, delta=1e-6)
        self.assertAlmostEqual(r.vc, 5.0, delta=1e-9)
        self.assertTrue(any("Cutoff" in w for w in r.warnings))

    def test_cutoff_boundary_vth_equals_vbe(self):
        # VCC=1.4, R1=R2=1k -> VTH = 0.7 V == VBE
        r = solve(1.4, 1e3, 1e3, 1e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "cutoff")

    def test_saturation_region(self):
        # VCC=1.2, R1=10k, R2=100k, RC=2.2k, RE=1k, beta=100 -> VCE ~ 0.06 V
        r = solve(1.2, 10e3, 100e3, 2.2e3, 1e3, 100.0, 0.7)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.2)
        self.assertTrue(any("Saturation" in w for w in r.warnings))


class TestFixedEmitter(unittest.TestCase):
    """ค่าอ้างอิงคำนวณมือสำหรับ Fixed Bias (RE=0) และ Emitter Bias (RB จาก VCC + RE)"""

    def test_fixed_reference_values(self):
        r = solve_fixed(12.0, 470e3, 2.2e3, 100.0, 0.70)
        self.assertAlmostEqual(r.vth, 12.0, delta=1e-9)
        self.assertAlmostEqual(r.rth, 470000.0, delta=1e-6)
        self.assertAlmostEqual(r.ib, 24.042553e-6, delta=1e-11)
        self.assertAlmostEqual(r.ic, 2.404255e-3, delta=1e-8)
        self.assertAlmostEqual(r.ie, 2.428298e-3, delta=1e-8)
        self.assertAlmostEqual(r.ve, 0.0, delta=1e-12)
        self.assertAlmostEqual(r.vb, 0.70, delta=1e-6)
        self.assertAlmostEqual(r.vc, 6.710638, delta=1e-5)
        self.assertAlmostEqual(r.vce, 6.710638, delta=1e-5)
        self.assertEqual(r.region, "forward_active")
        self.assertEqual(r.warnings, [])

    def test_emitter_reference_values(self):
        r = solve_emitter(12.0, 470e3, 2.2e3, 1e3, 100.0, 0.70)
        self.assertAlmostEqual(r.vth, 12.0, delta=1e-9)
        self.assertAlmostEqual(r.rth, 470000.0, delta=1e-6)
        self.assertAlmostEqual(r.ib, 19.789842e-6, delta=1e-11)
        self.assertAlmostEqual(r.ic, 1.978984e-3, delta=1e-8)
        self.assertAlmostEqual(r.ie, 1.998774e-3, delta=1e-8)
        self.assertAlmostEqual(r.ve, 1.998774, delta=1e-5)
        self.assertAlmostEqual(r.vb, 2.698774, delta=1e-5)
        self.assertAlmostEqual(r.vc, 7.646235, delta=1e-5)
        self.assertAlmostEqual(r.vce, 5.647461, delta=1e-5)
        self.assertEqual(r.region, "forward_active")
        self.assertEqual(r.warnings, [])

    def test_fixed_cutoff(self):
        r = solve_fixed(0.5, 470e3, 2.2e3, 100.0, 0.70)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertAlmostEqual(r.vb, 0.5, delta=1e-9)
        self.assertAlmostEqual(r.vc, 0.5, delta=1e-9)
        self.assertAlmostEqual(r.vce, 0.5, delta=1e-9)
        self.assertTrue(any("Cutoff" in w for w in r.warnings))

    def test_emitter_cutoff(self):
        r = solve_emitter(0.5, 470e3, 2.2e3, 1e3, 100.0, 0.70)
        self.assertEqual(r.region, "cutoff")
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.ic, 0.0)
        self.assertEqual(r.ie, 0.0)
        self.assertAlmostEqual(r.vb, 0.5, delta=1e-9)
        self.assertAlmostEqual(r.vc, 0.5, delta=1e-9)
        self.assertAlmostEqual(r.vce, 0.5, delta=1e-9)
        self.assertTrue(any("Cutoff" in w for w in r.warnings))

    def test_fixed_saturation(self):
        r = solve_fixed(12.0, 10e3, 2.2e3, 100.0, 0.70)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.2)
        self.assertTrue(any("Saturation" in w for w in r.warnings))

    def test_emitter_saturation(self):
        r = solve_emitter(12.0, 10e3, 2.2e3, 1e3, 100.0, 0.70)
        self.assertEqual(r.region, "saturation")
        self.assertLess(r.vce, 0.2)
        self.assertTrue(any("Saturation" in w for w in r.warnings))

    def test_invalid_resistances_name_fields(self):
        fixed_cases = [
            ((12.0, 0.0, 2.2e3, 100.0, 0.7), "RB"),
            ((12.0, -1.0, 2.2e3, 100.0, 0.7), "RB"),
            ((12.0, 470e3, 0.0, 100.0, 0.7), "RC"),
            ((12.0, 470e3, 2.2e3, 0.0, 0.7), "β"),
            ((12.0, 470e3, 2.2e3, 100.0, -0.1), "VBE"),
            ((0.0, 470e3, 2.2e3, 100.0, 0.7), "VCC"),
        ]
        for args, name in fixed_cases:
            with self.subTest(solver="fixed", field=name):
                with self.assertRaises(ValueError) as ctx:
                    solve_fixed(*args)
                self.assertIn(name, str(ctx.exception))
        for re in (0.0, -1.0):
            with self.subTest(solver="emitter", re=re):
                with self.assertRaises(ValueError) as ctx:
                    solve_emitter(12.0, 470e3, 2.2e3, re, 100.0, 0.7)
                self.assertIn("RE", str(ctx.exception))

    def test_non_finite_inputs_rejected(self):
        for bad in (float("inf"), float("nan")):
            with self.subTest(solver="fixed", bad=bad):
                with self.assertRaises(ValueError) as ctx:
                    solve_fixed(12.0, bad, 2.2e3, 100.0, 0.7)
                self.assertIn("จำนวนจำกัด", str(ctx.exception))
            with self.subTest(solver="emitter", bad=bad):
                with self.assertRaises(ValueError) as ctx:
                    solve_emitter(12.0, 470e3, 2.2e3, bad, 100.0, 0.7)
                self.assertIn("จำนวนจำกัด", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
