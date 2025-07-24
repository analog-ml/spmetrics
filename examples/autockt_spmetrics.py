import numpy as np
from spmetrics.extractor import SpMetricsExtractor

sim = SpMetricsExtractor(
    "examples/settaluriAutoCktDeepReinforcement2020_34_34_34_34_34_15_2.1e-12.cir",
    debug=True,
)
sim._run_ac_simulation(output_nodes=["v(net6)"])

# expected_metrics = [
#     ("gain", 51.05404384069384),
#     ("ibias", 7.6229408e-05),
#     ("phm", 7.741114443465108),
#     ("ugbw", 9647597.545011472),
# ]
expected_metrics = [
    ("ac_gain", 51.05404384069384),
    ("ibias", 7.6229408e-05),
    ("phase_margin", 7.741114443465108),
    ("unity_gain_bandwidth", 9647597.545011472),
]
print("Expected metrics:")
print(expected_metrics)

print("Current obtained metrics:")
print(sim.metrics)
