import unittest
from spmetrics.extractor import SpMetricsExtractor


class TestSpMetricsExtractor(unittest.TestCase):
    def test_liuLLMbasedAIAgent2025_optimized_g1_5(self):
        sim = SpMetricsExtractor(
            "examples/liuLLMbasedAIAgent2025_optimized_g1-5.cir", debug=True
        )
        sim.run_all_simulations()
        print(sim)

        expected_metrics = {
            "output_swing": 1.4404096009999998,
            "offset_voltage": 0.00039571539999999975,
            "bandwidth": 157.23039359,
            "unity_gain_bandwidth": 12589252.84107459,
            "phase_margin": 54.504397340672796,
            "ac_gain": 100.43850464700688,
            "icmr": 0.45100000000000007,
            "leakage_power": 0.00769409094592984,
            "tran_gain": 66.07348764224093,
            "cmrr_tran": 124.13528738665167,
            "cmrr_ac": 91.92981270713756,
        }
        for metric, expected_value in expected_metrics.items():
            self.assertAlmostEqual(sim.metrics[metric], expected_value, places=4)
